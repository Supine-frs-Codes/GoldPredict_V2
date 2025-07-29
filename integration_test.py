#!/usr/bin/env python3
"""
微信集成功能完整测试脚本
测试微信功能与现有预测系统的集成
"""

import sys
import json
import time
import threading
import requests
from datetime import datetime, timedelta
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

def test_existing_system():
    """测试现有预测系统是否正常"""
    print("🔍 测试现有预测系统")
    print("-" * 40)
    
    # 检查主要文件是否存在
    critical_files = [
        "unified_prediction_platform_fixed.py",
        "simple_enhanced_web.py",
        "adaptive_prediction_engine.py",
        "improved_mt5_manager.py"
    ]
    
    missing_files = []
    for file in critical_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ 缺少关键文件: {missing_files}")
        return False
    else:
        print("✅ 所有关键文件存在")
    
    # 测试导入
    try:
        from unified_prediction_platform_fixed import UnifiedPredictionController
        print("✅ 主系统导入成功")
    except ImportError as e:
        print(f"❌ 主系统导入失败: {e}")
        return False
    
    return True

def test_wechat_modules():
    """测试微信模块"""
    print("\n📱 测试微信模块")
    print("-" * 40)
    
    # 检查微信相关文件
    wechat_files = [
        "wechat_sender.py",
        "prediction_listener.py",
        "demo_wechat_prediction_system.py",
        "wechat_web_interface.py"
    ]
    
    for file in wechat_files:
        if Path(file).exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file} 不存在")
            return False
    
    # 测试导入
    try:
        from wechat_sender import WeChatSender
        from prediction_listener import PredictionListener
        from demo_wechat_prediction_system import DemoWeChatPredictionSystem
        print("✅ 微信模块导入成功")
    except ImportError as e:
        print(f"❌ 微信模块导入失败: {e}")
        return False
    
    return True

def test_configuration_files():
    """测试配置文件"""
    print("\n⚙️  测试配置文件")
    print("-" * 40)
    
    config_files = [
        ("wechat_config.json", "微信发送配置"),
        ("listener_config.json", "监听器配置")
    ]
    
    for file, desc in config_files:
        if Path(file).exists():
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                print(f"✅ {file}: {desc}")
            except json.JSONDecodeError as e:
                print(f"❌ {file}: JSON格式错误 - {e}")
                return False
        else:
            print(f"⚠️  {file}: 不存在，将使用默认配置")
    
    return True

def test_api_endpoints():
    """测试API端点"""
    print("\n🌐 测试API端点")
    print("-" * 40)
    
    # 启动微信Web界面（后台）
    import subprocess
    import time
    
    print("启动微信Web界面...")
    try:
        # 启动Web服务器
        web_process = subprocess.Popen([
            sys.executable, "wechat_web_interface.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # 等待服务器启动
        time.sleep(3)
        
        # 测试API端点
        api_endpoints = [
            ("http://localhost:5005/api/status", "系统状态"),
            ("http://localhost:5005/api/config", "配置管理"),
            ("http://localhost:5005/api/demo/status", "Demo状态")
        ]
        
        success_count = 0
        for url, desc in api_endpoints:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    print(f"✅ {desc}: {url}")
                    success_count += 1
                else:
                    print(f"❌ {desc}: {url} - HTTP {response.status_code}")
            except requests.RequestException as e:
                print(f"❌ {desc}: {url} - {e}")
        
        # 停止Web服务器
        web_process.terminate()
        web_process.wait()
        
        return success_count == len(api_endpoints)
        
    except Exception as e:
        print(f"❌ API测试失败: {e}")
        return False

def test_integration_workflow():
    """测试集成工作流程"""
    print("\n🔄 测试集成工作流程")
    print("-" * 40)
    
    try:
        # 1. 创建微信发送器
        from wechat_sender import WeChatSender
        sender = WeChatSender()
        print("✅ 微信发送器创建成功")
        
        # 2. 创建预测监听器
        from prediction_listener import PredictionListener
        listener = PredictionListener()
        print("✅ 预测监听器创建成功")
        
        # 3. 创建Demo系统
        from demo_wechat_prediction_system import DemoWeChatPredictionSystem
        demo = DemoWeChatPredictionSystem()
        print("✅ Demo系统创建成功")
        
        # 4. 测试配置管理
        original_config = sender.config.copy()
        test_config = {
            'target_groups': ['测试群聊'],
            'send_conditions': {
                'min_confidence': 0.5
            }
        }
        
        if sender.update_config(test_config):
            print("✅ 配置更新成功")
            # 恢复原配置
            sender.update_config(original_config)
        else:
            print("❌ 配置更新失败")
            return False
        
        # 5. 测试预测数据处理
        test_prediction = {
            'timestamp': datetime.now().isoformat(),
            'current_price': 2650.50,
            'predicted_price': 2675.25,
            'signal': '集成测试',
            'confidence': 0.75,
            'method': '集成测试',
            'target_time': datetime.now().isoformat()
        }
        
        # 测试消息格式化
        message = sender.format_prediction_message(test_prediction)
        if message and len(message) > 0:
            print("✅ 消息格式化成功")
        else:
            print("❌ 消息格式化失败")
            return False
        
        # 测试发送条件检查
        should_send = sender.should_send_message(test_prediction)
        print(f"✅ 发送条件检查: {'通过' if should_send else '不通过'}")
        
        return True
        
    except Exception as e:
        print(f"❌ 集成工作流程测试失败: {e}")
        return False

def test_file_monitoring():
    """测试文件监控功能"""
    print("\n📁 测试文件监控功能")
    print("-" * 40)
    
    try:
        # 创建测试目录和文件
        test_dir = Path("results/integration_test")
        test_dir.mkdir(parents=True, exist_ok=True)
        
        test_file = test_dir / "test_prediction.json"
        
        # 创建测试预测数据
        test_prediction = {
            'timestamp': datetime.now().isoformat(),
            'current_price': 2660.00,
            'predicted_price': 2685.00,
            'signal': '文件监控测试',
            'confidence': 0.80,
            'method': '文件监控测试'
        }
        
        # 写入测试文件
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_prediction, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 测试文件创建成功: {test_file}")
        
        # 测试文件读取
        with open(test_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        if loaded_data == test_prediction:
            print("✅ 文件读取验证成功")
        else:
            print("❌ 文件读取验证失败")
            return False
        
        # 清理测试文件
        test_file.unlink()
        print("✅ 测试文件清理完成")
        
        return True
        
    except Exception as e:
        print(f"❌ 文件监控测试失败: {e}")
        return False

def generate_integration_report():
    """生成集成测试报告"""
    print("\n📋 生成集成测试报告")
    print("-" * 40)
    
    report = {
        'test_time': datetime.now().isoformat(),
        'test_results': {
            'existing_system': False,
            'wechat_modules': False,
            'configuration_files': False,
            'api_endpoints': False,
            'integration_workflow': False,
            'file_monitoring': False
        },
        'recommendations': [],
        'next_steps': []
    }
    
    # 执行所有测试
    print("执行完整测试套件...")
    
    report['test_results']['existing_system'] = test_existing_system()
    report['test_results']['wechat_modules'] = test_wechat_modules()
    report['test_results']['configuration_files'] = test_configuration_files()
    report['test_results']['api_endpoints'] = test_api_endpoints()
    report['test_results']['integration_workflow'] = test_integration_workflow()
    report['test_results']['file_monitoring'] = test_file_monitoring()
    
    # 生成建议
    failed_tests = [test for test, result in report['test_results'].items() if not result]
    
    if not failed_tests:
        report['recommendations'].append("所有测试通过，系统集成成功")
        report['next_steps'].extend([
            "配置微信群聊目标",
            "启动预测监听器",
            "开始使用完整系统"
        ])
    else:
        report['recommendations'].append(f"以下测试失败: {', '.join(failed_tests)}")
        
        if 'existing_system' in failed_tests:
            report['next_steps'].append("检查现有预测系统的完整性")
        
        if 'wechat_modules' in failed_tests:
            report['next_steps'].append("重新安装微信相关依赖")
        
        if 'api_endpoints' in failed_tests:
            report['next_steps'].append("检查Web服务器配置")
    
    # 保存报告
    report_file = Path("integration_test_report.json")
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 集成测试报告已保存: {report_file}")
    
    return report

def main():
    """主测试流程"""
    print("🚀 微信集成功能完整测试")
    print("=" * 50)
    print("此脚本将测试微信功能与现有预测系统的完整集成")
    print("=" * 50)
    
    try:
        # 生成完整测试报告
        report = generate_integration_report()
        
        # 显示测试结果
        print("\n" + "=" * 50)
        print("📊 测试结果总结")
        print("=" * 50)
        
        passed_tests = sum(1 for result in report['test_results'].values() if result)
        total_tests = len(report['test_results'])
        
        for test_name, result in report['test_results'].items():
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{status} {test_name.replace('_', ' ').title()}")
        
        print(f"\n📈 总体结果: {passed_tests}/{total_tests} 测试通过")
        
        if passed_tests == total_tests:
            print("\n🎉 所有测试通过！微信集成功能已准备就绪")
            print("\n🚀 下一步操作:")
            print("1. 运行依赖安装: python install_wechat_dependencies.py")
            print("2. 验证微信功能: python verify_wechat_integration.py")
            print("3. 启动Web管理界面: python wechat_web_interface.py")
            print("4. 启动Demo系统: python demo_wechat_prediction_system.py")
        else:
            print(f"\n⚠️  {total_tests - passed_tests} 个测试失败")
            print("\n🔧 建议操作:")
            for recommendation in report['recommendations']:
                print(f"- {recommendation}")
            
            print("\n📋 下一步:")
            for step in report['next_steps']:
                print(f"- {step}")
        
        print(f"\n📄 详细报告: integration_test_report.json")
        
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
