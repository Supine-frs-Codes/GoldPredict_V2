#!/usr/bin/env python3
"""
多核处理预测系统
支持配置化的数据源、时间跨度和处理器核心数
"""

import multiprocessing as mp
import concurrent.futures
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging
import json
import argparse
import time
from pathlib import Path
import os
import psutil

from src.data.data_collector import GoldDataCollector
from src.data.multi_source_collector import MultiSourceCollector
from improved_prediction_system import ImprovedPredictionSystem

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MulticorePredictionSystem:
    """多核预测系统"""
    
    def __init__(self, config):
        self.config = config
        self.cpu_cores = self._get_cpu_cores()
        self.data_collector = GoldDataCollector()
        
        print(f"[系统] 多核预测系统初始化")
        print(f"   数据源: {config['data_source']}")
        print(f"   时间跨度: {config['time_period']}")
        print(f"   CPU核心: {self.cpu_cores}")
        print(f"   预测模式: {config['prediction_mode']}")
    
    def _get_cpu_cores(self):
        """获取CPU核心数配置"""
        total_cores = mp.cpu_count()
        
        if self.config['cpu_cores'] == 'auto':
            # 自动模式：使用总核心数的75%
            return max(1, int(total_cores * 0.75))
        elif self.config['cpu_cores'] == 'single':
            return 1
        elif self.config['cpu_cores'] == 'half':
            return max(1, total_cores // 2)
        elif self.config['cpu_cores'] == 'max':
            return total_cores
        else:
            return max(1, int(total_cores * 0.75))
    
    def get_data(self):
        """根据配置获取数据"""
        print(f"[数据] 使用 {self.config['data_source']} 数据源获取数据...")
        
        try:
            if self.config['data_source'] == 'mt5':
                # 使用MT5数据源
                data = self.data_collector.get_multi_source_data(
                    period=self.config['time_period'], 
                    preferred_source='mt5'
                )
            elif self.config['data_source'] == 'multi_source':
                # 使用多数据源
                data = self.data_collector.get_multi_source_data(
                    period=self.config['time_period']
                )
            elif self.config['data_source'] == 'yahoo':
                # 使用Yahoo Finance
                data = self.data_collector.combine_data_sources(
                    use_yahoo=True, 
                    use_multi_source=False,
                    period=self.config['time_period']
                )
            elif self.config['data_source'] == 'alpha_vantage':
                # 使用Alpha Vantage
                data = self.data_collector.combine_data_sources(
                    use_yahoo=False,
                    use_alpha_vantage=True,
                    use_multi_source=False,
                    period=self.config['time_period']
                )
            else:
                # 默认使用多数据源
                data = self.data_collector.combine_data_sources(
                    period=self.config['time_period']
                )
            
            if data.empty:
                raise ValueError("无法获取数据")
            
            print(f"[成功] 获取到 {len(data)} 条数据记录")
            return data
            
        except Exception as e:
            logger.error(f"数据获取失败: {e}")
            raise
    
    def parallel_prediction_task(self, args):
        """并行预测任务"""
        task_id, data_chunk, horizon, method = args

        try:
            # 确保数据包含必要的技术指标
            data_processed = self._preprocess_data(data_chunk.copy())

            # 为每个任务创建独立的预测器
            predictor = ImprovedPredictionSystem()

            if method == 'simple':
                predictions = predictor.simple_prediction(data_processed, [horizon])
            elif method == 'enhanced':
                simple_pred = predictor.simple_prediction(data_processed, [horizon])
                predictions = predictor.enhanced_prediction(data_processed, simple_pred)
            else:
                # 默认使用简单预测
                predictions = predictor.simple_prediction(data_processed, [horizon])

            return {
                'task_id': task_id,
                'horizon': horizon,
                'method': method,
                'predictions': predictions,
                'success': True
            }

        except Exception as e:
            return {
                'task_id': task_id,
                'horizon': horizon,
                'method': method,
                'error': str(e),
                'success': False
            }

    def _preprocess_data(self, data):
        """预处理数据，添加必要的技术指标"""
        try:
            # 确保基础列存在
            if 'close' not in data.columns:
                raise ValueError("数据缺少 'close' 列")

            # 计算技术指标
            data['returns'] = data['close'].pct_change()
            data['volatility'] = data['returns'].rolling(20).std()

            # 移动平均线
            data['ma_5'] = data['close'].rolling(5).mean()
            data['ma_10'] = data['close'].rolling(10).mean()
            data['ma_20'] = data['close'].rolling(20).mean()
            data['ma_50'] = data['close'].rolling(50).mean()

            # 填充NaN值
            data = data.fillna(method='bfill').fillna(method='ffill')

            return data

        except Exception as e:
            logger.error(f"数据预处理失败: {e}")
            raise
    
    def run_multicore_prediction(self):
        """运行多核预测"""
        start_time = time.time()
        
        print(f"[启动] 多核预测系统")
        print("=" * 50)
        
        # 1. 获取数据
        data = self.get_data()
        
        # 2. 准备预测任务
        horizons = [1, 5, 10, 30]  # 预测时间跨度
        methods = []
        
        if self.config['prediction_mode'] == 'simple':
            methods = ['simple']
        elif self.config['prediction_mode'] == 'advanced':
            methods = ['simple', 'enhanced']
        elif self.config['prediction_mode'] == 'ultimate':
            methods = ['simple', 'enhanced']
        
        # 3. 创建任务列表
        tasks = []
        task_id = 0
        
        for method in methods:
            for horizon in horizons:
                tasks.append((task_id, data, horizon, method))
                task_id += 1
        
        print(f"[任务] 创建了 {len(tasks)} 个预测任务")
        print(f"[处理] 使用 {self.cpu_cores} 个CPU核心并行处理")
        
        # 4. 并行执行预测
        results = []
        
        with concurrent.futures.ProcessPoolExecutor(max_workers=self.cpu_cores) as executor:
            # 提交所有任务
            future_to_task = {
                executor.submit(self.parallel_prediction_task, task): task 
                for task in tasks
            }
            
            # 收集结果
            completed = 0
            for future in concurrent.futures.as_completed(future_to_task):
                result = future.result()
                results.append(result)
                completed += 1
                
                if result['success']:
                    print(f"[完成] 任务 {result['task_id']}: {result['method']} - {result['horizon']}天 ✅")
                else:
                    print(f"[失败] 任务 {result['task_id']}: {result['error']} ❌")
                
                # 显示进度
                progress = (completed / len(tasks)) * 100
                print(f"[进度] {progress:.1f}% ({completed}/{len(tasks)})")
        
        # 5. 整理结果
        successful_results = [r for r in results if r['success']]
        failed_results = [r for r in results if not r['success']]
        
        print(f"\n[结果] 成功: {len(successful_results)}, 失败: {len(failed_results)}")
        
        # 6. 生成最终预测报告
        final_predictions = self._generate_final_report(successful_results, data)
        
        # 7. 保存结果
        self._save_results(final_predictions, data, start_time)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print("=" * 50)
        print(f"[完成] 多核预测系统运行完成!")
        print(f"   总耗时: {total_time:.2f}秒")
        print(f"   平均每任务: {total_time/len(tasks):.2f}秒")
        print(f"   CPU利用率: {self.cpu_cores}核心")
        print(f"   加速比: {len(tasks)/total_time:.2f}x")
        
        return final_predictions
    
    def _generate_final_report(self, results, data):
        """生成最终预测报告"""
        print(f"\n[报告] 生成最终预测报告...")
        
        current_price = data['close'].iloc[-1]
        final_predictions = {}
        
        # 按时间跨度和方法组织结果
        for result in results:
            horizon = result['horizon']
            method = result['method']
            predictions = result['predictions']
            
            key = f"{horizon}_day"
            if key not in final_predictions:
                final_predictions[key] = {
                    'horizon_days': horizon,
                    'current_price': float(current_price),
                    'methods': {}
                }
            
            final_predictions[key]['methods'][method] = predictions.get(key, {})
        
        # 计算综合预测
        for key, pred_data in final_predictions.items():
            methods = pred_data['methods']
            
            if 'enhanced' in methods and methods['enhanced']:
                # 优先使用增强预测
                best_pred = methods['enhanced']
            elif 'simple' in methods and methods['simple']:
                # 使用简单预测
                best_pred = methods['simple']
            else:
                continue
            
            # 添加综合预测结果
            pred_data['final_prediction'] = {
                'predicted_price': best_pred.get('predicted_price', current_price),
                'price_change_pct': best_pred.get('price_change_pct', 0),
                'confidence_lower': best_pred.get('confidence_lower', current_price * 0.95),
                'confidence_upper': best_pred.get('confidence_upper', current_price * 1.05),
                'trend_signal': best_pred.get('trend_signal', '横盘整理')
            }
            
            # 显示结果
            horizon = pred_data['horizon_days']
            final_pred = pred_data['final_prediction']
            print(f"   {horizon}天: ${final_pred['predicted_price']:.2f} "
                  f"({final_pred['price_change_pct']:+.2f}%) - {final_pred['trend_signal']}")
        
        return final_predictions
    
    def _save_results(self, predictions, data, start_time):
        """保存预测结果"""
        result = {
            'timestamp': datetime.now().isoformat(),
            'model_type': 'multicore_prediction_system',
            'config': self.config,
            'system_info': {
                'cpu_cores_used': self.cpu_cores,
                'total_cpu_cores': mp.cpu_count(),
                'memory_usage_gb': psutil.virtual_memory().used / (1024**3),
                'execution_time_seconds': time.time() - start_time
            },
            'data_summary': {
                'total_points': len(data),
                'current_price': float(data['close'].iloc[-1]),
                'data_source': self.config['data_source'],
                'time_period': self.config['time_period']
            },
            'predictions': predictions
        }
        
        output_path = Path("results/predictions/multicore_predictions.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"   结果已保存: {output_path}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='多核预测系统')
    parser.add_argument('--data-source', type=str, default='mt5', 
                       choices=['mt5', 'multi_source', 'yahoo', 'alpha_vantage'],
                       help='数据源选择')
    parser.add_argument('--period', type=str, default='3mo',
                       choices=['1d', '1w', '1mo', '3mo', '6mo', '1y'],
                       help='时间跨度')
    parser.add_argument('--cpu-cores', type=str, default='auto',
                       choices=['auto', 'single', 'half', 'max'],
                       help='CPU核心配置')
    parser.add_argument('--mode', type=str, default='simple',
                       choices=['simple', 'advanced', 'ultimate'],
                       help='预测模式')
    
    args = parser.parse_args()
    
    config = {
        'data_source': args.data_source,
        'time_period': args.period,
        'cpu_cores': args.cpu_cores,
        'prediction_mode': args.mode
    }
    
    print(f"[预测] 多核预测系统")
    print("=" * 40)
    
    try:
        system = MulticorePredictionSystem(config)
        predictions = system.run_multicore_prediction()
        
        print("\n[完成] 预测完成!")
        
    except Exception as e:
        print(f"[错误] 执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
