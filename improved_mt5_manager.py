#!/usr/bin/env python3
"""
改进的MT5连接管理器
解决连接不稳定问题，实现持久连接和智能重连
"""

import MetaTrader5 as mt5
import time
import threading
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ImprovedMT5Manager:
    """改进的MT5连接管理器"""
    
    def __init__(self):
        self.connected = False
        self.connection_lock = threading.Lock()
        self.last_connection_time = None
        self.connection_attempts = 0
        self.max_connection_attempts = 5
        self.reconnect_delay = 10  # 秒
        
        # 连接健康检查
        self.last_successful_request = None
        self.health_check_interval = 30  # 秒
        
        # 黄金符号缓存
        self.gold_symbol = None
        self.symbol_cache_time = None
        self.symbol_cache_duration = 300  # 5分钟
        
        print("[MT5管理器] 改进的MT5连接管理器初始化")
    
    def ensure_connection(self) -> bool:
        """确保MT5连接可用"""
        with self.connection_lock:
            # 检查现有连接
            if self.connected and self._is_connection_healthy():
                return True
            
            # 尝试连接
            return self._establish_connection()
    
    def _is_connection_healthy(self) -> bool:
        """检查连接健康状态"""
        try:
            # 检查MT5终端信息
            terminal_info = mt5.terminal_info()
            if terminal_info is None:
                logger.warning("MT5终端信息获取失败，连接可能已断开")
                return False
            
            # 检查账户信息
            account_info = mt5.account_info()
            if account_info is None:
                logger.warning("MT5账户信息获取失败")
                # 账户信息失败不一定意味着连接断开，继续检查
            
            # 更新最后成功请求时间
            self.last_successful_request = datetime.now()
            return True
            
        except Exception as e:
            logger.error(f"连接健康检查失败: {e}")
            return False
    
    def _establish_connection(self) -> bool:
        """建立MT5连接"""
        try:
            # 如果已连接，先断开
            if self.connected:
                self._safe_disconnect()
            
            # 尝试初始化连接
            if not mt5.initialize():
                logger.error("MT5初始化失败")
                return False
            
            # 验证连接
            terminal_info = mt5.terminal_info()
            if terminal_info is None:
                logger.error("无法获取MT5终端信息")
                mt5.shutdown()
                return False
            
            # 连接成功
            self.connected = True
            self.last_connection_time = datetime.now()
            self.connection_attempts = 0
            
            logger.info(f"MT5连接成功 - 终端: {terminal_info.name}")
            
            # 获取账户信息（可选）
            account_info = mt5.account_info()
            if account_info:
                logger.info(f"账户: {account_info.login}")
            
            return True
            
        except Exception as e:
            logger.error(f"MT5连接建立失败: {e}")
            self.connected = False
            return False
    
    def _safe_disconnect(self):
        """安全断开连接"""
        try:
            if self.connected:
                mt5.shutdown()
                self.connected = False
                logger.info("MT5连接已断开")
        except Exception as e:
            logger.error(f"断开连接时出错: {e}")
            self.connected = False
    
    def get_gold_symbol(self) -> Optional[str]:
        """获取黄金交易符号（带缓存）"""
        # 检查缓存
        if (self.gold_symbol and self.symbol_cache_time and 
            datetime.now() - self.symbol_cache_time < timedelta(seconds=self.symbol_cache_duration)):
            return self.gold_symbol
        
        # 确保连接
        if not self.ensure_connection():
            return None
        
        try:
            # 常见黄金符号
            gold_symbols = ['XAUUSD', 'GOLD', 'XAU/USD', 'XAUUSD.', 'XAUUSD#']
            
            # 获取所有可用符号
            symbols = mt5.symbols_get()
            if symbols is None:
                logger.error("无法获取交易符号列表")
                return None
            
            available_symbols = [s.name for s in symbols]
            
            # 查找黄金符号
            for symbol in gold_symbols:
                if symbol in available_symbols:
                    self.gold_symbol = symbol
                    self.symbol_cache_time = datetime.now()
                    logger.info(f"找到黄金符号: {symbol}")
                    return symbol
            
            # 模糊匹配
            for symbol in available_symbols:
                if 'XAU' in symbol.upper() or 'GOLD' in symbol.upper():
                    self.gold_symbol = symbol
                    self.symbol_cache_time = datetime.now()
                    logger.info(f"找到可能的黄金符号: {symbol}")
                    return symbol
            
            logger.warning("未找到黄金交易符号")
            return None
            
        except Exception as e:
            logger.error(f"获取黄金符号失败: {e}")
            return None
    
    def get_current_price(self, symbol: str = None) -> Optional[Dict[str, Any]]:
        """获取当前价格（带重试机制）"""
        if not symbol:
            symbol = self.get_gold_symbol()
            if not symbol:
                return None
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # 确保连接
                if not self.ensure_connection():
                    logger.warning(f"连接失败，尝试 {attempt + 1}/{max_retries}")
                    time.sleep(2)
                    continue
                
                # 获取报价
                tick = mt5.symbol_info_tick(symbol)
                if tick is None:
                    logger.warning(f"无法获取 {symbol} 的报价，尝试 {attempt + 1}/{max_retries}")
                    time.sleep(1)
                    continue
                
                # 成功获取数据
                self.last_successful_request = datetime.now()
                
                return {
                    'symbol': symbol,
                    'bid': float(tick.bid),
                    'ask': float(tick.ask),
                    'last': float(tick.last) if hasattr(tick, 'last') else 0.0,
                    'time': datetime.fromtimestamp(tick.time),
                    'volume': int(tick.volume) if hasattr(tick, 'volume') else 0
                }
                
            except Exception as e:
                logger.error(f"获取价格失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    # 强制重连
                    self.connected = False
        
        return None
    
    def get_historical_data(self, symbol: str = None, timeframe=mt5.TIMEFRAME_M1, 
                           count: int = 100) -> Optional[Dict[str, Any]]:
        """获取历史数据"""
        if not symbol:
            symbol = self.get_gold_symbol()
            if not symbol:
                return None
        
        try:
            # 确保连接
            if not self.ensure_connection():
                return None
            
            # 获取历史数据
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
            if rates is None or len(rates) == 0:
                logger.error(f"无法获取 {symbol} 的历史数据")
                return None
            
            # 转换为更友好的格式
            import pandas as pd
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            return {
                'symbol': symbol,
                'timeframe': timeframe,
                'count': len(df),
                'data': df
            }
            
        except Exception as e:
            logger.error(f"获取历史数据失败: {e}")
            return None
    
    def get_connection_status(self) -> Dict[str, Any]:
        """获取连接状态信息"""
        status = {
            'connected': self.connected,
            'last_connection_time': self.last_connection_time.isoformat() if self.last_connection_time else None,
            'last_successful_request': self.last_successful_request.isoformat() if self.last_successful_request else None,
            'connection_attempts': self.connection_attempts,
            'gold_symbol': self.gold_symbol
        }
        
        if self.connected:
            try:
                terminal_info = mt5.terminal_info()
                if terminal_info:
                    status['terminal_name'] = terminal_info.name
                    status['terminal_build'] = terminal_info.build
                    status['terminal_connected'] = terminal_info.connected
                
                account_info = mt5.account_info()
                if account_info:
                    status['account_login'] = account_info.login
                    status['account_server'] = account_info.server
                    status['account_currency'] = account_info.currency
                    
            except Exception as e:
                logger.error(f"获取状态信息失败: {e}")
                status['status_error'] = str(e)
        
        return status
    
    def test_connection(self) -> bool:
        """测试连接功能"""
        print("[测试] MT5连接测试开始...")
        
        # 1. 基础连接测试
        if not self.ensure_connection():
            print("❌ 基础连接失败")
            return False
        print("✅ 基础连接成功")
        
        # 2. 符号查找测试
        symbol = self.get_gold_symbol()
        if not symbol:
            print("❌ 黄金符号查找失败")
            return False
        print(f"✅ 黄金符号: {symbol}")
        
        # 3. 价格获取测试
        price_data = self.get_current_price(symbol)
        if not price_data:
            print("❌ 价格获取失败")
            return False
        print(f"✅ 当前价格: Bid={price_data['bid']:.2f}, Ask={price_data['ask']:.2f}")
        
        # 4. 连续获取测试
        print("🔄 连续获取测试 (5次)...")
        for i in range(5):
            price_data = self.get_current_price(symbol)
            if price_data:
                main_price = price_data['last'] if price_data['last'] > 0 else price_data['bid']
                print(f"   {i+1}. ${main_price:.2f}")
                time.sleep(1)
            else:
                print(f"   {i+1}. 获取失败")
                return False
        
        print("✅ 连续获取测试成功")
        
        # 5. 状态信息测试
        status = self.get_connection_status()
        print(f"✅ 连接状态: {status}")
        
        print("🎉 MT5连接测试完成!")
        return True
    
    def cleanup(self):
        """清理资源"""
        print("[清理] 清理MT5连接资源...")
        self._safe_disconnect()


# 全局MT5管理器实例
mt5_manager = ImprovedMT5Manager()


def get_mt5_manager() -> ImprovedMT5Manager:
    """获取全局MT5管理器实例"""
    return mt5_manager


def main():
    """测试函数"""
    print("改进的MT5连接管理器测试")
    print("=" * 40)
    
    manager = ImprovedMT5Manager()
    
    try:
        # 运行连接测试
        success = manager.test_connection()
        
        if success:
            print("\n🎉 所有测试通过!")
            
            # 持续监控测试
            print("\n🔄 持续监控测试 (30秒)...")
            start_time = time.time()
            
            while time.time() - start_time < 30:
                symbol = manager.get_gold_symbol()
                if symbol:
                    price_data = manager.get_current_price(symbol)
                    if price_data:
                        main_price = price_data['last'] if price_data['last'] > 0 else price_data['bid']
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] ${main_price:.2f}")
                    else:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] 价格获取失败")
                
                time.sleep(5)
            
            print("✅ 持续监控测试完成")
        else:
            print("\n❌ 测试失败")
    
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断测试")
    
    finally:
        manager.cleanup()


if __name__ == "__main__":
    main()
