#!/usr/bin/env python3
"""
MT5数据源模块
提供实时黄金价格数据获取功能
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import time

# 设置日志
logger = logging.getLogger(__name__)

class MT5DataSource:
    """MT5数据源类"""
    
    def __init__(self):
        self.symbol = "XAUUSD"  # 黄金交易对
        self.connected = False
        self.mt5 = None
        
    def connect(self):
        """连接MT5"""
        try:
            # 尝试导入MT5
            try:
                import MetaTrader5 as mt5
                self.mt5 = mt5
            except ImportError:
                logger.warning("MetaTrader5库未安装，使用模拟数据")
                return self._use_simulation()
            
            # 初始化MT5连接
            if not self.mt5.initialize():
                logger.warning("MT5初始化失败，使用模拟数据")
                return self._use_simulation()
            
            # 检查账户信息
            account_info = self.mt5.account_info()
            if account_info is None:
                logger.warning("无法获取MT5账户信息，使用模拟数据")
                return self._use_simulation()
            
            logger.info(f"MT5连接成功，账户: {account_info.login}")
            self.connected = True
            return True
            
        except Exception as e:
            logger.error(f"MT5连接失败: {e}")
            return self._use_simulation()
    
    def _use_simulation(self):
        """使用模拟数据"""
        logger.info("使用模拟黄金价格数据")
        self.connected = False
        return True
    
    def get_current_price(self):
        """获取当前黄金价格"""
        try:
            if self.connected and self.mt5:
                # 获取实时价格
                tick = self.mt5.symbol_info_tick(self.symbol)
                if tick is not None:
                    current_price = (tick.bid + tick.ask) / 2
                    logger.info(f"MT5实时黄金价格: ${current_price:.2f}")
                    return current_price
                else:
                    logger.warning("无法获取MT5实时价格，使用模拟价格")
            
            # 模拟价格（基于真实黄金价格范围）
            base_price = 3350.0
            variation = np.random.normal(0, 5)  # 正态分布变化
            current_price = base_price + variation
            logger.info(f"模拟黄金价格: ${current_price:.2f}")
            return current_price
            
        except Exception as e:
            logger.error(f"获取当前价格失败: {e}")
            return 3350.0  # 默认价格
    
    def get_historical_data(self, timeframe='H1', count=720):
        """获取历史数据"""
        try:
            if self.connected and self.mt5:
                # 设置时间框架
                if timeframe == 'H1':
                    mt5_timeframe = self.mt5.TIMEFRAME_H1
                elif timeframe == 'H4':
                    mt5_timeframe = self.mt5.TIMEFRAME_H4
                elif timeframe == 'D1':
                    mt5_timeframe = self.mt5.TIMEFRAME_D1
                else:
                    mt5_timeframe = self.mt5.TIMEFRAME_H1
                
                # 获取历史数据
                rates = self.mt5.copy_rates_from_pos(self.symbol, mt5_timeframe, 0, count)
                
                if rates is not None and len(rates) > 0:
                    # 转换为DataFrame
                    df = pd.DataFrame(rates)
                    df['timestamp'] = pd.to_datetime(df['time'], unit='s')

                    # 重命名列，确保格式一致
                    df.rename(columns={
                        'open': 'open',
                        'high': 'high',
                        'low': 'low',
                        'close': 'close',
                        'tick_volume': 'volume'
                    }, inplace=True)

                    # 删除原始time列，保留timestamp列
                    if 'time' in df.columns:
                        df.drop('time', axis=1, inplace=True)

                    # 确保数据类型正确
                    for col in ['open', 'high', 'low', 'close']:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    df['volume'] = pd.to_numeric(df['volume'], errors='coerce').fillna(1000)

                    logger.info(f"MT5获取到 {len(df)} 条历史数据，列: {list(df.columns)}")
                    return df
                else:
                    logger.warning("MT5无法获取历史数据，使用模拟数据")
            
            # 生成模拟历史数据
            return self._generate_simulated_data(timeframe, count)
            
        except Exception as e:
            logger.error(f"获取历史数据失败: {e}")
            return self._generate_simulated_data(timeframe, count)
    
    def _generate_simulated_data(self, timeframe='H1', count=720):
        """生成模拟历史数据"""
        try:
            # 时间设置
            if timeframe == 'H1':
                freq = 'H'
                end_time = datetime.now()
                start_time = end_time - timedelta(hours=count)
            elif timeframe == 'H4':
                freq = '4H'
                end_time = datetime.now()
                start_time = end_time - timedelta(hours=count*4)
            elif timeframe == 'D1':
                freq = 'D'
                end_time = datetime.now()
                start_time = end_time - timedelta(days=count)
            else:
                freq = 'H'
                end_time = datetime.now()
                start_time = end_time - timedelta(hours=count)
            
            # 生成时间索引
            time_index = pd.date_range(start=start_time, end=end_time, freq=freq)[:count]
            
            # 黄金价格模拟参数
            base_price = 3350.0
            np.random.seed(42)  # 确保可重复性
            
            # 生成价格走势
            returns = np.random.normal(0, 0.002, len(time_index))  # 0.2%的日波动率
            returns[0] = 0  # 第一个收益率为0
            
            # 累积收益率生成价格
            price_series = base_price * np.exp(np.cumsum(returns))
            
            # 添加趋势和季节性
            trend = np.linspace(0, 20, len(time_index))  # 轻微上涨趋势
            seasonal = 10 * np.sin(np.linspace(0, 4*np.pi, len(time_index)))  # 季节性波动
            price_series = price_series + trend + seasonal
            
            # 生成OHLC数据
            data = []
            for i, (timestamp, close) in enumerate(zip(time_index, price_series)):
                # 生成合理的OHLC数据
                volatility = np.random.uniform(0.5, 2.0)  # 随机波动率
                
                high = close + np.random.uniform(0, volatility)
                low = close - np.random.uniform(0, volatility)
                
                if i == 0:
                    open_price = close - np.random.uniform(-1, 1)
                else:
                    open_price = data[i-1]['close'] + np.random.uniform(-0.5, 0.5)
                
                # 确保OHLC逻辑正确
                high = max(high, open_price, close)
                low = min(low, open_price, close)
                
                volume = np.random.randint(1000, 5000)  # 模拟成交量
                
                data.append({
                    'open': open_price,
                    'high': high,
                    'low': low,
                    'close': close,
                    'volume': volume
                })
            
            # 创建DataFrame
            df = pd.DataFrame(data, index=time_index)

            # 添加timestamp列
            df['timestamp'] = df.index

            # 确保数据类型正确
            for col in ['open', 'high', 'low', 'close']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            df['volume'] = pd.to_numeric(df['volume'], errors='coerce').fillna(2000)

            logger.info(f"生成了 {len(df)} 条模拟黄金数据，列: {list(df.columns)}")
            return df
            
        except Exception as e:
            logger.error(f"生成模拟数据失败: {e}")
            # 返回最基本的数据
            time_index = pd.date_range(start=datetime.now()-timedelta(hours=count), 
                                     end=datetime.now(), freq='H')[:count]
            base_data = {
                'open': [3350.0] * len(time_index),
                'high': [3355.0] * len(time_index),
                'low': [3345.0] * len(time_index),
                'close': [3350.0] * len(time_index),
                'volume': [2000] * len(time_index)
            }
            return pd.DataFrame(base_data, index=time_index)
    
    def get_symbol_info(self):
        """获取交易品种信息"""
        try:
            if self.connected and self.mt5:
                symbol_info = self.mt5.symbol_info(self.symbol)
                if symbol_info is not None:
                    return {
                        'symbol': symbol_info.name,
                        'description': symbol_info.description,
                        'point': symbol_info.point,
                        'digits': symbol_info.digits,
                        'spread': symbol_info.spread,
                        'trade_mode': symbol_info.trade_mode
                    }
            
            # 返回模拟信息
            return {
                'symbol': 'XAUUSD',
                'description': 'Gold vs US Dollar',
                'point': 0.01,
                'digits': 2,
                'spread': 3,
                'trade_mode': 'FULL'
            }
            
        except Exception as e:
            logger.error(f"获取品种信息失败: {e}")
            return {
                'symbol': 'XAUUSD',
                'description': 'Gold vs US Dollar (Simulated)',
                'point': 0.01,
                'digits': 2,
                'spread': 3,
                'trade_mode': 'SIMULATION'
            }
    
    def disconnect(self):
        """断开MT5连接"""
        try:
            if self.connected and self.mt5:
                self.mt5.shutdown()
                logger.info("MT5连接已断开")
            self.connected = False
        except Exception as e:
            logger.error(f"断开MT5连接失败: {e}")

# 全局MT5数据源实例
mt5_data_source = MT5DataSource()

def get_mt5_data_source():
    """获取MT5数据源实例"""
    return mt5_data_source

if __name__ == "__main__":
    # 测试MT5数据源
    mt5_source = MT5DataSource()
    
    print("测试MT5数据源...")
    if mt5_source.connect():
        print("连接成功")
        
        # 测试获取当前价格
        current_price = mt5_source.get_current_price()
        print(f"当前黄金价格: ${current_price:.2f}")
        
        # 测试获取历史数据
        historical_data = mt5_source.get_historical_data('H1', 100)
        print(f"历史数据: {len(historical_data)} 条记录")
        print(historical_data.tail())
        
        # 测试获取品种信息
        symbol_info = mt5_source.get_symbol_info()
        print(f"品种信息: {symbol_info}")
        
        mt5_source.disconnect()
    else:
        print("连接失败")
