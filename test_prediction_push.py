#!/usr/bin/env python3
"""
测试三大预测系统的微信推送功能
验证实时预测系统、增强AI系统、传统ML系统的预测结果能否正确推送到微信
"""

import requests
import json
import time
from datetime import datetime
from pathlib import Path

def test_system_prediction_api(system_name, base_url="http://localhost:5000"):
    """测试系统预测API"""
    try:
        print(f"🔍 测试 {system_name} 预测API")
        
        api_url = f"{base_url}/api/prediction/{system_name}"
        response = requests.get(api_url, timeout=10)
        
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            try:
                prediction = response.json()
                
                if 'error' in prediction:
                    print(f"   ❌ API错误: {prediction['error']}")
                    return False
                
                # 检查预测数据完整性
                required_fields = ['current_price', 'predicted_price', 'signal', 'confidence']
                missing_fields = [field for field in required_fields if field not in prediction]
                
                if missing_fields:
                    print(f"   ⚠️  缺少字段: {missing_fields}")
                    return False
                
                print(f"   ✅ 预测数据完整")
                print(f"      当前价格: ${prediction['current_price']:.2f}")
                print(f"      预测价格: ${prediction['predicted_price']:.2f}")
                print(f"      交易信号: {prediction['signal']}")
                print(f"      置信度: {prediction['confidence']:.1%}")
                
                return prediction
                
            except json.JSONDecodeError:
                print(f"   ❌ 响应不是有效JSON")
                return False
        else:
            print(f"   ❌ HTTP错误: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ 请求异常: {e}")
        return False

def test_wechat_push_api(system_name, prediction_data, base_url="http://localhost:5000"):
    """测试微信推送API"""
    try:
        print(f"📱 测试 {system_name} 微信推送")
        
        api_url = f"{base_url}/api/wechat/test-prediction/{system_name}"
        response = requests.post(api_url, json=prediction_data, timeout=30)
        
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                
                if result.get('success'):
                    sent_groups = result.get('sent_groups', [])
                    print(f"   ✅ 推送成功到: {', '.join(sent_groups) if sent_groups else '无群聊'}")
                    return True
                else:
                    print(f"   ❌ 推送失败: {result.get('message', '未知错误')}")
                    return False
                    
            except json.JSONDecodeError:
                print(f"   ❌ 响应不是有效JSON")
                return False
        else:
            print(f"   ❌ HTTP错误: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ 请求异常: {e}")
        return False

def test_system_status(system_name, base_url="http://localhost:5000"):
    """测试系统状态"""
    try:
        print(f"🔧 检查 {system_name} 系统状态")
        
        api_url = f"{base_url}/api/status"
        response = requests.get(api_url, timeout=10)
        
        if response.status_code == 200:
            status_data = response.json()
            system_status = status_data.get(system_name, {})
            
            is_running = system_status.get('running', False)
            print(f"   系统状态: {'✅ 运行中' if is_running else '❌ 已停止'}")
            
            return is_running
        else:
            print(f"   ❌ 无法获取状态: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ 状态检查异常: {e}")
        return False

def start_system_if_needed(system_name, base_url="http://localhost:5000"):
    """如果系统未运行则启动"""
    try:
        if not test_system_status(system_name, base_url):
            print(f"🚀 尝试启动 {system_name} 系统")
            
            api_url = f"{base_url}/api/start/{system_name}"
            response = requests.post(api_url, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"   ✅ {system_name} 系统启动成功")
                    time.sleep(3)  # 等待系统初始化
                    return True
                else:
                    print(f"   ❌ {system_name} 系统启动失败: {result.get('message')}")
                    return False
            else:
                print(f"   ❌ 启动请求失败: HTTP {response.status_code}")
                return False
        else:
            return True
            
    except Exception as e:
        print(f"   ❌ 启动系统异常: {e}")
        return False

def main():
    """主测试流程"""
    print("📊 三大预测系统微信推送功能测试")
    print("=" * 60)
    print("测试实时预测、增强AI、传统ML系统的预测结果推送")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    
    # 测试的三大系统
    target_systems = {
        'realtime': '实时预测系统',
        'ai_enhanced': '增强AI系统', 
        'traditional': '传统ML系统'
    }
    
    test_results = {}
    
    print(f"🌐 测试服务器: {base_url}")
    print()
    
    # 首先测试服务器连接
    try:
        response = requests.get(f"{base_url}/api/status", timeout=5)
        if response.status_code != 200:
            print(f"❌ 服务器连接失败: HTTP {response.status_code}")
            print("请确保统一预测平台2.0正在运行")
            return
        print("✅ 服务器连接正常")
        print()
    except Exception as e:
        print(f"❌ 服务器连接失败: {e}")
        print("请确保统一预测平台2.0正在运行")
        return
    
    # 测试每个系统
    for system_name, system_desc in target_systems.items():
        print(f"📋 测试 {system_desc} ({system_name})")
        print("-" * 40)
        
        test_results[system_name] = {
            'system_running': False,
            'prediction_available': False,
            'wechat_push_success': False
        }
        
        # 1. 检查并启动系统
        if start_system_if_needed(system_name, base_url):
            test_results[system_name]['system_running'] = True
            
            # 2. 测试预测API
            prediction_data = test_system_prediction_api(system_name, base_url)
            if prediction_data:
                test_results[system_name]['prediction_available'] = True
                
                # 3. 测试微信推送
                if test_wechat_push_api(system_name, prediction_data, base_url):
                    test_results[system_name]['wechat_push_success'] = True
        
        print()
    
    # 总结测试结果
    print("=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)
    
    total_systems = len(target_systems)
    running_systems = sum(1 for r in test_results.values() if r['system_running'])
    available_predictions = sum(1 for r in test_results.values() if r['prediction_available'])
    successful_pushes = sum(1 for r in test_results.values() if r['wechat_push_success'])
    
    print(f"系统运行状态: {running_systems}/{total_systems}")
    print(f"预测数据可用: {available_predictions}/{total_systems}")
    print(f"微信推送成功: {successful_pushes}/{total_systems}")
    print()
    
    # 详细结果
    for system_name, system_desc in target_systems.items():
        result = test_results[system_name]
        status_icons = []
        
        status_icons.append("✅" if result['system_running'] else "❌")
        status_icons.append("✅" if result['prediction_available'] else "❌")
        status_icons.append("✅" if result['wechat_push_success'] else "❌")
        
        print(f"{system_desc:15} | 运行:{status_icons[0]} 预测:{status_icons[1]} 推送:{status_icons[2]}")
    
    print()
    
    # 给出建议
    if successful_pushes == total_systems:
        print("🎉 完美！所有系统的微信推送功能都正常工作")
        print("\n📱 现在可以启动自动推送器:")
        print("uv run python prediction_wechat_pusher.py")
    elif successful_pushes > 0:
        print(f"⚠️  部分系统正常工作 ({successful_pushes}/{total_systems})")
        print("请检查失败的系统并确保:")
        print("1. 系统已正确启动并初始化")
        print("2. 预测数据格式正确")
        print("3. 微信系统已连接")
    else:
        print("❌ 所有系统的微信推送都失败")
        print("请检查:")
        print("1. 统一预测平台2.0是否正常运行")
        print("2. 微信系统是否已连接")
        print("3. 各预测系统是否正确启动")
    
    print(f"\n🔧 管理界面: {base_url}")
    print(f"📱 微信管理: {base_url}/wechat-manager")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
