# GitHub Copilot Instructions — TradingView MCP

## Strict TradingView Tool Usage & Screenshot Restrictions

- **No Autonomous Probing**: Do NOT query TradingView Desktop or call TradingView MCP tools unless the user explicitly requests chart interaction.
- **NEVER Take Screenshots Unless Asked**: NEVER call `capture_screenshot` or trigger printscreen unless the user explicitly asks for a screenshot or image. Do not take screenshots as an automatic confirmation or routine step.
- **No Unsolicited Calculations / Audits**: When asked to check TradingView, retrieve only the specific item requested. Do NOT autonomously chain multiple tools, scrape all indicators, pull bar histories, or run heavy calculations. Keep responses fast, concise, and minimal.

## Workspace Directory Placement Rules

- **Scripts**: Put all utility scripts, backtest runners, data downloaders, and analysis programs (`.py`, `.mjs`, `.js`, `.sh`, `.c`) in `scripts/`. Never create scripts in the root directory.
- **Reports & Data**: Put all reports (`.md`), backtest outputs (`.json`, `.csv`, `.bin`), market bar datasets, and Pine Script files (`.pine`) in `reports/`. Always set output paths in code to `reports/<filename>`.
- **Screenshots**: Save all chart captures and screenshots in `screenshots/`.
- **Root Directory**: Keep the repository root clean. Only core MCP server configuration and documentation belong in root.
