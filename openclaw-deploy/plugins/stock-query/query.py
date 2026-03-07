#!/usr/bin/env python3
"""单股行情查询 - 输出飞书卡片格式
用法：python query.py NVDA
"""

import sys
import json
import os
import requests
import yfinance as yf
from datetime import datetime

FINNHUB_TOKEN = os.environ.get("FINNHUB_API_KEY", "")

CN_NAMES = {
    "AAPL":"苹果","MSFT":"微软","NVDA":"英伟达","AMZN":"亚马逊","GOOGL":"谷歌",
    "META":"Meta","TSLA":"特斯拉","LLY":"礼来","UNH":"联合健康","JPM":"摩根大通",
    "V":"Visa","XOM":"埃克森美孚","MA":"万事达","AVGO":"博通","JNJ":"强生",
    "PG":"宝洁","HD":"家得宝","COST":"好市多","MRK":"默克","ABBV":"艾伯维",
    "CVX":"雪佛龙","BAC":"美国银行","WMT":"沃尔玛","NFLX":"奈飞","CRM":"赛富时",
    "AMD":"AMD","KO":"可口可乐","ORCL":"甲骨文","PEP":"百事可乐","TMO":"赛默飞",
    "GS":"高盛","UBER":"优步","BTC-USD":"比特币","ETH-USD":"以太坊","SOL-USD":"Solana",
}


def pct_color(pct):
    if pct > 0:  return f"<font color='red'>**+{pct:.2f}%**</font>"
    if pct < 0:  return f"<font color='green'>**{pct:.2f}%**</font>"
    return f"**{pct:.2f}%**"


def fetch_stock_data(symbol):
    """获取股票完整数据"""
    sym = symbol.upper()
    ticker = yf.Ticker(sym)
    info = ticker.info
    hist = ticker.history(period="1y")
    hist = hist[hist["Close"].notna()]

    # 基本行情
    price = info.get("currentPrice") or info.get("regularMarketPrice")
    prev_close = info.get("previousClose") or info.get("regularMarketPreviousClose")
    change_pct = ((price - prev_close) / prev_close * 100) if price and prev_close else 0

    # 今日行情
    hist_1d = ticker.history(period="1d")
    today_open = float(hist_1d["Open"].iloc[-1]) if not hist_1d.empty else None
    today_high = float(hist_1d["High"].iloc[-1]) if not hist_1d.empty else None
    today_low = float(hist_1d["Low"].iloc[-1]) if not hist_1d.empty else None
    volume = info.get("volume") or info.get("regularMarketVolume")

    # 52周
    h52 = float(hist["Close"].max()) if len(hist) > 0 else info.get("fiftyTwoWeekHigh")
    l52 = float(hist["Close"].min()) if len(hist) > 0 else info.get("fiftyTwoWeekLow")
    pos = round((price - l52) / (h52 - l52) * 100, 1) if h52 and l52 and h52 > l52 else None

    # 技术指标
    tech = {}
    if len(hist) >= 20:
        c = hist["Close"]
        ma5 = round(float(c.rolling(5).mean().iloc[-1]), 2)
        ma20 = round(float(c.rolling(20).mean().iloc[-1]), 2)
        ma60 = round(float(c.rolling(60).mean().iloc[-1]), 2) if len(c) >= 60 else None

        # RSI
        delta = c.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rsi = 50.0
        if loss.iloc[-1] != 0:
            rsi = round(float(100 - 100 / (1 + gain.iloc[-1] / loss.iloc[-1])), 1)

        # MACD
        ema12 = c.ewm(span=12, adjust=False).mean()
        ema26 = c.ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        macd_sig = macd_line.ewm(span=9, adjust=False).mean()
        is_golden = float(macd_line.iloc[-1]) > float(macd_sig.iloc[-1])

        # 趋势
        curr = float(c.iloc[-1])
        if curr > ma5 and ma5 > ma20:
            trend = "多头↑"
        elif curr < ma5 and ma5 < ma20:
            trend = "空头↓"
        else:
            trend = "震荡→"

        # RSI 标签
        if rsi >= 75:   rsi_label = "超买⚠"
        elif rsi >= 60: rsi_label = "偏强"
        elif rsi <= 25: rsi_label = "超卖⚠"
        elif rsi <= 40: rsi_label = "偏弱"
        else:           rsi_label = "中性"

        tech = {
            "ma5": ma5, "ma20": ma20, "ma60": ma60,
            "rsi": rsi, "rsi_label": rsi_label,
            "macd_golden": is_golden,
            "trend": trend,
        }

    # 分析师评级
    ratings = None
    if FINNHUB_TOKEN:
        try:
            r = requests.get(
                "https://finnhub.io/api/v1/stock/recommendation",
                params={"symbol": sym, "token": FINNHUB_TOKEN}, timeout=8,
            )
            data = r.json()
            if data and isinstance(data, list):
                d = data[0]
                sb, b, h, s, ss = (d.get(k, 0) for k in
                                   ["strongBuy","buy","hold","sell","strongSell"])
                total = sb + b + h + s + ss
                if total > 0:
                    bull = (sb + b) / total
                    bear = (s + ss) / total
                    if bull >= 0.6:   con = "强烈买入"
                    elif bull >= 0.45: con = "买入"
                    elif bear >= 0.3:  con = "卖出"
                    else:             con = "持有"
                    ratings = {
                        "consensus": con,
                        "strong_buy": sb, "buy": b, "hold": h, "sell": s, "strong_sell": ss,
                        "target_price": info.get("targetMeanPrice"),
                    }
        except:
            pass

    # 新闻
    news = []
    try:
        news_data = ticker.news or []
        news = [n.get("title", "") for n in news_data[:3]]
    except:
        pass

    return {
        "symbol": sym,
        "name": CN_NAMES.get(sym, info.get("longName", sym)),
        "price": round(price, 2) if price else None,
        "change_pct": round(change_pct, 2),
        "prev_close": round(prev_close, 2) if prev_close else None,
        "open": round(today_open, 2) if today_open else None,
        "high": round(today_high, 2) if today_high else None,
        "low": round(today_low, 2) if today_low else None,
        "volume": volume,
        "market_cap": info.get("marketCap"),
        "pe": info.get("trailingPE"),
        "h52": round(h52, 2) if h52 else None,
        "l52": round(l52, 2) if l52 else None,
        "pos52": pos,
        "tech": tech,
        "ratings": ratings,
        "news": news,
    }


def build_card(data):
    """构建飞书卡片"""
    sym = data["symbol"]
    name = data["name"]
    price = data["price"]
    pct = data["change_pct"]

    # 卡片颜色
    if pct >= 3:     color = "green"
    elif pct >= 0:   color = "blue"
    elif pct >= -3:  color = "yellow"
    else:            color = "red"

    elements = []

    def div(md):
        elements.append({"tag": "div", "text": {"tag": "lark_md", "content": md}})

    def hr():
        elements.append({"tag": "hr"})

    # 基本信息
    div(f"**{sym}** {name}　{pct_color(pct)}　**${price}**")
    hr()

    # 今日行情
    lines = ["📊 **今日行情**"]
    if data["open"]:
        lines.append(f"> 开盘 ${data['open']}　最高 ${data['high']}　最低 ${data['low']}")
    if data["volume"]:
        vol_str = f"{data['volume']/1e6:.1f}M" if data['volume'] >= 1e6 else f"{data['volume']/1e3:.0f}K"
        lines.append(f"> 成交量 {vol_str}")
    if data["market_cap"]:
        cap = data["market_cap"]
        if cap >= 1e12:
            cap_str = f"${cap/1e12:.2f}万亿"
        elif cap >= 1e9:
            cap_str = f"${cap/1e9:.0f}亿"
        else:
            cap_str = f"${cap/1e6:.0f}M"
        lines.append(f"> 市值 {cap_str}　PE {data['pe']:.1f}" if data['pe'] else f"> 市值 {cap_str}")
    div("\n".join(lines))
    hr()

    # 52周位置
    if data["h52"] and data["l52"]:
        pos_str = f"在高点 **{data['pos52']:.0f}%**" if data["pos52"] else ""
        div(f"📈 **52周区间**\n> ${data['l52']} ~ ${data['h52']}　{pos_str}")
        hr()

    # 技术指标
    if data["tech"]:
        t = data["tech"]
        macd_str = "金叉↑" if t["macd_golden"] else "死叉↓"
        ma_str = f"MA5={t['ma5']} MA20={t['ma20']}"
        if t["ma60"]:
            ma_str += f" MA60={t['ma60']}"
        div(f"🔬 **技术面**\n> 趋势 **{t['trend']}**　RSI {t['rsi']} {t['rsi_label']}　{macd_str}\n> {ma_str}")
        hr()

    # 分析师评级
    if data["ratings"]:
        r = data["ratings"]
        emoji = {"强烈买入": "🟢", "买入": "📈", "持有": "➡️", "卖出": "📉"}.get(r["consensus"], "")
        rating_str = f"{emoji} **{r['consensus']}**　强买{r['strong_buy']} 买入{r['buy']} 持有{r['hold']} 卖出{r['sell']} 强卖{r['strong_sell']}"
        if r.get("target_price"):
            upside = (r["target_price"] - price) / price * 100
            rating_str += f"\n> 目标价 ${r['target_price']:.2f}　上行空间 {pct_color(upside)}"
        div(f"🏦 **分析师评级**\n> {rating_str}")
        hr()

    # 新闻
    if data["news"]:
        news_lines = ["📰 **近期新闻**"]
        for n in data["news"]:
            news_lines.append(f"> • {n[:50]}...")
        div("\n".join(news_lines))
        hr()

    div("_数据来源：Yahoo Finance · Finnhub_")

    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": f"📊 {sym} {name} 行情"},
            "template": color,
        },
        "elements": elements,
    }


def main():
    if len(sys.argv) < 2:
        print("用法：python query.py NVDA")
        sys.exit(1)

    symbol = sys.argv[1].upper()

    try:
        data = fetch_stock_data(symbol)
        card = build_card(data)
        print(json.dumps(card, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
