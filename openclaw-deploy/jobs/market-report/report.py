#!/usr/bin/env python3
"""美股日报 v4
数据源：
  - 行情：新浪财经（国内直连）
  - 指数/板块/52周：yfinance
  - 贪婪/恐惧指数：CNN Fear & Greed API
  - 新闻：Finnhub
  - 分析师评级：Finnhub
  - 加密货币：CoinGecko（免费无 key）
  - 分析：Claude API
"""

import os, re, json, time, requests, ssl
from datetime import datetime, timedelta
import pytz
import yfinance as yf
import pandas as pd
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context
import jinja2


class TLSAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = create_urllib3_context()
        ctx.set_ciphers("DEFAULT@SECLEVEL=1")
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        kwargs["ssl_context"] = ctx
        super().init_poolmanager(*args, **kwargs)


# ── 配置 ──────────────────────────────────────────────────────────────
FEISHU_APP_ID     = os.environ["FEISHU_APP_ID"]
FEISHU_APP_SECRET = os.environ["FEISHU_APP_SECRET"]
FEISHU_RECEIVE_ID = os.environ["FEISHU_RECEIVE_ID"]
ANTHROPIC_TOKEN   = os.environ["ANTHROPIC_AUTH_TOKEN"]
ANTHROPIC_URL     = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
FINNHUB_TOKEN     = os.environ["FINNHUB_API_KEY"]
TOP_N             = int(os.environ.get("TOP_N", "10"))

MAG7 = ["NVDA", "AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA"]

SP100 = [
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA",
    "LLY", "UNH", "JPM", "V", "XOM", "MA", "AVGO", "JNJ", "PG", "HD",
    "COST", "MRK", "ABBV", "CVX", "BAC", "WMT", "NFLX", "CRM", "AMD",
    "KO", "ORCL", "PEP", "TMO", "ACN", "MCD", "LIN", "CSCO", "ABT",
    "PM", "IBM", "ADBE", "DHR", "INTU", "TXN", "QCOM", "GE", "CAT",
    "AMGN", "RTX", "SPGI", "NOW", "ISRG", "PFE", "VZ", "UBER", "CMCSA",
    "NEE", "LOW", "HON", "MS", "BKNG", "UNP", "GS", "AXP", "COP",
    "T", "ELV", "TJX", "BLK", "VRTX", "MDT", "BSX", "C", "ADI",
    "GILD", "REGN", "CB", "DE", "SYK", "ADP", "MMC", "SO", "ETN",
    "ZTS", "PLD", "TMUS", "DUK", "CI", "MO", "EOG", "CME", "AON",
    "USB", "PNC", "WM", "ITW", "EMR", "APD", "MCO", "KLAC", "ANET",
]

# 新浪财经指数代码（国内直连）- 仅三大指数
INDEX_TICKERS_SINA = {
    "S&P 500": "gb_$inx",
    "NASDAQ":  "gb_ixic",
    "DOW":     "gb_dji",
}

# yfinance 配置（海外服务器可用）
INDEX_TICKERS = {
    "S&P 500": "^GSPC",
    "NASDAQ":  "^IXIC",
    "DOW":     "^DJI",
    "VIX":     "^VIX",
    "DXY":     "DX-Y.NYB",
    "10Y":     "^TNX",
}

SECTOR_ETFS = {
    "科技": "XLK", "通信": "XLC", "非必需消费": "XLY", "工业": "XLI",
    "金融": "XLF", "医疗": "XLV", "必需消费": "XLP", "材料": "XLB",
    "能源": "XLE", "公用事业": "XLU", "房地产": "XLRE",
}

SINA_HEADERS = {"Referer": "https://finance.sina.com.cn", "User-Agent": "Mozilla/5.0"}
WEEKDAY_CN   = {"Monday":"周一","Tuesday":"周二","Wednesday":"周三",
                "Thursday":"周四","Friday":"周五","Saturday":"周六","Sunday":"周日"}

CN_NAMES = {
    "AAPL":"苹果","MSFT":"微软","NVDA":"英伟达","AMZN":"亚马逊","GOOGL":"谷歌",
    "META":"Meta","TSLA":"特斯拉","LLY":"礼来","UNH":"联合健康","JPM":"摩根大通",
    "V":"Visa","XOM":"埃克森美孚","MA":"万事达","AVGO":"博通","JNJ":"强生",
    "PG":"宝洁","HD":"家得宝","COST":"好市多","MRK":"默克","ABBV":"艾伯维",
    "CVX":"雪佛龙","BAC":"美国银行","WMT":"沃尔玛","NFLX":"奈飞","CRM":"赛富时",
    "AMD":"AMD","KO":"可口可乐","ORCL":"甲骨文","PEP":"百事可乐","TMO":"赛默飞",
    "ACN":"埃森哲","MCD":"麦当劳","LIN":"林德","CSCO":"思科","ABT":"雅培",
    "PM":"菲莫国际","IBM":"IBM","ADBE":"Adobe","DHR":"丹纳赫","INTU":"Intuit",
    "TXN":"德州仪器","QCOM":"高通","GE":"通用电气","CAT":"卡特彼勒","AMGN":"安进",
    "RTX":"雷神技术","SPGI":"标普全球","NOW":"ServiceNow","ISRG":"直觉外科",
    "PFE":"辉瑞","VZ":"威瑞森","UBER":"优步","CMCSA":"康卡斯特","NEE":"下一代能源",
    "LOW":"劳氏","HON":"霍尼韦尔","MS":"摩根士丹利","BKNG":"缤客控股",
    "UNP":"联合太平洋","GS":"高盛","AXP":"美国运通","COP":"康菲石油","T":"AT&T",
    "ELV":"信诺","TJX":"TJX","BLK":"贝莱德","VRTX":"福泰制药","MDT":"美敦力",
    "BSX":"波士顿科学","C":"花旗","ADI":"亚德诺","GILD":"吉利德","REGN":"再生元",
    "CB":"丘博","DE":"迪尔","SYK":"史赛克","ADP":"ADP","MMC":"达信",
    "SO":"南方公司","ETN":"伊顿","ZTS":"硕腾","PLD":"普洛斯","TMUS":"T-Mobile",
    "DUK":"杜克能源","CI":"信诺集团","MO":"奥驰亚","EOG":"EOG资源","CME":"芝商所",
    "AON":"怡安","USB":"合众银行","PNC":"PNC金融","WM":"废物管理","ITW":"伊利诺工具",
    "EMR":"艾默生","APD":"空气化工","MCO":"穆迪","KLAC":"科磊","ANET":"Arista",
}


# ══════════════════════════════════════════════════════════════════════
# 数据获取
# ══════════════════════════════════════════════════════════════════════

def fetch_quotes(symbols):
    """新浪财经：批量拉取美股行情"""
    codes = ",".join("gb_" + s.lower() for s in symbols)
    resp  = requests.get(f"http://hq.sinajs.cn/list={codes}", headers=SINA_HEADERS, timeout=15)
    resp.encoding = "gbk"
    results = []
    for sym in symbols:
        code = "gb_" + sym.lower()
        m = re.search(rf'hq_str_{re.escape(code)}="([^"]*)"', resp.text)
        if not m or not m.group(1):
            continue
        fields = m.group(1).split(",")
        if len(fields) < 5 or not fields[1]:
            continue
        try:
            results.append({
                "symbol":     sym,
                "name":       fields[0] if not fields[0].replace(" ","").isascii() else CN_NAMES.get(sym, fields[0]),
                "price":      float(fields[1]),
                "change_pct": float(fields[2]),
                "updated":    fields[3],
            })
        except ValueError:
            continue
    return results


def get_trade_date(quotes):
    for q in quotes:
        if q.get("updated"):
            dt_bj = datetime.strptime(q["updated"], "%Y-%m-%d %H:%M:%S")
            dt_et = pytz.timezone("Asia/Shanghai").localize(dt_bj).astimezone(pytz.timezone("US/Eastern"))
            return dt_et.strftime("%Y-%m-%d"), dt_et.strftime("%A")
    return datetime.now().strftime("%Y-%m-%d"), ""


def fetch_indices():
    """指数数据：新浪（主要指数）+ yfinance（VIX/DXY/10Y 可选）"""
    results = {}

    # 1. 新浪财经：三大指数（国内直连，必成功）
    codes = ",".join(INDEX_TICKERS_SINA.values())
    try:
        resp = requests.get(f"http://hq.sinajs.cn/list={codes}", headers=SINA_HEADERS, timeout=15)
        resp.encoding = "gbk"
        for name, code in INDEX_TICKERS_SINA.items():
            m = re.search(rf'hq_str_{re.escape(code)}="([^"]*)"', resp.text)
            if m and m.group(1):
                fields = m.group(1).split(",")
                if len(fields) >= 3 and fields[1] and fields[2]:
                    try:
                        value = float(fields[1])
                        change_pct = float(fields[2])
                        results[name] = {"value": value, "change_pct": change_pct}
                    except ValueError:
                        pass
    except Exception as e:
        print(f"  ⚠️ 新浪指数: {e}")

    # 2. yfinance：VIX/DXY/10Y（可选，海外服务器可用）
    extra_tickers = {"VIX": "^VIX", "DXY": "DX-Y.NYB", "10Y": "^TNX"}
    for name, sym in extra_tickers.items():
        if name in results:
            continue
        try:
            hist = yf.Ticker(sym).history(period="5d")
            hist = hist[hist["Close"].notna()]
            if len(hist) >= 2:
                prev = float(hist["Close"].iloc[-2])
                last = float(hist["Close"].iloc[-1])
                results[name] = {"value": last, "change_pct": (last - prev) / prev * 100}
            time.sleep(0.1)
        except Exception:
            pass  # 静默失败，不影响主流程

    return results


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


def fetch_fear_greed():
    """CNN Fear & Greed Index"""
    try:
        r = requests.get(
            "https://production.dataviz.cnn.io/index/fearandgreed/graphdata",
            headers=CNN_HEADERS, timeout=10, verify=False,
        )
        fg = r.json().get("fear_and_greed", {})
        return {"score": round(fg.get("score", 50)), "rating": fg.get("rating", "Neutral")}
    except Exception as e:
        print(f"  ⚠️ 贪恐指数: {e}")
        return None


def fetch_sectors():
    """新浪财经：11 个 SPDR 板块 ETF"""
    results = {}
    syms = list(SECTOR_ETFS.values())
    try:
        codes = ",".join("gb_" + s.lower() for s in syms)
        resp = requests.get(f"http://hq.sinajs.cn/list={codes}", headers=SINA_HEADERS, timeout=15)
        resp.encoding = "gbk"
        for name, sym in SECTOR_ETFS.items():
            code = "gb_" + sym.lower()
            m = re.search(rf'hq_str_{re.escape(code)}="([^"]*)"', resp.text)
            if m and m.group(1):
                fields = m.group(1).split(",")
                if len(fields) >= 3 and fields[2]:
                    try:
                        results[name] = {
                            "etf": sym,
                            "change_pct": float(fields[2]),
                        }
                    except ValueError:
                        pass
    except Exception as e:
        print(f"  ⚠️ 板块数据: {e}")
    return results


def fetch_52w_and_technicals(symbols):
    """yfinance：一次拉取1年数据，同时计算52周位置 + 技术指标（MA/RSI/MACD）"""
    w52 = {}
    tech = {}
    try:
        data = yf.download(symbols, period="1y", interval="1d", auto_adjust=True,
                           progress=False, threads=True)
        close = data["Close"].dropna(how="all")

        for sym in symbols:
            if sym not in close.columns:
                continue
            c = close[sym].dropna()
            if len(c) < 20:
                continue

            curr = float(c.iloc[-1])

            # 52周高低位置
            h52 = float(c.max())
            l52 = float(c.min())
            if h52 > l52:
                w52[sym] = {"high": h52, "low": l52, "current": curr,
                            "position": (curr - l52) / (h52 - l52) * 100}

            # 均线
            ma5  = round(float(c.rolling(5).mean().iloc[-1]), 2)
            ma20 = round(float(c.rolling(20).mean().iloc[-1]), 2)
            ma60 = round(float(c.rolling(60).mean().iloc[-1]), 2) if len(c) >= 60 else None

            # RSI-14
            delta = c.diff()
            gain  = delta.clip(lower=0).rolling(14).mean()
            loss  = (-delta.clip(upper=0)).rolling(14).mean()
            rsi_val = 50.0
            if loss.iloc[-1] != 0:
                rsi_val = round(float(100 - 100 / (1 + gain.iloc[-1] / loss.iloc[-1])), 1)

            # MACD
            ema12 = c.ewm(span=12, adjust=False).mean()
            ema26 = c.ewm(span=26, adjust=False).mean()
            macd_line  = ema12 - ema26
            macd_sig   = macd_line.ewm(span=9, adjust=False).mean()
            is_golden  = float(macd_line.iloc[-1]) > float(macd_sig.iloc[-1])

            # 趋势判断
            if curr > ma5 and ma5 > ma20:
                trend = "多头↑"
            elif curr < ma5 and ma5 < ma20:
                trend = "空头↓"
            else:
                trend = "震荡→"

            # RSI 标签
            if rsi_val >= 75:   rsi_label = "超买⚠"
            elif rsi_val >= 60: rsi_label = "偏强"
            elif rsi_val <= 25: rsi_label = "超卖⚠"
            elif rsi_val <= 40: rsi_label = "偏弱"
            else:               rsi_label = "中性"

            tech[sym] = {
                "ma5": ma5, "ma20": ma20, "ma60": ma60,
                "rsi": rsi_val, "rsi_label": rsi_label,
                "macd_golden": is_golden,
                "trend": trend,
            }

    except Exception as e:
        print(f"  ⚠️ 52周+技术数据: {e}")
    return w52, tech


def fetch_analyst_ratings(symbols):
    """Finnhub：分析师评级共识"""
    results = {}
    for sym in symbols:
        try:
            r = requests.get(
                "https://finnhub.io/api/v1/stock/recommendation",
                params={"symbol": sym, "token": FINNHUB_TOKEN},
                timeout=8,
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
                    if bull >= 0.6:   consensus = "强烈买入"
                    elif bull >= 0.45: consensus = "买入"
                    elif bear >= 0.3:  consensus = "卖出"
                    else:             consensus = "持有"
                    results[sym] = {
                        "strong_buy": sb, "buy": b, "hold": h,
                        "sell": s, "strong_sell": ss, "consensus": consensus,
                    }
            time.sleep(0.3)
        except Exception as e:
            print(f"  ⚠️ 评级 [{sym}]: {e}")
    return results


def fetch_upcoming_earnings(symbols, trade_date_str):
    """yfinance：未来7天财报日历"""
    upcoming = []
    try:
        trade_dt  = datetime.strptime(trade_date_str, "%Y-%m-%d").date()
        deadline  = trade_dt + timedelta(days=7)
        for sym in symbols:
            try:
                cal = yf.Ticker(sym).calendar
                if cal is None:
                    continue
                earn = None
                if isinstance(cal, dict):
                    earn = cal.get("Earnings Date")
                elif hasattr(cal, "get"):
                    earn = cal.get("Earnings Date")
                if earn is None:
                    continue
                if isinstance(earn, (list, tuple)):
                    earn = earn[0]
                if hasattr(earn, "date"):
                    earn = earn.date()
                elif isinstance(earn, str):
                    earn = datetime.strptime(earn[:10], "%Y-%m-%d").date()
                if trade_dt <= earn <= deadline:
                    upcoming.append({
                        "symbol": sym,
                        "name":   CN_NAMES.get(sym, sym),
                        "date":   str(earn),
                    })
                time.sleep(0.1)
            except:
                pass
    except Exception as e:
        print(f"  ⚠️ 财报日历: {e}")
    return sorted(upcoming, key=lambda x: x["date"])


def fetch_crypto():
    """加密货币行情：优先 OKX（国内可访问），备选 CoinGecko/火币"""
    # 1. OKX API（国内直连）
    try:
        result = {}
        coins = [("BTC", "BTC-USDT"), ("ETH", "ETH-USDT"), ("SOL", "SOL-USDT")]
        for name, inst_id in coins:
            r = requests.get(
                f"https://www.okx.com/api/v5/market/ticker?instId={inst_id}",
                timeout=10,
            )
            data = r.json()
            if data.get("data"):
                d = data["data"][0]
                price = float(d["last"])
                open24h = float(d["open24h"])
                change_pct = (price - open24h) / open24h * 100
                result[name] = {"price": price, "change_pct": change_pct}
        if result:
            return result
    except Exception as e:
        print(f"  ⚠️ OKX: {e}")

    # 2. CoinGecko（全球可用）
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": "bitcoin,ethereum,solana", "vs_currencies": "usd", "include_24hr_change": "true"},
            timeout=10,
        )
        data = r.json()
        if data.get("bitcoin"):
            return {
                "BTC": {"price": data["bitcoin"]["usd"], "change_pct": data["bitcoin"].get("usd_24h_change", 0)},
                "ETH": {"price": data["ethereum"]["usd"], "change_pct": data["ethereum"].get("usd_24h_change", 0)},
                "SOL": {"price": data["solana"]["usd"], "change_pct": data["solana"].get("usd_24h_change", 0)},
            }
    except Exception as e:
        print(f"  ⚠️ CoinGecko: {e}")

    # 3. 火币 API
    try:
        result = {}
        symbols = {"BTC": "btcusdt", "ETH": "ethusdt", "SOL": "solusdt"}
        for name, symbol in symbols.items():
            r = requests.get(
                "https://api.huobi.pro/market/detail/merged",
                params={"symbol": symbol},
                timeout=10,
            )
            data = r.json()
            if data.get("status") == "ok" and data.get("tick"):
                tick = data["tick"]
                price = float(tick["close"])
                open_price = float(tick["open"])
                change_pct = (price - open_price) / open_price * 100
                result[name] = {"price": price, "change_pct": change_pct}
        return result if result else None
    except Exception as e:
        print(f"  ⚠️ 加密行情: {e}")
        return None


def fetch_macro_calendar():
    """ForexFactory 免费日历：本周+下周高/中影响力美元事件
    数据源：https://nfs.faireconomy.media/ff_calendar_thisweek.json
    无需 API key，用 curl 绕过本地 SSL 问题。
    """
    EVENT_CN = {
        "non-farm employment change": "非农就业",
        "nonfarm payrolls":           "非农就业",
        "unemployment claims":        "初申失业金",
        "unemployment rate":          "失业率",
        "core cpi":                   "核心CPI",
        "cpi":                        "CPI通胀",
        "core pce":                   "核心PCE",
        "pce":                        "PCE物价",
        "ppi":                        "PPI生产者价格",
        "fomc":                       "美联储会议",
        "fed rate":                   "利率决议",
        "interest rate":              "利率决议",
        "gdp":                        "GDP数据",
        "core retail sales":          "核心零售",
        "retail sales":               "零售销售",
        "ism manufacturing":          "ISM制造业",
        "ism services":               "ISM服务业",
        "adp non-farm":               "ADP就业",
        "average hourly earnings":    "平均时薪",
        "trade balance":              "贸易账",
        "consumer confidence":        "消费者信心",
        "jolts":                      "职位空缺",
    }
    IMPACT_EMOJI  = {"High": "🔴", "Medium": "🟡"}
    WEEKDAY_CN_MAP = {0:"周一",1:"周二",2:"周三",3:"周四",4:"周五",5:"周六",6:"周日"}

    import subprocess
    ny_tz  = pytz.timezone("America/New_York")
    today  = datetime.now(ny_tz).date()
    result = []

    for url in [
        "https://nfs.faireconomy.media/ff_calendar_thisweek.json",
        "https://nfs.faireconomy.media/ff_calendar_nextweek.json",
    ]:
        try:
            proc = subprocess.run(
                ["curl", "-s", "--insecure", "--noproxy", "*", url],
                capture_output=True, text=True, timeout=15,
            )
            if not proc.stdout.strip():
                continue
            events = json.loads(proc.stdout)
        except Exception as ex:
            print(f"  ⚠️ 宏观日历 fetch {url}: {ex}")
            continue

        for e in events:
            if e.get("country") != "USD":
                continue
            impact = e.get("impact", "Low")
            if impact not in ("High", "Medium"):
                continue
            try:
                dt = datetime.fromisoformat(e["date"]).astimezone(ny_tz)
            except Exception:
                continue
            event_date = dt.date()
            if event_date < today or event_date > today + timedelta(days=7):
                continue

            title_low = e.get("title", "").lower()
            cn_name   = next(
                (v for k, v in EVENT_CN.items() if k in title_low),
                e.get("title", "")[:18],
            )
            if event_date == today:
                when = "今日"
            elif event_date == today + timedelta(days=1):
                when = "明日"
            else:
                when = WEEKDAY_CN_MAP.get(event_date.weekday(), str(event_date)[5:])

            forecast = e.get("forecast", "")
            previous = e.get("previous", "")
            detail   = "  ".join(filter(None, [
                f"预期{forecast}" if forecast else "",
                f"前值{previous}" if previous else "",
            ]))
            result.append({
                "name":  cn_name,
                "when":  when,
                "time":  dt.strftime("%H:%M"),
                "emoji": IMPACT_EMOJI.get(impact, ""),
                "detail": detail,
                "_sort": dt,
            })

    result.sort(key=lambda x: x["_sort"])
    return result[:10]


def fetch_postmarket(symbols):
    """yfinance 盘后/盘前行情（有数据则返回，否则空）"""
    result = {}
    for sym in symbols:
        try:
            info = yf.Ticker(sym).info
            reg  = info.get("regularMarketPrice") or info.get("previousClose")
            if not reg:
                continue
            for key, label in [("postMarketPrice", "盘后"), ("preMarketPrice", "盘前")]:
                ext = info.get(key)
                if ext and abs(ext - reg) / reg > 0.0005:   # 忽略几乎相同的价格
                    result[sym] = {
                        "price":      ext,
                        "change_pct": (ext - reg) / reg * 100,
                        "label":      label,
                    }
                    break
        except:
            pass
        time.sleep(0.1)
    return result


def fetch_news(symbol, trade_date_str):
    trade_dt  = datetime.strptime(trade_date_str, "%Y-%m-%d")
    date_from = (trade_dt - timedelta(days=2)).strftime("%Y-%m-%d")
    try:
        r = requests.get(
            "https://finnhub.io/api/v1/company-news",
            params={"symbol": symbol, "from": date_from, "to": trade_date_str, "token": FINNHUB_TOKEN},
            timeout=10,
        )
        items = r.json()
        if isinstance(items, list):
            return [i["headline"] for i in items[:5] if i.get("headline")]
    except Exception as e:
        print(f"  ⚠️ 新闻 [{symbol}]: {e}")
    return []


def collect_news(symbols, trade_date_str):
    news_map = {}
    for sym in symbols:
        headlines = fetch_news(sym, trade_date_str)
        if headlines:
            news_map[sym] = headlines
        time.sleep(0.3)
    return news_map


# ══════════════════════════════════════════════════════════════════════
# Claude 分析
# ══════════════════════════════════════════════════════════════════════

CLAUDE_PROMPT_HEADER = """你是专业美股财经分析师，同时熟悉技术分析。以下是昨日美股异动股票的新闻和技术指标。

对每只股票，综合新闻面和技术面，请：
1. 将新闻标题翻译成中文（每条≤28字，保留关键数字和公司名）
2. 写1句分析（≤40字）：直接说涨跌核心原因，不废话
3. 给出影响判断（选一个）：📈短期利多 / 📉短期利空 / 🚀长期利多 / ⚠️长期利空 / ➡️中性
4. 给出操作建议（选一个，仅供参考）：🟢买入 / 🔵关注 / 🟡观望 / 🔴减持

技术指标说明：趋势=多头↑/空头↓/震荡→  RSI>70超买  RSI<30超卖  MACD金叉看涨/死叉看跌

严格按以下格式，每只股票后加 ---：

【SYMBOL】
新闻：译文1
新闻：译文2
分析：综合新闻+技术的判断
判断：📈短期利多
建议：🟢买入

---

"""


def _call_claude(prompt_text):
    """用 curl 调用 Claude，写临时文件避免 shell 截断"""
    import subprocess, tempfile, os
    payload = json.dumps({
        "model": "claude-sonnet-4-6", "max_tokens": 2000,
        "messages": [{"role": "user", "content": prompt_text}],
    })
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        f.write(payload)
        tmp_path = f.name
    try:
        proc = subprocess.run(
            ["curl", "-s", "--insecure", "--noproxy", "*",
             "-X", "POST",
             "-H", f"x-api-key: {ANTHROPIC_TOKEN}",
             "-H", "anthropic-version: 2023-06-01",
             "-H", "content-type: application/json",
             "-d", f"@{tmp_path}",
             f"{ANTHROPIC_URL}/v1/messages"],
            capture_output=True, text=True, timeout=90,
        )
        if not proc.stdout.strip():
            raise ValueError(f"curl empty response, stderr: {proc.stderr[:200]}")
        return json.loads(proc.stdout)["content"][0]["text"].strip()
    finally:
        os.unlink(tmp_path)


def _parse_claude_output(text, result):
    """解析 Claude 输出，写入 result dict"""
    current = None
    for line in text.splitlines():
        line = line.strip()
        if not line or line == "---":
            continue
        m = re.match(r"^【(\w+[-\w]*)】", line)
        if m:
            current = m.group(1)
            if current not in result:
                result[current] = {"news_cn": [], "analysis": "", "tag": "➡️中性", "advice": ""}
        elif current:
            if line.startswith("新闻："):
                result[current]["news_cn"].append(line[3:])
            elif line.startswith("分析："):
                result[current]["analysis"] = line[3:]
            elif line.startswith("判断："):
                result[current]["tag"] = line[3:]
            elif line.startswith("建议："):
                result[current]["advice"] = line[3:]


def claude_analyze(quote_map, news_map, batch_size=10, **kwargs):
    symbols_with_news = [s for s in quote_map if news_map.get(s)]
    symbols_no_news   = [s for s in quote_map if not news_map.get(s)]
    result = {s: {"news_cn": [], "analysis": "暂无相关新闻", "tag": "➡️中性", "advice": ""}
              for s in symbols_no_news}
    if not symbols_with_news:
        return result

    # 分批处理，每批 batch_size 只
    batches = [symbols_with_news[i:i+batch_size]
               for i in range(0, len(symbols_with_news), batch_size)]
    print(f"   分 {len(batches)} 批分析（每批≤{batch_size}只）")

    tech_map = kwargs.get("tech_map", {})

    for b_idx, batch in enumerate(batches, 1):
        blocks = []
        for sym in batch:
            q     = quote_map[sym]
            lines = "\n".join(f"  - {h}" for h in news_map[sym])
            # 拼接技术指标（如有）
            t = tech_map.get(sym)
            tech_str = ""
            if t:
                macd_label = "MACD金叉" if t["macd_golden"] else "MACD死叉"
                tech_str = (f"\n技术面：趋势={t['trend']}  "
                            f"RSI={t['rsi']}{t['rsi_label']}  {macd_label}  "
                            f"MA5={t['ma5']} MA20={t['ma20']}")
            blocks.append(f"【{sym}】{q['name']} {q['change_pct']:+.2f}%{tech_str}\n{lines}")

        prompt = CLAUDE_PROMPT_HEADER + "\n\n".join(blocks)
        try:
            text = _call_claude(prompt)
            _parse_claude_output(text, result)
            print(f"   批次 {b_idx}/{len(batches)} ✅")
        except Exception as e:
            print(f"   批次 {b_idx}/{len(batches)} ⚠️ {e}")
            for sym in batch:
                result[sym] = {"news_cn": news_map.get(sym, [])[:2],
                               "analysis": "", "tag": "➡️中性", "advice": ""}

    return result


# ══════════════════════════════════════════════════════════════════════
# 格式化辅助
# ══════════════════════════════════════════════════════════════════════

def pct_color(pct):
    if pct > 0:  return f"<font color='red'>**+{pct:.2f}%**</font>"
    if pct < 0:  return f"<font color='green'>**{pct:.2f}%**</font>"
    return f"**{pct:.2f}%**"


def idx_fmt(name, val, pct):
    """指数简洁格式，数字按大小格式化"""
    if name == "VIX":
        val_str = f"{val:.1f}"
    elif name in ("10Y", "DXY"):
        val_str = f"{val:.2f}"
    elif val >= 10000:
        val_str = f"{val:,.0f}"
    else:
        val_str = f"{val:,.1f}"
    return f"**{name}** {pct_color(pct)} {val_str}"


def vix_label(vix):
    if vix < 15:  return "😌平静"
    if vix < 20:  return "😊正常"
    if vix < 30:  return "😟警觉"
    return "😱恐慌"


def fg_label(score):
    if score >= 75: return f"{score} 🤑极度贪婪"
    if score >= 55: return f"{score} 😏贪婪"
    if score >= 45: return f"{score} 😐中性"
    if score >= 25: return f"{score} 😨恐惧"
    return f"{score} 😱极度恐惧"


def w52_bar(pos):
    """52周位置：统一用「在高点X%」表示当前价格在年内区间的位置"""
    return f"在高点{pos:.0f}%"


def rating_line(r):
    if not r:
        return ""
    consensus = r["consensus"]
    emoji = {"强烈买入": "🟢", "买入": "📈", "持有": "➡️", "卖出": "📉"}.get(consensus, "")
    return f"{emoji}{consensus}"


# ── Jinja2 模板：股票块左右列文字内容 ─────────────────────────────
_JENV = jinja2.Environment(autoescape=False)

# 左列：股票名 + tag/advice 单独一行 + 技术 + 评级 + 新闻 + AI分析
# tag/advice 独占一行，不与股票名同行，避免过长折行
_LEFT_TMPL = _JENV.from_string(
    "{% if rank %}**{{ rank }}. {{ sym }}** {{ name }}"
    "{% else %}**{{ sym }}** {{ name }}{% endif %}"
    "{% if tag or advice %}\n> {{ tag }}{% if advice %} {{ advice }}{% endif %}{% endif %}"
    "{% if tech %}\n> 📊 {{ tech }}{% endif %}"
    "{% if rating %}\n> 🏦 {{ rating }}{% endif %}"
    "{% for n in news %}\n> 📰 {{ n }}{% endfor %}"
    "{% if analysis %}\n> 💡 {{ analysis }}{% endif %}"
)

# 右列：只放 4 行最短内容，绝不断行
# 涨跌% / 价格 / 52周位置 / 建议
_RIGHT_TMPL = _JENV.from_string(
    "{{ pct }}\n**${{ price }}**"
    "{% if w52 %}\n{{ w52 }}{% endif %}"
    "{% if advice %}\n{{ advice }}{% endif %}"
)


def stock_col_set(sym, q, a, news_list,
                  w52_data=None, tech_data=None, rating=None, rank=None,
                  postmarket=None):
    """用 column_set 渲染单只股票：左列(内容) | 右列(4行指标)，手机右列永不断行"""
    news   = (a.get("news_cn") or news_list or [])[:2]
    tag    = a.get("tag", "")
    advice = a.get("advice", "")

    # 技术摘要放左列，可换行，内容完整
    tech_str = ""
    if tech_data:
        macd_str = "金叉↑" if tech_data["macd_golden"] else "死叉↓"
        tech_str = (f"趋势{tech_data['trend']}  "
                    f"RSI{tech_data['rsi']}{tech_data['rsi_label']}  {macd_str}")

    left_content = _LEFT_TMPL.render(
        rank=rank, sym=sym, name=q["name"],
        tag=tag if tag and "中性" not in tag else "",
        advice=advice,
        tech=tech_str,
        rating=rating_line(rating) if rating else "",
        news=news,
        analysis=a.get("analysis", ""),
    )
    # 盘后行情追加到右列
    pm_str = ""
    if postmarket:
        pm_str = f"{postmarket['label']} {pct_color(postmarket['change_pct'])}"

    right_content = _RIGHT_TMPL.render(
        pct=pct_color(q["change_pct"]),
        price=f"{q['price']:.2f}",
        w52=w52_bar(w52_data["position"]) if w52_data else "",
        advice=pm_str,   # 右列底部复用 advice 位置放盘后数据
    )

    return {
        "tag": "column_set",
        "flex_mode": "none",
        "background_style": "default",
        "columns": [
            {
                "tag": "column", "width": "weighted", "weight": 3,
                "vertical_align": "top",
                "elements": [{"tag": "div", "text": {"tag": "lark_md", "content": left_content}}],
            },
            {
                "tag": "column", "width": "weighted", "weight": 1,
                "vertical_align": "top",
                "elements": [{"tag": "div", "text": {"tag": "lark_md", "content": right_content}}],
            },
        ],
    }


# ══════════════════════════════════════════════════════════════════════
# 构建飞书卡片
# ══════════════════════════════════════════════════════════════════════

def build_message(quotes, trade_date, weekday_en, analysis, news_map,
                  indices, fear_greed, sectors, w52, analyst_ratings,
                  earnings, crypto, tech=None,
                  macro_calendar=None, postmarket=None):

    quote_map = {q["symbol"]: q for q in quotes}
    valid     = [q for q in quotes if q["change_pct"] != 0.0]
    sorted_q  = sorted(valid, key=lambda x: x["change_pct"], reverse=True)
    gainers   = sorted_q[:TOP_N]
    losers    = sorted_q[-TOP_N:][::-1]
    weekday   = WEEKDAY_CN.get(weekday_en, weekday_en)

    # 动态卡片颜色：随 S&P 500 涨跌变化
    sp_pct = (indices.get("S&P 500") or {}).get("change_pct", 0) if indices else 0
    if   sp_pct >=  1.0: header_color = "green"
    elif sp_pct >=  0:   header_color = "blue"
    elif sp_pct >= -1.0: header_color = "yellow"
    else:                header_color = "red"

    elements = []

    def div(md):
        elements.append({"tag": "div", "text": {"tag": "lark_md", "content": md}})

    def hr():
        elements.append({"tag": "hr"})

    def col_set(cols_content, weights=None):
        """飞书 column_set 多列布局，每列内容独立，手机不断行"""
        if weights is None:
            weights = [1] * len(cols_content)
        cols = []
        for content, weight in zip(cols_content, weights):
            cols.append({
                "tag": "column",
                "width": "weighted",
                "weight": weight,
                "vertical_align": "top",
                "elements": [
                    {"tag": "div", "text": {"tag": "lark_md", "content": content}}
                ],
            })
        elements.append({
            "tag": "column_set",
            "flex_mode": "none",
            "background_style": "default",
            "columns": cols,
        })

    # ── 1. 市场全景（column_set 多列，手机每列独立不断行）─────────
    if indices:
        div("🌍 **市场全景**")

        sp  = indices.get("S&P 500")
        nq  = indices.get("NASDAQ")
        dow = indices.get("DOW")

        # 三大指数：3列，每列独占空间
        idx_cols = []
        for label, key in [("S&P", "S&P 500"), ("NASDAQ", "NASDAQ"), ("DOW", "DOW")]:
            d = indices.get(key)
            if d:
                val_str = f"{d['value']:,.0f}" if d["value"] >= 1000 else f"{d['value']:.2f}"
                idx_cols.append(f"**{label}**\n{pct_color(d['change_pct'])}\n{val_str}")
        if idx_cols:
            col_set(idx_cols)

        # 情绪指标：VIX | 贪/恐 | 10Y债+DXY
        vix_content = fg_content = bonds_content = None
        if "VIX" in indices:
            vix = indices["VIX"]["value"]
            vix_content = f"**VIX**\n{vix:.1f} {vix_label(vix)}"
        if fear_greed:
            fg_content = f"**贪/恐**\n{fg_label(fear_greed['score'])}"
        bonds_parts = []
        if "10Y" in indices:
            bonds_parts.append(f"**10Y债** {indices['10Y']['value']:.2f}%")
        if "DXY" in indices:
            bonds_parts.append(f"**DXY** {indices['DXY']['value']:.1f}")
        if bonds_parts:
            bonds_content = "\n".join(bonds_parts)

        sentiment_cols = [c for c in [vix_content, fg_content, bonds_content] if c]
        if sentiment_cols:
            col_set(sentiment_cols)

        hr()

    # ── 1b. 宏观日历（有数据才显示）────────────────────────────────
    if macro_calendar:
        lines = ["📅 **宏观日历（未来7天）**"]
        for e in macro_calendar:
            detail_str = f"  {e['detail']}" if e.get("detail") else ""
            lines.append(f"> {e['emoji']} {e['when']} {e['time']} **{e['name']}**{detail_str}")
        div("\n".join(lines))
        hr()

    # ── 2. 板块轮动（2列：强势 | 弱势，每板块独占一行）───────────
    SHORT_NAMES = {
        "科技":"科技", "通信":"通信", "非必需消费":"消费↑",
        "工业":"工业", "金融":"金融", "医疗":"医疗",
        "必需消费":"必需↓", "材料":"材料", "能源":"能源",
        "公用事业":"公用", "房地产":"地产",
    }
    if sectors:
        ranked = sorted(sectors.items(), key=lambda x: x[1]["change_pct"], reverse=True)
        top3   = ranked[:3]
        bot3   = ranked[-3:][::-1]

        div("📦 **板块轮动**")

        hot_lines  = "🔥 **强势**\n" + "\n".join(
            f"{SHORT_NAMES.get(n, n)} {pct_color(d['change_pct'])}" for n, d in top3
        )
        cold_lines = "🧊 **弱势**\n" + "\n".join(
            f"{SHORT_NAMES.get(n, n)} {pct_color(d['change_pct'])}" for n, d in bot3
        )
        col_set([hot_lines, cold_lines])
        hr()

    # ── 2b. 涨跌快速一览（Top5 并排，快速扫一眼）───────────────────
    if len(sorted_q) >= 5:
        gain5 = sorted_q[:5]
        lose5 = sorted_q[-5:][::-1]
        gain_lines = "🔥 **涨幅前5**\n" + "\n".join(
            f"**{q['symbol']}** {pct_color(q['change_pct'])}" for q in gain5
        )
        lose_lines = "💀 **跌幅前5**\n" + "\n".join(
            f"**{q['symbol']}** {pct_color(q['change_pct'])}" for q in lose5
        )
        col_set([gain_lines, lose_lines])
        hr()

    # ── 3. 七姐妹（灰色背景卡片头 + 每股分隔线）────────────────────
    mag7_valid = [q for q in sorted_q if q["symbol"] in MAG7]
    mag7_up    = [q for q in mag7_valid if q["change_pct"] > 0]
    mag7_down  = [q for q in mag7_valid if q["change_pct"] < 0]

    # 灰色背景卡片：3列信息框
    best_q  = mag7_valid[0]  if mag7_valid else None
    worst_q = mag7_valid[-1] if mag7_valid else None
    elements.append({
        "tag": "column_set",
        "flex_mode": "none",
        "background_style": "grey",
        "columns": [
            {
                "tag": "column", "width": "weighted", "weight": 1,
                "vertical_align": "center",
                "elements": [{"tag": "div", "text": {"tag": "lark_md",
                    "content": "⭐ **七姐妹**"}}],
            },
            {
                "tag": "column", "width": "weighted", "weight": 1,
                "vertical_align": "center",
                "elements": [{"tag": "div", "text": {"tag": "lark_md",
                    "content": f"**{len(mag7_up)}涨 {len(mag7_down)}跌**"}}],
            },
            {
                "tag": "column", "width": "weighted", "weight": 1,
                "vertical_align": "center",
                "elements": [{"tag": "div", "text": {"tag": "lark_md",
                    "content": (
                        f"🔝 **{best_q['symbol']}** {pct_color(best_q['change_pct'])}\n"
                        f"🔻 **{worst_q['symbol']}** {pct_color(worst_q['change_pct'])}"
                        if best_q and worst_q else ""
                    )}}],
            },
        ],
    })

    for q in mag7_valid:
        sym = q["symbol"]
        elements.append(stock_col_set(
            sym=sym, q=q,
            a=analysis.get(sym, {}),
            news_list=news_map.get(sym, []),
            w52_data=w52.get(sym),
            tech_data=(tech or {}).get(sym),
            rating=analyst_ratings.get(sym),
            postmarket=(postmarket or {}).get(sym),
        ))
        hr()  # 每只股票后加分隔线

    # ── 4. 涨幅榜 ────────────────────────────────────────────────────
    div(f"🔥 **涨幅榜 Top {TOP_N}**")
    for i, q in enumerate(gainers, 1):
        sym = q["symbol"]
        if sym in MAG7:
            div(f"**{i}.** **{sym}** {q['name']}　{pct_color(q['change_pct'])}　"
                f"${q['price']:.2f}　_↑ 详见七姐妹_")
            hr()
            continue
        elements.append(stock_col_set(
            sym=sym, q=q,
            a=analysis.get(sym, {}),
            news_list=news_map.get(sym, []),
            rank=i,
        ))
        hr()

    # ── 5. 跌幅榜 ────────────────────────────────────────────────────
    div(f"💀 **跌幅榜 Top {TOP_N}**")
    for i, q in enumerate(losers, 1):
        sym = q["symbol"]
        if sym in MAG7:
            div(f"**{i}.** **{sym}** {q['name']}　{pct_color(q['change_pct'])}　"
                f"${q['price']:.2f}　_↓ 详见七姐妹_")
            hr()
            continue
        elements.append(stock_col_set(
            sym=sym, q=q,
            a=analysis.get(sym, {}),
            news_list=news_map.get(sym, []),
            rank=i,
        ))
        hr()

    # ── 6. 财报日历 ──────────────────────────────────────────────────
    if earnings:
        hr()
        lines = ["📅 **本周财报预告**"]
        today_str = trade_date
        for e in earnings:
            flag = "⚠️" if e["symbol"] in MAG7 else "📌"
            when = "今日" if e["date"] == today_str else e["date"]
            lines.append(f"> {flag} **{e['symbol']}** {e['name']}　{when}")
        div("\n".join(lines))

    # ── 7. 加密一瞥（4列，每币独占一列，手机不断行）─────────────────
    if crypto:
        hr()
        div("₿ **加密一瞥**")
        coin_cols = []
        for coin, d in crypto.items():
            price = f"${d['price']:,.0f}" if coin == "BTC" else f"${d['price']:,.2f}"
            coin_cols.append(f"**{coin}**\n{price}\n{pct_color(d['change_pct'])}")
        col_set(coin_cols)

    hr()
    div("_数据：新浪财经·yfinance·Finnhub·CNN·CoinGecko　AI分析及建议仅供参考，不构成投资意见_")

    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text",
                      "content": f"📊 美股日报 · {trade_date}（{weekday}）"},
            "template": header_color,
        },
        "elements": elements,
    }


# ══════════════════════════════════════════════════════════════════════
# 飞书发送
# ══════════════════════════════════════════════════════════════════════

def send_to_feishu(card):
    token_resp = requests.post(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET}, timeout=10,
    )
    token = token_resp.json()["tenant_access_token"]
    r = requests.post(
        "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"receive_id": FEISHU_RECEIVE_ID, "msg_type": "interactive",
              "content": json.dumps(card)},
        timeout=10,
    )
    return r.json()


# ══════════════════════════════════════════════════════════════════════
# 主流程
# ══════════════════════════════════════════════════════════════════════

def main():
    # ① 行情
    print("① 行情（新浪财经）...")
    quotes = fetch_quotes(SP100)
    valid  = [q for q in quotes if q["change_pct"] != 0.0]
    if len(valid) < 10:
        print(f"⚠️ 有效数据不足（{len(valid)}条），今天可能是非交易日，跳过")
        return
    trade_date, weekday_en = get_trade_date(quotes)
    print(f"   交易日：{trade_date}，{len(valid)} 支有效")

    sorted_q = sorted(valid, key=lambda x: x["change_pct"], reverse=True)
    gainers  = [q["symbol"] for q in sorted_q[:TOP_N]]
    losers   = [q["symbol"] for q in sorted_q[-TOP_N:]]

    # ② 指数
    print("② 指数（yfinance）...")
    indices = fetch_indices()
    print(f"   获取 {len(indices)}/{len(INDEX_TICKERS)} 个指数")

    # ③ 贪恐指数
    print("③ 贪恐指数（CNN）...")
    fear_greed = fetch_fear_greed()
    print(f"   {'分数: ' + str(fear_greed['score']) if fear_greed else '获取失败'}")

    # ④ 板块
    print("④ 板块轮动（yfinance ETFs）...")
    sectors = fetch_sectors()
    print(f"   获取 {len(sectors)}/{len(SECTOR_ETFS)} 个板块")

    # ⑤ 52周位置 + 技术指标
    print("⑤ 52周位置 + 技术分析（yfinance）...")
    w52, tech = fetch_52w_and_technicals(MAG7)
    print(f"   52周 {len(w52)}/7  技术 {len(tech)}/7")

    # ⑥ 分析师评级
    print("⑥ 分析师评级（Finnhub）...")
    analyst_ratings = fetch_analyst_ratings(MAG7)
    print(f"   获取 {len(analyst_ratings)}/7 个评级")

    # ⑦ 加密
    print("⑦ 加密行情（CoinGecko）...")
    crypto = fetch_crypto()
    print(f"   {'BTC ETH SOL OK' if crypto else '获取失败'}")

    # ⑦b 宏观日历
    print("⑦b 宏观日历（Finnhub）...")
    macro_calendar = fetch_macro_calendar()
    print(f"   获取 {len(macro_calendar)} 条事件")

    # ⑦c 盘后/盘前行情（MAG7）
    print("⑦c 盘后行情（yfinance）...")
    postmarket = fetch_postmarket(MAG7)
    print(f"   有盘后数据：{list(postmarket.keys())}")

    # ⑧ 新闻（覆盖七姐妹 + 完整涨跌榜）
    news_targets = list(dict.fromkeys(
        MAG7 + [s for s in gainers if s not in MAG7]
             + [s for s in losers  if s not in MAG7]
    ))
    print(f"⑧ 新闻（Finnhub），共 {len(news_targets)} 只...")
    news_map = collect_news(news_targets, trade_date)
    print(f"   有新闻：{[s for s in news_targets if news_map.get(s)]}")

    # ⑨ Claude 分析（技术面 + 新闻面综合）
    quote_map_targets = {q["symbol"]: q for q in valid if q["symbol"] in news_targets}
    print(f"⑨ Claude 分析...")
    analysis = claude_analyze(quote_map_targets, news_map, tech_map=tech)

    # ⑩ 财报日历
    earn_targets = list(dict.fromkeys(MAG7 + gainers[:5] + losers[:5]))
    print(f"⑩ 财报日历（yfinance）...")
    earnings = fetch_upcoming_earnings(earn_targets, trade_date)
    print(f"   未来7天财报：{[e['symbol'] for e in earnings]}")

    # ⑪ 构建并发送
    print("⑪ 发送飞书消息...")
    card   = build_message(valid, trade_date, weekday_en, analysis, news_map,
                           indices, fear_greed, sectors, w52, analyst_ratings,
                           earnings, crypto, tech=tech,
                           macro_calendar=macro_calendar, postmarket=postmarket)
    result = send_to_feishu(card)

    if result.get("code") == 0:
        print("✅ 发送成功")
    else:
        print(f"❌ 失败：{result}")


if __name__ == "__main__":
    main()
