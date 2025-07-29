#!/usr/bin/env python3
"""
轻量级终极预测系统
针对资源受限环境优化的预测功能
"""

import numpy as np
import pandas as pd
from pathlib import Path
import logging
import json
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

from src.data.data_collector import GoldDataCollector
from src.data.data_preprocessor import GoldDataPreprocessor
from src.visualization.charts import GoldPriceVisualizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LightweightPredictor:
    """轻量级预测器"""
    
    def __init__(self, config: dict = None):
        self.config = config or self._get_default_config()
        
        logger.info(f"[系统] 轻量级预测器初始化")
        
        # 初始化组件
        self.data_collector = GoldDataCollector()
        self.preprocessor = GoldDataPreprocessor()
        self.visualizer = GoldPriceVisualizer()
        
        # 结果存储
        self.results = {}
        
    def _get_default_config(self) -> dict:
        """获取轻量级默认配置"""
        return {
            # 数据配置
            'data_period': '6mo',  # 6个月历史数据
            'sequence_length': 20,  # 短序列长度
            'prediction_horizons': [1, 5, 10, 30],
            
            # 模型配置（轻量级）
            'use_ensemble': True,
            'use_technical_analysis': True,
            'use_statistical_models': True,
            
            # 输出配置
            'save_predictions': True,
            'create_visualizations': True
        }
    
    def advanced_technical_analysis(self, data: pd.DataFrame) -> dict:
        """高级技术分析"""
        logger.info("[分析] 进行高级技术分析...")
        
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
        
        # 成交量指标
        if 'volume' in data.columns:
            data['volume_ma'] = data['volume'].rolling(20).mean()
            data['volume_ratio'] = data['volume'] / data['volume_ma']
        
        # 价格动量
        data['momentum_5'] = data['close'] / data['close'].shift(5) - 1
        data['momentum_10'] = data['close'] / data['close'].shift(10) - 1
        
        return data
    
    def ensemble_prediction(self, data: pd.DataFrame) -> dict:
        """集成预测方法"""
        logger.info("[预测] 使用集成方法进行预测...")
        
        current_price = data['close'].iloc[-1]
        predictions = {}
        
        for horizon in self.config['prediction_horizons']:
            # 方法1: 移动平均趋势
            ma_trend = self._moving_average_prediction(data, horizon)
            
            # 方法2: 动量分析
            momentum_pred = self._momentum_prediction(data, horizon)
            
            # 方法3: 技术指标综合
            technical_pred = self._technical_indicator_prediction(data, horizon)
            
            # 方法4: 统计回归
            regression_pred = self._regression_prediction(data, horizon)
            
            # 方法5: 波动率调整
            volatility_pred = self._volatility_adjusted_prediction(data, horizon)
            
            # 集成预测（加权平均）
            weights = [0.25, 0.2, 0.25, 0.15, 0.15]  # 权重
            ensemble_pred = (
                weights[0] * ma_trend +
                weights[1] * momentum_pred +
                weights[2] * technical_pred +
                weights[3] * regression_pred +
                weights[4] * volatility_pred
            )
            
            # 计算置信区间
            pred_std = np.std([ma_trend, momentum_pred, technical_pred, regression_pred, volatility_pred])
            confidence_lower = ensemble_pred - 1.96 * pred_std
            confidence_upper = ensemble_pred + 1.96 * pred_std
            
            # 计算变化
            price_change = ensemble_pred - current_price
            price_change_pct = (price_change / current_price) * 100
            
            predictions[f'{horizon}_day'] = {
                'horizon_days': horizon,
                'current_price': float(current_price),
                'predicted_price': float(ensemble_pred),
                'price_change': float(price_change),
                'price_change_pct': float(price_change_pct),
                'confidence_lower': float(confidence_lower),
                'confidence_upper': float(confidence_upper),
                'confidence_interval': f"${confidence_lower:.2f} - ${confidence_upper:.2f}",
                'prediction_date': (datetime.now() + timedelta(days=horizon)).isoformat(),
                'methods': {
                    'moving_average': float(ma_trend),
                    'momentum': float(momentum_pred),
                    'technical': float(technical_pred),
                    'regression': float(regression_pred),
                    'volatility': float(volatility_pred)
                }
            }
            
            logger.info(f"   {horizon}天预测: ${ensemble_pred:.2f} ({price_change_pct:+.2f}%)")
        
        return predictions
    
    def _moving_average_prediction(self, data: pd.DataFrame, horizon: int) -> float:
        """移动平均预测"""
        # 使用多个时间窗口的移动平均
        ma_5 = data['close'].rolling(5).mean().iloc[-1]
        ma_10 = data['close'].rolling(10).mean().iloc[-1]
        ma_20 = data['close'].rolling(20).mean().iloc[-1]
        
        # 趋势强度
        trend_strength = (ma_5 - ma_20) / ma_20
        
        # 基于趋势的预测
        current_price = data['close'].iloc[-1]
        predicted_price = current_price * (1 + trend_strength * horizon * 0.1)
        
        return predicted_price
    
    def _momentum_prediction(self, data: pd.DataFrame, horizon: int) -> float:
        """动量预测"""
        # 计算不同时间窗口的动量
        momentum_5 = data['close'].iloc[-1] / data['close'].iloc[-6] - 1
        momentum_10 = data['close'].iloc[-1] / data['close'].iloc[-11] - 1
        
        # 加权动量
        weighted_momentum = 0.6 * momentum_5 + 0.4 * momentum_10
        
        # 预测
        current_price = data['close'].iloc[-1]
        predicted_price = current_price * (1 + weighted_momentum * horizon * 0.2)
        
        return predicted_price
    
    def _technical_indicator_prediction(self, data: pd.DataFrame, horizon: int) -> float:
        """技术指标预测"""
        current_price = data['close'].iloc[-1]
        
        # RSI信号
        rsi = data['rsi'].iloc[-1]
        if rsi > 70:
            rsi_signal = -0.1  # 超买
        elif rsi < 30:
            rsi_signal = 0.1   # 超卖
        else:
            rsi_signal = 0
        
        # MACD信号
        macd = data['macd'].iloc[-1]
        macd_signal = data['macd_signal'].iloc[-1]
        macd_trend = 0.05 if macd > macd_signal else -0.05
        
        # 布林带信号
        bb_upper = data['bb_upper'].iloc[-1]
        bb_lower = data['bb_lower'].iloc[-1]
        bb_middle = data['bb_middle'].iloc[-1]
        
        if current_price > bb_upper:
            bb_signal = -0.05  # 价格过高
        elif current_price < bb_lower:
            bb_signal = 0.05   # 价格过低
        else:
            bb_signal = (current_price - bb_middle) / bb_middle * 0.1
        
        # 综合信号
        total_signal = (rsi_signal + macd_trend + bb_signal) / 3
        
        # 预测
        predicted_price = current_price * (1 + total_signal * horizon * 0.3)
        
        return predicted_price
    
    def _regression_prediction(self, data: pd.DataFrame, horizon: int) -> float:
        """简单线性回归预测"""
        # 使用最近20天的数据进行线性回归
        recent_data = data['close'].tail(20).values
        x = np.arange(len(recent_data))
        
        # 线性回归
        coeffs = np.polyfit(x, recent_data, 1)
        slope = coeffs[0]
        
        # 预测
        current_price = data['close'].iloc[-1]
        predicted_price = current_price + slope * horizon
        
        return predicted_price
    
    def _volatility_adjusted_prediction(self, data: pd.DataFrame, horizon: int) -> float:
        """波动率调整预测"""
        current_price = data['close'].iloc[-1]
        
        # 计算历史波动率
        returns = data['close'].pct_change().dropna()
        volatility = returns.std()
        
        # 计算趋势
        trend = returns.mean()
        
        # 波动率调整的预测
        predicted_return = trend * horizon - volatility * np.sqrt(horizon) * 0.1
        predicted_price = current_price * (1 + predicted_return)
        
        return predicted_price
    
    def run_lightweight_prediction(self) -> dict:
        """运行轻量级预测流程"""
        logger.info("[启动] 轻量级终极预测系统")
        logger.info("=" * 60)
        
        start_time = datetime.now()
        
        try:
            # 1. 数据收集
            logger.info("[步骤1] 数据收集...")
            data = self.data_collector.combine_data_sources(
                use_yahoo=True, period=self.config['data_period']
            )
            logger.info(f"   获取 {len(data)} 条数据")
            
            # 2. 高级技术分析
            logger.info("[步骤2] 高级技术分析...")
            analyzed_data = self.advanced_technical_analysis(data)
            
            # 3. 集成预测
            logger.info("[步骤3] 集成预测...")
            predictions = self.ensemble_prediction(analyzed_data)
            
            # 4. 创建可视化
            logger.info("[步骤4] 创建可视化...")
            visualization_files = []
            
            # 价格历史图
            fig1 = self.visualizer.plot_price_history(data)
            path1 = Path("results/visualizations/lightweight_price_history.html")
            path1.parent.mkdir(parents=True, exist_ok=True)
            fig1.write_html(str(path1))
            visualization_files.append(str(path1))
            
            # 交互式预测图
            fig2 = self.visualizer.plot_interactive_multi_predictions(data, predictions)
            path2 = Path("results/visualizations/lightweight_interactive_predictions.html")
            fig2.write_html(str(path2))
            visualization_files.append(str(path2))
            
            # 技术指标图
            fig3 = self.visualizer.plot_technical_indicators(analyzed_data)
            path3 = Path("results/visualizations/lightweight_technical_indicators.html")
            fig3.write_html(str(path3))
            visualization_files.append(str(path3))
            
            # 5. 保存结果
            end_time = datetime.now()
            total_time = (end_time - start_time).total_seconds()
            
            # 保存预测结果
            if self.config['save_predictions']:
                pred_path = Path("results/predictions/lightweight_predictions.json")
                pred_path.parent.mkdir(parents=True, exist_ok=True)
                
                result = {
                    'timestamp': datetime.now().isoformat(),
                    'model_type': 'lightweight_ensemble',
                    'predictions': predictions,
                    'config': self.config,
                    'total_time_seconds': total_time,
                    'data_summary': {
                        'total_points': len(data),
                        'current_price': float(data['close'].iloc[-1]),
                        'price_range': {
                            'min': float(data['close'].min()),
                            'max': float(data['close'].max()),
                            'mean': float(data['close'].mean())
                        }
                    }
                }
                
                with open(pred_path, 'w') as f:
                    json.dump(result, f, indent=2)
            
            # 生成总结
            summary = {
                'status': 'success',
                'total_time_seconds': total_time,
                'data_points': len(data),
                'model_type': 'lightweight_ensemble',
                'predictions': predictions,
                'visualization_files': visualization_files
            }
            
            logger.info("=" * 60)
            logger.info("[完成] 轻量级预测系统运行完成!")
            logger.info(f"   总耗时: {total_time:.2f}秒")
            logger.info(f"   预测结果: {len(predictions)} 个时间跨度")
            logger.info(f"   可视化文件: {len(visualization_files)} 个")
            
            return summary
            
        except Exception as e:
            logger.error(f"[错误] 轻量级预测失败: {e}")
            raise


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='轻量级终极预测系统')
    parser.add_argument('--period', type=str, default='6mo', help='数据时间范围')
    parser.add_argument('--sequence-length', type=int, default=20, help='序列长度')
    
    args = parser.parse_args()
    
    # 配置
    config = {
        'data_period': args.period,
        'sequence_length': args.sequence_length,
        'prediction_horizons': [1, 5, 10, 30],
        'save_predictions': True,
        'create_visualizations': True
    }
    
    # 运行预测系统
    predictor = LightweightPredictor(config)
    results = predictor.run_lightweight_prediction()
    
    print(f"\n[完成] 轻量级预测系统运行完成!")
    print(f"查看结果: {results.get('visualization_files', [])}")


if __name__ == "__main__":
    main()
