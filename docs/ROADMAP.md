# Roadmap

## MVP 1.0（当前）
- DEX Screener 新币热点候选：Solana + BSC。
- GoPlus 风险适配器。
- Gate 公共行情 + 回撤扫描。
- X 官方 API / RSS provider。
- OpenAI-compatible LLM provider（适配本地 Qwen）。
- SQLite 事件/候选/模拟仓记录。
- Collector：1U 集邮 + 2x 回本 + moonbag trailing。
- Dip：热门币回撤 + 反弹确认 + TP/SL/trailing。
- Freqtrade Gate dry-run 插件。
- Gate live executor 代码存在但默认不可触发。

## 1.1：真正“早期热点 → 链上执行”
- 以 `0xfnzero/sol-trade-sdk`（MIT）作为 Solana Execution Adapter，不重写 Pump.fun/Raydium/Meteora/Jito 基础设施。
- Helius Enhanced WebSocket / Webhook：新池、聪明钱地址、交易确认。
- Jupiter / Pump / Raydium 路由与滑点模拟。
- 交易前 GoPlus + transaction simulation 双重 hard gate。
- 专用热钱包：余额上限、单笔上限、每日亏损熔断；主钱包绝不接机器人。

## 1.2：BSC / “牛来类”中文热点
- BSC 新池事件与 PancakeSwap 执行 adapter。
- GoPlus EVM token security / transaction simulation。
- Creator wallet / holder concentration / LP 状态。
- 中文热点词实体抽取：电影、游戏、社会事件、梗图、人物。

## 1.3：Smart Money
- 地址观察列表、命中次数、历史胜率只作为特征，不做无脑跟单。
- Helius / BSC RPC + Arkham/Cielo 等可用 API adapter。
- 钱包聚类：同源资金、同步买卖、关联 creator 的降权。

## 1.4：策略研究
- 把所有入场信号写入 event log，即使未买，避免只研究“幸存者”。
- 回放 / walk-forward / parameter sweep。
- 分链、分市值、分叙事类型统计胜率、最大回撤、滑点敏感度。
- Freqtrade 继续负责 CEX 回测；链上事件使用自建 event replay，而不是拿普通 K 线假装新池回测。

## 不做
- 不做“LLM 猜下一个百倍币然后直接控制钱包”。
- 不把 Telegram 不明闭源 bot 或下载 exe 接进主钱包。
- 不承诺稳定盈利或百倍币命中率。
