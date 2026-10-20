"""Fetch this week's remaining lunch menus with macros for every mensa in mensas.json.

Sources:
  food2050 (ZFV / UZH mensas): weekly page lists dishes; each dish detail page carries
      nutrition per portion and per 100 g, total weight, prices and allergens.
  cookpit (ETH API, used by Octavo): nutrition per 100 g only, so per-portion values are
      estimated with the median food2050 portion weight of the same run.

Writes the JSON file named in mensas.json ("output") and archives each day's dishes in the
CSV named in "history". Standard library only.
"""
import csv
import json
import re
import statistics
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta
from html import unescape
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
CONFIG = json.loads((ROOT / "mensas.json").read_text(encoding="utf-8"))
TZ = ZoneInfo(CONFIG["timezone"])
EXCLUDE = re.compile(CONFIG["exclude"], re.I)
HEADERS = {"User-Agent": "protein-mensa/1.0 (daily lunch macro ranking)"}
COOKPIT = "https://idapps.ethz.ch/cookpit-pub-services/v1/weeklyrotas"

NUTRIENTS = {
    "Kalorien": "kcal", "Fett": "fat", "davon gesättigte Fettsäuren": "satfat",
    "Kohlenhydrate": "carbs", "davon Zucker": "sugar", "Ballaststoffe": "fiber",
    "Protein": "protein", "Eiweiss": "protein", "Salz": "salt",
}
SMALL_WORDS = {"mit", "und", "an", "auf", "im", "in", "vom", "von", "der", "die", "das", "dem",
               "den", "zu", "à", "a", "la", "al", "alla", "con", "e", "et", "de", "di", "aus", "nach"}


def get(url):
    for attempt in range(2):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=20) as r:
                return r.read().decode("utf-8")
        except OSError:
            if attempt == 1:
                raise
            time.sleep(3)


def number(text):
    m = re.search(r"\d+(?:[.,]\d+)?", text or "")
    return float(m.group().replace(",", ".")) if m else None


def nice_name(name):
    """Title-case names the source shouts in capitals; leave normal casing alone."""
    name = " ".join(name.split())
    letters = [c for c in name if c.isalpha()]
    if not letters or sum(c.isupper() for c in letters) < 0.6 * len(letters):
        return name
    words = name.lower().split(" ")
    return " ".join(w if i and w in SMALL_WORDS else "-".join(p[:1].upper() + p[1:] for p in w.split("-"))
                    for i, w in enumerate(words))


def price_group(label):
    label = label.lower()
    if label.startswith(("stud", "intern")):
        return ["stud", "staff"] if "intern" in label else ["stud"]
    if label.startswith(("mitarb", "angest", "staff", "doz")):
        return ["staff"]
    if label.startswith(("ext", "gäst", "gast", "besuch")):
        return ["ext"]
    return []


def diet_from(vegan, vegetarian, allergens):
    if vegan:
        return "vegan"
    if vegetarian:
        return "vegetarian"
    if any(a.startswith(("Fisch", "Krebstiere", "Weichtiere")) for a in allergens):
        return "fish"
    return "meat"


# ---------- food2050 ----------

def rsc_payload(html):
    chunks = []
    for m in re.finditer(r"self\.__next_f\.push\((\[.*?\])\)</script>", html, re.S):
        arr = json.loads(m.group(1))
        if len(arr) > 1 and isinstance(arr[1], str):
            chunks.append(arr[1])
    return "".join(chunks)


def food2050_menu_items(url):
    s = rsc_payload(get(url))
    dec = json.JSONDecoder()
    return [dec.raw_decode(s, m.start())[0] for m in re.finditer(r'\{"__typename":"OutletMenuItemDish"', s)]


def food2050_detail(url):
    h = get(url).replace("<!-- -->", "")
    total, per100 = {}, {}
    rows = re.findall(r'FoodFactLabel[^"]*"[^>]*>([^<]+)</div><div[^>]*>([^<]*)</div><div[^>]*>([^<]*)</div>', h)
    for label, v_total, v_100 in rows:
        key = NUTRIENTS.get(unescape(label).strip())
        if key:
            total[key], per100[key] = number(v_total), number(v_100)
    weight = re.search(r"Gesamtgewicht</h3><div[^>]*>([^<]*)</div>", h)
    prices = {}
    for amount, label in re.findall(r'PriceTag[^"]*"[^>]*>([\d.]+) CHF</p><p[^>]*PriceLevel[^>]*>([^<]+)</p>', h):
        for g in price_group(unescape(label)):
            if float(amount) > 0:
                prices.setdefault(g, float(amount))
    allergens = [unescape(a).strip() for a in re.findall(r'DishFactsAllergens__Allergen[^"]*"[^>]*>([^<]+)</p>', h)]
    return total, per100, number(weight.group(1)) if weight else None, prices, allergens


def food2050_dishes(mensa, today, week_end, pool, known):
    """known: dishes from the previous run keyed by detail URL; their nutrition is reused so a
    normal run only fetches the weekly page plus dishes that are new or still lack macros."""
    todo = []
    for item in food2050_menu_items(mensa["url"]):
        url = item["detailUrl"]
        path, day = url.rstrip("/").split("/")[-2:]
        if not today.isoformat() <= day <= week_end.isoformat():
            continue
        dish = item["dish"]
        if not dish["name"].strip() or EXCLUDE.search(f"{path} {dish['name']}"):
            continue
        cat = item.get("category")
        line = cat["name"] if isinstance(cat, dict) else path.split(",")[-1].replace("-", " ")
        todo.append((url, day, line, dish))

    def details(t):
        url, _, _, dish = t
        old = known.get(url)
        if old and old["name"] == nice_name(dish["name"]):
            total = {k: old[k] for k in ("kcal", "protein", "carbs", "fat", "fiber", "sugar", "salt")}
            return total, old["per100"] or {}, old["weight"], old["prices"], old["allergens"]
        return food2050_detail(url)

    out = []
    for (url, day, line, dish), (total, per100, weight, prices, allergens) in zip(todo, pool.map(details, todo)):
        stats = dish.get("stats") or {}
        climate = (stats.get("food2050climateImpact") or {}).get("rating")
        balanced = (stats.get("food2050HealthRating") or {}).get("isBalanced")
        out.append({
            "mensa": mensa["id"], "date": day, "line": line,
            "name": nice_name(dish["name"]), "desc": " ".join((dish.get("description") or "").split()),
            "diet": diet_from(dish.get("isVegan"), dish.get("isVegetarian"), allergens),
            **{k: total.get(k) for k in ("kcal", "protein", "carbs", "fat", "fiber", "sugar", "salt")},
            "weight": weight, "estimated": False, "per100": per100 or None,
            "prices": prices, "allergens": allergens, "climate": climate, "balanced": balanced, "url": url,
        })
    return out


# ---------- cookpit (Octavo) ----------

def cookpit_dishes(mensa, today, week_end):
    query = urllib.parse.urlencode({
        "client-id": mensa["client_id"], "lang": "de", "facility": mensa["facility"], "rs-first": 0,
        "rs-size": 10, "valid-after": today.isoformat(), "valid-before": (week_end + timedelta(days=1)).isoformat(),
    })
    data = json.loads(get(f"{COOKPIT}?{query}"))
    out = []
    for rota in data.get("weekly-rota-array", []):
        start = date.fromisoformat(rota["valid-from"])
        monday = start - timedelta(days=start.weekday())
        for day in rota.get("day-of-week-array", []):
            d = monday + timedelta(days=day["day-of-week-code"] - 1)
            if not today <= d <= week_end:
                continue
            for hours in day.get("opening-hour-array", []):
                for meal_time in hours.get("meal-time-array", []):
                    if "mittag" not in meal_time["name"].lower():
                        continue
                    for line in meal_time.get("line-array", []):
                        meal = line.get("meal")
                        if not meal or EXCLUDE.search(f"{line['name']} {meal['name']}"):
                            continue
                        out.append(cookpit_dish(mensa, d, line["name"], meal))
    return out


def cookpit_dish(mensa, d, line, meal):
    kj = number(meal.get("energy"))
    per100 = None
    if kj:
        per100 = {"kcal": round(kj / 4.184), "protein": number(meal.get("protein")), "fat": number(meal.get("fat")),
                  "carbs": number(meal.get("carbohydrates")), "sugar": number(meal.get("sugar")),
                  "salt": number(meal.get("salt")), "satfat": number(meal.get("saturated-fatty-acids"))}
    classes = {c["desc"] for c in meal.get("meal-class-array", [])}
    allergens = [a["desc"] for a in meal.get("allergen-array", [])]
    if "Vegan" in classes:
        diet = "vegan"
    elif "Vegetarisch" in classes:
        diet = "vegetarian"
    elif "Fisch" in classes or any(m["desc"].startswith("Fisch") for m in meal.get("meat-type-array", [])):
        diet = "fish"
    elif classes or meal.get("meat-type-array"):
        diet = "meat"
    else:
        diet = "vegetarian"
    prices = {}
    for p in meal.get("meal-price-array", []):
        for g in price_group(p["customer-group-desc"]):
            prices.setdefault(g, p["price"])
    desc = meal.get("description") or ""
    return {
        "mensa": mensa["id"], "date": d.isoformat(), "line": line,
        "name": nice_name(meal["name"]), "desc": " · ".join(x.strip() for x in desc.split("|") if x.strip()),
        "diet": diet, "kcal": None, "protein": None, "carbs": None, "fat": None, "fiber": None,
        "sugar": None, "salt": None, "weight": None, "estimated": per100 is not None, "per100": per100,
        "prices": prices, "allergens": allergens, "climate": None, "balanced": None, "url": mensa["url"],
    }


# ---------- history archive ----------

HISTORY_FIELDS = ["date", "mensa", "line", "name", "desc", "diet", "protein", "kcal", "carbs", "fat", "fiber",
                  "sugar", "salt", "weight", "estimated", "price_stud", "price_staff", "price_ext"]


def history_row(d):
    row = {k: d.get(k) for k in HISTORY_FIELDS if not k.startswith("price_")}
    row.update({f"price_{g}": d["prices"].get(g) for g in ("stud", "staff", "ext")})
    return {k: "" if v is None else v for k, v in row.items()}


def update_history(dishes, previous, today):
    """Today's dishes replace any earlier run of today; past days only fill gaps (a day whose
    own runs all failed) from the previous data file."""
    path = ROOT / CONFIG["history"]
    day = today.isoformat()
    rows = []
    if path.exists():
        with path.open(encoding="utf-8", newline="") as f:
            rows = [r for r in csv.DictReader(f) if r["date"] != day]
    known = {r["date"] for r in rows}
    gaps = [d for d in previous if d["date"] < day and d["date"] not in known]
    rows += [history_row(d) for d in gaps + [d for d in dishes if d["date"] == day]]
    rows.sort(key=lambda r: (r["date"], r["mensa"], r["line"], r["name"]))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=HISTORY_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"History: {len(rows)} dishes over {len({r['date'] for r in rows})} days in {path.name}")


def main():
    now = datetime.now(TZ)
    today = now.date()
    week_end = today + timedelta(days=6 - today.weekday())
    path = ROOT / CONFIG["output"]
    previous = json.loads(path.read_text(encoding="utf-8"))["dishes"] if path.exists() else []
    known = {d["url"]: d for d in previous if d["protein"] is not None and not d["estimated"]}
    deadline = time.monotonic() + CONFIG["time_budget_s"]
    dishes, errors = [], []
    with ThreadPoolExecutor(max_workers=4) as pool:
        for mensa in CONFIG["mensas"]:
            found, problem = [], None
            if time.monotonic() > deadline:
                problem = "time budget used up"
            else:
                try:
                    if mensa["source"] == "food2050":
                        found = food2050_dishes(mensa, today, week_end, pool, known)
                    else:
                        found = cookpit_dishes(mensa, today, week_end)
                except Exception as e:  # one broken source must not take down the others
                    problem = f"{type(e).__name__}: {e}"
                if not found and not problem:
                    problem = "menu page returned no dishes"
            if problem:
                # Keep the last known menu instead of silently dropping the mensa.
                found = [d for d in previous if d["mensa"] == mensa["id"] and d["date"] >= today.isoformat()]
                errors.append({"mensa": mensa["id"], "error": problem, "kept": len(found)})
                print(f"!! {mensa['name']}: {problem}; kept {len(found)} dishes from the last run", file=sys.stderr)
            dishes.extend(found)
            print(f"{mensa['name']:<20} {len(found):>3} dishes")

    weights = [d["weight"] for d in dishes if d["weight"] and not d["estimated"]]
    portion = round(statistics.median(weights)) if weights else CONFIG["fallback_portion_g"]
    for d in dishes:
        if d["estimated"]:
            d["weight"] = portion
            for k in ("kcal", "protein", "carbs", "fat", "sugar", "salt"):
                v = d["per100"].get(k)
                d[k] = round(v * portion / 100, 1) if v is not None else None

    if not dishes:
        sys.exit("No dishes found at all; keeping the previous data file.")
    update_history(dishes, previous, today)

    out = {
        "generated": now.isoformat(timespec="minutes"),
        "today": today.isoformat(),
        "estimated_portion_g": portion,
        "mensas": [{k: m[k] for k in ("id", "name", "campus", "url")} for m in CONFIG["mensas"]],
        "dishes": sorted(dishes, key=lambda d: (d["date"], d["mensa"], d["line"])),
        "errors": errors,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Wrote {len(dishes)} dishes to {path} (estimated portion {portion} g, {len(errors)} errors)")


if __name__ == "__main__":
    main()
