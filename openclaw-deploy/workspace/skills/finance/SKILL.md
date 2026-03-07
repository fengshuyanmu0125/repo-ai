---
name: finance
description: 美股行情查询。用法：/finance NVDA
---

查询 `$ARGUMENTS` 指定的股票行情，用飞书卡片格式回复。

## 查询步骤

使用 yfinance 获取数据，然后构建飞书卡片发送。

### 1. 获取数据

调用 Python 获取股票信息：

```python
import yfinance as yf
ticker = yf.Ticker("NVDA")  # 替换为实际代码
info = ticker.info
hist = ticker.history(period="1d")
```

需要获取的数据：
- 当前价格：`info.get("currentPrice")` 或 `info.get("regularMarketPrice")`
- 涨跌幅：从 previousClose 计算
- 今日开高低：从 history 获取
- 市值：`info.get("marketCap")`
- PE：`info.get("trailingPE")`
- 52周高低：`info.get("fiftyTwoWeekHigh/Low")`

### 2. 构建卡片

```json
{
  "config": {"wide_screen_mode": true},
  "header": {
    "title": {"tag": "plain_text", "content": "📊 NVDA 英伟达 行情"},
    "template": "blue"
  },
  "elements": [
    {"tag": "div", "text": {"tag": "lark_md", "content": "**NVDA** 英伟达　<font color='red'>**+2.50%**</font>　**$180.00**"}},
    {"tag": "hr"},
    {"tag": "div", "text": {"tag": "lark_md", "content": "📊 **今日行情**\n> 开盘 $178.00　最高 $182.00　最低 $177.50"}},
    {"tag": "hr"},
    {"tag": "div", "text": {"tag": "lark_md", "content": "_数据来源：Yahoo Finance_"}}
  ]
}
```

### 3. 发送卡片

用 `feishu_chat` 工具的 `send_interactive_message` 发送卡片。

## 颜色规则

- 涨：`<font color='red'>**+X.XX%**</font>`
- 跌：`<font color='green'>**-X.XX%**</font>`
- 卡片颜色：涨≥3% 用 green，涨≥0 用 blue，跌≥-3% 用 yellow，大跌用 red

## 注意

- 必须以飞书卡片形式回复，不要纯文本
- 如果获取失败，告诉用户稍后重试
