import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import glob

BASE_URL = "https://www.lawson.co.jp"


def get_data_by_requests(url):
    print(f"Fetching: {url}")
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, "html.parser")

        data = {"URL": url}

        # 1. 商品名
        title_tag = soup.find("h2", class_="ttl") or soup.find("h1")
        data["商品名"] = title_tag.get_text(strip=True) if title_tag else "商品名不明"

        # 2. 画像URL
        img_tag = soup.find("img", src=lambda s: s and "/recommend/original/detail/img/" in s)
        if img_tag:
            img_src = img_tag.get("src")
            data["画像URL"] = BASE_URL + img_src if img_src.startswith("/") else img_src
        else:
            data["画像URL"] = "画像なし"

        # 3. 価格
        price_tag = soup.find("dl", class_="price")
        if price_tag:
            data["価格"] = price_tag.get_text(strip=True).replace("ローソン標準価格", "")

        # 4. 栄養成分
        nutrition_div = soup.find("div", class_="nutritionFacts_table")
        if nutrition_div:
            for dl in nutrition_div.find_all("dl"):
                dt, dd = dl.find("dt"), dl.find("dd")
                if dt and dd:
                    data[dt.get_text(strip=True)] = dd.get_text(strip=True)

        return data

    except Exception as e:
        print(f"Error: {e}")
        return None


def process_category(txt_file):
    category_name = txt_file.replace("urls_", "").replace(".txt", "")
    print(f"\n=== カテゴリ処理開始: {category_name} ===")

    with open(txt_file, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]

    all_data = []

    for i, url in enumerate(urls):
        print(f"[{i+1}/{len(urls)}]", end=" ")
        result = get_data_by_requests(url)
        if result:
            result["カテゴリ"] = category_name
            all_data.append(result)
        time.sleep(1)

    if not all_data:
        print(f"{category_name}: データ取得なし")
        return

    df = pd.DataFrame(all_data)

    # 列順整理
    first_cols = ["カテゴリ", "商品名", "価格", "画像URL", "URL"]
    other_cols = [c for c in df.columns if c not in first_cols]
    existing_first_cols = [c for c in first_cols if c in df.columns]
    df = df[existing_first_cols + other_cols]

    output_csv = f"lawson_{category_name}.csv"
    df.to_csv(output_csv, index=False, encoding="utf-8-sig")

    print(f"完了！ {output_csv} に {len(df)} 件保存しました")


def main():
    txt_files = sorted(glob.glob("urls/urls_*.txt"))

    if not txt_files:
        print("エラー: urls/urls_*.txt が見つかりません")
        return

    print(f"{len(txt_files)} カテゴリを処理します")

    for txt_file in txt_files:
        process_category(txt_file)

    print("\n=== すべてのカテゴリ処理が完了しました ===")


if __name__ == "__main__":
    main()
