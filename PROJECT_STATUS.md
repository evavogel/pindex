# Project Status
**Last updated:** 2026-10-20
**Current focus:** The p-index (IIFYM: If It Fits Your Mensa), a daily protein ranking of UZH mensas + Octavo, live at https://emvogel.com/pindex/.
**Where we left off:** v1 is live on GitHub Pages (repo evavogel/pindex), refreshed by a weekday GitHub Action (05:30/09:45 CET). A claude.ai snapshot also exists (https://claude.ai/artifact/6VdWMypf6wHmzYyFTjNPAx) but does not update. An independent LLM macro estimate was considered and dropped (needs a paid API key).
**Next steps:**
- Watch the first scheduled runs; food2050 is scraped from HTML, so a site redesign would break `scrape.py` (look for a failed Action or errors in the site footer).
- Optional no-API sanity check: flag dishes whose kcal disagree with 4·protein + 4·carbs + 9·fat.
