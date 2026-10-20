# Project Status
**Last updated:** 2026-10-20
**Current focus:** The p-index (IIFYM: If It Fits Your Mensa), a daily protein ranking of UZH mensas + Octavo, live at https://emvogel.com/pindex/.
**Where we left off:** Live on GitHub Pages (repo evavogel/pindex) with week cards, Samuel bonus (+100 for Octavo and Schnitzel), a served-day archive (`docs/data/history.csv`, from 2026-10-20) and a Hall of Fame (avg protein/fat/kcal per mensa). food2050 throttled us after many test scrapes on 2026-10-20, so the scraper now reuses known dish pages, keeps last known menus on failure, and pushes only redeploy.
**Next steps:**
- Check the first scheduled runs (2026-10-21, 05:30 and 09:45 CEST) in the Actions tab; the footer names any mensa that fell back to its last known menu.
- Optional: pindex.emvogel.com needs one CNAME record at Namecheap (host `pindex` → `evavogel.github.io.`), then set the custom domain on the repo.
- Optional: limit the Samuel bonus to meat Schnitzel (Gemüseschnitzel currently matches).
- Optional no-API sanity check: flag dishes whose kcal disagree with 4·protein + 4·carbs + 9·fat.
