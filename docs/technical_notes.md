# 📄 Technical Documentation
## Book Price & Availability Analysis

---

## Architecture Overview

This project follows a **linear ETL pipeline** architecture:

```
Extract  →  Transform  →  Load  →  Analyse  →  Present
scraper     cleaner       CSV      notebook    dashboard
```

Each stage is independent — you can re-run any single stage without
rerunning upstream stages (as long as its input file exists).

---

## Module Reference

### `scraper.py`

| Component | Purpose |
|-----------|---------|
| `get_soup(url)` | HTTP GET with timeout, returns BeautifulSoup tree |
| `parse_rating(article)` | Reads star-rating from CSS class attribute |
| `parse_listing_page(soup)` | Extracts 20 books from one catalogue page |
| `enrich_with_detail_page(book)` | Fetches individual book page for category + stock count |
| `scrape_all_books()` | Orchestrates all 50 pages |
| `save_to_csv(books)` | Writes dataclass list to CSV |

**Key design decisions:**
- Uses a `@dataclass` (`Book`) as the data model — this gives free `asdict()` serialisation and makes fields self-documenting
- `REQUEST_DELAY_SECONDS = 0.6` — polite rate limiting; do not remove
- Category is fetched from the detail-page breadcrumb, not the listing page (it's not available there)

**Common mistake to avoid:** Using `article.find("p", {"class": "star-rating"}).text` to get
the rating — the text is always empty. The rating is only in the class list:
`article.find("p", class_="star-rating")["class"]` → `["star-rating", "Three"]`

---

### `data_cleaning.py`

| Function | Input | Output |
|----------|-------|--------|
| `load_raw()` | CSV path | raw DataFrame |
| `drop_duplicates()` | DataFrame | DataFrame (deduped) |
| `handle_missing_values()` | DataFrame | DataFrame (no critical NaNs) |
| `clean_price()` | DataFrame | DataFrame (price as float64) |
| `clean_availability()` | DataFrame | DataFrame + `in_stock` bool column |
| `engineer_features()` | DataFrame | DataFrame + `price_tier`, `title_length`, `title_word_count` |
| `validate()` | DataFrame | None (raises on assertion failure) |
| `run_pipeline()` | paths | cleaned DataFrame + saves CSV |

**Price tier bins:**

| Label | Range |
|-------|-------|
| Budget | £0 – £20 |
| Mid | £20 – £35 |
| Premium | £35 – £50 |
| Luxury | £50+ |

---

### `app.py` (Streamlit Dashboard)

**Pages:**
1. **Home** — hero, KPI cards, quick price histogram, project summary
2. **Dashboard** — full analytics with all 7 chart types + download button
3. **Book Explorer** — search + sort + card-based book listing + download
4. **About** — project architecture, data schema, author info

**Data loading:** `@st.cache_data` wraps the `load_data()` function so the CSV is only read once per session, not on every user interaction.

**Sidebar filters** are applied to a `filtered` DataFrame that all pages read from. This means every page respects the sidebar state consistently.

---

## Data Schema (cleaned_books.csv)

| Column | dtype | Example | Notes |
|--------|-------|---------|-------|
| `title` | object | "Sapiens: A Brief History..." | Raw title from `<a title="">` |
| `price_gbp` | float64 | 54.23 | Stripped of £ symbol |
| `availability` | object | "In stock" | Raw text from listing page |
| `in_stock` | bool | True | Derived from availability text |
| `price_tier` | category | "Luxury (£50+)" | pd.cut into 4 bins |
| `title_length` | int64 | 38 | `len(title)` |
| `title_word_count` | int64 | 7 | `len(title.split())` |
| `product_url` | object | "https://books.toscrape.com/..." | Full URL |
| `image_url` | object | "https://books.toscrape.com/..." | Full cover image URL |

---

## Running the Full Pipeline

```bash
# 1. Setup
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Scrape (60–90 seconds for all 1000 books)
python scraper.py

# 3. Clean
python data_cleaning.py

# 4. Launch dashboard
streamlit run app.py

# 5. Or open notebook
jupyter notebook notebooks/analysis.ipynb
```

---

## Known Limitations

1. **Sample size:** The bundled `cleaned_books.csv` contains 60 books from 3 pages.
   Run `scraper.py` to expand to 1000. The scraper is fully functional.

2. **No ratings in scraped columns:** Ratings are in the data if you run the full scraper
   (the `parse_rating()` function in `scraper.py` correctly extracts them from the
   CSS class), but the dashboard currently doesn't have a rating filter UI — easy to add.

3. **No real-time data:** This is a one-shot scrape, not a live feed. To track prices
   over time, schedule `scraper.py` via cron or GitHub Actions and append to a dated CSV.

---

*Documentation version: 1.0 · 2026*
