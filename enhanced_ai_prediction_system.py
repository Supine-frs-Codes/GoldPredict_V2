#!/usr/bin/env python3
"""
增强AI预测系统
集成可选的高级功能模块，保持核心系统简洁
"""

import sys
import os
import importlib
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
import warnings
warnings.filterwarnings('ignore')

# 添加模块路径
sys.path.append(str(Path(__file__).parent / "modules"))

from adaptive_prediction_engine import AdaptivePredictionEngine
from improved_mt5_manager import ImprovedMT5Manager

# 尝试导入torch用于设备检测
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

logger = logging.getLogger(__name__)


class EnhancedAIPredictionSystem:
    """增强AI预测系统"""
    
    def __init__(self, config: Dict = None):
        self.config = config or self._get_default_config()

        # 核心引擎将在后面初始化
        self.core_engine = None

        self.optional_modules = {}
        self.enabled_features = set()
        self.module_status = {}
        self.system_running = False

        # 性能指标跟踪
        self.performance_metrics = {
            'total_predictions': 0,
            'correct_predictions': 0,
            'accuracy_rate': 0.0,
            'average_confidence': 0.0,
            'model_contributions': {},
            'prediction_history': [],
            'accuracy_history': []
        }

        # 可选模块配置
        self.available_modules = {
            'advanced_technical': {
                'module': 'advanced_technical_indicators',
                'class': 'AdvancedTechnicalIndicators',
                'description': '高级技术指标分析'
            },
            'deep_learning': {
                'module': 'deep_learning_models',
                'class': 'DeepLearningEnsemble',
                'description': '深度学习模型集成'
            },
            'gpu_acceleration': {
                'module': 'gpu_accelerated_computing',
                'class': 'GPUAcceleratedComputing',
                'description': 'GPU加速计算'
            },
            'sentiment_analysis': {
                'module': 'market_sentiment_analysis',
                'class': 'MarketSentimentAnalyzer',
                'description': '市场情绪分析'
            }
        }
        
        print(f"[增强AI] 增强AI预测系统初始化")
        print(f"   可用模块: {len(self.available_modules)}个")
        
        # 初始化核心引擎
        self._initialize_core_engine()
        
        # 根据配置启用可选模块
        self._initialize_optional_modules()
    
    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            'core': {
                'interval_minutes': 5,
                'data_collection_seconds': 5,
                'min_data_points': 10,
                'auto_optimize': True
            },
            'optional_features': {
                'advanced_technical': True,
                'deep_learning': False,  # 默认关闭，需要额外依赖
                'gpu_acceleration': False,  # 默认关闭，需要GPU
                'sentiment_analysis': False  # 默认关闭，需要网络API
            },
            'feature_weights': {
                'core_prediction': 0.5,
                'advanced_technical': 0.2,
                'deep_learning': 0.2,
                'sentiment_analysis': 0.1
            }
        }
    
    def _initialize_core_engine(self):
        """初始化核心预测引擎"""
        try:
            self.core_engine = AdaptivePredictionEngine(self.config['core'])
            print(f"[核心] 核心预测引擎初始化成功")
        except Exception as e:
            logger.error(f"核心引擎初始化失败: {e}")
            raise
    
    def _initialize_optional_modules(self):
        """初始化可选模块"""
        enabled_features = self.config.get('optional_features', {})
        
        for feature_name, enabled in enabled_features.items():
            if enabled and feature_name in self.available_modules:
                success = self._load_optional_module(feature_name)
                if success:
                    self.enabled_features.add(feature_name)
                    print(f"[模块] {self.available_modules[feature_name]['description']} 已启用")
                else:
                    print(f"[警告] {feature_name} 模块加载失败，将跳过")
        
        print(f"[增强AI] 已启用 {len(self.enabled_features)} 个可选模块")
    
    def _load_optional_module(self, feature_name: str) -> bool:
        """加载可选模块"""
        try:
            module_info = self.available_modules[feature_name]
            module_name = module_info['module']
            class_name = module_info['class']
            
            # 动态导入模块
            module = importlib.import_module(module_name)
            module_class = getattr(module, class_name)
            
            # 创建实例
            if feature_name == 'deep_learning':
                # 自动选择设备：优先GPU，否则CPU
                if TORCH_AVAILABLE:
                    device = 'cuda' if torch.cuda.is_available() else 'cpu'
                    instance = module_class(device=device)
                else:
                    instance = module_class(device='cpu')
            else:
                instance = module_class()
            
            self.optional_modules[feature_name] = instance
            return True
            
        except ImportError as e:
            # 根据模块类型提供更友好的错误信息
            missing_deps = self._get_missing_dependencies(feature_name, str(e))
            if missing_deps:
                logger.info(f"模块 {feature_name} 需要额外依赖: {missing_deps}")
                print(f"[信息] {feature_name} 模块需要额外依赖: {missing_deps}")
            else:
                logger.warning(f"模块 {feature_name} 导入失败: {e}")
                print(f"[警告] {feature_name} 模块加载失败，将跳过")
            return False
        except Exception as e:
            logger.error(f"模块 {feature_name} 加载失败: {e}")
            return False

    def _get_missing_dependencies(self, feature_name: str, error_msg: str) -> str:
        """根据错误信息获取缺失的依赖"""
        dependency_map = {
            'deep_learning': {
                'torch': 'PyTorch (uv add torch)',
                'transformers': 'Transformers (uv add transformers)',
                'stable_baselines3': 'Stable Baselines3 (uv add stable-baselines3)'
            },
            'sentiment_analysis': {
                'textblob': 'TextBlob (已安装)',
                'vaderSentiment': 'VADER Sentiment (uv add vaderSentiment)',
                'requests': 'Requests (uv add requests)'
            },
            'gpu_acceleration': {
                'torch': 'PyTorch with CUDA (uv add torch)',
                'cupy': 'CuPy (uv add cupy-cuda11x)',
                'numba': 'Numba (uv add numba)'
            }
        }

        if feature_name in dependency_map:
            for dep, install_cmd in dependency_map[feature_name].items():
                if dep in error_msg:
                    return install_cmd

        return ""
    
    def start(self) -> bool:
        """启动系统（统一接口）"""
        return self.start_system()

    def start_system(self) -> bool:
        """启动增强预测系统"""
        try:
            print(f"[启动] 启动增强AI预测系统...")

            # 启动核心引擎
            if self.core_engine is None:
                print(f"[错误] 核心引擎未初始化")
                return False

            if not self.core_engine.start_engine():
                print(f"[错误] 核心引擎启动失败")
                return False
            
            # 初始化可选模块
            self._initialize_optional_modules_data()

            # 设置系统运行状态
            self.system_running = True

            print(f"[成功] 增强AI预测系统启动成功")
            return True
            
        except Exception as e:
            logger.error(f"系统启动失败: {e}")
            return False
    
    def stop_system(self):
        """停止增强预测系统"""
        try:
            print(f"[停止] 停止增强AI预测系统...")
            
            # 停止核心引擎
            if self.core_engine:
                self.core_engine.stop_engine()
            
            # 清理可选模块
            self._cleanup_optional_modules()

            # 设置系统停止状态
            self.system_running = False

            print(f"[停止] 增强AI预测系统已停止")
            
        except Exception as e:
            logger.error(f"系统停止失败: {e}")
    
    def _initialize_optional_modules_data(self):
        """初始化可选模块数据"""
        try:
            # 为深度学习模块准备训练数据
            if 'deep_learning' in self.enabled_features:
                self._prepare_deep_learning_data()
            
        except Exception as e:
            logger.error(f"可选模块数据初始化失败: {e}")
    
    def _prepare_deep_learning_data(self):
        """为深度学习模块准备数据"""
        try:
            if len(self.core_engine.price_history) >= 100:
                # 转换价格历史为DataFrame
                df = pd.DataFrame(self.core_engine.price_history)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                # 训练深度学习模型
                dl_module = self.optional_modules['deep_learning']
                train_result = dl_module.train_models(df, epochs=20, batch_size=16)
                
                if train_result['success']:
                    print(f"[深度学习] 模型训练完成")
                else:
                    print(f"[深度学习] 模型训练失败: {train_result['message']}")
            
        except Exception as e:
            logger.error(f"深度学习数据准备失败: {e}")
    
    def _cleanup_optional_modules(self):
        """清理可选模块"""
        try:
            for feature_name, module in self.optional_modules.items():
                if hasattr(module, 'cleanup'):
                    module.cleanup()
                elif hasattr(module, 'optimize_memory_usage'):
                    module.optimize_memory_usage()
            
            self.optional_modules.clear()
            self.enabled_features.clear()
            
        except Exception as e:
            logger.error(f"可选模块清理失败: {e}")
    
    def make_enhanced_prediction(self) -> Dict:
        """执行增强预测"""
        try:
            # 获取核心预测
            core_prediction = self.core_engine.get_latest_prediction()
            if not core_prediction:
                return {'success': False, 'message': '核心预测不可用'}

            # 调试：打印核心预测数据
            print(f"[调试] 核心预测数据: {core_prediction}")

            # 提取核心预测数据，处理不同的字段名
            predicted_price = core_prediction.get('predicted_price') or core_prediction.get('price', 0)
            confidence = core_prediction.get('confidence', 0.5)
            signal = core_prediction.get('signal', 'neutral')
            current_price = core_prediction.get('current_price', 0)

            print(f"[调试] 提取的数据: price={predicted_price}, confidence={confidence}, signal={signal}, current={current_price}")

            # 收集所有预测结果
            predictions = {
                'core': {
                    'price': predicted_price,
                    'confidence': confidence,
                    'signal': signal
                }
            }
            
            # 获取可选模块预测
            optional_predictions = self._get_optional_predictions()
            predictions.update(optional_predictions)
            
            # 集成所有预测
            final_prediction = self._integrate_predictions(predictions)

            # 更新性能指标
            self._update_performance_metrics(final_prediction, current_price)

            print(f"[调试] 最终返回数据: current_price={current_price}, predicted_price={final_prediction.get('price')}, signal={final_prediction.get('signal')}, confidence={final_prediction.get('confidence')}")

            return {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'current_price': current_price,
                'final_prediction': final_prediction,
                'individual_predictions': predictions,
                'enabled_features': list(self.enabled_features),
                'confidence': final_prediction['confidence']
            }
            
        except Exception as e:
            logger.error(f"增强预测失败: {e}")
            return {'success': False, 'message': str(e)}
    
    def _get_optional_predictions(self) -> Dict:
        """获取可选模块预测"""
        optional_predictions = {}
        
        try:
            # 准备数据
            if not self.core_engine.price_history:
                return optional_predictions
            
            df = pd.DataFrame(self.core_engine.price_history)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # 高级技术指标预测
            if 'advanced_technical' in self.enabled_features:
                tech_prediction = self._get_technical_prediction(df)
                if tech_prediction:
                    optional_predictions['advanced_technical'] = tech_prediction
            
            # 深度学习预测
            if 'deep_learning' in self.enabled_features:
                dl_prediction = self._get_deep_learning_prediction(df)
                if dl_prediction:
                    optional_predictions['deep_learning'] = dl_prediction
            
            # 情绪分析预测
            if 'sentiment_analysis' in self.enabled_features:
                sentiment_prediction = self._get_sentiment_prediction()
                if sentiment_prediction:
                    optional_predictions['sentiment_analysis'] = sentiment_prediction
            
        except Exception as e:
            logger.error(f"可选预测获取失败: {e}")
        
        return optional_predictions
    
    def _get_technical_prediction(self, df: pd.DataFrame) -> Optional[Dict]:
        """获取技术指标预测"""
        try:
            tech_module = self.optional_modules['advanced_technical']
            indicators = tech_module.calculate_all_indicators(df)
            signal = tech_module.get_prediction_signal(indicators)
            
            # 基于技术指标生成价格预测
            current_price = df['price'].iloc[-1]
            signal_strength = signal['strength']
            
            if signal['signal'] == 'bullish':
                predicted_price = current_price * (1 + signal_strength * 0.01)
            elif signal['signal'] == 'bearish':
                predicted_price = current_price * (1 - signal_strength * 0.01)
            else:
                predicted_price = current_price
            
            return {
                'price': predicted_price,
                'confidence': signal['confidence'],
                'signal': signal['signal'],
                'details': signal['details']
            }
            
        except Exception as e:
            logger.error(f"技术指标预测失败: {e}")
            return None
    
    def _get_deep_learning_prediction(self, df: pd.DataFrame) -> Optional[Dict]:
        """获取深度学习预测"""
        try:
            dl_module = self.optional_modules['deep_learning']
            
            if not dl_module.is_trained:
                return None
            
            prediction_result = dl_module.predict(df)
            
            if prediction_result['success']:
                return {
                    'price': prediction_result['ensemble_prediction'],
                    'confidence': prediction_result['confidence'],
                    'signal': 'bullish' if prediction_result['ensemble_prediction'] > df['price'].iloc[-1] else 'bearish',
                    'details': {
                        'individual_models': prediction_result['individual_predictions'],
                        'anomaly_score': prediction_result['anomaly_score']
                    }
                }
            
        except Exception as e:
            logger.error(f"深度学习预测失败: {e}")
        
        return None
    
    def _get_sentiment_prediction(self) -> Optional[Dict]:
        """获取情绪分析预测"""
        try:
            sentiment_module = self.optional_modules['sentiment_analysis']
            sentiment_result = sentiment_module.analyze_comprehensive_sentiment()
            signal = sentiment_module.get_sentiment_prediction_signal(sentiment_result)
            
            return {
                'price': None,  # 情绪分析不直接预测价格
                'confidence': signal['confidence'],
                'signal': signal['signal'],
                'details': {
                    'sentiment_score': signal['strength'],
                    'sentiment_details': signal['details']
                }
            }
            
        except Exception as e:
            logger.error(f"情绪分析预测失败: {e}")
        
        return None
    
    def _integrate_predictions(self, predictions: Dict) -> Dict:
        """集成所有预测结果"""
        try:
            weights = self.config.get('feature_weights', {})
            
            # 收集价格预测
            price_predictions = []
            confidence_scores = []
            signal_votes = {'bullish': 0, 'bearish': 0, 'neutral': 0}
            
            for pred_name, pred_data in predictions.items():
                if pred_data and isinstance(pred_data, dict):
                    weight = weights.get(pred_name, 0.1)
                    
                    # 价格预测
                    if pred_data.get('price') is not None:
                        price_predictions.append({
                            'price': pred_data['price'],
                            'weight': weight,
                            'confidence': pred_data.get('confidence', 0.5)
                        })
                    
                    # 置信度
                    confidence_scores.append(pred_data.get('confidence', 0.5) * weight)
                    
                    # 信号投票（添加中文信号映射）
                    signal = pred_data.get('signal', 'neutral')

                    # 将中文信号映射为英文信号
                    signal_mapping = {
                        '看涨': 'bullish',
                        '轻微看涨': 'bullish',
                        '强烈看涨': 'bullish',
                        '看跌': 'bearish',
                        '轻微看跌': 'bearish',
                        '强烈看跌': 'bearish',
                        '中性': 'neutral',
                        '横盘': 'neutral',
                        'bullish': 'bullish',
                        'bearish': 'bearish',
                        'neutral': 'neutral'
                    }

                    mapped_signal = signal_mapping.get(signal, 'neutral')
                    signal_votes[mapped_signal] += weight
            
            # 计算加权平均价格
            if price_predictions:
                total_weight = sum(p['weight'] * p['confidence'] for p in price_predictions)
                if total_weight > 0:
                    weighted_price = sum(p['price'] * p['weight'] * p['confidence'] for p in price_predictions) / total_weight
                else:
                    weighted_price = predictions.get('core', {}).get('price', 0)
            else:
                weighted_price = predictions.get('core', {}).get('price', 0)

            print(f"[调试] 价格预测列表: {price_predictions}")
            print(f"[调试] 最终加权价格: {weighted_price}")
            
            # 计算综合置信度
            total_confidence = sum(confidence_scores) if confidence_scores else 0.5
            
            # 确定最终信号
            final_signal_en = max(signal_votes, key=signal_votes.get)

            # 将英文信号转换回中文信号
            signal_reverse_mapping = {
                'bullish': '看涨',
                'bearish': '看跌',
                'neutral': '中性'
            }

            final_signal = signal_reverse_mapping.get(final_signal_en, '中性')

            return {
                'price': weighted_price,
                'confidence': min(total_confidence, 0.95),
                'signal': final_signal,
                'signal_votes': signal_votes,
                'contributing_models': len([p for p in predictions.values() if p])
            }
            
        except Exception as e:
            logger.error(f"预测集成失败: {e}")
            # 返回核心预测作为备选
            core = predictions.get('core', {})
            return {
                'price': core.get('price', 0),
                'confidence': core.get('confidence', 0.5),
                'signal': core.get('signal', 'neutral'),
                'signal_votes': {'neutral': 1},
                'contributing_models': 1
            }

    def _update_performance_metrics(self, prediction: Dict, current_price: float):
        """更新性能指标"""
        try:
            # 增加预测总数
            self.performance_metrics['total_predictions'] += 1

            # 保存预测历史
            prediction_record = {
                'timestamp': datetime.now().isoformat(),
                'predicted_price': prediction['price'],
                'current_price': current_price,
                'confidence': prediction['confidence'],
                'signal': prediction['signal'],
                'contributing_models': prediction.get('contributing_models', 1)
            }

            self.performance_metrics['prediction_history'].append(prediction_record)

            # 限制历史记录数量
            if len(self.performance_metrics['prediction_history']) > 100:
                self.performance_metrics['prediction_history'].pop(0)

            # 验证之前的预测（如果有足够的历史数据）
            self._verify_past_predictions(current_price)

            # 更新平均置信度
            recent_predictions = self.performance_metrics['prediction_history'][-10:]
            if recent_predictions:
                avg_confidence = sum(p['confidence'] for p in recent_predictions) / len(recent_predictions)
                self.performance_metrics['average_confidence'] = avg_confidence

            # 更新模型贡献统计
            contributing_models = prediction.get('contributing_models', 1)
            if 'model_contributions' not in self.performance_metrics:
                self.performance_metrics['model_contributions'] = {}

            for model_name in ['core', 'advanced_technical', 'deep_learning', 'sentiment_analysis']:
                if model_name not in self.performance_metrics['model_contributions']:
                    self.performance_metrics['model_contributions'][model_name] = 0
                if model_name in prediction.get('signal_votes', {}):
                    self.performance_metrics['model_contributions'][model_name] += 1

        except Exception as e:
            logger.error(f"性能指标更新失败: {e}")

    def _verify_past_predictions(self, current_price: float):
        """验证过去的预测"""
        try:
            current_time = datetime.now()
            correct_predictions = 0
            total_verifiable = 0

            for prediction in self.performance_metrics['prediction_history']:
                pred_time = datetime.fromisoformat(prediction['timestamp'])
                time_diff = (current_time - pred_time).total_seconds() / 60  # 分钟

                # 验证5分钟前的预测
                if 4 <= time_diff <= 6:
                    total_verifiable += 1
                    predicted_price = prediction['predicted_price']
                    actual_price = current_price

                    # 计算预测准确性（允许1%的误差）
                    error_rate = abs(predicted_price - actual_price) / actual_price
                    if error_rate <= 0.01:  # 1%误差内认为正确
                        correct_predictions += 1

            # 更新准确率
            if total_verifiable > 0:
                accuracy = correct_predictions / total_verifiable
                self.performance_metrics['accuracy_rate'] = accuracy
                self.performance_metrics['correct_predictions'] = correct_predictions

                # 更新准确率历史
                self.performance_metrics['accuracy_history'].append({
                    'timestamp': datetime.now().isoformat(),
                    'accuracy': accuracy,
                    'sample_size': total_verifiable
                })

                # 限制准确率历史数量
                if len(self.performance_metrics['accuracy_history']) > 50:
                    self.performance_metrics['accuracy_history'].pop(0)

        except Exception as e:
            logger.error(f"预测验证失败: {e}")

    def get_system_status(self) -> Dict:
        """获取系统状态"""
        try:
            core_status = self.core_engine.get_status() if self.core_engine else {}
            
            # 可选模块状态
            module_status = {}
            for feature_name in self.enabled_features:
                if feature_name in self.optional_modules:
                    module = self.optional_modules[feature_name]
                    if hasattr(module, 'get_status'):
                        module_status[feature_name] = module.get_status()
                    elif hasattr(module, 'get_model_info'):
                        module_status[feature_name] = module.get_model_info()
                    else:
                        module_status[feature_name] = {'status': 'active'}
            
            return {
                'core_engine': core_status,
                'enabled_features': list(self.enabled_features),
                'available_modules': list(self.available_modules.keys()),
                'module_status': module_status,
                'system_running': core_status.get('running', False),
                'performance_metrics': self.performance_metrics
            }
            
        except Exception as e:
            logger.error(f"状态获取失败: {e}")
            return {'error': str(e)}
    
    def update_configuration(self, new_config: Dict) -> bool:
        """更新系统配置"""
        try:
            # 更新配置
            self.config.update(new_config)
            
            # 更新核心引擎配置
            if 'core' in new_config and self.core_engine:
                self.core_engine.update_config(new_config['core'])
            
            # 重新初始化可选模块（如果特性配置改变）
            if 'optional_features' in new_config:
                self._cleanup_optional_modules()
                self._initialize_optional_modules()
            
            print(f"[配置] 系统配置已更新")
            return True
            
        except Exception as e:
            logger.error(f"配置更新失败: {e}")
            return False


def main():
    """测试函数"""
    print("增强AI预测系统测试")
    print("=" * 40)
    
    # 创建配置
    config = {
        'core': {
            'interval_minutes': 1,
            'data_collection_seconds': 2,
            'min_data_points': 5
        },
        'optional_features': {
            'advanced_technical': True,
            'deep_learning': False,  # 需要PyTorch
            'gpu_acceleration': False,  # 需要CUDA
            'sentiment_analysis': False  # 需要网络API
        }
    }
    
    # 创建增强AI系统
    ai_system = EnhancedAIPredictionSystem(config)
    
    try:
        # 启动系统
        if ai_system.start_system():
            print("✅ 增强AI系统启动成功")
            
            # 等待数据收集
            import time
            print("⏱️ 等待数据收集...")
            time.sleep(15)
            
            # 执行增强预测
            print("🔮 执行增强预测...")
            prediction = ai_system.make_enhanced_prediction()
            
            if prediction['success']:
                print("✅ 增强预测成功")
                final = prediction['final_prediction']
                print(f"   当前价格: ${prediction['current_price']:.2f}")
                print(f"   预测价格: ${final['price']:.2f}")
                print(f"   信号: {final['signal']}")
                print(f"   置信度: {final['confidence']:.2f}")
                print(f"   贡献模型: {final['contributing_models']}个")
                
                # 显示各模型预测
                print(f"\n📊 各模型预测:")
                for name, pred in prediction['individual_predictions'].items():
                    if pred and pred.get('price'):
                        print(f"   {name}: ${pred['price']:.2f} ({pred['signal']})")
            else:
                print(f"❌ 增强预测失败: {prediction['message']}")
            
            # 获取系统状态
            status = ai_system.get_system_status()
            print(f"\n📊 系统状态:")
            print(f"   核心引擎运行: {status['core_engine'].get('running', False)}")
            print(f"   启用功能: {status['enabled_features']}")
            
            ai_system.stop_system()
        else:
            print("❌ 增强AI系统启动失败")
        
        print("\n✅ 增强AI预测系统测试完成!")
        
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断")
        ai_system.stop_system()
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        ai_system.stop_system()


if __name__ == "__main__":
    main()
