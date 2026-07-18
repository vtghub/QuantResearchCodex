# MCP-native-core Developer Tooling

`vtghub/MCP-native-core` is developer-only AI tooling for codebase inspection. It is not a production dependency for the QuantResearchCodex platform.

## Pin

- Repository: `https://github.com/vtghub/MCP-native-core`
- Commit: `16888c0566e27cb10c589b73e68351136b7d1b5d`

## Intended Use

- Build the Rust MCP server locally.
- Configure its `fast_search` and `parse_structure` tools for coding-agent inspection of this workspace.
- Keep `rg`, Python type checking, TypeScript type checking, and language-native parsers as fallbacks.

## Guardrails

- Do not import MCP-native-core from application code.
- Do not require it in Docker images, Helm charts, Terraform, or CI.
- Do not use it to store credentials, trading data, broker tokens, or vendor data.
