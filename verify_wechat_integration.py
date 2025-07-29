#!/usr/bin/env python3
"""
微信集成功能验证脚本
验证微信发送功能和预测监听器的完整工作流程
"""

import sys
import json
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from wechat_sender import WeChatSender
from prediction_listener import PredictionListener

def check_dependencies():
    """检查依赖项"""
    print("🔍 检查依赖项")
    print("-" * 30)
    
    dependencies = {
        'wxauto': '微信自动化库',
        'watchdog': '文件监控库',
        'requests': 'HTTP请求库'
    }
    
    missing_deps = []
    
    for dep, desc in dependencies.items():
        try:
            __import__(dep)
            print(f"✅ {dep}: {desc}")
        except ImportError:
            print(f"❌ {dep}: {desc} - 未安装")
            missing_deps.append(dep)
    
    if missing_deps:
        print(f"\n⚠️  缺少依赖项，请安装:")
        for dep in missing_deps:
            print(f"   pip install {dep}")
        return False
    
    print("✅ 所有依赖项已安装")
    return True

def test_wechat_connection():
    """测试微信连接"""
    print("\n📱 测试微信连接")
    print("-" * 30)
    
    sender = WeChatSender()
    
    print("正在连接微信...")
    if sender.connect_wechat():
        print("✅ 微信连接成功")
        
        # 获取群聊列表
        groups = sender.get_group_list()
        print(f"✅ 找到 {len(groups)} 个群聊")
        
        if groups:
            print("前10个群聊:")
            for i, group in enumerate(groups[:10], 1):
                print(f"   {i}. {group}")
        
        sender.disconnect_wechat()
        return True, groups
    else:
        print("❌ 微信连接失败")
        print(f"   错误: {sender.last_error}")
        return False, []

def setup_test_groups(available_groups):
    """设置测试群聊"""
    print("\n⚙️  设置测试群聊")
    print("-" * 30)
    
    if not available_groups:
        print("❌ 没有可用的群聊")
        return []
    
    print("可用的群聊:")
    for i, group in enumerate(available_groups, 1):
        print(f"   {i}. {group}")
    
    print("\n请选择要用于测试的群聊（输入序号，多个用逗号分隔）:")
    print("⚠️  注意：测试消息会发送到选中的群聊中！")
    
    try:
        selection = input("请输入选择（例如：1,3,5）或按回车跳过: ").strip()
        
        if not selection:
            print("跳过群聊设置")
            return []
        
        indices = [int(x.strip()) - 1 for x in selection.split(',')]
        selected_groups = [available_groups[i] for i in indices if 0 <= i < len(available_groups)]
        
        print(f"✅ 已选择 {len(selected_groups)} 个群聊:")
        for group in selected_groups:
            print(f"   - {group}")
        
        # 更新微信配置
        sender = WeChatSender()
        sender.update_config({'target_groups': selected_groups})
        
        return selected_groups
        
    except (ValueError, IndexError) as e:
        print(f"❌ 输入无效: {e}")
        return []

def test_message_sending(test_groups):
    """测试消息发送"""
    print("\n📤 测试消息发送")
    print("-" * 30)
    
    if not test_groups:
        print("⚠️  没有配置测试群聊，跳过发送测试")
        return False
    
    sender = WeChatSender()
    
    # 连接微信
    if not sender.connect_wechat():
        print("❌ 微信连接失败")
        return False
    
    # 创建测试预测数据
    test_prediction = {
        'timestamp': datetime.now().isoformat(),
        'current_price': 2650.50,
        'predicted_price': 2675.25,
        'signal': '测试看涨信号',
        'confidence': 0.75,
        'method': '验证测试',
        'target_time': (datetime.now() + timedelta(minutes=5)).isoformat()
    }
    
    print("发送测试预测消息...")
    print("测试数据:")
    print(f"   当前价格: ${test_prediction['current_price']}")
    print(f"   预测价格: ${test_prediction['predicted_price']}")
    print(f"   交易信号: {test_prediction['signal']}")
    print(f"   置信度: {test_prediction['confidence']:.1%}")
    
    # 确认发送
    confirm = input("\n确认发送测试消息到选中的群聊吗？(y/n): ").lower()
    if confirm != 'y':
        print("取消发送测试")
        sender.disconnect_wechat()
        return False
    
    # 发送消息
    result = sender.send_prediction_to_groups(test_prediction)
    
    if result['success']:
        print(f"✅ 测试消息发送成功!")
        print(f"   成功发送到: {result['sent_groups']}")
        if result['failed_groups']:
            print(f"   发送失败: {result['failed_groups']}")
    else:
        print(f"❌ 测试消息发送失败")
        print(f"   错误: {result['errors']}")
    
    sender.disconnect_wechat()
    return result['success']

def create_test_prediction_file():
    """创建测试预测文件"""
    print("\n📄 创建测试预测文件")
    print("-" * 30)
    
    # 确保目录存在
    test_dir = Path("results/test")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建测试预测数据
    test_prediction = {
        'timestamp': datetime.now().isoformat(),
        'current_price': 2655.75,
        'predicted_price': 2680.50,
        'signal': '文件监听测试信号',
        'confidence': 0.80,
        'method': '文件监听验证',
        'target_time': (datetime.now() + timedelta(minutes=10)).isoformat()
    }
    
    # 保存测试文件
    test_file = test_dir / "test_prediction.json"
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(test_prediction, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 测试预测文件已创建: {test_file}")
    return test_file

def test_prediction_listener():
    """测试预测监听器"""
    print("\n👂 测试预测监听器")
    print("-" * 30)
    
    # 创建监听器
    listener = PredictionListener()
    
    # 显示配置
    print("监听器配置:")
    print(f"   文件监控: {listener.config['monitoring']['enable_file_monitoring']}")
    print(f"   API监控: {listener.config['monitoring']['enable_api_monitoring']}")
    print(f"   检查间隔: {listener.config['monitoring']['check_interval_seconds']}秒")
    
    # 询问是否进行监听测试
    test_listener = input("\n是否测试预测监听器？(y/n): ").lower()
    if test_listener != 'y':
        print("跳过监听器测试")
        return True
    
    print("\n启动监听器...")
    if listener.start_monitoring():
        print("✅ 监听器启动成功")
        
        # 创建测试文件
        test_file = create_test_prediction_file()
        
        print(f"\n等待监听器检测文件变化...")
        print("（监听器会检测到文件变化并尝试发送消息）")
        
        # 等待一段时间让监听器处理
        time.sleep(5)
        
        # 修改测试文件触发监听
        print("修改测试文件以触发监听...")
        test_prediction = {
            'timestamp': datetime.now().isoformat(),
            'current_price': 2660.25,
            'predicted_price': 2685.75,
            'signal': '监听器触发测试',
            'confidence': 0.85,
            'method': '文件变化监听',
            'target_time': (datetime.now() + timedelta(minutes=15)).isoformat()
        }
        
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_prediction, f, indent=2, ensure_ascii=False)
        
        print("等待监听器处理...")
        time.sleep(10)
        
        # 停止监听器
        listener.stop_monitoring()
        print("✅ 监听器测试完成")
        
        # 显示发送历史
        history = listener.get_send_history(5)
        if history:
            print(f"\n最近发送历史 ({len(history)} 条):")
            for record in history:
                print(f"   {record['created_at']}: {record['signal']} -> {record['sent_groups']}")
        
        return True
    else:
        print("❌ 监听器启动失败")
        return False

def test_api_monitoring():
    """测试API监控"""
    print("\n🌐 测试API监控")
    print("-" * 30)
    
    # 检查预测系统是否运行
    import requests
    
    api_endpoints = [
        "http://localhost:5000/api/prediction/latest",
        "http://localhost:5003/api/prediction/latest"
    ]
    
    available_apis = []
    
    for api_url in api_endpoints:
        try:
            response = requests.get(api_url, timeout=5)
            if response.status_code == 200:
                print(f"✅ API可用: {api_url}")
                available_apis.append(api_url)
            else:
                print(f"⚠️  API响应异常: {api_url} - {response.status_code}")
        except requests.RequestException:
            print(f"❌ API不可用: {api_url}")
    
    if available_apis:
        print(f"\n找到 {len(available_apis)} 个可用的API端点")
        return True
    else:
        print("\n⚠️  没有找到可用的API端点")
        print("请确保预测系统正在运行:")
        print("   python unified_prediction_platform_fixed.py")
        print("   python simple_enhanced_web.py")
        return False

def generate_verification_report():
    """生成验证报告"""
    print("\n📋 生成验证报告")
    print("-" * 30)
    
    report = {
        'verification_time': datetime.now().isoformat(),
        'tests_performed': [],
        'configuration_files': [],
        'recommendations': []
    }
    
    # 检查配置文件
    config_files = [
        'wechat_config.json',
        'listener_config.json'
    ]
    
    for config_file in config_files:
        if Path(config_file).exists():
            report['configuration_files'].append(f"✅ {config_file}")
        else:
            report['configuration_files'].append(f"❌ {config_file}")
    
    # 保存报告
    report_file = Path("wechat_integration_verification_report.json")
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 验证报告已保存: {report_file}")
    return report_file

def main():
    """主验证流程"""
    print("🚀 微信集成功能验证")
    print("=" * 50)
    print("此脚本将验证微信发送功能和预测监听器的完整工作流程")
    print("⚠️  请确保微信PC版已启动并登录")
    print("=" * 50)
    
    try:
        # 1. 检查依赖项
        if not check_dependencies():
            print("\n❌ 依赖项检查失败，请安装缺少的库后重试")
            return
        
        # 2. 测试微信连接
        wechat_ok, available_groups = test_wechat_connection()
        if not wechat_ok:
            print("\n❌ 微信连接失败，请检查微信是否正常运行")
            return
        
        # 3. 设置测试群聊
        test_groups = setup_test_groups(available_groups)
        
        # 4. 测试消息发送
        if test_groups:
            send_ok = test_message_sending(test_groups)
            if not send_ok:
                print("\n⚠️  消息发送测试失败")
        
        # 5. 测试API监控
        api_ok = test_api_monitoring()
        
        # 6. 测试预测监听器
        listener_ok = test_prediction_listener()
        
        # 7. 生成验证报告
        report_file = generate_verification_report()
        
        # 总结
        print("\n" + "=" * 50)
        print("📊 验证总结")
        print("=" * 50)
        print(f"✅ 依赖项检查: 通过")
        print(f"{'✅' if wechat_ok else '❌'} 微信连接: {'通过' if wechat_ok else '失败'}")
        print(f"{'✅' if test_groups else '⚠️ '} 群聊配置: {'已配置' if test_groups else '未配置'}")
        print(f"{'✅' if api_ok else '⚠️ '} API监控: {'可用' if api_ok else '不可用'}")
        print(f"{'✅' if listener_ok else '❌'} 监听器: {'正常' if listener_ok else '异常'}")
        
        if wechat_ok and test_groups:
            print("\n🎉 微信集成功能验证完成！")
            print("现在可以启动完整的预测系统和微信监听器了。")
        else:
            print("\n⚠️  部分功能验证失败，请检查相关配置。")
        
        print(f"\n📄 详细报告: {report_file}")
        
    except KeyboardInterrupt:
        print("\n\n验证被用户中断")
    except Exception as e:
        print(f"\n❌ 验证过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
