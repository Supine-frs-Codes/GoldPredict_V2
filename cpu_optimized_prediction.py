#!/usr/bin/env python3
"""
CPU优化的终极预测系统
针对CPU环境优化的高级预测功能
"""

import torch
import numpy as np
import pandas as pd
from pathlib import Path
import logging
import json
from datetime import datetime, timedelta
import warnings
import multiprocessing as mp
warnings.filterwarnings('ignore')

from src.data.data_collector import GoldDataCollector
from src.data.data_preprocessor import GoldDataPreprocessor
from src.visualization.charts import GoldPriceVisualizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CPUOptimizedPredictor:
    """CPU优化的预测器"""
    
    def __init__(self, config: dict = None):
        default_config = self._get_default_config()
        if config:
            default_config.update(config)
        self.config = default_config
        
        # CPU优化设置
        torch.set_num_threads(mp.cpu_count())
        torch.set_num_interop_threads(mp.cpu_count())
        
        logger.info(f"[系统] CPU优化预测器初始化")
        logger.info(f"[CPU] 线程数: {torch.get_num_threads()}")
        logger.info(f"[CPU] 交互线程数: {torch.get_num_interop_threads()}")
        
        # 初始化组件
        self.data_collector = GoldDataCollector()
        self.preprocessor = GoldDataPreprocessor()
        self.visualizer = GoldPriceVisualizer()
        
        # 结果存储
        self.results = {}
        
    def _get_default_config(self) -> dict:
        """获取CPU优化的默认配置"""
        return {
            # 数据配置
            'data_period': '1y',  # 1年历史数据（减少内存使用）
            'sequence_length': 30,  # 较短序列长度
            'prediction_horizons': [1, 5, 10, 30],
            
            # 模型配置（CPU优化）
            'model_config': {
                'hidden_size': 128,  # 较小的隐藏层
                'num_layers': 2,     # 较少的层数
                'dropout': 0.2,
                'use_attention': True,
                'use_ensemble': True
            },
            
            # 训练配置（CPU优化）
            'epochs': 50,           # 较少的训练轮数
            'batch_size': 32,       # 较小的批次大小
            'learning_rate': 0.001,
            'weight_decay': 1e-4,
            'early_stopping_patience': 10,
            
            # CPU特定优化
            'num_workers': min(4, mp.cpu_count()),
            'pin_memory': False,    # CPU不需要
            'compile_model': False, # CPU编译可能较慢
            
            # 输出配置
            'save_model': True,
            'save_predictions': True,
            'create_visualizations': True
        }
    
    def create_advanced_cpu_model(self, input_size: int) -> torch.nn.Module:
        """创建CPU优化的高级模型"""
        
        class CPUOptimizedLSTM(torch.nn.Module):
            def __init__(self, input_size, hidden_size=128, num_layers=2, dropout=0.2):
                super().__init__()
                
                # LSTM层
                self.lstm = torch.nn.LSTM(
                    input_size=input_size,
                    hidden_size=hidden_size,
                    num_layers=num_layers,
                    dropout=dropout if num_layers > 1 else 0,
                    batch_first=True,
                    bidirectional=True
                )
                
                # 注意力机制
                self.attention = torch.nn.MultiheadAttention(
                    embed_dim=hidden_size * 2,
                    num_heads=4,
                    dropout=dropout,
                    batch_first=True
                )
                
                # 输出层
                self.output_layers = torch.nn.ModuleDict({
                    'price': torch.nn.Sequential(
                        torch.nn.Linear(hidden_size * 2, hidden_size),
                        torch.nn.ReLU(),
                        torch.nn.Dropout(dropout),
                        torch.nn.Linear(hidden_size, 1)
                    ),
                    'volatility': torch.nn.Sequential(
                        torch.nn.Linear(hidden_size * 2, hidden_size // 2),
                        torch.nn.ReLU(),
                        torch.nn.Dropout(dropout),
                        torch.nn.Linear(hidden_size // 2, 1)
                    ),
                    'trend': torch.nn.Sequential(
                        torch.nn.Linear(hidden_size * 2, hidden_size // 2),
                        torch.nn.ReLU(),
                        torch.nn.Dropout(dropout),
                        torch.nn.Linear(hidden_size // 2, 3)  # 上涨、下跌、横盘
                    )
                })
                
            def forward(self, x):
                # LSTM处理
                lstm_out, _ = self.lstm(x)
                
                # 注意力机制
                attn_out, _ = self.attention(lstm_out, lstm_out, lstm_out)
                
                # 使用最后一个时间步
                last_output = attn_out[:, -1, :]
                
                # 多任务输出
                outputs = {}
                for task, layer in self.output_layers.items():
                    outputs[task] = layer(last_output)
                
                return outputs
        
        return CPUOptimizedLSTM(
            input_size=input_size,
            hidden_size=self.config['model_config']['hidden_size'],
            num_layers=self.config['model_config']['num_layers'],
            dropout=self.config['model_config']['dropout']
        )
    
    def train_cpu_optimized_model(self, X_train, y_train, X_val, y_val):
        """CPU优化的训练过程"""
        logger.info("[训练] 开始CPU优化训练...")
        
        # 创建模型
        input_size = X_train.shape[-1]
        model = self.create_advanced_cpu_model(input_size)
        
        logger.info(f"[模型] CPU优化模型创建完成")
        logger.info(f"   参数数量: {sum(p.numel() for p in model.parameters()):,}")
        
        # 优化器和损失函数
        optimizer = torch.optim.AdamW(
            model.parameters(),
            lr=self.config['learning_rate'],
            weight_decay=self.config['weight_decay']
        )
        
        # 多任务损失函数
        price_criterion = torch.nn.MSELoss()
        volatility_criterion = torch.nn.MSELoss()
        trend_criterion = torch.nn.CrossEntropyLoss()
        
        # 学习率调度器
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode='min', factor=0.5, patience=5
        )
        
        # 数据加载器
        train_dataset = torch.utils.data.TensorDataset(
            torch.FloatTensor(X_train),
            torch.FloatTensor(y_train)
        )
        val_dataset = torch.utils.data.TensorDataset(
            torch.FloatTensor(X_val),
            torch.FloatTensor(y_val)
        )
        
        train_loader = torch.utils.data.DataLoader(
            train_dataset,
            batch_size=self.config['batch_size'],
            shuffle=True,
            num_workers=self.config['num_workers']
        )
        val_loader = torch.utils.data.DataLoader(
            val_dataset,
            batch_size=self.config['batch_size'],
            shuffle=False,
            num_workers=self.config['num_workers']
        )
        
        # 训练循环
        best_val_loss = float('inf')
        patience_counter = 0
        history = {'train_loss': [], 'val_loss': [], 'learning_rate': []}
        
        for epoch in range(self.config['epochs']):
            # 训练阶段
            model.train()
            train_loss = 0.0
            
            for batch_x, batch_y in train_loader:
                optimizer.zero_grad()
                
                outputs = model(batch_x)
                
                # 多任务损失
                price_loss = price_criterion(outputs['price'], batch_y)
                
                # 简化版本：主要关注价格预测
                loss = price_loss
                
                loss.backward()
                
                # 梯度裁剪
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                
                optimizer.step()
                train_loss += loss.item()
            
            # 验证阶段
            model.eval()
            val_loss = 0.0
            
            with torch.no_grad():
                for batch_x, batch_y in val_loader:
                    outputs = model(batch_x)
                    loss = price_criterion(outputs['price'], batch_y)
                    val_loss += loss.item()
            
            train_loss /= len(train_loader)
            val_loss /= len(val_loader)
            
            # 学习率调度
            scheduler.step(val_loss)
            current_lr = optimizer.param_groups[0]['lr']
            
            # 记录历史
            history['train_loss'].append(train_loss)
            history['val_loss'].append(val_loss)
            history['learning_rate'].append(current_lr)
            
            # 早停检查
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                best_model_state = model.state_dict().copy()
            else:
                patience_counter += 1
            
            # 打印进度
            if epoch % 10 == 0 or epoch == self.config['epochs'] - 1:
                logger.info(
                    f"Epoch {epoch+1}/{self.config['epochs']} - "
                    f"Train Loss: {train_loss:.6f}, "
                    f"Val Loss: {val_loss:.6f}, "
                    f"LR: {current_lr:.2e}"
                )
            
            # 早停
            if patience_counter >= self.config['early_stopping_patience']:
                logger.info(f"Early stopping at epoch {epoch+1}")
                break
        
        # 加载最佳模型
        model.load_state_dict(best_model_state)
        
        logger.info(f"[训练] 完成 - 最佳验证损失: {best_val_loss:.6f}")
        
        return model, history
    
    def make_advanced_predictions(self, model, data: pd.DataFrame) -> dict:
        """进行高级预测"""
        logger.info("[预测] 开始高级多时间跨度预测...")
        
        # 预处理最新数据
        processed_data = self.preprocessor.create_features(data)
        latest_sequence = processed_data.iloc[-self.config['sequence_length']:].values
        latest_sequence = torch.FloatTensor(latest_sequence).unsqueeze(0)
        
        model.eval()
        predictions = {}
        current_price = data['close'].iloc[-1]
        
        with torch.no_grad():
            # 基础预测
            outputs = model(latest_sequence)
            base_prediction = outputs['price'].item()
            
            # 多时间跨度预测
            for horizon in self.config['prediction_horizons']:
                # 使用不同的时间衰减因子
                time_factor = 1 + (horizon - 1) * 0.1  # 时间越长，不确定性越大
                
                # 计算预测价格
                pred_price = base_prediction * time_factor
                price_change = pred_price - current_price
                price_change_pct = (price_change / current_price) * 100
                
                # 计算置信区间（基于历史波动率）
                volatility = data['close'].pct_change().std() * np.sqrt(horizon)
                confidence_lower = pred_price * (1 - volatility * 1.96)
                confidence_upper = pred_price * (1 + volatility * 1.96)
                
                predictions[f'{horizon}_day'] = {
                    'horizon_days': horizon,
                    'current_price': float(current_price),
                    'predicted_price': float(pred_price),
                    'price_change': float(price_change),
                    'price_change_pct': float(price_change_pct),
                    'confidence_lower': float(confidence_lower),
                    'confidence_upper': float(confidence_upper),
                    'confidence_interval': f"${confidence_lower:.2f} - ${confidence_upper:.2f}",
                    'prediction_date': (datetime.now() + timedelta(days=horizon)).isoformat()
                }
                
                logger.info(f"   {horizon}天预测: ${pred_price:.2f} ({price_change_pct:+.2f}%)")
        
        return predictions
    
    def run_complete_prediction(self) -> dict:
        """运行完整的CPU优化预测流程"""
        logger.info("[启动] CPU优化终极预测系统")
        logger.info("=" * 60)
        
        start_time = datetime.now()
        
        try:
            # 1. 数据收集
            logger.info("[步骤1] 数据收集...")
            data = self.data_collector.combine_data_sources(
                use_yahoo=True, period=self.config['data_period']
            )
            logger.info(f"   获取 {len(data)} 条数据")
            
            # 2. 数据预处理
            logger.info("[步骤2] 数据预处理...")
            processed_data = self.preprocessor.create_features(data)
            sequences, targets = self.preprocessor.create_sequences(
                processed_data, 
                sequence_length=self.config['sequence_length'],
                target_column='close'
            )
            
            # 数据分割
            train_size = int(0.7 * len(sequences))
            val_size = int(0.2 * len(sequences))
            
            X_train = sequences[:train_size]
            y_train = targets[:train_size]
            X_val = sequences[train_size:train_size+val_size]
            y_val = targets[train_size:train_size+val_size]
            X_test = sequences[train_size+val_size:]
            y_test = targets[train_size+val_size:]
            
            logger.info(f"   训练集: {len(X_train)}, 验证集: {len(X_val)}, 测试集: {len(X_test)}")
            
            # 3. 模型训练
            logger.info("[步骤3] 模型训练...")
            model, history = self.train_cpu_optimized_model(X_train, y_train, X_val, y_val)
            
            # 4. 模型评估
            logger.info("[步骤4] 模型评估...")
            model.eval()
            with torch.no_grad():
                test_outputs = model(torch.FloatTensor(X_test))
                test_predictions = test_outputs['price'].numpy()
                
                from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
                mse = mean_squared_error(y_test, test_predictions)
                mae = mean_absolute_error(y_test, test_predictions)
                r2 = r2_score(y_test, test_predictions)
                
                metrics = {
                    'mse': float(mse),
                    'mae': float(mae),
                    'rmse': float(np.sqrt(mse)),
                    'r2': float(r2)
                }
                
                logger.info(f"   RMSE: {metrics['rmse']:.4f}, R²: {metrics['r2']:.4f}")
            
            # 5. 进行预测
            logger.info("[步骤5] 多时间跨度预测...")
            predictions = self.make_advanced_predictions(model, data)
            
            # 6. 创建可视化
            logger.info("[步骤6] 创建可视化...")
            visualization_files = []
            
            # 价格历史图
            fig1 = self.visualizer.plot_price_history(data)
            path1 = Path("results/visualizations/cpu_price_history.html")
            path1.parent.mkdir(parents=True, exist_ok=True)
            fig1.write_html(str(path1))
            visualization_files.append(str(path1))
            
            # 交互式预测图
            fig2 = self.visualizer.plot_interactive_multi_predictions(data, predictions)
            path2 = Path("results/visualizations/cpu_interactive_predictions.html")
            fig2.write_html(str(path2))
            visualization_files.append(str(path2))
            
            # 训练历史图
            fig3 = self.visualizer.plot_training_history(history)
            path3 = Path("results/visualizations/cpu_training_history.html")
            fig3.write_html(str(path3))
            visualization_files.append(str(path3))
            
            # 7. 保存结果
            end_time = datetime.now()
            total_time = (end_time - start_time).total_seconds()
            
            # 保存模型
            if self.config['save_model']:
                model_path = Path("results/models/cpu_optimized_model.pth")
                model_path.parent.mkdir(parents=True, exist_ok=True)
                torch.save({
                    'model_state_dict': model.state_dict(),
                    'config': self.config,
                    'history': history,
                    'metrics': metrics
                }, model_path)
            
            # 保存预测结果
            if self.config['save_predictions']:
                pred_path = Path("results/predictions/cpu_optimized_predictions.json")
                pred_path.parent.mkdir(parents=True, exist_ok=True)
                
                result = {
                    'timestamp': datetime.now().isoformat(),
                    'model_type': 'cpu_optimized',
                    'predictions': predictions,
                    'metrics': metrics,
                    'config': self.config,
                    'total_time_seconds': total_time
                }
                
                with open(pred_path, 'w') as f:
                    json.dump(result, f, indent=2)
            
            # 生成总结
            summary = {
                'status': 'success',
                'total_time_seconds': total_time,
                'data_points': len(data),
                'model_type': 'cpu_optimized',
                'metrics': metrics,
                'predictions': predictions,
                'visualization_files': visualization_files
            }
            
            logger.info("=" * 60)
            logger.info("[完成] CPU优化预测系统运行完成!")
            logger.info(f"   总耗时: {total_time:.2f}秒")
            logger.info(f"   模型性能: RMSE={metrics['rmse']:.4f}, R²={metrics['r2']:.4f}")
            logger.info(f"   预测结果: {len(predictions)} 个时间跨度")
            logger.info(f"   可视化文件: {len(visualization_files)} 个")
            
            return summary
            
        except Exception as e:
            logger.error(f"[错误] CPU优化预测失败: {e}")
            raise


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='CPU优化终极预测系统')
    parser.add_argument('--epochs', type=int, default=50, help='训练轮数')
    parser.add_argument('--batch-size', type=int, default=32, help='批次大小')
    parser.add_argument('--learning-rate', type=float, default=0.001, help='学习率')
    
    args = parser.parse_args()
    
    # 配置
    config = {
        'epochs': args.epochs,
        'batch_size': args.batch_size,
        'learning_rate': args.learning_rate,
        'data_period': '1y',
        'sequence_length': 30,
        'prediction_horizons': [1, 5, 10, 30],
        'model_config': {
            'hidden_size': 128,
            'num_layers': 2,
            'dropout': 0.2,
            'use_attention': True,
            'use_ensemble': True
        },
        'weight_decay': 1e-4,
        'early_stopping_patience': 10,
        'num_workers': 4,
        'pin_memory': False,
        'compile_model': False,
        'save_model': True,
        'save_predictions': True,
        'create_visualizations': True
    }
    
    # 运行预测系统
    predictor = CPUOptimizedPredictor(config)
    results = predictor.run_complete_prediction()
    
    print(f"\n[完成] CPU优化预测系统运行完成!")
    print(f"查看结果: {results.get('visualization_files', [])}")


if __name__ == "__main__":
    main()
