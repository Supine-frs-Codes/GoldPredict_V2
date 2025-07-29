#!/usr/bin/env python3
"""
黄金价格预测微信发送Demo系统
集成基础预测功能和微信自动发送功能的演示版本
"""

import sys
import json
import time
import threading
import logging
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from wechat_sender import WeChatSender
from improved_mt5_manager import ImprovedMT5Manager

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimplePredictionEngine:
    """简化的预测引擎 - 使用MT5数据源"""

    def __init__(self):
        self.symbol = "XAUUSD"  # 黄金交易符号
        self.last_prediction = None
        self.mt5_manager = ImprovedMT5Manager()

    def get_gold_data(self, hours=24):
        """从MT5获取黄金价格数据"""
        try:
            # 确保MT5连接
            if not self.mt5_manager.ensure_connection():
                logger.error("MT5连接失败")
                return None

            # 获取历史数据
            import MetaTrader5 as mt5
            historical_result = self.mt5_manager.get_historical_data(
                symbol=self.symbol,
                timeframe=mt5.TIMEFRAME_H1,  # 1小时K线
                count=hours
            )

            if historical_result is None or 'data' not in historical_result:
                logger.error("无法获取MT5历史数据")
                return None

            historical_data = historical_result['data']

            # 转换为与原系统兼容的格式
            data = pd.DataFrame()
            data['Close'] = historical_data['close']
            data['High'] = historical_data['high']
            data['Low'] = historical_data['low']
            data['Open'] = historical_data['open']
            data['Volume'] = historical_data['tick_volume']  # MT5使用tick_volume
            data.index = historical_data['time']

            return data

        except Exception as e:
            logger.error(f"获取MT5数据失败: {e}")
            return None
    
    def calculate_technical_indicators(self, data):
        """计算技术指标"""
        try:
            # 移动平均线
            data['MA5'] = data['Close'].rolling(window=5).mean()
            data['MA20'] = data['Close'].rolling(window=20).mean()
            
            # RSI
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            data['RSI'] = 100 - (100 / (1 + rs))
            
            # 布林带
            data['BB_Middle'] = data['Close'].rolling(window=20).mean()
            bb_std = data['Close'].rolling(window=20).std()
            data['BB_Upper'] = data['BB_Middle'] + (bb_std * 2)
            data['BB_Lower'] = data['BB_Middle'] - (bb_std * 2)
            
            # 成交量移动平均
            data['Volume_MA'] = data['Volume'].rolling(window=10).mean()
            
            return data
        except Exception as e:
            logger.error(f"计算技术指标失败: {e}")
            return data
    
    def generate_prediction(self):
        """生成预测"""
        try:
            logger.info("开始生成预测...")

            # 获取当前实时价格
            current_price_data = self.mt5_manager.get_current_price(self.symbol)
            if current_price_data is None:
                logger.error("无法获取当前价格")
                return None

            current_price = (current_price_data['bid'] + current_price_data['ask']) / 2

            # 获取历史数据
            data = self.get_gold_data(hours=48)  # 获取48小时数据
            if data is None:
                return None

            # 计算技术指标
            data = self.calculate_technical_indicators(data)

            # 获取最新历史数据
            latest = data.iloc[-1]
            
            # 简单预测逻辑
            prediction_factors = []
            
            # 1. 移动平均线趋势
            if not pd.isna(latest['MA5']) and not pd.isna(latest['MA20']):
                if latest['MA5'] > latest['MA20']:
                    ma_signal = 1  # 看涨
                    prediction_factors.append(("MA趋势", 1, 0.3))
                else:
                    ma_signal = -1  # 看跌
                    prediction_factors.append(("MA趋势", -1, 0.3))
            else:
                ma_signal = 0
                prediction_factors.append(("MA趋势", 0, 0.1))
            
            # 2. RSI超买超卖
            if not pd.isna(latest['RSI']):
                if latest['RSI'] > 70:
                    rsi_signal = -1  # 超买，看跌
                    prediction_factors.append(("RSI信号", -1, 0.2))
                elif latest['RSI'] < 30:
                    rsi_signal = 1  # 超卖，看涨
                    prediction_factors.append(("RSI信号", 1, 0.2))
                else:
                    rsi_signal = 0  # 中性
                    prediction_factors.append(("RSI信号", 0, 0.1))
            else:
                rsi_signal = 0
                prediction_factors.append(("RSI信号", 0, 0.1))
            
            # 3. 布林带位置
            if not pd.isna(latest['BB_Upper']) and not pd.isna(latest['BB_Lower']):
                if current_price > latest['BB_Upper']:
                    bb_signal = -1  # 价格过高，看跌
                    prediction_factors.append(("布林带", -1, 0.2))
                elif current_price < latest['BB_Lower']:
                    bb_signal = 1  # 价格过低，看涨
                    prediction_factors.append(("布林带", 1, 0.2))
                else:
                    bb_signal = 0  # 正常范围
                    prediction_factors.append(("布林带", 0, 0.1))
            else:
                bb_signal = 0
                prediction_factors.append(("布林带", 0, 0.1))
            
            # 4. 成交量确认
            if not pd.isna(latest['Volume_MA']):
                if latest['Volume'] > latest['Volume_MA'] * 1.2:
                    volume_signal = 1  # 成交量放大，确认趋势
                    prediction_factors.append(("成交量", 1, 0.3))
                else:
                    volume_signal = 0  # 成交量正常
                    prediction_factors.append(("成交量", 0, 0.2))
            else:
                volume_signal = 0
                prediction_factors.append(("成交量", 0, 0.1))
            
            # 计算综合信号
            total_weight = sum(weight for _, _, weight in prediction_factors)
            weighted_signal = sum(signal * weight for _, signal, weight in prediction_factors) / total_weight
            
            # 生成预测价格
            price_change_pct = weighted_signal * 0.5  # 最大0.5%的变化
            predicted_price = current_price * (1 + price_change_pct / 100)
            
            # 计算置信度
            confidence = min(0.9, max(0.3, abs(weighted_signal) * 0.3 + 0.4))
            
            # 生成交易信号
            if weighted_signal > 0.3:
                signal = "看涨"
            elif weighted_signal < -0.3:
                signal = "看跌"
            else:
                signal = "中性"
            
            # 构建预测结果
            prediction = {
                'timestamp': datetime.now().isoformat(),
                'current_price': current_price,
                'predicted_price': predicted_price,
                'price_change': predicted_price - current_price,
                'price_change_pct': (predicted_price - current_price) / current_price * 100,
                'signal': signal,
                'confidence': confidence,
                'method': 'Demo技术分析(MT5)',
                'target_time': (datetime.now() + timedelta(hours=1)).isoformat(),
                'data_source': 'MetaTrader5',
                'symbol': self.symbol,
                'bid_price': current_price_data['bid'],
                'ask_price': current_price_data['ask'],
                'factors': [
                    {
                        'name': name,
                        'signal': sig,
                        'weight': weight
                    } for name, sig, weight in prediction_factors
                ],
                'technical_data': {
                    'rsi': float(latest['RSI']) if not pd.isna(latest['RSI']) else None,
                    'ma5': float(latest['MA5']) if not pd.isna(latest['MA5']) else None,
                    'ma20': float(latest['MA20']) if not pd.isna(latest['MA20']) else None,
                    'volume': float(latest['Volume']),
                    'volume_ma': float(latest['Volume_MA']) if not pd.isna(latest['Volume_MA']) else None
                }
            }
            
            self.last_prediction = prediction
            logger.info(f"预测生成完成: {signal} (置信度: {confidence:.1%})")
            
            return prediction
            
        except Exception as e:
            logger.error(f"生成预测失败: {e}")
            return None
    
    def get_latest_prediction(self):
        """获取最新预测"""
        return self.last_prediction

    def get_mt5_status(self):
        """获取MT5连接状态"""
        try:
            if not self.mt5_manager.ensure_connection():
                return {
                    'connected': False,
                    'error': 'MT5连接失败'
                }

            # 获取当前价格测试连接
            current_price = self.mt5_manager.get_current_price(self.symbol)
            if current_price is None:
                return {
                    'connected': False,
                    'error': '无法获取价格数据'
                }

            return {
                'connected': True,
                'symbol': self.symbol,
                'current_price': (current_price['bid'] + current_price['ask']) / 2,
                'bid': current_price['bid'],
                'ask': current_price['ask'],
                'last_update': current_price['time'].isoformat()
            }

        except Exception as e:
            return {
                'connected': False,
                'error': str(e)
            }

class DemoWeChatPredictionSystem:
    """Demo微信预测系统"""
    
    def __init__(self):
        self.prediction_engine = SimplePredictionEngine()
        self.wechat_sender = WeChatSender()
        self.is_running = False
        self.prediction_thread = None
        self.prediction_interval = 300  # 5分钟
        self.prediction_history = []
        
    def start_system(self):
        """启动系统"""
        if self.is_running:
            logger.warning("系统已在运行中")
            return False
        
        logger.info("启动Demo微信预测系统...")
        
        # 连接微信
        if not self.wechat_sender.connect_wechat():
            logger.error("微信连接失败，无法启动系统")
            return False
        
        # 启动预测循环
        self.is_running = True
        self.prediction_thread = threading.Thread(target=self._prediction_loop, daemon=True)
        self.prediction_thread.start()
        
        logger.info("Demo系统启动成功")
        return True
    
    def stop_system(self):
        """停止系统"""
        if not self.is_running:
            logger.warning("系统未在运行")
            return
        
        logger.info("停止Demo微信预测系统...")
        self.is_running = False
        
        # 断开微信连接
        self.wechat_sender.disconnect_wechat()
        
        logger.info("Demo系统已停止")
    
    def _prediction_loop(self):
        """预测循环"""
        while self.is_running:
            try:
                # 生成预测
                prediction = self.prediction_engine.generate_prediction()
                
                if prediction:
                    # 保存到历史
                    self.prediction_history.append(prediction)
                    if len(self.prediction_history) > 100:  # 只保留最近100个
                        self.prediction_history = self.prediction_history[-100:]
                    
                    # 保存到文件
                    self._save_prediction(prediction)
                    
                    # 发送到微信群
                    result = self.wechat_sender.send_prediction_to_groups(prediction)
                    
                    if result['success']:
                        logger.info(f"预测已发送到微信群: {result['sent_groups']}")
                    else:
                        logger.warning(f"微信发送失败: {result['errors']}")
                
                # 等待下次预测
                time.sleep(self.prediction_interval)
                
            except Exception as e:
                logger.error(f"预测循环出错: {e}")
                time.sleep(60)  # 出错后等待1分钟再重试
    
    def _save_prediction(self, prediction):
        """保存预测到文件"""
        try:
            # 保存到results目录
            results_dir = Path("results/demo")
            results_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存最新预测
            latest_file = results_dir / "latest_demo_prediction.json"
            with open(latest_file, 'w', encoding='utf-8') as f:
                json.dump(prediction, f, indent=2, ensure_ascii=False)
            
            # 保存历史预测
            history_file = results_dir / f"demo_prediction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(prediction, f, indent=2, ensure_ascii=False)
            
            logger.info(f"预测已保存: {latest_file}")
            
        except Exception as e:
            logger.error(f"保存预测失败: {e}")
    
    def manual_prediction(self):
        """手动生成预测"""
        logger.info("手动生成预测...")
        prediction = self.prediction_engine.generate_prediction()
        
        if prediction:
            self.prediction_history.append(prediction)
            self._save_prediction(prediction)
            
            # 发送到微信群
            result = self.wechat_sender.send_prediction_to_groups(prediction)
            
            return {
                'success': True,
                'prediction': prediction,
                'wechat_result': result
            }
        else:
            return {
                'success': False,
                'message': '预测生成失败'
            }
    
    def get_status(self):
        """获取系统状态"""
        mt5_status = self.prediction_engine.get_mt5_status()

        return {
            'running': self.is_running,
            'wechat_connected': self.wechat_sender.is_connected,
            'mt5_connected': mt5_status['connected'],
            'mt5_status': mt5_status,
            'prediction_interval': self.prediction_interval,
            'predictions_count': len(self.prediction_history),
            'last_prediction': self.prediction_engine.get_latest_prediction(),
            'wechat_config': self.wechat_sender.get_status(),
            'data_source': 'MetaTrader5'
        }
    
    def set_prediction_interval(self, interval_seconds):
        """设置预测间隔"""
        self.prediction_interval = max(60, interval_seconds)  # 最小1分钟
        logger.info(f"预测间隔已设置为: {self.prediction_interval}秒")

def interactive_demo():
    """交互式Demo"""
    print("🚀 黄金价格预测微信发送Demo系统")
    print("=" * 50)
    
    system = DemoWeChatPredictionSystem()
    
    try:
        while True:
            print("\n请选择操作:")
            print("1. 启动自动预测系统")
            print("2. 手动生成预测")
            print("3. 查看系统状态")
            print("4. 设置预测间隔")
            print("5. 查看预测历史")
            print("6. 测试微信连接")
            print("0. 退出")
            
            choice = input("\n请输入选择 (0-6): ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                if system.start_system():
                    print("✅ 系统启动成功，正在自动生成预测...")
                    print("按任意键停止系统...")
                    input()
                    system.stop_system()
                else:
                    print("❌ 系统启动失败")
            elif choice == '2':
                print("生成手动预测...")
                result = system.manual_prediction()
                if result['success']:
                    pred = result['prediction']
                    print(f"✅ 预测生成成功:")
                    print(f"   当前价格: ${pred['current_price']:.2f}")
                    print(f"   预测价格: ${pred['predicted_price']:.2f}")
                    print(f"   交易信号: {pred['signal']}")
                    print(f"   置信度: {pred['confidence']:.1%}")
                    
                    wechat_result = result['wechat_result']
                    if wechat_result['success']:
                        print(f"   微信发送: 成功 -> {wechat_result['sent_groups']}")
                    else:
                        print(f"   微信发送: 失败 -> {wechat_result['errors']}")
                else:
                    print("❌ 预测生成失败")
            elif choice == '3':
                status = system.get_status()
                print("系统状态:")
                print(f"   运行状态: {'运行中' if status['running'] else '已停止'}")
                print(f"   微信连接: {'已连接' if status['wechat_connected'] else '未连接'}")
                print(f"   MT5连接: {'已连接' if status['mt5_connected'] else '未连接'}")
                print(f"   数据源: {status['data_source']}")
                print(f"   预测间隔: {status['prediction_interval']}秒")
                print(f"   预测数量: {status['predictions_count']}")

                # 显示MT5状态详情
                mt5_status = status['mt5_status']
                if mt5_status['connected']:
                    print(f"   MT5符号: {mt5_status['symbol']}")
                    print(f"   当前价格: ${mt5_status['current_price']:.2f}")
                    print(f"   买价/卖价: ${mt5_status['bid']:.2f} / ${mt5_status['ask']:.2f}")
                else:
                    print(f"   MT5错误: {mt5_status.get('error', '未知错误')}")

                if status['last_prediction']:
                    last = status['last_prediction']
                    print(f"   最新预测: {last['signal']} (${last['current_price']:.2f} -> ${last['predicted_price']:.2f})")
            elif choice == '4':
                try:
                    interval = int(input("请输入预测间隔（秒，最小60）: "))
                    system.set_prediction_interval(interval)
                    print(f"✅ 预测间隔已设置为: {interval}秒")
                except ValueError:
                    print("❌ 输入无效")
            elif choice == '5':
                history = system.prediction_history[-10:]  # 显示最近10个
                if history:
                    print(f"最近 {len(history)} 个预测:")
                    for i, pred in enumerate(reversed(history), 1):
                        timestamp = datetime.fromisoformat(pred['timestamp']).strftime('%H:%M:%S')
                        print(f"   {i}. {timestamp}: {pred['signal']} ${pred['current_price']:.2f} -> ${pred['predicted_price']:.2f}")
                else:
                    print("暂无预测历史")
            elif choice == '6':
                print("测试微信连接...")
                if system.wechat_sender.connect_wechat():
                    groups = system.wechat_sender.get_group_list()
                    print(f"✅ 微信连接成功，找到 {len(groups)} 个群聊")
                    system.wechat_sender.disconnect_wechat()
                else:
                    print("❌ 微信连接失败")
            else:
                print("无效选择，请重试")
    
    except KeyboardInterrupt:
        print("\n\n系统被用户中断")
    finally:
        system.stop_system()
        print("Demo系统已退出")

def main():
    """主函数"""
    print("🎯 黄金价格预测微信发送Demo系统 (MT5版)")
    print("=" * 50)
    print("此Demo系统集成了:")
    print("  📈 基于MT5的黄金价格预测算法")
    print("  📱 微信群消息自动发送")
    print("  ⏰ 定时预测生成")
    print("  📊 预测历史记录")
    print("  🔗 MetaTrader5实时数据源")
    print("=" * 50)

    # 检查依赖
    try:
        import pandas
        import numpy
        import MetaTrader5
        print("✅ 依赖项检查通过")
    except ImportError as e:
        print(f"❌ 缺少依赖项: {e}")
        print("请安装: pip install pandas numpy MetaTrader5")
        print("并确保MetaTrader5终端已安装并运行")
        return
    
    # 启动交互式Demo
    interactive_demo()

if __name__ == "__main__":
    main()
