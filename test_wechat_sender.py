#!/usr/bin/env python3
"""
微信发送功能测试脚本
用于验证微信消息发送功能是否正常工作
"""

import sys
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from wechat_sender import WeChatSender

def test_basic_functionality():
    """测试基础功能"""
    print("🔧 测试基础功能")
    print("-" * 30)
    
    # 创建发送器实例
    sender = WeChatSender()
    print("✅ 微信发送器创建成功")
    
    # 检查配置文件
    config_file = Path("wechat_config.json")
    if config_file.exists():
        print("✅ 配置文件存在")
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            print(f"   目标群聊数量: {len(config.get('target_groups', []))}")
            print(f"   最小置信度: {config.get('send_conditions', {}).get('min_confidence', 0)}")
    else:
        print("❌ 配置文件不存在")
    
    return sender

def test_message_formatting():
    """测试消息格式化"""
    print("\n📝 测试消息格式化")
    print("-" * 30)
    
    sender = WeChatSender()
    
    # 创建测试预测数据
    test_predictions = [
        {
            'timestamp': datetime.now().isoformat(),
            'current_price': 2650.50,
            'predicted_price': 2675.25,
            'signal': '看涨',
            'confidence': 0.75,
            'method': '技术分析',
            'target_time': (datetime.now() + timedelta(minutes=5)).isoformat()
        },
        {
            'timestamp': datetime.now().isoformat(),
            'current_price': 2680.00,
            'predicted_price': 2665.50,
            'signal': '看跌',
            'confidence': 0.65,
            'method': 'AI预测',
            'target_time': (datetime.now() + timedelta(minutes=10)).isoformat()
        }
    ]
    
    for i, prediction in enumerate(test_predictions, 1):
        print(f"\n测试预测 {i}:")
        message = sender.format_prediction_message(prediction)
        print(message)
        print("-" * 50)
    
    print("✅ 消息格式化测试完成")

def test_send_conditions():
    """测试发送条件"""
    print("\n🎯 测试发送条件")
    print("-" * 30)
    
    sender = WeChatSender()
    
    # 测试不同条件的预测数据
    test_cases = [
        {
            'name': '高置信度，大幅变化',
            'data': {
                'current_price': 2650.00,
                'predicted_price': 2680.00,  # +1.13%
                'confidence': 0.8
            },
            'expected': True
        },
        {
            'name': '低置信度',
            'data': {
                'current_price': 2650.00,
                'predicted_price': 2680.00,
                'confidence': 0.2  # 低于默认0.3
            },
            'expected': False
        },
        {
            'name': '小幅变化',
            'data': {
                'current_price': 2650.00,
                'predicted_price': 2651.00,  # +0.04%，低于默认0.1%
                'confidence': 0.8
            },
            'expected': False
        }
    ]
    
    for case in test_cases:
        should_send = sender.should_send_message(case['data'])
        status = "✅" if should_send == case['expected'] else "❌"
        print(f"{status} {case['name']}: {should_send} (期望: {case['expected']})")
    
    print("✅ 发送条件测试完成")

def test_wechat_connection():
    """测试微信连接"""
    print("\n📱 测试微信连接")
    print("-" * 30)
    
    sender = WeChatSender()
    
    print("正在尝试连接微信...")
    print("⚠️  请确保:")
    print("   1. 微信PC版已启动并登录")
    print("   2. 已安装wxauto库: pip install wxauto")
    print("   3. 微信版本兼容")
    
    try:
        if sender.connect_wechat():
            print("✅ 微信连接成功")
            
            # 获取群聊列表
            print("\n获取群聊列表...")
            groups = sender.get_group_list()
            
            if groups:
                print(f"✅ 找到 {len(groups)} 个群聊:")
                for i, group in enumerate(groups[:10], 1):  # 只显示前10个
                    print(f"   {i}. {group}")
                
                if len(groups) > 10:
                    print(f"   ... 还有 {len(groups) - 10} 个群聊")
            else:
                print("⚠️  未找到群聊或获取失败")
            
            # 显示状态
            status = sender.get_status()
            print(f"\n发送器状态:")
            print(f"   连接状态: {status['connected']}")
            print(f"   配置的目标群聊: {status['target_groups']}")
            
            sender.disconnect_wechat()
            print("✅ 微信连接已断开")
            
        else:
            print("❌ 微信连接失败")
            print(f"   错误信息: {sender.last_error}")
            print("\n可能的解决方案:")
            print("   1. 确保微信PC版已启动并登录")
            print("   2. 检查wxauto库是否正确安装")
            print("   3. 尝试重启微信")
            print("   4. 检查微信版本是否兼容")
            
    except Exception as e:
        print(f"❌ 连接测试出错: {e}")

def test_config_management():
    """测试配置管理"""
    print("\n⚙️  测试配置管理")
    print("-" * 30)
    
    sender = WeChatSender()
    
    # 显示当前配置
    print("当前配置:")
    print(f"   目标群聊: {sender.config.get('target_groups', [])}")
    print(f"   最小置信度: {sender.config.get('send_conditions', {}).get('min_confidence', 0)}")
    print(f"   最小价格变化: {sender.config.get('send_conditions', {}).get('min_price_change_pct', 0)}%")
    
    # 测试配置更新
    print("\n测试配置更新...")
    new_config = {
        'target_groups': ['测试群聊1', '测试群聊2'],
        'send_conditions': {
            'min_confidence': 0.5,
            'min_price_change_pct': 0.2
        }
    }
    
    if sender.update_config(new_config):
        print("✅ 配置更新成功")
        print(f"   新的目标群聊: {sender.config.get('target_groups', [])}")
        print(f"   新的最小置信度: {sender.config.get('send_conditions', {}).get('min_confidence', 0)}")
    else:
        print("❌ 配置更新失败")
    
    print("✅ 配置管理测试完成")

def interactive_test():
    """交互式测试"""
    print("\n🎮 交互式测试")
    print("-" * 30)
    
    sender = WeChatSender()
    
    while True:
        print("\n请选择测试项目:")
        print("1. 连接微信并获取群聊列表")
        print("2. 发送测试消息")
        print("3. 更新目标群聊")
        print("4. 查看当前配置")
        print("0. 退出")
        
        choice = input("\n请输入选择 (0-4): ").strip()
        
        if choice == '0':
            break
        elif choice == '1':
            test_wechat_connection()
        elif choice == '2':
            if sender.connect_wechat():
                # 创建测试预测数据
                test_prediction = {
                    'timestamp': datetime.now().isoformat(),
                    'current_price': 2650.50,
                    'predicted_price': 2675.25,
                    'signal': '测试信号',
                    'confidence': 0.75,
                    'method': '测试方法',
                    'target_time': (datetime.now() + timedelta(minutes=5)).isoformat()
                }
                
                print("发送测试消息...")
                result = sender.send_prediction_to_groups(test_prediction)
                
                if result['success']:
                    print(f"✅ 消息发送成功到: {result['sent_groups']}")
                else:
                    print(f"❌ 消息发送失败: {result['errors']}")
                
                sender.disconnect_wechat()
            else:
                print("❌ 无法连接微信")
                
        elif choice == '3':
            groups_input = input("请输入目标群聊名称（用逗号分隔）: ").strip()
            if groups_input:
                groups = [g.strip() for g in groups_input.split(',')]
                sender.update_config({'target_groups': groups})
                print(f"✅ 目标群聊已更新: {groups}")
            
        elif choice == '4':
            status = sender.get_status()
            print(f"连接状态: {status['connected']}")
            print(f"目标群聊: {status['target_groups']}")
            print(f"配置文件: {status['config_file']}")
        
        else:
            print("无效选择，请重试")

def main():
    """主测试函数"""
    print("🚀 微信发送功能测试")
    print("=" * 50)
    
    try:
        # 基础功能测试
        test_basic_functionality()
        
        # 消息格式化测试
        test_message_formatting()
        
        # 发送条件测试
        test_send_conditions()
        
        # 配置管理测试
        test_config_management()
        
        # 微信连接测试
        test_wechat_connection()
        
        print("\n" + "=" * 50)
        print("📋 测试总结")
        print("=" * 50)
        print("✅ 基础功能测试完成")
        print("✅ 消息格式化测试完成")
        print("✅ 发送条件测试完成")
        print("✅ 配置管理测试完成")
        print("✅ 微信连接测试完成")
        
        # 询问是否进行交互式测试
        if input("\n是否进行交互式测试? (y/n): ").lower() == 'y':
            interactive_test()
        
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中出错: {e}")
    
    print("\n测试完成！")

if __name__ == "__main__":
    main()
