import unittest
import tempfile
from pathlib import Path
from modules.context.repomap import RepoMapper
from modules.context.budgeter import TokenBudgeter
from modules.context.state import StateManager

class TestContextModule(unittest.TestCase):
    def test_token_budgeter_boundaries(self):
        self.assertEqual(TokenBudgeter.estimate_tokens(""), 0)
        self.assertEqual(TokenBudgeter.trim_to_budget("short text", 100), "short text")
        
        long_text = "\n".join([f"line_{i} = {i}" for i in range(100)])
        trimmed = TokenBudgeter.trim_to_budget(long_text, max_tokens=20)
        self.assertIn("Truncated", trimmed)

    def test_repomap_python_ast_and_decorators(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sample_py = Path(tmpdir) / "engine.py"
            sample_py.write_text(
                'MAX_RETRIES = 5\n'
                '_INTERNAL_VAL = 10\n\n'
                'class CoreEngine(BaseModule):\n'
                '    """Main engine class."""\n'
                '    @property\n'
                '    def is_active(self):\n'
                '        return True\n\n'
                '    @staticmethod\n'
                '    def ping(host: str):\n'
                '        pass\n\n'
                '    async def execute(self, task):\n'
                '        pass\n'
            )
            mapper = RepoMapper(root_dir=tmpdir)
            repo_map = mapper.generate_map()
            self.assertIn("const MAX_RETRIES", repo_map)
            self.assertNotIn("_INTERNAL_VAL", repo_map)
            self.assertIn("class CoreEngine(BaseModule):", repo_map)
            self.assertIn("@property def is_active()", repo_map)
            self.assertIn("@staticmethod def ping(host: str)", repo_map)
            self.assertIn("async def execute(task)", repo_map)

    def test_repomap_generic_fallback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sample_ts = Path(tmpdir) / "service.ts"
            sample_ts.write_text(
                'export class AuthService {\n'
                '  export async function verifyToken(token: string) {\n'
                '  }\n'
                '}\n'
            )
            mapper = RepoMapper(root_dir=tmpdir)
            repo_map = mapper.generate_map()
            self.assertIn("📁 `service.ts`", repo_map)
            self.assertIn("export class AuthService", repo_map)
            self.assertIn("export async function verifyToken", repo_map)

    def test_state_manager_save_and_permissions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_mgr = StateManager(root_dir=tmpdir)
            out_file = state_mgr.save_snapshot(goal="Testing Snapshots & Security")
            self.assertTrue(out_file.exists())
            content = out_file.read_text(encoding="utf-8")
            self.assertIn("Working State Snapshot", content)
            self.assertIn("Testing Snapshots & Security", content)

    def test_context_benchmarker(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sample_py = Path(tmpdir) / "app.py"
            sample_py.write_text("class Server:\n    def run(self):\n        pass\n" * 20)
            from modules.context.benchmarker import ContextBenchmarker
            bench = ContextBenchmarker(root_dir=tmpdir)
            stats = bench.run_benchmark(budget=500)
            self.assertEqual(stats["raw_files"], 1)
            self.assertGreater(stats["raw_tokens"], 0)
            self.assertGreater(stats["reduction_pct"], 0)
            
            # ASCII report
            report = ContextBenchmarker.render_cli_report(stats)
            self.assertIn("Compression Benchmark", report)
            
            # JSON report
            json_report = ContextBenchmarker.render_json(stats)
            self.assertIn('"reduction_pct"', json_report)
            
            # Markdown report
            md_report = ContextBenchmarker.render_markdown(stats)
            self.assertIn("### 📊 agyswap Context Compression Benchmark", md_report)
            self.assertIn("Token_Savings", md_report)

    def test_context_benchmarker_empty_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from modules.context.benchmarker import ContextBenchmarker
            bench = ContextBenchmarker(root_dir=tmpdir)
            stats = bench.run_benchmark(budget=500)
            self.assertEqual(stats["raw_files"], 0)
            self.assertEqual(stats["raw_tokens"], 0)
            self.assertEqual(stats["reduction_pct"], 0.0)
            report = ContextBenchmarker.render_cli_report(stats)
            self.assertIn("Indexed Files      : 0", report)

    def test_golden_benchmark_regression(self):
        """Regression test ensuring 100% symbol recall and > 65% compression on standard testset."""
        from modules.context.benchmarker import ContextBenchmarker
        stats = ContextBenchmarker.run_golden_benchmark()
        self.assertGreaterEqual(stats["raw_files"], 6)
        self.assertGreater(stats["expected_symbols_count"], 20)
        self.assertEqual(stats["recall_pct"], 100.0, f"Missing symbols: {stats.get('missing_symbols')}")
        self.assertGreater(stats["reduction_pct"], 65.0)
        self.assertLess(stats["latency_ms"], 50.0)  # sub-50ms execution
        report = ContextBenchmarker.render_golden_report(stats)
        self.assertIn("Golden Quality & Context Benchmark", report)

if __name__ == "__main__":
    unittest.main()
