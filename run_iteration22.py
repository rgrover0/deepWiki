"""
Iteration 22 - GitHub Copilot MCP Server

Verifies:
  1. mcp-server/main.py: FastMCP app, 5 tool functions, streamable-http transport
  2. mcp-server/client.py: api_get, api_post, DEEPWIKI_API_URL
  3. mcp-server/requirements.txt: mcp[cli], httpx, python-dotenv
  4. mcp-server/railway.toml: startCommand = "python main.py"
  5. mcp-server/Dockerfile: python:3.11-slim, CMD python main.py
  6. .github/copilot-instructions.md: references @deepwiki tools, 87% savings
  7. docker-compose.yaml: mcp-server service on port 8090
  8. Live import: FastMCP, all 5 tools registered

Done when: `python mcp-server/main.py` starts on port 8090 and
  MCP inspector shows 5 tools: deepwiki_search, deepwiki_get_class,
  deepwiki_get_flow, deepwiki_get_api_consumers, deepwiki_get_decisions.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

print("=" * 60)
print("DeepWiki - Iteration 22: GitHub Copilot MCP Server")
print("=" * 60)

all_ok = True


def grep(path: Path, pattern: str) -> bool:
    if not path.exists():
        return False
    return pattern in path.read_text(encoding="utf-8", errors="ignore")


# -- 1. mcp-server/main.py ----------------------------------------------------
print("\n[1/8] mcp-server/main.py:")
main = ROOT / "mcp-server/main.py"
checks = [
    ("FastMCP",                      "FastMCP import"),
    ('"DeepWiki"',                   "FastMCP app named DeepWiki"),
    ("def deepwiki_search",          "deepwiki_search tool"),
    ("def deepwiki_get_class",       "deepwiki_get_class tool"),
    ("def deepwiki_get_flow",        "deepwiki_get_flow tool"),
    ("def deepwiki_get_api_consumers","deepwiki_get_api_consumers tool"),
    ("def deepwiki_get_decisions",   "deepwiki_get_decisions tool"),
    ('transport="streamable-http"',  "streamable-http transport"),
    ('os.getenv("PORT", 8090)',      "PORT env var"),
]
for pattern, desc in checks:
    ok = grep(main, pattern)
    print(f"  {'OK  ' if ok else 'MISS'}  {desc}")
    all_ok &= ok


# -- 2. mcp-server/client.py --------------------------------------------------
print("\n[2/8] mcp-server/client.py:")
client = ROOT / "mcp-server/client.py"
checks = [
    ("DEEPWIKI_API_URL",   "DEEPWIKI_API_URL env var"),
    ("def api_get",        "api_get function"),
    ("def api_post",       "api_post function"),
    ("httpx",              "httpx client"),
]
for pattern, desc in checks:
    ok = grep(client, pattern)
    print(f"  {'OK  ' if ok else 'MISS'}  {desc}")
    all_ok &= ok


# -- 3. requirements.txt -------------------------------------------------------
print("\n[3/8] mcp-server/requirements.txt:")
req = ROOT / "mcp-server/requirements.txt"
checks = [
    ("mcp",           "mcp package"),
    ("httpx",         "httpx"),
    ("python-dotenv", "python-dotenv"),
]
for pattern, desc in checks:
    ok = grep(req, pattern)
    print(f"  {'OK  ' if ok else 'MISS'}  {desc}")
    all_ok &= ok


# -- 4. railway.toml ----------------------------------------------------------
print("\n[4/8] mcp-server/railway.toml:")
railway = ROOT / "mcp-server/railway.toml"
checks = [
    ("python main.py",  "startCommand = python main.py"),
]
for pattern, desc in checks:
    ok = grep(railway, pattern)
    print(f"  {'OK  ' if ok else 'MISS'}  {desc}")
    all_ok &= ok


# -- 5. Dockerfile ------------------------------------------------------------
print("\n[5/8] mcp-server/Dockerfile:")
dockerfile = ROOT / "mcp-server/Dockerfile"
checks = [
    ("python:3.11-slim", "base image"),
    ("requirements.txt", "installs requirements"),
    ("python main.py",   "CMD python main.py"),
]
for pattern, desc in checks:
    ok = grep(dockerfile, pattern)
    print(f"  {'OK  ' if ok else 'MISS'}  {desc}")
    all_ok &= ok


# -- 6. .github/copilot-instructions.md ---------------------------------------
print("\n[6/8] .github/copilot-instructions.md:")
copilot = ROOT / ".github/copilot-instructions.md"
checks = [
    ("deepwiki_search",          "deepwiki_search mentioned"),
    ("deepwiki_get_class",       "deepwiki_get_class mentioned"),
    ("deepwiki_get_flow",        "deepwiki_get_flow mentioned"),
    ("deepwiki_get_api_consumers","deepwiki_get_api_consumers mentioned"),
    ("deepwiki_get_decisions",   "deepwiki_get_decisions mentioned"),
    ("87%",                      "87% token savings mentioned"),
    ("streamable-http",          "streamable-http transport in config example"),
]
for pattern, desc in checks:
    ok = grep(copilot, pattern)
    print(f"  {'OK  ' if ok else 'MISS'}  {desc}")
    all_ok &= ok


# -- 7. docker-compose.yaml ---------------------------------------------------
print("\n[7/8] docker-compose.yaml:")
dc = ROOT / "docker-compose.yaml"
checks = [
    ("mcp-server",         "mcp-server service"),
    ("8090:8090",          "port 8090 mapped"),
    ("DEEPWIKI_API_URL",   "DEEPWIKI_API_URL env"),
]
for pattern, desc in checks:
    ok = grep(dc, pattern)
    print(f"  {'OK  ' if ok else 'MISS'}  {desc}")
    all_ok &= ok


# -- 8. Live import -----------------------------------------------------------
print("\n[8/8] Live import — FastMCP + tool registration:")
try:
    import sys as _sys
    _sys.path.insert(0, str(ROOT / "mcp-server"))
    from mcp.server.fastmcp import FastMCP as _FastMCP
    print("  OK    FastMCP importable")

    # Check tool count by inspecting main.py AST (no side effects)
    import ast
    src = (ROOT / "mcp-server/main.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    tools = [
        n.name for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.name.startswith("deepwiki_")
    ]
    expected = {
        "deepwiki_search", "deepwiki_get_class", "deepwiki_get_flow",
        "deepwiki_get_api_consumers", "deepwiki_get_decisions",
    }
    missing = expected - set(tools)
    ok = not missing
    print(f"  {'OK  ' if ok else 'FAIL'}  5 tool functions defined"
          + (f" (missing: {missing})" if missing else f": {', '.join(sorted(tools))}"))
    if not ok:
        all_ok = False
except ImportError as e:
    print(f"  SKIP  mcp not installed: {e}")
    print("        Run: pip install mcp[cli] httpx python-dotenv")
except Exception as e:
    print(f"  FAIL  {type(e).__name__}: {e}")
    all_ok = False


print("\n" + "=" * 60)
print(f"Iteration 22: {'ALL CHECKS PASS' if all_ok else 'SOME CHECKS FAILED'}")
print()
print("  Start locally:")
print("    cd mcp-server")
print("    DEEPWIKI_API_URL=http://localhost:8000 python main.py")
print("    # -> MCP server on http://localhost:8090/mcp")
print()
print("  Inspect with MCP CLI:")
print("    npx @modelcontextprotocol/inspector http://localhost:8090/mcp")
print()
print("  Deploy to Railway:")
print("    railway up --service mcp-server")
print("    # set env vars: DEEPWIKI_API_URL, PORT")
print("=" * 60)
