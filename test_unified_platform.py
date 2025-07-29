#!/usr/bin/env python3
"""
测试统一预测平台的导入
"""

print("开始测试导入...")

try:
    print("1. 测试基础导入...")
    from flask import Flask, render_template_string, jsonify, request
    print("   ✅ Flask导入成功")
    
    print("2. 测试自适应预测引擎...")
    from adaptive_prediction_engine import AdaptivePredictionEngine
    print("   ✅ 自适应预测引擎导入成功")
    
    print("3. 测试增强AI系统...")
    from enhanced_ai_prediction_system import EnhancedAIPredictionSystem
    print("   ✅ 增强AI系统导入成功")
    
    print("4. 测试传统ML系统...")
    from traditional_ml_system import TraditionalMLSystem
    print("   ✅ 传统ML系统导入成功")
    
    print("5. 测试自动交易系统...")
    from auto_trading_system import AutoTradingSystem
    print("   ✅ 自动交易系统导入成功")
    
    print("6. 测试简单预测系统...")
    from simple_prediction_system import SimplePredictionSystem
    print("   ✅ 简单预测系统导入成功")
    
    print("7. 测试统一数据管理器...")
    from unified_data_manager import data_manager
    print("   ✅ 统一数据管理器导入成功")
    
    print("\n🎉 所有导入测试通过！")
    
    # 测试创建Flask应用
    print("\n8. 测试Flask应用创建...")
    app = Flask(__name__)
    print("   ✅ Flask应用创建成功")
    
    print("\n✅ 统一平台准备就绪！")
    
except Exception as e:
    print(f"\n❌ 导入测试失败: {e}")
    import traceback
    traceback.print_exc()
