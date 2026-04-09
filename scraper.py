import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
import os
import re

# ... (保留之前的 get_bot_rate 和 get_hsbc_rate 函式) ...

def main():
    twd_rate = get_bot_rate()
    myr_rate = get_hsbc_rate()
    
    if twd_rate and myr_rate:
        # 計算 1 台幣可以換多少馬幣 (TWD/MYR)
        twd_to_myr = round(myr_rate / twd_rate, 5)
        # 計算 1 馬幣可以換多少台幣 (MYR/TWD) -> 這是你要的新增欄位
        myr_to_twd = round(twd_rate / myr_rate, 5)
        
        tz = timezone(timedelta(hours=8))
        now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
        
        file_name = "exchange_rates.csv"
        # 欄位包含：時間, 台銀賣出, HSBC買入, 台幣換馬幣, 馬幣換台幣
        new_data = pd.DataFrame([[now, twd_rate, myr_rate, twd_to_myr, myr_to_twd]], 
                                columns=["Date", "USD_TWD", "USD_MYR_TTBuy", "TWD_MYR", "MYR_TWD"])
        
        if not os.path.isfile(file_name):
            new_data.to_csv(file_name, index=False, encoding='utf-8-sig')
        else:
            new_data.to_csv(file_name, mode='a', header=False, index=False, encoding='utf-8-sig')
        
        # --- 關鍵修改：將結果傳遞給 GitHub Actions ---
        if 'GITHUB_OUTPUT' in os.environ:
            with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                f.write(f"myr_twd={myr_to_twd}\n")
                f.write(f"update_time={now}\n")
        
        print(f"✅ 記錄成功: MYR/TWD = {myr_to_twd}")

if __name__ == "__main__":
    main()
