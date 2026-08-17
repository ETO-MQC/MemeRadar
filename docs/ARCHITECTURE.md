# Architecture

```text
[X API / RSS] ------> SocialProvider ----> LLM Narrative ----┐
                                                            │
[DEX Screener] -----> Discovery ----> GoPlus Risk ----------+--> Score/Rules --> PaperExecutor
                                                            │                    ├─ Collector 1U
[Gate public API] --> Dip Detector --------------------------┘                    └─ Hot Dip

                                                     optional external engines
                                                     ├─ Freqtrade (Gate CEX)
                                                     ├─ CloddsBot (agent / skills)
                                                     └─ sol-trade-sdk (Solana, v1.1)
```

核心原则：**AI 不在交易热路径**。风险 hard-gate、仓位、止盈止损和熔断全部确定性执行。
