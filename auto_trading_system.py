#!/usr/bin/env python3
"""
自动模拟EA交易系统
专注于黄金(XAUUSD)的全自动交易，集成强化学习机制
"""

import numpy as np
import pandas as pd
import MetaTrader5 as mt5
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
import json
import sqlite3
from pathlib import Path
import threading
import time

logger = logging.getLogger(__name__)


class AutoTradingSystem:
    """自动模拟EA交易系统"""
    
    def __init__(self, config: Dict = None):
        self.config = config or self._get_default_config()
        self.is_running = False
        self.is_connected = False
        
        # 交易状态
        self.account_info = {}
        self.positions = []
        self.orders = []
        self.trade_history = []
        
        # 强化学习参数
        self.q_table = {}
        self.learning_rate = 0.1
        self.discount_factor = 0.95
        self.epsilon = 0.1  # 探索率
        
        # 交易统计
        self.total_trades = 0
        self.winning_trades = 0
        self.total_profit = 0.0
        self.max_drawdown = 0.0
        
        # 风险管理
        self.max_position_size = self.config['risk_management']['max_position_size']
        self.stop_loss_pips = self.config['risk_management']['stop_loss_pips']
        self.take_profit_pips = self.config['risk_management']['take_profit_pips']
        
        # 数据库初始化
        self.db_path = Path("results/auto_trading.db")
        self.db_path.parent.mkdir(exist_ok=True)
        self._init_database()
        
        print(f"[自动交易] 自动模拟EA交易系统初始化")
        print(f"   交易品种: {self.config['symbol']}")
        print(f"   初始资金: ${self.config['initial_balance']:,.2f}")
        print(f"   杠杆: {self.config['leverage']}:1")
        print(f"   最大仓位: {self.max_position_size}")
    
    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        try:
            import MetaTrader5 as mt5
            timeframe = mt5.TIMEFRAME_M5
        except:
            timeframe = 16385  # M5的数值

        return {
            'symbol': 'XAUUSD',
            'initial_balance': 1000000.0,  # 100万美金
            'leverage': 100,
            'timeframe': timeframe,
            'risk_management': {
                'max_position_size': 200.0,  # 最大200手 (适应当前持仓)
                'stop_loss_pips': 50,        # 止损50点
                'take_profit_pips': 100,     # 止盈100点
                'max_daily_loss': 100000.0,  # 最大日亏损10万 (适应虚拟账户)
                'risk_per_trade': 0.02       # 每笔交易风险2%
            },
            'trading_hours': {
                'start': '00:00',
                'end': '23:59',
                'timezone': 'UTC'
            },
            'prediction_sources': {
                'realtime': {'weight': 0.3, 'enabled': True},
                'ai_enhanced': {'weight': 0.4, 'enabled': True},
                'traditional': {'weight': 0.3, 'enabled': True}
            }
        }
    
    def _init_database(self):
        """初始化数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建交易记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket INTEGER UNIQUE,
                    symbol TEXT,
                    type TEXT,
                    volume REAL,
                    open_price REAL,
                    close_price REAL,
                    open_time TEXT,
                    close_time TEXT,
                    profit REAL,
                    commission REAL,
                    swap REAL,
                    comment TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建账户状态表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS account_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    balance REAL,
                    equity REAL,
                    margin REAL,
                    free_margin REAL,
                    margin_level REAL,
                    profit REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建强化学习状态表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS rl_states (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    state TEXT,
                    action TEXT,
                    reward REAL,
                    next_state TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            print(f"[自动交易] 数据库初始化完成: {self.db_path}")
            
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
    
    def connect_mt5(self) -> bool:
        """连接MT5"""
        try:
            if not mt5.initialize():
                print(f"[自动交易] MT5初始化失败: {mt5.last_error()}")
                return False
            
            # 获取账户信息
            account_info = mt5.account_info()
            if account_info is None:
                print(f"[自动交易] 无法获取账户信息: {mt5.last_error()}")
                return False
            
            self.account_info = account_info._asdict()
            
            # 检查是否为模拟账户
            if not self._is_demo_account():
                print(f"[自动交易] 安全检查失败: 只能在模拟账户中运行")
                return False
            
            # 检查交易品种
            symbol_info = mt5.symbol_info(self.config['symbol'])
            if symbol_info is None:
                print(f"[自动交易] 交易品种 {self.config['symbol']} 不可用")
                return False
            
            if not symbol_info.visible:
                if not mt5.symbol_select(self.config['symbol'], True):
                    print(f"[自动交易] 无法选择交易品种 {self.config['symbol']}")
                    return False
            
            self.is_connected = True
            print(f"[自动交易] MT5连接成功")
            print(f"   账户: {self.account_info['login']}")
            print(f"   服务器: {self.account_info['server']}")
            print(f"   余额: ${self.account_info['balance']:,.2f}")
            print(f"   杠杆: {self.account_info['leverage']}:1")
            
            return True
            
        except Exception as e:
            logger.error(f"MT5连接失败: {e}")
            return False
    
    def _is_demo_account(self) -> bool:
        """检查是否为模拟账户"""
        try:
            # 检查账户类型
            if 'trade_mode' in self.account_info:
                return self.account_info['trade_mode'] == mt5.ACCOUNT_TRADE_MODE_DEMO
            
            # 备用检查：通过服务器名称判断
            server = self.account_info.get('server', '').lower()
            demo_keywords = ['demo', 'test', 'practice', 'simulation']
            return any(keyword in server for keyword in demo_keywords)
            
        except Exception as e:
            logger.error(f"账户类型检查失败: {e}")
            return False
    
    def start(self) -> bool:
        """启动系统（统一接口）"""
        return self.start_trading()

    def start_trading(self) -> bool:
        """启动自动交易"""
        try:
            if not self.is_connected:
                if not self.connect_mt5():
                    return False
            
            if self.is_running:
                print(f"[自动交易] 交易系统已在运行中")
                return True
            
            self.is_running = True
            
            # 启动交易线程
            self.trading_thread = threading.Thread(target=self._trading_loop, daemon=True)
            self.trading_thread.start()
            
            print(f"[自动交易] 自动交易系统已启动")
            return True
            
        except Exception as e:
            logger.error(f"启动自动交易失败: {e}")
            return False
    
    def stop_trading(self) -> bool:
        """停止自动交易"""
        try:
            if not self.is_running:
                print(f"[自动交易] 交易系统未运行")
                return True
            
            self.is_running = False
            
            # 等待交易线程结束
            if hasattr(self, 'trading_thread'):
                self.trading_thread.join(timeout=5)
            
            # 关闭所有持仓（可选）
            if self.config.get('close_all_on_stop', False):
                self._close_all_positions()
            
            print(f"[自动交易] 自动交易系统已停止")
            return True
            
        except Exception as e:
            logger.error(f"停止自动交易失败: {e}")
            return False
    
    def _trading_loop(self):
        """交易主循环"""
        print(f"[自动交易] 交易循环开始")
        
        while self.is_running:
            try:
                # 更新账户信息
                self._update_account_info()
                
                # 更新持仓信息
                self._update_positions()
                
                # 风险检查
                if not self._risk_check():
                    print(f"[自动交易] 风险检查失败，暂停交易")
                    time.sleep(60)  # 等待1分钟后重试
                    continue
                
                # 获取预测信号
                signals = self._get_prediction_signals()
                
                # 生成交易决策
                action = self._make_trading_decision(signals)
                
                # 执行交易
                if action != 'HOLD':
                    self._execute_trade(action, signals)
                
                # 管理现有持仓
                self._manage_positions()
                
                # 记录状态
                self._save_account_status()
                
                # 等待下一个周期
                time.sleep(self.config.get('trading_interval', 30))  # 默认30秒
                
            except Exception as e:
                logger.error(f"交易循环错误: {e}")
                time.sleep(10)  # 错误后等待10秒
        
        print(f"[自动交易] 交易循环结束")
    
    def _update_account_info(self):
        """更新账户信息"""
        try:
            account_info = mt5.account_info()
            if account_info:
                self.account_info = account_info._asdict()
        except Exception as e:
            logger.error(f"更新账户信息失败: {e}")
    
    def _update_positions(self):
        """更新持仓信息"""
        try:
            positions = mt5.positions_get(symbol=self.config['symbol'])
            self.positions = [pos._asdict() for pos in positions] if positions else []
        except Exception as e:
            logger.error(f"更新持仓信息失败: {e}")
    
    def _risk_check(self) -> bool:
        """风险检查"""
        try:
            # 检查账户余额
            if self.account_info['balance'] <= 0:
                return False
            
            # 检查保证金水平
            margin_level = self.account_info.get('margin_level', 0)
            if margin_level > 0 and margin_level < 100:  # 保证金水平低于100%
                return False
            
            # 检查日亏损限制
            daily_loss = self._calculate_daily_loss()
            if daily_loss > self.config['risk_management']['max_daily_loss']:
                return False
            
            # 检查最大持仓
            total_volume = sum(pos['volume'] for pos in self.positions)
            if total_volume >= self.max_position_size:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"风险检查失败: {e}")
            return False
    
    def _calculate_daily_loss(self) -> float:
        """计算当日亏损"""
        try:
            today = datetime.now().date()
            daily_profit = 0.0
            
            # 计算已平仓交易的盈亏
            for trade in self.trade_history:
                if trade.get('close_time', '').startswith(str(today)):
                    daily_profit += trade.get('profit', 0)
            
            # 计算当前持仓的浮动盈亏
            for pos in self.positions:
                daily_profit += pos.get('profit', 0)
            
            return max(0, -daily_profit)  # 只返回亏损部分
            
        except Exception as e:
            logger.error(f"计算日亏损失败: {e}")
            return 0.0

    def _get_prediction_signals(self) -> Dict:
        """获取预测信号"""
        signals = {}

        try:
            # 从各预测系统获取信号
            for source, config in self.config['prediction_sources'].items():
                if not config['enabled']:
                    continue

                try:
                    if source == 'realtime':
                        signal = self._get_realtime_signal()
                    elif source == 'ai_enhanced':
                        signal = self._get_ai_enhanced_signal()
                    elif source == 'traditional':
                        signal = self._get_traditional_signal()
                    else:
                        continue

                    if signal:
                        signals[source] = {
                            'signal': signal.get('signal', 'HOLD'),
                            'confidence': signal.get('confidence', 0.5),
                            'weight': config['weight']
                        }

                except Exception as e:
                    logger.error(f"获取 {source} 信号失败: {e}")

            return signals

        except Exception as e:
            logger.error(f"获取预测信号失败: {e}")
            return {}

    def _get_realtime_signal(self) -> Optional[Dict]:
        """获取实时预测信号"""
        try:
            import requests
            response = requests.get('http://localhost:5000/api/prediction/realtime', timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'error' not in data:
                    return {
                        'signal': self._convert_signal(data.get('signal', 'HOLD')),
                        'confidence': data.get('confidence', 0.5),
                        'price': data.get('predicted_price', 0)
                    }
        except Exception as e:
            logger.debug(f"获取实时信号失败: {e}")
        return None

    def _get_ai_enhanced_signal(self) -> Optional[Dict]:
        """获取增强AI信号"""
        try:
            import requests
            response = requests.get('http://localhost:5000/api/prediction/ai_enhanced', timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'error' not in data:
                    return {
                        'signal': self._convert_signal(data.get('signal', 'HOLD')),
                        'confidence': data.get('confidence', 0.5),
                        'price': data.get('predicted_price', 0)
                    }
        except Exception as e:
            logger.debug(f"获取AI增强信号失败: {e}")
        return None

    def _get_traditional_signal(self) -> Optional[Dict]:
        """获取传统ML信号"""
        try:
            import requests
            response = requests.get('http://localhost:5000/api/prediction/traditional', timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'error' not in data:
                    return {
                        'signal': self._convert_signal(data.get('signal', 'HOLD')),
                        'confidence': data.get('confidence', 0.5),
                        'price': data.get('predicted_price', 0)
                    }
        except Exception as e:
            logger.debug(f"获取传统ML信号失败: {e}")
        return None

    def _convert_signal(self, signal: str) -> str:
        """转换信号格式"""
        signal_map = {
            '看涨': 'BUY',
            '看跌': 'SELL',
            'bullish': 'BUY',
            'bearish': 'SELL',
            'buy': 'BUY',
            'sell': 'SELL',
            '中性': 'HOLD',
            'neutral': 'HOLD',
            'hold': 'HOLD'
        }
        return signal_map.get(signal.lower(), 'HOLD')

    def _make_trading_decision(self, signals: Dict) -> str:
        """生成交易决策"""
        try:
            if not signals:
                return 'HOLD'

            # 计算加权信号
            buy_score = 0.0
            sell_score = 0.0
            total_weight = 0.0

            for source, signal_data in signals.items():
                signal = signal_data['signal']
                confidence = signal_data['confidence']
                weight = signal_data['weight']

                weighted_confidence = confidence * weight
                total_weight += weight

                if signal == 'BUY':
                    buy_score += weighted_confidence
                elif signal == 'SELL':
                    sell_score += weighted_confidence

            if total_weight == 0:
                return 'HOLD'

            # 归一化分数
            buy_score /= total_weight
            sell_score /= total_weight

            # 决策阈值
            decision_threshold = 0.6

            # 强化学习调整
            current_state = self._get_current_state()
            rl_action = self._get_rl_action(current_state)

            # 结合传统信号和强化学习
            if buy_score > decision_threshold and rl_action in ['BUY', 'HOLD']:
                return 'BUY'
            elif sell_score > decision_threshold and rl_action in ['SELL', 'HOLD']:
                return 'SELL'
            else:
                return 'HOLD'

        except Exception as e:
            logger.error(f"交易决策失败: {e}")
            return 'HOLD'

    def _get_current_state(self) -> str:
        """获取当前市场状态"""
        try:
            # 获取当前价格数据
            timeframe = self.config.get('timeframe', 16385)  # 默认M5
            rates = mt5.copy_rates_from_pos(self.config['symbol'], timeframe, 0, 10)
            if rates is None or len(rates) == 0:
                return 'UNKNOWN'

            current_price = rates[-1]['close']

            # 计算技术指标
            prices = [rate['close'] for rate in rates]
            ma5 = np.mean(prices[-5:]) if len(prices) >= 5 else current_price
            ma10 = np.mean(prices[-10:]) if len(prices) >= 10 else current_price

            # 定义状态
            if current_price > ma5 > ma10:
                trend = 'UPTREND'
            elif current_price < ma5 < ma10:
                trend = 'DOWNTREND'
            else:
                trend = 'SIDEWAYS'

            # 计算波动率
            if len(prices) >= 5:
                volatility = np.std(prices[-5:])
                vol_level = 'HIGH' if volatility > np.mean([rate['high'] - rate['low'] for rate in rates[-5:]]) else 'LOW'
            else:
                vol_level = 'LOW'

            return f"{trend}_{vol_level}"

        except Exception as e:
            logger.error(f"获取市场状态失败: {e}")
            return 'UNKNOWN'

    def _get_rl_action(self, state: str) -> str:
        """强化学习动作选择"""
        try:
            # ε-贪婪策略
            if np.random.random() < self.epsilon:
                return np.random.choice(['BUY', 'SELL', 'HOLD'])

            # 选择Q值最高的动作
            if state in self.q_table:
                q_values = self.q_table[state]
                return max(q_values, key=q_values.get)
            else:
                # 初始化新状态
                self.q_table[state] = {'BUY': 0.0, 'SELL': 0.0, 'HOLD': 0.0}
                return 'HOLD'

        except Exception as e:
            logger.error(f"强化学习动作选择失败: {e}")
            return 'HOLD'

    def _execute_trade(self, action: str, signals: Dict):
        """执行交易"""
        try:
            if action == 'HOLD':
                return

            # 检查是否已有相同方向的持仓
            existing_positions = [pos for pos in self.positions if pos['type'] == (0 if action == 'BUY' else 1)]
            if existing_positions:
                print(f"[自动交易] 已有 {action} 持仓，跳过开仓")
                return

            # 计算交易量
            volume = self._calculate_position_size()
            if volume <= 0:
                print(f"[自动交易] 计算交易量为0，跳过交易")
                return

            # 获取当前价格
            symbol_info = mt5.symbol_info(self.config['symbol'])
            if symbol_info is None:
                print(f"[自动交易] 无法获取品种信息")
                return

            current_price = symbol_info.ask if action == 'BUY' else symbol_info.bid

            # 计算止损止盈
            point = symbol_info.point
            if action == 'BUY':
                sl = current_price - self.stop_loss_pips * point
                tp = current_price + self.take_profit_pips * point
                order_type = mt5.ORDER_TYPE_BUY
            else:
                sl = current_price + self.stop_loss_pips * point
                tp = current_price - self.take_profit_pips * point
                order_type = mt5.ORDER_TYPE_SELL

            # 获取品种的填充模式
            symbol_info = mt5.symbol_info(self.config['symbol'])
            filling_mode = self._get_filling_mode(symbol_info)

            # 构建交易请求
            request = {
                'action': mt5.TRADE_ACTION_DEAL,
                'symbol': self.config['symbol'],
                'volume': volume,
                'type': order_type,
                'price': current_price,
                'sl': sl,
                'tp': tp,
                'deviation': 20,
                'magic': 12345,
                'comment': f'AutoEA_{action}',
                'type_time': mt5.ORDER_TIME_GTC,
                'type_filling': filling_mode,
            }

            # 发送交易请求
            result = mt5.order_send(request)

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                print(f"[自动交易] 交易失败: {result.retcode} - {result.comment}")
                return

            print(f"[自动交易] 交易成功: {action} {volume} 手 @ {current_price}")
            print(f"   止损: {sl:.5f}, 止盈: {tp:.5f}")
            print(f"   订单号: {result.order}")

            # 记录交易
            self._record_trade(result, action, signals)

        except Exception as e:
            logger.error(f"执行交易失败: {e}")

    def _get_filling_mode(self, symbol_info):
        """获取合适的订单填充模式"""
        try:
            if symbol_info is None:
                return mt5.ORDER_FILLING_FOK

            # 检查品种支持的填充模式
            filling_modes = symbol_info.filling_mode

            # 按优先级选择填充模式
            if filling_modes & 2:  # ORDER_FILLING_IOC
                return mt5.ORDER_FILLING_IOC
            elif filling_modes & 1:  # ORDER_FILLING_FOK
                return mt5.ORDER_FILLING_FOK
            elif filling_modes & 4:  # ORDER_FILLING_RETURN
                return mt5.ORDER_FILLING_RETURN
            else:
                # 默认使用FOK模式
                return mt5.ORDER_FILLING_FOK

        except Exception as e:
            logger.error(f"获取填充模式失败: {e}")
            return mt5.ORDER_FILLING_FOK

    def _calculate_position_size(self) -> float:
        """计算仓位大小"""
        try:
            # 基于风险百分比计算
            account_balance = self.account_info['balance']
            risk_amount = account_balance * self.config['risk_management']['risk_per_trade']

            # 获取品种信息
            symbol_info = mt5.symbol_info(self.config['symbol'])
            if symbol_info is None:
                return 0.0

            # 计算每点价值
            point_value = symbol_info.trade_tick_value
            stop_loss_amount = self.stop_loss_pips * point_value

            if stop_loss_amount <= 0:
                return 0.0

            # 计算仓位大小
            volume = risk_amount / stop_loss_amount

            # 限制最大仓位
            volume = min(volume, self.max_position_size)

            # 调整到最小交易单位
            volume_step = symbol_info.volume_step
            volume = round(volume / volume_step) * volume_step

            # 确保最小交易量
            volume = max(volume, symbol_info.volume_min)

            return volume

        except Exception as e:
            logger.error(f"计算仓位大小失败: {e}")
            return 0.0

    def _manage_positions(self):
        """管理现有持仓"""
        try:
            for position in self.positions:
                # 检查是否需要调整止损
                self._trail_stop_loss(position)

                # 检查是否需要部分平仓
                self._check_partial_close(position)

        except Exception as e:
            logger.error(f"持仓管理失败: {e}")

    def _trail_stop_loss(self, position: Dict):
        """移动止损"""
        try:
            if position['profit'] <= 0:
                return  # 只对盈利持仓移动止损

            symbol_info = mt5.symbol_info(self.config['symbol'])
            if symbol_info is None:
                return

            current_price = symbol_info.bid if position['type'] == 0 else symbol_info.ask
            point = symbol_info.point
            trail_distance = 30 * point  # 移动止损距离30点

            if position['type'] == 0:  # 买单
                new_sl = current_price - trail_distance
                if new_sl > position['sl'] + point:  # 只向有利方向移动
                    self._modify_position(position['ticket'], new_sl, position['tp'])
            else:  # 卖单
                new_sl = current_price + trail_distance
                if new_sl < position['sl'] - point:  # 只向有利方向移动
                    self._modify_position(position['ticket'], new_sl, position['tp'])

        except Exception as e:
            logger.error(f"移动止损失败: {e}")

    def _check_partial_close(self, position: Dict):
        """检查部分平仓"""
        try:
            # 如果盈利超过50点，平仓一半
            if position['profit'] > 500:  # 假设每点10美元
                partial_volume = position['volume'] / 2
                if partial_volume >= mt5.symbol_info(self.config['symbol']).volume_min:
                    self._close_position_partial(position['ticket'], partial_volume)

        except Exception as e:
            logger.error(f"部分平仓检查失败: {e}")

    def _modify_position(self, ticket: int, sl: float, tp: float):
        """修改持仓"""
        try:
            request = {
                'action': mt5.TRADE_ACTION_SLTP,
                'position': ticket,
                'sl': sl,
                'tp': tp,
            }

            result = mt5.order_send(request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"[自动交易] 持仓修改成功: {ticket}, SL: {sl:.5f}, TP: {tp:.5f}")
            else:
                print(f"[自动交易] 持仓修改失败: {result.retcode}")

        except Exception as e:
            logger.error(f"修改持仓失败: {e}")

    def _close_position_partial(self, ticket: int, volume: float):
        """部分平仓"""
        try:
            position = next((pos for pos in self.positions if pos['ticket'] == ticket), None)
            if not position:
                return

            request = {
                'action': mt5.TRADE_ACTION_DEAL,
                'position': ticket,
                'symbol': self.config['symbol'],
                'volume': volume,
                'type': mt5.ORDER_TYPE_SELL if position['type'] == 0 else mt5.ORDER_TYPE_BUY,
                'deviation': 20,
                'magic': 12345,
                'comment': 'AutoEA_PartialClose',
                'type_time': mt5.ORDER_TIME_GTC,
                'type_filling': mt5.ORDER_FILLING_IOC,
            }

            result = mt5.order_send(request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"[自动交易] 部分平仓成功: {ticket}, 平仓量: {volume}")
            else:
                print(f"[自动交易] 部分平仓失败: {result.retcode}")

        except Exception as e:
            logger.error(f"部分平仓失败: {e}")

    def _close_all_positions(self):
        """关闭所有持仓"""
        try:
            for position in self.positions:
                self._close_position(position['ticket'])

        except Exception as e:
            logger.error(f"关闭所有持仓失败: {e}")

    def _close_position(self, ticket: int):
        """关闭指定持仓"""
        try:
            position = next((pos for pos in self.positions if pos['ticket'] == ticket), None)
            if not position:
                return

            request = {
                'action': mt5.TRADE_ACTION_DEAL,
                'position': ticket,
                'symbol': self.config['symbol'],
                'volume': position['volume'],
                'type': mt5.ORDER_TYPE_SELL if position['type'] == 0 else mt5.ORDER_TYPE_BUY,
                'deviation': 20,
                'magic': 12345,
                'comment': 'AutoEA_Close',
                'type_time': mt5.ORDER_TIME_GTC,
                'type_filling': mt5.ORDER_FILLING_IOC,
            }

            result = mt5.order_send(request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"[自动交易] 平仓成功: {ticket}")
            else:
                print(f"[自动交易] 平仓失败: {result.retcode}")

        except Exception as e:
            logger.error(f"平仓失败: {e}")

    def _record_trade(self, result, action: str, signals: Dict):
        """记录交易"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO trades (ticket, symbol, type, volume, open_price, open_time, comment)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                result.order,
                self.config['symbol'],
                action,
                result.volume,
                result.price,
                datetime.now().isoformat(),
                f"Signals: {json.dumps(signals)}"
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"记录交易失败: {e}")

    def _save_account_status(self):
        """保存账户状态"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO account_status (balance, equity, margin, free_margin, margin_level, profit)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                self.account_info.get('balance', 0),
                self.account_info.get('equity', 0),
                self.account_info.get('margin', 0),
                self.account_info.get('margin_free', 0),
                self.account_info.get('margin_level', 0),
                self.account_info.get('profit', 0)
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"保存账户状态失败: {e}")

    def update_rl_model(self, state: str, action: str, reward: float, next_state: str):
        """更新强化学习模型"""
        try:
            # 初始化Q表
            if state not in self.q_table:
                self.q_table[state] = {'BUY': 0.0, 'SELL': 0.0, 'HOLD': 0.0}
            if next_state not in self.q_table:
                self.q_table[next_state] = {'BUY': 0.0, 'SELL': 0.0, 'HOLD': 0.0}

            # Q-learning更新
            current_q = self.q_table[state][action]
            max_next_q = max(self.q_table[next_state].values())

            new_q = current_q + self.learning_rate * (reward + self.discount_factor * max_next_q - current_q)
            self.q_table[state][action] = new_q

            # 记录到数据库
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO rl_states (state, action, reward, next_state)
                VALUES (?, ?, ?, ?)
            ''', (state, action, reward, next_state))

            conn.commit()
            conn.close()

            print(f"[强化学习] 更新Q值: {state}-{action} = {new_q:.4f}, 奖励: {reward:.2f}")

        except Exception as e:
            logger.error(f"更新强化学习模型失败: {e}")

    def get_status(self) -> Dict:
        """获取系统状态"""
        try:
            # 更新账户信息
            if self.is_connected:
                self._update_account_info()
                self._update_positions()

            # 计算统计信息
            total_profit = sum(pos.get('profit', 0) for pos in self.positions)

            return {
                'running': self.is_running,
                'connected': self.is_connected,
                'account_info': self.account_info,
                'positions': self.positions,
                'position_count': len(self.positions),
                'total_profit': total_profit,
                'total_trades': self.total_trades,
                'winning_trades': self.winning_trades,
                'win_rate': (self.winning_trades / max(self.total_trades, 1)) * 100,
                'config': self.config,
                'q_table_size': len(self.q_table)
            }

        except Exception as e:
            logger.error(f"获取状态失败: {e}")
            return {
                'running': self.is_running,
                'connected': self.is_connected,
                'error': str(e)
            }

    def get_trade_history(self, limit: int = 100) -> List[Dict]:
        """获取交易历史"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM trades
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))

            columns = [description[0] for description in cursor.description]
            trades = [dict(zip(columns, row)) for row in cursor.fetchall()]

            conn.close()
            return trades

        except Exception as e:
            logger.error(f"获取交易历史失败: {e}")
            return []

    def emergency_stop(self):
        """紧急停止"""
        try:
            print(f"[自动交易] 执行紧急停止")

            # 停止交易
            self.is_running = False

            # 关闭所有持仓
            self._close_all_positions()

            # 断开MT5连接
            mt5.shutdown()
            self.is_connected = False

            print(f"[自动交易] 紧急停止完成")

        except Exception as e:
            logger.error(f"紧急停止失败: {e}")


def main():
    """测试函数"""
    print("自动模拟EA交易系统测试")
    print("=" * 50)

    # 创建交易系统
    config = {
        'symbol': 'XAUUSD',
        'initial_balance': 1000000.0,
        'leverage': 100,
        'risk_management': {
            'max_position_size': 5.0,
            'stop_loss_pips': 30,
            'take_profit_pips': 60,
            'risk_per_trade': 0.01
        }
    }

    trading_system = AutoTradingSystem(config)

    try:
        # 连接MT5
        print("🔗 连接MT5...")
        if trading_system.connect_mt5():
            print("✅ MT5连接成功")

            # 获取状态
            status = trading_system.get_status()
            print(f"📊 账户状态:")
            print(f"   余额: ${status['account_info'].get('balance', 0):,.2f}")
            print(f"   净值: ${status['account_info'].get('equity', 0):,.2f}")
            print(f"   杠杆: {status['account_info'].get('leverage', 0)}:1")

            print("\n✅ 自动交易系统测试完成!")
        else:
            print("❌ MT5连接失败")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
    finally:
        trading_system.emergency_stop()


if __name__ == "__main__":
    main()
