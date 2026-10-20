# Project Status
**Last updated:** 2026-10-20
**Current focus:** The p-index (IIFYM: If It Fits Your Mensa), a daily protein ranking of UZH mensas + Octavo, ready to deploy to GitHub Pages.
**Where we left off:** v1 built and tested locally: scraper (food2050 + ETH Cookpit), pixel-diner single-page site with mensa skip/meh/ok/fave, kcal tax, diet filter, craving rules and shareable setup links, plus a weekday GitHub Action. Not yet a git repo or deployed.
**Next steps:**
- Decide on git init + GitHub repo `pindex` (account?) and push; set Pages source to GitHub Actions; run the workflow once.
- Optional: custom domain (e.g. pindex.ch) via a CNAME in `docs/`.
- Watch the first scheduled runs; food2050 is scraped from HTML, so a site redesign would break `scrape.py` (look for errors in the footer or a failed Action).
