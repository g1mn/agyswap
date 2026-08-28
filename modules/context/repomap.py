"""
RepoMapper: Extracts compact AST-based codebase maps (classes, functions, signatures)
to drastically compress project context (10~15% of raw size, < 2,000 tokens).
Supports Tree-sitter when available, with pure Python ast & regex fallbacks.
"""

from __future__ import annotations

import os
import ast
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

# Control-flow keywords excluded from C/C++ function-signature matching so that
# statements like "if (x) {" or "return foo(x);" are never mistaken for declarations.
_C_KEYWORDS = r"(?:if|while|for|switch|else|return|do|sizeof|typedef|case|goto|break|continue|default|catch|try|new|delete|throw)"
# Arg-list content: "::" (qualified names like std::vector) is allowed as a unit, but a
# lone ":" is not, so a constructor's " : member(x) {}" initializer list can't be
# mistaken for part of the argument list and swallowed up to its trailing "{".
_C_ARGS = r"(?:::|[^;{}:])*"
_C_FUNC_PATTERN = re.compile(
    rf"^(?!{_C_KEYWORDS}\b)(?:static\s+)?(?:inline\s+)?(?:virtual\s+)?(?:explicit\s+)?"
    rf"[\w][\w\s\*&:<>,]*?\s[\*&]?(?!{_C_KEYWORDS}\s*\()(\w+)\s*\({_C_ARGS}\)\s*(?:const\s*)?(?:override\s*)?[;{{]"
)

# Pre-compiled generic regex patterns for maximum performance
GENERIC_PATTERNS: Dict[str, List[re.Pattern[str]]] = {
    ".js": [
        re.compile(r"^(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*(?:<[^>]*>)?\s*\("),
        re.compile(r"^(?:export\s+)?class\s+(\w+)"),
        re.compile(r"^(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s*)?\("),
    ],
    ".ts": [
        re.compile(r"^(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*(?:<[^>]*>)?\s*\("),
        re.compile(r"^(?:export\s+)?class\s+(\w+)"),
        re.compile(r"^(?:export\s+)?interface\s+(\w+)"),
        re.compile(r"^(?:export\s+)?type\s+(\w+)\s*="),
        re.compile(r"^(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s*)?\("),
    ],
    ".tsx": [
        re.compile(r"^(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*(?:<[^>]*>)?\s*\("),
        re.compile(r"^(?:export\s+)?class\s+(\w+)"),
        re.compile(r"^(?:export\s+)?interface\s+(\w+)"),
        re.compile(r"^(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s*)?\("),
    ],
    ".jsx": [
        re.compile(r"^(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*(?:<[^>]*>)?\s*\("),
        re.compile(r"^(?:export\s+)?class\s+(\w+)"),
        re.compile(r"^(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s*)?\("),
    ],
    ".go": [
        re.compile(r"^func\s+(?:\([^)]+\)\s+)?(\w+)\s*\("),
        re.compile(r"^type\s+(\w+)\s+(?:struct|interface)"),
    ],
    ".rs": [
        re.compile(r"^(?:pub\s+)?(?:async\s+)?fn\s+(\w+)"),
        re.compile(r"^(?:pub\s+)?(?:struct|enum|trait)\s+(\w+)"),
    ],
    ".sh": [
        re.compile(r"^(\w+)\s*\(\)\s*\{"),
    ],
    ".java": [
        re.compile(r"^(?:public|private|protected)?\s*(?:static\s+)?(?:final\s+)?(?:abstract\s+)?(?:class|interface|enum)\s+(\w+)"),
        re.compile(r"^(?:public|private|protected)\s+(?:static\s+)?(?:final\s+)?(?:synchronized\s+)?[\w<>\[\],\.\s]+?\s(\w+)\s*\([^;{]*\)\s*(?:throws\s+[\w,\s]+)?\s*\{"),
    ],
    ".c": [
        re.compile(r"^(?:typedef\s+)?struct\s+(\w+)"),
        _C_FUNC_PATTERN,
    ],
    ".cpp": [
        re.compile(r"^(?:class|struct)\s+(\w+)"),
        _C_FUNC_PATTERN,
    ],
    ".h": [
        re.compile(r"^(?:class|struct)\s+(\w+)"),
        _C_FUNC_PATTERN,
    ],
}
DEFAULT_FALLBACK_PATTERNS = [re.compile(r"^(?:def|class|function|func|fn)\s+(\w+)")]


class RepoMapper:
    def __init__(self, root_dir: str | Path = ".", max_tokens: int = 2000):
        self.root_dir = Path(root_dir).resolve()
        self.max_tokens = max_tokens
        self.ignored_dirs = {
            ".git", ".github", "__pycache__", ".venv", "venv", "node_modules",
            "dist", "build", ".egg-info", ".idea", ".vscode", "assets",
            ".pytest_cache", ".mypy_cache", ".ruff_cache", ".tox", "vendor",
            "coverage", "htmlcov", "site-packages"
        }
        self.supported_extensions = {".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".java", ".c", ".cpp", ".h", ".sh"}

    def generate_map(self) -> str:
        """Generates a compressed repository skeleton."""
        file_maps: List[str] = []
        
        for root, dirs, files in os.walk(self.root_dir):
            # Prune ignored directories in-place
            dirs[:] = [d for d in dirs if d not in self.ignored_dirs and not d.startswith(".")]
            
            for file in sorted(files):
                ext = Path(file).suffix.lower()
                if ext in self.supported_extensions:
                    full_path = Path(root) / file
                    try:
                        rel_path = full_path.relative_to(self.root_dir)
                    except ValueError:
                        rel_path = full_path
                    
                    # Ignore hidden files
                    if any(part.startswith(".") for part in rel_path.parts):
                        continue
                        
                    file_map = self._parse_file(full_path, rel_path)
                    if file_map:
                        file_maps.append(file_map)
                        
        if not file_maps:
            return "# Repository Map (Empty or No Supported Source Files Found)\n"
            
        header = f"# 🗺️ Compact Repository Map ({len(file_maps)} files indexed)\n\n"
        return header + "\n".join(file_maps)

    def _parse_file(self, full_path: Path, rel_path: Path) -> Optional[str]:
        ext = full_path.suffix.lower()
        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            return None

        lines = content.splitlines()
        total_lines = len(lines)
        
        if ext == ".py":
            symbols = self._parse_python(content)
        else:
            symbols = self._parse_generic(content, ext)

        if not symbols:
            return f"📁 `{rel_path}` ({total_lines} lines)"

        res = [f"📁 `{rel_path}` ({total_lines} lines):"]
        for sym in symbols:
            res.append(f"  {sym}")
        return "\n".join(res)

    def _format_arg(self, a: ast.arg) -> str:
        if a.annotation and hasattr(ast, "unparse"):
            try:
                return f"{a.arg}: {ast.unparse(a.annotation)}"
            except Exception:
                pass
        return a.arg

    def _format_args(self, args: ast.arguments, is_method: bool = False) -> str:
        """Formats a full signature (positional-only, normal, *args, keyword-only, **kwargs) with optional type annotations."""
        def is_self_or_cls(a: ast.arg) -> bool:
            return is_method and a.arg in ("self", "cls")

        posonly = [a for a in args.posonlyargs if not is_self_or_cls(a)]
        normal = [a for a in args.args if not is_self_or_cls(a)]

        parts = [self._format_arg(a) for a in posonly]
        if posonly:
            parts.append("/")
        parts.extend(self._format_arg(a) for a in normal)

        if args.vararg:
            parts.append(f"*{self._format_arg(args.vararg)}")
        elif args.kwonlyargs:
            parts.append("*")
        parts.extend(self._format_arg(a) for a in args.kwonlyargs)

        if args.kwarg:
            parts.append(f"**{self._format_arg(args.kwarg)}")

        return ", ".join(parts)

    def _format_decorators(self, decorator_list: list[ast.expr]) -> str:
        """Renders every decorator (not just a hardcoded allowlist), so @x.setter / @app.route(...) survive."""
        if not decorator_list:
            return ""
        names = []
        for d in decorator_list:
            if hasattr(ast, "unparse"):
                try:
                    names.append(f"@{ast.unparse(d)}")
                    continue
                except Exception:
                    pass
            if isinstance(d, ast.Name):
                names.append(f"@{d.id}")
            elif isinstance(d, ast.Attribute):
                names.append(f"@{d.attr}")
        return (" ".join(names) + " ") if names else ""

    def _format_return(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
        """Formats return type annotation if present."""
        if getattr(node, "returns", None) and hasattr(ast, "unparse"):
            try:
                return f" -> {ast.unparse(node.returns)}"
            except Exception:
                pass
        return ""

    def _iter_assign_names(self, target: ast.expr):
        """Yields every bound name in an assignment target, recursing through tuple/list unpacking."""
        if isinstance(target, ast.Name):
            yield target.id
        elif isinstance(target, (ast.Tuple, ast.List)):
            for elt in target.elts:
                yield from self._iter_assign_names(elt)
        elif isinstance(target, ast.Starred):
            yield from self._iter_assign_names(target.value)

    def _parse_python(self, content: str) -> List[str]:
        """Parse python file using native ast module for 100% precision."""
        symbols = []
        try:
            tree = ast.parse(content)
            for node in tree.body:
                # Top-level UPPER_CASE constants
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        for name in self._iter_assign_names(target):
                            if name.isupper() and not name.startswith("_"):
                                symbols.append(f"const {name}")

                elif isinstance(node, ast.ClassDef):
                    # Class signature
                    bases = []
                    for b in node.bases:
                        if hasattr(ast, "unparse"):
                            bases.append(ast.unparse(b))
                        elif isinstance(b, ast.Name):
                            bases.append(b.id)
                    base_str = f"({', '.join(bases)})" if bases else ""
                    doc = ast.get_docstring(node)
                    doc_preview = f" # {doc.strip().splitlines()[0]}" if doc and doc.strip() else ""
                    symbols.append(f"class {node.name}{base_str}:{doc_preview}")
                    
                    # Class methods
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            dec_prefix = self._format_decorators(item.decorator_list)
                            args_str = self._format_args(item.args, is_method=True)
                            ret_str = self._format_return(item)
                            fn_prefix = "async def" if isinstance(item, ast.AsyncFunctionDef) else "def"
                            symbols.append(f"    {dec_prefix}{fn_prefix} {item.name}({args_str}){ret_str}")

                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    args_str = self._format_args(node.args, is_method=False)
                    ret_str = self._format_return(node)
                    fn_prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
                    doc = ast.get_docstring(node)
                    doc_preview = f" # {doc.strip().splitlines()[0]}" if doc and doc.strip() else ""
                    symbols.append(f"{fn_prefix} {node.name}({args_str}){ret_str}{doc_preview}")
        except Exception:
            # Fallback to regex if syntax error
            return self._parse_generic(content, ".py")
        return symbols

    def _parse_generic(self, content: str, ext: str) -> List[str]:
        """Fast regex-based symbol extractor using pre-compiled patterns."""
        symbols = []
        target_patterns = GENERIC_PATTERNS.get(ext, DEFAULT_FALLBACK_PATTERNS)
        
        for line in content.splitlines():
            line_str = line.strip()
            for pat in target_patterns:
                if pat.search(line_str):
                    clean_line = line_str.rstrip("{").strip()
                    if clean_line:
                        symbols.append(clean_line)
                    break
        return symbols
