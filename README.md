# 📚 Book Price & Availability Analysis

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Streamlit-1.41-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white"/>
  <img src="https://img.shields.io/badge/BeautifulSoup-4.12-59666C?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/pandas-2.2-150458?style=for-the-badge&logo=pandas&logoColor=white"/>
  <img src="https://img.shields.io/badge/seaborn-0.13-4C72B0?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge"/>
</p>

<p align="center">
  <b>An end-to-end data analytics project — real web scraping · professional EDA · interactive dashboard</b>
</p>

---

## 🔍 Project Overview

This project builds a **complete data analytics pipeline** on real book data scraped live from
[books.toscrape.com](https://books.toscrape.com) — a public, scraping-friendly practice catalogue.

Every step is production-grade: the scraper handles pagination and error recovery, the cleaning
pipeline is modular and reusable, the EDA notebook is fully annotated with business interpretations,
and the Streamlit dashboard offers real-time search, filtering, sorting, and CSV download.

> 📌 **No synthetic data.** Every number in this project comes from the actual website.

---

## 🎯 Objectives

- Scrape real book data (title, price, availability) across all 50 pages of the catalogue
- Build a modular, logged, production-style cleaning pipeline
- Conduct meaningful Exploratory Data Analysis with business-readable insights
- Deliver an interactive, filterable, searchable web dashboard
- Package everything as a professional portfolio artifact

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🕷️ Multi-page scraper | Scrapes all 50 pages (1000 books) with rate limiting & error handling |
| 🧹 Cleaning pipeline | Deduplication, type conversion, feature engineering, validation |
| 📓 EDA notebook | 11 sections, 7 chart types, annotated business insights |
| 📊 Interactive dashboard | Streamlit app with real-time filter/search/sort |
| 🎛️ Price tier filter | Budget / Mid / Premium / Luxury segmentation |
| 🔍 Full-text search | Search books by title keyword |
| ⬇️ CSV download | Download filtered results directly from the dashboard |
| 📈 7 chart types | Histogram, KDE, bar, horizontal bar, scatter, box plot, pie |

---

## 📊 Key Findings (from real data)

| Metric | Value |
|--------|-------|
| Books scraped (sample) | 60 verified live books |
| Average price | **£35.00** |
| Median price | **£33.49** |
| Price range | **£12.84 – £57.31** |
| Most expensive | *Slow States of Collapse: Poems* — £57.31 |
| Cheapest | *In Her Wake* — £12.84 |
| Most common tier | Mid (£20–35) |
| In-stock rate | 100% (sampled pages) |

> Run `scraper.py` to extend to the full 1000-book dataset.

---

## 🛠️ Technology Stack

```
Web Scraping    →  requests · BeautifulSoup · lxml
Data Layer      →  pandas · NumPy
Visualisation   →  matplotlib · seaborn · plotly
Dashboard       →  Streamlit
Notebook        →  Jupyter
Dev Tooling     →  Git · virtual env · logging · PEP 8
```

---

## 🗂️ Project Architecture

```
Book_Price_Rating_Analysis/
│
├── app.py                      ← Streamlit dashboard (4 pages)
├── scraper.py                  ← Production web scraper
├── data_cleaning.py            ← Modular cleaning pipeline
├── generate_notebook.py        ← Notebook builder script
├── requirements.txt
├── README.md
├── LICENSE
├── .gitignore
│
├── data/
│   ├── raw_books.csv           ← Raw scraped output
│   └── cleaned_books.csv       ← Processed, analysis-ready data
│
├── notebooks/
│   └── analysis.ipynb          ← Full EDA (11 sections)
│
├── images/                     ← Exported charts (PNG)
│   ├── price_distribution.png
│   ├── price_tier_counts.png
│   ├── price_boxplot.png
│   ├── titlelen_vs_price.png
│   ├── top10_expensive.png
│   └── top10_cheapest.png
│
│
├── docs/
│   └── technical_notes.md
│
└── screenshots/                ← Add dashboard screenshots here
```

---

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/Book_Price_Rating_Analysis.git
cd Book_Price_Rating_Analysis
```

### 2. Create a virtual environment

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Scrape the data *(takes ~60 seconds, be patient)*

```bash
python scraper.py
```

This creates `data/raw_books.csv` with 1000 real books.

### 5. Clean the data

```bash
python data_cleaning.py
```

This creates `data/cleaned_books.csv` with engineered features.

### 6. Launch the dashboard

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

### 7. (Optional) Open the EDA notebook

```bash
jupyter notebook notebooks/analysis.ipynb
```

---

## 📸 Screenshots

> *Add your own after running `streamlit run app.py`:*

| Home | Dashboard |
|------|-----------|
| *(screenshot)* | *(screenshot)* |

| Book Explorer | About |
|---------------|-------|
| *(screenshot)* | *(screenshot)* |

---

## 📈 Data Flow

```
books.toscrape.com
      │
      ▼
 scraper.py          ← requests + BeautifulSoup, 50 pages
      │
      ▼
data/raw_books.csv   ← title, price, availability, URL, image
      │
      ▼
data_cleaning.py     ← deduplicate, clean types, add features
      │
      ▼
data/cleaned_books.csv  ← in_stock flag, price_tier, title_length
      │
      ├──▶ notebooks/analysis.ipynb  ← EDA & charts
      │
      └──▶ app.py (Streamlit)        ← Interactive dashboard
```

---

## 🔮 Future Enhancements

- [ ] Schedule daily scraping with `cron` / GitHub Actions to track price changes over time
- [ ] Category analysis — already built into `scraper.py`, just needs category column activation
- [ ] Price alert system — email notification when a book drops below a threshold
- [ ] Sentiment analysis on book descriptions
- [ ] Docker container for one-command deployment
- [ ] Deploy dashboard to Streamlit Community Cloud (free)

---

## 📄 License

MIT License — see [LICENSE](LICENSE)

---

## 🙏 Acknowledgements

- [books.toscrape.com](https://books.toscrape.com) — a free, public, scraping-safe practice site
- [Streamlit](https://streamlit.io) — the fastest way to turn data scripts into shareable web apps
- [Seaborn](https://seaborn.pydata.org) — statistical data visualisation library

---

<p align="center">Built with ❤️ by Binish · AIKTC · 2026</p>
