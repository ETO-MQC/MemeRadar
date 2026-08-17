# MemeRadar MVP 1.0

一个面向“小额试仓 / 集邮 + 热门币回撤低吸”的本地热点雷达与模拟交易工作台。**默认只开模拟盘**。

## 设计原则：不从零发明交易基础设施

MVP 把成熟开源生态拆成可替换层：

- **CloddsBot (MIT)**：参考其 AI provider / skill / risk-engine / Solana DeFi 的分层方式；MVP 不复制钱包密钥逻辑。
- **Freqtrade (GPL-3.0)**：作为 Gate 回撤策略的成熟 dry-run / backtest / live 外部引擎；本仓只提供策略插件与配置，不内嵌其源码。
- **Hummingbot**：后续用于标准化 CEX/DEX connector、订单簿和 paper-trade；Gate 连接器本身已支持 paper trade。
- **CCXT (MIT)**：MVP 的 Gate 实盘适配器依赖它，避免自己实现交易所签名和市场精度处理。
- **sol-trade-sdk (MIT)**：MVP 1.1 计划中的 Solana 实盘执行桥，覆盖 Pump/Raydium/Meteora 等。
- **warp-id/solana-trading-bot**：只参考 TP/SL、pool filter、snipe-list 等产品设计；当前仓库未发现明确 LICENSE，因此不复制其代码。

数据/API 层：DEX Screener（发现）、GoPlus（Token Security）、Gate API（CEX 行情/现货）、X API / RSS（热点账号）、OpenAI-compatible LLM（叙事评分）。

## 现在能用什么

1. Solana + BSC 新币/热点候选扫描。
2. 流动性、成交量、买卖流、年龄、动量、GoPlus、LLM 叙事组成评分。
3. X 指定账号监控（需要 X Bearer Token）与任意 RSS/Atom 源。
4. 本地 Qwen/llama.cpp 或任意 OpenAI-compatible 模型接入。
5. 1U“集邮”模拟策略：2x 时默认卖一半回收本金，剩余 moonbag 用回撤移动止盈；-40% 硬止损。
6. Gate 热门币回撤低吸模拟策略：120 分钟高点回撤 + 反弹确认 + 成交量门槛。
7. Gate watchlist 可在 UI 直接添加。
8. Gate **现货**实盘执行器已写入，但默认锁死；必须同时设置 `LIVE_TRADING_ENABLED=true`、API Key/Secret、以及固定 `LIVE_ARM_CODE` 才会解锁。当前 UI 不自动调用实盘接口，MVP 先用模拟盘验证。
9. Freqtrade Gate dry-run 策略插件与示例配置已附带，可把“低吸策略”交给成熟框架做回测/前向测试。

## Windows 一键运行

双击 `启动_MVP.bat`。首次运行会：创建 `.venv` → 安装依赖 → 打开浏览器 → 启动 `http://127.0.0.1:8765`。

Python 要求：3.11+。不填任何密钥也可运行 DEX Screener + Gate 公共行情 + 模拟盘。

## 接你的本地 Qwen

把 `.env.example` 复制为 `.env`（首次运行会自动复制），然后例如：

```env
LLM_ENABLED=true
LLM_BASE_URL=http://127.0.0.1:8092/v1
LLM_MODEL=local-model
LLM_API_KEY=
```

LLM 只做“有没有真实热点催化/是否纯刷屏”的辅助评分，不直接拿钱包权限。

## X 账号

在 `.env` 填 `X_BEARER_TOKEN`，然后 UI 输入 `@账号`。没有 X API 时仍可添加 RSS/Atom；后续 1.1 会加更多可插拔社交 provider。

## Gate

MVP 默认使用 Gate 公共 REST 行情。你可以在 UI 添加 `TOKEN_USDT`。

真实 Gate API Key 只放 `.env`，不要提交到 Git。建议单独创建 **仅现货交易** 的 API Key，关闭提现权限，并设置 IP 白名单。

## Freqtrade dry-run

目录 `freqtrade/` 已准备：

- `user_data/strategies/MemeDipGateStrategy.py`
- `config.gate.dryrun.example.json`

安装 Freqtrade 后复制配置并保持 `dry_run: true`，先跑 forward test，再考虑任何真实资金。

## 第一次建议怎么测

- 保持 `collector.auto_paper_buy=false`、`dip.auto_paper_buy=false`。
- 手动看 2~3 天雷达，遇到你认为像“现实热点 → 币”的候选只点“模拟买”。
- 观察：发现时市值/流动性、2x 前需要多久、最大回撤、假热点比例。
- 再把自动模拟买打开，让样本至少积累到 100 笔。
- 不要因为某一个历史百倍币把阈值过拟合。

## 安全边界

- 不保存链上私钥。
- 不支持杠杆/合约自动交易。
- 不把 LLM 输出直接当下单指令。
- Gate 实盘默认锁死且 UI MVP 不自动触发。
- 所有新币可能归零；模拟结果不能代表真实成交，因为真实交易还有滑点、MEV、交易失败和流动性撤走。

详见 `docs/ROADMAP.md` 与 `docs/UPSTREAMS.md`。
