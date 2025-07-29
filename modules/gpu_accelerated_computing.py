#!/usr/bin/env python3
"""
GPU加速计算模块
提供CUDA加速的并行计算功能
"""

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset
import cupy as cp
from numba import cuda, jit
from typing import Dict, List, Optional, Tuple, Union
import logging
import time
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class GPUAcceleratedComputing:
    """GPU加速计算管理器"""
    
    def __init__(self):
        self.device = self._detect_best_device()
        self.cuda_available = torch.cuda.is_available()
        self.cupy_available = self._check_cupy()
        self.memory_pool = None
        
        if self.cuda_available:
            self._initialize_gpu()
        
        print(f"[GPU加速] 初始化完成")
        print(f"   设备: {self.device}")
        print(f"   CUDA可用: {self.cuda_available}")
        print(f"   CuPy可用: {self.cupy_available}")
    
    def _detect_best_device(self) -> str:
        """检测最佳计算设备"""
        if torch.cuda.is_available():
            # 检测GPU型号和性能
            gpu_count = torch.cuda.device_count()
            best_device = 'cuda:0'
            
            for i in range(gpu_count):
                gpu_name = torch.cuda.get_device_name(i)
                gpu_memory = torch.cuda.get_device_properties(i).total_memory
                
                print(f"[GPU {i}] {gpu_name}, 内存: {gpu_memory // 1024**3}GB")
                
                # RTX 50系列优先
                if 'RTX 50' in gpu_name or 'RTX 5' in gpu_name:
                    best_device = f'cuda:{i}'
                    break
            
            return best_device
        else:
            return 'cpu'
    
    def _check_cupy(self) -> bool:
        """检查CuPy可用性"""
        try:
            import cupy
            return True
        except ImportError:
            return False
    
    def _initialize_gpu(self):
        """初始化GPU设置"""
        try:
            # 设置GPU内存管理
            torch.cuda.empty_cache()
            
            # 启用混合精度训练
            if hasattr(torch.cuda, 'amp'):
                self.use_amp = True
            else:
                self.use_amp = False
            
            # 初始化CuPy内存池
            if self.cupy_available:
                self.memory_pool = cp.get_default_memory_pool()
                self.memory_pool.set_limit(size=2**30)  # 1GB限制
            
            print(f"[GPU] 初始化成功，混合精度: {self.use_amp}")
            
        except Exception as e:
            logger.error(f"GPU初始化失败: {e}")
    
    def accelerated_technical_analysis(self, prices: np.ndarray, volumes: np.ndarray = None) -> Dict:
        """GPU加速技术分析计算"""
        try:
            if self.cupy_available and len(prices) > 1000:
                return self._cupy_technical_analysis(prices, volumes)
            else:
                return self._torch_technical_analysis(prices, volumes)
                
        except Exception as e:
            logger.error(f"GPU技术分析失败: {e}")
            return self._cpu_fallback_analysis(prices, volumes)
    
    def _cupy_technical_analysis(self, prices: np.ndarray, volumes: np.ndarray = None) -> Dict:
        """使用CuPy进行技术分析"""
        try:
            # 转换为CuPy数组
            prices_gpu = cp.asarray(prices)
            
            results = {}
            
            # 移动平均线
            results['sma_5'] = self._gpu_sma(prices_gpu, 5)
            results['sma_20'] = self._gpu_sma(prices_gpu, 20)
            results['sma_50'] = self._gpu_sma(prices_gpu, 50)
            
            # 指数移动平均
            results['ema_12'] = self._gpu_ema(prices_gpu, 12)
            results['ema_26'] = self._gpu_ema(prices_gpu, 26)
            
            # MACD
            results['macd'] = self._gpu_macd(prices_gpu)
            
            # RSI
            results['rsi'] = self._gpu_rsi(prices_gpu)
            
            # 布林带
            results['bollinger'] = self._gpu_bollinger_bands(prices_gpu)
            
            # 波动率
            results['volatility'] = self._gpu_volatility(prices_gpu)
            
            # 如果有成交量数据
            if volumes is not None:
                volumes_gpu = cp.asarray(volumes)
                results['volume_sma'] = self._gpu_sma(volumes_gpu, 20)
                results['obv'] = self._gpu_obv(prices_gpu, volumes_gpu)
            
            # 转换回CPU
            for key, value in results.items():
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        if hasattr(sub_value, 'get'):
                            results[key][sub_key] = float(cp.asnumpy(sub_value))
                else:
                    if hasattr(value, 'get'):
                        results[key] = float(cp.asnumpy(value))
            
            return results
            
        except Exception as e:
            logger.error(f"CuPy技术分析失败: {e}")
            return self._torch_technical_analysis(prices, volumes)
    
    def _gpu_sma(self, prices: cp.ndarray, period: int) -> cp.ndarray:
        """GPU加速简单移动平均"""
        if len(prices) < period:
            return prices[-1] if len(prices) > 0 else cp.array([0])
        
        # 使用卷积计算移动平均
        kernel = cp.ones(period) / period
        sma = cp.convolve(prices, kernel, mode='valid')
        return sma[-1] if len(sma) > 0 else prices[-1]
    
    def _gpu_ema(self, prices: cp.ndarray, period: int) -> cp.ndarray:
        """GPU加速指数移动平均"""
        if len(prices) < 2:
            return prices[-1] if len(prices) > 0 else cp.array([0])
        
        alpha = 2.0 / (period + 1)
        ema = cp.zeros_like(prices)
        ema[0] = prices[0]
        
        for i in range(1, len(prices)):
            ema[i] = alpha * prices[i] + (1 - alpha) * ema[i-1]
        
        return ema[-1]
    
    def _gpu_macd(self, prices: cp.ndarray) -> Dict:
        """GPU加速MACD计算"""
        if len(prices) < 26:
            return {'macd': 0, 'signal': 0, 'histogram': 0}
        
        ema_12 = self._gpu_ema(prices, 12)
        ema_26 = self._gpu_ema(prices, 26)
        macd_line = ema_12 - ema_26
        
        # 信号线（MACD的9日EMA）
        macd_array = cp.array([macd_line])
        signal_line = self._gpu_ema(macd_array, 9)
        histogram = macd_line - signal_line
        
        return {
            'macd': float(cp.asnumpy(macd_line)),
            'signal': float(cp.asnumpy(signal_line)),
            'histogram': float(cp.asnumpy(histogram))
        }
    
    def _gpu_rsi(self, prices: cp.ndarray, period: int = 14) -> cp.ndarray:
        """GPU加速RSI计算"""
        if len(prices) < period + 1:
            return cp.array([50])
        
        # 计算价格变化
        deltas = cp.diff(prices)
        gains = cp.where(deltas > 0, deltas, 0)
        losses = cp.where(deltas < 0, -deltas, 0)
        
        # 计算平均收益和损失
        avg_gain = cp.mean(gains[-period:])
        avg_loss = cp.mean(losses[-period:])
        
        if avg_loss == 0:
            return cp.array([100])
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _gpu_bollinger_bands(self, prices: cp.ndarray, period: int = 20, std_dev: float = 2) -> Dict:
        """GPU加速布林带计算"""
        if len(prices) < period:
            current_price = prices[-1] if len(prices) > 0 else 0
            return {
                'upper': float(cp.asnumpy(current_price * 1.01)),
                'middle': float(cp.asnumpy(current_price)),
                'lower': float(cp.asnumpy(current_price * 0.99))
            }
        
        # 计算移动平均和标准差
        sma = self._gpu_sma(prices, period)
        recent_prices = prices[-period:]
        std = cp.std(recent_prices)
        
        upper = sma + (std_dev * std)
        lower = sma - (std_dev * std)
        
        return {
            'upper': float(cp.asnumpy(upper)),
            'middle': float(cp.asnumpy(sma)),
            'lower': float(cp.asnumpy(lower))
        }
    
    def _gpu_volatility(self, prices: cp.ndarray, period: int = 20) -> cp.ndarray:
        """GPU加速波动率计算"""
        if len(prices) < 2:
            return cp.array([0])
        
        # 计算对数收益率
        log_returns = cp.diff(cp.log(prices))
        
        # 计算滚动标准差
        if len(log_returns) >= period:
            volatility = cp.std(log_returns[-period:]) * cp.sqrt(252)  # 年化波动率
        else:
            volatility = cp.std(log_returns) * cp.sqrt(252)
        
        return volatility
    
    def _gpu_obv(self, prices: cp.ndarray, volumes: cp.ndarray) -> cp.ndarray:
        """GPU加速OBV计算"""
        if len(prices) < 2 or len(volumes) < 2:
            return cp.array([0])
        
        price_changes = cp.diff(prices)
        obv = cp.zeros(len(volumes))
        
        for i in range(1, len(volumes)):
            if price_changes[i-1] > 0:
                obv[i] = obv[i-1] + volumes[i]
            elif price_changes[i-1] < 0:
                obv[i] = obv[i-1] - volumes[i]
            else:
                obv[i] = obv[i-1]
        
        return obv[-1]
    
    def _torch_technical_analysis(self, prices: np.ndarray, volumes: np.ndarray = None) -> Dict:
        """使用PyTorch进行技术分析"""
        try:
            # 转换为PyTorch张量
            prices_tensor = torch.FloatTensor(prices).to(self.device)
            
            results = {}
            
            # 移动平均线
            results['sma_5'] = self._torch_sma(prices_tensor, 5)
            results['sma_20'] = self._torch_sma(prices_tensor, 20)
            
            # 简化的技术指标
            if len(prices) >= 2:
                returns = torch.diff(prices_tensor)
                results['volatility'] = float(torch.std(returns).cpu())
                results['momentum'] = float((prices_tensor[-1] - prices_tensor[-min(10, len(prices_tensor))]).cpu())
            
            # 转换回CPU
            for key, value in results.items():
                if torch.is_tensor(value):
                    results[key] = float(value.cpu())
            
            return results
            
        except Exception as e:
            logger.error(f"PyTorch技术分析失败: {e}")
            return self._cpu_fallback_analysis(prices, volumes)
    
    def _torch_sma(self, prices: torch.Tensor, period: int) -> torch.Tensor:
        """PyTorch简单移动平均"""
        if len(prices) < period:
            return prices[-1] if len(prices) > 0 else torch.tensor(0.0)
        
        return torch.mean(prices[-period:])
    
    def _cpu_fallback_analysis(self, prices: np.ndarray, volumes: np.ndarray = None) -> Dict:
        """CPU备用技术分析"""
        results = {}
        
        if len(prices) >= 5:
            results['sma_5'] = np.mean(prices[-5:])
        if len(prices) >= 20:
            results['sma_20'] = np.mean(prices[-20:])
        
        if len(prices) >= 2:
            returns = np.diff(prices)
            results['volatility'] = np.std(returns)
            results['momentum'] = prices[-1] - prices[-min(10, len(prices))]
        
        return results
    
    def batch_prediction(self, models: List[nn.Module], data_batches: List[torch.Tensor]) -> List[torch.Tensor]:
        """批量预测处理"""
        try:
            if not self.cuda_available:
                return self._cpu_batch_prediction(models, data_batches)
            
            results = []
            
            # 使用混合精度训练
            if self.use_amp:
                with torch.cuda.amp.autocast():
                    for model, batch in zip(models, data_batches):
                        model.eval()
                        with torch.no_grad():
                            batch_gpu = batch.to(self.device)
                            prediction = model(batch_gpu)
                            results.append(prediction.cpu())
            else:
                for model, batch in zip(models, data_batches):
                    model.eval()
                    with torch.no_grad():
                        batch_gpu = batch.to(self.device)
                        prediction = model(batch_gpu)
                        results.append(prediction.cpu())
            
            return results
            
        except Exception as e:
            logger.error(f"批量预测失败: {e}")
            return self._cpu_batch_prediction(models, data_batches)
    
    def _cpu_batch_prediction(self, models: List[nn.Module], data_batches: List[torch.Tensor]) -> List[torch.Tensor]:
        """CPU批量预测"""
        results = []
        
        for model, batch in zip(models, data_batches):
            model.eval()
            with torch.no_grad():
                prediction = model(batch)
                results.append(prediction)
        
        return results
    
    def parallel_feature_extraction(self, data: np.ndarray, feature_functions: List) -> Dict:
        """并行特征提取"""
        try:
            if self.cupy_available and len(data) > 1000:
                return self._gpu_feature_extraction(data, feature_functions)
            else:
                return self._cpu_feature_extraction(data, feature_functions)
                
        except Exception as e:
            logger.error(f"并行特征提取失败: {e}")
            return self._cpu_feature_extraction(data, feature_functions)
    
    def _gpu_feature_extraction(self, data: np.ndarray, feature_functions: List) -> Dict:
        """GPU并行特征提取"""
        data_gpu = cp.asarray(data)
        features = {}
        
        # 并行计算多个特征
        for i, func in enumerate(feature_functions):
            try:
                feature_name = f"feature_{i}"
                features[feature_name] = cp.asnumpy(func(data_gpu))
            except Exception as e:
                logger.error(f"特征 {i} 计算失败: {e}")
                features[f"feature_{i}"] = 0
        
        return features
    
    def _cpu_feature_extraction(self, data: np.ndarray, feature_functions: List) -> Dict:
        """CPU特征提取"""
        features = {}
        
        for i, func in enumerate(feature_functions):
            try:
                feature_name = f"feature_{i}"
                features[feature_name] = func(data)
            except Exception as e:
                logger.error(f"特征 {i} 计算失败: {e}")
                features[f"feature_{i}"] = 0
        
        return features
    
    def optimize_memory_usage(self):
        """优化内存使用"""
        try:
            if self.cuda_available:
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
            
            if self.cupy_available and self.memory_pool:
                self.memory_pool.free_all_blocks()
            
            print("[GPU] 内存优化完成")
            
        except Exception as e:
            logger.error(f"内存优化失败: {e}")
    
    def get_gpu_info(self) -> Dict:
        """获取GPU信息"""
        info = {
            'cuda_available': self.cuda_available,
            'cupy_available': self.cupy_available,
            'device': self.device,
            'use_amp': getattr(self, 'use_amp', False)
        }
        
        if self.cuda_available:
            info['gpu_count'] = torch.cuda.device_count()
            info['current_device'] = torch.cuda.current_device()
            
            for i in range(torch.cuda.device_count()):
                props = torch.cuda.get_device_properties(i)
                info[f'gpu_{i}'] = {
                    'name': props.name,
                    'total_memory': props.total_memory // 1024**3,  # GB
                    'major': props.major,
                    'minor': props.minor
                }
        
        return info
    
    def benchmark_performance(self, data_size: int = 10000) -> Dict:
        """性能基准测试"""
        print(f"[基准测试] 开始性能测试，数据大小: {data_size}")
        
        # 生成测试数据
        test_data = np.random.randn(data_size).astype(np.float32)
        
        results = {}
        
        # CPU基准测试
        start_time = time.time()
        cpu_result = self._cpu_fallback_analysis(test_data)
        cpu_time = time.time() - start_time
        results['cpu_time'] = cpu_time
        
        # GPU基准测试
        if self.cuda_available:
            start_time = time.time()
            gpu_result = self.accelerated_technical_analysis(test_data)
            gpu_time = time.time() - start_time
            results['gpu_time'] = gpu_time
            results['speedup'] = cpu_time / gpu_time if gpu_time > 0 else 1.0
        
        print(f"[基准测试] 完成")
        print(f"   CPU时间: {results['cpu_time']:.4f}s")
        if 'gpu_time' in results:
            print(f"   GPU时间: {results['gpu_time']:.4f}s")
            print(f"   加速比: {results['speedup']:.2f}x")
        
        return results


def main():
    """测试函数"""
    print("GPU加速计算模块测试")
    print("=" * 40)
    
    # 创建GPU计算管理器
    gpu_compute = GPUAcceleratedComputing()
    
    try:
        # 显示GPU信息
        info = gpu_compute.get_gpu_info()
        print(f"✅ GPU信息:")
        for key, value in info.items():
            print(f"   {key}: {value}")
        
        # 性能基准测试
        print(f"\n🚀 性能基准测试...")
        benchmark = gpu_compute.benchmark_performance(data_size=50000)
        
        # 测试技术分析加速
        print(f"\n📊 测试GPU加速技术分析...")
        test_prices = np.random.randn(10000) * 10 + 3400
        test_volumes = np.random.randint(1000, 5000, 10000)
        
        start_time = time.time()
        analysis_result = gpu_compute.accelerated_technical_analysis(test_prices, test_volumes)
        analysis_time = time.time() - start_time
        
        print(f"✅ 技术分析完成，耗时: {analysis_time:.4f}s")
        print(f"   计算指标数量: {len(analysis_result)}")
        
        # 显示部分结果
        for key, value in list(analysis_result.items())[:5]:
            print(f"   {key}: {value}")
        
        # 内存优化
        print(f"\n🧹 内存优化...")
        gpu_compute.optimize_memory_usage()
        
        print("\n✅ GPU加速计算测试完成!")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")


if __name__ == "__main__":
    main()
