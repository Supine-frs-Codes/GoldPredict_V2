#!/usr/bin/env python3
"""
实时自动化预测引擎
支持短周期预测和实时交易指导
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

# 机器学习库
try:
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import mean_squared_error, accuracy_score
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

# 深度学习库
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    DL_AVAILABLE = True
except ImportError:
    DL_AVAILABLE = False

from src.data.mt5_data_collector import MT5DataCollector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RealTimePredictionEngine:
    """实时预测引擎"""
    
    def __init__(self, config):
        self.config = config
        self.running = False
        self.data_queue = queue.Queue(maxsize=1000)
        self.prediction_queue = queue.Queue(maxsize=100)
        
        # 数据收集器
        self.mt5_collector = MT5DataCollector()
        
        # 预测器
        self.lightweight_predictor = LightweightPredictor()
        self.complex_predictor = ComplexPredictor() if ML_AVAILABLE else None
        self.deep_predictor = DeepLearningPredictor() if DL_AVAILABLE else None
        
        # 验证系统
        self.accuracy_tracker = AccuracyTracker()
        
        # 数据存储
        self.setup_database()
        
        # 历史数据缓存
        self.price_history = []
        self.prediction_history = []
        
        print(f"[引擎] 实时预测引擎初始化完成")
        print(f"   预测间隔: {config['interval_minutes']}分钟")
        print(f"   轻量级预测器: ✅")
        print(f"   复杂预测器: {'✅' if ML_AVAILABLE else '❌'}")
        print(f"   深度学习预测器: {'✅' if DL_AVAILABLE else '❌'}")
    
    def setup_database(self):
        """设置数据库"""
        db_path = Path("results/realtime/predictions.db")
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                current_price REAL,
                predicted_price REAL,
                prediction_type TEXT,
                signal TEXT,
                confidence REAL,
                actual_price REAL,
                accuracy REAL,
                verified_at TEXT
            )
        ''')
        
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS price_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                price REAL,
                volume REAL,
                bid REAL,
                ask REAL
            )
        ''')
        self.conn.commit()
    
    def start_engine(self):
        """启动预测引擎"""
        if self.running:
            print("[警告] 引擎已在运行中")
            return
        
        self.running = True
        print("[启动] 实时预测引擎启动")
        
        # 启动数据收集线程
        data_thread = threading.Thread(target=self._data_collection_loop, daemon=True)
        data_thread.start()
        
        # 启动预测线程
        prediction_thread = threading.Thread(target=self._prediction_loop, daemon=True)
        prediction_thread.start()
        
        # 启动验证线程
        verification_thread = threading.Thread(target=self._verification_loop, daemon=True)
        verification_thread.start()
        
        print("[成功] 所有线程已启动")
    
    def stop_engine(self):
        """停止预测引擎"""
        self.running = False
        print("[停止] 实时预测引擎已停止")
    
    def _data_collection_loop(self):
        """数据收集循环"""
        print("[数据] 数据收集线程启动")
        
        while self.running:
            try:
                if not self.mt5_collector.connect():
                    print("[错误] MT5连接失败，等待重试...")
                    time.sleep(30)
                    continue
                
                symbol = self.mt5_collector.find_gold_symbol()
                if not symbol:
                    print("[错误] 未找到黄金符号")
                    time.sleep(30)
                    continue
                
                # 获取当前价格
                current_price = self.mt5_collector.get_current_price(symbol)
                if current_price:
                    price_data = {
                        'timestamp': datetime.now().isoformat(),
                        'price': current_price['last'],
                        'volume': current_price.get('volume', 0),
                        'bid': current_price['bid'],
                        'ask': current_price['ask']
                    }
                    
                    # 添加到队列
                    if not self.data_queue.full():
                        self.data_queue.put(price_data)
                    
                    # 添加到历史数据
                    self.price_history.append(price_data)
                    if len(self.price_history) > 1000:  # 保持最近1000个数据点
                        self.price_history.pop(0)
                    
                    # 保存到数据库
                    self._save_price_data(price_data)
                    
                    print(f"[数据] {current_price['last']:.2f} | Bid: {current_price['bid']:.2f} | Ask: {current_price['ask']:.2f}")
                
                self.mt5_collector.disconnect()
                time.sleep(10)  # 每10秒获取一次数据
                
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
                
                # 检查是否到了预测时间
                if current_time - last_prediction_time >= interval_seconds:
                    if len(self.price_history) >= 20:  # 至少需要20个数据点
                        self._make_predictions()
                        last_prediction_time = current_time
                    else:
                        print(f"[等待] 数据不足，当前: {len(self.price_history)}/20")
                
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"预测循环错误: {e}")
                time.sleep(10)
    
    def _make_predictions(self):
        """执行预测"""
        try:
            print(f"\n[预测] 开始 {self.config['interval_minutes']} 分钟预测...")
            
            # 准备数据
            df = pd.DataFrame(self.price_history)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            current_price = df['price'].iloc[-1]
            current_time = datetime.now()
            
            predictions = {}
            
            # 1. 轻量级预测
            lightweight_pred = self.lightweight_predictor.predict(df)
            predictions['lightweight'] = lightweight_pred
            
            # 2. 复杂预测 (如果可用)
            if self.complex_predictor:
                complex_pred = self.complex_predictor.predict(df)
                predictions['complex'] = complex_pred
            
            # 3. 深度学习预测 (如果可用)
            if self.deep_predictor:
                deep_pred = self.deep_predictor.predict(df)
                predictions['deep'] = deep_pred
            
            # 4. 集成预测
            ensemble_pred = self._ensemble_prediction(predictions, current_price)
            
            # 5. 生成交易信号
            signal = self._generate_trading_signal(ensemble_pred, current_price)
            
            # 6. 保存预测结果
            prediction_result = {
                'timestamp': current_time.isoformat(),
                'current_price': current_price,
                'predicted_price': ensemble_pred['price'],
                'signal': signal['direction'],
                'confidence': signal['confidence'],
                'predictions': predictions,
                'target_time': (current_time + timedelta(minutes=self.config['interval_minutes'])).isoformat()
            }
            
            self.prediction_queue.put(prediction_result)
            self._save_prediction(prediction_result)
            
            print(f"[结果] 当前: ${current_price:.2f} → 预测: ${ensemble_pred['price']:.2f}")
            print(f"[信号] {signal['direction']} (置信度: {signal['confidence']:.1%})")
            
        except Exception as e:
            logger.error(f"预测执行错误: {e}")
    
    def _ensemble_prediction(self, predictions, current_price):
        """集成预测"""
        if not predictions:
            return {'price': current_price, 'confidence': 0.5}
        
        # 权重分配
        weights = {
            'lightweight': 0.3,
            'complex': 0.4,
            'deep': 0.3
        }
        
        total_weight = 0
        weighted_price = 0
        
        for pred_type, pred_data in predictions.items():
            if pred_data and pred_type in weights:
                weight = weights[pred_type]
                weighted_price += pred_data['price'] * weight
                total_weight += weight
        
        if total_weight > 0:
            final_price = weighted_price / total_weight
        else:
            final_price = current_price
        
        # 计算置信度
        confidence = min(total_weight, 1.0)
        
        return {
            'price': final_price,
            'confidence': confidence
        }
    
    def _generate_trading_signal(self, prediction, current_price):
        """生成交易信号"""
        price_change = prediction['price'] - current_price
        price_change_pct = price_change / current_price
        
        # 信号阈值
        strong_threshold = 0.002  # 0.2%
        weak_threshold = 0.0005   # 0.05%
        
        if price_change_pct > strong_threshold:
            direction = "强烈看涨"
            confidence = min(0.9, prediction['confidence'] + 0.2)
        elif price_change_pct > weak_threshold:
            direction = "看涨"
            confidence = prediction['confidence']
        elif price_change_pct < -strong_threshold:
            direction = "强烈看跌"
            confidence = min(0.9, prediction['confidence'] + 0.2)
        elif price_change_pct < -weak_threshold:
            direction = "看跌"
            confidence = prediction['confidence']
        else:
            direction = "横盘"
            confidence = max(0.3, prediction['confidence'] - 0.2)
        
        return {
            'direction': direction,
            'confidence': confidence,
            'price_change': price_change,
            'price_change_pct': price_change_pct
        }
    
    def _verification_loop(self):
        """验证循环"""
        print("[验证] 验证线程启动")
        
        while self.running:
            try:
                # 检查需要验证的预测
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
                pred_id, timestamp, current_price, predicted_price, pred_type, signal, confidence, _, _, _ = row
                
                # 获取实际价格
                actual_price = self._get_actual_price_at_time(timestamp)
                if actual_price:
                    # 计算准确率
                    accuracy = self._calculate_accuracy(predicted_price, actual_price, current_price)
                    
                    # 更新数据库
                    self.conn.execute('''
                        UPDATE predictions 
                        SET actual_price = ?, accuracy = ?, verified_at = ?
                        WHERE id = ?
                    ''', (actual_price, accuracy, current_time.isoformat(), pred_id))
                    
                    self.conn.commit()
                    
                    print(f"[验证] 预测ID {pred_id}: 准确率 {accuracy:.1%}")
            
        except Exception as e:
            logger.error(f"验证错误: {e}")
    
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
    
    def _calculate_accuracy(self, predicted, actual, baseline):
        """计算预测准确率"""
        if actual == baseline:
            return 0.5  # 价格没变化
        
        predicted_direction = 1 if predicted > baseline else -1
        actual_direction = 1 if actual > baseline else -1
        
        # 方向准确性
        direction_correct = predicted_direction == actual_direction
        
        # 价格准确性
        predicted_change = abs(predicted - baseline)
        actual_change = abs(actual - baseline)
        price_accuracy = 1 - min(abs(predicted_change - actual_change) / actual_change, 1) if actual_change > 0 else 0.5
        
        # 综合准确率
        if direction_correct:
            return 0.5 + 0.5 * price_accuracy
        else:
            return 0.5 * (1 - price_accuracy)
    
    def _save_price_data(self, price_data):
        """保存价格数据"""
        try:
            self.conn.execute('''
                INSERT INTO price_data (timestamp, price, volume, bid, ask)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                price_data['timestamp'],
                price_data['price'],
                price_data['volume'],
                price_data['bid'],
                price_data['ask']
            ))
            self.conn.commit()
        except Exception as e:
            logger.error(f"保存价格数据错误: {e}")
    
    def _save_prediction(self, prediction):
        """保存预测结果"""
        try:
            self.conn.execute('''
                INSERT INTO predictions (timestamp, current_price, predicted_price, prediction_type, signal, confidence)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                prediction['timestamp'],
                prediction['current_price'],
                prediction['predicted_price'],
                'ensemble',
                prediction['signal'],
                prediction['confidence']
            ))
            self.conn.commit()
        except Exception as e:
            logger.error(f"保存预测结果错误: {e}")
    
    def get_latest_prediction(self):
        """获取最新预测"""
        if not self.prediction_queue.empty():
            return self.prediction_queue.get()
        return None
    
    def get_accuracy_stats(self):
        """获取准确率统计"""
        try:
            cursor = self.conn.execute('''
                SELECT 
                    COUNT(*) as total,
                    AVG(accuracy) as avg_accuracy,
                    COUNT(CASE WHEN accuracy > 0.6 THEN 1 END) as good_predictions
                FROM predictions 
                WHERE verified_at IS NOT NULL
                AND datetime(timestamp) >= datetime('now', '-24 hours')
            ''')
            
            result = cursor.fetchone()
            if result and result[0] > 0:
                return {
                    'total_predictions': result[0],
                    'average_accuracy': result[1],
                    'good_prediction_rate': result[2] / result[0] if result[0] > 0 else 0
                }
        except Exception as e:
            logger.error(f"获取统计错误: {e}")
        
        return {'total_predictions': 0, 'average_accuracy': 0, 'good_prediction_rate': 0}


class LightweightPredictor:
    """轻量级预测器 - 基于技术指标的快速预测"""

    def __init__(self):
        self.name = "轻量级预测器"

    def predict(self, df):
        """执行轻量级预测"""
        try:
            if len(df) < 10:
                return None

            # 计算技术指标
            df = self._calculate_indicators(df.copy())

            current_price = df['price'].iloc[-1]

            # 1. 移动平均趋势
            ma_5 = df['ma_5'].iloc[-1]
            ma_10 = df['ma_10'].iloc[-1]
            ma_trend = (ma_5 - ma_10) / ma_10 if ma_10 != 0 else 0

            # 2. 价格动量
            price_momentum = (current_price - df['price'].iloc[-5]) / df['price'].iloc[-5] if len(df) >= 5 else 0

            # 3. 波动率
            returns = df['price'].pct_change().dropna()
            volatility = returns.std() if len(returns) > 1 else 0

            # 4. RSI信号
            rsi = self._calculate_rsi(df['price'])
            rsi_signal = (50 - rsi) / 100 if rsi else 0

            # 5. 价格位置 (相对于近期高低点)
            recent_high = df['price'].tail(10).max()
            recent_low = df['price'].tail(10).min()
            price_position = (current_price - recent_low) / (recent_high - recent_low) if recent_high != recent_low else 0.5

            # 综合预测
            trend_weight = 0.3
            momentum_weight = 0.25
            rsi_weight = 0.2
            position_weight = 0.15
            volatility_weight = 0.1

            # 计算预测变化
            predicted_change = (
                ma_trend * trend_weight +
                price_momentum * momentum_weight +
                rsi_signal * rsi_weight +
                (0.5 - price_position) * position_weight * 0.1 +
                -volatility * volatility_weight * 0.5  # 高波动性降低预测幅度
            )

            # 限制预测变化幅度
            predicted_change = max(-0.01, min(0.01, predicted_change))  # 限制在±1%

            predicted_price = current_price * (1 + predicted_change)

            # 计算置信度
            confidence = self._calculate_confidence(ma_trend, price_momentum, volatility, rsi)

            return {
                'price': predicted_price,
                'confidence': confidence,
                'components': {
                    'ma_trend': ma_trend,
                    'momentum': price_momentum,
                    'rsi_signal': rsi_signal,
                    'volatility': volatility
                }
            }

        except Exception as e:
            logger.error(f"轻量级预测错误: {e}")
            return None

    def _calculate_indicators(self, df):
        """计算技术指标"""
        # 移动平均
        df['ma_5'] = df['price'].rolling(5).mean()
        df['ma_10'] = df['price'].rolling(10).mean()

        # 填充NaN
        df = df.fillna(method='bfill').fillna(method='ffill')

        return df

    def _calculate_rsi(self, prices, period=14):
        """计算RSI"""
        try:
            if len(prices) < period + 1:
                return 50  # 默认中性值

            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50
        except:
            return 50

    def _calculate_confidence(self, ma_trend, momentum, volatility, rsi):
        """计算预测置信度"""
        # 趋势一致性
        trend_consistency = 1 - abs(ma_trend - momentum) if abs(ma_trend - momentum) < 1 else 0

        # RSI极值
        rsi_extreme = max(0, (abs(rsi - 50) - 20) / 30) if rsi else 0

        # 波动率影响 (低波动率 = 高置信度)
        volatility_factor = max(0, 1 - volatility * 10)

        # 综合置信度
        confidence = (trend_consistency * 0.4 + rsi_extreme * 0.3 + volatility_factor * 0.3)

        return max(0.3, min(0.9, confidence))


class ComplexPredictor:
    """复杂预测器 - 基于机器学习的预测"""

    def __init__(self):
        self.name = "复杂预测器"
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False

        if ML_AVAILABLE:
            self.model = GradientBoostingRegressor(
                n_estimators=50,
                max_depth=3,
                learning_rate=0.1,
                random_state=42
            )

    def predict(self, df):
        """执行复杂预测"""
        try:
            if not ML_AVAILABLE or len(df) < 20:
                return None

            # 准备特征
            features = self._prepare_features(df.copy())
            if features is None or len(features) < 10:
                return None

            # 训练模型 (如果需要)
            if not self.is_trained:
                self._train_model(features)

            # 预测
            if self.is_trained:
                latest_features = features.iloc[-1:].values
                latest_features_scaled = self.scaler.transform(latest_features)

                predicted_price = self.model.predict(latest_features_scaled)[0]

                # 计算置信度
                confidence = self._calculate_ml_confidence(features)

                return {
                    'price': predicted_price,
                    'confidence': confidence,
                    'model_type': 'GradientBoosting'
                }

        except Exception as e:
            logger.error(f"复杂预测错误: {e}")

        return None

    def _prepare_features(self, df):
        """准备机器学习特征"""
        try:
            # 技术指标
            df['ma_5'] = df['price'].rolling(5).mean()
            df['ma_10'] = df['price'].rolling(10).mean()
            df['ma_20'] = df['price'].rolling(20).mean()

            # 价格变化
            df['price_change_1'] = df['price'].pct_change(1)
            df['price_change_3'] = df['price'].pct_change(3)
            df['price_change_5'] = df['price'].pct_change(5)

            # 波动率
            df['volatility_5'] = df['price'].rolling(5).std()
            df['volatility_10'] = df['price'].rolling(10).std()

            # 价格位置
            df['high_5'] = df['price'].rolling(5).max()
            df['low_5'] = df['price'].rolling(5).min()
            df['price_position'] = (df['price'] - df['low_5']) / (df['high_5'] - df['low_5'])

            # 成交量特征 (如果有)
            if 'volume' in df.columns:
                df['volume_ma_5'] = df['volume'].rolling(5).mean()
                df['volume_ratio'] = df['volume'] / df['volume_ma_5']
            else:
                df['volume_ratio'] = 1.0

            # 选择特征列
            feature_columns = [
                'ma_5', 'ma_10', 'ma_20',
                'price_change_1', 'price_change_3', 'price_change_5',
                'volatility_5', 'volatility_10',
                'price_position', 'volume_ratio'
            ]

            # 创建目标变量 (下一个价格)
            df['target'] = df['price'].shift(-1)

            # 删除NaN行
            df = df.dropna()

            if len(df) < 10:
                return None

            return df[feature_columns + ['target']]

        except Exception as e:
            logger.error(f"特征准备错误: {e}")
            return None

    def _train_model(self, features):
        """训练模型"""
        try:
            if len(features) < 10:
                return

            X = features.iloc[:-1, :-1].values  # 除了最后一行和目标列
            y = features.iloc[:-1, -1].values   # 目标列，除了最后一行

            # 标准化特征
            X_scaled = self.scaler.fit_transform(X)

            # 训练模型
            self.model.fit(X_scaled, y)
            self.is_trained = True

            print(f"[训练] 复杂预测器训练完成，样本数: {len(X)}")

        except Exception as e:
            logger.error(f"模型训练错误: {e}")

    def _calculate_ml_confidence(self, features):
        """计算机器学习置信度"""
        try:
            # 基于特征稳定性计算置信度
            recent_volatility = features['volatility_5'].iloc[-5:].mean()
            price_trend_consistency = abs(features['price_change_1'].iloc[-5:].mean())

            # 数据质量评分
            data_quality = min(1.0, len(features) / 50)  # 数据越多质量越高

            # 综合置信度
            confidence = (
                (1 - min(recent_volatility * 100, 1)) * 0.4 +  # 低波动性
                min(price_trend_consistency * 10, 1) * 0.3 +   # 趋势一致性
                data_quality * 0.3                              # 数据质量
            )

            return max(0.4, min(0.8, confidence))

        except:
            return 0.5


class DeepLearningPredictor:
    """深度学习预测器"""

    def __init__(self):
        self.name = "深度学习预测器"
        self.model = None
        self.is_trained = False

        if DL_AVAILABLE:
            self.model = self._create_model()

    def _create_model(self):
        """创建神经网络模型"""
        class PricePredictor(nn.Module):
            def __init__(self, input_size=10):
                super(PricePredictor, self).__init__()
                self.lstm = nn.LSTM(input_size, 32, batch_first=True)
                self.fc1 = nn.Linear(32, 16)
                self.fc2 = nn.Linear(16, 1)
                self.dropout = nn.Dropout(0.2)

            def forward(self, x):
                lstm_out, _ = self.lstm(x)
                x = lstm_out[:, -1, :]  # 取最后一个时间步
                x = torch.relu(self.fc1(x))
                x = self.dropout(x)
                x = self.fc2(x)
                return x

        return PricePredictor()

    def predict(self, df):
        """执行深度学习预测"""
        try:
            if not DL_AVAILABLE or len(df) < 30:
                return None

            # 准备序列数据
            sequences = self._prepare_sequences(df.copy())
            if sequences is None:
                return None

            # 训练模型 (如果需要)
            if not self.is_trained and len(sequences) > 20:
                self._train_model(sequences)

            # 预测
            if self.is_trained:
                latest_sequence = sequences[-1:].unsqueeze(0)  # 添加batch维度

                self.model.eval()
                with torch.no_grad():
                    predicted_price = self.model(latest_sequence).item()

                return {
                    'price': predicted_price,
                    'confidence': 0.7,  # 深度学习模型的基础置信度
                    'model_type': 'LSTM'
                }

        except Exception as e:
            logger.error(f"深度学习预测错误: {e}")

        return None

    def _prepare_sequences(self, df, sequence_length=10):
        """准备序列数据"""
        try:
            # 标准化价格
            prices = df['price'].values
            normalized_prices = (prices - prices.mean()) / prices.std()

            # 创建序列
            sequences = []
            for i in range(len(normalized_prices) - sequence_length):
                seq = normalized_prices[i:i+sequence_length]
                sequences.append(seq)

            if len(sequences) < 5:
                return None

            return torch.FloatTensor(sequences)

        except Exception as e:
            logger.error(f"序列准备错误: {e}")
            return None

    def _train_model(self, sequences):
        """训练深度学习模型"""
        try:
            if len(sequences) < 20:
                return

            # 准备训练数据
            X = sequences[:-1]  # 输入序列
            y = sequences[1:, -1]  # 目标值 (下一个价格)

            # 添加特征维度
            X = X.unsqueeze(-1)

            # 训练设置
            criterion = nn.MSELoss()
            optimizer = optim.Adam(self.model.parameters(), lr=0.001)

            # 简单训练循环
            self.model.train()
            for epoch in range(50):  # 快速训练
                optimizer.zero_grad()
                outputs = self.model(X).squeeze()
                loss = criterion(outputs, y)
                loss.backward()
                optimizer.step()

            self.is_trained = True
            print(f"[训练] 深度学习预测器训练完成，损失: {loss.item():.6f}")

        except Exception as e:
            logger.error(f"深度学习训练错误: {e}")


class AccuracyTracker:
    """准确率跟踪器"""

    def __init__(self):
        self.predictions = []
        self.accuracies = []

    def add_prediction(self, prediction, actual):
        """添加预测结果"""
        self.predictions.append(prediction)

        # 计算准确率
        accuracy = self._calculate_accuracy(prediction, actual)
        self.accuracies.append(accuracy)

        # 保持最近100个结果
        if len(self.predictions) > 100:
            self.predictions.pop(0)
            self.accuracies.pop(0)

    def _calculate_accuracy(self, prediction, actual):
        """计算准确率"""
        # 方向准确性
        pred_direction = 1 if prediction['price'] > prediction['current_price'] else -1
        actual_direction = 1 if actual > prediction['current_price'] else -1

        direction_correct = pred_direction == actual_direction

        # 价格准确性
        pred_change = abs(prediction['price'] - prediction['current_price'])
        actual_change = abs(actual - prediction['current_price'])

        if actual_change > 0:
            price_accuracy = 1 - min(abs(pred_change - actual_change) / actual_change, 1)
        else:
            price_accuracy = 0.5

        # 综合准确率
        if direction_correct:
            return 0.5 + 0.5 * price_accuracy
        else:
            return 0.5 * (1 - price_accuracy)

    def get_stats(self):
        """获取统计信息"""
        if not self.accuracies:
            return {'count': 0, 'average': 0, 'recent': 0}

        return {
            'count': len(self.accuracies),
            'average': np.mean(self.accuracies),
            'recent': np.mean(self.accuracies[-10:]) if len(self.accuracies) >= 10 else np.mean(self.accuracies)
        }
