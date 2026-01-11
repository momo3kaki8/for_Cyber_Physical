import requests
from bs4 import BeautifulSoup
import time
import re
import csv
import os

CSV_FILE = "seven_eleven.csv"

FIELDNAMES = [
    "カテゴリ", "商品名", "価格", "画像URL", "商品URL",
    "熱量", "たんぱく質", "脂質", "炭水化物",
    "糖質", "食物繊維", "食塩相当量"
]

BASE_URL = "https://www.sej.co.jp"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# CSV初期化
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()


# --------------------------------
# URL① → カテゴリ名
# --------------------------------
def extract_category(url):
    return url.rstrip("/").split("/")[-1]


# --------------------------------
# 栄養成分パース
# --------------------------------
def parse_nutrition_text(text):
    result = {k: "" for k in FIELDNAMES[5:]}

    patterns = {
        "熱量": r"熱量：([\d.]+kcal)",
        "たんぱく質": r"たんぱく質：([\d.]+g)",
        "脂質": r"脂質：([\d.]+g)",
        "炭水化物": r"炭水化物：([\d.]+g)",
        "糖質": r"糖質：([\d.]+g)",
        "食物繊維": r"食物繊維：([\d.]+g)",
        "食塩相当量": r"食塩相当量：([\d.]+g)",
    }

    for k, p in patterns.items():
        m = re.search(p, text)
        if m:
            result[k] = m.group(1)

    return result


# --------------------------------
# URL① → URL②
# --------------------------------
def collect_lineup_urls(urls):
    results = []

    for url in urls:
        category = extract_category(url)
        print(f"チェック中: {url}")

        soup = BeautifulSoup(
            requests.get(url, headers=HEADERS, timeout=15).text,
            "html.parser"
        )

        found = False
        for a in soup.find_all("a"):
            if "ラインナップを見る" in a.get_text(strip=True):
                href = a.get("href")
                if href:
                    results.append(
                        (category, BASE_URL + href if href.startswith("/") else href)
                    )
                    found = True

        if not found:
            results.append((category, url))

        time.sleep(1)

    return list(dict.fromkeys(results))


# --------------------------------
# ページネーション
# --------------------------------
def collect_pagination_urls(url):
    urls = {url}

    soup = BeautifulSoup(
        requests.get(url, headers=HEADERS, timeout=15).text,
        "html.parser"
    )

    for a in soup.select(".pager a"):
        href = a.get("href")
        if href:
            urls.add(BASE_URL + href if href.startswith("/") else href)

    return sorted(urls)


# --------------------------------
# 商品一覧
# --------------------------------
def scrape_item_list(url):
    soup = BeautifulSoup(
        requests.get(url, headers=HEADERS, timeout=15).text,
        "html.parser"
    )

    items = []

    for block in soup.select("div.list_inner"):
        name_tag = block.select_one(".item_ttl a")
        if not name_tag:
            continue

        price = ""
        price_tag = block.select_one(".item_price p")
        if price_tag:
            m = re.search(r"税込([0-9.]+)円", price_tag.get_text())
            if m:
                price = f"{m.group(1)}円(税込)"

        items.append({
            "商品名": name_tag.get_text(strip=True),
            "商品URL": BASE_URL + name_tag["href"],
            "画像URL": block.select_one("img")["data-original"],
            "価格": price
        })

    return items


# --------------------------------
# 商品詳細
# --------------------------------
def scrape_item_detail(url, retry=2):
    for _ in range(retry + 1):
        try:
            soup = BeautifulSoup(
                requests.get(url, headers=HEADERS, timeout=15).text,
                "html.parser"
            )

            th = soup.find("th", string="栄養成分")
            if not th:
                return {}

            td = th.find_next_sibling("td")
            return parse_nutrition_text(td.get_text(strip=True))

        except requests.exceptions.ReadTimeout:
            time.sleep(5)

    return {}


def append_csv(row):
    with open(CSV_FILE, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writerow(row)


# --------------------------------
# main
# --------------------------------
def main():
    with open("urls_category.txt", encoding="utf-8") as f:
        urls = [l.strip() for l in f if l.strip()]

    url2_list = collect_lineup_urls(urls)

    for category, base_url in url2_list:
        print(f"\nカテゴリ処理: {category}")

        for page_url in collect_pagination_urls(base_url):
            for item in scrape_item_list(page_url):
                nutrition = scrape_item_detail(item["商品URL"])

                append_csv({
                    "カテゴリ": category,
                    **item,
                    **nutrition
                })

                time.sleep(1)

            time.sleep(2)

    print("\n保存完了:", CSV_FILE)


if __name__ == "__main__":
    main()
