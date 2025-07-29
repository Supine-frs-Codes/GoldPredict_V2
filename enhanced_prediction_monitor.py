#!/usr/bin/env python3
"""
增强预测监控器
专门用于监控统一预测平台2.0中各个系统的预测结果
并自动发送到微信群聊
"""

import json
import time
import threading
import logging
from datetime import datetime, timedelta
from pathlib import Path
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PredictionFileHandler(FileSystemEventHandler):
    """预测文件变化处理器"""
    
    def __init__(self, monitor):
        self.monitor = monitor
        self.last_modified = {}
        
    def on_modified(self, event):
        """文件修改事件"""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        
        # 监听预测结果文件
        if file_path.suffix == '.json' and any(keyword in file_path.name.lower() 
                                              for keyword in ['prediction', 'result', 'forecast']):
            # 防止重复触发
            current_time = time.time()
            if file_path in self.last_modified:
                if current_time - self.last_modified[file_path] < 3:  # 3秒内不重复处理
                    return
            
            self.last_modified[file_path] = current_time
            
            logger.info(f"检测到预测文件更新: {file_path}")
            self.monitor.handle_prediction_file_update(file_path)

class EnhancedPredictionMonitor:
    """增强预测监控器"""
    
    def __init__(self, unified_platform_url="http://localhost:5000"):
        self.unified_platform_url = unified_platform_url
        self.is_running = False
        self.observer = None
        self.api_thread = None
        self.last_sent_predictions = {}
        
        # 监控配置
        self.config = {
            'file_paths': [
                'results/realtime/',
                'results/ai_enhanced/',
                'results/traditional/',
                'results/auto_trading/',
                'results/simple/',
                'results/predictions/'
            ],
            'api_endpoints': [
                f"{unified_platform_url}/api/prediction/realtime",
                f"{unified_platform_url}/api/prediction/ai_enhanced",
                f"{unified_platform_url}/api/prediction/traditional",
                f"{unified_platform_url}/api/prediction/auto_trading",
                f"{unified_platform_url}/api/prediction/simple"
            ],
            'check_interval_seconds': 30,
            'min_time_between_sends': 300,  # 5分钟
            'enable_file_monitoring': True,
            'enable_api_monitoring': True
        }
        
        # 系统映射
        self.system_mapping = {
            'realtime': '实时预测系统',
            'ai_enhanced': '增强AI系统',
            'traditional': '传统ML系统',
            'auto_trading': '自动交易系统',
            'simple': '简单预测系统'
        }
    
    def start_monitoring(self):
        """启动监控"""
        if self.is_running:
            logger.warning("监控已在运行中")
            return False
        
        logger.info("启动增强预测监控器...")
        self.is_running = True
        
        # 启动文件监控
        if self.config['enable_file_monitoring']:
            try:
                self.observer = Observer()
                handler = PredictionFileHandler(self)
                
                # 监控预测结果目录
                for dir_path in self.config['file_paths']:
                    watch_dir = Path(dir_path)
                    if watch_dir.exists():
                        self.observer.schedule(handler, str(watch_dir), recursive=True)
                        logger.info(f"开始监控目录: {watch_dir}")
                    else:
                        logger.warning(f"监控目录不存在: {watch_dir}")
                
                self.observer.start()
                logger.info("文件监控已启动")
                
            except Exception as e:
                logger.error(f"启动文件监控失败: {e}")
        
        # 启动API监控
        if self.config['enable_api_monitoring']:
            try:
                self.api_thread = threading.Thread(target=self._monitor_api_endpoints, daemon=True)
                self.api_thread.start()
                logger.info("API监控已启动")
            except Exception as e:
                logger.error(f"启动API监控失败: {e}")
        
        logger.info("增强预测监控器已启动")
        return True
    
    def stop_monitoring(self):
        """停止监控"""
        if not self.is_running:
            logger.warning("监控未在运行")
            return
        
        logger.info("停止增强预测监控器...")
        self.is_running = False
        
        # 停止文件监控
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            logger.info("文件监控已停止")
        
        logger.info("增强预测监控器已停止")
    
    def handle_prediction_file_update(self, file_path: Path):
        """处理预测文件更新"""
        try:
            logger.info(f"处理预测文件: {file_path}")
            
            # 读取预测数据
            with open(file_path, 'r', encoding='utf-8') as f:
                prediction_data = json.load(f)
            
            # 确定系统类型
            system_name = self._determine_system_from_path(file_path)
            
            # 检查是否应该发送
            if not self._should_send_prediction(prediction_data, system_name):
                return
            
            # 发送到统一平台的微信系统
            result = self._send_to_wechat_system(system_name, prediction_data)
            
            if result:
                logger.info(f"预测结果已发送到微信: {system_name}")
                self.last_sent_predictions[system_name] = time.time()
            else:
                logger.error(f"发送预测结果失败: {system_name}")
                
        except Exception as e:
            logger.error(f"处理预测文件更新时出错: {e}")
    
    def _monitor_api_endpoints(self):
        """监控API端点"""
        while self.is_running:
            try:
                for api_url in self.config['api_endpoints']:
                    try:
                        response = requests.get(api_url, timeout=10)
                        if response.status_code == 200:
                            prediction_data = response.json()
                            
                            # 确定系统类型
                            system_name = self._determine_system_from_api(api_url)
                            
                            # 检查数据是否有效
                            if prediction_data and 'current_price' in prediction_data:
                                if self._should_send_prediction(prediction_data, system_name):
                                    result = self._send_to_wechat_system(system_name, prediction_data)
                                    if result:
                                        logger.info(f"API预测结果已发送到微信: {system_name}")
                                        self.last_sent_predictions[system_name] = time.time()
                        else:
                            logger.warning(f"API请求失败: {api_url} - {response.status_code}")
                            
                    except requests.RequestException as e:
                        logger.debug(f"API请求异常: {api_url} - {e}")
                    except Exception as e:
                        logger.error(f"处理API响应时出错: {api_url} - {e}")
                
                time.sleep(self.config['check_interval_seconds'])
                
            except Exception as e:
                logger.error(f"API监控循环出错: {e}")
                time.sleep(60)
    
    def _determine_system_from_path(self, file_path: Path) -> str:
        """从文件路径确定系统类型"""
        path_str = str(file_path).lower()
        
        if 'realtime' in path_str:
            return 'realtime'
        elif 'ai_enhanced' in path_str or 'ai' in path_str:
            return 'ai_enhanced'
        elif 'traditional' in path_str or 'ml' in path_str:
            return 'traditional'
        elif 'trading' in path_str or 'auto' in path_str:
            return 'auto_trading'
        elif 'simple' in path_str:
            return 'simple'
        else:
            return 'unknown'
    
    def _determine_system_from_api(self, api_url: str) -> str:
        """从API URL确定系统类型"""
        if 'realtime' in api_url:
            return 'realtime'
        elif 'ai_enhanced' in api_url:
            return 'ai_enhanced'
        elif 'traditional' in api_url:
            return 'traditional'
        elif 'auto_trading' in api_url:
            return 'auto_trading'
        elif 'simple' in api_url:
            return 'simple'
        else:
            return 'unknown'
    
    def _should_send_prediction(self, prediction_data: dict, system_name: str) -> bool:
        """判断是否应该发送预测"""
        try:
            # 检查时间间隔
            min_interval = self.config['min_time_between_sends']
            if system_name in self.last_sent_predictions:
                last_sent_time = self.last_sent_predictions[system_name]
                if time.time() - last_sent_time < min_interval:
                    logger.debug(f"发送间隔太短，跳过: {system_name}")
                    return False
            
            # 检查预测数据的基本有效性
            required_fields = ['current_price', 'predicted_price', 'confidence']
            for field in required_fields:
                if field not in prediction_data:
                    logger.warning(f"预测数据缺少必需字段: {field}")
                    return False
            
            # 检查置信度
            confidence = prediction_data.get('confidence', 0)
            if confidence < 0.3:  # 最小置信度阈值
                logger.debug(f"置信度太低，跳过发送: {confidence}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"检查发送条件时出错: {e}")
            return False
    
    def _send_to_wechat_system(self, system_name: str, prediction_data: dict) -> bool:
        """发送预测结果到统一平台的微信系统"""
        try:
            # 添加系统信息
            enhanced_data = prediction_data.copy()
            enhanced_data['source_system'] = system_name
            enhanced_data['system_name'] = self.system_mapping.get(system_name, system_name)
            
            # 发送到统一平台的微信API
            api_url = f"{self.unified_platform_url}/api/wechat/test-prediction/{system_name}"
            
            response = requests.post(api_url, json=enhanced_data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return result.get('success', False)
            else:
                logger.error(f"微信发送API请求失败: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"发送到微信系统失败: {e}")
            return False
    
    def get_status(self) -> dict:
        """获取监控状态"""
        return {
            'running': self.is_running,
            'file_monitoring': self.config['enable_file_monitoring'],
            'api_monitoring': self.config['enable_api_monitoring'],
            'monitored_paths': self.config['file_paths'],
            'monitored_apis': self.config['api_endpoints'],
            'last_sent_predictions': dict(self.last_sent_predictions)
        }

def main():
    """主函数 - 用于独立运行"""
    print("🔍 增强预测监控器")
    print("=" * 50)
    print("监控统一预测平台2.0的各个系统预测结果")
    print("并自动发送到微信群聊")
    print("=" * 50)
    
    monitor = EnhancedPredictionMonitor()
    
    try:
        # 显示配置
        print("监控配置:")
        print(f"  文件监控: {monitor.config['enable_file_monitoring']}")
        print(f"  API监控: {monitor.config['enable_api_monitoring']}")
        print(f"  检查间隔: {monitor.config['check_interval_seconds']}秒")
        print(f"  发送间隔: {monitor.config['min_time_between_sends']}秒")
        
        # 启动监控
        if monitor.start_monitoring():
            print("\n✅ 监控已启动，按 Ctrl+C 停止...")
            
            # 保持运行
            while True:
                time.sleep(1)
        else:
            print("❌ 监控启动失败")
            
    except KeyboardInterrupt:
        print("\n\n停止监控...")
        monitor.stop_monitoring()
        print("监控已停止")
    except Exception as e:
        print(f"❌ 运行出错: {e}")
        monitor.stop_monitoring()

if __name__ == "__main__":
    main()
