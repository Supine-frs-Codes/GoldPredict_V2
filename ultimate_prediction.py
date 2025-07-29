#!/usr/bin/env python3
"""
一键终极预测系统
从数据收集到模型训练再到可视化的完整流程
"""

import torch
import numpy as np
import pandas as pd
from pathlib import Path
import logging
import json
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

from src.data.data_collector import GoldDataCollector
from src.data.data_preprocessor import GoldDataPreprocessor
from src.models.advanced_models import create_advanced_model
from src.training.advanced_trainer import AdvancedTrainer
from src.visualization.charts import GoldPriceVisualizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UltimatePredictionSystem:
    """终极预测系统"""
    
    def __init__(self, config: dict = None):
        self.config = config or self._get_default_config()
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"[系统] 初始化完成，使用设备: {self.device}")
        
        # 初始化组件
        self.data_collector = GoldDataCollector()
        self.preprocessor = GoldDataPreprocessor()
        self.visualizer = GoldPriceVisualizer()
        
        # 结果存储
        self.results = {}
        
    def _get_default_config(self) -> dict:
        """获取默认配置"""
        return {
            # 数据配置
            'data_period': '2y',  # 2年历史数据
            'sequence_length': 60,  # 序列长度
            'prediction_horizons': [1, 5, 10, 30],  # 预测天数
            
            # 模型配置
            'model_type': 'ensemble',
            'model_config': {
                'use_transformer': True,
                'use_hybrid': True,
                'use_conv': True,
                'd_model': 256,
                'num_heads': 8,
                'transformer_layers': 6,
                'lstm_hidden': 256,
                'lstm_layers': 2,
                'num_filters': 64,
                'dropout': 0.1
            },
            
            # 训练配置
            'epochs': 100,
            'batch_size': 64,
            'learning_rate': 0.001,
            'weight_decay': 1e-5,
            'early_stopping_patience': 15,
            'mixed_precision': True,
            'compile_model': True,
            
            # 输出配置
            'save_model': True,
            'save_predictions': True,
            'create_visualizations': True
        }
    
    def collect_data(self) -> pd.DataFrame:
        """收集数据"""
        logger.info("[数据] 开始收集黄金价格数据...")
        
        try:
            # 获取多源数据
            data = self.data_collector.combine_data_sources(
                use_yahoo=True,
                period=self.config['data_period']
            )
            
            if data.empty:
                raise ValueError("无法获取数据")
            
            logger.info(f"[成功] 获取到 {len(data)} 条数据记录")
            logger.info(f"   时间范围: {data['date'].min()} 到 {data['date'].max()}")
            logger.info(f"   当前价格: ${data['close'].iloc[-1]:.2f}")
            
            # 保存原始数据
            output_path = Path("results/data/ultimate_raw_data.csv")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            data.to_csv(output_path, index=False)
            
            self.results['raw_data'] = data
            return data
            
        except Exception as e:
            logger.error(f"[错误] 数据收集失败: {e}")
            raise
    
    def preprocess_data(self, data: pd.DataFrame) -> tuple:
        """预处理数据"""
        logger.info("[处理] 开始数据预处理...")
        
        try:
            # 特征工程
            processed_data = self.preprocessor.create_features(data)
            
            # 创建序列数据
            sequences, targets = self.preprocessor.create_sequences(
                processed_data, 
                sequence_length=self.config['sequence_length'],
                target_column='close'
            )
            
            # 数据分割
            train_size = int(0.7 * len(sequences))
            val_size = int(0.15 * len(sequences))
            
            X_train = sequences[:train_size]
            y_train = targets[:train_size]
            X_val = sequences[train_size:train_size+val_size]
            y_val = targets[train_size:train_size+val_size]
            X_test = sequences[train_size+val_size:]
            y_test = targets[train_size+val_size:]
            
            logger.info(f"[成功] 数据预处理完成")
            logger.info(f"   训练集: {len(X_train)} 样本")
            logger.info(f"   验证集: {len(X_val)} 样本")
            logger.info(f"   测试集: {len(X_test)} 样本")
            logger.info(f"   特征维度: {X_train.shape[-1]}")
            
            # 保存预处理数据
            self.results['processed_data'] = processed_data
            self.results['train_data'] = (X_train, y_train)
            self.results['val_data'] = (X_val, y_val)
            self.results['test_data'] = (X_test, y_test)
            
            return X_train, y_train, X_val, y_val, X_test, y_test
            
        except Exception as e:
            logger.error(f"[错误] 数据预处理失败: {e}")
            raise
    
    def train_model(self, X_train, y_train, X_val, y_val) -> AdvancedTrainer:
        """训练模型"""
        logger.info("[模型] 开始高级模型训练...")
        
        try:
            # 创建模型
            input_size = X_train.shape[-1]
            model = create_advanced_model(
                input_size=input_size,
                model_type=self.config['model_type'],
                config=self.config['model_config']
            )
            
            logger.info(f"[模型] 创建 {self.config['model_type']} 模型")
            logger.info(f"   参数数量: {sum(p.numel() for p in model.parameters()):,}")
            logger.info(f"   可训练参数: {sum(p.numel() for p in model.parameters() if p.requires_grad):,}")
            
            # 创建训练器
            trainer = AdvancedTrainer(
                model=model,
                device='auto',
                mixed_precision=self.config['mixed_precision'],
                compile_model=self.config['compile_model']
            )
            
            # 训练
            training_results = trainer.train(
                X_train=X_train,
                y_train=y_train,
                X_val=X_val,
                y_val=y_val,
                epochs=self.config['epochs'],
                batch_size=self.config['batch_size'],
                learning_rate=self.config['learning_rate'],
                weight_decay=self.config['weight_decay'],
                early_stopping_patience=self.config['early_stopping_patience']
            )
            
            logger.info(f"[成功] 模型训练完成")
            logger.info(f"   最佳验证损失: {training_results['best_val_loss']:.6f}")
            logger.info(f"   训练轮数: {training_results['total_epochs']}")
            logger.info(f"   训练时间: {training_results['total_time']:.2f}秒")
            
            # 保存模型
            if self.config['save_model']:
                model_path = Path("results/models/ultimate_model.pth")
                model_path.parent.mkdir(parents=True, exist_ok=True)
                trainer.save_model(str(model_path))
            
            self.results['trainer'] = trainer
            self.results['training_results'] = training_results
            
            return trainer
            
        except Exception as e:
            logger.error(f"[错误] 模型训练失败: {e}")
            raise
    
    def evaluate_model(self, trainer: AdvancedTrainer, X_test, y_test) -> dict:
        """评估模型"""
        logger.info("[评估] 开始模型评估...")
        
        try:
            # 评估指标
            metrics = trainer.evaluate(X_test, y_test)
            
            logger.info(f"[成功] 模型评估完成")
            logger.info(f"   RMSE: {metrics['rmse']:.4f}")
            logger.info(f"   MAE: {metrics['mae']:.4f}")
            logger.info(f"   R²: {metrics['r2']:.4f}")
            logger.info(f"   方向准确率: {metrics['direction_accuracy']:.4f}")
            
            self.results['evaluation_metrics'] = metrics
            return metrics
            
        except Exception as e:
            logger.error(f"[错误] 模型评估失败: {e}")
            raise
    
    def make_predictions(self, trainer: AdvancedTrainer, data: pd.DataFrame) -> dict:
        """进行多时间跨度预测"""
        logger.info("[预测] 开始多时间跨度预测...")
        
        try:
            predictions = {}
            current_price = data['close'].iloc[-1]
            
            # 准备最新数据
            processed_data = self.preprocessor.create_features(data)
            latest_sequence = processed_data.iloc[-self.config['sequence_length']:].values
            latest_sequence = latest_sequence.reshape(1, *latest_sequence.shape)
            
            # 多步预测
            for horizon in self.config['prediction_horizons']:
                pred_price = trainer.predict(latest_sequence)[0, 0]
                price_change = pred_price - current_price
                price_change_pct = (price_change / current_price) * 100
                
                predictions[f'{horizon}_day'] = {
                    'horizon_days': horizon,
                    'current_price': float(current_price),
                    'predicted_price': float(pred_price),
                    'price_change': float(price_change),
                    'price_change_pct': float(price_change_pct),
                    'prediction_date': (datetime.now() + timedelta(days=horizon)).isoformat()
                }
                
                logger.info(f"   {horizon}天预测: ${pred_price:.2f} ({price_change_pct:+.2f}%)")
            
            # 保存预测结果
            if self.config['save_predictions']:
                output_path = Path("results/predictions/ultimate_predictions.json")
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                result = {
                    'timestamp': datetime.now().isoformat(),
                    'model_type': self.config['model_type'],
                    'predictions': predictions,
                    'metadata': {
                        'data_points': len(data),
                        'sequence_length': self.config['sequence_length'],
                        'model_config': self.config['model_config']
                    }
                }
                
                with open(output_path, 'w') as f:
                    json.dump(result, f, indent=2)
            
            self.results['predictions'] = predictions
            return predictions
            
        except Exception as e:
            logger.error(f"[错误] 预测失败: {e}")
            raise
    
    def create_visualizations(self, data: pd.DataFrame, predictions: dict) -> list:
        """创建可视化图表"""
        logger.info("[图表] 开始创建可视化...")
        
        try:
            output_files = []
            
            if self.config['create_visualizations']:
                # 1. 价格历史图表
                fig1 = self.visualizer.plot_price_history(data)
                path1 = Path("results/visualizations/ultimate_price_history.html")
                path1.parent.mkdir(parents=True, exist_ok=True)
                fig1.write_html(str(path1))
                output_files.append(str(path1))
                
                # 2. 多时间跨度预测图表
                fig2 = self.visualizer.plot_multi_horizon_predictions(data, predictions)
                path2 = Path("results/visualizations/ultimate_multi_predictions.html")
                fig2.write_html(str(path2))
                output_files.append(str(path2))
                
                # 3. 训练历史图表
                if 'training_results' in self.results:
                    fig3 = self.visualizer.plot_training_history(
                        self.results['training_results']['history']
                    )
                    path3 = Path("results/visualizations/ultimate_training_history.html")
                    fig3.write_html(str(path3))
                    output_files.append(str(path3))
                
                logger.info(f"[成功] 创建了 {len(output_files)} 个可视化文件")
                for file in output_files:
                    logger.info(f"   {file}")
            
            self.results['visualization_files'] = output_files
            return output_files
            
        except Exception as e:
            logger.error(f"[错误] 可视化创建失败: {e}")
            raise
    
    def run_complete_pipeline(self) -> dict:
        """运行完整的预测流程"""
        logger.info("[启动] 开始一键终极预测流程...")
        logger.info("=" * 60)
        
        start_time = datetime.now()
        
        try:
            # 1. 数据收集
            data = self.collect_data()
            
            # 2. 数据预处理
            X_train, y_train, X_val, y_val, X_test, y_test = self.preprocess_data(data)
            
            # 3. 模型训练
            trainer = self.train_model(X_train, y_train, X_val, y_val)
            
            # 4. 模型评估
            metrics = self.evaluate_model(trainer, X_test, y_test)
            
            # 5. 进行预测
            predictions = self.make_predictions(trainer, data)
            
            # 6. 创建可视化
            visualization_files = self.create_visualizations(data, predictions)
            
            # 7. 生成总结报告
            end_time = datetime.now()
            total_time = (end_time - start_time).total_seconds()
            
            summary = {
                'status': 'success',
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'total_time_seconds': total_time,
                'data_points': len(data),
                'model_type': self.config['model_type'],
                'evaluation_metrics': metrics,
                'predictions': predictions,
                'visualization_files': visualization_files,
                'config': self.config
            }
            
            # 保存总结报告
            report_path = Path("results/ultimate_prediction_report.json")
            with open(report_path, 'w') as f:
                json.dump(summary, f, indent=2)
            
            logger.info("=" * 60)
            logger.info("[完成] 一键终极预测流程完成!")
            logger.info(f"   总耗时: {total_time:.2f}秒")
            logger.info(f"   模型性能: RMSE={metrics['rmse']:.4f}, R²={metrics['r2']:.4f}")
            logger.info(f"   预测结果: {len(predictions)} 个时间跨度")
            logger.info(f"   可视化文件: {len(visualization_files)} 个")
            logger.info(f"   报告文件: {report_path}")
            
            return summary
            
        except Exception as e:
            logger.error(f"[错误] 终极预测流程失败: {e}")
            raise


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='一键终极预测系统')
    parser.add_argument('--config', type=str, help='配置文件路径')
    parser.add_argument('--epochs', type=int, default=100, help='训练轮数')
    parser.add_argument('--batch-size', type=int, default=64, help='批次大小')
    parser.add_argument('--learning-rate', type=float, default=0.001, help='学习率')
    
    args = parser.parse_args()
    
    # 加载配置
    config = None
    if args.config and Path(args.config).exists():
        with open(args.config, 'r') as f:
            config = json.load(f)
    
    # 更新配置
    if config is None:
        config = {}
    
    config.update({
        'epochs': args.epochs,
        'batch_size': args.batch_size,
        'learning_rate': args.learning_rate
    })
    
    # 运行预测系统
    system = UltimatePredictionSystem(config)
    results = system.run_complete_pipeline()
    
    print(f"\n[完成] 终极预测系统运行完成!")
    print(f"查看结果: {results.get('visualization_files', [])}")


if __name__ == "__main__":
    main()
