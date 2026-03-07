---
name: finance
description: 美股行情查询。支持单只/多只股票详情。用法：/finance NVDA，/finance NVDA AAPL TSLA
---

处理 /finance 命令时，根据用户传入的参数 `$ARGUMENTS` 查询股票行情。

**重要**：使用 **exec** 工具在 gateway 上执行 Python 脚本获取数据。

---

## 查询单只或多只股票

参数是股票代码（如 `NVDA` 或 `NVDA AAPL TSLA`）时，对**每只**股票执行以下命令：

```
python3 /root/.openclaw/plugins/stock-query/query.py SYMBOL
```

其中 SYMBOL 替换为实际股票代码（大写）。

脚本会输出飞书卡片 JSON，你需要：
1. 使用 **exec** 工具执行命令，host 设为 `gateway`
2. 解析返回的 JSON
3. 使用 **feishu_chat** 工具的 `send_interactive_message` 发送卡片

### 示例调用流程

用户输入：`/finance NVDA`

1. 调用 exec 工具：
   - command: `python3 /root/.openclaw/plugins/stock-query/query.py NVDA`
   - host: `gateway`

2. 解析返回的 JSON（这是一个飞书卡片格式）

3. 调用 feishu_chat 工具发送卡片：
   - tool: `send_interactive_message`
   - 参数: receive_id（从上下文获取）, card（exec 返回的 JSON）

### 多只股票

如果用户输入多只股票如 `/finance NVDA AAPL TSLA`，依次查询每只，然后：
- 可以分别发送卡片
- 或者在最后加一段对比总结

---

## 特殊命令

### market - 大盘概况

用户输入 `/finance market` 时，执行：
```
python3 -c "
import yfinance as yf, json
symbols = {'^GSPC':'S&P500', '^IXIC':'NASDAQ', '^DJI':'DOW', '^VIX':'VIX'}
result = []
for sym, name in symbols.items():
    try:
        t = yf.Ticker(sym)
        h = t.history(period='2d')['Close'].dropna()
        if len(h) >= 2:
            pct = (h.iloc[-1] - h.iloc[-2]) / h.iloc[-2] * 100
            result.append(f'{name}: {h.iloc[-1]:.2f} ({pct:+.2f}%)')
    except: pass
print('\\n'.join(result))
"
```

用文字回复用户（不需要卡片）。

### crypto - 加密货币

用户输入 `/finance crypto` 时，执行：
```
python3 -c "
import requests, json
r = requests.get('https://api.coingecko.com/api/v3/simple/price', params={'ids':'bitcoin,ethereum,solana','vs_currencies':'usd','include_24hr_change':'true'}, timeout=10)
d = r.json()
for coin, name in [('bitcoin','BTC'),('ethereum','ETH'),('solana','SOL')]:
    p = d[coin]['usd']
    c = d[coin].get('usd_24h_change', 0)
    print(f'{name}: \${p:,.2f} ({c:+.2f}%)')
"
```

用文字回复用户。

---

## 注意事项

- 必须用 **exec** 工具执行命令（host=gateway）
- 股票代码全大写：NVDA AAPL MSFT TSLA META AMZN GOOGL
- 工具调用失败时说明原因，不要捏造数据
- 发送卡片时使用 feishu_chat 的 send_interactive_message
