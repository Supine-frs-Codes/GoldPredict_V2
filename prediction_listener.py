#!/usr/bin/env python3
"""
预测结果监听器
监听黄金价格预测系统的结果，并自动发送到微信群
"""

import json
import time
import threading
import logging
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, List
import sqlite3
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from wechat_sender import WeChatSender

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PredictionFileHandler(FileSystemEventHandler):
    """预测文件变化处理器"""
    
    def __init__(self, listener):
        self.listener = listener
        self.last_modified = {}
        
    def on_modified(self, event):
        """文件修改事件"""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        
        # 只监听预测结果文件
        if file_path.suffix == '.json' and any(keyword in file_path.name.lower() 
                                              for keyword in ['prediction', 'latest']):
            # 防止重复触发
            current_time = time.time()
            if file_path in self.last_modified:
                if current_time - self.last_modified[file_path] < 2:  # 2秒内不重复处理
                    return
            
            self.last_modified[file_path] = current_time
            
            logger.info(f"检测到预测文件更新: {file_path}")
            self.listener.handle_prediction_file_update(file_path)

class PredictionListener:
    """预测结果监听器"""
    
    def __init__(self, config_file: str = "listener_config.json"):
        """
        初始化监听器
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = Path(config_file)
        self.config = self._load_config()
        self.wechat_sender = WeChatSender()
        self.is_running = False
        self.observer = None
        self.api_thread = None
        self.last_sent_predictions = {}  # 记录最后发送的预测，避免重复发送
        
        # 初始化数据库
        self._init_database()
        
    def _load_config(self) -> Dict:
        """加载配置文件"""
        default_config = {
            "monitoring": {
                "file_paths": [
                    "results/realtime/latest_prediction.json",
                    "results/predictions/web_simple_prediction.json",
                    "results/predictions/improved_predictions.json"
                ],
                "api_endpoints": [
                    "http://localhost:5000/api/prediction/latest",
                    "http://localhost:5000/api/prediction/realtime",
                    "http://localhost:5000/api/prediction/ai_enhanced",
                    "http://localhost:5000/api/prediction/traditional",
                    "http://localhost:5000/api/prediction/auto_trading"
                ],
                "check_interval_seconds": 30,
                "enable_file_monitoring": True,
                "enable_api_monitoring": True
            },
            "filtering": {
                "min_time_between_sends": 300,  # 5分钟
                "deduplicate_predictions": True,
                "max_predictions_per_hour": 12
            },
            "logging": {
                "log_file": "prediction_listener.log",
                "log_level": "INFO"
            }
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 合并默认配置
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            except Exception as e:
                logger.error(f"加载配置文件失败: {e}")
                return default_config
        else:
            self._save_config(default_config)
            return default_config
    
    def _save_config(self, config: Dict):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            logger.info(f"配置文件已保存: {self.config_file}")
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
    
    def _init_database(self):
        """初始化数据库"""
        try:
            db_path = Path("results/listener_history.db")
            db_path.parent.mkdir(parents=True, exist_ok=True)
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sent_predictions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        prediction_hash TEXT NOT NULL,
                        source TEXT NOT NULL,
                        current_price REAL,
                        predicted_price REAL,
                        signal TEXT,
                        confidence REAL,
                        sent_groups TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                conn.commit()
                
            logger.info("数据库初始化完成")
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
    
    def _get_prediction_hash(self, prediction_data: Dict) -> str:
        """生成预测数据的哈希值，用于去重"""
        try:
            # 使用关键字段生成哈希
            key_fields = {
                'timestamp': prediction_data.get('timestamp', ''),
                'current_price': prediction_data.get('current_price', 0),
                'predicted_price': prediction_data.get('predicted_price', 0),
                'signal': prediction_data.get('signal', ''),
                'confidence': prediction_data.get('confidence', 0)
            }
            return str(hash(json.dumps(key_fields, sort_keys=True)))
        except Exception as e:
            logger.error(f"生成预测哈希失败: {e}")
            return str(time.time())
    
    def _should_send_prediction(self, prediction_data: Dict, source: str) -> bool:
        """判断是否应该发送预测"""
        try:
            # 生成预测哈希
            pred_hash = self._get_prediction_hash(prediction_data)
            
            # 检查是否重复
            if self.config['filtering']['deduplicate_predictions']:
                db_path = Path("results/listener_history.db")
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        'SELECT COUNT(*) FROM sent_predictions WHERE prediction_hash = ?',
                        (pred_hash,)
                    )
                    if cursor.fetchone()[0] > 0:
                        logger.info(f"预测已发送过，跳过: {pred_hash}")
                        return False
            
            # 检查时间间隔
            min_interval = self.config['filtering']['min_time_between_sends']
            if source in self.last_sent_predictions:
                last_sent_time = self.last_sent_predictions[source]
                if time.time() - last_sent_time < min_interval:
                    logger.info(f"发送间隔太短，跳过: {source}")
                    return False
            
            # 检查每小时发送限制
            max_per_hour = self.config['filtering']['max_predictions_per_hour']
            if max_per_hour > 0:
                db_path = Path("results/listener_history.db")
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.cursor()
                    one_hour_ago = datetime.now() - timedelta(hours=1)
                    cursor.execute(
                        'SELECT COUNT(*) FROM sent_predictions WHERE created_at > ?',
                        (one_hour_ago.isoformat(),)
                    )
                    if cursor.fetchone()[0] >= max_per_hour:
                        logger.info(f"已达到每小时发送限制: {max_per_hour}")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"检查发送条件时出错: {e}")
            return False
    
    def _record_sent_prediction(self, prediction_data: Dict, source: str, sent_groups: List[str]):
        """记录已发送的预测"""
        try:
            pred_hash = self._get_prediction_hash(prediction_data)
            
            db_path = Path("results/listener_history.db")
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO sent_predictions (
                        timestamp, prediction_hash, source, current_price, 
                        predicted_price, signal, confidence, sent_groups
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    prediction_data.get('timestamp', ''),
                    pred_hash,
                    source,
                    prediction_data.get('current_price', 0),
                    prediction_data.get('predicted_price', 0),
                    prediction_data.get('signal', ''),
                    prediction_data.get('confidence', 0),
                    json.dumps(sent_groups)
                ))
                conn.commit()
            
            # 更新最后发送时间
            self.last_sent_predictions[source] = time.time()
            
        except Exception as e:
            logger.error(f"记录发送历史失败: {e}")
    
    def handle_prediction_file_update(self, file_path: Path):
        """处理预测文件更新"""
        try:
            logger.info(f"处理预测文件: {file_path}")
            
            # 读取预测数据
            with open(file_path, 'r', encoding='utf-8') as f:
                prediction_data = json.load(f)
            
            # 检查是否应该发送
            if not self._should_send_prediction(prediction_data, str(file_path)):
                return
            
            # 发送到微信群
            result = self.wechat_sender.send_prediction_to_groups(prediction_data)
            
            if result['success']:
                logger.info(f"预测结果已发送到微信群: {result['sent_groups']}")
                self._record_sent_prediction(prediction_data, str(file_path), result['sent_groups'])
            else:
                logger.error(f"发送预测结果失败: {result['errors']}")
                
        except Exception as e:
            logger.error(f"处理预测文件更新时出错: {e}")
    
    def handle_api_prediction(self, api_url: str, prediction_data: Dict):
        """处理API预测数据"""
        try:
            logger.info(f"处理API预测: {api_url}")
            
            # 检查是否应该发送
            if not self._should_send_prediction(prediction_data, api_url):
                return
            
            # 发送到微信群
            result = self.wechat_sender.send_prediction_to_groups(prediction_data)
            
            if result['success']:
                logger.info(f"API预测结果已发送到微信群: {result['sent_groups']}")
                self._record_sent_prediction(prediction_data, api_url, result['sent_groups'])
            else:
                logger.error(f"发送API预测结果失败: {result['errors']}")
                
        except Exception as e:
            logger.error(f"处理API预测时出错: {e}")
    
    def _monitor_api_endpoints(self):
        """监控API端点"""
        api_endpoints = self.config['monitoring']['api_endpoints']
        check_interval = self.config['monitoring']['check_interval_seconds']
        
        while self.is_running:
            try:
                for api_url in api_endpoints:
                    try:
                        response = requests.get(api_url, timeout=10)
                        if response.status_code == 200:
                            prediction_data = response.json()
                            
                            # 检查数据是否有效
                            if prediction_data and 'current_price' in prediction_data:
                                self.handle_api_prediction(api_url, prediction_data)
                        else:
                            logger.warning(f"API请求失败: {api_url} - {response.status_code}")
                            
                    except requests.RequestException as e:
                        logger.warning(f"API请求异常: {api_url} - {e}")
                    except Exception as e:
                        logger.error(f"处理API响应时出错: {api_url} - {e}")
                
                time.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"API监控循环出错: {e}")
                time.sleep(check_interval)
    
    def start_monitoring(self):
        """开始监控"""
        if self.is_running:
            logger.warning("监控已在运行中")
            return
        
        logger.info("启动预测结果监控...")
        self.is_running = True
        
        # 连接微信
        if not self.wechat_sender.connect_wechat():
            logger.error("微信连接失败，无法启动监控")
            self.is_running = False
            return False
        
        # 启动文件监控
        if self.config['monitoring']['enable_file_monitoring']:
            try:
                self.observer = Observer()
                handler = PredictionFileHandler(self)
                
                # 监控预测结果目录
                watch_dirs = set()
                for file_path in self.config['monitoring']['file_paths']:
                    watch_dir = Path(file_path).parent
                    if watch_dir.exists():
                        watch_dirs.add(str(watch_dir))
                
                for watch_dir in watch_dirs:
                    self.observer.schedule(handler, watch_dir, recursive=False)
                    logger.info(f"开始监控目录: {watch_dir}")
                
                self.observer.start()
                logger.info("文件监控已启动")
                
            except Exception as e:
                logger.error(f"启动文件监控失败: {e}")
        
        # 启动API监控
        if self.config['monitoring']['enable_api_monitoring']:
            try:
                self.api_thread = threading.Thread(target=self._monitor_api_endpoints, daemon=True)
                self.api_thread.start()
                logger.info("API监控已启动")
            except Exception as e:
                logger.error(f"启动API监控失败: {e}")
        
        logger.info("预测结果监控已启动")
        return True
    
    def stop_monitoring(self):
        """停止监控"""
        if not self.is_running:
            logger.warning("监控未在运行")
            return
        
        logger.info("停止预测结果监控...")
        self.is_running = False
        
        # 停止文件监控
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            logger.info("文件监控已停止")
        
        # API监控线程会自动停止（daemon线程）
        
        # 断开微信连接
        self.wechat_sender.disconnect_wechat()
        
        logger.info("预测结果监控已停止")
    
    def get_status(self) -> Dict:
        """获取监控状态"""
        return {
            'running': self.is_running,
            'wechat_connected': self.wechat_sender.is_connected,
            'file_monitoring': self.config['monitoring']['enable_file_monitoring'],
            'api_monitoring': self.config['monitoring']['enable_api_monitoring'],
            'monitored_files': self.config['monitoring']['file_paths'],
            'monitored_apis': self.config['monitoring']['api_endpoints'],
            'last_sent_predictions': dict(self.last_sent_predictions)
        }
    
    def get_send_history(self, limit: int = 50) -> List[Dict]:
        """获取发送历史"""
        try:
            db_path = Path("results/listener_history.db")
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM sent_predictions 
                    ORDER BY created_at DESC 
                    LIMIT ?
                ''', (limit,))
                
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                
                return [dict(zip(columns, row)) for row in rows]
                
        except Exception as e:
            logger.error(f"获取发送历史失败: {e}")
            return []


def main():
    """主函数 - 用于测试"""
    print("🎯 预测结果监听器")
    print("=" * 50)
    
    listener = PredictionListener()
    
    try:
        # 显示配置
        print("当前配置:")
        print(f"  监控文件: {listener.config['monitoring']['file_paths']}")
        print(f"  监控API: {listener.config['monitoring']['api_endpoints']}")
        print(f"  检查间隔: {listener.config['monitoring']['check_interval_seconds']}秒")
        
        # 启动监控
        if listener.start_monitoring():
            print("\n✅ 监控已启动，按 Ctrl+C 停止...")
            
            # 保持运行
            while True:
                time.sleep(1)
        else:
            print("❌ 监控启动失败")
            
    except KeyboardInterrupt:
        print("\n\n停止监控...")
        listener.stop_monitoring()
        print("监控已停止")
    except Exception as e:
        print(f"❌ 运行出错: {e}")
        listener.stop_monitoring()


if __name__ == "__main__":
    main()
