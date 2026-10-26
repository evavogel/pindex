# Project Status
**Last updated:** 2026-10-26
**Current focus:** The p-index (IIFYM: If It Fits Your Mensa), a daily protein ranking of 27 UZH and ETH mensas (incl. Octavo), live at https://emvogel.com/pindex/.
**Where we left off:** Live on GitHub Pages (repo evavogel/pindex) with week cards, Samuel bonus (+100 for Octavo and Schnitzel), a served-day archive (`docs/data/history.csv`, from 2026-10-20) and a Hall of Fame (avg protein/fat/kcal per mensa). food2050 throttled us after many test scrapes on 2026-10-20, so the scraper now reuses known dish pages, keeps last known menus on failure, and pushes only redeploy.
**Next steps:**
- GitHub started last week's scheduled runs about 5 hours late; since 2026-10-26 there are four weekday slots (04:17, 06:23, 08:37, 10:41 CET). Check that one lands before lunch; if not, trigger by hand (Actions -> Run workflow).
- food&lab and Mendokoro published no menu for the week of 2026-10-26 (Mendokoro's standing menu ended 2026-10-25).
- Optional: pindex.emvogel.com needs one CNAME record at Namecheap (host `pindex` → `evavogel.github.io.`), then set the custom domain on the repo.
- ETH/Octavo publish per-100 g values only; they are scaled to the median food2050 plate (548 g), which likely overstates light dishes (e.g. Salat Bowl ≈50 g protein). Consider a per-kitchen portion or a user setting.
- Optional: limit the Samuel bonus to meat Schnitzel (Gemüseschnitzel currently matches).
- Optional no-API sanity check: flag dishes whose kcal disagree with 4·protein + 4·carbs + 9·fat.
