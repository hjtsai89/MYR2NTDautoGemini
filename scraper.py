import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
import re

def get_bot_rate():
    """抓取台灣銀行 USD/TWD 賣出匯率"""
    url = "https://rate.bot.com.tw/xrt?Lang=zh-TW"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        df = pd.read_html(response.text)[0]
        # 取得「本行即期賣出」USD 匯率 (索引 4)
        usd_twd = df.iloc[0, 4]
        return float(usd_twd)
    except Exception as e:
        print(f"台銀抓取失敗: {e}")
        return None

def get_hsbc_rate():
    """抓取 HSBC Malaysia USD/MYR 即期買入匯率 (TT Buy)"""
    url = "https://www.hsbc.com.my/investments/products/foreign-exchange/currency-rate/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 尋找所有表格行
        rows = soup.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 4:
                cell_text = cells[0].get_text(strip=True)
                # 判斷是否為 USD 行
                if "USD" in cell_text or "US Dollar" in cell_text:
                    # TT Buy 通常在第 4 欄 (索引 3)
                    rate_text = cells[3].get_text(strip=True)
                    # 提取純數字
                    rate_match = re.search(r"(\d+\.\d+)", rate_text)
                    if rate_match:
                        return float(rate_match.group(1))
        
        print("在 HSBC 頁面找不到 USD 數據行")
        return None
    except Exception as e:
        print(f"HSBC 抓取失敗: {e}")
        return None

def main():
    twd_rate = get_bot_rate()
    myr_rate = get_hsbc_rate()
    
    # 檢查是否抓取成功，若兩者皆失敗則報錯退出
    if twd_rate is None or myr_rate is None:
        print("無法取得完整數據，停止寫入。")
        exit(1)

    file_name = "exchange_rates.csv"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    df_new = pd.DataFrame([[now, twd_rate, myr_rate]], columns=["Date", "USD_TWD", "USD_MYR_TTBuy"])
    
    if not os.path.isfile(file_name):
        df_new.to_csv(file_name, index=False, encoding='utf-8-sig')
    else:
        df_new.to_csv(file_name, mode='a', header=False, index=False, encoding='utf-8-sig')
        
    print(f"✅ 成功執行: {now} | TWD: {twd_rate} | MYR: {myr_rate}")

if __name__ == "__main__":
    main()
