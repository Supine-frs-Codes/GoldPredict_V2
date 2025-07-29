#!/usr/bin/env python3
"""
简化的预测推送测试
验证三大系统的基本功能
"""

import requests
import json
import time

def test_server_connection():
    """测试服务器连接"""
    try:
        response = requests.get("http://localhost:5000/api/status", timeout=5)
        if response.status_code == 200:
            print("✅ 服务器连接正常")
            return True
        else:
            print(f"❌ 服务器响应异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 服务器连接失败: {e}")
        return False

def test_system_start(system_name):
    """测试系统启动"""
    try:
        print(f"🚀 尝试启动 {system_name} 系统")
        
        response = requests.post(f"http://localhost:5000/api/start/{system_name}", timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"   ✅ {system_name} 启动成功: {result.get('message')}")
                return True
            else:
                print(f"   ❌ {system_name} 启动失败: {result.get('message')}")
                return False
        else:
            print(f"   ❌ 启动请求失败: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ 启动异常: {e}")
        return False

def test_prediction_api(system_name):
    """测试预测API"""
    try:
        print(f"📊 测试 {system_name} 预测API")
        
        response = requests.get(f"http://localhost:5000/api/prediction/{system_name}", timeout=10)
        
        if response.status_code == 200:
            try:
                prediction = response.json()
                if 'error' not in prediction:
                    print(f"   ✅ 预测数据获取成功")
                    print(f"      当前价格: ${prediction.get('current_price', 0):.2f}")
                    print(f"      预测价格: ${prediction.get('predicted_price', 0):.2f}")
                    print(f"      置信度: {prediction.get('confidence', 0):.1%}")
                    return prediction
                else:
                    print(f"   ❌ API返回错误: {prediction['error']}")
                    return None
            except json.JSONDecodeError:
                print(f"   ❌ 响应格式错误")
                return None
        else:
            print(f"   ❌ API请求失败: HTTP {response.status_code}")
            return None
            
    except Exception as e:
        print(f"   ❌ 请求异常: {e}")
        return None

def test_wechat_push(system_name, prediction_data):
    """测试微信推送"""
    try:
        print(f"📱 测试 {system_name} 微信推送")
        
        response = requests.post(
            f"http://localhost:5000/api/wechat/test-prediction/{system_name}", 
            json=prediction_data, 
            timeout=30
        )
        
        if response.status_code == 200:
            try:
                result = response.json()
                if result.get('success'):
                    sent_groups = result.get('sent_groups', [])
                    print(f"   ✅ 推送成功: {len(sent_groups)} 个群聊")
                    return True
                else:
                    print(f"   ❌ 推送失败: {result.get('message')}")
                    return False
            except json.JSONDecodeError:
                print(f"   ❌ 响应格式错误")
                return False
        else:
            print(f"   ❌ 推送请求失败: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ 推送异常: {e}")
        return False

def main():
    """主测试流程"""
    print("🔧 简化预测推送测试")
    print("=" * 40)
    
    # 1. 测试服务器连接
    if not test_server_connection():
        print("\n请确保统一预测平台2.0正在运行:")
        print("uv run python unified_prediction_platform_fixed_ver2.0.py")
        return
    
    print()
    
    # 2. 测试三大系统
    systems = ['realtime', 'ai_enhanced', 'traditional']
    results = {}
    
    for system_name in systems:
        print(f"📋 测试 {system_name} 系统")
        print("-" * 30)
        
        results[system_name] = {
            'started': False,
            'prediction': False,
            'wechat': False
        }
        
        # 启动系统
        if test_system_start(system_name):
            results[system_name]['started'] = True
            time.sleep(2)  # 等待系统初始化
            
            # 测试预测
            prediction_data = test_prediction_api(system_name)
            if prediction_data:
                results[system_name]['prediction'] = True
                
                # 测试微信推送
                if test_wechat_push(system_name, prediction_data):
                    results[system_name]['wechat'] = True
        
        print()
    
    # 3. 总结结果
    print("=" * 40)
    print("📊 测试结果总结")
    print("=" * 40)
    
    for system_name in systems:
        result = results[system_name]
        status = []
        status.append("✅" if result['started'] else "❌")
        status.append("✅" if result['prediction'] else "❌")
        status.append("✅" if result['wechat'] else "❌")
        
        print(f"{system_name:12} | 启动:{status[0]} 预测:{status[1]} 推送:{status[2]}")
    
    # 统计
    total_started = sum(1 for r in results.values() if r['started'])
    total_prediction = sum(1 for r in results.values() if r['prediction'])
    total_wechat = sum(1 for r in results.values() if r['wechat'])
    
    print(f"\n总计: 启动 {total_started}/3, 预测 {total_prediction}/3, 推送 {total_wechat}/3")
    
    if total_wechat == 3:
        print("\n🎉 完美！所有系统都可以正常推送到微信")
        print("\n📱 现在可以启动自动推送器:")
        print("uv run python prediction_wechat_pusher.py")
    elif total_wechat > 0:
        print(f"\n⚠️  部分系统正常 ({total_wechat}/3)")
        print("可以启动自动推送器，但部分系统可能无法推送")
    else:
        print("\n❌ 所有系统推送都失败")
        print("请检查微信系统是否正常连接")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n测试被中断")
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
