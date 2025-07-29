#!/usr/bin/env python3
"""
统一数据管理系统
集中管理所有预测系统的数据存储、查询和同步
"""

import sqlite3
import json
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
import threading
import time

logger = logging.getLogger(__name__)


class UnifiedDataManager:
    """统一数据管理器"""
    
    def __init__(self, db_path: str = "results/unified_data.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self.lock = threading.Lock()
        
        self._init_database()
        print(f"[数据管理] 统一数据管理系统初始化完成")
        print(f"   数据库路径: {self.db_path}")
    
    def _init_database(self):
        """初始化数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 系统状态表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS system_status (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        system_name TEXT NOT NULL,
                        status TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        details TEXT
                    )
                ''')
                
                # 预测结果表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS predictions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        system_name TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        current_price REAL,
                        predicted_price REAL,
                        signal TEXT,
                        confidence REAL,
                        accuracy REAL,
                        details TEXT
                    )
                ''')
                
                # 价格数据表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS price_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        symbol TEXT DEFAULT 'XAUUSD',
                        price REAL NOT NULL,
                        high REAL,
                        low REAL,
                        volume INTEGER,
                        source TEXT
                    )
                ''')
                
                # 交易记录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS trading_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        ticket INTEGER,
                        symbol TEXT,
                        type TEXT,
                        volume REAL,
                        open_price REAL,
                        close_price REAL,
                        profit REAL,
                        commission REAL,
                        swap REAL,
                        comment TEXT
                    )
                ''')
                
                # 系统性能表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS system_performance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        system_name TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        total_predictions INTEGER DEFAULT 0,
                        correct_predictions INTEGER DEFAULT 0,
                        accuracy_rate REAL DEFAULT 0.0,
                        avg_confidence REAL DEFAULT 0.0,
                        performance_score REAL DEFAULT 0.0
                    )
                ''')
                
                # 配置历史表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS config_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        system_name TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        config_data TEXT NOT NULL,
                        version INTEGER DEFAULT 1
                    )
                ''')
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
    
    def save_system_status(self, system_name: str, status: str, details: Dict = None):
        """保存系统状态"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO system_status (system_name, status, details)
                        VALUES (?, ?, ?)
                    ''', (system_name, status, json.dumps(details) if details else None))
                    conn.commit()
        except Exception as e:
            logger.error(f"保存系统状态失败: {e}")
    
    def save_prediction(self, system_name: str, prediction_data: Dict):
        """保存预测结果"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO predictions (
                            system_name, current_price, predicted_price, 
                            signal, confidence, details
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        system_name,
                        prediction_data.get('current_price'),
                        prediction_data.get('predicted_price'),
                        prediction_data.get('signal'),
                        prediction_data.get('confidence'),
                        json.dumps(prediction_data)
                    ))
                    conn.commit()
        except Exception as e:
            logger.error(f"保存预测结果失败: {e}")
    
    def save_price_data(self, price: float, symbol: str = 'XAUUSD', 
                       high: float = None, low: float = None, 
                       volume: int = None, source: str = 'MT5'):
        """保存价格数据"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO price_data (symbol, price, high, low, volume, source)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (symbol, price, high, low, volume, source))
                    conn.commit()
        except Exception as e:
            logger.error(f"保存价格数据失败: {e}")
    
    def save_trading_record(self, trading_data: Dict):
        """保存交易记录"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO trading_records (
                            ticket, symbol, type, volume, open_price, 
                            close_price, profit, commission, swap, comment
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        trading_data.get('ticket'),
                        trading_data.get('symbol'),
                        trading_data.get('type'),
                        trading_data.get('volume'),
                        trading_data.get('open_price'),
                        trading_data.get('close_price'),
                        trading_data.get('profit'),
                        trading_data.get('commission'),
                        trading_data.get('swap'),
                        trading_data.get('comment')
                    ))
                    conn.commit()
        except Exception as e:
            logger.error(f"保存交易记录失败: {e}")
    
    def update_system_performance(self, system_name: str, performance_data: Dict):
        """更新系统性能"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO system_performance (
                            system_name, total_predictions, correct_predictions,
                            accuracy_rate, avg_confidence, performance_score
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        system_name,
                        performance_data.get('total_predictions', 0),
                        performance_data.get('correct_predictions', 0),
                        performance_data.get('accuracy_rate', 0.0),
                        performance_data.get('avg_confidence', 0.0),
                        performance_data.get('performance_score', 0.0)
                    ))
                    conn.commit()
        except Exception as e:
            logger.error(f"更新系统性能失败: {e}")
    
    def get_recent_predictions(self, system_name: str = None, limit: int = 100) -> List[Dict]:
        """获取最近的预测结果"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if system_name:
                    cursor.execute('''
                        SELECT * FROM predictions 
                        WHERE system_name = ?
                        ORDER BY timestamp DESC 
                        LIMIT ?
                    ''', (system_name, limit))
                else:
                    cursor.execute('''
                        SELECT * FROM predictions 
                        ORDER BY timestamp DESC 
                        LIMIT ?
                    ''', (limit,))
                
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"获取预测结果失败: {e}")
            return []
    
    def get_price_history(self, hours: int = 24, symbol: str = 'XAUUSD') -> List[Dict]:
        """获取价格历史"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                start_time = datetime.now() - timedelta(hours=hours)
                cursor.execute('''
                    SELECT * FROM price_data 
                    WHERE symbol = ? AND timestamp >= ?
                    ORDER BY timestamp ASC
                ''', (symbol, start_time.isoformat()))
                
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"获取价格历史失败: {e}")
            return []
    
    def get_system_performance_history(self, system_name: str = None, days: int = 7) -> List[Dict]:
        """获取系统性能历史"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                start_time = datetime.now() - timedelta(days=days)
                
                if system_name:
                    cursor.execute('''
                        SELECT * FROM system_performance 
                        WHERE system_name = ? AND timestamp >= ?
                        ORDER BY timestamp ASC
                    ''', (system_name, start_time.isoformat()))
                else:
                    cursor.execute('''
                        SELECT * FROM system_performance 
                        WHERE timestamp >= ?
                        ORDER BY timestamp ASC
                    ''', (start_time.isoformat(),))
                
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"获取性能历史失败: {e}")
            return []
    
    def get_trading_summary(self, days: int = 30) -> Dict:
        """获取交易汇总"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                start_time = datetime.now() - timedelta(days=days)
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_trades,
                        SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END) as winning_trades,
                        SUM(profit) as total_profit,
                        AVG(profit) as avg_profit,
                        MAX(profit) as max_profit,
                        MIN(profit) as min_profit
                    FROM trading_records 
                    WHERE timestamp >= ?
                ''', (start_time.isoformat(),))
                
                result = cursor.fetchone()
                if result:
                    return {
                        'total_trades': result[0] or 0,
                        'winning_trades': result[1] or 0,
                        'total_profit': result[2] or 0.0,
                        'avg_profit': result[3] or 0.0,
                        'max_profit': result[4] or 0.0,
                        'min_profit': result[5] or 0.0,
                        'win_rate': (result[1] / max(result[0], 1)) * 100 if result[0] else 0
                    }
                
        except Exception as e:
            logger.error(f"获取交易汇总失败: {e}")
        
        return {
            'total_trades': 0, 'winning_trades': 0, 'total_profit': 0.0,
            'avg_profit': 0.0, 'max_profit': 0.0, 'min_profit': 0.0, 'win_rate': 0.0
        }
    
    def export_data(self, table_name: str, start_date: str = None, end_date: str = None) -> str:
        """导出数据到CSV"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = f"SELECT * FROM {table_name}"
                params = []
                
                if start_date and end_date:
                    query += " WHERE timestamp BETWEEN ? AND ?"
                    params = [start_date, end_date]
                
                df = pd.read_sql_query(query, conn, params=params)
                
                export_path = f"exports/{table_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                Path("exports").mkdir(exist_ok=True)
                df.to_csv(export_path, index=False)
                
                return export_path
                
        except Exception as e:
            logger.error(f"导出数据失败: {e}")
            return ""
    
    def backup_database(self) -> str:
        """备份数据库"""
        try:
            backup_path = f"backups/unified_data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            Path("backups").mkdir(exist_ok=True)
            
            # 复制数据库文件
            import shutil
            shutil.copy2(self.db_path, backup_path)
            
            return backup_path
            
        except Exception as e:
            logger.error(f"备份数据库失败: {e}")
            return ""
    
    def get_dashboard_data(self) -> Dict:
        """获取仪表板数据"""
        try:
            # 获取最新价格
            price_data = self.get_price_history(hours=1)
            current_price = price_data[-1]['price'] if price_data else 0
            
            # 获取系统性能
            performance_data = self.get_system_performance_history(days=1)
            
            # 获取交易汇总
            trading_summary = self.get_trading_summary(days=7)
            
            # 获取最新预测
            recent_predictions = self.get_recent_predictions(limit=10)
            
            return {
                'current_price': current_price,
                'price_history': price_data[-50:] if price_data else [],  # 最近50个价格点
                'performance_data': performance_data,
                'trading_summary': trading_summary,
                'recent_predictions': recent_predictions,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取仪表板数据失败: {e}")
            return {}

    def get_realtime_price_data(self) -> Dict:
        """获取实时价格数据（专门为实时预测系统）"""
        try:
            # 尝试从MT5获取实时数据
            current_price = self._get_mt5_current_price()

            # 获取最近的价格历史
            price_history = self.get_price_history(hours=1)

            if not price_history:
                price_history = self._generate_realtime_mock_data()

            return {
                'current_price': current_price,
                'price_history': price_history,
                'timestamp': datetime.now().isoformat(),
                'symbol': 'XAUUSD'
            }

        except Exception as e:
            logger.error(f"获取实时价格数据失败: {e}")
            return self._get_fallback_realtime_data()

    def _get_mt5_current_price(self) -> float:
        """从MT5获取当前价格"""
        try:
            import MetaTrader5 as mt5

            if not mt5.initialize():
                raise Exception("MT5初始化失败")

            # 获取XAUUSD的当前价格
            symbol_info = mt5.symbol_info_tick("XAUUSD")
            if symbol_info:
                price = (symbol_info.bid + symbol_info.ask) / 2

                # 保存到数据库
                self.save_price_data(
                    price=price,
                    high=symbol_info.ask,
                    low=symbol_info.bid,
                    source='MT5_REALTIME'
                )

                mt5.shutdown()
                return price
            else:
                mt5.shutdown()
                raise Exception("无法获取XAUUSD价格")

        except Exception as e:
            logger.warning(f"MT5价格获取失败: {e}")
            # 返回模拟价格
            import random
            base_price = 2000.0
            return base_price + random.uniform(-10, 10)

    def _generate_realtime_mock_data(self) -> List[Dict]:
        """生成实时模拟数据"""
        import random
        base_price = 2000.0
        data = []

        for i in range(60):  # 最近60分钟的数据
            timestamp = datetime.now() - timedelta(minutes=60-i)

            # 模拟价格波动
            if i == 0:
                price = base_price
            else:
                prev_price = data[-1]['price']
                change = random.uniform(-2, 2)  # 每分钟最多变化2美元
                price = prev_price + change

            data.append({
                'timestamp': timestamp.isoformat(),
                'price': price,
                'bid': price - 0.05,
                'ask': price + 0.05,
                'volume': random.randint(100, 1000),
                'source': 'MOCK_REALTIME'
            })

        return data

    def _get_fallback_realtime_data(self) -> Dict:
        """获取备用实时数据"""
        return {
            'current_price': 2000.0,
            'price_history': self._generate_realtime_mock_data(),
            'timestamp': datetime.now().isoformat(),
            'symbol': 'XAUUSD'
        }


# 全局数据管理器实例
data_manager = UnifiedDataManager()


def main():
    """测试函数"""
    print("统一数据管理系统测试")
    print("=" * 40)
    
    # 测试保存数据
    data_manager.save_price_data(2000.50, source='TEST')
    data_manager.save_prediction('test_system', {
        'current_price': 2000.50,
        'predicted_price': 2005.25,
        'signal': 'BUY',
        'confidence': 0.75
    })
    
    # 测试查询数据
    predictions = data_manager.get_recent_predictions(limit=5)
    print(f"最近预测数: {len(predictions)}")
    
    price_history = data_manager.get_price_history(hours=1)
    print(f"价格历史数: {len(price_history)}")
    
    dashboard_data = data_manager.get_dashboard_data()
    print(f"仪表板数据: {len(dashboard_data)} 项")
    
    print("✅ 统一数据管理系统测试完成!")


if __name__ == "__main__":
    main()
