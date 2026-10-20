# The p-index

**IIFYM: If It Fits Your Mensa.** A pixel-diner dashboard that ranks today's lunch at the UZH mensas (plus Octavo) by protein, with your own mensa preferences and food cravings layered on top.

Live: **https://emvogel.com/pindex/** (also reachable via https://evavogel.github.io/pindex/).

## How it works

- `scrape.py` fetches the rest of this week's lunch menus for every mensa in `mensas.json` and writes `docs/data/menus.json`. Standard library only.
  - UZH mensas (ZFV): the food2050 weekly page lists dishes, and each dish page gives nutrition per portion, weight, prices and allergens.
  - Octavo: the ETH Cookpit API (facility 23), which publishes nutrition per 100 g only. Per-portion values are scaled to the median food2050 portion weight of the same run and marked as estimates.
- `docs/data/history.csv` archives every served day: one row per dish with macros, weight and prices (`estimated` = Octavo's scaled values). Rankings are not stored, since they depend on each visitor's house rules.
- `docs/index.html` is the whole site (HTML, CSS, JS and the pixel sprites). It reads `data/menus.json` and stores each visitor's settings in their own browser.
- `.github/workflows/update-menus.yml` runs the scraper on weekday mornings, commits the data and deploys `docs/` to GitHub Pages.

**p-index** of a dish = protein (g) − kcal tax (points per 100 kcal) ± mensa bias (fave/meh) + matching craving rules. Each mensa is ranked by its best dish.

## Deployment

Repository `evavogel/pindex`, Pages source **GitHub Actions**. Every push to `main` and every scheduled run scrapes, commits `docs/data/` (menus and history) and deploys. To refresh by hand: *Actions → Update menus and deploy → Run workflow*.

Scheduled workflows pause after 60 days without repository activity. The daily data commit keeps the repository active.

## Local

```bash
python scrape.py
python -m http.server 8765 --directory docs
```

Then open http://localhost:8765.

## Adding a mensa

Add an entry to `mensas.json`. For a ZFV location, `url` is its food2050 weekly lunch page (linked from the location's page on zfv.ch). Dishes whose line or name matches the `exclude` pattern (soups, desserts, add-ons) are skipped.
