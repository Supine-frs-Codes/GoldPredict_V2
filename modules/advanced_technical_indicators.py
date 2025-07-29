#!/usr/bin/env python3
"""
高级技术指标模块
集成更多专业技术分析指标
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import logging

# 尝试导入talib，如果失败则使用备用实现
try:
    import talib
    TALIB_AVAILABLE = True
    print("[技术指标] 使用 TA-Lib 进行技术指标计算")
except ImportError:
    TALIB_AVAILABLE = False
    print("[警告] talib未安装，将使用 finta 作为备用技术指标库")

# 导入备用技术指标库
try:
    from finta import TA
    FINTA_AVAILABLE = True
except ImportError:
    FINTA_AVAILABLE = False
    print("[警告] finta也未安装，将使用简化的技术指标计算")

logger = logging.getLogger(__name__)


class AdvancedTechnicalIndicators:
    """高级技术指标计算器"""
    
    def __init__(self):
        self.indicators = {}
        self.weights = {
            'macd': 0.15,
            'bollinger': 0.15,
            'kdj': 0.12,
            'williams': 0.10,
            'volume': 0.08,
            'ichimoku': 0.12,
            'fibonacci': 0.08,
            'pivot': 0.10,
            'atr': 0.10
        }
        
        print("[技术指标] 高级技术指标模块初始化")
    
    def calculate_all_indicators(self, df: pd.DataFrame) -> Dict:
        """计算所有技术指标"""
        try:
            if len(df) < 50:  # 需要足够的数据点
                return self._get_default_indicators()
            
            # 确保数据列存在
            required_columns = ['price', 'bid', 'ask']
            for col in required_columns:
                if col not in df.columns:
                    logger.warning(f"缺少必要列: {col}")
                    return self._get_default_indicators()
            
            # 准备价格数据
            high = df['ask'].values  # 使用ask作为高价
            low = df['bid'].values   # 使用bid作为低价
            close = df['price'].values
            volume = df.get('volume', pd.Series([1000] * len(df))).values
            
            indicators = {}
            
            # 1. MACD指标
            indicators['macd'] = self._calculate_macd(close)
            
            # 2. 布林带指标
            indicators['bollinger'] = self._calculate_bollinger_bands(close)
            
            # 3. KDJ指标
            indicators['kdj'] = self._calculate_kdj(high, low, close)
            
            # 4. 威廉指标
            indicators['williams'] = self._calculate_williams_r(high, low, close)
            
            # 5. 成交量指标
            indicators['volume'] = self._calculate_volume_indicators(close, volume)
            
            # 6. 一目均衡表
            indicators['ichimoku'] = self._calculate_ichimoku(high, low, close)
            
            # 7. 斐波那契回调
            indicators['fibonacci'] = self._calculate_fibonacci_retracement(high, low, close)
            
            # 8. 枢轴点
            indicators['pivot'] = self._calculate_pivot_points(high, low, close)
            
            # 9. ATR (平均真实波幅)
            indicators['atr'] = self._calculate_atr(high, low, close)
            
            # 计算综合信号
            indicators['composite_signal'] = self._calculate_composite_signal(indicators)
            
            self.indicators = indicators
            return indicators
            
        except Exception as e:
            logger.error(f"计算技术指标错误: {e}")
            return self._get_default_indicators()
    
    def _calculate_macd(self, close: np.ndarray) -> Dict:
        """计算MACD指标"""
        try:
            if TALIB_AVAILABLE:
                # 使用 TA-Lib，确保数据类型为 double
                close_double = close.astype(np.float64)
                macd, macd_signal, macd_hist = talib.MACD(close_double, fastperiod=12, slowperiod=26, signalperiod=9)
                current_macd = macd[-1] if not np.isnan(macd[-1]) else 0
                current_signal = macd_signal[-1] if not np.isnan(macd_signal[-1]) else 0
                current_hist = macd_hist[-1] if not np.isnan(macd_hist[-1]) else 0
            elif FINTA_AVAILABLE:
                # 使用 finta 作为备用
                df = pd.DataFrame({'close': close})
                macd_result = TA.MACD(df)
                if len(macd_result) > 0:
                    current_macd = macd_result['MACD'].iloc[-1] if not pd.isna(macd_result['MACD'].iloc[-1]) else 0
                    current_signal = macd_result['SIGNAL'].iloc[-1] if not pd.isna(macd_result['SIGNAL'].iloc[-1]) else 0
                    current_hist = current_macd - current_signal
                else:
                    current_macd = current_signal = current_hist = 0
            else:
                # 简化实现
                current_macd = current_signal = current_hist = 0

            # 生成信号
            if current_macd > current_signal and current_hist > 0:
                signal = 'bullish'
                strength = min(abs(current_hist) * 1000, 1.0)
            elif current_macd < current_signal and current_hist < 0:
                signal = 'bearish'
                strength = min(abs(current_hist) * 1000, 1.0)
            else:
                signal = 'neutral'
                strength = 0.5

            return {
                'macd': current_macd,
                'signal': current_signal,
                'histogram': current_hist,
                'trend_signal': signal,
                'strength': strength
            }

        except Exception as e:
            logger.error(f"MACD计算错误: {e}")
            return {'macd': 0, 'signal': 0, 'histogram': 0, 'trend_signal': 'neutral', 'strength': 0.5}
    
    def _calculate_bollinger_bands(self, close: np.ndarray) -> Dict:
        """计算布林带指标"""
        try:
            if TALIB_AVAILABLE:
                # 使用 TA-Lib，确保数据类型为 double
                close_double = close.astype(np.float64)
                upper, middle, lower = talib.BBANDS(close_double, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
                current_upper = upper[-1] if not np.isnan(upper[-1]) else close[-1] * 1.01
                current_middle = middle[-1] if not np.isnan(middle[-1]) else close[-1]
                current_lower = lower[-1] if not np.isnan(lower[-1]) else close[-1] * 0.99
            elif FINTA_AVAILABLE:
                # 使用 finta 作为备用
                df = pd.DataFrame({'close': close})
                bb_result = TA.BBANDS(df)
                if len(bb_result) > 0:
                    current_upper = bb_result['BB_UPPER'].iloc[-1] if not pd.isna(bb_result['BB_UPPER'].iloc[-1]) else close[-1] * 1.01
                    current_middle = bb_result['BB_MIDDLE'].iloc[-1] if not pd.isna(bb_result['BB_MIDDLE'].iloc[-1]) else close[-1]
                    current_lower = bb_result['BB_LOWER'].iloc[-1] if not pd.isna(bb_result['BB_LOWER'].iloc[-1]) else close[-1] * 0.99
                else:
                    current_upper = close[-1] * 1.01
                    current_middle = close[-1]
                    current_lower = close[-1] * 0.99
            else:
                # 简化实现：使用移动平均和标准差
                window = min(20, len(close))
                if window > 1:
                    recent_close = close[-window:]
                    current_middle = np.mean(recent_close)
                    std_dev = np.std(recent_close)
                    current_upper = current_middle + 2 * std_dev
                    current_lower = current_middle - 2 * std_dev
                else:
                    current_upper = close[-1] * 1.01
                    current_middle = close[-1]
                    current_lower = close[-1] * 0.99

            current_price = close[-1]
            
            # 计算价格在布林带中的位置
            bb_position = (current_price - current_lower) / (current_upper - current_lower) if current_upper != current_lower else 0.5
            
            # 生成信号
            if bb_position > 0.8:
                signal = 'overbought'
                strength = bb_position
            elif bb_position < 0.2:
                signal = 'oversold'
                strength = 1 - bb_position
            else:
                signal = 'neutral'
                strength = 0.5
            
            # 计算带宽
            bandwidth = (current_upper - current_lower) / current_middle if current_middle != 0 else 0
            
            return {
                'upper': current_upper,
                'middle': current_middle,
                'lower': current_lower,
                'position': bb_position,
                'bandwidth': bandwidth,
                'signal': signal,
                'strength': strength
            }
            
        except Exception as e:
            logger.error(f"布林带计算错误: {e}")
            return {'upper': 0, 'middle': 0, 'lower': 0, 'position': 0.5, 'bandwidth': 0, 'signal': 'neutral', 'strength': 0.5}
    
    def _calculate_kdj(self, high: np.ndarray, low: np.ndarray, close: np.ndarray) -> Dict:
        """计算KDJ指标"""
        try:
            # 确保数据类型为 double
            high_double = high.astype(np.float64)
            low_double = low.astype(np.float64)
            close_double = close.astype(np.float64)

            if TALIB_AVAILABLE:
                # 计算K值和D值
                k_values = talib.STOCHF(high_double, low_double, close_double, fastk_period=9, fastd_period=3, fastd_matype=0)[0]
                d_values = talib.STOCHF(high_double, low_double, close_double, fastk_period=9, fastd_period=3, fastd_matype=0)[1]
            else:
                # 简化实现
                k_values = np.array([50] * len(close))
                d_values = np.array([50] * len(close))
            
            # 计算J值
            j_values = 3 * k_values - 2 * d_values
            
            current_k = k_values[-1] if not np.isnan(k_values[-1]) else 50
            current_d = d_values[-1] if not np.isnan(d_values[-1]) else 50
            current_j = j_values[-1] if not np.isnan(j_values[-1]) else 50
            
            # 生成信号
            if current_k > current_d and current_k > 20:
                signal = 'bullish'
                strength = min((current_k - current_d) / 100, 1.0)
            elif current_k < current_d and current_k < 80:
                signal = 'bearish'
                strength = min((current_d - current_k) / 100, 1.0)
            else:
                signal = 'neutral'
                strength = 0.5
            
            return {
                'k': current_k,
                'd': current_d,
                'j': current_j,
                'signal': signal,
                'strength': strength
            }
            
        except Exception as e:
            logger.error(f"KDJ计算错误: {e}")
            return {'k': 50, 'd': 50, 'j': 50, 'signal': 'neutral', 'strength': 0.5}
    
    def _calculate_williams_r(self, high: np.ndarray, low: np.ndarray, close: np.ndarray) -> Dict:
        """计算威廉指标"""
        try:
            # 确保数据类型为 double
            high_double = high.astype(np.float64)
            low_double = low.astype(np.float64)
            close_double = close.astype(np.float64)

            if TALIB_AVAILABLE:
                williams = talib.WILLR(high_double, low_double, close_double, timeperiod=14)
                current_williams = williams[-1] if not np.isnan(williams[-1]) else -50
            else:
                # 简化实现
                current_williams = -50
            
            # 生成信号
            if current_williams > -20:
                signal = 'overbought'
                strength = (20 + current_williams) / 20
            elif current_williams < -80:
                signal = 'oversold'
                strength = (current_williams + 100) / 20
            else:
                signal = 'neutral'
                strength = 0.5
            
            return {
                'williams_r': current_williams,
                'signal': signal,
                'strength': strength
            }
            
        except Exception as e:
            logger.error(f"威廉指标计算错误: {e}")
            return {'williams_r': -50, 'signal': 'neutral', 'strength': 0.5}
    
    def _calculate_volume_indicators(self, close: np.ndarray, volume: np.ndarray) -> Dict:
        """计算成交量指标"""
        try:
            # 确保数组类型为 double
            close_double = close.astype(np.float64)
            volume_double = volume.astype(np.float64)

            if TALIB_AVAILABLE:
                # OBV (能量潮)
                obv = talib.OBV(close_double, volume_double)
                current_obv = obv[-1] if not np.isnan(obv[-1]) else 0

                # 成交量移动平均
                volume_ma = talib.SMA(volume_double, timeperiod=20)
                current_volume = volume_double[-1]
                current_volume_ma = volume_ma[-1] if not np.isnan(volume_ma[-1]) else current_volume
            else:
                # 简化实现
                current_obv = 0
                current_volume = volume_double[-1]
                window = min(20, len(volume_double))
                current_volume_ma = np.mean(volume_double[-window:]) if window > 0 else current_volume
            
            # 成交量比率
            volume_ratio = current_volume / current_volume_ma if current_volume_ma != 0 else 1
            
            # 生成信号
            if volume_ratio > 1.5:
                signal = 'high_volume'
                strength = min(volume_ratio / 2, 1.0)
            elif volume_ratio < 0.5:
                signal = 'low_volume'
                strength = 1 - volume_ratio
            else:
                signal = 'normal_volume'
                strength = 0.5
            
            return {
                'obv': current_obv,
                'volume_ratio': volume_ratio,
                'signal': signal,
                'strength': strength
            }
            
        except Exception as e:
            logger.error(f"成交量指标计算错误: {e}")
            return {'obv': 0, 'volume_ratio': 1, 'signal': 'normal_volume', 'strength': 0.5}
    
    def _calculate_ichimoku(self, high: np.ndarray, low: np.ndarray, close: np.ndarray) -> Dict:
        """计算一目均衡表"""
        try:
            # 转换线 (Tenkan-sen)
            tenkan_high = pd.Series(high).rolling(9).max()
            tenkan_low = pd.Series(low).rolling(9).min()
            tenkan = (tenkan_high + tenkan_low) / 2
            
            # 基准线 (Kijun-sen)
            kijun_high = pd.Series(high).rolling(26).max()
            kijun_low = pd.Series(low).rolling(26).min()
            kijun = (kijun_high + kijun_low) / 2
            
            current_price = close[-1]
            current_tenkan = tenkan.iloc[-1] if not pd.isna(tenkan.iloc[-1]) else current_price
            current_kijun = kijun.iloc[-1] if not pd.isna(kijun.iloc[-1]) else current_price
            
            # 生成信号
            if current_tenkan > current_kijun and current_price > current_tenkan:
                signal = 'bullish'
                strength = min((current_price - current_kijun) / current_kijun, 0.05) * 20
            elif current_tenkan < current_kijun and current_price < current_tenkan:
                signal = 'bearish'
                strength = min((current_kijun - current_price) / current_kijun, 0.05) * 20
            else:
                signal = 'neutral'
                strength = 0.5
            
            return {
                'tenkan': current_tenkan,
                'kijun': current_kijun,
                'signal': signal,
                'strength': strength
            }
            
        except Exception as e:
            logger.error(f"一目均衡表计算错误: {e}")
            return {'tenkan': 0, 'kijun': 0, 'signal': 'neutral', 'strength': 0.5}
    
    def _calculate_fibonacci_retracement(self, high: np.ndarray, low: np.ndarray, close: np.ndarray) -> Dict:
        """计算斐波那契回调"""
        try:
            # 获取最近的高点和低点
            recent_high = np.max(high[-20:])
            recent_low = np.min(low[-20:])
            current_price = close[-1]
            
            # 计算斐波那契水平
            diff = recent_high - recent_low
            fib_levels = {
                '0%': recent_high,
                '23.6%': recent_high - 0.236 * diff,
                '38.2%': recent_high - 0.382 * diff,
                '50%': recent_high - 0.5 * diff,
                '61.8%': recent_high - 0.618 * diff,
                '100%': recent_low
            }
            
            # 找到当前价格所在的斐波那契区间
            signal = 'neutral'
            strength = 0.5
            
            if current_price > fib_levels['23.6%']:
                signal = 'resistance_area'
                strength = 0.7
            elif current_price < fib_levels['61.8%']:
                signal = 'support_area'
                strength = 0.7
            
            return {
                'levels': fib_levels,
                'current_level': self._find_fib_level(current_price, fib_levels),
                'signal': signal,
                'strength': strength
            }
            
        except Exception as e:
            logger.error(f"斐波那契回调计算错误: {e}")
            return {'levels': {}, 'current_level': '50%', 'signal': 'neutral', 'strength': 0.5}
    
    def _calculate_pivot_points(self, high: np.ndarray, low: np.ndarray, close: np.ndarray) -> Dict:
        """计算枢轴点"""
        try:
            # 使用前一天的数据计算枢轴点
            prev_high = high[-2] if len(high) > 1 else high[-1]
            prev_low = low[-2] if len(low) > 1 else low[-1]
            prev_close = close[-2] if len(close) > 1 else close[-1]
            
            # 计算枢轴点
            pivot = (prev_high + prev_low + prev_close) / 3
            
            # 计算支撑和阻力位
            r1 = 2 * pivot - prev_low
            s1 = 2 * pivot - prev_high
            r2 = pivot + (prev_high - prev_low)
            s2 = pivot - (prev_high - prev_low)
            
            current_price = close[-1]
            
            # 生成信号
            if current_price > r1:
                signal = 'above_resistance'
                strength = 0.8
            elif current_price < s1:
                signal = 'below_support'
                strength = 0.8
            else:
                signal = 'between_levels'
                strength = 0.5
            
            return {
                'pivot': pivot,
                'r1': r1,
                'r2': r2,
                's1': s1,
                's2': s2,
                'signal': signal,
                'strength': strength
            }
            
        except Exception as e:
            logger.error(f"枢轴点计算错误: {e}")
            return {'pivot': 0, 'r1': 0, 'r2': 0, 's1': 0, 's2': 0, 'signal': 'neutral', 'strength': 0.5}
    
    def _calculate_atr(self, high: np.ndarray, low: np.ndarray, close: np.ndarray) -> Dict:
        """计算平均真实波幅"""
        try:
            # 确保数据类型为 double
            high_double = high.astype(np.float64)
            low_double = low.astype(np.float64)
            close_double = close.astype(np.float64)

            if TALIB_AVAILABLE:
                atr = talib.ATR(high_double, low_double, close_double, timeperiod=14)
                current_atr = atr[-1] if not np.isnan(atr[-1]) else 0
            else:
                # 简化实现：使用价格范围的标准差
                window = min(14, len(close))
                if window > 1:
                    price_range = high_double[-window:] - low_double[-window:]
                    current_atr = np.std(price_range)
                else:
                    current_atr = 0

            current_price = close_double[-1]
            
            # 计算ATR百分比
            atr_percentage = (current_atr / current_price) * 100 if current_price != 0 else 0
            
            # 生成信号
            if atr_percentage > 0.5:
                signal = 'high_volatility'
                strength = min(atr_percentage / 1.0, 1.0)
            elif atr_percentage < 0.1:
                signal = 'low_volatility'
                strength = 1 - (atr_percentage / 0.1)
            else:
                signal = 'normal_volatility'
                strength = 0.5
            
            return {
                'atr': current_atr,
                'atr_percentage': atr_percentage,
                'signal': signal,
                'strength': strength
            }
            
        except Exception as e:
            logger.error(f"ATR计算错误: {e}")
            return {'atr': 0, 'atr_percentage': 0, 'signal': 'normal_volatility', 'strength': 0.5}
    
    def _calculate_composite_signal(self, indicators: Dict) -> Dict:
        """计算综合信号"""
        try:
            bullish_signals = 0
            bearish_signals = 0
            total_strength = 0
            
            for indicator_name, indicator_data in indicators.items():
                if isinstance(indicator_data, dict) and 'signal' in indicator_data:
                    signal = indicator_data['signal']
                    strength = indicator_data.get('strength', 0.5)
                    weight = self.weights.get(indicator_name, 0.1)

                    # 确保 signal 是字符串类型
                    signal_str = str(signal) if signal is not None else 'neutral'

                    if 'bullish' in signal_str or 'oversold' in signal_str or 'support' in signal_str:
                        bullish_signals += weight * strength
                    elif 'bearish' in signal_str or 'overbought' in signal_str or 'resistance' in signal_str:
                        bearish_signals += weight * strength

                    total_strength += weight * strength
            
            # 计算综合信号
            net_signal = bullish_signals - bearish_signals
            confidence = total_strength / sum(self.weights.values()) if sum(self.weights.values()) > 0 else 0.5
            
            if net_signal > 0.1:
                composite_signal = 'bullish'
            elif net_signal < -0.1:
                composite_signal = 'bearish'
            else:
                composite_signal = 'neutral'
            
            return {
                'signal': composite_signal,
                'strength': abs(net_signal),
                'confidence': confidence,
                'bullish_score': bullish_signals,
                'bearish_score': bearish_signals
            }
            
        except Exception as e:
            logger.error(f"综合信号计算错误: {e}")
            return {'signal': 'neutral', 'strength': 0.5, 'confidence': 0.5, 'bullish_score': 0, 'bearish_score': 0}
    
    def _find_fib_level(self, price: float, levels: Dict) -> str:
        """找到价格对应的斐波那契水平"""
        min_diff = float('inf')
        closest_level = '50%'
        
        for level_name, level_price in levels.items():
            diff = abs(price - level_price)
            if diff < min_diff:
                min_diff = diff
                closest_level = level_name
        
        return closest_level
    
    def _get_default_indicators(self) -> Dict:
        """获取默认指标值"""
        return {
            'macd': {'macd': 0, 'signal': 0, 'histogram': 0, 'trend_signal': 'neutral', 'strength': 0.5},
            'bollinger': {'upper': 0, 'middle': 0, 'lower': 0, 'position': 0.5, 'bandwidth': 0, 'signal': 'neutral', 'strength': 0.5},
            'kdj': {'k': 50, 'd': 50, 'j': 50, 'signal': 'neutral', 'strength': 0.5},
            'williams': {'williams_r': -50, 'signal': 'neutral', 'strength': 0.5},
            'volume': {'obv': 0, 'volume_ratio': 1, 'signal': 'normal_volume', 'strength': 0.5},
            'ichimoku': {'tenkan': 0, 'kijun': 0, 'signal': 'neutral', 'strength': 0.5},
            'fibonacci': {'levels': {}, 'current_level': '50%', 'signal': 'neutral', 'strength': 0.5},
            'pivot': {'pivot': 0, 'r1': 0, 'r2': 0, 's1': 0, 's2': 0, 'signal': 'neutral', 'strength': 0.5},
            'atr': {'atr': 0, 'atr_percentage': 0, 'signal': 'normal_volatility', 'strength': 0.5},
            'composite_signal': {'signal': 'neutral', 'strength': 0.5, 'confidence': 0.5, 'bullish_score': 0, 'bearish_score': 0}
        }
    
    def get_prediction_signal(self, indicators: Dict = None) -> Dict:
        """获取预测信号"""
        if indicators is None:
            indicators = self.indicators
        
        if not indicators or 'composite_signal' not in indicators:
            return {'signal': 'neutral', 'confidence': 0.5, 'strength': 0.5}
        
        composite = indicators['composite_signal']
        return {
            'signal': composite['signal'],
            'confidence': composite['confidence'],
            'strength': composite['strength'],
            'details': {
                'bullish_score': composite['bullish_score'],
                'bearish_score': composite['bearish_score'],
                'contributing_indicators': self._get_contributing_indicators(indicators)
            }
        }
    
    def _get_contributing_indicators(self, indicators: Dict) -> List[str]:
        """获取贡献指标列表"""
        contributing = []
        
        for name, data in indicators.items():
            if isinstance(data, dict) and 'signal' in data and data['signal'] != 'neutral':
                contributing.append(f"{name}: {data['signal']}")
        
        return contributing


def main():
    """测试函数"""
    print("高级技术指标模块测试")
    print("=" * 40)
    
    # 创建测试数据
    np.random.seed(42)
    n_points = 100
    base_price = 3400
    
    # 生成模拟价格数据
    price_changes = np.random.normal(0, 5, n_points)
    prices = [base_price]
    for change in price_changes:
        prices.append(prices[-1] + change)
    
    # 创建DataFrame
    df = pd.DataFrame({
        'price': prices[1:],
        'bid': [p - 0.05 for p in prices[1:]],
        'ask': [p + 0.05 for p in prices[1:]],
        'volume': np.random.randint(1000, 5000, n_points)
    })
    
    # 测试技术指标
    indicators = AdvancedTechnicalIndicators()
    
    try:
        # 计算所有指标
        results = indicators.calculate_all_indicators(df)
        
        print("✅ 技术指标计算成功")
        print(f"计算指标数量: {len(results)}")
        
        # 显示综合信号
        composite = results.get('composite_signal', {})
        print(f"\n📊 综合信号:")
        print(f"   信号: {composite.get('signal', 'unknown')}")
        print(f"   强度: {composite.get('strength', 0):.2f}")
        print(f"   置信度: {composite.get('confidence', 0):.2f}")
        
        # 显示主要指标
        print(f"\n📈 主要指标:")
        for name in ['macd', 'bollinger', 'kdj']:
            if name in results:
                indicator = results[name]
                print(f"   {name.upper()}: {indicator.get('signal', 'unknown')} (强度: {indicator.get('strength', 0):.2f})")
        
        # 获取预测信号
        prediction = indicators.get_prediction_signal(results)
        print(f"\n🔮 预测信号:")
        print(f"   信号: {prediction['signal']}")
        print(f"   置信度: {prediction['confidence']:.2f}")
        print(f"   强度: {prediction['strength']:.2f}")
        
        print("\n✅ 高级技术指标测试完成!")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")


if __name__ == "__main__":
    main()
