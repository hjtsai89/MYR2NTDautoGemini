import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
import re

def get_bot_rate():
    """抓取台灣銀行 USD/TWD 賣出匯率"""
    url = "https://rate.bot.com.tw/xrt?Lang=zh-TW"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    response = requests.get(url, headers=headers)
    df = pd.read_html(response.text)[0]
    # 取得「本行即期賣出」USD 匯率 (第 5 欄，索引 4)
    usd_twd = df.iloc[0, 4]
    return float(usd_twd)

def get_hsbc_rate():
    """抓取 HSBC Malaysia USD/MYR 即期買入匯率 (TT Buy)"""
    # 這是 HSBC 正確的即時匯率數據頁面
    url = "https://www.hsbc.com.my/investments/products/foreign-exchange/currency-rate/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    target_row = None
    # 遍歷所有表格行，尋找包含 "USD" 的行
    for row in soup.find_all('tr'):
        cells = row.find_all('td')
        if len(cells) > 0 and 'USD' in cells[0].get_text():
            target_row = row
            break
            
    if target_row:
        cols = target_row.find_all('td')
        # HSBC 表格結構預期為: 
        # [0]Currency | [1]Name | [2]TT Sell | [3]TT Buy
        # 取得 TT Buy (第 4 欄，索引 3)
        rate_text = cols[3].get_text(strip=True)
        # 使用正規表達式提取純數字 (例如: 4.7120)
        rate = re.findall(r"\d+\.\d+", rate_text)[0]
        return float(rate)
    else:
        raise Exception("無法在 HSBC 頁面找到 USD/MYR TT Buy 數據")

def main():
    try:
        twd_rate = get_bot_rate()
        myr_rate = get_hsbc_rate()
        
        file_name = "exchange_rates.csv"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 準備寫入資料
        df_new = pd.DataFrame([[now, twd_rate, myr_rate]], columns=["Date", "USD_TWD", "USD_MYR_TTBuy"])
        
        # 儲存至 CSV
        if not os.path.isfile(file_name):
            df_new.to_csv(file_name, index=False, encoding='utf-8-sig')
        else:
            df_new.to_csv(file_name, mode='a', header=False, index=False, encoding='utf-8-sig')
            
        print(f"成功更新: {now} | TWD Sell: {twd_rate} | MYR TT Buy: {myr_rate}")
        
    except Exception as e:
        print(f"執行出錯: {e}")
        exit(1)

if __name__ == "__main__":
    main()
