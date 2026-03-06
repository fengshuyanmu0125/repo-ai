#!/usr/bin/env python3
"""美股 MCP Server - 供 openclaw bot 按需查询
数据源：
  - 行情/指数/板块/52周：Yahoo Finance (yfinance)
  - 新闻：Finnhub
  - 贪恐指数：CNN Fear & Greed API
  - 加密货币：CoinGecko
  - 分析师评级：Finnhub
"""

import json
import os
import ssl
import time
from datetime import datetime, timedelta

import pandas as pd
import requests
import yfinance as yf
from mcp.server.fastmcp import FastMCP
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context

mcp = FastMCP("us-market")

FINNHUB_TOKEN = os.environ.get("FINNHUB_TOKEN", "")

SP100 = [
    "AAPL","MSFT","NVDA","AMZN","GOOGL","META","TSLA","LLY","UNH","JPM",
    "V","XOM","MA","AVGO","JNJ","PG","HD","COST","MRK","ABBV","CVX","BAC",
    "WMT","NFLX","CRM","AMD","KO","ORCL","PEP","TMO","ACN","MCD","LIN",
    "CSCO","ABT","PM","IBM","ADBE","DHR","INTU","TXN","QCOM","GE","CAT",
    "AMGN","RTX","SPGI","NOW","ISRG","PFE","VZ","UBER","CMCSA","NEE","LOW",
    "HON","MS","BKNG","UNP","GS","AXP","COP","T","ELV","TJX","BLK","VRTX",
    "MDT","BSX","C","ADI","GILD","REGN","CB","DE","SYK","ADP","MMC","SO",
    "ETN","ZTS","PLD","TMUS","DUK","CI","MO","EOG","CME","AON","USB","PNC",
    "WM","ITW","EMR","APD","MCO","KLAC","ANET",
]

SECTOR_ETFS = {
    "科技":"XLK","通信":"XLC","非必需消费":"XLY","工业":"XLI","金融":"XLF",
    "医疗":"XLV","必需消费":"XLP","材料":"XLB","能源":"XLE","公用事业":"XLU","房地产":"XLRE",
}

CN_NAMES = {
    "AAPL":"苹果","MSFT":"微软","NVDA":"英伟达","AMZN":"亚马逊","GOOGL":"谷歌",
    "META":"Meta","TSLA":"特斯拉","JPM":"摩根大通","V":"Visa","XOM":"埃克森美孚",
    "MA":"万事达","AVGO":"博通","BAC":"美国银行","WMT":"沃尔玛","NFLX":"奈飞",
    "AMD":"AMD","GS":"高盛","UBER":"优步","CRM":"赛富时",
}


class TLSAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = create_urllib3_context()
        ctx.set_ciphers("DEFAULT@SECLEVEL=1")
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        kwargs["ssl_context"] = ctx
        super().init_poolmanager(*args, **kwargs)


CNN_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://edition.cnn.com",
    "Referer": "https://edition.cnn.com/markets/fear-and-greed",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
}


def _fetch_fear_greed():
    """内部：获取 CNN 贪恐指数"""
    r = requests.get(
        "https://production.dataviz.cnn.io/index/fearandgreed/graphdata",
        headers=CNN_HEADERS, timeout=10, verify=False,
    )
    fg = r.json().get("fear_and_greed", {})
    score = round(fg.get("score", 50))
    if score >= 75:   label = "极度贪婪"
    elif score >= 55: label = "贪婪"
    elif score >= 45: label = "中性"
    elif score >= 25: label = "恐惧"
    else:             label = "极度恐惧"
    return {"score": score, "label": label}


# ══════════════════════════════════════════════════════════════════════
# 原有工具
# ══════════════════════════════════════════════════════════════════════

@mcp.tool()
def get_market_movers(top_n: int = 10) -> str:
    """
    获取美股市值前100中，前一个交易日涨跌幅最大的股票。

    Args:
        top_n: 涨幅榜和跌幅榜各取前几名，默认10
    """
    df = yf.download(
        SP100, period="5d", interval="1d",
        auto_adjust=True, progress=False, threads=True,
    )
    close = df["Close"].dropna(how="all")
    if len(close) < 2:
        return "今天可能是非交易日，暂无数据"

    prev = close.iloc[-2]
    last = close.iloc[-1]
    pct  = ((last - prev) / prev * 100).dropna()

    data = pd.DataFrame({
        "symbol":     pct.index,
        "close":      last[pct.index].values,
        "change_pct": pct.values,
    }).sort_values("change_pct", ascending=False).reset_index(drop=True)

    trade_date = close.index[-1].strftime("%Y-%m-%d")
    gainers = data.head(top_n)
    losers  = data.tail(top_n).iloc[::-1]

    result = {
        "trade_date": trade_date,
        "gainers": [
            {"rank": i+1, "symbol": r["symbol"],
             "change_pct": round(r["change_pct"], 2), "close": round(r["close"], 2)}
            for i, (_, r) in enumerate(gainers.iterrows())
        ],
        "losers": [
            {"rank": i+1, "symbol": r["symbol"],
             "change_pct": round(r["change_pct"], 2), "close": round(r["close"], 2)}
            for i, (_, r) in enumerate(losers.iterrows())
        ],
    }
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def get_stock_news(symbol: str, max_items: int = 5) -> str:
    """
    获取指定美股的最新新闻标题。

    Args:
        symbol: 股票代码，如 NVDA、AAPL
        max_items: 最多返回几条新闻，默认5
    """
    if not FINNHUB_TOKEN:
        return "未配置 FINNHUB_TOKEN"
    try:
        ticker = yf.Ticker(symbol.upper())
        news   = ticker.news or []
        items  = [{"title": n.get("title",""), "publisher": n.get("publisher",""),
                   "link": n.get("link","")} for n in news[:max_items]]
        return json.dumps({"symbol": symbol.upper(), "news": items}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"获取失败：{e}"


@mcp.tool()
def get_stock_quote(symbol: str) -> str:
    """
    获取指定美股的实时行情（价格、涨跌、市值等）。

    Args:
        symbol: 股票代码，如 NVDA、AAPL
    """
    try:
        info = yf.Ticker(symbol.upper()).info
        result = {
            "symbol":     symbol.upper(),
            "name":       info.get("longName", CN_NAMES.get(symbol.upper(), "")),
            "price":      info.get("currentPrice") or info.get("regularMarketPrice"),
            "change_pct": round((info.get("regularMarketChangePercent") or 0) * 100, 2),
            "market_cap": info.get("marketCap"),
            "pe_ratio":   info.get("trailingPE"),
            "52w_high":   info.get("fiftyTwoWeekHigh"),
            "52w_low":    info.get("fiftyTwoWeekLow"),
        }
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"获取失败：{e}"


# ══════════════════════════════════════════════════════════════════════
# 新增工具
# ══════════════════════════════════════════════════════════════════════

@mcp.tool()
def get_market_overview() -> str:
    """
    获取市场全景：三大指数、VIX、美元指数、10年期国债收益率、贪婪/恐惧指数。
    每日开盘前或盘后调用，了解整体市场情绪。
    """
    INDEX_TICKERS = {
        "S&P 500": "^GSPC", "NASDAQ": "^IXIC", "DOW": "^DJI",
        "VIX": "^VIX", "DXY": "DX-Y.NYB", "10Y美债": "^TNX",
    }
    result = {}

    # 指数
    for name, sym in INDEX_TICKERS.items():
        try:
            hist = yf.Ticker(sym).history(period="5d")
            hist = hist[hist["Close"].notna()]
            if len(hist) >= 2:
                prev = float(hist["Close"].iloc[-2])
                last = float(hist["Close"].iloc[-1])
                result[name] = {
                    "value":      round(last, 2),
                    "change_pct": round((last - prev) / prev * 100, 2),
                }
            time.sleep(0.1)
        except Exception as e:
            result[name] = {"error": str(e)}

    # 贪恐指数
    try:
        fg_data = _fetch_fear_greed()
        result["贪/恐指数"] = fg_data if fg_data else {"error": "获取失败"}
    except Exception as e:
        result["贪/恐指数"] = {"error": str(e)}

    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def get_sector_performance() -> str:
    """
    获取美股11个SPDR板块ETF的涨跌表现，了解资金流向和板块轮动。
    返回各板块涨跌幅，按涨幅排序。
    """
    syms = list(SECTOR_ETFS.values())
    try:
        data = yf.download(syms, period="5d", interval="1d",
                           auto_adjust=True, progress=False, threads=True)
        close = data["Close"].dropna(how="all")
        if len(close) < 2:
            return "数据不足"
        prev = close.iloc[-2]
        last = close.iloc[-1]
        items = []
        for name, sym in SECTOR_ETFS.items():
            if sym in close.columns and pd.notna(prev[sym]) and pd.notna(last[sym]):
                pct = float((last[sym] - prev[sym]) / prev[sym] * 100)
                items.append({"sector": name, "etf": sym,
                              "change_pct": round(pct, 2), "price": round(float(last[sym]), 2)})
        items.sort(key=lambda x: x["change_pct"], reverse=True)
        return json.dumps({
            "date": str(close.index[-1].date()),
            "sectors": items,
            "strongest": items[0]["sector"] if items else "",
            "weakest":   items[-1]["sector"] if items else "",
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"获取失败：{e}"


@mcp.tool()
def get_stock_detail(symbol: str) -> str:
    """
    获取指定股票的详细信息：行情、52周位置、分析师评级、最新新闻。
    用于深度了解某只股票的当前状态。

    Args:
        symbol: 股票代码，如 NVDA、AAPL、TSLA
    """
    sym = symbol.upper()
    result = {"symbol": sym}

    # 行情 + 52周
    try:
        ticker = yf.Ticker(sym)
        info   = ticker.info
        hist   = ticker.history(period="1y")
        hist   = hist[hist["Close"].notna()]
        price  = info.get("currentPrice") or info.get("regularMarketPrice")
        h52    = float(hist["Close"].max()) if len(hist) > 0 else info.get("fiftyTwoWeekHigh")
        l52    = float(hist["Close"].min()) if len(hist) > 0 else info.get("fiftyTwoWeekLow")
        pos    = round((price - l52) / (h52 - l52) * 100, 1) if h52 and l52 and h52 > l52 else None

        result["quote"] = {
            "name":       info.get("longName", CN_NAMES.get(sym, sym)),
            "price":      price,
            "change_pct": round((info.get("regularMarketChangePercent") or 0) * 100, 2),
            "market_cap": info.get("marketCap"),
            "pe_ratio":   info.get("trailingPE"),
        }
        result["52w"] = {
            "high": round(h52, 2) if h52 else None,
            "low":  round(l52, 2) if l52 else None,
            "position_pct": pos,
            "note": "越接近100%说明越靠近历史高位",
        }
    except Exception as e:
        result["quote_error"] = str(e)

    # 分析师评级
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
                bull  = (sb + b) / total if total else 0
                bear  = (s + ss) / total if total else 0
                if bull >= 0.6:   con = "强烈买入"
                elif bull >= 0.45: con = "买入"
                elif bear >= 0.3:  con = "卖出"
                else:             con = "持有"
                result["analyst_ratings"] = {
                    "consensus": con, "period": d.get("period", ""),
                    "strong_buy": sb, "buy": b, "hold": h, "sell": s, "strong_sell": ss,
                }
        except Exception as e:
            result["ratings_error"] = str(e)

    # 新闻
    try:
        news = yf.Ticker(sym).news or []
        result["news"] = [{"title": n.get("title",""), "publisher": n.get("publisher","")}
                          for n in news[:5]]
    except Exception as e:
        result["news_error"] = str(e)

    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def get_crypto_prices() -> str:
    """
    获取主流加密货币实时价格：BTC、ETH、SOL、BNB。
    数据来自 CoinGecko（免费，无需 API key）。
    """
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": "bitcoin,ethereum,solana,binancecoin",
                    "vs_currencies": "usd",
                    "include_24hr_change": "true",
                    "include_market_cap": "true"},
            timeout=10,
        )
        d = r.json()
        mapping = {
            "bitcoin": "BTC", "ethereum": "ETH",
            "solana": "SOL", "binancecoin": "BNB",
        }
        result = {}
        for cg_id, ticker in mapping.items():
            if cg_id in d:
                result[ticker] = {
                    "price":      d[cg_id]["usd"],
                    "change_24h": round(d[cg_id].get("usd_24h_change", 0), 2),
                    "market_cap": d[cg_id].get("usd_market_cap"),
                }
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"获取失败：{e}"


@mcp.tool()
def get_earnings_calendar(days_ahead: int = 7) -> str:
    """
    获取未来N天内的财报日历（S&P 100 主要个股）。
    用于提前了解可能引发市场波动的重要财报时间。

    Args:
        days_ahead: 查询未来几天，默认7天
    """
    MAG7     = ["NVDA", "AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA"]
    targets  = MAG7 + ["JPM", "GS", "BAC", "MS", "V", "MA", "NFLX", "AMD",
                       "AVGO", "CRM", "ADBE", "ORCL", "QCOM", "TXN"]
    today    = datetime.now().date()
    deadline = today + timedelta(days=days_ahead)
    upcoming = []

    for sym in targets:
        try:
            cal = yf.Ticker(sym).calendar
            if cal is None:
                continue
            earn = (cal.get("Earnings Date") if isinstance(cal, dict) else None)
            if earn is None:
                continue
            if isinstance(earn, (list, tuple)):
                earn = earn[0]
            if hasattr(earn, "date"):
                earn = earn.date()
            elif isinstance(earn, str):
                earn = datetime.strptime(earn[:10], "%Y-%m-%d").date()
            if today <= earn <= deadline:
                upcoming.append({"symbol": sym, "date": str(earn),
                                 "is_mag7": sym in MAG7})
            time.sleep(0.1)
        except:
            pass

    upcoming.sort(key=lambda x: x["date"])
    return json.dumps({
        "query_range": f"{today} ~ {deadline}",
        "count": len(upcoming),
        "earnings": upcoming,
    }, ensure_ascii=False, indent=2)


@mcp.tool()
def get_fear_greed_index() -> str:
    """
    获取 CNN 贪婪/恐惧指数（0-100）。
    0=极度恐惧，50=中性，100=极度贪婪。用于判断当前市场整体情绪。
    """
    try:
        data = _fetch_fear_greed()
        return json.dumps({
            "score": data["score"], "label": data["label"],
            "interpretation": "高分说明市场情绪乐观，低分说明悲观；极端值往往预示反转",
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"获取失败：{e}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
