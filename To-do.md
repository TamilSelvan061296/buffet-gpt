# To-do

## Idempotency in ingestion

Each run re-parses and re-chunks every file in `src/buffet_sink/{html,pdf}/`. When embedding is wired in, this means re-embedding everything on every run — slow and costly.

Add a simple skip-if-unchanged check, e.g. cache `(path, mtime, size)` or a content hash, and only process files that have changed since the last run.

## Whole corpus held in memory

`HtmlLoader.load_html_files()` and `PdfLoader.load_pdf_files()` return `list[Document]`, and `main.py` accumulates everything into one list before chunking. Fine for ~50 Berkshire letters; falls apart once we add 10-Ks, transcripts, or other sources.

Switch the loader contract to a generator (`Iterator[Document]`) so load → chunk → embed can stream end-to-end without holding the full corpus in memory at any point.
