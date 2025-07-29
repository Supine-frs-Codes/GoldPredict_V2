#!/usr/bin/env python3
"""
测试Demo预测系统
验证预测功能和微信发送功能的集成
"""

import sys
import time
from datetime import datetime
from pathlib import Path

def test_demo_prediction():
    """测试Demo预测功能"""
    print("🎮 测试Demo预测系统")
    print("=" * 50)
    
    try:
        from demo_wechat_prediction_system import DemoWeChatPredictionSystem
        
        # 创建Demo系统
        demo = DemoWeChatPredictionSystem()
        print("✅ Demo系统创建成功")
        
        # 获取系统状态
        status = demo.get_status()
        print(f"📊 系统状态:")
        print(f"   运行状态: {'运行中' if status['running'] else '已停止'}")
        print(f"   微信连接: {'已连接' if status['wechat_connected'] else '未连接'}")
        print(f"   MT5连接: {'已连接' if status['mt5_connected'] else '未连接'}")
        print(f"   数据源: {status['data_source']}")
        print(f"   预测间隔: {status['prediction_interval']}秒")
        print(f"   预测数量: {status['predictions_count']}")

        # 显示MT5状态详情
        mt5_status = status['mt5_status']
        if mt5_status['connected']:
            print(f"   MT5符号: {mt5_status['symbol']}")
            print(f"   当前价格: ${mt5_status['current_price']:.2f}")
            print(f"   买价/卖价: ${mt5_status['bid']:.2f} / ${mt5_status['ask']:.2f}")
        else:
            print(f"   MT5错误: {mt5_status.get('error', '未知错误')}")
            print("   💡 请确保MetaTrader5终端已启动并登录")
        
        # 测试手动预测
        print("\n🔮 执行手动预测...")
        result = demo.manual_prediction()
        
        if result['success']:
            pred = result['prediction']
            print("✅ 预测生成成功!")
            print(f"📈 预测结果:")
            print(f"   当前价格: ${pred['current_price']:.2f}")
            print(f"   预测价格: ${pred['predicted_price']:.2f}")
            print(f"   价格变化: {pred['price_change']:+.2f} ({pred['price_change_pct']:+.2f}%)")
            print(f"   交易信号: {pred['signal']}")
            print(f"   置信度: {pred['confidence']:.1%}")
            print(f"   预测方法: {pred['method']}")
            
            # 显示技术指标
            if 'technical_data' in pred:
                tech = pred['technical_data']
                print(f"\n📊 技术指标:")
                if tech.get('rsi'):
                    print(f"   RSI: {tech['rsi']:.2f}")
                if tech.get('ma5') and tech.get('ma20'):
                    print(f"   MA5: ${tech['ma5']:.2f}")
                    print(f"   MA20: ${tech['ma20']:.2f}")
                if tech.get('volume'):
                    print(f"   成交量: {tech['volume']:,.0f}")
            
            # 显示预测因子
            if 'factors' in pred:
                print(f"\n🔍 预测因子:")
                for factor in pred['factors']:
                    signal_text = "看涨" if factor['signal'] > 0 else "看跌" if factor['signal'] < 0 else "中性"
                    print(f"   {factor['name']}: {signal_text} (权重: {factor['weight']:.1f})")
            
            # 微信发送结果
            wechat_result = result['wechat_result']
            print(f"\n📱 微信发送结果:")
            if wechat_result['success']:
                print(f"   ✅ 发送成功到: {', '.join(wechat_result['sent_groups'])}")
                if wechat_result['failed_groups']:
                    print(f"   ❌ 发送失败: {', '.join(wechat_result['failed_groups'])}")
            else:
                print(f"   ❌ 发送失败: {', '.join(wechat_result.get('errors', ['未知错误']))}")
                print(f"   💡 提示: 请确保微信PC版已启动并登录")
        else:
            print(f"❌ 预测生成失败: {result.get('message', '未知错误')}")
        
        return result['success']
        
    except Exception as e:
        print(f"❌ Demo系统测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_mt5_connection():
    """测试MT5连接"""
    print("\n🔗 测试MT5连接")
    print("-" * 40)

    try:
        from improved_mt5_manager import ImprovedMT5Manager

        mt5_manager = ImprovedMT5Manager()
        print("✅ MT5管理器创建成功")

        # 尝试连接MT5
        print("正在尝试连接MetaTrader5...")
        print("⚠️  请确保:")
        print("   1. MetaTrader5终端已启动")
        print("   2. 已登录MT5账户")
        print("   3. XAUUSD符号可用")

        if mt5_manager.ensure_connection():
            print("✅ MT5连接成功!")

            # 获取当前价格
            current_price = mt5_manager.get_current_price("XAUUSD")
            if current_price:
                print(f"✅ 获取XAUUSD价格成功:")
                print(f"   买价: ${current_price['bid']:.2f}")
                print(f"   卖价: ${current_price['ask']:.2f}")
                print(f"   中间价: ${(current_price['bid'] + current_price['ask']) / 2:.2f}")
                print(f"   更新时间: {current_price['time']}")
            else:
                print("⚠️  无法获取价格数据")

            return True
        else:
            print("❌ MT5连接失败")
            print("\n💡 可能的解决方案:")
            print("   1. 确保MetaTrader5终端已启动并登录")
            print("   2. 检查网络连接")
            print("   3. 确认XAUUSD符号可用")
            print("   4. 重启MetaTrader5终端")
            return False

    except Exception as e:
        print(f"❌ MT5连接测试失败: {e}")
        return False

def test_wechat_connection():
    """测试微信连接"""
    print("\n📱 测试微信连接")
    print("-" * 40)
    
    try:
        from wechat_sender import WeChatSender
        
        sender = WeChatSender()
        print("✅ 微信发送器创建成功")
        
        # 尝试连接微信
        print("正在尝试连接微信...")
        print("⚠️  请确保:")
        print("   1. 微信PC版已启动并登录")
        print("   2. 微信版本兼容wxauto库")
        
        if sender.connect_wechat():
            print("✅ 微信连接成功!")
            
            # 获取群聊列表
            groups = sender.get_group_list()
            if groups:
                print(f"✅ 找到 {len(groups)} 个群聊:")
                for i, group in enumerate(groups[:5], 1):  # 只显示前5个
                    print(f"   {i}. {group}")
                if len(groups) > 5:
                    print(f"   ... 还有 {len(groups) - 5} 个群聊")
            else:
                print("⚠️  未找到群聊")
            
            sender.disconnect_wechat()
            return True
        else:
            print("❌ 微信连接失败")
            print(f"   错误: {sender.last_error}")
            print("\n💡 可能的解决方案:")
            print("   1. 确保微信PC版已启动并登录")
            print("   2. 尝试重启微信")
            print("   3. 检查wxauto库版本")
            return False
            
    except Exception as e:
        print(f"❌ 微信连接测试失败: {e}")
        return False

def main():
    """主测试流程"""
    print("🚀 Demo系统和微信集成测试 (MT5版)")
    print("=" * 50)
    print("此测试将验证基于MT5的Demo预测系统和微信发送功能")
    print("=" * 50)

    try:
        # 1. 测试MT5连接
        mt5_ok = test_mt5_connection()

        # 2. 测试微信连接
        wechat_ok = test_wechat_connection()

        # 3. 测试Demo预测
        demo_ok = test_demo_prediction()

        # 总结
        print("\n" + "=" * 50)
        print("📊 测试结果总结")
        print("=" * 50)

        print(f"{'✅' if mt5_ok else '❌'} MT5连接: {'成功' if mt5_ok else '失败'}")
        print(f"{'✅' if wechat_ok else '❌'} 微信连接: {'成功' if wechat_ok else '失败'}")
        print(f"{'✅' if demo_ok else '❌'} Demo预测: {'成功' if demo_ok else '失败'}")

        if mt5_ok and wechat_ok and demo_ok:
            print("\n🎉 所有测试通过！系统已准备就绪")
            print("\n🚀 使用建议:")
            print("1. 确保MetaTrader5终端保持运行")
            print("2. 配置 wechat_config.json 中的目标群聊")
            print("3. 启动Web管理界面: uv run python wechat_web_interface.py")
            print("4. 或直接使用Demo系统: uv run python demo_wechat_prediction_system.py")
        elif demo_ok:
            if not mt5_ok:
                print("\n⚠️  MT5连接失败，预测功能可能受限")
                print("请检查MetaTrader5终端是否正常运行")
            if not wechat_ok:
                print("\n⚠️  微信连接失败，无法发送消息")
                print("请检查微信PC版是否正常运行")
        else:
            print("\n❌ 测试失败，请检查系统配置")
        
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
