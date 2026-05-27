# GitHub Copilot — DeepWiki Integration

This repository is connected to a **DeepWiki MCP Server** that gives Copilot
direct access to the pre-built knowledge graph for this codebase.
Use `@deepwiki` tools **before writing or modifying code** to understand the
existing architecture, avoid duplicating logic, and follow established patterns.

## Available tools

| Tool | When to use |
|------|-------------|
| `deepwiki_search` | Locate relevant classes or methods by intent ("how is X done?") |
| `deepwiki_get_class` | Read the wiki summary + method list for a specific class |
| `deepwiki_get_flow` | Trace a full cross-repo call chain (Angular -> API -> Spring Boot) |
| `deepwiki_get_api_consumers` | Find Angular services that call a specific REST endpoint |
| `deepwiki_get_decisions` | Understand design intent before modifying a module |

## Key facts

- `deepwiki_search` reduces token usage by **87%+** vs sending raw source files.
- The knowledge graph covers: `spring-petclinic` (Java/Spring Boot backend)
  and `angular-petclinic` (Angular 21 frontend).
- Cross-repo flow traces follow `CONSUMES` edges from Angular service calls
  to matching `APIContract` nodes and then BFS through Spring `CALLS` edges.

## Recommended workflow

1. `deepwiki_search("<what you're trying to do>")` — find the right class
2. `deepwiki_get_class("<ClassName>")` — read its wiki and method list
3. `deepwiki_get_flow("<ClassName.methodName>")` — understand call chain
4. Write or edit code informed by the retrieved context

## MCP server config

Add to your Copilot / VS Code MCP settings:

```json
{
  "mcpServers": {
    "deepwiki": {
      "url": "https://<your-railway-app>.up.railway.app/mcp",
      "transport": "streamable-http"
    }
  }
}
```

Replace `<your-railway-app>` with the actual Railway deployment URL after deploy.
