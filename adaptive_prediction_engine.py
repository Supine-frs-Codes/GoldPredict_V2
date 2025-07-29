#!/usr/bin/env python3
"""
自适应预测引擎
具备自我学习和优化能力的实时预测系统
"""

import time
import threading
import queue
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging
from pathlib import Path
import sqlite3
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

from improved_mt5_manager import ImprovedMT5Manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AdaptivePredictionEngine:
    """自适应预测引擎"""
    
    def __init__(self, config, wechat_controller=None):
        self.config = config
        self.running = False
        self.mt5_manager = ImprovedMT5Manager()

        # 微信推送控制器
        self.wechat_controller = wechat_controller
        self.last_wechat_push_time = 0
        
        # 数据存储
        self.price_history = []
        self.prediction_history = []
        self.accuracy_history = []
        
        # 自适应参数
        self.confidence_base = 0.3
        self.confidence_growth_rate = 0.05
        self.accuracy_window = 20  # 用于计算准确率的窗口大小
        
        # 预测器权重（自适应调整）
        self.predictor_weights = {
            'technical': 0.4,
            'momentum': 0.3,
            'volatility': 0.2,
            'pattern': 0.1
        }
        
        # 性能指标
        self.performance_metrics = {
            'total_predictions': 0,
            'correct_predictions': 0,
            'average_accuracy': 0.0,
            'recent_accuracy': 0.0,
            'confidence_trend': 0.0
        }
        
        # 设置数据库
        self.setup_database()
        
        print(f"[引擎] 自适应预测引擎初始化")
        print(f"   预测间隔: {config['interval_minutes']}分钟")
        print(f"   数据收集间隔: {config['data_collection_seconds']}秒")
        print(f"   最少数据点: {config['min_data_points']}个")
        print(f"   自适应学习: 启用")
    
    def setup_database(self):
        """设置增强数据库"""
        db_path = Path("results/realtime/adaptive_predictions.db")
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
        
        # 预测表
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                current_price REAL,
                predicted_price REAL,
                signal TEXT,
                confidence REAL,
                actual_price REAL,
                accuracy REAL,
                verified_at TEXT,
                method TEXT,
                predictor_weights TEXT,
                market_conditions TEXT
            )
        ''')
        
        # 价格数据表
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS price_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                price REAL,
                bid REAL,
                ask REAL,
                volume REAL,
                spread REAL
            )
        ''')
        
        # 性能指标表
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                total_predictions INTEGER,
                correct_predictions INTEGER,
                average_accuracy REAL,
                recent_accuracy REAL,
                confidence_level REAL,
                predictor_weights TEXT
            )
        ''')
        
        self.conn.commit()
    
    def start(self):
        """启动系统（统一接口）"""
        return self.start_engine()

    def start_engine(self):
        """启动预测引擎"""
        if self.running:
            print("[警告] 引擎已在运行中")
            return False
        
        print("[启动] 自适应预测引擎启动")
        
        # 执行自检
        if not self._self_check():
            print("[错误] 自检失败，无法启动")
            return False
        
        self.running = True
        
        # 启动各个线程
        threads = [
            threading.Thread(target=self._data_collection_loop, daemon=True),
            threading.Thread(target=self._prediction_loop, daemon=True),
            threading.Thread(target=self._verification_loop, daemon=True),
            threading.Thread(target=self._optimization_loop, daemon=True),
            threading.Thread(target=self._performance_monitoring_loop, daemon=True)
        ]
        
        for thread in threads:
            thread.start()
        
        print("[成功] 所有线程已启动")
        return True
    
    def stop_engine(self):
        """停止预测引擎"""
        self.running = False
        print("[停止] 自适应预测引擎已停止")
        
        # 保存最终性能指标
        self._save_performance_metrics()
        
        # 清理资源
        try:
            self.mt5_manager.cleanup()
        except Exception as e:
            logger.error(f"清理MT5连接时出错: {e}")
    
    def _self_check(self):
        """系统自检"""
        print("[自检] 开始系统自检...")
        
        # 1. MT5连接检查
        print("   检查MT5连接...")
        if not self.mt5_manager.ensure_connection():
            print("   ❌ MT5连接失败")
            return False
        print("   ✅ MT5连接正常")
        
        # 2. 黄金符号检查
        print("   检查黄金符号...")
        symbol = self.mt5_manager.get_gold_symbol()
        if not symbol:
            print("   ❌ 未找到黄金符号")
            return False
        print(f"   ✅ 黄金符号: {symbol}")
        
        # 3. 价格数据检查
        print("   检查价格数据...")
        price_data = self.mt5_manager.get_current_price(symbol)
        if not price_data:
            print("   ❌ 无法获取价格数据")
            return False
        print(f"   ✅ 当前价格: ${price_data['bid']:.2f}")
        
        # 4. 数据库检查
        print("   检查数据库...")
        try:
            cursor = self.conn.execute("SELECT COUNT(*) FROM predictions")
            count = cursor.fetchone()[0]
            print(f"   ✅ 数据库正常，历史预测: {count}条")
        except Exception as e:
            print(f"   ❌ 数据库错误: {e}")
            return False
        
        # 5. 加载历史性能
        print("   加载历史性能...")
        self._load_historical_performance()
        print(f"   ✅ 历史准确率: {self.performance_metrics['average_accuracy']:.1%}")
        
        print("[自检] 系统自检完成 ✅")
        return True
    
    def _load_historical_performance(self):
        """加载历史性能数据"""
        try:
            # 加载最近的性能指标
            cursor = self.conn.execute('''
                SELECT * FROM performance_metrics 
                ORDER BY timestamp DESC LIMIT 1
            ''')
            
            result = cursor.fetchone()
            if result:
                self.performance_metrics.update({
                    'total_predictions': result[2],
                    'correct_predictions': result[3],
                    'average_accuracy': result[4],
                    'recent_accuracy': result[5]
                })
                
                # 加载预测器权重
                if result[7]:
                    weights = json.loads(result[7])
                    self.predictor_weights.update(weights)
            
            # 加载最近的准确率历史
            cursor = self.conn.execute('''
                SELECT accuracy FROM predictions 
                WHERE verified_at IS NOT NULL 
                ORDER BY timestamp DESC LIMIT ?
            ''', (self.accuracy_window,))
            
            accuracies = [row[0] for row in cursor.fetchall()]
            self.accuracy_history = accuracies
            
        except Exception as e:
            logger.error(f"加载历史性能失败: {e}")
    
    def _data_collection_loop(self):
        """数据收集循环"""
        print("[数据] 数据收集线程启动")
        
        while self.running:
            try:
                symbol = self.mt5_manager.get_gold_symbol()
                if not symbol:
                    time.sleep(30)
                    continue
                
                # 获取当前价格
                current_price = self.mt5_manager.get_current_price(symbol)
                if current_price:
                    main_price = current_price['last'] if current_price['last'] > 0 else current_price['bid']
                    spread = current_price['ask'] - current_price['bid']
                    
                    price_data = {
                        'timestamp': datetime.now().isoformat(),
                        'price': main_price,
                        'bid': current_price['bid'],
                        'ask': current_price['ask'],
                        'volume': current_price.get('volume', 0),
                        'spread': spread
                    }
                    
                    # 添加到历史数据
                    self.price_history.append(price_data)
                    max_history_size = self.config.get('max_history_size', 1000)
                    if len(self.price_history) > max_history_size:
                        self.price_history.pop(0)
                    
                    # 保存到数据库
                    self._save_price_data(price_data)
                    
                    print(f"[数据] {main_price:.2f} | 点差: {spread:.2f} | 历史: {len(self.price_history)}")
                else:
                    print("[警告] 价格获取失败")
                    time.sleep(2)
                
                time.sleep(self.config['data_collection_seconds'])
                
            except Exception as e:
                logger.error(f"数据收集错误: {e}")
                time.sleep(30)
    
    def _prediction_loop(self):
        """预测循环"""
        print("[预测] 预测线程启动")
        
        last_prediction_time = 0
        interval_seconds = self.config['interval_minutes'] * 60
        
        while self.running:
            try:
                current_time = time.time()
                
                if current_time - last_prediction_time >= interval_seconds:
                    if len(self.price_history) >= self.config['min_data_points']:
                        self._make_adaptive_prediction()
                        last_prediction_time = current_time
                    else:
                        print(f"[等待] 数据不足: {len(self.price_history)}/{self.config['min_data_points']}")
                
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"预测循环错误: {e}")
                time.sleep(10)
    
    def _make_adaptive_prediction(self):
        """执行自适应预测"""
        try:
            print(f"\n[预测] 开始自适应预测...")
            
            # 准备数据
            df = pd.DataFrame(self.price_history)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            current_price = df['price'].iloc[-1]
            current_time = datetime.now()
            
            # 分析市场条件
            market_conditions = self._analyze_market_conditions(df)
            
            # 执行多种预测方法
            predictions = {
                'technical': self._technical_prediction(df),
                'momentum': self._momentum_prediction(df),
                'volatility': self._volatility_prediction(df),
                'pattern': self._pattern_prediction(df)
            }
            
            # 自适应权重调整
            adjusted_weights = self._adjust_predictor_weights(predictions, market_conditions)
            
            # 集成预测
            final_prediction = self._ensemble_prediction(predictions, adjusted_weights, current_price)
            
            # 计算自适应置信度
            confidence = self._calculate_adaptive_confidence(final_prediction, market_conditions)
            
            # 生成交易信号
            signal = self._generate_enhanced_signal(final_prediction, current_price, confidence)
            
            # 保存预测结果
            prediction_result = {
                'timestamp': current_time.isoformat(),
                'current_price': current_price,
                'predicted_price': final_prediction['price'],
                'signal': signal['direction'],
                'confidence': confidence,
                'method': 'adaptive_ensemble',
                'predictor_weights': json.dumps(adjusted_weights),
                'market_conditions': json.dumps(market_conditions),
                'target_time': (current_time + timedelta(minutes=self.config['interval_minutes'])).isoformat()
            }
            
            self.prediction_history.append(prediction_result)
            self._save_prediction(prediction_result)

            # 检查是否需要推送到微信
            self._check_and_send_wechat_push(prediction_result)

            # 更新性能指标
            self.performance_metrics['total_predictions'] += 1

            print(f"[结果] 当前: ${current_price:.2f} → 预测: ${final_prediction['price']:.2f}")
            print(f"[信号] {signal['direction']} (置信度: {confidence:.1%})")
            print(f"[权重] {adjusted_weights}")
            print(f"[调试] 保存的预测结果信号: {prediction_result['signal']}")
            
        except Exception as e:
            logger.error(f"自适应预测错误: {e}")
    
    def _analyze_market_conditions(self, df):
        """分析市场条件"""
        try:
            # 计算技术指标
            df['returns'] = df['price'].pct_change()
            df['volatility'] = df['returns'].rolling(10).std()
            df['ma_5'] = df['price'].rolling(5).mean()
            df['ma_20'] = df['price'].rolling(20).mean() if len(df) >= 20 else df['price'].rolling(len(df)).mean()
            
            current_price = df['price'].iloc[-1]
            volatility = df['volatility'].iloc[-1] if not pd.isna(df['volatility'].iloc[-1]) else 0
            
            # 趋势强度
            trend_strength = abs((df['ma_5'].iloc[-1] - df['ma_20'].iloc[-1]) / df['ma_20'].iloc[-1]) if df['ma_20'].iloc[-1] != 0 else 0
            
            # 价格位置
            recent_high = df['price'].tail(20).max()
            recent_low = df['price'].tail(20).min()
            price_position = (current_price - recent_low) / (recent_high - recent_low) if recent_high != recent_low else 0.5
            
            # 成交量分析（如果有）
            volume_trend = 0
            if 'volume' in df.columns and df['volume'].sum() > 0:
                recent_volume = df['volume'].tail(5).mean()
                historical_volume = df['volume'].mean()
                volume_trend = (recent_volume - historical_volume) / historical_volume if historical_volume > 0 else 0
            
            return {
                'volatility': float(volatility),
                'trend_strength': float(trend_strength),
                'price_position': float(price_position),
                'volume_trend': float(volume_trend),
                'market_regime': self._classify_market_regime(volatility, trend_strength)
            }
            
        except Exception as e:
            logger.error(f"市场条件分析错误: {e}")
            return {
                'volatility': 0.01,
                'trend_strength': 0.1,
                'price_position': 0.5,
                'volume_trend': 0,
                'market_regime': 'normal'
            }
    
    def _classify_market_regime(self, volatility, trend_strength):
        """分类市场状态"""
        if volatility > 0.02:
            return 'high_volatility'
        elif trend_strength > 0.01:
            return 'trending'
        elif volatility < 0.005:
            return 'low_volatility'
        else:
            return 'normal'
    
    def _technical_prediction(self, df):
        """技术分析预测"""
        try:
            current_price = df['price'].iloc[-1]
            
            # 移动平均
            df['ma_5'] = df['price'].rolling(5).mean()
            df['ma_10'] = df['price'].rolling(10).mean()
            
            ma_5 = df['ma_5'].iloc[-1]
            ma_10 = df['ma_10'].iloc[-1]
            
            # 趋势信号
            trend_signal = (ma_5 - ma_10) / ma_10 if ma_10 != 0 else 0
            
            # RSI
            rsi = self._calculate_rsi(df['price'])
            rsi_signal = (50 - rsi) / 100 if rsi else 0
            
            # 预测价格变化
            price_change = trend_signal * 0.6 + rsi_signal * 0.4
            price_change = max(-0.01, min(0.01, price_change))  # 限制在±1%
            
            predicted_price = current_price * (1 + price_change)
            
            return {
                'price': predicted_price,
                'confidence': min(0.8, abs(trend_signal) + 0.3),
                'components': {
                    'trend': trend_signal,
                    'rsi': rsi_signal
                }
            }
            
        except Exception as e:
            logger.error(f"技术分析预测错误: {e}")
            return {'price': df['price'].iloc[-1], 'confidence': 0.3}
    
    def _momentum_prediction(self, df):
        """动量预测"""
        try:
            current_price = df['price'].iloc[-1]
            
            # 短期动量
            if len(df) >= 5:
                momentum_5 = (current_price - df['price'].iloc[-5]) / df['price'].iloc[-5]
            else:
                momentum_5 = 0
            
            # 中期动量
            if len(df) >= 10:
                momentum_10 = (current_price - df['price'].iloc[-10]) / df['price'].iloc[-10]
            else:
                momentum_10 = momentum_5
            
            # 动量信号
            momentum_signal = momentum_5 * 0.7 + momentum_10 * 0.3
            momentum_signal = max(-0.005, min(0.005, momentum_signal))
            
            predicted_price = current_price * (1 + momentum_signal)
            
            return {
                'price': predicted_price,
                'confidence': min(0.7, abs(momentum_signal) * 100 + 0.3),
                'components': {
                    'short_momentum': momentum_5,
                    'medium_momentum': momentum_10
                }
            }
            
        except Exception as e:
            logger.error(f"动量预测错误: {e}")
            return {'price': df['price'].iloc[-1], 'confidence': 0.3}
    
    def _volatility_prediction(self, df):
        """波动率预测"""
        try:
            current_price = df['price'].iloc[-1]
            
            # 计算波动率
            returns = df['price'].pct_change().dropna()
            if len(returns) > 1:
                volatility = returns.std()
                recent_volatility = returns.tail(5).std()
            else:
                volatility = recent_volatility = 0.01
            
            # 波动率变化
            volatility_change = recent_volatility - volatility
            
            # 基于波动率的预测调整
            volatility_signal = -volatility_change * 0.5  # 高波动率降低预测幅度
            volatility_signal = max(-0.003, min(0.003, volatility_signal))
            
            predicted_price = current_price * (1 + volatility_signal)
            
            return {
                'price': predicted_price,
                'confidence': max(0.2, 0.8 - volatility * 50),  # 低波动率高置信度
                'components': {
                    'volatility': volatility,
                    'volatility_change': volatility_change
                }
            }
            
        except Exception as e:
            logger.error(f"波动率预测错误: {e}")
            return {'price': df['price'].iloc[-1], 'confidence': 0.3}
    
    def _pattern_prediction(self, df):
        """模式识别预测"""
        try:
            current_price = df['price'].iloc[-1]
            
            # 简单模式识别
            if len(df) >= 5:
                recent_prices = df['price'].tail(5).values
                
                # 检测趋势模式
                if all(recent_prices[i] <= recent_prices[i+1] for i in range(4)):
                    pattern_signal = 0.002  # 上升趋势
                elif all(recent_prices[i] >= recent_prices[i+1] for i in range(4)):
                    pattern_signal = -0.002  # 下降趋势
                else:
                    # 检测反转模式
                    if recent_prices[-1] > recent_prices[-2] and recent_prices[-2] < recent_prices[-3]:
                        pattern_signal = 0.001  # 可能反转向上
                    elif recent_prices[-1] < recent_prices[-2] and recent_prices[-2] > recent_prices[-3]:
                        pattern_signal = -0.001  # 可能反转向下
                    else:
                        pattern_signal = 0
            else:
                pattern_signal = 0
            
            predicted_price = current_price * (1 + pattern_signal)
            
            return {
                'price': predicted_price,
                'confidence': min(0.6, abs(pattern_signal) * 200 + 0.2),
                'components': {
                    'pattern_signal': pattern_signal
                }
            }
            
        except Exception as e:
            logger.error(f"模式预测错误: {e}")
            return {'price': df['price'].iloc[-1], 'confidence': 0.3}
    
    def _calculate_rsi(self, prices, period=14):
        """计算RSI"""
        try:
            if len(prices) < period + 1:
                return 50
            
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50
        except:
            return 50

    def _adjust_predictor_weights(self, predictions, market_conditions):
        """自适应调整预测器权重"""
        try:
            adjusted_weights = self.predictor_weights.copy()

            # 根据市场状态调整权重
            market_regime = market_conditions['market_regime']
            volatility = market_conditions['volatility']
            trend_strength = market_conditions['trend_strength']

            if market_regime == 'high_volatility':
                # 高波动时增加波动率预测器权重
                adjusted_weights['volatility'] *= 1.5
                adjusted_weights['technical'] *= 0.8
            elif market_regime == 'trending':
                # 趋势市场增加技术分析和动量权重
                adjusted_weights['technical'] *= 1.3
                adjusted_weights['momentum'] *= 1.2
                adjusted_weights['volatility'] *= 0.7
            elif market_regime == 'low_volatility':
                # 低波动时增加模式识别权重
                adjusted_weights['pattern'] *= 1.4
                adjusted_weights['volatility'] *= 0.6

            # 根据历史准确率调整权重
            if len(self.accuracy_history) >= 5:
                recent_accuracy = np.mean(self.accuracy_history[-5:])
                if recent_accuracy > 0.6:
                    # 准确率高时保持当前策略
                    pass
                elif recent_accuracy < 0.4:
                    # 准确率低时重新平衡权重
                    adjusted_weights = {k: 0.25 for k in adjusted_weights.keys()}

            # 标准化权重
            total_weight = sum(adjusted_weights.values())
            if total_weight > 0:
                adjusted_weights = {k: v/total_weight for k, v in adjusted_weights.items()}

            return adjusted_weights

        except Exception as e:
            logger.error(f"权重调整错误: {e}")
            return self.predictor_weights

    def _ensemble_prediction(self, predictions, weights, current_price):
        """集成预测"""
        try:
            weighted_price = 0
            total_weight = 0

            for method, prediction in predictions.items():
                if prediction and method in weights:
                    weight = weights[method]
                    weighted_price += prediction['price'] * weight
                    total_weight += weight

            if total_weight > 0:
                final_price = weighted_price / total_weight
            else:
                final_price = current_price

            return {
                'price': final_price,
                'components': predictions
            }

        except Exception as e:
            logger.error(f"集成预测错误: {e}")
            return {'price': current_price}

    def _calculate_adaptive_confidence(self, prediction, market_conditions):
        """计算自适应置信度"""
        try:
            base_confidence = self.confidence_base

            # 根据历史准确率调整基础置信度
            if len(self.accuracy_history) >= 5:
                recent_accuracy = np.mean(self.accuracy_history[-5:])
                confidence_adjustment = (recent_accuracy - 0.5) * 0.4  # ±0.2的调整范围
                base_confidence += confidence_adjustment

            # 根据市场条件调整
            volatility = market_conditions['volatility']
            trend_strength = market_conditions['trend_strength']

            # 低波动率增加置信度
            volatility_factor = max(0.5, 1 - volatility * 20)

            # 强趋势增加置信度
            trend_factor = min(1.5, 1 + trend_strength * 10)

            # 综合置信度
            final_confidence = base_confidence * volatility_factor * trend_factor

            # 限制在合理范围内
            final_confidence = max(0.1, min(0.95, final_confidence))

            return final_confidence

        except Exception as e:
            logger.error(f"置信度计算错误: {e}")
            return 0.5

    def _generate_enhanced_signal(self, prediction, current_price, confidence):
        """生成增强交易信号"""
        try:
            price_change = prediction['price'] - current_price
            price_change_pct = price_change / current_price

            # 动态阈值（基于置信度）
            base_threshold = 0.0005  # 0.05%
            strong_threshold = base_threshold * (2 - confidence)  # 置信度高时阈值更低
            weak_threshold = base_threshold * (1 - confidence * 0.5)

            if price_change_pct > strong_threshold:
                if confidence > 0.7:
                    direction = "强烈看涨"
                else:
                    direction = "看涨"
            elif price_change_pct > weak_threshold:
                direction = "轻微看涨"
            elif price_change_pct < -strong_threshold:
                if confidence > 0.7:
                    direction = "强烈看跌"
                else:
                    direction = "看跌"
            elif price_change_pct < -weak_threshold:
                direction = "轻微看跌"
            else:
                direction = "横盘"

            return {
                'direction': direction,
                'price_change': price_change,
                'price_change_pct': price_change_pct,
                'confidence': confidence
            }

        except Exception as e:
            logger.error(f"信号生成错误: {e}")
            return {
                'direction': '横盘',
                'price_change': 0,
                'price_change_pct': 0,
                'confidence': 0.5
            }

    def _verification_loop(self):
        """验证循环"""
        print("[验证] 验证线程启动")

        while self.running:
            try:
                self._verify_predictions()
                time.sleep(60)  # 每分钟检查一次
            except Exception as e:
                logger.error(f"验证循环错误: {e}")
                time.sleep(60)

    def _verify_predictions(self):
        """验证预测结果"""
        try:
            current_time = datetime.now()

            # 查询需要验证的预测
            cursor = self.conn.execute('''
                SELECT * FROM predictions
                WHERE verified_at IS NULL
                AND datetime(timestamp) <= datetime(?, '-{} minutes')
            '''.format(self.config['interval_minutes']), (current_time.isoformat(),))

            unverified = cursor.fetchall()

            for row in unverified:
                pred_id = row[0]
                timestamp = row[1]
                current_price = row[2]
                predicted_price = row[3]
                signal = row[4]
                confidence = row[5]

                # 获取实际价格
                actual_price = self._get_actual_price_at_time(timestamp)
                if actual_price:
                    # 计算准确率
                    accuracy = self._calculate_enhanced_accuracy(
                        predicted_price, actual_price, current_price, signal, confidence
                    )

                    # 更新数据库
                    self.conn.execute('''
                        UPDATE predictions
                        SET actual_price = ?, accuracy = ?, verified_at = ?
                        WHERE id = ?
                    ''', (actual_price, accuracy, current_time.isoformat(), pred_id))

                    self.conn.commit()

                    # 更新准确率历史
                    self.accuracy_history.append(accuracy)
                    if len(self.accuracy_history) > self.accuracy_window:
                        self.accuracy_history.pop(0)

                    # 更新性能指标
                    if accuracy > 0.6:
                        self.performance_metrics['correct_predictions'] += 1

                    print(f"[验证] 预测ID {pred_id}: 准确率 {accuracy:.1%}")

        except Exception as e:
            logger.error(f"验证错误: {e}")

    def _calculate_enhanced_accuracy(self, predicted, actual, baseline, signal, confidence):
        """计算增强准确率"""
        try:
            if actual == baseline:
                return 0.5

            # 方向准确性
            predicted_direction = 1 if predicted > baseline else -1
            actual_direction = 1 if actual > baseline else -1
            direction_correct = predicted_direction == actual_direction

            # 价格准确性
            predicted_change = abs(predicted - baseline)
            actual_change = abs(actual - baseline)

            if actual_change > 0:
                price_accuracy = 1 - min(abs(predicted_change - actual_change) / actual_change, 1)
            else:
                price_accuracy = 0.5

            # 信号强度准确性
            signal_bonus = 0
            if "强烈" in signal and direction_correct:
                signal_bonus = 0.1  # 强信号正确时额外奖励
            elif "轻微" in signal and direction_correct:
                signal_bonus = 0.05  # 轻微信号正确时小额奖励

            # 置信度调整
            confidence_factor = confidence if direction_correct else (1 - confidence)

            # 综合准确率
            if direction_correct:
                accuracy = 0.4 + 0.4 * price_accuracy + 0.1 * confidence_factor + signal_bonus
            else:
                accuracy = 0.3 * (1 - price_accuracy) * (1 - confidence_factor)

            return max(0, min(1, accuracy))

        except Exception as e:
            logger.error(f"准确率计算错误: {e}")
            return 0.5

    def _get_actual_price_at_time(self, target_timestamp):
        """获取指定时间的实际价格"""
        target_time = datetime.fromisoformat(target_timestamp)
        target_time += timedelta(minutes=self.config['interval_minutes'])

        # 在价格历史中查找最接近的价格
        closest_price = None
        min_time_diff = float('inf')

        for price_data in self.price_history:
            price_time = datetime.fromisoformat(price_data['timestamp'])
            time_diff = abs((price_time - target_time).total_seconds())

            if time_diff < min_time_diff:
                min_time_diff = time_diff
                closest_price = price_data['price']

        return closest_price if min_time_diff < 300 else None  # 5分钟内的数据才有效

    def _optimization_loop(self):
        """优化循环"""
        print("[优化] 优化线程启动")

        while self.running:
            try:
                # 每10分钟执行一次优化
                time.sleep(600)

                if len(self.accuracy_history) >= 10:
                    self._optimize_system()

            except Exception as e:
                logger.error(f"优化循环错误: {e}")
                time.sleep(600)

    def _optimize_system(self):
        """系统优化"""
        try:
            print("[优化] 执行系统优化...")

            # 1. 分析预测器性能
            predictor_performance = self._analyze_predictor_performance()

            # 2. 调整基础置信度
            self._adjust_base_confidence()

            # 3. 优化预测器权重
            self._optimize_predictor_weights(predictor_performance)

            # 4. 更新性能指标
            self._update_performance_metrics()

            print(f"[优化] 系统优化完成，当前准确率: {self.performance_metrics['recent_accuracy']:.1%}")

        except Exception as e:
            logger.error(f"系统优化错误: {e}")

    def _analyze_predictor_performance(self):
        """分析预测器性能"""
        try:
            # 获取最近的预测结果
            cursor = self.conn.execute('''
                SELECT predictor_weights, accuracy FROM predictions
                WHERE verified_at IS NOT NULL
                AND datetime(timestamp) >= datetime('now', '-24 hours')
                ORDER BY timestamp DESC
            ''')

            results = cursor.fetchall()
            performance = {}

            for weights_json, accuracy in results:
                if weights_json:
                    weights = json.loads(weights_json)
                    for predictor, weight in weights.items():
                        if predictor not in performance:
                            performance[predictor] = []
                        performance[predictor].append(accuracy * weight)

            # 计算平均性能
            avg_performance = {}
            for predictor, scores in performance.items():
                avg_performance[predictor] = np.mean(scores) if scores else 0.5

            return avg_performance

        except Exception as e:
            logger.error(f"预测器性能分析错误: {e}")
            return {}

    def _adjust_base_confidence(self):
        """调整基础置信度"""
        try:
            if len(self.accuracy_history) >= 10:
                recent_accuracy = np.mean(self.accuracy_history[-10:])

                # 根据准确率调整基础置信度
                if recent_accuracy > 0.7:
                    self.confidence_base = min(0.6, self.confidence_base + 0.02)
                elif recent_accuracy < 0.4:
                    self.confidence_base = max(0.2, self.confidence_base - 0.02)

                print(f"[优化] 基础置信度调整为: {self.confidence_base:.2f}")

        except Exception as e:
            logger.error(f"置信度调整错误: {e}")

    def _optimize_predictor_weights(self, performance):
        """优化预测器权重"""
        try:
            if not performance:
                return

            # 根据性能调整权重
            total_performance = sum(performance.values())
            if total_performance > 0:
                for predictor in self.predictor_weights:
                    if predictor in performance:
                        # 性能好的预测器增加权重
                        performance_ratio = performance[predictor] / total_performance
                        self.predictor_weights[predictor] = 0.7 * self.predictor_weights[predictor] + 0.3 * performance_ratio

            # 标准化权重
            total_weight = sum(self.predictor_weights.values())
            if total_weight > 0:
                self.predictor_weights = {k: v/total_weight for k, v in self.predictor_weights.items()}

            print(f"[优化] 预测器权重已优化: {self.predictor_weights}")

        except Exception as e:
            logger.error(f"权重优化错误: {e}")

    def _update_performance_metrics(self):
        """更新性能指标"""
        try:
            if len(self.accuracy_history) > 0:
                self.performance_metrics['average_accuracy'] = np.mean(self.accuracy_history)
                self.performance_metrics['recent_accuracy'] = np.mean(self.accuracy_history[-10:]) if len(self.accuracy_history) >= 10 else np.mean(self.accuracy_history)

                # 计算置信度趋势
                if len(self.accuracy_history) >= 5:
                    recent_trend = np.mean(self.accuracy_history[-5:]) - np.mean(self.accuracy_history[-10:-5]) if len(self.accuracy_history) >= 10 else 0
                    self.performance_metrics['confidence_trend'] = recent_trend

        except Exception as e:
            logger.error(f"性能指标更新错误: {e}")

    def _performance_monitoring_loop(self):
        """性能监控循环"""
        print("[监控] 性能监控线程启动")

        while self.running:
            try:
                # 每5分钟保存一次性能指标
                time.sleep(300)
                self._save_performance_metrics()

            except Exception as e:
                logger.error(f"性能监控错误: {e}")
                time.sleep(300)

    def _save_price_data(self, price_data):
        """保存价格数据"""
        try:
            self.conn.execute('''
                INSERT INTO price_data (timestamp, price, bid, ask, volume, spread)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                price_data['timestamp'],
                price_data['price'],
                price_data['bid'],
                price_data['ask'],
                price_data['volume'],
                price_data['spread']
            ))
            self.conn.commit()
        except Exception as e:
            logger.error(f"保存价格数据错误: {e}")

    def _save_prediction(self, prediction):
        """保存预测结果"""
        try:
            self.conn.execute('''
                INSERT INTO predictions (timestamp, current_price, predicted_price, signal, confidence, method, predictor_weights, market_conditions)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                prediction['timestamp'],
                prediction['current_price'],
                prediction['predicted_price'],
                prediction['signal'],
                prediction['confidence'],
                prediction['method'],
                prediction['predictor_weights'],
                prediction['market_conditions']
            ))
            self.conn.commit()
        except Exception as e:
            logger.error(f"保存预测结果错误: {e}")

    def _save_performance_metrics(self):
        """保存性能指标"""
        try:
            self.conn.execute('''
                INSERT INTO performance_metrics (timestamp, total_predictions, correct_predictions, average_accuracy, recent_accuracy, confidence_level, predictor_weights)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                self.performance_metrics['total_predictions'],
                self.performance_metrics['correct_predictions'],
                self.performance_metrics['average_accuracy'],
                self.performance_metrics['recent_accuracy'],
                self.confidence_base,
                json.dumps(self.predictor_weights)
            ))
            self.conn.commit()
        except Exception as e:
            logger.error(f"保存性能指标错误: {e}")

    def get_status(self):
        """获取系统状态"""
        return {
            'running': self.running,
            'config': self.config,
            'performance_metrics': self.performance_metrics,
            'predictor_weights': self.predictor_weights,
            'confidence_base': self.confidence_base,
            'data_points': len(self.price_history),
            'predictions_count': len(self.prediction_history),
            'accuracy_history': self.accuracy_history[-10:] if len(self.accuracy_history) >= 10 else self.accuracy_history
        }

    def get_latest_prediction(self):
        """获取最新预测"""
        if self.prediction_history:
            latest = self.prediction_history[-1]
            print(f"[调试] get_latest_prediction返回信号: {latest.get('signal', 'N/A')}")
            return latest
        return None

    def _check_and_send_wechat_push(self, prediction_result):
        """检查并发送微信推送"""
        try:
            # 检查是否启用微信推送
            if not self.config.get('wechat_push_enabled', False):
                return

            # 检查是否有微信控制器
            if not self.wechat_controller:
                return

            # 检查推送间隔
            current_time = time.time()
            push_interval_seconds = self.config.get('wechat_push_interval_minutes', 30) * 60

            if current_time - self.last_wechat_push_time < push_interval_seconds:
                return

            # 发送微信推送
            result = self.wechat_controller.send_prediction_to_wechat('realtime', prediction_result)

            if result.get('success', False):
                self.last_wechat_push_time = current_time
                print(f"[微信] 预测结果已推送到微信群")
            else:
                print(f"[微信] 推送失败: {result.get('message', '未知错误')}")

        except Exception as e:
            logger.error(f"微信推送检查失败: {e}")

    def update_wechat_config(self, enabled: bool, interval_minutes: int = 30):
        """更新微信推送配置"""
        self.config['wechat_push_enabled'] = enabled
        self.config['wechat_push_interval_minutes'] = interval_minutes
        print(f"[配置] 微信推送: {'启用' if enabled else '禁用'}, 间隔: {interval_minutes}分钟")

    def update_config(self, new_config):
        """更新配置"""
        self.config.update(new_config)
        print(f"[配置] 配置已更新: {new_config}")


def main():
    """测试函数"""
    print("自适应预测引擎测试")
    print("=" * 40)

    config = {
        'interval_minutes': 1,
        'data_collection_seconds': 2,
        'min_data_points': 5
    }

    engine = AdaptivePredictionEngine(config)

    try:
        if engine.start_engine():
            print("引擎启动成功，运行60秒...")
            time.sleep(60)

            # 显示状态
            status = engine.get_status()
            print(f"\n系统状态:")
            print(f"  数据点: {status['data_points']}")
            print(f"  预测数: {status['predictions_count']}")
            print(f"  平均准确率: {status['performance_metrics']['average_accuracy']:.1%}")
            print(f"  置信度基准: {status['confidence_base']:.2f}")

            engine.stop_engine()
        else:
            print("引擎启动失败")

    except KeyboardInterrupt:
        print("\n用户中断")
        engine.stop_engine()


if __name__ == "__main__":
    main()
