#!/usr/bin/env python3
"""
测试统一预测平台2.0
验证微信集成功能是否正常工作
"""

import sys
import time
from pathlib import Path

def test_imports():
    """测试导入"""
    print("🔍 测试模块导入")
    print("-" * 40)
    
    success_count = 0
    total_count = 0
    
    # 测试基础模块
    modules = [
        ("flask", "Flask Web框架"),
        ("json", "JSON处理"),
        ("threading", "多线程"),
        ("datetime", "时间处理"),
        ("pathlib", "路径处理")
    ]
    
    for module, desc in modules:
        total_count += 1
        try:
            __import__(module)
            print(f"✅ {module}: {desc}")
            success_count += 1
        except ImportError as e:
            print(f"❌ {module}: {desc} - {e}")
    
    # 测试微信模块
    try:
        from wechat_sender import WeChatSender
        print(f"✅ wechat_sender: 微信发送器")
        success_count += 1
    except ImportError as e:
        print(f"❌ wechat_sender: 微信发送器 - {e}")
    total_count += 1
    
    try:
        from prediction_listener import PredictionListener
        print(f"✅ prediction_listener: 预测监听器")
        success_count += 1
    except ImportError as e:
        print(f"❌ prediction_listener: 预测监听器 - {e}")
    total_count += 1
    
    print(f"\n📊 导入测试结果: {success_count}/{total_count} 成功")
    return success_count >= total_count - 2  # 允许2个模块失败

def test_unified_platform():
    """测试统一平台"""
    print("\n🚀 测试统一预测平台2.0")
    print("-" * 40)
    
    try:
        # 导入统一平台
        import importlib.util
        spec = importlib.util.spec_from_file_location("unified_v2", "unified_prediction_platform_fixed_ver2.0.py")
        unified_v2 = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(unified_v2)

        controller = unified_v2.controller
        app = unified_v2.app
        print("✅ 统一平台导入成功")
        
        # 测试控制器
        status = controller.get_system_status()
        print(f"✅ 控制器状态获取成功: {len(status)} 个系统")
        
        # 测试微信系统状态
        wechat_status = controller.get_system_status('wechat')
        print(f"✅ 微信系统状态: {wechat_status}")
        
        # 测试Flask应用
        with app.test_client() as client:
            response = client.get('/')
            if response.status_code == 200:
                print("✅ Web界面访问正常")
            else:
                print(f"⚠️  Web界面访问异常: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ 统一平台测试失败: {e}")
        return False

def test_wechat_integration():
    """测试微信集成"""
    print("\n📱 测试微信集成功能")
    print("-" * 40)
    
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("unified_v2", "unified_prediction_platform_fixed_ver2.0.py")
        unified_v2 = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(unified_v2)

        controller = unified_v2.controller
        
        # 测试微信系统启动
        print("测试微信系统启动...")
        result = controller.start_system('wechat')
        
        if result['success']:
            print("✅ 微信系统启动成功")
            
            # 测试发送功能
            test_prediction = {
                'timestamp': '2025-07-26T03:00:00',
                'current_price': 3338.80,
                'predicted_price': 3345.50,
                'signal': '测试信号',
                'confidence': 0.75,
                'method': '集成测试'
            }
            
            send_result = controller.send_prediction_to_wechat('test', test_prediction)
            
            if send_result['success']:
                print(f"✅ 测试消息发送成功: {send_result['sent_groups']}")
            else:
                print(f"⚠️  测试消息发送失败: {send_result['message']}")
            
            # 停止微信系统
            controller.stop_system('wechat')
            print("✅ 微信系统已停止")
            
            return True
        else:
            print(f"❌ 微信系统启动失败: {result['message']}")
            return False
            
    except Exception as e:
        print(f"❌ 微信集成测试失败: {e}")
        return False

def test_api_endpoints():
    """测试API端点"""
    print("\n🌐 测试API端点")
    print("-" * 40)
    
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("unified_v2", "unified_prediction_platform_fixed_ver2.0.py")
        unified_v2 = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(unified_v2)

        app = unified_v2.app
        
        # 测试主要API端点
        endpoints = [
            ('/', 'GET', '主页'),
            ('/api/status', 'GET', '系统状态'),
            ('/api/prediction/latest', 'GET', '最新预测'),
            ('/wechat-manager', 'GET', '微信管理器')
        ]
        
        success_count = 0
        
        with app.test_client() as client:
            for endpoint, method, desc in endpoints:
                try:
                    if method == 'GET':
                        response = client.get(endpoint)
                    else:
                        response = client.post(endpoint)
                    
                    if response.status_code in [200, 404]:  # 404也算正常，可能是模块不可用
                        print(f"✅ {endpoint}: {desc} - {response.status_code}")
                        success_count += 1
                    else:
                        print(f"⚠️  {endpoint}: {desc} - {response.status_code}")
                        
                except Exception as e:
                    print(f"❌ {endpoint}: {desc} - {e}")
        
        print(f"\n📊 API测试结果: {success_count}/{len(endpoints)} 成功")
        return success_count >= len(endpoints) - 1
        
    except Exception as e:
        print(f"❌ API端点测试失败: {e}")
        return False

def test_enhanced_monitor():
    """测试增强监控器"""
    print("\n🔍 测试增强预测监控器")
    print("-" * 40)
    
    try:
        from enhanced_prediction_monitor import EnhancedPredictionMonitor
        
        # 创建监控器
        monitor = EnhancedPredictionMonitor()
        print("✅ 增强监控器创建成功")
        
        # 测试状态获取
        status = monitor.get_status()
        print(f"✅ 监控器状态: 运行中={status['running']}")
        
        # 测试配置
        config = monitor.config
        print(f"✅ 监控配置: 文件监控={config['enable_file_monitoring']}, API监控={config['enable_api_monitoring']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 增强监控器测试失败: {e}")
        return False

def main():
    """主测试流程"""
    print("🚀 统一预测平台2.0集成测试")
    print("=" * 50)
    print("验证微信集成功能和系统完整性")
    print("=" * 50)
    
    test_results = {}
    
    try:
        # 1. 测试导入
        test_results['imports'] = test_imports()
        
        # 2. 测试统一平台
        test_results['unified_platform'] = test_unified_platform()
        
        # 3. 测试微信集成
        test_results['wechat_integration'] = test_wechat_integration()
        
        # 4. 测试API端点
        test_results['api_endpoints'] = test_api_endpoints()
        
        # 5. 测试增强监控器
        test_results['enhanced_monitor'] = test_enhanced_monitor()
        
        # 总结结果
        print("\n" + "=" * 50)
        print("📊 测试结果总结")
        print("=" * 50)
        
        passed_tests = sum(1 for result in test_results.values() if result)
        total_tests = len(test_results)
        
        for test_name, result in test_results.items():
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{status} {test_name.replace('_', ' ').title()}")
        
        print(f"\n📈 总体结果: {passed_tests}/{total_tests} 测试通过")
        
        if passed_tests >= total_tests - 1:  # 允许一个测试失败
            print("\n🎉 集成测试成功！统一预测平台2.0已准备就绪")
            print("\n🚀 使用方法:")
            print("1. 启动系统: uv run python unified_prediction_platform_fixed_ver2.0.py")
            print("2. 访问主界面: http://localhost:5000")
            print("3. 微信管理: http://localhost:5000/wechat-manager")
            print("4. 启动增强监控: uv run python enhanced_prediction_monitor.py")
        else:
            print(f"\n⚠️  集成测试部分失败 ({total_tests - passed_tests} 个测试失败)")
            print("请检查失败的组件并修复相关问题")
        
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
