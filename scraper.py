import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
from io import StringIO
import os
import re


def get_bot_rate():
    url = "https://rate.bot.com.tw/xrt?Lang=zh-TW"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        print(f"[BOT] status={response.status_code}, len={len(response.text)}")
        # 內容太短時（可能是地區限制/攔截頁），印出來看看到底回了什麼
        if len(response.text) < 5000:
            print(f"[BOT] 內容過短，完整內容: {response.text!r}")
        # 修掉 FutureWarning：literal html 要包成 StringIO
        df = pd.read_html(StringIO(response.text))[0]
        rate = float(df.iloc[0, 4])
        print(f"[BOT] 取得 USD/TWD = {rate}")
        return rate
    except Exception as e:
        print(f"[BOT] 抓取失敗: {type(e).__name__}: {e}")
        return None


def get_hsbc_rate():
    url = "https://www.hsbc.com.my/investments/products/foreign-exchange/currency-rate/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        print(f"[HSBC] status={response.status_code}, len={len(response.text)}")
        # 印出前 300 字，看看拿到的到底是真的匯率頁還是被擋的挑戰頁/錯誤頁
        print(f"[HSBC] 內容預覽: {response.text[:300]!r}")

        soup = BeautifulSoup(response.text, 'html.parser')
        rows_checked = 0
        for row in soup.find_all('tr'):
            cells = row.find_all(['td', 'th'])
            rows_checked += 1
            if len(cells) >= 4 and "USD" in cells[0].get_text():
                rate_text = cells[3].get_text(strip=True)
                m = re.search(r"(\d+\.\d+)", rate_text)
                if m:
                    rate = float(m.group(1))
                    print(f"[HSBC] 取得 USD/MYR = {rate}")
                    return rate
        print(f"[HSBC] 掃了 {rows_checked} 個 <tr>，沒找到符合條件的 USD 列")
        return None
    except Exception as e:
        print(f"[HSBC] 抓取失敗: {type(e).__name__}: {e}")
        return None


def main():
    twd_rate = get_bot_rate()
    myr_rate = get_hsbc_rate()

    if twd_rate and myr_rate:
        twd_to_myr = round(myr_rate / twd_rate, 5)
        myr_to_twd = round(twd_rate / myr_rate, 5)

        tz = timezone(timedelta(hours=8))
        now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

        file_name = "exchange_rates.csv"
        new_data = pd.DataFrame([[now, twd_rate, myr_rate, myr_to_twd, twd_to_myr]],
                                 columns=["Date", "USD/TWD", "USD/MYR", "MYR/TWD", "TWD/MYR"])

        if not os.path.isfile(file_name):
            new_data.to_csv(file_name, index=False, encoding='utf-8-sig')
        else:
            new_data.to_csv(file_name, mode='a', header=False, index=False, encoding='utf-8-sig')

        if 'GITHUB_OUTPUT' in os.environ:
            with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                f.write(f"myr_twd={myr_to_twd}\n")
                f.write(f"update_time={now}\n")

        print(f"成功記錄: MYR/TWD = {myr_to_twd}")
    else:
        print(f"抓取失敗，請檢查網頁結構。(twd_rate={twd_rate}, myr_rate={myr_rate})")
        exit(1)


if __name__ == "__main__":
    main()
