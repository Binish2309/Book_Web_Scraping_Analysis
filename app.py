"""
app.py
-------
Streamlit dashboard for Book Price & Availability Analysis.

Run:
    streamlit run app.py
"""

from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

# ── PAGE CONFIG ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Book Analytics Dashboard",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CUSTOM CSS ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Main background */
.main { background-color: #F8F9FA; }

/* Stat cards */
.stat-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 12px;
    padding: 20px 24px;
    color: white;
    text-align: center;
    box-shadow: 0 4px 15px rgba(102,126,234,0.3);
    margin-bottom: 8px;
}
.stat-card .value { font-size: 2rem; font-weight: 700; margin: 0; }
.stat-card .label { font-size: 0.85rem; opacity: 0.9; margin: 0; letter-spacing: 0.5px; }

.stat-card-green {
    background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    box-shadow: 0 4px 15px rgba(17,153,142,0.3);
}
.stat-card-orange {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    box-shadow: 0 4px 15px rgba(245,87,108,0.3);
}
.stat-card-blue {
    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    box-shadow: 0 4px 15px rgba(79,172,254,0.3);
}
.stat-card-purple {
    background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
    box-shadow: 0 4px 15px rgba(67,233,123,0.3);
}

/* Section header */
.section-header {
    font-size: 1.4rem;
    font-weight: 700;
    color: #2d3436;
    border-left: 4px solid #667eea;
    padding-left: 12px;
    margin: 24px 0 16px 0;
}

/* Book card */
.book-card {
    background: white;
    border-radius: 10px;
    padding: 14px;
    border: 1px solid #e0e0e0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    margin-bottom: 10px;
    transition: box-shadow 0.2s;
}
.book-title { font-weight: 700; font-size: 0.95rem; color: #2d3436; }
.book-price { color: #667eea; font-size: 1.1rem; font-weight: 700; }
.book-stock { color: #11998e; font-size: 0.8rem; }

/* Hero */
.hero {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 16px;
    padding: 40px;
    color: white;
    text-align: center;
    margin-bottom: 28px;
}
.hero h1 { font-size: 2.4rem; font-weight: 800; margin: 0; }
.hero p  { font-size: 1.05rem; opacity: 0.9; margin: 8px 0 0 0; }
</style>
""", unsafe_allow_html=True)


# ── DATA LOADING ───────────────────────────────────────────────────────────────
@st.cache_data
def load_data() -> pd.DataFrame:
    """Load cleaned CSV; fall back to raw sample if full dataset not yet present."""
    for path in ["data/cleaned_books.csv", "data/raw_books_live_sample.csv"]:
        p = Path(path)
        if p.exists():
            df = pd.read_csv(p)
            # Ensure required columns exist
            if "price_gbp" not in df.columns:
                continue
            # Re-apply cleaning for raw sample fallback
            df["price_gbp"] = (
                df["price_gbp"].astype(str)
                .str.replace("£", "", regex=False)
                .str.replace("Â", "", regex=False)
                .str.strip()
                .astype(float)
            )
            if "availability" not in df.columns:
                df["availability"] = "In stock"
            if "in_stock" not in df.columns:
                df["in_stock"] = df["availability"].str.contains("In stock", case=False, na=False)
            if "price_tier" not in df.columns:
                df["price_tier"] = pd.cut(
                    df["price_gbp"],
                    bins=[0, 20, 35, 50, np.inf],
                    labels=["Budget (<£20)", "Mid (£20-35)", "Premium (£35-50)", "Luxury (£50+)"],
                )
            if "title_length" not in df.columns:
                df["title_length"] = df["title"].str.len()
            return df
    st.error("No dataset found. Run scraper.py first, then data_cleaning.py.")
    st.stop()


df = load_data()

# ── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/book-shelf.png", width=72)
    st.markdown("## 📚 Book Analytics")
    st.markdown("---")
    page = st.radio(
        "Navigate",
        ["🏠 Home", "📊 Dashboard", "🔍 Book Explorer", "ℹ️ About"],
        label_visibility="collapsed",
    )
    st.markdown("---")

    st.markdown("### 🎛️ Filters")
    price_min, price_max = float(df["price_gbp"].min()), float(df["price_gbp"].max())
    price_range = st.slider(
        "Price Range (£)",
        min_value=price_min,
        max_value=price_max,
        value=(price_min, price_max),
        step=0.50,
    )

    tiers = ["All"] + list(df["price_tier"].cat.categories if hasattr(df["price_tier"], "cat") else df["price_tier"].unique())
    selected_tier = st.selectbox("Price Tier", tiers)

    avail_filter = st.selectbox("Availability", ["All", "In Stock", "Out of Stock"])

    st.markdown("---")
    st.markdown("### ℹ️ Dataset")
    st.info(f"**{len(df)}** books loaded\n\nSource: books.toscrape.com")


# ── FILTERED DATA ──────────────────────────────────────────────────────────────
filtered = df[df["price_gbp"].between(*price_range)]
if selected_tier != "All":
    filtered = filtered[filtered["price_tier"].astype(str) == selected_tier]
if avail_filter == "In Stock":
    filtered = filtered[filtered["in_stock"] == True]
elif avail_filter == "Out of Stock":
    filtered = filtered[filtered["in_stock"] == False]


# ── CHART HELPER ───────────────────────────────────────────────────────────────
sns.set_theme(style="whitegrid", palette="muted")

def render_chart(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight")
    buf.seek(0)
    st.image(buf, use_container_width=True)
    plt.close(fig)


# ══════════════════════════════════════════════════════════════════════════════
# HOME PAGE
# ══════════════════════════════════════════════════════════════════════════════
if page == "🏠 Home":
    st.markdown("""
    <div class="hero">
        <h1>📚 Book Price & Availability Analytics</h1>
        <p>A complete end-to-end data analytics project — real web-scraped data · professional visualisations · interactive dashboard</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="stat-card">
            <p class="value">{len(df)}</p>
            <p class="label">📖 BOOKS SCRAPED</p></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="stat-card stat-card-green">
            <p class="value">£{df['price_gbp'].mean():.2f}</p>
            <p class="label">💷 AVERAGE PRICE</p></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="stat-card stat-card-orange">
            <p class="value">£{df['price_gbp'].max():.2f}</p>
            <p class="label">🏆 HIGHEST PRICE</p></div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class="stat-card stat-card-blue">
            <p class="value">{df['in_stock'].sum()}</p>
            <p class="label">✅ IN STOCK</p></div>""", unsafe_allow_html=True)

    st.markdown("")
    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown('<p class="section-header">🚀 Project Overview</p>', unsafe_allow_html=True)
        st.markdown("""
This project demonstrates a **complete data analytics pipeline** built on real
web-scraped data from [books.toscrape.com](https://books.toscrape.com).

**What was built:**
- 🕷️ Production web scraper (`scraper.py`) — all 50 pages, 1000 books
- 🧹 Modular cleaning pipeline (`data_cleaning.py`)
- 📓 Full EDA Jupyter notebook (`notebooks/analysis.ipynb`)
- 📊 This interactive Streamlit dashboard (`app.py`)
- 📄 Professional README, documentation, and LinkedIn assets

**Tech Stack:** Python · BeautifulSoup · pandas · seaborn · matplotlib · Streamlit
        """)

    with col_r:
        st.markdown('<p class="section-header">💡 Key Findings</p>', unsafe_allow_html=True)
        st.markdown(f"""
| Metric | Value |
|--------|-------|
| Price Range | £{df['price_gbp'].min():.2f} – £{df['price_gbp'].max():.2f} |
| Average Price | £{df['price_gbp'].mean():.2f} |
| Median Price | £{df['price_gbp'].median():.2f} |
| Most Expensive | {df.loc[df.price_gbp.idxmax(),'title'][:35]}... |
| Cheapest | {df.loc[df.price_gbp.idxmin(),'title'][:35]} |
| Books In Stock | {df['in_stock'].sum()} / {len(df)} ({df['in_stock'].mean()*100:.0f}%) |
| Most Common Tier | {df['price_tier'].mode()[0]} |
        """)

    st.markdown('<p class="section-header">📈 Quick Price Distribution</p>', unsafe_allow_html=True)
    fig, ax = plt.subplots(figsize=(10, 3.5))
    sns.histplot(df["price_gbp"], bins=20, kde=True, color="#667eea", ax=ax)
    ax.axvline(df["price_gbp"].mean(), color="crimson", linestyle="--", label=f"Mean £{df['price_gbp'].mean():.2f}")
    ax.axvline(df["price_gbp"].median(), color="orange", linestyle="--", label=f"Median £{df['price_gbp'].median():.2f}")
    ax.legend(); ax.set_xlabel("Price (£)"); ax.set_ylabel("Count")
    ax.set_title("All Book Prices — Distribution with KDE", fontweight="bold")
    render_chart(fig)


# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD PAGE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📊 Dashboard":
    st.markdown("## 📊 Analytics Dashboard")
    st.caption(f"Showing **{len(filtered)}** books after filters")

    # Stat row
    c1, c2, c3, c4, c5 = st.columns(5)
    metrics = [
        ("Books", len(filtered), None),
        ("Avg Price", f"£{filtered['price_gbp'].mean():.2f}" if len(filtered) else "—", None),
        ("Min Price", f"£{filtered['price_gbp'].min():.2f}" if len(filtered) else "—", None),
        ("Max Price", f"£{filtered['price_gbp'].max():.2f}" if len(filtered) else "—", None),
        ("In Stock", filtered['in_stock'].sum() if len(filtered) else 0, None),
    ]
    for col, (label, val, delta) in zip([c1,c2,c3,c4,c5], metrics):
        col.metric(label, val, delta)

    st.divider()

    if len(filtered) == 0:
        st.warning("No books match the current filters. Adjust the sidebar filters.")
        st.stop()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Price Distribution**")
        fig, ax = plt.subplots(figsize=(7, 4))
        sns.histplot(filtered["price_gbp"], bins=15, kde=True, color="#667eea", ax=ax)
        ax.set_xlabel("Price (£)"); ax.set_ylabel("Count")
        render_chart(fig)

    with col2:
        st.markdown("**Price Tier Breakdown**")
        order = ["Budget (<£20)", "Mid (£20-35)", "Premium (£35-50)", "Luxury (£50+)"]
        tier_counts = filtered["price_tier"].astype(str).value_counts().reindex(order, fill_value=0)
        colors = ["#55A868", "#4C72B0", "#DD8452", "#C44E52"]
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.bar(tier_counts.index, tier_counts.values, color=colors)
        ax.set_ylabel("Count"); ax.set_xlabel("")
        for i, v in enumerate(tier_counts.values):
            if v: ax.text(i, v + 0.1, str(v), ha="center", fontweight="bold", fontsize=10)
        plt.xticks(rotation=15, ha="right")
        render_chart(fig)

    col3, col4 = st.columns(2)

    with col3:
        st.markdown("**Top 10 Most Expensive Books**")
        top10 = filtered.nlargest(10, "price_gbp")[["title", "price_gbp"]]
        fig, ax = plt.subplots(figsize=(7, 5))
        ax.barh(top10["title"].str[:38], top10["price_gbp"], color="#C44E52")
        ax.invert_yaxis(); ax.set_xlabel("Price (£)")
        for i, v in enumerate(top10["price_gbp"]):
            ax.text(v + 0.2, i, f"£{v:.2f}", va="center", fontsize=8.5)
        render_chart(fig)

    with col4:
        st.markdown("**Top 10 Cheapest Books**")
        bot10 = filtered.nsmallest(10, "price_gbp")[["title", "price_gbp"]]
        fig, ax = plt.subplots(figsize=(7, 5))
        ax.barh(bot10["title"].str[:38], bot10["price_gbp"], color="#55A868")
        ax.invert_yaxis(); ax.set_xlabel("Price (£)")
        for i, v in enumerate(bot10["price_gbp"]):
            ax.text(v + 0.1, i, f"£{v:.2f}", va="center", fontsize=8.5)
        render_chart(fig)

    col5, col6 = st.columns(2)

    with col5:
        st.markdown("**Price Box Plot**")
        fig, ax = plt.subplots(figsize=(7, 4))
        sns.boxplot(y=filtered["price_gbp"], color="#764ba2", ax=ax)
        ax.set_ylabel("Price (£)")
        render_chart(fig)

    with col6:
        st.markdown("**Availability Breakdown**")
        avail = filtered["in_stock"].map({True: "In Stock", False: "Out of Stock"}).value_counts()
        fig, ax = plt.subplots(figsize=(7, 4))
        colors_av = ["#55A868" if v == "In Stock" else "#C44E52" for v in avail.index]
        ax.bar(avail.index, avail.values, color=colors_av)
        ax.set_ylabel("Count")
        for i, v in enumerate(avail.values):
            ax.text(i, v + 0.1, str(v), ha="center", fontweight="bold")
        render_chart(fig)

    st.divider()
    st.markdown("**Title Length vs Price (Scatter)**")
    fig, ax = plt.subplots(figsize=(12, 4))
    hue_order = ["Budget (<£20)", "Mid (£20-35)", "Premium (£35-50)", "Luxury (£50+)"]
    sns.scatterplot(data=filtered, x="title_length", y="price_gbp",
                    hue=filtered["price_tier"].astype(str),
                    hue_order=hue_order, ax=ax, s=80, alpha=0.8)
    z = np.polyfit(filtered["title_length"], filtered["price_gbp"], 1)
    xs = np.linspace(filtered["title_length"].min(), filtered["title_length"].max(), 100)
    ax.plot(xs, np.poly1d(z)(xs), "r--", linewidth=1.5, label="Trend")
    ax.legend(); ax.set_xlabel("Title Length (chars)"); ax.set_ylabel("Price (£)")
    render_chart(fig)

    st.markdown("### ⬇️ Download Filtered Data")
    csv_bytes = filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Download Filtered Books CSV",
        data=csv_bytes,
        file_name="filtered_books.csv",
        mime="text/csv",
    )


# ══════════════════════════════════════════════════════════════════════════════
# BOOK EXPLORER PAGE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔍 Book Explorer":
    st.markdown("## 🔍 Book Explorer")

    col_s, col_sort = st.columns([3, 1])
    with col_s:
        search = st.text_input("🔎 Search by title", placeholder="e.g. Sharp, Light, Sapiens...")
    with col_sort:
        sort_by = st.selectbox("Sort by", ["Price: Low → High", "Price: High → Low", "Title A–Z", "Title Z–A"])

    results = filtered.copy()
    if search.strip():
        results = results[results["title"].str.contains(search.strip(), case=False, na=False)]

    sort_map = {
        "Price: Low → High": ("price_gbp", True),
        "Price: High → Low": ("price_gbp", False),
        "Title A–Z": ("title", True),
        "Title Z–A": ("title", False),
    }
    col, asc = sort_map[sort_by]
    results = results.sort_values(col, ascending=asc).reset_index(drop=True)

    st.caption(f"**{len(results)}** books found")

    if len(results) == 0:
        st.info("No books match your search. Try a different keyword.")
    else:
        for _, row in results.iterrows():
            stock_color = "#11998e" if row.get("in_stock", True) else "#C44E52"
            stock_label = "✅ In Stock" if row.get("in_stock", True) else "❌ Out of Stock"
            tier = str(row.get("price_tier", ""))
            url = row.get("product_url", "#")
            st.markdown(f"""
            <div class="book-card">
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div style="flex:1">
                        <p class="book-title">📖 {row['title']}</p>
                        <span style="background:#f0f0f0; border-radius:4px; padding:2px 8px; font-size:0.78rem; color:#555;">{tier}</span>
                        &nbsp;<a href="{url}" target="_blank" style="font-size:0.78rem; color:#667eea;">View on site ↗</a>
                    </div>
                    <div style="text-align:right; margin-left:16px;">
                        <p class="book-price">£{row['price_gbp']:.2f}</p>
                        <p class="book-stock" style="color:{stock_color};">{stock_label}</p>
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

    st.markdown("---")
    csv_bytes = results.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download Search Results CSV", csv_bytes, "search_results.csv", "text/csv")


# ══════════════════════════════════════════════════════════════════════════════
# ABOUT PAGE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "ℹ️ About":
    st.markdown("## ℹ️ About This Project")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
### 📌 Project Summary
**Book Price & Availability Analysis** is an end-to-end data analytics project
that scrapes real book listings from books.toscrape.com, cleans the data with a
professional pipeline, conducts exploratory data analysis, and presents everything
through this interactive dashboard.

### 🎯 Objectives
- Demonstrate real web scraping with `requests` + `BeautifulSoup`
- Build a modular, reusable data cleaning pipeline
- Conduct meaningful EDA with business-relevant insights
- Deliver a professional, interactive dashboard

### 🛠️ Technology Stack
| Layer | Tools |
|-------|-------|
| Scraping | Python · requests · BeautifulSoup |
| Data | pandas · NumPy |
| Visualisation | matplotlib · seaborn |
| Dashboard | Streamlit |
| Notebook | Jupyter |
| Version Control | Git · GitHub |
        """)
    with col2:
        st.markdown("""
### 🗂️ Project Architecture
```
Book_Price_Rating_Analysis/
├── app.py                 ← This dashboard
├── scraper.py             ← Web scraper
├── data_cleaning.py       ← Cleaning pipeline
├── requirements.txt
├── README.md
├── data/
│   ├── raw_books.csv      ← Raw scraped data
│   └── cleaned_books.csv  ← Cleaned data
├── notebooks/
│   └── analysis.ipynb     ← Full EDA
├── images/                ← Chart exports
├── linkedin/              ← Portfolio assets
└── docs/                  ← Documentation
```

### 📊 Data Schema
| Column | Type | Description |
|--------|------|-------------|
| title | str | Book title |
| price_gbp | float | Price in GBP |
| availability | str | Stock status text |
| in_stock | bool | True if in stock |
| price_tier | category | Budget/Mid/Premium/Luxury |
| title_length | int | Character count |
| product_url | str | Source page URL |
| image_url | str | Cover image URL |
        """)

    st.markdown("---")
    st.markdown("### 👤 Author")
    st.info("""
**Built by:** Binish (AIKTC)
**Purpose:** Internship portfolio project demonstrating end-to-end data analytics skills
**Source website:** https://books.toscrape.com (a public, scraping-friendly practice site)
    """)
