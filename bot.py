import os
import requests
import pandas as pd
from datetime import datetime
from binance.client import Client

# --- إعدادات البيئة ---
BINANCE_API_KEY = os.environ.get('BINANCE_API_KEY')
BINANCE_API_SECRET = os.environ.get('BINANCE_API_SECRET')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)

BLACKLIST = {'LINK', 'BTT', 'TOMO', 'MATIC', 'ARES', 'GARD', 'BB', 'WBETH', 'WNXM', 'PHM', 'SPEC', 'RAFT', 'NIZA', 'REN', 'XVS', 'SHIB', 'KMNO', 'OMNI', 'CAKE', 'BZRX', 'HEGIC', 'BETA', 'FRONT', 'RAMP', 'PERP', 'KAVA', 'ALPACA', 'RUNE', 'KCS', 'DF', 'OM', 'MLN', 'YFI', 'GNO', 'MIR', 'BADGER', 'SYNC', 'TROY', 'ZRO', 'AKRO', 'BURGER', 'SUN', 'MBOX', 'OIN', 'PIG', 'FARM', 'WBTC', 'MEAN', 'TUT', 'AERO', 'NIL', 'CRH', 'RED', 'BTL', 'LAYER', 'CNAME', 'TST', 'BERA', 'LEMN', 'ACT', 'OLAND', 'BIO', 'SOLV', 'EYWA', 'CGPT', 'BPT', 'HIVP', 'PENGU', 'IZI', 'VANA', 'VELO', 'ACX', 'ORCA', 'XION', 'THE', 'BMT', 'CETUS', 'VELA', 'VIRTUAL', 'STRP', 'KERNEL', 'INIT', 'WAL', 'SIGN', 'SYRUP', 'SYNTH', 'PAI', 'ATU', 'AIXBT', 'USD1', 'SAHARA', 'HNB', 'BXC', 'PUMP', 'FOREST', 'MYRO', 'PLUME', 'DOP', 'BFUSD', 'SPICE', 'LILPEPE', 'DOLO', 'OCTO', 'RESOLVE', 'EUR', 'EURI', 'FDUSD', 'USDC', 'TUSD', 'USDTTRY', 'BTC', 'ETH', 'APT', 'HBAR', 'STORJ', 'CVX', 'ZRX', 'FLOKI'}

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try: requests.post(url, json=payload)
    except: pass

def get_recent_data(symbol, interval='1h', limit=100):
    try:
        klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
        if not klines: return None
        df = pd.DataFrame(klines, columns=['Open time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close time', 'QAV', 'NoT', 'TBB', 'TBQ', 'Ignore'])
        df[['Open', 'High', 'Low', 'Close']] = df[['Open', 'High', 'Low', 'Close']].astype(float)
        return df
    except: return None

def get_candidates():
    try:
        tickers = client.get_ticker()
        candidates = []
        for t in tickers:
            sym = t['symbol']
            if sym.endswith('USDT'):
                base = sym.replace('USDT', '')
                if base not in BLACKLIST and float(t['quoteVolume']) > 2000000:
                    candidates.append(sym)
        return candidates
    except: return []

def run_bot_job():
    candidates = get_candidates()
    all_signals = []
    
    # 1. Breakout
    for sym in candidates:
        df = get_recent_data(sym, '1h', limit=60)
        if df is not None and len(df) > 50 and df.iloc[-2]['Close'] > df['High'].iloc[-50:-5].max():
            all_signals.append(f"📈 <b>Breakout 1H (LONG):</b> #{sym}")
            
    # 2. CHoCH Long
    for sym in candidates:
        df = get_recent_data(sym, '1h', limit=100)
        if df is not None and len(df) > 50 and df.iloc[-15:]['Close'].max() > df['High'].iloc[-50:-15].max():
            all_signals.append(f"🎯 <b>CHoCH 1H (LONG):</b> #{sym}")

    # 3. CHoCH Short
    for sym in candidates:
        df = get_recent_data(sym, '1h', limit=100)
        if df is not None and len(df) > 50 and df.iloc[-15:]['Close'].min() < df['Low'].iloc[-50:-15].min():
            all_signals.append(f"🔻 <b>CHoCH 1H (SHORT):</b> #{sym}")
    
    if all_signals:
        msg = "<b>🚨 Sniper Bot V22 (Hourly Scan)</b>\n\n" + "\n".join(all_signals[:10]) + "\n\n⚠️ <i>check it yourself</i>"
        send_telegram_message(msg)

run_bot_job()
