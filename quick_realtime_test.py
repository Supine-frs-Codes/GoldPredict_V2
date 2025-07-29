#!/usr/bin/env python3
"""
快速实时预测测试
用于验证系统功能
"""

import time
from simple_realtime_prediction import SimpleRealTimePrediction
from improved_mt5_manager import ImprovedMT5Manager

def test_mt5_connection():
    """测试MT5连接"""
    print("🔗 测试改进的MT5连接...")

    manager = ImprovedMT5Manager()

    try:
        # 使用改进的连接测试
        if manager.test_connection():
            print("✅ 改进的MT5连接测试成功")
            return True
        else:
            print("❌ 改进的MT5连接测试失败")
            return False
    finally:
        manager.cleanup()

def quick_prediction_test():
    """快速预测测试"""
    print("\n🤖 快速预测测试...")
    
    # 测试MT5连接
    if not test_mt5_connection():
        print("❌ 无法连接MT5，测试终止")
        return
    
    print("\n🚀 启动实时预测系统 (快速模式)...")
    # 使用快速模式：2秒收集间隔，5个数据点即可预测
    predictor = SimpleRealTimePrediction(
        interval_minutes=1,
        data_collection_seconds=2,
        min_data_points=5
    )

    try:
        predictor.start_prediction()

        print("⏱️ 等待数据收集 (15秒)...")
        time.sleep(15)
        
        print(f"📊 当前数据点数: {len(predictor.price_history)}")
        
        if len(predictor.price_history) >= 5:
            print("✅ 数据收集正常")
            
            # 显示最近的价格数据
            print("\n📈 最近价格数据:")
            for i, price_data in enumerate(predictor.price_history[-5:]):
                print(f"   {i+1}. {price_data['timestamp'][:19]} - ${price_data['price']:.2f}")
        else:
            print("⚠️ 数据收集不足")
        
        print("\n⏹️ 停止预测系统...")
        predictor.stop_prediction()
        
        # 显示统计信息
        stats = predictor.get_stats()
        print(f"\n📊 统计信息:")
        print(f"   总预测数: {stats['total_predictions']}")
        print(f"   平均准确率: {stats['average_accuracy']:.1%}")
        print(f"   优秀预测率: {stats['good_prediction_rate']:.1%}")
        
        print("\n✅ 快速测试完成!")
        
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断测试")
        predictor.stop_prediction()
    except Exception as e:
        print(f"\n❌ 测试错误: {e}")
        predictor.stop_prediction()

def main():
    """主函数"""
    print("🧪 实时预测系统快速测试")
    print("=" * 40)
    
    quick_prediction_test()

if __name__ == "__main__":
    main()
