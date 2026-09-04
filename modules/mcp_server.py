"""agyswap.modules.mcp_server — Modern Stateless Model Context Protocol (MCP) Server.

Implements the 2026 Stateless MCP specification:
  - 100% Stateless: No mandatory handshake, no session affinity/sticky connections.
  - Self-Describing: Every request can execute independently without prior initialize state.
  - Dual-Mode Transport:
      1. stdio (default): Line-delimited JSON-RPC 2.0 with instant tool execution.
      2. HTTP (--http [port]): Zero-dependency lightweight HTTP JSON-RPC endpoint.
"""
from __future__ import annotations

import sys
import json
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Dict, Any, List, Optional

PROTOCOL_VERSION = "2026-07-28"
SERVER_NAME = "agyswap-stateless-mcp"
SERVER_VERSION = "0.6.0"

# Standard MCP Tool Definitions
TOOLS_SCHEMA = [
    {
        "name": "agyswap_list_accounts",
        "description": "Lists all registered Google Antigravity account profiles in agyswap, including slot numbers, email addresses, aliases, active status, and token expiration information.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "agyswap_get_quota",
        "description": "Checks real-time per-model Gemini API quota (remaining percentage, reset time) for the active account or a specific target slot/email.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "Optional slot number, email, or alias. Defaults to the active account.",
                },
                "refresh": {
                    "type": "boolean",
                    "description": "If true, bypasses the TTL cache and forces a live API re-fetch.",
                    "default": False,
                },
            },
        },
    },
    {
        "name": "agyswap_switch_account",
        "description": "Switches the active Google Antigravity profile in macOS Keychain to a specific slot/alias or rotates to the next available account.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "Optional slot number, email, or alias. If omitted, rotates to the next non-disabled account.",
                },
                "force": {
                    "type": "boolean",
                    "description": "If true, forces switch even if the token is expired.",
                    "default": False,
                },
                "compact_context": {
                    "type": "boolean",
                    "description": "If true, automatically synchronizes a 96% compressed AST repository map and state before switching.",
                    "default": True,
                },
            },
        },
    },
    {
        "name": "agyswap_rotate_token",
        "description": "Refreshes OAuth credentials using stored Google refresh tokens in the background (no browser interaction required).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "Optional slot number, email, or alias to refresh. Defaults to active account.",
                },
                "all": {
                    "type": "boolean",
                    "description": "If true, refreshes tokens for all registered accounts.",
                    "default": False,
                },
            },
        },
    },
    {
        "name": "agyswap_compact_context",
        "description": "Generates a 96% token-compressed AST repository map (REPO_MAP.md) and working state snapshot (STATE.md) into .agents/memory/ to prevent token bloat.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "budget": {
                    "type": "integer",
                    "description": "Maximum token budget for the repository map (default: 2000).",
                    "default": 2000,
                },
                "goal": {
                    "type": "string",
                    "description": "Description of the current task or working goal.",
                    "default": "Active Development",
                },
            },
        },
    },
]


def tool_list_accounts(arguments: Dict[str, Any]) -> str:
    import agyswap

    cfg = agyswap.StorageManager.load_config()
    accounts = cfg.get("accounts", [])
    active_slot = cfg.get("active_slot")

    result = {
        "active_slot": active_slot,
        "total_accounts": len(accounts),
        "accounts": [],
    }

    for acc in accounts:
        s_num = acc.get("slot")
        exp_time, exp_rel, is_expired, is_soon = ("Unknown", "", False, False)
        try:
            sdata = agyswap.StorageManager.load_slot(s_num)
            exp_raw = sdata.get("token", {}).get("expiry", "")
            exp_time, exp_rel, is_expired, is_soon = agyswap.format_expiry_detail(exp_raw)
        except Exception:
            pass

        result["accounts"].append({
            "slot": s_num,
            "email": acc.get("email"),
            "alias": acc.get("alias") or None,
            "is_active": (s_num == active_slot),
            "disabled": acc.get("disabled", False),
            "last_used_at": acc.get("last_used_at"),
            "token_status": {
                "is_expired": is_expired,
                "is_soon": is_soon,
                "expiry_time": exp_time,
                "relative": exp_rel,
            },
        })

    return json.dumps(result, indent=2, ensure_ascii=False)


def tool_get_quota(arguments: Dict[str, Any]) -> str:
    import agyswap
    import modules.quota as quota

    target = arguments.get("target")
    refresh = arguments.get("refresh", False)

    cfg = agyswap.StorageManager.load_config()
    accounts = cfg.get("accounts", [])
    if not accounts:
        return json.dumps({"error": "No registered accounts found."})

    target_accs = []
    if target:
        found = agyswap.find_account(accounts, str(target).strip())
        if not found:
            return json.dumps({"error": f"Account '{target}' not found."})
        target_accs.append(found)
    else:
        active_slot = cfg.get("active_slot")
        found = next((a for a in accounts if a.get("slot") == active_slot), None)
        if found:
            target_accs.append(found)
        else:
            target_accs = [a for a in accounts if not a.get("disabled", False)]

    results = {}
    for acc in target_accs:
        s_num = acc.get("slot")
        email = acc.get("email")
        try:
            sdata = agyswap.StorageManager.load_slot(s_num)
            access_token = sdata.get("token", {}).get("access_token")
            if not access_token:
                results[email] = {"error": "Missing access token"}
                continue
            entry = quota.fetch_for_account(email, access_token, force=refresh)
            results[email] = {
                "slot": s_num,
                "alias": acc.get("alias") or None,
                "fetched_at": entry.get("fetched_at"),
                "stale": entry.get("stale", False),
                "models": entry.get("models", {}),
            }
        except Exception as e:
            results[email] = {"slot": s_num, "error": str(e)}

    return json.dumps(results, indent=2, ensure_ascii=False)


def tool_switch_account(arguments: Dict[str, Any]) -> str:
    import agyswap

    target = arguments.get("target")
    force = arguments.get("force", False)
    compact_ctx = arguments.get("compact_context", True)

    cfg = agyswap.StorageManager.load_config()
    accounts = cfg.get("accounts", [])
    if not accounts:
        return json.dumps({"error": "No registered accounts found."})

    if compact_ctx:
        try:
            agyswap.cmd_context(
                agyswap.argparse.Namespace(
                    ctx_action="clean",
                    dir=".",
                    budget=2000,
                    goal="Switched account via Stateless MCP tool",
                )
            )
        except Exception:
            pass

    try:
        agyswap.cmd_switch(
            agyswap.argparse.Namespace(
                target=str(target).strip() if target is not None else None,
                dry_run=False,
                force=force,
                resume=False,
                new_session=False,
                dangerously_skip_permissions=False,
                ctx=False,
            )
        )
        updated_cfg = agyswap.StorageManager.load_config()
        active_slot = updated_cfg.get("active_slot")
        active_acc = next((a for a in updated_cfg.get("accounts", []) if a.get("slot") == active_slot), None)
        return json.dumps({
            "status": "success",
            "active_slot": active_slot,
            "email": active_acc.get("email") if active_acc else None,
            "alias": active_acc.get("alias") if active_acc else None,
            "message": f"Successfully switched to Slot #{active_slot}.",
        }, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})


def tool_rotate_token(arguments: Dict[str, Any]) -> str:
    import agyswap

    target = arguments.get("target")
    refresh_all = arguments.get("all", False)

    try:
        if refresh_all:
            agyswap.cmd_rotate(agyswap.argparse.Namespace(target=None, all=True))
            return json.dumps({"status": "success", "message": "Triggered background token rotation for all accounts."})
        else:
            agyswap.cmd_rotate(agyswap.argparse.Namespace(target=str(target).strip() if target else None, all=False))
            return json.dumps({"status": "success", "message": f"Refreshed token for target: {target or 'active slot'}."})
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})


def tool_compact_context(arguments: Dict[str, Any]) -> str:
    import agyswap

    budget = arguments.get("budget", 2000)
    goal = arguments.get("goal", "Active Development")

    try:
        agyswap.cmd_context(
            agyswap.argparse.Namespace(
                ctx_action="clean",
                dir=".",
                budget=budget,
                goal=goal,
            )
        )
        return json.dumps({
            "status": "success",
            "message": "Repository AST map and state snapshot successfully synced to .agents/memory/",
            "budget": budget,
            "goal": goal,
        }, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})


TOOL_DISPATCH = {
    "agyswap_list_accounts": tool_list_accounts,
    "agyswap_get_quota": tool_get_quota,
    "agyswap_switch_account": tool_switch_account,
    "agyswap_rotate_token": tool_rotate_token,
    "agyswap_compact_context": tool_compact_context,
}


def dispatch_mcp_request(req: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Stateless MCP Request Dispatcher.

    Does not require an 'initialize' call to precede other requests.
    Every request is completely self-contained and stateless.
    """
    req_id = req.get("id")
    method = req.get("method")
    params = req.get("params", {})

    # Self-describing handshake (optional in 2026 Stateless spec, but fully supported for backward compat)
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": PROTOCOL_VERSION,
                "serverInfo": {
                    "name": SERVER_NAME,
                    "version": SERVER_VERSION,
                },
                "capabilities": {
                    "stateless": True,
                    "tools": {},
                },
            },
        }

    elif method in ("notifications/initialized", "initialized"):
        return None

    elif method == "ping":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {},
        }

    # Stateless Tool Discovery
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": TOOLS_SCHEMA,
            },
        }

    # Stateless Tool Execution
    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        fn = TOOL_DISPATCH.get(tool_name)

        if not fn:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32601,
                    "message": f"Tool '{tool_name}' not found.",
                },
            }

        try:
            content_text = fn(arguments)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": content_text,
                        }
                    ],
                },
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "isError": True,
                    "content": [
                        {
                            "type": "text",
                            "text": f"Error executing {tool_name}: {e}\n{traceback.format_exc()}",
                        }
                    ],
                },
            }

    else:
        if req_id is not None:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32601,
                    "message": f"Method '{method}' not found.",
                },
            }
        return None


class StatelessMCPServer:
    """Stateless MCP Server running over stdio (line-delimited JSON-RPC)."""

    def run_stdio(self):
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                req = json.loads(line)
                resp = dispatch_mcp_request(req)
                if resp is not None:
                    sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
                    sys.stdout.flush()
            except Exception as e:
                err_resp = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": f"Parse error: {e}",
                    },
                }
                sys.stdout.write(json.dumps(err_resp) + "\n")
                sys.stdout.flush()


class StatelessMCPHTTPHandler(BaseHTTPRequestHandler):
    """Zero-dependency HTTP Handler for Stateless MCP over HTTP."""

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        # Allow routing via header if present (2026 spec feature)
        mcp_method = self.headers.get("Mcp-Method")

        try:
            req = json.loads(body.decode("utf-8"))
            if mcp_method and "method" not in req:
                req["method"] = mcp_method

            resp = dispatch_mcp_request(req)
            resp_body = json.dumps(resp, ensure_ascii=False).encode("utf-8") if resp else b"{}"

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Mcp-Server", f"{SERVER_NAME}/{SERVER_VERSION}")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(resp_body)))
            self.end_headers()
            self.wfile.write(resp_body)
        except Exception as e:
            err_body = json.dumps({
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Invalid JSON-RPC payload: {e}"},
            }).encode("utf-8")
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(err_body)))
            self.end_headers()
            self.wfile.write(err_body)

    def do_OPTIONS(self):
        """CORS pre-flight support for browser-based AI environments."""
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Mcp-Method, Mcp-Name")
        self.end_headers()

    def log_message(self, format, *args):
        # Suppress noisy HTTP request logging to keep console clean
        pass


def run_http_server(host: str = "127.0.0.1", port: int = 8765):
    """Starts a lightweight stateless HTTP MCP endpoint."""
    server = HTTPServer((host, port), StatelessMCPHTTPHandler)
    print(f"🌐 [agyswap stateless mcp] Listening on http://{host}:{port}/mcp (Press Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Stopped MCP HTTP server.")
    finally:
        server.server_close()
