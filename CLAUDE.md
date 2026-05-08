# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

A chatbot that emulates Warren Buffett, grounded in his annual Berkshire Hathaway shareholder letters (1977–2024). Early scaffolding stage: the corpus is downloaded but ingestion / retrieval / chat are not yet implemented.

## Tooling

Python 3.12+, managed with [uv](https://docs.astral.sh/uv/). `uv.lock` is checked in.

```bash
uv sync                    # install deps from uv.lock
uv run python main.py      # run entrypoint
uv add <pkg>               # add a dependency (updates pyproject.toml + uv.lock)
```

There is no test suite, linter, or formatter configured yet — don't invent commands for these.

## Layout and data flow

- `main.py` — placeholder entrypoint, prints a hello string.
- `src/scripts/scrape_letters.py` — one-shot scraper that pulls every annual letter from `berkshirehathaway.com/letters/letters.html` and saves them. It handles the 1998–2003 stub "landing pages" by following the inner PDF/HTML link, and uses windows-1252 decoding because the index page is served that way. Run with `uv run python src/scripts/scrape_letters.py`.
- `src/scripts/data_ingestor.py` — empty `html_loader` / `pdf_loader` class stubs intended to wrap LangChain document loaders. Not implemented.
- `src/buffet_sink/html/` — letters 1977–1997 as HTML.
- `src/buffet_sink/pdf/` — letters 1998–2024 as PDF.

**Note on the scraper output path:** `scrape_letters.py` writes to `src/scripts/letters/` (its `OUT_DIR`), but the curated corpus lives at `src/buffet_sink/{html,pdf}/`. The `buffet_sink` tree is the source of truth for ingestion; re-running the scraper will not overwrite it. If you need to refresh the corpus, either point ingestion at `src/scripts/letters/` or update `OUT_DIR` to write into `src/buffet_sink/`.

The split by year (HTML vs PDF) reflects how Berkshire publishes them — early years are HTML, later years are PDF — so any ingestion code must handle both formats.
