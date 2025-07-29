#!/usr/bin/env python3
"""
演示黄金价格预测功能
"""

import numpy as np
import pandas as pd
import torch
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import logging

from src.data.data_collector import GoldDataCollector
from src.data.data_preprocessor import GoldDataPreprocessor
from src.features.technical_indicators import calculate_all_indicators
from src.models.deep_learning_models import LSTMModel, DeepLearningTrainer, TimeSeriesDataset
from src.visualization.charts import GoldPriceVisualizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """演示预测功能"""
    print("[金牌] 黄金价格预测演示")
    print("=" * 50)
    
    # 1. 获取数据
    print("\n1. 获取最新黄金价格数据...")
    collector = GoldDataCollector()
    data = collector.combine_data_sources(use_yahoo=True, period='6mo')
    
    if data.empty:
        print("[错误] 无法获取数据")
        return
    
    print(f"[成功] 获取到 {len(data)} 条数据")
    print(f"   时间范围: {data['date'].min()} 到 {data['date'].max()}")
    print(f"   当前价格: ${data['close'].iloc[-1]:.2f}")
    
    # 2. 数据预处理
    print("\n2. 数据预处理...")
    
    # 简化的预处理，避免过度清洗
    preprocessor = GoldDataPreprocessor()
    
    # 添加基本特征
    data['returns'] = data['close'].pct_change()
    data['ma_5'] = data['close'].rolling(5).mean()
    data['ma_20'] = data['close'].rolling(20).mean()
    data['volatility'] = data['returns'].rolling(10).std()
    
    # 清理数据
    data = data.dropna().reset_index(drop=True)
    
    print(f"[成功] 预处理完成，剩余 {len(data)} 条数据")
    
    # 3. 准备训练数据
    print("\n3. 准备训练数据...")
    
    # 选择特征
    feature_cols = ['open', 'high', 'low', 'close', 'volume', 'returns', 'ma_5', 'ma_20', 'volatility']
    sequence_length = 20
    
    # 创建序列
    X, y = preprocessor.prepare_sequences(
        data, 
        sequence_length=sequence_length,
        feature_columns=feature_cols
    )
    
    print(f"[成功] 创建了 {len(X)} 个序列，特征维度: {X.shape}")
    
    # 4. 训练简单模型
    print("\n4. 训练LSTM模型...")
    
    # 分割数据
    split_idx = int(0.8 * len(X))
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    
    # 标准化
    X_train_scaled, X_test_scaled, y_train_scaled, y_test_scaled = preprocessor.scale_data(
        X_train, X_test, y_train, y_test
    )
    
    # 创建模型
    input_size = X_train_scaled.shape[2]
    model = LSTMModel(input_size=input_size, hidden_size=64, num_layers=2)
    
    # 训练
    trainer = DeepLearningTrainer(model, device='cpu', learning_rate=0.001)
    
    # 创建数据加载器
    from torch.utils.data import DataLoader
    train_dataset = TimeSeriesDataset(X_train_scaled, y_train_scaled)
    val_dataset = TimeSeriesDataset(X_test_scaled, y_test_scaled)
    
    train_loader = DataLoader(train_dataset, batch_size=8, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=8, shuffle=False)
    
    # 训练模型
    history = trainer.train(
        train_loader=train_loader,
        val_loader=val_loader,
        epochs=30,
        early_stopping_patience=10
    )
    
    print(f"[成功] 训练完成，最佳验证损失: {history['best_val_loss']:.6f}")
    
    # 5. 进行预测
    print("\n5. 进行价格预测...")
    
    # 使用最后的序列进行预测
    last_sequence = X_test_scaled[-1:] if len(X_test_scaled) > 0 else X_train_scaled[-1:]
    
    model.eval()
    with torch.no_grad():
        prediction_tensor = model(torch.FloatTensor(last_sequence))
        prediction_scaled = prediction_tensor.numpy().item()  # 获取标量值

    # 反标准化
    prediction = preprocessor.inverse_transform_target(np.array([prediction_scaled]))[0]
    current_price = data['close'].iloc[-1]
    
    # 计算预测结果
    price_change = prediction - current_price
    price_change_pct = (price_change / current_price) * 100
    
    print(f"[成功] 预测结果:")
    print(f"   当前价格: ${current_price:.2f}")
    print(f"   预测价格: ${prediction:.2f}")
    print(f"   价格变化: ${price_change:.2f} ({price_change_pct:+.2f}%)")
    
    # 6. 创建可视化
    print("\n6. 创建可视化图表...")
    
    try:
        viz = GoldPriceVisualizer()
        
        # 价格历史图
        fig = viz.plot_price_history(data)
        
        # 添加预测点
        import plotly.graph_objects as go
        
        # 预测日期（假设预测明天的价格）
        last_date = pd.to_datetime(data['date'].iloc[-1])
        pred_date = last_date + timedelta(days=1)
        
        fig.add_trace(go.Scatter(
            x=[pred_date],
            y=[prediction],
            mode='markers',
            name='预测价格',
            marker=dict(size=15, color='red', symbol='diamond'),
            hovertemplate=f"<b>预测价格</b><br>日期: {pred_date.strftime('%Y-%m-%d')}<br>价格: ${prediction:.2f}<br>变化: {price_change_pct:+.2f}%<extra></extra>"
        ))
        
        fig.update_layout(title="黄金价格历史与预测")
        
        # 保存图表
        fig.write_html("gold_price_prediction.html")
        print("[成功] 图表已保存为 gold_price_prediction.html")
        
    except Exception as e:
        print(f"[警告]  可视化创建失败: {e}")
    
    # 7. 模型性能评估
    print("\n7. 模型性能评估...")
    
    if len(X_test_scaled) > 0:
        # 在测试集上评估
        test_predictions = trainer.predict(val_loader)
        test_predictions_original = preprocessor.inverse_transform_target(test_predictions)
        y_test_original = preprocessor.inverse_transform_target(y_test_scaled)
        
        # 计算指标
        from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
        
        mse = mean_squared_error(y_test_original, test_predictions_original)
        mae = mean_absolute_error(y_test_original, test_predictions_original)
        r2 = r2_score(y_test_original, test_predictions_original)
        
        print(f"[成功] 测试集性能:")
        print(f"   均方误差 (MSE): {mse:.2f}")
        print(f"   平均绝对误差 (MAE): {mae:.2f}")
        print(f"   R² 分数: {r2:.4f}")
    
    # 8. 总结
    print("\n" + "=" * 50)
    print("[完成] 黄金价格预测演示完成！")
    print("=" * 50)
    print("[成功] 数据获取和预处理成功")
    print("[成功] LSTM模型训练完成")
    print("[成功] 价格预测生成")
    print("[成功] 可视化图表创建")
    print("[成功] 性能评估完成")
    
    print(f"\n[数据] 关键结果:")
    print(f"   • 训练数据: {len(X_train)} 个序列")
    print(f"   • 测试数据: {len(X_test)} 个序列")
    print(f"   • 当前价格: ${current_price:.2f}")
    print(f"   • 预测价格: ${prediction:.2f}")
    print(f"   • 预期变化: {price_change_pct:+.2f}%")
    
    print(f"\n[任务] 下一步建议:")
    print("   1. 收集更多历史数据以提高预测准确性")
    print("   2. 添加更多技术指标和宏观经济数据")
    print("   3. 尝试不同的模型架构和超参数")
    print("   4. 实施交叉验证和更严格的模型评估")
    print("   5. 考虑集成多个模型以提高稳定性")
    
    return True

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[错误] 演示失败: {e}")
        import traceback
        traceback.print_exc()
