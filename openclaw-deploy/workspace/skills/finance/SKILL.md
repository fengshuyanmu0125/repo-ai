---
name: finance
description: 美股行情查询。支持单只/多只股票详情、大盘概况、板块轮动、加密货币行情。用法：/finance NVDA，/finance NVDA AAPL TSLA，/finance market，/finance sectors，/finance crypto
---

根据用户传入的参数 `$ARGUMENTS`，判断查询类型并获取数据后用**中文**回复。

Python 解释器：`python3`（路径 `/opt/venv/bin/python3`，如不可用则用 `python3`）

---

## 1. 大盘概况（market）

参数是 `market` 时，用 `system.run` 执行：

```python
import yfinance as yf, json

symbols = {
    "S&P 500": "^GSPC", "NASDAQ": "^IXIC", "道指": "^DJI",
    "VIX": "^VIX", "10年债": "^TNX", "美元指数": "DX-Y.NYB"
}
sectors = {
    "科技":"XLK","医疗":"XLV","金融":"XLF","能源":"XLE","消费":"XLY",
    "工业":"XLI","材料":"XLB","公用":"XLU","通信":"XLC","地产":"XLRE","日消":"XLP"
}

result = {}
all_syms = list(symbols.values()) + list(sectors.values())
tickers = yf.download(all_syms, period="2d", auto_adjust=True, progress=False)["Close"]
for name, sym in {**symbols, **sectors}.items():
    if sym in tickers.columns:
        row = tickers[sym].dropna()
        if len(row) >= 2:
            cur, prev = float(row.iloc[-1]), float(row.iloc[-2])
            result[name] = {"price": round(cur,2), "change_pct": round((cur-prev)/prev*100,2)}

print(json.dumps(result, ensure_ascii=False))
```

输出中文格式：

**📊 市场概况**
三大指数：S&P 点位 涨跌% / NASDAQ / 道指
市场情绪：VIX X.X（恐慌程度）/ 10年债 X.XX% / 美元指数
板块轮动：🔥 强势前3 / 🧊 弱势后3
一句话点评资金整体方向

---

## 2. 板块表现（sectors）

参数是 `sectors` 时，获取11个板块 ETF 今日涨跌排序输出：

```
📦 板块轮动（今日）
1. 能源  XLE  +1.20%
...
11. 工业 XLI  -1.50%
```

一句话总结今日板块资金流向。

---

## 3. 加密行情（crypto）

参数是 `crypto` 时，执行：

```python
import yfinance as yf, json
syms = {"BTC": "BTC-USD", "ETH": "ETH-USD", "SOL": "SOL-USD", "BNB": "BNB-USD"}
result = {}
for name, sym in syms.items():
    t = yf.Ticker(sym)
    fi = t.fast_info
    try:
        result[name] = {"price": round(fi.last_price,2), "change_pct": round((fi.last_price - fi.previous_close)/fi.previous_close*100,2)}
    except: pass
print(json.dumps(result, ensure_ascii=False))
```

输出格式：

```
₿ 加密行情
BTC  $87,000  -1.20%
ETH  $2,100   +0.80%
SOL  $145     +2.10%
```

---

## 4. 单只/多只股票详情（默认）

参数是股票代码时（如 `NVDA` 或 `NVDA AAPL TSLA`），对每只股票执行：

```python
import yfinance as yf, json, os, requests

sym = "NVDA"  # 替换为实际代码
t = yf.Ticker(sym)
info = t.info
hist = t.history(period="1d")
fast = t.fast_info

finnhub_key = os.environ.get("FINNHUB_API_KEY", os.environ.get("FINNHUB_TOKEN", ""))
ratings = {}
news_list = []
try:
    if finnhub_key:
        r = requests.get(
            f"https://finnhub.io/api/v1/stock/recommendation?symbol={sym}&token={finnhub_key}",
            timeout=5)
        data = r.json()
        if data: ratings = data[0]
        # 近期新闻
        from datetime import datetime, timedelta
        to_d = datetime.now().strftime("%Y-%m-%d")
        fr_d = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        nr = requests.get(
            f"https://finnhub.io/api/v1/company-news?symbol={sym}&from={fr_d}&to={to_d}&token={finnhub_key}",
            timeout=5)
        news_list = [n["headline"] for n in nr.json()[:3]] if nr.ok else []
except: pass

result = {
    "price": round(fast.last_price, 2),
    "change_pct": round((fast.last_price - fast.previous_close)/fast.previous_close*100, 2),
    "open": round(float(hist["Open"].iloc[-1]), 2) if not hist.empty else None,
    "high": round(float(hist["High"].iloc[-1]), 2) if not hist.empty else None,
    "low": round(float(hist["Low"].iloc[-1]), 2) if not hist.empty else None,
    "volume_m": round(fast.three_month_average_volume/1e6, 1),
    "market_cap": info.get("marketCap"),
    "pe": info.get("trailingPE"),
    "week52_low": info.get("fiftyTwoWeekLow"),
    "week52_high": info.get("fiftyTwoWeekHigh"),
    "target_price": info.get("targetMeanPrice"),
    "short_name": info.get("shortName",""),
    "ratings": ratings,
    "news": news_list,
}
print(json.dumps(result, ensure_ascii=False))
```

对每只股票，中文输出：

---
**[代码] 公司名** `+X.XX%`　$XXX.XX

**📊 行情**
- 今日：开 $X / 高 $X / 低 $X / 量 XXM
- 市值：$X万亿　PE：X.Xx
- 52周：$低 ~ $高，当前**在高点XX%**（接近年内偏高/中位/偏低区间）

**🏦 分析师评级**
- 综合评级（强烈买入/买入/持有/卖出）
- 目标价：$XXX，较当前**上行空间 +XX.X%**

**📰 近期动态**（2-3条英文标题翻译成中文，每条1句）

**💡 综合判断**：结合价格位置、评级、新闻，给出1句中文点评

---

查询多只时，末尾加横向比较：谁最强/最弱、估值或动能差异。

---

## 注意
- 优先使用 `/opt/venv/bin/python3`，不可用时用 `python3`
- 环境变量 `FINNHUB_API_KEY` 由容器注入，直接用 `os.environ.get` 读取
- 股票代码全大写：NVDA AAPL MSFT TSLA META AMZN GOOGL
- 工具调用失败时说明原因，不捏造数据
- 所有输出使用中文
