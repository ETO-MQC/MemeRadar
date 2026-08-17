# 这是给 Freqtrade 外部引擎使用的策略插件，不复制 Freqtrade 源码。
# 目的：把“热门币回撤低吸”交给成熟的 dry-run/backtest/live 框架验证。
from freqtrade.strategy import IStrategy
from pandas import DataFrame
import talib.abstract as ta

class MemeDipGateStrategy(IStrategy):
    timeframe = "1m"
    stoploss = -0.06
    minimal_roi = {"0": 0.10}
    trailing_stop = True
    trailing_stop_positive = 0.04
    trailing_stop_positive_offset = 0.06
    trailing_only_offset_is_reached = True
    process_only_new_candles = True

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["high120"] = dataframe["high"].rolling(120, min_periods=30).max()
        dataframe["drawdown"] = (dataframe["high120"] - dataframe["close"]) / dataframe["high120"]
        dataframe["volma"] = dataframe["volume"].rolling(30, min_periods=10).mean()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        cond=(dataframe["drawdown"] >= 0.15) & (dataframe["close"] > dataframe["close"].shift(1)*1.012) & (dataframe["volume"] > dataframe["volma"]) & (dataframe["rsi"] < 55)
        dataframe.loc[cond, "enter_long"] = 1
        dataframe.loc[cond, "enter_tag"] = "hot_dip_rebound"
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[(dataframe["rsi"] > 78), "exit_long"] = 1
        return dataframe
