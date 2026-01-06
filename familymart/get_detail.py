import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import os

BASE_URL = "https://www.family.co.jp"


def get_price_from_goods_page(url):
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        price_span = soup.find("span", class_="ly-kakaku-usual")
        if not price_span:
            return ""

        text = price_span.get_text(strip=True)
        m = re.search(r"税込\s*([0-9,]+)円", text)
        if m:
            return f"{m.group(1)}円(税込)"

        return ""

    except Exception as e:
        print("価格取得失敗:", e)
        return ""


def scrape_familymart_safety(url, category):
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")

    items = soup.select("li")
    results = []

    for item in items:
        name_tag = item.select_one(".item_basic_info .name a")
        if not name_tag:
            continue

        name = name_tag.get_text(strip=True)
        goods_url = name_tag["href"]
        if goods_url.startswith("/"):
            goods_url = BASE_URL + goods_url

        # 画像URL
        img_tag = item.select_one("img")
        if img_tag and img_tag.get("src"):
            img_src = img_tag["src"]
            img_url = BASE_URL + img_src if img_src.startswith("/") else img_src
        else:
            img_url = ""

        # 栄養成分
        nut_values = item.select(".item_nutritional_info td.con_nut")
        if len(nut_values) == 5:
            kcal, protein, fat, carb, salt = [v.get_text(strip=True) for v in nut_values]
            kcal = f"{kcal}kcal"
            protein = f"{protein}g"
            fat = f"{fat}g"
            carb = f"{carb}g"
            salt = f"{salt}g"
        else:
            kcal = protein = fat = carb = salt = ""

        price = get_price_from_goods_page(goods_url)

        results.append({
            "カテゴリ": category,
            "商品名": name,
            "価格": price,
            "画像URL": img_url,
            "URL": goods_url,
            "熱量": kcal,
            "たんぱく質": protein,
            "脂質": fat,
            "炭水化物": carb,
            "糖質": "",
            "食物繊維": "",
            "食塩相当量": salt,
        })

        time.sleep(1)

    return results


def main():
    all_results = []

    with open("urls_all.txt", "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]

    print(f"{len(urls)} 件の一覧ページを処理します")

    for i, url in enumerate(urls, 1):
        # ★ URLからカテゴリ名を生成
        # goods010.html → goods010
        category = os.path.basename(url).replace(".html", "")

        print(f"\n[{i}/{len(urls)}] 処理中: {url} / CATEGORY={category}")

        data = scrape_familymart_safety(url, category)
        all_results.extend(data)

        time.sleep(2)

    if not all_results:
        print("データが取得できませんでした")
        return

    df = pd.DataFrame(all_results)

    df = df[
        [
            "カテゴリ",
            "商品名",
            "価格",
            "画像URL",
            "URL",
            "熱量",
            "たんぱく質",
            "脂質",
            "炭水化物",
            "糖質",
            "食物繊維",
            "食塩相当量",
        ]
    ]

    df.to_csv("familymart_all_with_images.csv", index=False, encoding="utf-8-sig")
    print("\n保存完了: familymart_all_with_images.csv")


if __name__ == "__main__":
    main()
