#!/usr/bin/env python3
"""
简单预测系统修复版本
参考原始版本，生成可视化HTML文件展示预测结果
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import logging

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

logger = logging.getLogger(__name__)

class SimplePredictionSystemFixed:
    """简单预测系统修复版"""
    
    def __init__(self):
        """初始化系统"""
        self.results_dir = Path("results/simple_prediction")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # 预测历史
        self.prediction_history = []
        
    def generate_mock_data(self, days=30):
        """生成模拟数据"""
        try:
            logger.info(f"生成 {days} 天的模拟黄金价格数据...")
            
            # 生成时间序列
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)
            time_index = pd.date_range(start=start_time, end=end_time, freq='H')
            
            # 生成价格数据
            np.random.seed(42)
            base_price = 3300
            
            # 趋势组件
            trend = np.linspace(0, 50, len(time_index))
            
            # 季节性组件
            seasonal = 20 * np.sin(2 * np.pi * np.arange(len(time_index)) / (24 * 7))
            
            # 随机噪声
            noise = np.random.normal(0, 10, len(time_index))
            
            # 组合价格
            prices = base_price + trend + seasonal + noise
            
            # 创建OHLCV数据
            data = []
            for i, (timestamp, price) in enumerate(zip(time_index, prices)):
                open_price = price + np.random.normal(0, 2)
                high_price = price + abs(np.random.normal(5, 3))
                low_price = price - abs(np.random.normal(5, 3))
                close_price = price
                volume = np.random.randint(1000, 10000)
                
                data.append({
                    'timestamp': timestamp,
                    'open': open_price,
                    'high': high_price,
                    'low': low_price,
                    'close': close_price,
                    'volume': volume
                })
            
            df = pd.DataFrame(data)
            logger.info(f"生成了 {len(df)} 条数据记录")
            return df
            
        except Exception as e:
            logger.error(f"数据生成失败: {e}")
            return None
    
    def calculate_technical_indicators(self, data):
        """计算技术指标"""
        try:
            df = data.copy()
            
            # 移动平均线
            df['sma_5'] = df['close'].rolling(window=5).mean()
            df['sma_20'] = df['close'].rolling(window=20).mean()
            df['sma_50'] = df['close'].rolling(window=50).mean()
            
            # 指数移动平均线
            df['ema_12'] = df['close'].ewm(span=12).mean()
            df['ema_26'] = df['close'].ewm(span=26).mean()
            
            # MACD
            df['macd'] = df['ema_12'] - df['ema_26']
            df['macd_signal'] = df['macd'].ewm(span=9).mean()
            df['macd_histogram'] = df['macd'] - df['macd_signal']
            
            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # 布林带
            df['bb_middle'] = df['close'].rolling(window=20).mean()
            bb_std = df['close'].rolling(window=20).std()
            df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
            df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
            
            # 成交量移动平均
            df['volume_sma'] = df['volume'].rolling(window=20).mean()
            
            return df
            
        except Exception as e:
            logger.error(f"技术指标计算失败: {e}")
            return data
    
    def make_simple_prediction(self, data):
        """进行简单预测"""
        try:
            logger.info("开始进行简单预测...")
            
            # 获取最新数据
            latest = data.iloc[-1]
            current_price = latest['close']
            
            # 简单的技术分析预测
            sma_5 = latest['sma_5']
            sma_20 = latest['sma_20']
            rsi = latest['rsi']
            macd = latest['macd']
            macd_signal = latest['macd_signal']
            
            # 预测逻辑
            signals = []
            
            # 移动平均线信号
            if sma_5 > sma_20:
                signals.append(1)  # 看涨
            else:
                signals.append(-1)  # 看跌
            
            # RSI信号
            if rsi < 30:
                signals.append(1)  # 超卖，看涨
            elif rsi > 70:
                signals.append(-1)  # 超买，看跌
            else:
                signals.append(0)  # 中性
            
            # MACD信号
            if macd > macd_signal:
                signals.append(1)  # 看涨
            else:
                signals.append(-1)  # 看跌
            
            # 综合信号
            total_signal = sum(signals)
            
            # 预测价格变化
            if total_signal > 1:
                price_change_pct = np.random.uniform(0.5, 2.0)
                signal_text = "强烈看涨"
            elif total_signal > 0:
                price_change_pct = np.random.uniform(0.1, 0.8)
                signal_text = "看涨"
            elif total_signal == 0:
                price_change_pct = np.random.uniform(-0.3, 0.3)
                signal_text = "中性"
            elif total_signal > -2:
                price_change_pct = np.random.uniform(-0.8, -0.1)
                signal_text = "看跌"
            else:
                price_change_pct = np.random.uniform(-2.0, -0.5)
                signal_text = "强烈看跌"
            
            # 计算预测价格
            predicted_price = current_price * (1 + price_change_pct / 100)
            
            # 计算置信度
            confidence = min(0.95, max(0.5, 0.7 + abs(total_signal) * 0.1))
            
            prediction_result = {
                'timestamp': datetime.now().isoformat(),
                'current_price': float(current_price),
                'predicted_price': float(predicted_price),
                'price_change': float(predicted_price - current_price),
                'price_change_pct': float(price_change_pct),
                'signal': signal_text,
                'confidence': float(confidence),
                'technical_indicators': {
                    'sma_5': float(sma_5),
                    'sma_20': float(sma_20),
                    'rsi': float(rsi),
                    'macd': float(macd),
                    'macd_signal': float(macd_signal)
                },
                'signals': {
                    'ma_signal': signals[0],
                    'rsi_signal': signals[1],
                    'macd_signal': signals[2],
                    'total_signal': total_signal
                }
            }
            
            # 保存预测历史
            self.prediction_history.append(prediction_result)
            
            logger.info(f"预测完成: {current_price:.2f} → {predicted_price:.2f} ({signal_text})")
            
            return prediction_result
            
        except Exception as e:
            logger.error(f"预测失败: {e}")
            return None
    
    def generate_charts(self, data, prediction):
        """生成图表"""
        try:
            logger.info("生成预测图表...")
            
            # 设置图表样式
            plt.style.use('default')
            sns.set_palette("husl")
            
            # 创建子图
            fig, axes = plt.subplots(2, 2, figsize=(16, 12))
            fig.suptitle('黄金价格预测分析', fontsize=16, fontweight='bold')
            
            # 最近30天的数据
            recent_data = data.tail(30 * 24)  # 最近30天
            
            # 1. 价格走势图
            ax1 = axes[0, 0]
            ax1.plot(recent_data['timestamp'], recent_data['close'], label='收盘价', linewidth=2)
            ax1.plot(recent_data['timestamp'], recent_data['sma_5'], label='5日均线', alpha=0.7)
            ax1.plot(recent_data['timestamp'], recent_data['sma_20'], label='20日均线', alpha=0.7)
            
            # 添加预测点
            pred_time = datetime.now() + timedelta(hours=1)
            ax1.scatter([pred_time], [prediction['predicted_price']], 
                       color='red', s=100, label=f"预测价格: ${prediction['predicted_price']:.2f}", zorder=5)
            
            ax1.set_title('价格走势与预测')
            ax1.set_xlabel('时间')
            ax1.set_ylabel('价格 ($)')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            ax1.tick_params(axis='x', rotation=45)
            
            # 2. 技术指标 - RSI
            ax2 = axes[0, 1]
            ax2.plot(recent_data['timestamp'], recent_data['rsi'], label='RSI', color='purple', linewidth=2)
            ax2.axhline(y=70, color='r', linestyle='--', alpha=0.7, label='超买线(70)')
            ax2.axhline(y=30, color='g', linestyle='--', alpha=0.7, label='超卖线(30)')
            ax2.axhline(y=50, color='gray', linestyle='-', alpha=0.5)
            
            current_rsi = prediction['technical_indicators']['rsi']
            ax2.scatter([recent_data['timestamp'].iloc[-1]], [current_rsi], 
                       color='red', s=100, label=f"当前RSI: {current_rsi:.1f}", zorder=5)
            
            ax2.set_title('相对强弱指数 (RSI)')
            ax2.set_xlabel('时间')
            ax2.set_ylabel('RSI')
            ax2.set_ylim(0, 100)
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            ax2.tick_params(axis='x', rotation=45)
            
            # 3. MACD
            ax3 = axes[1, 0]
            ax3.plot(recent_data['timestamp'], recent_data['macd'], label='MACD', linewidth=2)
            ax3.plot(recent_data['timestamp'], recent_data['macd_signal'], label='信号线', linewidth=2)
            ax3.bar(recent_data['timestamp'], recent_data['macd_histogram'], 
                   label='MACD柱状图', alpha=0.6, width=0.02)
            ax3.axhline(y=0, color='black', linestyle='-', alpha=0.5)
            
            ax3.set_title('MACD指标')
            ax3.set_xlabel('时间')
            ax3.set_ylabel('MACD')
            ax3.legend()
            ax3.grid(True, alpha=0.3)
            ax3.tick_params(axis='x', rotation=45)
            
            # 4. 成交量
            ax4 = axes[1, 1]
            ax4.bar(recent_data['timestamp'], recent_data['volume'], alpha=0.6, label='成交量')
            ax4.plot(recent_data['timestamp'], recent_data['volume_sma'], 
                    color='red', label='成交量均线', linewidth=2)
            
            ax4.set_title('成交量分析')
            ax4.set_xlabel('时间')
            ax4.set_ylabel('成交量')
            ax4.legend()
            ax4.grid(True, alpha=0.3)
            ax4.tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            
            # 保存图表
            chart_path = self.results_dir / f"prediction_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"图表已保存到: {chart_path}")
            return str(chart_path)
            
        except Exception as e:
            logger.error(f"图表生成失败: {e}")
            return None

    def generate_html_report(self, data, prediction, chart_path):
        """生成HTML预测报告"""
        try:
            logger.info("生成HTML预测报告...")

            # 读取图表文件并转换为base64
            import base64
            chart_base64 = ""
            if chart_path and os.path.exists(chart_path):
                with open(chart_path, 'rb') as f:
                    chart_data = f.read()
                    chart_base64 = base64.b64encode(chart_data).decode('utf-8')

            # 获取最新技术指标
            latest = data.iloc[-1]

            # 生成HTML内容
            html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>黄金价格预测报告</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #ff6b6b 0%, #feca57 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}

        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: bold;
        }}

        .header .subtitle {{
            margin-top: 10px;
            font-size: 1.2em;
            opacity: 0.9;
        }}

        .content {{
            padding: 30px;
        }}

        .prediction-summary {{
            background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
            color: white;
            padding: 25px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }}

        .prediction-summary h2 {{
            margin: 0 0 15px 0;
            font-size: 1.8em;
        }}

        .price-info {{
            display: flex;
            justify-content: space-around;
            flex-wrap: wrap;
            margin: 20px 0;
        }}

        .price-item {{
            text-align: center;
            margin: 10px;
        }}

        .price-value {{
            font-size: 2em;
            font-weight: bold;
            margin: 5px 0;
        }}

        .price-label {{
            font-size: 0.9em;
            opacity: 0.8;
        }}

        .signal-badge {{
            display: inline-block;
            padding: 10px 20px;
            border-radius: 25px;
            font-weight: bold;
            font-size: 1.1em;
            margin: 10px;
        }}

        .signal-bullish {{
            background: #00b894;
            color: white;
        }}

        .signal-bearish {{
            background: #e17055;
            color: white;
        }}

        .signal-neutral {{
            background: #636e72;
            color: white;
        }}

        .technical-indicators {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}

        .indicator-card {{
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            border-left: 4px solid #74b9ff;
        }}

        .indicator-card h3 {{
            margin: 0 0 15px 0;
            color: #2d3436;
        }}

        .indicator-value {{
            font-size: 1.5em;
            font-weight: bold;
            color: #0984e3;
        }}

        .chart-container {{
            text-align: center;
            margin: 30px 0;
        }}

        .chart-container img {{
            max-width: 100%;
            height: auto;
            border-radius: 10px;
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        }}

        .analysis-section {{
            background: #f8f9fa;
            border-radius: 10px;
            padding: 25px;
            margin: 30px 0;
        }}

        .analysis-section h3 {{
            color: #2d3436;
            margin-bottom: 15px;
        }}

        .confidence-bar {{
            background: #ddd;
            border-radius: 10px;
            height: 20px;
            margin: 10px 0;
            overflow: hidden;
        }}

        .confidence-fill {{
            height: 100%;
            background: linear-gradient(90deg, #00b894 0%, #00cec9 100%);
            border-radius: 10px;
            transition: width 0.3s ease;
        }}

        .timestamp {{
            text-align: center;
            color: #636e72;
            margin-top: 30px;
            font-size: 0.9em;
        }}

        @media (max-width: 768px) {{
            .price-info {{
                flex-direction: column;
            }}

            .technical-indicators {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏆 黄金价格预测报告</h1>
            <div class="subtitle">基于技术分析的智能预测系统</div>
        </div>

        <div class="content">
            <div class="prediction-summary">
                <h2>📊 预测摘要</h2>
                <div class="price-info">
                    <div class="price-item">
                        <div class="price-label">当前价格</div>
                        <div class="price-value">${prediction['current_price']:.2f}</div>
                    </div>
                    <div class="price-item">
                        <div class="price-label">预测价格</div>
                        <div class="price-value">${prediction['predicted_price']:.2f}</div>
                    </div>
                    <div class="price-item">
                        <div class="price-label">价格变化</div>
                        <div class="price-value">{prediction['price_change']:+.2f}</div>
                    </div>
                    <div class="price-item">
                        <div class="price-label">变化幅度</div>
                        <div class="price-value">{prediction['price_change_pct']:+.2f}%</div>
                    </div>
                </div>

                <div class="signal-badge signal-{'bullish' if '看涨' in prediction['signal'] else 'bearish' if '看跌' in prediction['signal'] else 'neutral'}">
                    {prediction['signal']}
                </div>

                <div style="margin-top: 20px;">
                    <div style="font-size: 1.1em; margin-bottom: 10px;">预测置信度</div>
                    <div class="confidence-bar">
                        <div class="confidence-fill" style="width: {prediction['confidence']*100:.1f}%"></div>
                    </div>
                    <div style="margin-top: 5px;">{prediction['confidence']*100:.1f}%</div>
                </div>
            </div>

            <div class="technical-indicators">
                <div class="indicator-card">
                    <h3>📈 5日移动平均线</h3>
                    <div class="indicator-value">${prediction['technical_indicators']['sma_5']:.2f}</div>
                    <div style="margin-top: 10px; color: #636e72;">
                        {'看涨信号' if prediction['signals']['ma_signal'] > 0 else '看跌信号' if prediction['signals']['ma_signal'] < 0 else '中性信号'}
                    </div>
                </div>

                <div class="indicator-card">
                    <h3>📊 RSI指标</h3>
                    <div class="indicator-value">{prediction['technical_indicators']['rsi']:.1f}</div>
                    <div style="margin-top: 10px; color: #636e72;">
                        {'超卖区域' if prediction['technical_indicators']['rsi'] < 30 else '超买区域' if prediction['technical_indicators']['rsi'] > 70 else '正常区域'}
                    </div>
                </div>

                <div class="indicator-card">
                    <h3>🔄 MACD指标</h3>
                    <div class="indicator-value">{prediction['technical_indicators']['macd']:.3f}</div>
                    <div style="margin-top: 10px; color: #636e72;">
                        {'金叉信号' if prediction['signals']['macd_signal'] > 0 else '死叉信号'}
                    </div>
                </div>

                <div class="indicator-card">
                    <h3>📉 20日移动平均线</h3>
                    <div class="indicator-value">${prediction['technical_indicators']['sma_20']:.2f}</div>
                    <div style="margin-top: 10px; color: #636e72;">
                        支撑/阻力位参考
                    </div>
                </div>
            </div>

            {f'''
            <div class="chart-container">
                <h3>📈 技术分析图表</h3>
                <img src="data:image/png;base64,{chart_base64}" alt="预测分析图表">
            </div>
            ''' if chart_base64 else ''}

            <div class="analysis-section">
                <h3>🔍 分析说明</h3>
                <p><strong>预测方法：</strong>基于移动平均线、RSI和MACD等技术指标的综合分析</p>
                <p><strong>数据来源：</strong>模拟的黄金价格历史数据</p>
                <p><strong>预测周期：</strong>短期（1小时）价格预测</p>
                <p><strong>风险提示：</strong>本预测仅供参考，投资有风险，决策需谨慎</p>

                <h4>📋 信号分析详情：</h4>
                <ul>
                    <li><strong>移动平均线信号：</strong> {'看涨' if prediction['signals']['ma_signal'] > 0 else '看跌' if prediction['signals']['ma_signal'] < 0 else '中性'}</li>
                    <li><strong>RSI信号：</strong> {'看涨' if prediction['signals']['rsi_signal'] > 0 else '看跌' if prediction['signals']['rsi_signal'] < 0 else '中性'}</li>
                    <li><strong>MACD信号：</strong> {'看涨' if prediction['signals']['macd_signal'] > 0 else '看跌'}</li>
                    <li><strong>综合信号强度：</strong> {prediction['signals']['total_signal']}</li>
                </ul>
            </div>

            <div class="timestamp">
                📅 报告生成时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}
            </div>
        </div>
    </div>
</body>
</html>
            """

            # 保存HTML文件
            html_path = self.results_dir / f"prediction_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            logger.info(f"HTML报告已保存到: {html_path}")
            return str(html_path)

        except Exception as e:
            logger.error(f"HTML报告生成失败: {e}")
            return None

    def run_simple_prediction(self):
        """运行简单预测"""
        try:
            logger.info("开始运行简单预测...")

            # 1. 生成模拟数据
            data = self.generate_mock_data(days=30)
            if data is None:
                return {'success': False, 'message': '数据生成失败'}

            # 2. 计算技术指标
            data = self.calculate_technical_indicators(data)

            # 3. 进行预测
            prediction = self.make_simple_prediction(data)
            if prediction is None:
                return {'success': False, 'message': '预测失败'}

            # 4. 生成图表
            chart_path = self.generate_charts(data, prediction)

            # 5. 生成HTML报告
            html_path = self.generate_html_report(data, prediction, chart_path)

            return {
                'success': True,
                'message': '简单预测完成',
                'prediction': prediction,
                'chart_path': chart_path,
                'html_path': html_path,
                'data_points': len(data)
            }

        except Exception as e:
            logger.error(f"简单预测失败: {e}")
            return {'success': False, 'message': str(e)}

    def run_multiple_prediction(self):
        """运行多模型预测"""
        try:
            logger.info("开始运行多模型预测...")

            # 生成数据
            data = self.generate_mock_data(days=30)
            if data is None:
                return {'success': False, 'message': '数据生成失败'}

            data = self.calculate_technical_indicators(data)

            # 运行多个预测模型
            predictions = []

            # 模型1：技术指标预测
            pred1 = self.make_simple_prediction(data)
            if pred1:
                pred1['model_name'] = '技术指标模型'
                predictions.append(pred1)

            # 模型2：趋势预测
            pred2 = self._make_trend_prediction(data)
            if pred2:
                pred2['model_name'] = '趋势分析模型'
                predictions.append(pred2)

            # 模型3：波动率预测
            pred3 = self._make_volatility_prediction(data)
            if pred3:
                pred3['model_name'] = '波动率模型'
                predictions.append(pred3)

            # 集成预测
            if predictions:
                ensemble_prediction = self._ensemble_predictions(predictions)

                # 生成图表
                chart_path = self.generate_charts(data, ensemble_prediction)

                # 生成HTML报告
                html_path = self.generate_html_report(data, ensemble_prediction, chart_path)

                return {
                    'success': True,
                    'message': '多模型预测完成',
                    'individual_predictions': predictions,
                    'ensemble_prediction': ensemble_prediction,
                    'chart_path': chart_path,
                    'html_path': html_path
                }
            else:
                return {'success': False, 'message': '所有预测模型都失败了'}

        except Exception as e:
            logger.error(f"多模型预测失败: {e}")
            return {'success': False, 'message': str(e)}

    def _make_trend_prediction(self, data):
        """趋势分析预测"""
        try:
            latest = data.iloc[-1]
            current_price = latest['close']

            # 计算短期和长期趋势
            short_trend = data['close'].tail(5).pct_change().mean()
            long_trend = data['close'].tail(20).pct_change().mean()

            # 趋势强度
            trend_strength = abs(short_trend) + abs(long_trend)

            # 预测价格变化
            if short_trend > 0 and long_trend > 0:
                price_change_pct = trend_strength * 100 * 2
                signal = "看涨"
            elif short_trend < 0 and long_trend < 0:
                price_change_pct = -trend_strength * 100 * 2
                signal = "看跌"
            else:
                price_change_pct = (short_trend + long_trend) * 100
                signal = "中性"

            predicted_price = current_price * (1 + price_change_pct / 100)
            confidence = min(0.9, max(0.5, trend_strength * 10))

            return {
                'timestamp': datetime.now().isoformat(),
                'current_price': float(current_price),
                'predicted_price': float(predicted_price),
                'price_change': float(predicted_price - current_price),
                'price_change_pct': float(price_change_pct),
                'signal': signal,
                'confidence': float(confidence),
                'technical_indicators': {
                    'short_trend': float(short_trend),
                    'long_trend': float(long_trend),
                    'trend_strength': float(trend_strength)
                }
            }

        except Exception as e:
            logger.error(f"趋势预测失败: {e}")
            return None

    def _make_volatility_prediction(self, data):
        """波动率预测"""
        try:
            latest = data.iloc[-1]
            current_price = latest['close']

            # 计算历史波动率
            returns = data['close'].pct_change().dropna()
            volatility = returns.std()

            # 基于波动率的预测
            if volatility > 0.02:  # 高波动
                price_change_pct = np.random.uniform(-2, 2)
                signal = "高波动"
                confidence = 0.6
            elif volatility > 0.01:  # 中等波动
                price_change_pct = np.random.uniform(-1, 1)
                signal = "中等波动"
                confidence = 0.7
            else:  # 低波动
                price_change_pct = np.random.uniform(-0.5, 0.5)
                signal = "低波动"
                confidence = 0.8

            predicted_price = current_price * (1 + price_change_pct / 100)

            return {
                'timestamp': datetime.now().isoformat(),
                'current_price': float(current_price),
                'predicted_price': float(predicted_price),
                'price_change': float(predicted_price - current_price),
                'price_change_pct': float(price_change_pct),
                'signal': signal,
                'confidence': float(confidence),
                'technical_indicators': {
                    'volatility': float(volatility),
                    'volatility_level': signal
                }
            }

        except Exception as e:
            logger.error(f"波动率预测失败: {e}")
            return None

    def _ensemble_predictions(self, predictions):
        """集成多个预测结果"""
        try:
            if not predictions:
                return None

            # 加权平均
            weights = [p['confidence'] for p in predictions]
            total_weight = sum(weights)

            # 计算加权平均预测价格
            weighted_price = sum(p['predicted_price'] * p['confidence'] for p in predictions) / total_weight

            # 计算平均置信度
            avg_confidence = sum(weights) / len(weights)

            # 确定信号
            signals = [p['signal'] for p in predictions]
            signal_counts = {}
            for signal in signals:
                if '看涨' in signal:
                    signal_counts['bullish'] = signal_counts.get('bullish', 0) + 1
                elif '看跌' in signal:
                    signal_counts['bearish'] = signal_counts.get('bearish', 0) + 1
                else:
                    signal_counts['neutral'] = signal_counts.get('neutral', 0) + 1

            # 选择最多的信号
            if signal_counts.get('bullish', 0) > signal_counts.get('bearish', 0):
                ensemble_signal = "集成看涨"
            elif signal_counts.get('bearish', 0) > signal_counts.get('bullish', 0):
                ensemble_signal = "集成看跌"
            else:
                ensemble_signal = "集成中性"

            current_price = predictions[0]['current_price']
            price_change = weighted_price - current_price
            price_change_pct = (price_change / current_price) * 100

            return {
                'timestamp': datetime.now().isoformat(),
                'current_price': float(current_price),
                'predicted_price': float(weighted_price),
                'price_change': float(price_change),
                'price_change_pct': float(price_change_pct),
                'signal': ensemble_signal,
                'confidence': float(avg_confidence),
                'model_count': len(predictions),
                'technical_indicators': {
                    'ensemble_method': 'weighted_average',
                    'model_weights': weights
                }
            }

        except Exception as e:
            logger.error(f"集成预测失败: {e}")
            return None

    def get_status(self):
        """获取系统状态"""
        return {
            'running': True,
            'prediction_history_count': len(self.prediction_history),
            'last_prediction': self.prediction_history[-1] if self.prediction_history else None,
            'results_directory': str(self.results_dir)
        }

    def start(self):
        """启动系统"""
        try:
            logger.info("启动简单预测系统...")

            # 创建结果目录
            self.results_dir.mkdir(parents=True, exist_ok=True)

            # 初始化系统状态
            self.prediction_history = []

            logger.info("简单预测系统启动成功")
            return True

        except Exception as e:
            logger.error(f"简单预测系统启动失败: {e}")
            return False

    def start_system(self):
        """启动系统（别名方法）"""
        return self.start()

    def run_task(self, task_type):
        """运行任务"""
        try:
            logger.info(f"执行任务: {task_type}")

            if task_type == 'simple_prediction':
                return self.run_simple_prediction()
            elif task_type == 'multiple_prediction':
                return self.run_multiple_prediction()
            elif task_type == 'volatility_prediction':
                return self.run_volatility_prediction()
            else:
                return {
                    'success': False,
                    'message': f'未知任务类型: {task_type}'
                }

        except Exception as e:
            logger.error(f"任务执行失败: {e}")
            return {
                'success': False,
                'message': str(e)
            }

    def get_task_status(self, task_id):
        """获取任务状态"""
        # 简单预测系统的任务都是同步执行的，所以直接返回完成状态
        return {
            'task_id': task_id,
            'status': 'completed',
            'result': {
                'message': '任务已完成',
                'timestamp': datetime.now().isoformat()
            }
        }
