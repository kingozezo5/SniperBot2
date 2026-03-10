import time
import schedule
import requests
import pandas as pd
from datetime import datetime
from binance.client import Client

# ==========================================
# ⚙️ إعدادات البوت وتليجرام
# ==========================================
BINANCE_API_KEY = os.environ.get('BINANCE_API_KEY')
BINANCE_API_SECRET = os.environ.get('BINANCE_API_SECRET')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)

# ==========================================
# 🛑 قائمة الحظر (تأكد أنها مكتوبة بالاسم الأساسي للعملة)
# ==========================================
BLACKLIST = {
    'LINK', 'BTT', 'TOMO', 'MATIC', 'ARES', 'GARD', 'BB', 'WBETH', 'WNXM', 'PHM', 'SPEC', 'RAFT', 'NIZA', 'REN', 'XVS',
    'SHIB', 'KMNO', 'OMNI', 'CAKE', 'BZRX', 'HEGIC', 'BETA', 'FRONT', 'RAMP', 'PERP',
    'KAVA', 'ALPACA', 'RUNE', 'KCS', 'DF', 'OM', 'MLN', 'YFI', 'GNO', 'MIR', 'BADGER',
    'SYNC', 'TROY', 'ZRO', 'AKRO', 'BURGER', 'SUN', 'MBOX', 'OIN', 'PIG', 'FARM', 'WBTC',
    'MEAN', 'TUT', 'AERO', 'NIL', 'CRH', 'RED', 'BTL', 'LAYER', 'CNAME', 'TST', 'BERA',
    'LEMN', 'ACT', 'OLAND', 'BIO', 'SOLV', 'EYWA', 'CGPT', 'BPT', 'HIVP', 'PENGU', 'IZI',
    'VANA', 'VELO', 'ACX', 'ORCA', 'XION', 'THE', 'BMT', 'CETUS', 'VELA', 'VIRTUAL',
    'STRP', 'KERNEL', 'INIT', 'WAL', 'SIGN', 'SYRUP', 'SYNTH', 'PAI', 'ATU', 'AIXBT',
    'USD1', 'SAHARA', 'HNB', 'BXC', 'PUMP', 'FOREST', 'MYRO', 'PLUME', 'DOP', 'BFUSD',
    'SPICE', 'LILPEPE', 'DOLO', 'OCTO', 'RESOLVE', 'EUR', 'EURI', 'FDUSD', 'USDC',
    'TUSD', 'USDTTRY', 'BTC', 'ETH', 'APT', 'HBAR', 'STORJ', 'CVX', 'ZRX', 'FLOKI'
}

# ==========================================
# 🧠 الذاكرة لمنع التكرار (Cooldown)
# ==========================================
sent_alerts_cache = {}
COOLDOWN_HOURS = 12 

def is_new_alert(strategy_name, symbol):
    current_time = datetime.now()
    key = f"{strategy_name}_{symbol}"
    if key in sent_alerts_cache:
        last_time = sent_alerts_cache[key]
        if (current_time - last_time).total_seconds() / 3600 < COOLDOWN_HOURS:
            return False
    sent_alerts_cache[key] = current_time
    return True

# ==========================================
# 🛠️ دالات العمل
# ==========================================
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram Error: {e}")

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
                # استخراج اسم العملة الحقيقي (مثل LINK)
                base = sym.replace('USDT', '')
                if base not in BLACKLIST and float(t['quoteVolume']) > 2000000:
                    candidates.append(sym)
        return candidates
    except: return []

# ==========================================
# 🔍 الاستراتيجيات
# ==========================================
def scan_breakout_1h(candidates):
    results = []
    for sym in candidates:
        df = get_recent_data(sym, '1h', limit=60)
        if df is None or len(df) < 50: continue
        if df.iloc[-2]['Close'] > df['High'].iloc[-50:-5].max():
            if is_new_alert("Breakout_Long", sym):
                results.append(f"📈 <b>Breakout 1H (LONG):</b> #{sym}")
    return results

def scan_choch_1h_long(candidates):
    results = []
    for sym in candidates:
        df = get_recent_data(sym, '1h', limit=100)
        if df is None or len(df) < 50: continue
        lookback = df.iloc[-50:-15]
        last_lh = lookback['High'].max()
        if df.iloc[-15:]['Close'].max() > last_lh:
            if is_new_alert("Choch_Long", sym):
                results.append(f"🎯 <b>CHoCH 1H (LONG):</b> #{sym}")
    return results

def scan_choch_1h_short(candidates):
    results = []
    for sym in candidates:
        df = get_recent_data(sym, '1h', limit=100)
        if df is None or len(df) < 50: continue
        lookback = df.iloc[-50:-15]
        last_ll = lookback['Low'].min()
        if df.iloc[-15:]['Close'].min() < last_ll:
            if is_new_alert("Choch_Short", sym):
                results.append(f"🔻 <b>CHoCH 1H (SHORT):</b> #{sym}")
    return results

def run_bot_job():
    candidates = get_candidates()
    all_signals = []
    all_signals.extend(scan_breakout_1h(candidates))
    all_signals.extend(scan_choch_1h_long(candidates))
    all_signals.extend(scan_choch_1h_short(candidates))
    
    if all_signals:
        msg = "<b>🚨 Sniper Bot V22 (Hourly Scan)</b>\n\n" + "\n".join(all_signals) + "\n\n⚠️ <i>possible breakout check it yourself before you decide to trade</i>"
        send_telegram_message(msg)

if __name__ == "__main__":
    print("🤖 Bot Started...")
    schedule.every().hour.at(":01").do(run_bot_job)
    while True:
        schedule.run_pending()
        time.sleep(1)