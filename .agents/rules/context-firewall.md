---
trigger: always_on
---

# 🛡️ Context Firewall & Token Budget Policy

This policy strictly enforces token-efficiency to prevent context bloat and rate-limit exhaustion in Antigravity sessions.

## 1. File Inspection (Slice-First)
- **NEVER** view full files exceeding 80 lines without `StartLine`/`EndLine` ranges.
- Always check the compact repository map (`.agents/memory/REPO_MAP.md` or run `agyswap ctx map`) before searching or reading raw code.

## 2. Command Output Sanitization
- For terminal commands with potentially long outputs (`git log`, `pytest`, `find`, `cat`), always pipe through `head`, `tail`, or `grep` (e.g. `pytest | tail -n 20`).

## 3. Subagent Offloading
- If a task involves searching 3+ files or comprehensive codebase exploration, delegate to a background subagent (`invoke_subagent` with type `research`).

## 4. State Continuity
- Read `.agents/memory/STATE.md` to restore working context instantly with < 200 tokens.
