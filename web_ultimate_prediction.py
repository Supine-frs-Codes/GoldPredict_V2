#!/usr/bin/env python3
"""
Web专用的终极预测脚本
确保在Web环境中稳定运行
"""

import numpy as np
import pandas as pd
from pathlib import Path
import logging
import json
from datetime import datetime, timedelta
import warnings
import sys
import os

# 设置编码
if sys.platform.startswith('win'):
    os.environ['PYTHONIOENCODING'] = 'utf-8'

warnings.filterwarnings('ignore')

from src.data.data_collector import GoldDataCollector
from src.data.data_preprocessor import GoldDataPreprocessor
from src.visualization.charts import GoldPriceVisualizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebUltimatePredictor:
    """Web专用终极预测器"""
    
    def __init__(self):
        logger.info("[系统] Web终极预测器初始化")
        
        # 初始化组件
        self.data_collector = GoldDataCollector()
        self.preprocessor = GoldDataPreprocessor()
        self.visualizer = GoldPriceVisualizer()
        
        # 配置
        self.config = {
            'data_period': '6mo',
            'prediction_horizons': [1, 5, 10, 30],
            'use_advanced_analysis': True,
            'create_interactive_charts': True
        }
        
    def collect_and_analyze_data(self):
        """数据收集和分析"""
        print("[数据] 开始收集黄金价格数据...")
        
        try:
            # 获取数据
            data = self.data_collector.combine_data_sources(
                use_yahoo=True, period=self.config['data_period']
            )
            
            if data.empty:
                raise ValueError("无法获取数据")
            
            print(f"[成功] 获取到 {len(data)} 条数据记录")
            print(f"   时间范围: {data['date'].min()} 到 {data['date'].max()}")
            print(f"   当前价格: ${data['close'].iloc[-1]:.2f}")
            
            return data
            
        except Exception as e:
            print(f"[错误] 数据收集失败: {e}")
            raise
    
    def advanced_technical_analysis(self, data):
        """高级技术分析"""
        print("[分析] 进行高级技术分析...")
        
        # 计算技术指标
        data = data.copy()
        
        # 移动平均线
        data['ma_5'] = data['close'].rolling(5).mean()
        data['ma_10'] = data['close'].rolling(10).mean()
        data['ma_20'] = data['close'].rolling(20).mean()
        data['ma_50'] = data['close'].rolling(50).mean()
        
        # 指数移动平均
        data['ema_12'] = data['close'].ewm(span=12).mean()
        data['ema_26'] = data['close'].ewm(span=26).mean()
        
        # MACD
        data['macd'] = data['ema_12'] - data['ema_26']
        data['macd_signal'] = data['macd'].ewm(span=9).mean()
        data['macd_histogram'] = data['macd'] - data['macd_signal']
        
        # RSI
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['rsi'] = 100 - (100 / (1 + rs))
        
        # 布林带
        data['bb_middle'] = data['close'].rolling(20).mean()
        bb_std = data['close'].rolling(20).std()
        data['bb_upper'] = data['bb_middle'] + (bb_std * 2)
        data['bb_lower'] = data['bb_middle'] - (bb_std * 2)
        
        # 波动率
        data['volatility'] = data['close'].pct_change().rolling(20).std()
        
        # 价格动量
        data['momentum_5'] = data['close'] / data['close'].shift(5) - 1
        data['momentum_10'] = data['close'] / data['close'].shift(10) - 1
        
        print("[成功] 技术分析完成")
        return data
    
    def ensemble_prediction(self, data):
        """集成预测"""
        print("[预测] 使用高级集成方法进行预测...")
        
        current_price = data['close'].iloc[-1]
        predictions = {}
        
        for horizon in self.config['prediction_horizons']:
            # 方法1: 趋势分析
            trend_pred = self._trend_analysis_prediction(data, horizon)
            
            # 方法2: 技术指标
            technical_pred = self._technical_indicator_prediction(data, horizon)
            
            # 方法3: 动量分析
            momentum_pred = self._momentum_prediction(data, horizon)
            
            # 方法4: 波动率模型
            volatility_pred = self._volatility_model_prediction(data, horizon)
            
            # 方法5: 均值回归
            mean_reversion_pred = self._mean_reversion_prediction(data, horizon)
            
            # 集成预测（智能加权）
            weights = self._calculate_dynamic_weights(data, horizon)
            
            ensemble_pred = (
                weights[0] * trend_pred +
                weights[1] * technical_pred +
                weights[2] * momentum_pred +
                weights[3] * volatility_pred +
                weights[4] * mean_reversion_pred
            )
            
            # 计算置信区间
            pred_methods = [trend_pred, technical_pred, momentum_pred, volatility_pred, mean_reversion_pred]
            pred_std = np.std(pred_methods)
            confidence_lower = ensemble_pred - 1.96 * pred_std
            confidence_upper = ensemble_pred + 1.96 * pred_std
            
            # 计算变化
            price_change = ensemble_pred - current_price
            price_change_pct = (price_change / current_price) * 100
            
            # 趋势判断
            if price_change_pct > 1:
                trend = "强烈看涨"
            elif price_change_pct > 0.5:
                trend = "看涨"
            elif price_change_pct > -0.5:
                trend = "横盘整理"
            elif price_change_pct > -1:
                trend = "看跌"
            else:
                trend = "强烈看跌"
            
            predictions[f'{horizon}_day'] = {
                'horizon_days': horizon,
                'current_price': float(current_price),
                'predicted_price': float(ensemble_pred),
                'price_change': float(price_change),
                'price_change_pct': float(price_change_pct),
                'confidence_lower': float(confidence_lower),
                'confidence_upper': float(confidence_upper),
                'confidence_interval': f"${confidence_lower:.2f} - ${confidence_upper:.2f}",
                'trend_signal': trend,
                'prediction_date': (datetime.now() + timedelta(days=horizon)).isoformat(),
                'methods': {
                    'trend_analysis': float(trend_pred),
                    'technical_indicators': float(technical_pred),
                    'momentum_analysis': float(momentum_pred),
                    'volatility_model': float(volatility_pred),
                    'mean_reversion': float(mean_reversion_pred)
                },
                'weights': {
                    'trend': float(weights[0]),
                    'technical': float(weights[1]),
                    'momentum': float(weights[2]),
                    'volatility': float(weights[3]),
                    'mean_reversion': float(weights[4])
                }
            }
            
            print(f"   {horizon}天预测: ${ensemble_pred:.2f} ({price_change_pct:+.2f}%) - {trend}")
        
        return predictions
    
    def _trend_analysis_prediction(self, data, horizon):
        """趋势分析预测"""
        # 多时间框架趋势分析
        short_trend = (data['ma_5'].iloc[-1] - data['ma_20'].iloc[-1]) / data['ma_20'].iloc[-1]
        long_trend = (data['ma_20'].iloc[-1] - data['ma_50'].iloc[-1]) / data['ma_50'].iloc[-1]
        
        # 趋势强度
        trend_strength = (short_trend + long_trend) / 2
        
        # 预测
        current_price = data['close'].iloc[-1]
        return current_price * (1 + trend_strength * horizon * 0.1)
    
    def _technical_indicator_prediction(self, data, horizon):
        """技术指标预测"""
        current_price = data['close'].iloc[-1]
        
        # RSI信号
        rsi = data['rsi'].iloc[-1]
        rsi_signal = (50 - rsi) / 100  # 标准化RSI信号
        
        # MACD信号
        macd_signal = data['macd_histogram'].iloc[-1] / current_price
        
        # 布林带信号
        bb_position = (current_price - data['bb_lower'].iloc[-1]) / (data['bb_upper'].iloc[-1] - data['bb_lower'].iloc[-1])
        bb_signal = (0.5 - bb_position) * 0.1
        
        # 综合信号
        total_signal = (rsi_signal + macd_signal + bb_signal) / 3
        
        return current_price * (1 + total_signal * horizon * 0.2)
    
    def _momentum_prediction(self, data, horizon):
        """动量预测"""
        momentum_5 = data['momentum_5'].iloc[-1]
        momentum_10 = data['momentum_10'].iloc[-1]
        
        # 加权动量
        weighted_momentum = 0.6 * momentum_5 + 0.4 * momentum_10
        
        current_price = data['close'].iloc[-1]
        return current_price * (1 + weighted_momentum * horizon * 0.15)
    
    def _volatility_model_prediction(self, data, horizon):
        """波动率模型预测"""
        returns = data['close'].pct_change().dropna()
        mean_return = returns.mean()
        volatility = returns.std()
        
        # 考虑时间衰减的预测
        predicted_return = mean_return * horizon - volatility * np.sqrt(horizon) * 0.1
        
        current_price = data['close'].iloc[-1]
        return current_price * (1 + predicted_return)
    
    def _mean_reversion_prediction(self, data, horizon):
        """均值回归预测 - 修复过度悲观问题"""
        current_price = data['close'].iloc[-1]
        long_term_mean = data['close'].rolling(50).mean().iloc[-1]  # 使用较短期均值

        # 偏离程度
        deviation = (current_price - long_term_mean) / long_term_mean

        # 减弱均值回归强度，避免过度悲观
        reversion_strength = min(horizon / 60, 0.5) * 0.1  # 大幅减少回归强度

        # 限制回归影响
        reversion_effect = max(-0.05, min(0.05, -deviation * reversion_strength))  # 限制在±5%

        return current_price * (1 + reversion_effect)
    
    def _calculate_dynamic_weights(self, data, horizon):
        """计算动态权重"""
        # 基于市场状态调整权重
        volatility = data['volatility'].iloc[-1]
        
        if volatility > 0.02:  # 高波动市场
            weights = [0.2, 0.35, 0.25, 0.15, 0.05]  # 更重视技术指标和动量，减少均值回归
        elif volatility < 0.01:  # 低波动市场
            weights = [0.35, 0.25, 0.2, 0.15, 0.05]  # 更重视趋势，减少均值回归
        else:  # 正常市场
            weights = [0.3, 0.3, 0.25, 0.1, 0.05]  # 大幅减少均值回归权重

        # 根据预测时间调整 - 减少长期预测的均值回归影响
        if horizon > 20:  # 长期预测
            weights[4] += 0.05  # 轻微增加均值回归权重
            weights[0] -= 0.05  # 轻微减少趋势权重
        
        return weights
    
    def create_visualizations(self, data, predictions):
        """创建可视化"""
        print("[图表] 创建高级可视化图表...")
        
        visualization_files = []
        
        try:
            # 1. 交互式预测图表
            fig1 = self.visualizer.plot_interactive_multi_predictions(data, predictions)
            path1 = Path("results/visualizations/web_ultimate_interactive.html")
            path1.parent.mkdir(parents=True, exist_ok=True)
            fig1.write_html(str(path1))
            visualization_files.append(str(path1))
            print(f"   交互式预测图: {path1}")
            
            # 2. 技术指标图表
            fig2 = self.visualizer.plot_technical_indicators(data)
            path2 = Path("results/visualizations/web_ultimate_technical.html")
            fig2.write_html(str(path2))
            visualization_files.append(str(path2))
            print(f"   技术指标图: {path2}")
            
            # 3. 价格历史图表
            fig3 = self.visualizer.plot_price_history(data)
            path3 = Path("results/visualizations/web_ultimate_history.html")
            fig3.write_html(str(path3))
            visualization_files.append(str(path3))
            print(f"   价格历史图: {path3}")
            
        except Exception as e:
            print(f"[警告] 可视化创建部分失败: {e}")
        
        return visualization_files
    
    def run_ultimate_prediction(self):
        """运行终极预测"""
        print("[启动] Web终极预测系统")
        print("=" * 50)
        
        start_time = datetime.now()
        
        try:
            # 1. 数据收集
            data = self.collect_and_analyze_data()
            
            # 2. 技术分析
            analyzed_data = self.advanced_technical_analysis(data)
            
            # 3. 集成预测
            predictions = self.ensemble_prediction(analyzed_data)
            
            # 4. 创建可视化
            visualization_files = self.create_visualizations(analyzed_data, predictions)
            
            # 5. 保存结果
            end_time = datetime.now()
            total_time = (end_time - start_time).total_seconds()
            
            # 保存预测结果
            pred_path = Path("results/predictions/web_ultimate_predictions.json")
            pred_path.parent.mkdir(parents=True, exist_ok=True)
            
            result = {
                'timestamp': datetime.now().isoformat(),
                'model_type': 'web_ultimate_ensemble',
                'predictions': predictions,
                'data_summary': {
                    'total_points': len(data),
                    'current_price': float(data['close'].iloc[-1]),
                    'data_period': self.config['data_period'],
                    'price_range': {
                        'min': float(data['close'].min()),
                        'max': float(data['close'].max()),
                        'mean': float(data['close'].mean())
                    }
                },
                'execution_info': {
                    'total_time_seconds': total_time,
                    'visualization_files': visualization_files
                }
            }
            
            with open(pred_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            print("=" * 50)
            print("[完成] Web终极预测系统运行完成!")
            print(f"   总耗时: {total_time:.2f}秒")
            print(f"   预测结果: {len(predictions)} 个时间跨度")
            print(f"   可视化文件: {len(visualization_files)} 个")
            print(f"   结果文件: {pred_path}")
            
            return True
            
        except Exception as e:
            print(f"[错误] 终极预测失败: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Web终极预测系统')
    parser.add_argument('--mode', type=str, default='ultimate', help='预测模式')
    
    args = parser.parse_args()
    
    print(f"[预测] Web终极预测系统 - {args.mode}模式")
    print("=" * 40)
    
    try:
        predictor = WebUltimatePredictor()
        success = predictor.run_ultimate_prediction()
        
        if success:
            print("\n[完成] 预测完成!")
        else:
            print("\n[错误] 预测失败!")
            
    except Exception as e:
        print(f"[错误] 执行失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 确保正确退出
    import sys
    sys.exit(0)


if __name__ == "__main__":
    main()
