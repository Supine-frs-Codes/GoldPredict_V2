#!/usr/bin/env python3
"""
简化版实时预测系统
不依赖复杂的机器学习库，专注于技术分析
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
import argparse

from src.data.mt5_data_collector import MT5DataCollector
from improved_mt5_manager import ImprovedMT5Manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleRealTimePrediction:
    """简化版实时预测系统"""
    
    def __init__(self, interval_minutes=5, data_collection_seconds=5, min_data_points=10):
        self.interval_minutes = interval_minutes
        self.data_collection_seconds = data_collection_seconds  # 数据收集间隔
        self.min_data_points = min_data_points  # 最少数据点数
        self.running = False
        self.mt5_manager = ImprovedMT5Manager()

        # 数据存储
        self.price_history = []
        self.prediction_history = []

        # 设置数据库
        self.setup_database()

        print(f"[系统] 简化版实时预测系统初始化")
        print(f"   预测间隔: {interval_minutes}分钟")
        print(f"   数据收集间隔: {data_collection_seconds}秒")
        print(f"   最少数据点: {min_data_points}个")
        print(f"   数据源: MetaTrader 5")
    
    def setup_database(self):
        """设置数据库"""
        db_path = Path("results/realtime/simple_predictions.db")
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
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
                method TEXT
            )
        ''')
        
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS price_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                price REAL,
                bid REAL,
                ask REAL
            )
        ''')
        self.conn.commit()
    
    def start_prediction(self):
        """启动预测系统"""
        if self.running:
            print("[警告] 系统已在运行中")
            return
        
        self.running = True
        print("[启动] 简化版实时预测系统启动")
        
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
    
    def stop_prediction(self):
        """停止预测系统"""
        self.running = False
        print("[停止] 简化版实时预测系统已停止")

        # 清理MT5连接
        try:
            self.mt5_manager.cleanup()
        except Exception as e:
            logger.error(f"清理MT5连接时出错: {e}")
    
    def _data_collection_loop(self):
        """数据收集循环 - 使用改进的连接管理"""
        print("[数据] 数据收集线程启动")

        while self.running:
            try:
                # 获取黄金符号
                symbol = self.mt5_manager.get_gold_symbol()
                if not symbol:
                    print("[错误] 未找到黄金符号，等待重试...")
                    time.sleep(30)
                    continue

                # 获取当前价格 (内置连接管理和重试机制)
                current_price = self.mt5_manager.get_current_price(symbol)
                if current_price:
                    # 使用bid价格作为主要价格，如果last为0
                    main_price = current_price['last'] if current_price['last'] > 0 else current_price['bid']

                    price_data = {
                        'timestamp': datetime.now().isoformat(),
                        'price': main_price,
                        'bid': current_price['bid'],
                        'ask': current_price['ask']
                    }

                    # 添加到历史数据
                    self.price_history.append(price_data)
                    if len(self.price_history) > 500:  # 保持最近500个数据点
                        self.price_history.pop(0)

                    # 保存到数据库
                    self._save_price_data(price_data)

                    print(f"[数据] {main_price:.2f} | 历史数据: {len(self.price_history)}")
                else:
                    print("[警告] 价格获取失败，等待重试...")
                    time.sleep(2)  # 短暂等待后重试

                time.sleep(self.data_collection_seconds)  # 可配置的数据收集间隔

            except Exception as e:
                logger.error(f"数据收集错误: {e}")
                time.sleep(30)
    
    def _prediction_loop(self):
        """预测循环"""
        print("[预测] 预测线程启动")
        
        last_prediction_time = 0
        interval_seconds = self.interval_minutes * 60
        
        while self.running:
            try:
                current_time = time.time()
                
                # 检查是否到了预测时间
                if current_time - last_prediction_time >= interval_seconds:
                    if len(self.price_history) >= self.min_data_points:  # 可配置的最少数据点
                        self._make_prediction()
                        last_prediction_time = current_time
                    else:
                        print(f"[等待] 数据不足，当前: {len(self.price_history)}/{self.min_data_points}")
                
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"预测循环错误: {e}")
                time.sleep(10)
    
    def _make_prediction(self):
        """执行预测"""
        try:
            print(f"\n[预测] 开始 {self.interval_minutes} 分钟预测...")
            
            # 准备数据
            df = pd.DataFrame(self.price_history)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            current_price = df['price'].iloc[-1]
            current_time = datetime.now()
            
            # 执行技术分析预测
            prediction_result = self._technical_analysis_prediction(df)
            
            if prediction_result:
                # 生成交易信号
                signal = self._generate_signal(prediction_result, current_price)
                
                # 保存预测结果
                prediction_data = {
                    'timestamp': current_time.isoformat(),
                    'current_price': current_price,
                    'predicted_price': prediction_result['price'],
                    'signal': signal['direction'],
                    'confidence': prediction_result['confidence'],
                    'method': 'technical_analysis',
                    'target_time': (current_time + timedelta(minutes=self.interval_minutes)).isoformat()
                }
                
                self.prediction_history.append(prediction_data)
                self._save_prediction(prediction_data)
                
                print(f"[结果] 当前: ${current_price:.2f} → 预测: ${prediction_result['price']:.2f}")
                print(f"[信号] {signal['direction']} (置信度: {prediction_result['confidence']:.1%})")
                
                # 保存到JSON文件供Web界面读取
                self._save_latest_prediction(prediction_data)
            
        except Exception as e:
            logger.error(f"预测执行错误: {e}")
    
    def _technical_analysis_prediction(self, df):
        """技术分析预测"""
        try:
            current_price = df['price'].iloc[-1]
            
            # 1. 移动平均线分析
            df['ma_5'] = df['price'].rolling(5).mean()
            df['ma_10'] = df['price'].rolling(10).mean()
            df['ma_20'] = df['price'].rolling(20).mean()
            
            ma_5 = df['ma_5'].iloc[-1]
            ma_10 = df['ma_10'].iloc[-1]
            ma_20 = df['ma_20'].iloc[-1]
            
            # 趋势强度
            short_trend = (ma_5 - ma_10) / ma_10 if ma_10 != 0 else 0
            long_trend = (ma_10 - ma_20) / ma_20 if ma_20 != 0 else 0
            
            # 2. 价格动量
            if len(df) >= 10:
                momentum_5 = (current_price - df['price'].iloc[-5]) / df['price'].iloc[-5]
                momentum_10 = (current_price - df['price'].iloc[-10]) / df['price'].iloc[-10]
            else:
                momentum_5 = momentum_10 = 0
            
            # 3. 波动率
            returns = df['price'].pct_change().dropna()
            volatility = returns.std() if len(returns) > 1 else 0
            
            # 4. 支撑阻力位
            recent_high = df['price'].tail(20).max()
            recent_low = df['price'].tail(20).min()
            price_position = (current_price - recent_low) / (recent_high - recent_low) if recent_high != recent_low else 0.5
            
            # 5. RSI计算
            rsi = self._calculate_rsi(df['price'])
            rsi_signal = (50 - rsi) / 100 if rsi else 0
            
            # 综合预测
            trend_component = (short_trend * 0.6 + long_trend * 0.4) * 0.3
            momentum_component = (momentum_5 * 0.7 + momentum_10 * 0.3) * 0.25
            rsi_component = rsi_signal * 0.2
            position_component = (0.5 - price_position) * 0.15
            volatility_component = -volatility * 0.1  # 高波动性降低预测幅度
            
            # 总预测变化
            total_change = (
                trend_component + 
                momentum_component + 
                rsi_component + 
                position_component + 
                volatility_component
            )
            
            # 限制预测变化幅度
            total_change = max(-0.005, min(0.005, total_change))  # 限制在±0.5%
            
            predicted_price = current_price * (1 + total_change)
            
            # 计算置信度
            confidence = self._calculate_confidence(
                short_trend, momentum_5, volatility, rsi, price_position
            )
            
            return {
                'price': predicted_price,
                'confidence': confidence,
                'components': {
                    'trend': trend_component,
                    'momentum': momentum_component,
                    'rsi': rsi_component,
                    'position': position_component,
                    'volatility': volatility_component
                }
            }
            
        except Exception as e:
            logger.error(f"技术分析错误: {e}")
            return None
    
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
    
    def _calculate_confidence(self, trend, momentum, volatility, rsi, position):
        """计算预测置信度"""
        # 趋势一致性
        trend_consistency = 1 - abs(trend - momentum) if abs(trend - momentum) < 1 else 0
        
        # RSI极值
        rsi_extreme = max(0, (abs(rsi - 50) - 20) / 30) if rsi else 0
        
        # 价格位置
        position_factor = 1 - abs(position - 0.5) * 2  # 中间位置置信度更高
        
        # 波动率影响
        volatility_factor = max(0, 1 - volatility * 20)
        
        # 综合置信度
        confidence = (
            trend_consistency * 0.3 + 
            rsi_extreme * 0.25 + 
            position_factor * 0.25 + 
            volatility_factor * 0.2
        )
        
        return max(0.3, min(0.9, confidence))
    
    def _generate_signal(self, prediction, current_price):
        """生成交易信号"""
        price_change = prediction['price'] - current_price
        price_change_pct = price_change / current_price
        
        # 信号阈值
        strong_threshold = 0.002  # 0.2%
        weak_threshold = 0.0005   # 0.05%
        
        if price_change_pct > strong_threshold:
            direction = "强烈看涨"
        elif price_change_pct > weak_threshold:
            direction = "看涨"
        elif price_change_pct < -strong_threshold:
            direction = "强烈看跌"
        elif price_change_pct < -weak_threshold:
            direction = "看跌"
        else:
            direction = "横盘"
        
        return {
            'direction': direction,
            'price_change': price_change,
            'price_change_pct': price_change_pct
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
            '''.format(self.interval_minutes), (current_time.isoformat(),))
            
            unverified = cursor.fetchall()
            
            for row in unverified:
                pred_id, timestamp, current_price, predicted_price, signal, confidence, _, _, _, method = row
                
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
        target_time += timedelta(minutes=self.interval_minutes)
        
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
            return 0.5
        
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
                INSERT INTO price_data (timestamp, price, bid, ask)
                VALUES (?, ?, ?, ?)
            ''', (
                price_data['timestamp'],
                price_data['price'],
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
                INSERT INTO predictions (timestamp, current_price, predicted_price, signal, confidence, method)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                prediction['timestamp'],
                prediction['current_price'],
                prediction['predicted_price'],
                prediction['signal'],
                prediction['confidence'],
                prediction['method']
            ))
            self.conn.commit()
        except Exception as e:
            logger.error(f"保存预测结果错误: {e}")
    
    def _save_latest_prediction(self, prediction):
        """保存最新预测到JSON文件"""
        try:
            output_path = Path("results/realtime/latest_prediction.json")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(prediction, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存最新预测错误: {e}")
    
    def get_stats(self):
        """获取统计信息"""
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


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='简化版实时预测系统')
    parser.add_argument('--interval', type=int, default=5, help='预测间隔(分钟)')
    parser.add_argument('--duration', type=int, default=0, help='运行时长(分钟)，0表示无限运行')
    parser.add_argument('--data-interval', type=int, default=5, help='数据收集间隔(秒)')
    parser.add_argument('--min-data', type=int, default=10, help='最少数据点数')
    parser.add_argument('--fast-mode', action='store_true', help='快速模式(2秒收集间隔，5个数据点)')

    args = parser.parse_args()

    # 快速模式配置
    if args.fast_mode:
        data_interval = 2
        min_data = 5
        print(f"[模式] 快速模式启用")
    else:
        data_interval = args.data_interval
        min_data = args.min_data

    print(f"简化版实时预测系统")
    print("=" * 40)

    try:
        predictor = SimpleRealTimePrediction(
            interval_minutes=args.interval,
            data_collection_seconds=data_interval,
            min_data_points=min_data
        )
        predictor.start_prediction()
        
        if args.duration > 0:
            print(f"[运行] 系统将运行 {args.duration} 分钟")
            time.sleep(args.duration * 60)
            predictor.stop_prediction()
        else:
            print("[运行] 系统无限运行，按Ctrl+C停止")
            try:
                while predictor.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n[停止] 用户中断")
                predictor.stop_prediction()
        
        # 显示统计信息
        stats = predictor.get_stats()
        print(f"\n[统计] 总预测数: {stats['total_predictions']}")
        print(f"[统计] 平均准确率: {stats['average_accuracy']:.1%}")
        print(f"[统计] 优秀预测率: {stats['good_prediction_rate']:.1%}")
        
    except Exception as e:
        print(f"[错误] 系统错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
