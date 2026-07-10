"""
scraper.py
-----------
Scrapes book data (title, price, rating, availability, category, product URL,
image URL, stock count) from https://books.toscrape.com/ across all 50
catalogue pages (1000 books) and writes data/raw_books.csv.

WHY A LOCAL RUN IS NEEDED:
This project was authored inside a sandboxed assistant environment with no
outbound socket access, so the bundled data/raw_books.csv was assembled from
real fetched pages but capped at a verified sample. Run this script on your
own machine (or Colab) to regenerate the FULL, real 1000-book dataset,
including star ratings -- ratings live only in an HTML class attribute
(e.g. class="star-rating Three") that text-extraction tools strip out, but
a real requests+BeautifulSoup run reads it correctly, as this script does.

Usage:
    pip install -r requirements.txt
    python scraper.py
"""

from __future__ import annotations

import csv
import logging
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://books.toscrape.com/"
CATALOGUE_URL = BASE_URL + "catalogue/page-{}.html"
OUTPUT_PATH = Path("data/raw_books.csv")
TOTAL_PAGES = 50
REQUEST_DELAY_SECONDS = 0.6  # be a polite, rate-limited scraper
TIMEOUT_SECONDS = 15

RATING_WORDS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("book_scraper")


@dataclass
class Book:
    title: str
    price_gbp: float
    rating: int
    availability: str
    stock_count: Optional[int]
    category: str
    product_url: str
    image_url: str


def get_soup(url: str) -> BeautifulSoup:
    """Fetch a URL and return a parsed BeautifulSoup object.

    Why: centralising the request logic means timeout/retry/error handling
    lives in one place instead of being copy-pasted at every call site.
    Expected output: a BeautifulSoup tree for the page, or a raised
    requests.RequestException on network failure (handled by the caller).
    Common beginner mistake: forgetting a timeout, which lets one dead
    request hang the whole scraper indefinitely.
    """
    response = requests.get(url, timeout=TIMEOUT_SECONDS)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def parse_rating(article) -> int:
    """Convert the star-rating CSS class (e.g. 'star-rating Three') to an int.

    Why: the rating is never rendered as visible text on this site, only as
    a CSS class name, so it must be read from the class list, not innerText.
    Common beginner mistake: scraping the visible page text for "stars" and
    getting nothing back -- the value simply isn't there as text.
    """
    tag = article.find("p", class_="star-rating")
    classes = tag.get("class", []) if tag else []
    for cls in classes:
        if cls in RATING_WORDS:
            return RATING_WORDS[cls]
    return 0


def parse_listing_page(soup: BeautifulSoup) -> list[dict]:
    """Extract title, price, rating, availability, and URLs from one listing page."""
    books = []
    for article in soup.select("article.product_pod"):
        title = article.h3.a["title"].strip()
        relative_href = article.h3.a["href"]
        product_url = BASE_URL + "catalogue/" + relative_href.replace("../../../", "")
        price_text = article.select_one("p.price_color").text
        price = float(price_text.replace("£", "").replace("Â", "").strip())
        availability = article.select_one("p.instock.availability").text.strip()
        rating = parse_rating(article)
        image_relative = article.find("img")["src"]
        image_url = BASE_URL + image_relative.replace("../../", "")
        books.append(
            {
                "title": title,
                "price_gbp": price,
                "rating": rating,
                "availability": availability,
                "product_url": product_url,
                "image_url": image_url,
            }
        )
    return books


def enrich_with_detail_page(book: dict) -> Book:
    """Visit a book's detail page to pull category and exact stock count.

    Why: category (breadcrumb) and the numeric "X available" count only
    live on the product detail page, not the listing page.
    Common beginner mistake: re-scraping the whole detail page instead of
    targeting the breadcrumb + product table, which is slower and fragile.
    """
    soup = get_soup(book["product_url"])
    breadcrumb = soup.select("ul.breadcrumb li a")
    category = breadcrumb[-1].text.strip() if len(breadcrumb) >= 3 else "Unknown"

    stock_text = soup.select_one("p.instock.availability").text
    stock_count = None
    if "(" in stock_text:
        digits = "".join(ch for ch in stock_text if ch.isdigit())
        stock_count = int(digits) if digits else None

    return Book(
        title=book["title"],
        price_gbp=book["price_gbp"],
        rating=book["rating"],
        availability=book["availability"],
        stock_count=stock_count,
        category=category,
        product_url=book["product_url"],
        image_url=book["image_url"],
    )


def scrape_all_books() -> list[Book]:
    all_books: list[Book] = []
    for page_num in range(1, TOTAL_PAGES + 1):
        url = CATALOGUE_URL.format(page_num)
        try:
            soup = get_soup(url)
        except requests.RequestException as exc:
            logger.error("Failed to fetch page %s: %s", page_num, exc)
            continue

        page_books = parse_listing_page(soup)
        logger.info("Page %s/%s -> %s books found", page_num, TOTAL_PAGES, len(page_books))

        for raw_book in page_books:
            try:
                enriched = enrich_with_detail_page(raw_book)
                all_books.append(enriched)
            except (requests.RequestException, AttributeError, IndexError) as exc:
                logger.warning("Skipping '%s' due to error: %s", raw_book["title"], exc)
            time.sleep(REQUEST_DELAY_SECONDS)

        time.sleep(REQUEST_DELAY_SECONDS)

    return all_books


def save_to_csv(books: list[Book], output_path: Path = OUTPUT_PATH) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(books[0]).keys()))
        writer.writeheader()
        for book in books:
            writer.writerow(asdict(book))
    logger.info("Saved %s books to %s", len(books), output_path)


def main() -> None:
    logger.info("Starting full scrape of %s pages (~1000 books)...", TOTAL_PAGES)
    books = scrape_all_books()
    if not books:
        logger.error("No books scraped -- aborting CSV write.")
        return
    save_to_csv(books)
    logger.info("Done. Run the cleaning step next: python data_cleaning.py")


if __name__ == "__main__":
    main()
