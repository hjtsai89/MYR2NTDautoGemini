import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
import os
import re

def get_bot_rate():
    url = "https://rate.bot.com.tw/xrt?Lang=zh-TW"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        df = pd.read_html(response.text)[0]
        return float(df.iloc[0, 4])
    except:
        return None

def get_hsbc_rate():
    url = "https://www.hsbc.com.my/investments/products/foreign-exchange/currency-rate/"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        for row in soup.find_all('tr'):
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 4 and "USD" in cells[0].get_text():
                rate_text = cells[3].get_text(strip=True)
                return float(re.search(r"(\d+\.\d+)", rate_text).group(1))
        return None
    except:
        return None

def main():
    twd_rate = get_bot_rate()
    myr_rate = get_hsbc_rate()
    
    if twd_rate and myr_rate:
        # 計算匯率
        twd_to_myr = round(myr_rate / twd_rate, 5)
        myr_to_twd = round(twd_rate / myr_rate, 5) # 你要的新欄位
        
        tz = timezone(timedelta(hours=8))
        now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
        
        file_name = "exchange_rates.csv"
        new_data = pd.DataFrame([[now, twd_rate, myr_rate, twd_to_myr, myr_to_twd]], 
                                columns=["Date", "USD_TWD", "USD_MYR_TTBuy", "TWD_MYR", "MYR_TWD"])
        
        if not os.path.isfile(file_name):
            new_data.to_csv(file_name, index=False, encoding='utf-8-sig')
        else:
            new_data.to_csv(file_name, mode='a', header=False, index=False, encoding='utf-8-sig')
        
        # 輸出到 GitHub Actions 的環境變數
        if 'GITHUB_OUTPUT' in os.environ:
            with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                f.write(f"myr_twd={myr_to_twd}\n")
                f.write(f"update_time={now}\n")
        
        print(f"成功記錄: MYR/TWD = {myr_to_twd}")
    else:
        print("抓取失敗，請檢查網頁結構。")
        exit(1)

if __name__ == "__main__":
    main()
