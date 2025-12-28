import time
import undetected_chromedriver as uc
from bs4 import BeautifulSoup

def get_and_save_urls():
    # --- ブラウザ設定 ---
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    # バージョン不一致対策(139を指定)
    driver = uc.Chrome(options=options, version_main=139)
    
    # 収集対象のカテゴリ
    CATEGORY_URL = "https://www.lawson.co.jp/recommend/original/rice/"
    BASE_URL = "https://www.lawson.co.jp"
    
    try:
        print(f"一覧ページにアクセス中: {CATEGORY_URL}")
        driver.get(CATEGORY_URL)
        
        # 1. 初期読み込み待ち
        time.sleep(8)
        
        # 2. 段階的にスクロールして全商品を読み込ませる (合計3000px分)
        print("ページをスクロールして商品を読み込んでいます...")
        for i in range(3):
            driver.execute_script(f"window.scrollBy(0, 1000);")
            time.sleep(2)
            print(f"  スクロール中... ({i+1}/3)")

        # 3. 解析
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        links = []
        
        # 詳細ページURLのパターンを抽出
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/recommend/original/detail/' in href:
                # 相対パスを絶対パスに変換
                full_url = BASE_URL + href if href.startswith('/') else href
                links.append(full_url)
        
        # 重複を排除
        links = sorted(list(set(links)))
        
        # 4. ファイル保存
        if links:
            with open("urls_rice.txt", "w", encoding="utf-8") as f:
                for url in links:
                    f.write(url + "\n")
            print("-" * 30)
            print(f"成功！ {len(links)} 件のURLを 'urls_rice.txt' に保存しました。")
            print("上位5件を表示:")
            for u in links[:5]:
                print(f"  - {u}")
            print("-" * 30)
        else:
            print("警告: URLが見つかりませんでした。")
            
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    get_and_save_urls()