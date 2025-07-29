#!/usr/bin/env python3
"""
快速实时预测演示
快速收集数据并执行预测，用于演示和测试
"""

import time
from simple_realtime_prediction import SimpleRealTimePrediction
from improved_mt5_manager import ImprovedMT5Manager

def fast_demo():
    """快速演示"""
    print("🚀 快速实时预测演示")
    print("=" * 40)
    
    # 测试MT5连接
    print("🔗 测试MT5连接...")
    manager = ImprovedMT5Manager()
    
    try:
        if not manager.ensure_connection():
            print("❌ MT5连接失败，演示终止")
            return
        
        symbol = manager.get_gold_symbol()
        if not symbol:
            print("❌ 未找到黄金符号，演示终止")
            return
        
        print(f"✅ MT5连接成功，黄金符号: {symbol}")
        
        # 获取初始价格
        initial_price = manager.get_current_price(symbol)
        if initial_price:
            main_price = initial_price['last'] if initial_price['last'] > 0 else initial_price['bid']
            print(f"📊 当前价格: ${main_price:.2f}")
        
        manager.cleanup()
        
    except Exception as e:
        print(f"❌ 连接测试失败: {e}")
        return
    
    print("\n🤖 启动快速预测系统...")
    print("配置:")
    print("   预测间隔: 1分钟")
    print("   数据收集: 每2秒")
    print("   最少数据: 5个点")
    print("   预期等待: 10-15秒")
    
    # 创建快速预测系统
    predictor = SimpleRealTimePrediction(
        interval_minutes=1,      # 1分钟预测间隔
        data_collection_seconds=2,  # 2秒收集一次数据
        min_data_points=5        # 5个数据点即可预测
    )
    
    try:
        predictor.start_prediction()
        
        print("\n⏱️ 等待数据收集和首次预测...")
        
        # 监控数据收集进度
        for i in range(30):  # 最多等待60秒
            time.sleep(2)
            data_count = len(predictor.price_history)
            print(f"[{i*2:2d}s] 数据点: {data_count}/5", end="")
            
            if data_count >= 5:
                print(" ✅ 数据充足")
                break
            else:
                print(" ⏳ 收集中...")
        
        # 等待首次预测
        print("\n🔮 等待首次预测执行...")
        time.sleep(65)  # 等待超过1分钟，触发预测
        
        # 显示结果
        print(f"\n📊 最终数据统计:")
        print(f"   收集数据点: {len(predictor.price_history)}")
        print(f"   预测次数: {len(predictor.prediction_history)}")
        
        if len(predictor.price_history) >= 3:
            print(f"\n📈 最近价格数据:")
            for i, price_data in enumerate(predictor.price_history[-3:]):
                timestamp = price_data['timestamp'][:19]
                price = price_data['price']
                print(f"   {i+1}. {timestamp} - ${price:.2f}")
        
        # 显示预测结果
        if len(predictor.prediction_history) > 0:
            latest_prediction = predictor.prediction_history[-1]
            print(f"\n🎯 最新预测:")
            print(f"   当前价格: ${latest_prediction['current_price']:.2f}")
            print(f"   预测价格: ${latest_prediction['predicted_price']:.2f}")
            print(f"   交易信号: {latest_prediction['signal']}")
            print(f"   置信度: {latest_prediction['confidence']:.1%}")
        else:
            print("\n⚠️ 暂无预测结果")
        
        # 获取统计信息
        stats = predictor.get_stats()
        print(f"\n📊 系统统计:")
        print(f"   总预测数: {stats['total_predictions']}")
        print(f"   平均准确率: {stats['average_accuracy']:.1%}")
        print(f"   优秀预测率: {stats['good_prediction_rate']:.1%}")
        
        print("\n⏹️ 停止预测系统...")
        predictor.stop_prediction()
        
        print("\n✅ 快速演示完成!")
        
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断演示")
        predictor.stop_prediction()
    except Exception as e:
        print(f"\n❌ 演示错误: {e}")
        predictor.stop_prediction()

def ultra_fast_demo():
    """超快速演示 - 仅用于测试数据收集"""
    print("⚡ 超快速数据收集测试")
    print("=" * 40)
    
    # 创建超快速配置
    predictor = SimpleRealTimePrediction(
        interval_minutes=1,      # 1分钟预测间隔
        data_collection_seconds=1,  # 1秒收集一次数据
        min_data_points=3        # 3个数据点即可预测
    )
    
    try:
        predictor.start_prediction()
        
        print("⏱️ 超快速数据收集 (10秒)...")
        
        for i in range(10):
            time.sleep(1)
            data_count = len(predictor.price_history)
            print(f"[{i+1:2d}s] 数据点: {data_count}")
            
            if data_count >= 3:
                print("✅ 数据收集完成，可以开始预测")
                break
        
        print(f"\n📊 收集到 {len(predictor.price_history)} 个数据点")
        
        if len(predictor.price_history) >= 2:
            print("📈 价格变化:")
            first_price = predictor.price_history[0]['price']
            last_price = predictor.price_history[-1]['price']
            change = last_price - first_price
            change_pct = (change / first_price) * 100
            print(f"   起始: ${first_price:.2f}")
            print(f"   最新: ${last_price:.2f}")
            print(f"   变化: {change:+.2f} ({change_pct:+.3f}%)")
        
        predictor.stop_prediction()
        print("✅ 超快速测试完成!")
        
    except Exception as e:
        print(f"❌ 测试错误: {e}")
        predictor.stop_prediction()

def main():
    """主函数"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--ultra-fast':
        ultra_fast_demo()
    else:
        fast_demo()

if __name__ == "__main__":
    main()
