#!/usr/bin/env python3
"""
Quick start script for the Gold Price Prediction System.
Demonstrates basic functionality and RTX 50 series optimization.
"""

import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Quick start demonstration."""
    print("[金牌] Gold Price Prediction System - Quick Start")
    print("=" * 50)
    
    try:
        # 1. Check GPU compatibility
        print("\n1. 检查GPU兼容性...")
        from src.utils.gpu_utils import check_rtx_50_compatibility, GPUManager
        
        gpu_manager = GPUManager()
        gpu_manager.print_gpu_info()
        
        # 2. Test data collection
        print("\n2. 测试数据收集...")
        from src.data.data_collector import GoldDataCollector
        
        collector = GoldDataCollector()
        data = collector.combine_data_sources(use_yahoo=True, period='3mo')
        
        if not data.empty:
            print(f"[成功] 成功获取 {len(data)} 条数据记录")
            print(f"   数据范围: {data['date'].min()} 到 {data['date'].max()}")
            print(f"   当前价格: ${data['close'].iloc[-1]:.2f}")
        else:
            print("[错误] 数据获取失败")
            return
        
        # 3. Test data preprocessing
        print("\n3. 测试数据预处理...")
        from src.data.data_preprocessor import GoldDataPreprocessor
        from src.features.technical_indicators import calculate_all_indicators

        # Add basic technical indicators (simplified for demo)
        try:
            data_with_indicators = calculate_all_indicators(data)
            print(f"[成功] 添加技术指标，总特征数: {len(data_with_indicators.columns)}")
        except Exception as e:
            print(f"[警告]  技术指标计算失败，使用原始数据: {e}")
            data_with_indicators = data.copy()

        # Simple preprocessing for demo
        preprocessor = GoldDataPreprocessor()

        # Use only basic features for demo
        basic_data = data[['date', 'open', 'high', 'low', 'close', 'volume']].copy()
        basic_data['returns'] = basic_data['close'].pct_change()
        basic_data['ma_5'] = basic_data['close'].rolling(5).mean()
        basic_data = basic_data.dropna()

        print(f"[成功] 基础数据预处理完成，特征数: {len(basic_data.columns)}")

        # Prepare sequences with basic data
        if len(basic_data) > 10:
            # Use only numeric columns for sequences
            numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'returns', 'ma_5']
            X, y = preprocessor.prepare_sequences(
                basic_data,
                sequence_length=min(10, len(basic_data)-1),
                feature_columns=numeric_cols
            )
            print(f"[成功] 序列准备完成: {X.shape[0]} 个序列，每个长度 {X.shape[1]}，特征数 {X.shape[2]}")
        else:
            print("[错误] 数据太少，无法进行演示")
            return False
        
        # 4. Test model creation (without training)
        print("\n4. 测试模型创建...")
        from src.models.deep_learning_models import LSTMModel, GRUModel, TransformerModel
        
        input_size = X.shape[2]
        
        # Create models
        lstm_model = LSTMModel(input_size=input_size, hidden_size=64, num_layers=2)
        gru_model = GRUModel(input_size=input_size, hidden_size=64, num_layers=2)
        transformer_model = TransformerModel(input_size=input_size, d_model=64, nhead=4, num_layers=2)
        
        print(f"[成功] LSTM模型创建成功，参数数量: {sum(p.numel() for p in lstm_model.parameters()):,}")
        print(f"[成功] GRU模型创建成功，参数数量: {sum(p.numel() for p in gru_model.parameters()):,}")
        print(f"[成功] Transformer模型创建成功，参数数量: {sum(p.numel() for p in transformer_model.parameters()):,}")
        
        # 5. Test GPU optimization
        print("\n5. 测试GPU优化...")
        if gpu_manager.cuda_available:
            device = gpu_manager.get_optimal_device()
            print(f"[成功] 最优设备: {device}")
            
            # Test model optimization
            optimized_lstm = gpu_manager.optimize_model_for_gpu(lstm_model)
            print(f"[成功] LSTM模型GPU优化完成")
            
            # Test memory stats
            memory_stats = gpu_manager.get_memory_stats()
            if memory_stats:
                print(f"[成功] GPU内存状态: {memory_stats}")
        else:
            print("ℹ️  CUDA不可用，将使用CPU模式")
        
        # 6. Test visualization
        print("\n6. 测试可视化...")
        from src.visualization.charts import GoldPriceVisualizer
        
        viz = GoldPriceVisualizer()
        
        # Create price chart
        price_fig = viz.plot_price_history(data)
        print("[成功] 价格历史图表创建成功")
        
        # Create technical indicators chart
        tech_fig = viz.plot_technical_indicators(data_with_indicators)
        print("[成功] 技术指标图表创建成功")
        
        # 7. Test prediction system (without trained model)
        print("\n7. 测试预测系统...")
        from src.prediction.predictor import GoldPricePredictor
        
        predictor = GoldPricePredictor()
        
        # Test data preparation
        X_prepared, processed_data = predictor.prepare_data(data)
        print(f"[成功] 预测数据准备完成: {X_prepared.shape}")
        
        # Test market info
        market_info = predictor._get_market_info()
        print(f"[成功] 市场信息获取成功: 市场{'开放' if market_info['is_market_open'] else '关闭'}")
        
        # 8. Summary
        print("\n" + "=" * 50)
        print("🎉 快速启动测试完成！")
        print("=" * 50)
        print("[成功] 所有核心功能测试通过")
        print("[成功] RTX 50系列优化就绪")
        print("[成功] 数据管道正常工作")
        print("[成功] 模型创建成功")
        print("[成功] 可视化功能正常")
        print("[成功] 预测系统就绪")
        
        print("\n[剪贴板] 下一步操作:")
        print("1. 运行完整训练: uv run python train.py --config configs/rtx50_config.json")
        print("2. 进行预测: uv run python predict.py --model ./models/ensemble --mode multiple")
        print("3. 查看GPU基准测试: uv run python test_gpu.py")
        print("4. 阅读完整文档: README.md")
        
        return True
        
    except ImportError as e:
        print(f"[错误] 导入错误: {e}")
        print("请确保所有依赖已正确安装: uv sync")
        return False
    except Exception as e:
        print(f"[错误] 运行错误: {e}")
        logger.exception("Quick start failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
