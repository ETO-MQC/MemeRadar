# Upstream / Open-source reuse map

| Upstream | License / status | 在本项目里的角色 |
|---|---|---|
| alsk1992/CloddsBot | MIT | AI/provider/skills/risk-engine 分层参考；未来可做外部 agent bridge |
| 0xfnzero/sol-trade-sdk | MIT | 1.1 Solana 实盘执行层首选 |
| freqtrade/freqtrade | GPL-3.0 | Gate dry-run、backtest、live 外部引擎；本项目只提供插件/配置 |
| hummingbot/hummingbot | Apache-2.0（请安装时再次核对仓库 LICENSE） | Gate paper-trade / connector 架构参考，后续可接 Gateway |
| ccxt/ccxt | MIT | 当前 Gate live adapter 的交易所 SDK |
| warp-id/solana-trading-bot | 未在仓库根目录找到 LICENSE | 仅参考配置思想，不复制代码 |

## 为什么不把所有仓库源码直接粘进来

“站在巨人的肩膀上”不等于把几个仓库硬合并。不同许可证、运行时和密钥模型会让安全性更差。MVP 采用 **Adapter + 外部引擎**：可复用成熟底层，又能随时替换某个项目。

运行 `scripts/install_upstreams.ps1` 可把明确选择的上游源码拉到本地 `upstreams/` 供审计/继续开发；该目录默认不提交 Git。
