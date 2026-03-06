---
name: finance
description: 美股行情查询。支持单只/多只股票详情、大盘概况、板块轮动、加密货币行情。用法：/finance NVDA，/finance NVDA AAPL TSLA，/finance market，/finance sectors，/finance crypto
---

**重要**：处理 /finance 时**必须**调用 **exec** 工具在 gateway 上执行 Python 脚本获取数据，**禁止**使用网页搜索、Brave API 或其它联网查行情；未配置 Brave 时会报错，本 skill 用 yfinance 无需 Brave。

根据用户传入的参数 `$ARGUMENTS`，判断查询类型，然后**用 exec 工具**执行对应 Python，把输出整理成中文回复。

---

## 1. 大盘概况（market）

参数是 `market` 时，用 **exec** 工具执行（host=gateway），command 为以下 Python 脚本：

```python
import yfinance as yf, json, datetime, pytz

symbols = {
    "S&P 500": "^GSPC", "NASDAQ": "^IXIC", "道指": "^DJI",
    "VIX": "^VIX", "10年债": "^TNX", "美元指数": "DX-Y.NYB"
}
sectors = {
    "科技":"XLK","医疗":"XLV","金融":"XLF","能源":"XLE","消费":"XLY",
    "工业":"XLI","材料":"XLB","公用":"XLU","通信":"XLC","地产":"XLRE","日消":"XLP"
}

result = {}
tickers = yf.download(list(symbols.values()) + list(sectors.values()), period="2d", auto_adjust=True, progress=False)["Close"]
for name, sym in {**symbols, **sectors}.items():
    if sym in tickers.columns:
        row = tickers[sym].dropna()
        if len(row) >= 2:
            cur, prev = row.iloc[-1], row.iloc[-2]
            result[name] = {"price": round(cur,2), "change_pct": round((cur-prev)/prev*100,2)}

print(json.dumps(result, ensure_ascii=False))
```

输出格式（中文）：

**📊 市场概况**
三大指数：S&P 点位 涨跌% / NASDAQ / 道指
市场情绪：VIX X.X（判断恐慌程度）/ 10年债 X.XX% / 美元指数 XXX.X
板块轮动：🔥 强势前3 / 🧊 弱势后3
一句话点评：今日资金整体方向

---

## 2. 板块表现（sectors）

参数是 `sectors` 时，获取11个板块 ETF 今日涨跌，按涨幅排序输出：

```
📦 板块轮动（今日）
1. 能源  XLE  +1.20%
2. 科技  XLK  +0.80%
...
11. 工业 XLI  -1.50%
```

一句话总结今日板块资金流向。

---

## 3. 加密行情（crypto）

参数是 `crypto` 时，用 **exec** 工具执行：

```python
import yfinance as yf, json
syms = {"BTC": "BTC-USD", "ETH": "ETH-USD", "SOL": "SOL-USD", "BNB": "BNB-USD"}
result = {}
for name, sym in syms.items():
    t = yf.Ticker(sym)
    info = t.fast_info
    try:
        result[name] = {"price": round(info.last_price,2), "change_pct": round((info.last_price - info.previous_close)/info.previous_close*100,2)}
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

参数是股票代码（如 `NVDA` 或 `NVDA AAPL TSLA`）时，对每只股票用 **exec** 工具执行：

```python
import yfinance as yf, json, os, requests

sym = "NVDA"  # 替换为实际代码
t = yf.Ticker(sym)
info = t.info
hist = t.history(period="1d")
fast = t.fast_info

# 分析师评级（Finnhub）
finnhub_key = ""  # 从 ~/.openclaw/workspace/.env 或环境变量读取
ratings = {}
try:
    env_path = os.path.expanduser("~/ai/openclaw-deploy/jobs/market-report/.env")
    for line in open(env_path):
        if line.startswith("FINNHUB_API_KEY"):
            finnhub_key = line.split("=",1)[1].strip()
    if finnhub_key:
        r = requests.get(f"https://finnhub.io/api/v1/stock/recommendation?symbol={sym}&token={finnhub_key}", timeout=5)
        data = r.json()
        if data: ratings = data[0]
except: pass

result = {
    "price": round(fast.last_price, 2),
    "change_pct": round((fast.last_price - fast.previous_close)/fast.previous_close*100, 2),
    "open": round(hist["Open"].iloc[-1], 2) if not hist.empty else None,
    "high": round(hist["High"].iloc[-1], 2) if not hist.empty else None,
    "low": round(hist["Low"].iloc[-1], 2) if not hist.empty else None,
    "volume": round(fast.three_month_average_volume/1e6, 1),
    "market_cap": info.get("marketCap"),
    "pe": info.get("trailingPE"),
    "week52_low": info.get("fiftyTwoWeekLow"),
    "week52_high": info.get("fiftyTwoWeekHigh"),
    "target_price": info.get("targetMeanPrice"),
    "ratings": ratings,
}
print(json.dumps(result, ensure_ascii=False))
```

对每只股票，用中文输出：

---
**[代码] 中文公司名** `+X.XX%`　$XXX.XX

**📊 行情**
- 今日：开 $X / 高 $X / 低 $X / 量 XXM
- 市值：$X万亿　PE：X.Xx
- 52周：$低 ~ $高，当前**在高点XX%**（接近年内偏高/中位/偏低区间）

**🏦 分析师评级**
- 综合评级（买入/持有/卖出数量）
- 目标价：$XXX，较当前**上行空间 +XX.X%**

**📰 近期动态**（2-3条中文摘要，每条1句）

**💡 综合判断**：结合位置、评级、新闻，1句中文点评

---

查询多只时，末尾加横向比较：谁最强/最弱、估值或动能差异。

---

## 注意
- 必须用 **exec** 工具执行 Python（不要用网页搜索/Brave）。本机 gateway 已配置 PATH 含 anaconda，`python3` 即带 yfinance
- 股票代码全大写：NVDA AAPL MSFT TSLA META AMZN GOOGL
- 工具调用失败时说明原因，不要捏造数据
- 所有输出使用中文，数字保留合理精度
