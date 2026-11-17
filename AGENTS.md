# Agent Instructions — TradingView MCP

This file provides instructions for all AI agents, assistants, and automated systems (including Antigravity, Gemini, OpenAI Codex, Cline, and other autonomous agents) operating within this repository.

## Strict Workspace Organization & File Placement Rules

To prevent repository clutter and keep the project structured, all AI agents MUST strictly adhere to the following file placement rules:

### 1. Working Scripts & Runners → `scripts/`
- **Target Directory:** `scripts/`
- Place **all** working scripts, data scrapers, bar extractors, simulation engines, backtest routines, optimization scripts, and runner tools here.
- Applies to all languages: Python (`.py`), Node.js (`.js`, `.mjs`), Bash/Shell (`.sh`), C (`.c`), etc.
- **Rule:** Never save execution scripts directly in the project root directory.

### 2. Reports, Datasets & Strategy Artifacts → `reports/`
- **Target Directory:** `reports/`
- **Written Reports:** Save all analysis documents, backtest review markdown files, risk models, and comparative audits (`.md`) in `reports/`.
- **Results & Data:** Save all backtest outcome files, optimization summaries, combinatorial permutation results, and databases (`.json`, `.csv`, `.bin`) in `reports/`.
- **Pine Scripts:** Save all TradingView Pine Script indicators, strategies, and libraries (`.pine`) in `reports/`.
- **Historical Market Bars:** Save all exported OHLCV bar datasets (`.csv`, `.json`) in `reports/`.
- **Path Precaution in Code:** When generating files programmatically from scripts, **always** use explicit paths pointing into `reports/` (e.g., `open('reports/results.json', 'w')` or `df.to_csv('reports/matrix.csv')`), never `./results.json`.

### 3. Screenshots → `screenshots/`
- **Target Directory:** `screenshots/`
- All visual charts and automated snapshots taken via `capture_screenshot` or Chrome DevTools Protocol must be stored in `screenshots/`.

### 4. Root Directory Preservation
- The root directory (`./`) is reserved strictly for core repository configuration and manifests:
  - `package.json`, `package-lock.json`, `eslint.config.mjs`
  - Documentation: `README.md`, `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`, `SETUP_GUIDE.md`, `RESEARCH.md`
  - Instruction files: `AGENTS.md`, `CLAUDE.md`, `.cursorrules`
  - Top-level subdirectories: `src/`, `tests/`, `scripts/`, `reports/`, `screenshots/`, `agents/`, `skills/`
- **Rule:** Do NOT write loose output files, datasets, or scripts into the root folder.
