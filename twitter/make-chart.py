#!/usr/bin/env python3
"""Clean dark-theme stock charts for Twitter - @jeeniferdq style"""
import sys, os, requests, warnings, json
import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from datetime import datetime
from pathlib import Path

os.chdir('C:/Users/firas/.openclaw/workspace')
warnings.filterwarnings('ignore')
Path("logs").mkdir(exist_ok=True)
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def get_ohlcv(symbol, period="1mo"):
    now = int(datetime.now().timestamp())
    periods = {"5d": 5*86400, "1mo": 30*86400, "3mo": 90*86400}
    start = now - periods.get(period, 30*86400)
    r = requests.get(
        f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
        params={"period1": start, "period2": now, "interval": "1d"},
        headers=HEADERS, timeout=10, verify=False
    )
    if r.status_code != 200: return None
    result = r.json().get("chart", {}).get("result", [])
    if not result: return None
    timestamps = result[0]["timestamp"]
    q = result[0]["indicators"]["quote"][0]
    df = pd.DataFrame({
        "Open": q["open"], "High": q["high"],
        "Low": q["low"], "Close": q["close"], "Volume": q["volume"],
    }, index=pd.to_datetime(timestamps, unit="s").normalize())
    df.index.name = "Date"
    return df.dropna()

def make_chart(symbol: str, period: str = "1mo", today_change: float = None) -> str:
    df = get_ohlcv(symbol, period)
    if df is None or len(df) < 3:
        return None

    out = f"logs/chart-{symbol}.png"
    price = df['Close'].iloc[-1]
    month_change = ((df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0]) * 100
    display_change = today_change if today_change is not None else month_change
    color = '#00e676' if display_change >= 0 else '#ff1744'

    # Add 20 SMA
    add_plots = [
        mpf.make_addplot(df['Close'].rolling(20).mean(), color='#ffb300', width=1.2, linestyle='--'),
    ]

    mc = mpf.make_marketcolors(
        up='#00e676', down='#ff1744',
        edge='inherit', wick='inherit',
        volume={'up': '#00e676', 'down': '#ff1744'},
        alpha=0.85,
    )
    style = mpf.make_mpf_style(
        marketcolors=mc,
        facecolor='#0d1117',
        edgecolor='#0d1117',
        figcolor='#0d1117',
        gridcolor='#21262d',
        gridstyle='-',
        gridaxis='both',
        y_on_right=True,
        rc={
            'axes.labelcolor': '#8b949e',
            'xtick.color': '#8b949e',
            'ytick.color': '#8b949e',
            'axes.edgecolor': '#21262d',
            'font.size': 10,
        }
    )

    fig, axes = mpf.plot(
        df, type='candle', style=style,
        addplot=add_plots,
        volume=True, figsize=(10, 6),
        returnfig=True,
        tight_layout=True,
        panel_ratios=(4, 1),
        datetime_format='%b %d',
        xrotation=0,
    )

    ax = axes[0]
    ax.set_title("")

    # Clean header
    fig.text(0.04, 0.95, f"${symbol}", fontsize=22, color='#f0f6fc',
             fontweight='bold', va='top')
    fig.text(0.04, 0.88, f"${price:.2f}", fontsize=16, color='#8b949e', va='top')
    fig.text(0.04, 0.82, f"{display_change:+.1f}% today" if today_change else f"{month_change:+.1f}% (1mo)",
             fontsize=14, color=color, va='top', fontweight='bold')

    # Period label
    fig.text(0.98, 0.95, period.upper(), fontsize=11, color='#8b949e',
             ha='right', va='top')

    # Subtle watermark
    fig.text(0.98, 0.02, '@jeeniferdq', fontsize=9, color='#30363d',
             ha='right', va='bottom')

    plt.savefig(out, dpi=160, bbox_inches='tight',
                facecolor='#0d1117', edgecolor='none')
    plt.close()
    print(f"Chart: {out}")
    return out

def post_with_chart(symbol, text, today_change=None, post_type="chart"):
    import tweepy
    creds = json.loads(Path("config/twitter-api.json").read_text())
    auth = tweepy.OAuth1UserHandler(
        creds["consumer_key"], creds["consumer_secret"],
        creds["access_token"], creds["access_token_secret"]
    )
    api_v1 = tweepy.API(auth)
    client = tweepy.Client(
        consumer_key=creds["consumer_key"], consumer_secret=creds["consumer_secret"],
        access_token=creds["access_token"], access_token_secret=creds["access_token_secret"],
    )

    chart_path = make_chart(symbol, today_change=today_change)
    media_ids = None
    if chart_path:
        media = api_v1.media_upload(filename=chart_path)
        media_ids = [media.media_id]

    r = client.create_tweet(text=text, media_ids=media_ids)
    tweet_id = r.data["id"]
    url = f"https://twitter.com/jeeniferdq/status/{tweet_id}"

    log_file = Path("logs/twitter-posts.json")
    log = []
    if log_file.exists():
        try: log = json.loads(log_file.read_text())
        except: pass
    log.append({"ts": datetime.now().isoformat(), "type": post_type, "text": text, "id": tweet_id, "url": url})
    log_file.write_text(json.dumps(log, indent=2))
    print(f"Posted -> {url}")
    return tweet_id, url

if __name__ == "__main__":
    sym = sys.argv[1] if len(sys.argv) > 1 else "CE"
    change = float(sys.argv[2]) if len(sys.argv) > 2 else None
    if "--post" in sys.argv:
        text = f"${sym} chart"
        post_with_chart(sym, text, today_change=change)
    else:
        make_chart(sym, today_change=change)
