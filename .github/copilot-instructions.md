# GitHub Copilot Instructions — TradingView MCP

## Workspace Directory Placement Rules

- **Scripts**: Put all utility scripts, backtest runners, data downloaders, and analysis programs (`.py`, `.mjs`, `.js`, `.sh`, `.c`) in `scripts/`. Never create scripts in the root directory.
- **Reports & Data**: Put all reports (`.md`), backtest outputs (`.json`, `.csv`, `.bin`), market bar datasets, and Pine Script files (`.pine`) in `reports/`. Always set output paths in code to `reports/<filename>`.
- **Screenshots**: Save all chart captures and screenshots in `screenshots/`.
- **Root Directory**: Keep the repository root clean. Only core MCP server configuration and documentation belong in root.
