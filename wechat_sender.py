#!/usr/bin/env python3
"""
微信消息发送模块
支持自动发送黄金价格预测结果到指定微信群
"""

import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import threading

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WeChatSender:
    """微信消息发送器"""
    
    def __init__(self, config_file: str = "wechat_config.json"):
        """
        初始化微信发送器
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = Path(config_file)
        self.config = self._load_config()
        self.wx = None
        self.is_connected = False
        self.last_error = None
        
    def _load_config(self) -> Dict:
        """加载配置文件"""
        default_config = {
            "target_groups": [],  # 目标群聊名称列表
            "message_template": {
                "title": "🏆 黄金价格预测报告",
                "format": """
📊 **黄金价格预测更新**

🕐 时间: {timestamp}
💰 当前价格: ${current_price:.2f}
🎯 预测价格: ${predicted_price:.2f}
📈 价格变化: {price_change:+.2f} ({price_change_pct:+.2f}%)
🔮 交易信号: {signal}
📊 置信度: {confidence:.1%}

⚡ 预测方法: {method}
🎯 目标时间: {target_time}

---
💡 此预测仅供参考，投资有风险，请谨慎决策！
                """.strip()
            },
            "send_conditions": {
                "min_confidence": 0.3,  # 最小置信度
                "min_price_change_pct": 0.1,  # 最小价格变化百分比
                "cooldown_minutes": 5  # 发送冷却时间（分钟）
            },
            "retry_settings": {
                "max_retries": 3,
                "retry_delay": 5
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
            # 创建默认配置文件
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
    
    def connect_wechat(self) -> bool:
        """连接微信"""
        try:
            # 尝试导入wxauto
            try:
                from wxauto import WeChat
                logger.info("使用wxauto库连接微信")
            except ImportError:
                logger.error("wxauto库未安装，请运行: pip install wxauto")
                return False
            
            # 初始化微信连接
            self.wx = WeChat()
            
            # 检查微信是否已登录
            if self.wx:
                self.is_connected = True
                logger.info("微信连接成功")
                return True
            else:
                logger.error("微信连接失败")
                return False
                
        except Exception as e:
            logger.error(f"连接微信时出错: {e}")
            self.last_error = str(e)
            return False
    
    def disconnect_wechat(self):
        """断开微信连接"""
        try:
            if self.wx:
                self.wx = None
            self.is_connected = False
            logger.info("微信连接已断开")
        except Exception as e:
            logger.error(f"断开微信连接时出错: {e}")
    
    def get_group_list(self) -> List[str]:
        """获取群聊列表"""
        if not self.is_connected or not self.wx:
            logger.error("微信未连接")
            return []
        
        try:
            # 获取所有聊天对象
            chat_list = self.wx.GetAllMessage()
            groups = []
            
            for chat in chat_list:
                if chat.get('type') == 'group':  # 群聊
                    groups.append(chat.get('name', ''))
            
            return groups
        except Exception as e:
            logger.error(f"获取群聊列表失败: {e}")
            return []
    
    def format_prediction_message(self, prediction_data: Dict) -> str:
        """格式化预测消息"""
        try:
            template = self.config['message_template']['format']
            
            # 处理时间格式
            timestamp = prediction_data.get('timestamp', '')
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    timestamp = dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass
            
            # 处理目标时间
            target_time = prediction_data.get('target_time', '')
            if target_time:
                try:
                    dt = datetime.fromisoformat(target_time.replace('Z', '+00:00'))
                    target_time = dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass
            
            # 计算价格变化
            current_price = prediction_data.get('current_price', 0)
            predicted_price = prediction_data.get('predicted_price', 0)
            price_change = predicted_price - current_price
            price_change_pct = (price_change / max(current_price, 1)) * 100
            
            # 格式化消息
            message = template.format(
                timestamp=timestamp,
                current_price=current_price,
                predicted_price=predicted_price,
                price_change=price_change,
                price_change_pct=price_change_pct,
                signal=prediction_data.get('signal', '未知'),
                confidence=prediction_data.get('confidence', 0),
                method=prediction_data.get('method', '技术分析'),
                target_time=target_time
            )
            
            return message
            
        except Exception as e:
            logger.error(f"格式化消息失败: {e}")
            return f"预测数据格式化失败: {e}"
    
    def should_send_message(self, prediction_data: Dict) -> bool:
        """判断是否应该发送消息"""
        try:
            conditions = self.config['send_conditions']
            
            # 检查置信度
            confidence = prediction_data.get('confidence', 0)
            if confidence < conditions['min_confidence']:
                logger.info(f"置信度过低 ({confidence:.2%} < {conditions['min_confidence']:.2%})，跳过发送")
                return False
            
            # 检查价格变化幅度
            current_price = prediction_data.get('current_price', 0)
            predicted_price = prediction_data.get('predicted_price', 0)
            if current_price > 0:
                price_change_pct = abs((predicted_price - current_price) / current_price * 100)
                if price_change_pct < conditions['min_price_change_pct']:
                    logger.info(f"价格变化幅度过小 ({price_change_pct:.2f}% < {conditions['min_price_change_pct']:.2f}%)，跳过发送")
                    return False
            
            # 检查冷却时间
            # TODO: 实现冷却时间检查
            
            return True
            
        except Exception as e:
            logger.error(f"检查发送条件时出错: {e}")
            return False
    
    def send_to_group(self, group_name: str, message: str) -> bool:
        """发送消息到指定群聊"""
        if not self.is_connected or not self.wx:
            logger.error("微信未连接")
            return False
        
        try:
            # 发送消息
            result = self.wx.SendMsg(msg=message, who=group_name)
            
            if result:
                logger.info(f"消息已发送到群聊: {group_name}")
                return True
            else:
                logger.error(f"发送消息到群聊失败: {group_name}")
                return False
                
        except Exception as e:
            logger.error(f"发送消息时出错: {e}")
            self.last_error = str(e)
            return False
    
    def send_prediction_to_groups(self, prediction_data: Dict) -> Dict:
        """发送预测结果到所有配置的群聊"""
        results = {
            'success': False,
            'sent_groups': [],
            'failed_groups': [],
            'message': '',
            'errors': []
        }
        
        try:
            # 检查是否应该发送
            if not self.should_send_message(prediction_data):
                results['message'] = '不满足发送条件'
                return results
            
            # 格式化消息
            message = self.format_prediction_message(prediction_data)
            results['message'] = message
            
            # 获取目标群聊
            target_groups = self.config.get('target_groups', [])
            if not target_groups:
                results['errors'].append('未配置目标群聊')
                return results
            
            # 发送到各个群聊
            for group_name in target_groups:
                if self.send_to_group(group_name, message):
                    results['sent_groups'].append(group_name)
                else:
                    results['failed_groups'].append(group_name)
                    results['errors'].append(f'发送到 {group_name} 失败')
                
                # 发送间隔
                time.sleep(1)
            
            # 判断整体成功状态
            results['success'] = len(results['sent_groups']) > 0
            
            return results
            
        except Exception as e:
            logger.error(f"发送预测结果时出错: {e}")
            results['errors'].append(str(e))
            return results

    def send_formatted_message_to_groups(self, formatted_message: str) -> Dict:
        """发送格式化消息到所有配置的群聊"""
        results = {
            'success': False,
            'sent_groups': [],
            'failed_groups': [],
            'errors': [],
            'message': ''
        }

        try:
            if not self.is_connected:
                results['message'] = '微信未连接'
                results['errors'].append('微信未连接')
                return results

            target_groups = self.config.get('target_groups', [])
            if not target_groups:
                results['message'] = '未配置目标群聊'
                results['errors'].append('未配置目标群聊')
                return results

            sent_count = 0
            for group_name in target_groups:
                try:
                    if self.send_to_group(group_name, formatted_message):
                        results['sent_groups'].append(group_name)
                        sent_count += 1
                        logger.info(f"格式化消息已发送到群聊: {group_name}")
                    else:
                        results['failed_groups'].append(group_name)
                        results['errors'].append(f"发送到群聊失败: {group_name}")
                        logger.error(f"发送到群聊失败: {group_name}")
                except Exception as e:
                    results['failed_groups'].append(group_name)
                    results['errors'].append(f"发送到群聊 {group_name} 时出错: {str(e)}")
                    logger.error(f"发送到群聊 {group_name} 时出错: {e}")

            if sent_count > 0:
                results['success'] = True
                results['message'] = f'成功发送到 {sent_count} 个群聊'
            else:
                results['message'] = '所有群聊发送失败'

        except Exception as e:
            logger.error(f"发送格式化消息时出错: {e}")
            results['message'] = f'发送失败: {str(e)}'
            results['errors'].append(str(e))

        return results

    def update_config(self, new_config: Dict) -> bool:
        """更新配置"""
        try:
            self.config.update(new_config)
            self._save_config(self.config)
            logger.info("配置已更新")
            return True
        except Exception as e:
            logger.error(f"更新配置失败: {e}")
            return False
    
    def get_status(self) -> Dict:
        """获取发送器状态"""
        return {
            'connected': self.is_connected,
            'target_groups': self.config.get('target_groups', []),
            'last_error': self.last_error,
            'config_file': str(self.config_file)
        }


def test_wechat_sender():
    """测试微信发送功能"""
    print("=" * 50)
    print("微信发送功能测试")
    print("=" * 50)
    
    # 创建发送器
    sender = WeChatSender()
    
    # 连接微信
    print("正在连接微信...")
    if sender.connect_wechat():
        print("✅ 微信连接成功")
        
        # 获取群聊列表
        print("\n获取群聊列表...")
        groups = sender.get_group_list()
        print(f"找到 {len(groups)} 个群聊:")
        for i, group in enumerate(groups[:10], 1):  # 只显示前10个
            print(f"  {i}. {group}")
        
        # 测试消息格式化
        print("\n测试消息格式化...")
        test_prediction = {
            'timestamp': datetime.now().isoformat(),
            'current_price': 2650.50,
            'predicted_price': 2675.25,
            'signal': '看涨',
            'confidence': 0.75,
            'method': '技术分析',
            'target_time': datetime.now().isoformat()
        }
        
        message = sender.format_prediction_message(test_prediction)
        print("格式化的消息:")
        print(message)
        
        # 显示状态
        status = sender.get_status()
        print(f"\n发送器状态: {status}")
        
    else:
        print("❌ 微信连接失败")
        print(f"错误: {sender.last_error}")
    
    print("=" * 50)


if __name__ == "__main__":
    test_wechat_sender()
