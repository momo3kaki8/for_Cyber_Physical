import time
import os
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from urllib.parse import urlparse

BASE_URL = "https://www.lawson.co.jp"
INPUT_FILE = "urls_all.txt"


def extract_category_name(url: str) -> str:
    """
    URL末尾のカテゴリ名を取得
    例: https://.../rice/ → rice
    """
    path = urlparse(url).path.rstrip("/")
    return path.split("/")[-1]


def collect_urls(driver, category_url: str) -> list:
    print(f"一覧ページにアクセス中: {category_url}")
    driver.get(category_url)

    # 初期読み込み待ち
    time.sleep(8)

    # スクロールして商品を読み込む
    print("ページをスクロールして商品を読み込んでいます...")
    for i in range(3):
        driver.execute_script("window.scrollBy(0, 1000);")
        time.sleep(2)
        print(f"  スクロール中... ({i+1}/3)")

    soup = BeautifulSoup(driver.page_source, "html.parser")

    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/recommend/original/detail/" in href:
            full_url = BASE_URL + href if href.startswith("/") else href
            links.append(full_url)

    return sorted(set(links))


def get_and_save_urls():
    # --- ブラウザ設定 ---
    options = uc.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = uc.Chrome(options=options, version_main=139)

    try:
        # カテゴリURL一覧を読み込む
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            category_urls = [line.strip() for line in f if line.strip()]

        print(f"{len(category_urls)} 件のカテゴリURLを処理します")

        for category_url in category_urls:
            category_name = extract_category_name(category_url)
            output_file = f"urls_{category_name}.txt"

            links = collect_urls(driver, category_url)

            if links:
                with open(output_file, "w", encoding="utf-8") as f:
                    for url in links:
                        f.write(url + "\n")

                print("-" * 40)
                print(f"{category_name}: {len(links)} 件保存 → {output_file}")
                print("上位5件:")
                for u in links[:5]:
                    print(f"  - {u}")
                print("-" * 40)
            else:
                print(f"警告: {category_name} はURLが取得できませんでした")

    except Exception as e:
        print(f"エラーが発生しました: {e}")

    finally:
        driver.quit()


if __name__ == "__main__":
    get_and_save_urls()
