from binance.client import Client
import pandas as pd
import time
import requests
import os
from Technicalindicatorstrategy import TurtleMACDTimeZoneFilter
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

# Binance API Key (可為空)
client = Client(api_key='', api_secret='')

# Telegram config
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 負責將分析結果推送到你的 Telegram。
def send_telegram_message(message):
    apiURL = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    try:
        response = requests.post(apiURL, json={
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'Markdown'
        })
        print(response.text)
    except Exception as e:
        print(e)

# 取得成交量最高的 USDT 交易對，過濾掉 BULL/BEAR 等槓桿代幣。
def get_top_symbols(limit=100, quote_asset='USDT'):
    tickers = client.get_ticker()
    usdt_pairs = [
        t for t in tickers if t['symbol'].endswith(quote_asset)
        and not t['symbol'].endswith('BULLUSDT')
        and not t['symbol'].endswith('BEARUSDT')
    ]
    sorted_pairs = sorted(usdt_pairs, key=lambda x: float(x['quoteVolume']), reverse=True)
    return [t['symbol'] for t in sorted_pairs[:limit]]

# 驅動整個流程，循環處理每個幣種、分析、通知。
def main():
    long_symbols = []
    short_symbols = []
    top_symbols = ['BTCUSDT','ETHUSDT','SOLUSDT','XRPUSDT','BNBUSDT','ADAUSDT']#get_top_symbols()

    # 循環處理每個幣種、分析、通知。
    for symbol in top_symbols:
        print(f"分析 {symbol}...")
        try:
            result = TurtleMACDTimeZoneFilter.get_signals(symbol=symbol, interval='2h', end_time=datetime.now(), limit = 500).tail(1)
            if result["signal"].values[0] == 1:
                print(f"{symbol} 多單訊號 - 海龜多單 原因:{result['reason'].values[0]} 進場價格:{result['entry_price'].values[0]} 停損:{result['stop_loss'].values[0]}")
                long_symbols.append(f"{symbol} (海龜多單) 原因:{result['reason'].values[0]} 進場價格:{result['entry_price'].values[0]} 停損:{result['stop_loss'].values[0]}")
            if result["signal"].values[0] == -1:
                print(f"{symbol} 空單訊號 - 海龜空單 原因:{result['reason'].values[0]} 進場價格:{result['entry_price'].values[0]} 停損:{result['stop_loss'].values[0]}")
                short_symbols.append(f"{symbol} (海龜空單) 原因:{result['reason'].values[0]} 進場價格:{result['entry_price'].values[0]} 停損:{result['stop_loss'].values[0]}")
        except Exception as e:
            print(f"{symbol} 分析失敗: {e}")
        time.sleep(0.5)

    # 整理訊息後發送
    message = ""
    if long_symbols:
        message += "📈 *符合 海龜 多單條件的幣種:*\n" + "\n".join(long_symbols) + "\n\n"
    if short_symbols:
        message += "📉 *符合 海龜 空單條件的幣種:*\n" + "\n".join(short_symbols)
    if not message:
        message = "❌ 目前無幣種符合 海龜 多單或空單條件"
    send_telegram_message(message)

# 主程序
if __name__ == "__main__":
    main()