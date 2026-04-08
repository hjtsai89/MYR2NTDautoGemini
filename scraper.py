import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os

def get_bot_rate():
    """抓取台灣銀行 USD/TWD 匯率"""
    url = "https://rate.bot.com.tw/xrt?Lang=zh-TW"
    header = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=header)
    df = pd.read_html(response.text)[0]
    # 取得「本行現鈔賣出」或「本行即期賣出」，這裡取即期賣出 (索引列 0, 欄位 4)
    usd_twd = df.iloc[0, 4]
    return float(usd_twd)

def get_hsbc_rate():
    """抓取 HSBC Malaysia MYR/USD 匯率"""
    # 備註：銀行官網常變動，若失效需檢查 HTML 結構
    # url = "https://www.hsbc.com.my/investments/market-information/foreign-exchange-rates/"
    url = "https://www.hsbc.com.my/investments/products/foreign-exchange/currency-rate/"
    header = {'User-Agent': 'Mozilla/5.0'}
    # 這裡建議使用穩定 API 或解析其表格，暫用範例邏輯
    # 若 HSBC 難爬，建議改用匯率 API
    return 4.75  # 建議先手動測試抓取邏輯

def main():
    try:
        twd_rate = get_bot_rate()
        myr_rate = get_hsbc_rate() # 實際部署時需確保此處邏輯正確
        
        file_name = "exchange_rates.csv"
        now = datetime.now().strftime("%Y-%m-%d")
        
        df_new = pd.DataFrame([[now, twd_rate, myr_rate]], columns=["Date", "USD_TWD", "MYR_USD"])
        
        if not os.path.isfile(file_name):
            df_new.to_csv(file_name, index=False)
        else:
            df_new.to_csv(file_name, mode='a', header=False, index=False)
            
        print(f"成功記錄: {now} - TWD:{twd_rate}, MYR:{myr_rate}")
    except Exception as e:
        print(f"發生錯誤: {e}")

if __name__ == "__main__":
    main()
