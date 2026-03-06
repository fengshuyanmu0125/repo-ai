---
description: 美股行情查询，支持单只/多只股票详情、大盘概况、板块、加密货币
argument-hint: 股票代码如「finance NVDA」，多只「finance NVDA AAPL TSLA」，大盘「finance market」，板块「finance sectors」，加密「finance crypto」
---

# 美股行情查询

根据 $ARGUMENTS 的内容，判断查询类型并调用对应工具：

---

## 1. 大盘概况（market）

如果 $ARGUMENTS 是 `market`，依次调用：
1. `get_market_overview` — 三大指数、VIX、贪恐指数、10年债、美元指数
2. `get_sector_performance` — 11个板块 ETF 今日表现

用中文输出：

**📊 市场概况**

三大指数：S&P / NASDAQ / DOW 当前点位及今日涨跌
市场情绪：VIX 恐慌值（+判断）、贪/恐指数（+判断）、10年债收益率、美元指数
板块轮动：🔥 强势前3（名称+涨幅）/ 🧊 弱势后3（名称+跌幅）
一句话点评：资金今日整体方向

---

## 2. 板块表现（sectors）

如果 $ARGUMENTS 是 `sectors`，调用 `get_sector_performance`，输出11个板块排行，格式：

```
📦 板块轮动
1. 能源      +1.20%
2. 科技      +0.80%
...
11. 工业     -1.50%
```

用一句话总结今日板块资金流向。

---

## 3. 加密行情（crypto）

如果 $ARGUMENTS 是 `crypto`，调用 `get_crypto_prices`，输出：

```
₿ 加密行情
BTC   $87,000   -1.20%
ETH   $2,100    +0.80%
SOL   $145      +2.10%
```

---

## 4. 单只/多只股票详情（默认）

如果 $ARGUMENTS 是股票代码（如 `NVDA` 或 `NVDA AAPL TSLA`），对每只股票调用 `get_stock_detail`。

对每只股票，用中文输出：

---
**[代码] 中文公司名** `+X.XX%`  $XXX.XX

📊 行情
- 今日：开 $X / 高 $X / 低 $X / 量 XXM
- 52周：$低 ~ $高，当前在高点 XX%

📈 技术面（如有数据）
- 趋势 / RSI / MACD 简要判断

🏦 分析师评级
- 综合评级，买入/持有/卖出人数

📰 近期动态（2-3条中文新闻摘要，每条1句话）

💡 综合判断：[结合价格位置、评级、新闻，给出1句中文点评]

---

查询多只时，最后加一段横向比较：谁最强/最弱、估值或动能差异。

---

## 注意
- 股票代码全大写，如 NVDA AAPL MSFT TSLA META AMZN GOOGL
- 工具调用失败时说明原因，不要捏造数据
- 所有输出使用中文，数字保留原始精度
