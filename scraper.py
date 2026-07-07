import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
import os
import re


def get_bot_rate():
    # rate.bot.com.tw 的網頁本體與 CSV 端點皆已被防爬蟲機制擋下 (整個網域對雲端機房 IP 有防護)。
    # 保留這個函式作為第一優先資料源，失敗時由 get_cathay_rate() 頂上。
    url = "https://rate.bot.com.tw/xrt/flcsv/0/day"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        print(f"[BOT] status={response.status_code}, len={len(response.text)}")
        if len(response.text) < 500:
            print(f"[BOT] 內容過短，完整內容: {response.text!r}")

        # CSV 每一行格式: 幣別,本行買入,現金,即期,遠期10天,...,本行賣出,現金,即期,遠期10天,...
        # 即期買入價在第 4 欄 (index 3)
        for line in response.text.strip().splitlines():
            parts = line.split(',')
            if parts and parts[0] == 'USD':
                rate = float(parts[3])
                print(f"[BOT] 取得 USD/TWD (即期買入) = {rate}")
                return rate
        print("[BOT] CSV 裡找不到 USD 這一行")
        return None
    except Exception as e:
        print(f"[BOT] 抓取失敗: {type(e).__name__}: {e}")
        return None


def get_cathay_rate():
    # 備援資料源：國泰世華銀行首頁「即時匯率」小工具用的局部 HTML 頁面。
    # 不是完整網銀主站，防護通常較寬鬆；取 USD 的「銀行賣出」價作為 USD/TWD 基準價。
    url = "https://cathaybk.com.tw/CathayBK/Web/service/partial/NewExchangeList.aspx"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        print(f"[Cathay] status={response.status_code}, len={len(response.text)}")
        if len(response.text) < 300:
            print(f"[Cathay] 內容過短，完整內容: {response.text!r}")

        soup = BeautifulSoup(response.text, 'html.parser')
        for row in soup.find_all('tr'):
            cells = row.find_all(['td', 'th'])
            row_text = ''.join(c.get_text() for c in cells)
            if 'USD' in row_text.upper():
                # 從這一列找出所有像數字的欄位，最後一個視為「銀行賣出」
                numbers = []
                for c in cells:
                    txt = c.get_text(strip=True).replace(',', '')
                    m = re.fullmatch(r"\d+\.?\d*", txt)
                    if m:
                        numbers.append(float(txt))
                if numbers:
                    sell_rate = numbers[-1]
                    print(f"[Cathay] 取得 USD/TWD (銀行賣出) = {sell_rate}")
                    return sell_rate
        print("[Cathay] 找不到 USD 這一列或無法解析數字")
        return None
    except Exception as e:
        print(f"[Cathay] 抓取失敗: {type(e).__name__}: {e}")
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
    twd_source = "BOT"

    if twd_rate is None:
        print("[main] BOT 失敗，改用國泰世華銀行備援資料源")
        twd_rate = get_cathay_rate()
        twd_source = "Cathay"

    myr_rate = get_hsbc_rate()

    if twd_rate and myr_rate:
        twd_to_myr = round(myr_rate / twd_rate, 5)
        myr_to_twd = round(twd_rate / myr_rate, 5)

        tz = timezone(timedelta(hours=8))
        now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

        file_name = "exchange_rates.csv"
        new_data = pd.DataFrame([[now, twd_rate, twd_source, myr_rate, myr_to_twd, twd_to_myr]],
                                 columns=["Date", "USD/TWD", "USD/TWD_Source", "USD/MYR", "MYR/TWD", "TWD/MYR"])

        if not os.path.isfile(file_name):
            new_data.to_csv(file_name, index=False, encoding='utf-8-sig')
        else:
            new_data.to_csv(file_name, mode='a', header=False, index=False, encoding='utf-8-sig')

        if 'GITHUB_OUTPUT' in os.environ:
            with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                f.write(f"myr_twd={myr_to_twd}\n")
                f.write(f"update_time={now}\n")

        print(f"成功記錄: MYR/TWD = {myr_to_twd} (USD/TWD 來源: {twd_source})")
    else:
        print(f"抓取失敗，請檢查網頁結構。(twd_rate={twd_rate}, myr_rate={myr_rate})")
        exit(1)


if __name__ == "__main__":
    main()
