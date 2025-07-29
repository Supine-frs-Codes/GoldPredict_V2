#!/usr/bin/env python3
"""
传统ML预测系统 Ver 2.0
增强版本，包含可视化、模型训练结果展示、历史数据预测验证等功能
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端，避免Tkinter线程问题
import matplotlib.pyplot as plt
import seaborn as sns

# 导入MT5数据源
try:
    from mt5_data_source import get_mt5_data_source
    MT5_AVAILABLE = True
    print("[导入] MT5数据源模块导入成功")
except ImportError as e:
    print(f"[警告] MT5数据源模块导入失败: {e}")
    MT5_AVAILABLE = False
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.svm import SVR
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler, MinMaxScaler
import joblib
import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
import logging
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

logger = logging.getLogger(__name__)

class TraditionalMLSystemV2:
    """传统ML预测系统增强版"""
    
    def __init__(self, config=None):
        """初始化系统"""
        self.config = config or {
            'data_source': 'mt5',
            'time_period': 'H1',
            'model_type': 'random_forest',
            'lookback_days': 30,
            'prediction_horizon': 24,  # 预测未来24小时
            'feature_engineering': True,
            'auto_hyperparameter_tuning': True,
            'cross_validation_folds': 5
        }
        
        self.models = {}
        self.scalers = {}
        self.training_history = []
        self.prediction_history = []
        self.performance_metrics = {}
        self.feature_importance = {}
        self.is_trained = False
        self.last_training_time = None

        # 新增：训练过程监控
        self.training_progress = {
            'current_step': 0,
            'total_steps': 0,
            'current_stage': 'idle',
            'stage_progress': 0,
            'logs': [],
            'metrics_history': [],
            'hyperparameter_search_results': [],
            'cross_validation_scores': [],
            'learning_curves': {}
        }

        # 训练参数详情
        self.training_details = {
            'dataset_info': {},
            'feature_engineering_stats': {},
            'model_parameters': {},
            'optimization_results': {},
            'validation_results': {}
        }
        
        # 模型定义
        self.available_models = {
            'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
            'gradient_boosting': GradientBoostingRegressor(n_estimators=100, random_state=42),
            'linear_regression': LinearRegression(),
            'ridge': Ridge(alpha=1.0),
            'lasso': Lasso(alpha=1.0),
            'svr': SVR(kernel='rbf'),
            'neural_network': MLPRegressor(hidden_layer_sizes=(100, 50), max_iter=500, random_state=42),
            'ensemble': None  # 集成模型
        }
        
        # 创建结果目录
        self.results_dir = Path("results/traditional_ml")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # 可视化设置
        self.visualization_config = {
            'figure_size': (12, 8),
            'dpi': 100,
            'style': 'seaborn-v0_8',
            'color_palette': 'husl'
        }

    def _update_training_progress(self, stage: str, step: int = None, total: int = None, message: str = None):
        """更新训练进度"""
        if stage:
            self.training_progress['current_stage'] = stage
        if step is not None:
            self.training_progress['current_step'] = step
        if total is not None:
            self.training_progress['total_steps'] = total
        if message:
            timestamp = datetime.now().strftime('%H:%M:%S')
            self.training_progress['logs'].append(f"[{timestamp}] {message}")
            # 限制日志数量
            if len(self.training_progress['logs']) > 100:
                self.training_progress['logs'] = self.training_progress['logs'][-100:]

        # 计算阶段进度
        if self.training_progress['total_steps'] > 0:
            self.training_progress['stage_progress'] = (
                self.training_progress['current_step'] / self.training_progress['total_steps'] * 100
            )

    def _log_training_metric(self, metric_name: str, value: float, epoch: int = None):
        """记录训练指标"""
        metric_entry = {
            'timestamp': datetime.now().isoformat(),
            'metric_name': metric_name,
            'value': value,
            'epoch': epoch
        }
        self.training_progress['metrics_history'].append(metric_entry)

    def get_training_progress(self):
        """获取训练进度信息"""
        return {
            'progress': self.training_progress,
            'details': self.training_details,
            'is_training': self.training_progress['current_stage'] not in ['idle', 'completed', 'failed']
        }
        
    def update_config(self, new_config: dict):
        """更新配置"""
        self.config.update(new_config)
        logger.info(f"配置已更新: {new_config}")
        
        # 如果关键配置改变，重置训练状态
        key_params = ['data_source', 'time_period', 'model_type', 'lookback_days']
        if any(param in new_config for param in key_params):
            self.is_trained = False
            logger.info("关键配置已更改，需要重新训练模型")
    
    def collect_data(self):
        """收集训练数据"""
        try:
            # 这里应该从实际数据源收集数据
            # 为了演示，我们生成模拟数据
            # 安全获取配置参数
            data_source = self.config.get('data_source', 'mt5')
            time_period = self.config.get('time_period', 'H1')
            lookback_days = self.config.get('lookback_days', 30)

            logger.info(f"从 {data_source} 收集 {time_period} 数据...")

            # 尝试使用MT5实时数据
            if MT5_AVAILABLE and data_source == 'mt5':
                try:
                    mt5_source = get_mt5_data_source()
                    if mt5_source.connect():
                        # 计算需要的数据点数
                        if time_period == 'H1':
                            count = lookback_days * 24
                        elif time_period == 'H4':
                            count = lookback_days * 6
                        elif time_period == 'D1':
                            count = lookback_days
                        else:
                            count = lookback_days * 24

                        # 获取MT5历史数据
                        df = mt5_source.get_historical_data(time_period, count)

                        if df is not None and len(df) > 0:
                            logger.info(f"MT5成功获取 {len(df)} 条实时数据")

                            # 获取当前实时价格
                            current_price = mt5_source.get_current_price()
                            logger.info(f"MT5当前黄金价格: ${current_price:.2f}")

                            # 重置索引，将时间索引转换为timestamp列
                            df = df.reset_index()
                            if 'time' in df.columns:
                                df.rename(columns={'time': 'timestamp'}, inplace=True)
                            elif df.index.name == 'time':
                                df['timestamp'] = df.index
                            else:
                                df['timestamp'] = df.index

                            # 确保timestamp列是datetime类型
                            df['timestamp'] = pd.to_datetime(df['timestamp'])

                            # 将当前价格添加到数据中
                            current_time = pd.Timestamp.now()
                            new_row = {
                                'timestamp': current_time,
                                'open': current_price,
                                'high': current_price,
                                'low': current_price,
                                'close': current_price,
                                'volume': 1000
                            }
                            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

                            # 保存当前价格供预测使用
                            self.current_price = current_price

                            logger.info(f"MT5数据格式化完成，列: {list(df.columns)}, 数据量: {len(df)}")
                            return df
                        else:
                            logger.warning("MT5数据获取失败，使用模拟数据")
                    else:
                        logger.warning("MT5连接失败，使用模拟数据")
                except Exception as e:
                    logger.error(f"MT5数据获取异常: {e}")

            # 生成模拟的黄金价格数据（更真实的黄金价格模拟）
            logger.info("使用模拟黄金价格数据")
            np.random.seed(42)
            days = lookback_days
            hours_per_day = 24 if time_period == 'H1' else 1
            total_points = days * hours_per_day

            # 黄金价格基础参数（基于真实黄金价格范围）
            base_price = 3350  # 当前黄金价格水平

            # 长期趋势（黄金通常有上涨趋势）
            trend = np.linspace(0, 30, total_points)

            # 市场波动（黄金价格波动性）
            volatility = 15  # 黄金日波动率约1-2%
            noise = np.random.normal(0, volatility, total_points)

            # 季节性和周期性（黄金有一定的季节性）
            seasonal = 25 * np.sin(np.linspace(0, 6*np.pi, total_points))  # 长期周期
            daily_cycle = 8 * np.sin(np.linspace(0, total_points/24*2*np.pi, total_points))  # 日内周期

            # 随机冲击（模拟重大事件影响）
            shocks = np.zeros(total_points)
            shock_points = np.random.choice(total_points, size=max(1, total_points//100), replace=False)
            shocks[shock_points] = np.random.normal(0, 50, len(shock_points))

            # 组合价格
            prices = base_price + trend + seasonal + daily_cycle + noise + shocks

            # 确保价格在合理范围内
            prices = np.clip(prices, base_price * 0.85, base_price * 1.15)
            
            # 创建时间序列
            start_time = datetime.now() - timedelta(days=days)
            if time_period == 'H1':
                time_index = pd.date_range(start=start_time, periods=total_points, freq='H')
            else:
                time_index = pd.date_range(start=start_time, periods=total_points, freq='D')
            
            # 创建DataFrame
            data = pd.DataFrame({
                'timestamp': time_index,
                'open': prices + np.random.normal(0, 2, total_points),
                'high': prices + np.abs(np.random.normal(5, 3, total_points)),
                'low': prices - np.abs(np.random.normal(5, 3, total_points)),
                'close': prices,
                'volume': np.random.randint(1000, 10000, total_points)
            })
            
            logger.info(f"收集到 {len(data)} 条数据记录")
            return data
            
        except Exception as e:
            logger.error(f"数据收集失败: {e}")
            return None
    
    def engineer_features(self, data):
        """特征工程"""
        try:
            logger.info("开始特征工程...")

            df = data.copy()

            # 验证数据结构
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"缺少必要的列: {missing_columns}")
                return data

            # 确保有timestamp列
            if 'timestamp' not in df.columns:
                if df.index.name == 'time' or isinstance(df.index, pd.DatetimeIndex):
                    df['timestamp'] = df.index
                else:
                    # 创建时间戳列
                    df['timestamp'] = pd.date_range(start=datetime.now() - timedelta(hours=len(df)),
                                                  periods=len(df), freq='H')

            # 确保timestamp是datetime类型
            df['timestamp'] = pd.to_datetime(df['timestamp'])

            logger.info(f"数据验证完成，列: {list(df.columns)}, 数据量: {len(df)}")
            
            # 基础技术指标
            df['sma_5'] = df['close'].rolling(window=5).mean()
            df['sma_20'] = df['close'].rolling(window=20).mean()
            df['ema_12'] = df['close'].ewm(span=12).mean()
            df['ema_26'] = df['close'].ewm(span=26).mean()
            
            # MACD
            df['macd'] = df['ema_12'] - df['ema_26']
            df['macd_signal'] = df['macd'].ewm(span=9).mean()
            df['macd_histogram'] = df['macd'] - df['macd_signal']
            
            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # 布林带
            df['bb_middle'] = df['close'].rolling(window=20).mean()
            bb_std = df['close'].rolling(window=20).std()
            df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
            df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
            df['bb_width'] = df['bb_upper'] - df['bb_lower']
            df['bb_position'] = (df['close'] - df['bb_lower']) / df['bb_width']
            
            # 价格变化特征
            df['price_change'] = df['close'].pct_change()
            df['price_change_5'] = df['close'].pct_change(periods=5)
            df['volatility'] = df['price_change'].rolling(window=20).std()
            
            # 成交量特征
            df['volume_sma'] = df['volume'].rolling(window=20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_sma']
            
            # 时间特征
            df['hour'] = df['timestamp'].dt.hour
            df['day_of_week'] = df['timestamp'].dt.dayofweek
            df['month'] = df['timestamp'].dt.month
            
            # 滞后特征
            for lag in [1, 2, 3, 5, 10]:
                df[f'close_lag_{lag}'] = df['close'].shift(lag)
                df[f'volume_lag_{lag}'] = df['volume'].shift(lag)
            
            # 移除包含NaN的行
            df = df.dropna()
            
            logger.info(f"特征工程完成，生成 {len(df.columns)} 个特征")
            return df
            
        except Exception as e:
            logger.error(f"特征工程失败: {e}")
            return data
    
    def prepare_training_data(self, data):
        """准备训练数据"""
        try:
            # 选择特征列（排除时间戳和目标变量）
            feature_cols = [col for col in data.columns 
                          if col not in ['timestamp', 'close']]
            
            X = data[feature_cols].values
            y = data['close'].values
            
            # 数据标准化
            scaler_X = StandardScaler()
            scaler_y = StandardScaler()
            
            X_scaled = scaler_X.fit_transform(X)
            y_scaled = scaler_y.fit_transform(y.reshape(-1, 1)).ravel()
            
            # 保存缩放器
            self.scalers = {
                'X': scaler_X,
                'y': scaler_y,
                'feature_names': feature_cols
            }
            
            # 分割训练和测试数据
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y_scaled, test_size=0.2, random_state=42, shuffle=False
            )
            
            logger.info(f"训练数据准备完成: 训练集 {len(X_train)}, 测试集 {len(X_test)}")
            
            return {
                'X_train': X_train,
                'X_test': X_test,
                'y_train': y_train,
                'y_test': y_test,
                'feature_names': feature_cols
            }
            
        except Exception as e:
            logger.error(f"训练数据准备失败: {e}")
            return None
    
    def train_model(self, training_data):
        """训练模型"""
        try:
            model_type = self.config['model_type']
            logger.info(f"开始训练 {model_type} 模型...")

            # 初始化训练进度
            self._update_training_progress('preparing', 0, 100, f"开始训练 {model_type} 模型")

            X_train = training_data['X_train']
            y_train = training_data['y_train']
            X_test = training_data['X_test']
            y_test = training_data['y_test']

            # 记录数据集信息
            self.training_details['dataset_info'] = {
                'training_samples': len(X_train),
                'test_samples': len(X_test),
                'feature_count': X_train.shape[1],
                'feature_names': training_data['feature_names'],
                'train_test_split': f"{len(X_train)}/{len(X_test)} (80%/20%)"
            }

            self._update_training_progress('data_prepared', 10, 100, f"数据准备完成: 训练集{len(X_train)}样本, 测试集{len(X_test)}样本")
            
            if model_type == 'ensemble':
                # 训练集成模型
                self._update_training_progress('training_ensemble', 20, 100, "开始训练集成模型")
                models = {}
                predictions = {}

                base_models = ['random_forest', 'gradient_boosting', 'ridge']
                for i, base_model in enumerate(base_models):
                    self._update_training_progress('training_ensemble', 20 + i * 15, 100, f"训练 {base_model} 模型")
                    model = self.available_models[base_model]
                    model.fit(X_train, y_train)
                    models[base_model] = model
                    predictions[base_model] = model.predict(X_test)

                    # 记录模型参数
                    self.training_details['model_parameters'][base_model] = self._get_model_params(model)

                # 简单平均集成
                ensemble_pred = np.mean(list(predictions.values()), axis=0)

                self.models = models
                test_pred = ensemble_pred

                self._update_training_progress('ensemble_complete', 65, 100, "集成模型训练完成")

            else:
                # 训练单个模型
                self._update_training_progress('training_model', 20, 100, f"开始训练 {model_type} 模型")
                model = self.available_models[model_type]

                # 超参数调优
                if self.config.get('auto_hyperparameter_tuning', False):
                    self._update_training_progress('hyperparameter_tuning', 25, 100, "开始超参数调优")
                    model = self._tune_hyperparameters(model, X_train, y_train)
                    self._update_training_progress('hyperparameter_complete', 45, 100, "超参数调优完成")

                self._update_training_progress('model_fitting', 50, 100, "开始模型拟合")
                model.fit(X_train, y_train)
                test_pred = model.predict(X_test)

                self.models[model_type] = model

                # 记录模型参数
                self.training_details['model_parameters'][model_type] = self._get_model_params(model)

                self._update_training_progress('model_complete', 65, 100, f"{model_type} 模型训练完成")
            
            # 计算性能指标
            self._update_training_progress('evaluating', 70, 100, "开始模型评估")

            mse = mean_squared_error(y_test, test_pred)
            mae = mean_absolute_error(y_test, test_pred)
            r2 = r2_score(y_test, test_pred)

            # 记录评估指标
            self._log_training_metric('MSE', mse)
            self._log_training_metric('MAE', mae)
            self._log_training_metric('R2', r2)

            # 交叉验证
            self._update_training_progress('cross_validation', 75, 100, "开始交叉验证")

            if model_type != 'ensemble':
                cv_scores = cross_val_score(
                    model, X_train, y_train,
                    cv=self.config.get('cross_validation_folds', 5),
                    scoring='neg_mean_squared_error'
                )
                cv_rmse = np.sqrt(-cv_scores.mean())

                # 记录交叉验证结果
                self.training_progress['cross_validation_scores'] = cv_scores.tolist()
                self.training_details['validation_results'] = {
                    'cv_scores': cv_scores.tolist(),
                    'cv_mean': cv_scores.mean(),
                    'cv_std': cv_scores.std(),
                    'cv_rmse': cv_rmse
                }
            else:
                cv_rmse = np.sqrt(mse)
                self.training_details['validation_results'] = {
                    'ensemble_rmse': cv_rmse,
                    'note': 'Ensemble model validation based on test set'
                }

            # 保存性能指标
            self.performance_metrics = {
                'mse': mse,
                'mae': mae,
                'r2': r2,
                'rmse': np.sqrt(mse),
                'cv_rmse': cv_rmse,
                'training_time': datetime.now().isoformat()
            }

            self._update_training_progress('metrics_calculated', 85, 100, f"性能评估完成 - RMSE: {np.sqrt(mse):.4f}, R²: {r2:.4f}")
            
            # 特征重要性（如果模型支持）
            self._update_training_progress('feature_importance', 90, 100, "计算特征重要性")

            if model_type != 'ensemble':
                if hasattr(model, 'feature_importances_'):
                    self.feature_importance = dict(zip(
                        training_data['feature_names'],
                        model.feature_importances_
                    ))
                    self.training_details['feature_engineering_stats'] = {
                        'total_features': len(training_data['feature_names']),
                        'top_features': sorted(self.feature_importance.items(),
                                             key=lambda x: x[1], reverse=True)[:10]
                    }
            else:
                # 集成模型的特征重要性（平均）
                if all(hasattr(m, 'feature_importances_') for m in self.models.values()):
                    avg_importance = np.mean([m.feature_importances_ for m in self.models.values()], axis=0)
                    self.feature_importance = dict(zip(training_data['feature_names'], avg_importance))
                    self.training_details['feature_engineering_stats'] = {
                        'total_features': len(training_data['feature_names']),
                        'ensemble_avg_importance': True,
                        'top_features': sorted(self.feature_importance.items(),
                                             key=lambda x: x[1], reverse=True)[:10]
                    }

            self.is_trained = True
            self.last_training_time = datetime.now()

            # 完成训练
            self._update_training_progress('completed', 100, 100, f"训练完成 - RMSE: {np.sqrt(mse):.4f}, R²: {r2:.4f}")

            logger.info(f"模型训练完成 - RMSE: {np.sqrt(mse):.4f}, R²: {r2:.4f}")

            # 保存训练历史
            training_record = {
                'timestamp': datetime.now().isoformat(),
                'model_type': model_type,
                'config': self.config.copy(),
                'metrics': self.performance_metrics.copy(),
                'training_details': self.training_details.copy()
            }
            self.training_history.append(training_record)

            return True
            
        except Exception as e:
            logger.error(f"模型训练失败: {e}")
            return False
    
    def _tune_hyperparameters(self, model, X_train, y_train):
        """超参数调优"""
        try:
            logger.info("开始超参数调优...")
            
            param_grids = {
                'random_forest': {
                    'n_estimators': [50, 100, 200],
                    'max_depth': [10, 20, None],
                    'min_samples_split': [2, 5, 10]
                },
                'gradient_boosting': {
                    'n_estimators': [50, 100, 200],
                    'learning_rate': [0.01, 0.1, 0.2],
                    'max_depth': [3, 5, 7]
                },
                'ridge': {
                    'alpha': [0.1, 1.0, 10.0, 100.0]
                },
                'svr': {
                    'C': [0.1, 1, 10],
                    'gamma': ['scale', 'auto', 0.001, 0.01]
                }
            }
            
            model_name = type(model).__name__.lower()
            for key in param_grids:
                if key in model_name:
                    param_grid = param_grids[key]
                    break
            else:
                return model
            
            grid_search = GridSearchCV(
                model, param_grid, cv=3, scoring='neg_mean_squared_error',
                n_jobs=-1, verbose=0
            )
            
            grid_search.fit(X_train, y_train)
            logger.info(f"最佳参数: {grid_search.best_params_}")
            
            return grid_search.best_estimator_

        except Exception as e:
            logger.error(f"超参数调优失败: {e}")
            return model

    def _get_model_params(self, model):
        """获取模型参数"""
        try:
            params = model.get_params()
            # 过滤掉不可序列化的参数
            serializable_params = {}
            for key, value in params.items():
                try:
                    json.dumps(value)  # 测试是否可序列化
                    serializable_params[key] = value
                except (TypeError, ValueError):
                    serializable_params[key] = str(value)
            return serializable_params
        except Exception as e:
            logger.error(f"获取模型参数失败: {e}")
            return {}

    def make_prediction(self, future_hours=None):
        """进行预测"""
        try:
            if not self.is_trained:
                return {'success': False, 'message': '模型尚未训练'}

            future_hours = future_hours or self.config.get('prediction_horizon', 24)

            # 收集最新数据进行预测
            latest_data = self.collect_data()
            if latest_data is None:
                return {'success': False, 'message': '无法获取最新数据'}

            # 特征工程
            if self.config.get('feature_engineering', True):
                latest_data = self.engineer_features(latest_data)

            # 准备预测数据
            feature_cols = self.scalers['feature_names']
            X_latest = latest_data[feature_cols].iloc[-1:].values
            X_scaled = self.scalers['X'].transform(X_latest)

            # 进行预测
            model_type = self.config['model_type']

            if model_type == 'ensemble':
                predictions = []
                for model_name, model in self.models.items():
                    pred_scaled = model.predict(X_scaled)
                    predictions.append(pred_scaled[0])

                final_pred_scaled = np.mean(predictions)
            else:
                model = self.models[model_type]
                pred_scaled = model.predict(X_scaled)
                final_pred_scaled = pred_scaled[0]

            # 反标准化
            final_pred = self.scalers['y'].inverse_transform([[final_pred_scaled]])[0][0]

            # 获取当前价格 - 优先使用MT5实时价格
            if MT5_AVAILABLE and hasattr(self, 'current_price'):
                current_price = self.current_price
                logger.info(f"使用缓存的MT5实时价格: ${current_price:.2f}")
            elif MT5_AVAILABLE:
                try:
                    mt5_source = get_mt5_data_source()
                    if mt5_source.connect():
                        current_price = mt5_source.get_current_price()
                        self.current_price = current_price
                        logger.info(f"获取MT5实时价格: ${current_price:.2f}")
                    else:
                        current_price = latest_data['close'].iloc[-1]
                        logger.info(f"MT5连接失败，使用历史价格: ${current_price:.2f}")
                except Exception as e:
                    current_price = latest_data['close'].iloc[-1]
                    logger.error(f"MT5价格获取失败: {e}，使用历史价格: ${current_price:.2f}")
            else:
                current_price = latest_data['close'].iloc[-1]
                logger.info(f"使用历史数据价格: ${current_price:.2f}")

            # 计算信号（黄金价格预测专用）
            price_change = final_pred - current_price
            price_change_pct = (price_change / current_price) * 100

            # 黄金价格信号判断逻辑
            if price_change_pct > 2:
                signal = '强烈看涨'
            elif price_change_pct > 1:
                signal = '看涨'
            elif price_change_pct > 0.2:
                signal = '轻微看涨'
            elif price_change_pct > -0.2:
                signal = '横盘'
            elif price_change_pct > -1:
                signal = '轻微看跌'
            elif price_change_pct > -2:
                signal = '看跌'
            else:
                signal = '强烈看跌'

            # 计算置信度（基于模型性能）
            r2 = self.performance_metrics.get('r2', 0.5)
            confidence = max(0.5, min(0.95, r2))

            prediction_result = {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'current_price': float(current_price),
                'predicted_price': float(final_pred),
                'price_change': float(price_change),
                'price_change_pct': float(price_change_pct),
                'signal': signal,
                'confidence': float(confidence),
                'model_type': model_type,
                'prediction_horizon_hours': future_hours,
                'performance_metrics': self.performance_metrics
            }

            # 保存预测历史
            self.prediction_history.append(prediction_result)

            logger.info(f"预测完成: {current_price:.2f} → {final_pred:.2f} ({signal})")

            return prediction_result

        except Exception as e:
            logger.error(f"预测失败: {e}")
            return {'success': False, 'message': str(e)}

    def validate_predictions(self, validation_days=7):
        """验证预测准确性"""
        try:
            logger.info(f"开始验证最近 {validation_days} 天的预测准确性...")

            # 获取历史数据
            historical_data = self.collect_data()
            if historical_data is None:
                return {'success': False, 'message': '无法获取历史数据'}

            # 模拟历史预测
            validation_results = []
            data_points = len(historical_data)
            validation_points = min(validation_days * 24, data_points // 2)

            for i in range(validation_points):
                try:
                    # 使用历史数据的前部分训练，预测后部分
                    train_end = data_points - validation_points + i
                    train_data = historical_data.iloc[:train_end]
                    actual_price = historical_data.iloc[train_end]['close']

                    # 简化的预测（使用当前模型）
                    if self.config.get('feature_engineering', True):
                        train_data = self.engineer_features(train_data)

                    if len(train_data) > 0:
                        feature_cols = self.scalers['feature_names']
                        X_val = train_data[feature_cols].iloc[-1:].values
                        X_scaled = self.scalers['X'].transform(X_val)

                        model_type = self.config['model_type']
                        if model_type == 'ensemble':
                            predictions = []
                            for model in self.models.values():
                                pred_scaled = model.predict(X_scaled)
                                predictions.append(pred_scaled[0])
                            pred_scaled = np.mean(predictions)
                        else:
                            model = self.models[model_type]
                            pred_scaled = model.predict(X_scaled)[0]

                        predicted_price = self.scalers['y'].inverse_transform([[pred_scaled]])[0][0]

                        error = abs(predicted_price - actual_price)
                        error_pct = (error / actual_price) * 100

                        validation_results.append({
                            'timestamp': historical_data.iloc[train_end]['timestamp'],
                            'actual_price': actual_price,
                            'predicted_price': predicted_price,
                            'error': error,
                            'error_pct': error_pct
                        })

                except Exception as e:
                    continue

            if not validation_results:
                return {'success': False, 'message': '验证数据不足'}

            # 计算验证指标
            errors = [r['error'] for r in validation_results]
            error_pcts = [r['error_pct'] for r in validation_results]

            validation_metrics = {
                'total_predictions': len(validation_results),
                'mean_absolute_error': np.mean(errors),
                'mean_absolute_error_pct': np.mean(error_pcts),
                'median_absolute_error': np.median(errors),
                'max_error': np.max(errors),
                'min_error': np.min(errors),
                'accuracy_within_1pct': sum(1 for e in error_pcts if e <= 1.0) / len(error_pcts),
                'accuracy_within_2pct': sum(1 for e in error_pcts if e <= 2.0) / len(error_pcts),
                'accuracy_within_5pct': sum(1 for e in error_pcts if e <= 5.0) / len(error_pcts)
            }

            logger.info(f"验证完成 - 平均误差: {validation_metrics['mean_absolute_error_pct']:.2f}%")

            return {
                'success': True,
                'validation_metrics': validation_metrics,
                'validation_results': validation_results[-50:]  # 返回最近50个结果
            }

        except Exception as e:
            logger.error(f"预测验证失败: {e}")
            return {'success': False, 'message': str(e)}

    def generate_visualizations(self):
        """生成可视化图表"""
        try:
            logger.info("生成可视化图表...")

            # 设置绘图样式
            plt.style.use('default')
            sns.set_palette(self.visualization_config['color_palette'])

            visualizations = {}

            # 1. 模型性能对比图
            if self.training_history:
                fig, ax = plt.subplots(figsize=self.visualization_config['figure_size'])

                models = [h['model_type'] for h in self.training_history[-10:]]
                rmse_scores = [h['metrics']['rmse'] for h in self.training_history[-10:]]
                r2_scores = [h['metrics']['r2'] for h in self.training_history[-10:]]

                x = np.arange(len(models))
                width = 0.35

                ax.bar(x - width/2, rmse_scores, width, label='RMSE', alpha=0.8)
                ax2 = ax.twinx()
                ax2.bar(x + width/2, r2_scores, width, label='R²', alpha=0.8, color='orange')

                ax.set_xlabel('模型训练历史')
                ax.set_ylabel('RMSE')
                ax2.set_ylabel('R² Score')
                ax.set_title('模型性能对比')
                ax.set_xticks(x)
                ax.set_xticklabels(models, rotation=45)
                ax.legend(loc='upper left')
                ax2.legend(loc='upper right')

                plt.tight_layout()
                performance_path = self.results_dir / 'model_performance.png'
                plt.savefig(performance_path, dpi=self.visualization_config['dpi'])
                plt.close()

                visualizations['model_performance'] = str(performance_path)

            # 2. 特征重要性图
            if self.feature_importance:
                fig, ax = plt.subplots(figsize=self.visualization_config['figure_size'])

                # 选择前15个最重要的特征
                sorted_features = sorted(self.feature_importance.items(),
                                       key=lambda x: x[1], reverse=True)[:15]

                features, importance = zip(*sorted_features)

                y_pos = np.arange(len(features))
                ax.barh(y_pos, importance, alpha=0.8)
                ax.set_yticks(y_pos)
                ax.set_yticklabels(features)
                ax.set_xlabel('重要性')
                ax.set_title('特征重要性排序')
                ax.grid(axis='x', alpha=0.3)

                plt.tight_layout()
                importance_path = self.results_dir / 'feature_importance.png'
                plt.savefig(importance_path, dpi=self.visualization_config['dpi'])
                plt.close()

                visualizations['feature_importance'] = str(importance_path)

            # 3. 预测结果时间序列图
            if self.prediction_history:
                fig, ax = plt.subplots(figsize=self.visualization_config['figure_size'])

                recent_predictions = self.prediction_history[-50:]
                timestamps = [datetime.fromisoformat(p['timestamp']) for p in recent_predictions]
                current_prices = [p['current_price'] for p in recent_predictions]
                predicted_prices = [p['predicted_price'] for p in recent_predictions]

                ax.plot(timestamps, current_prices, label='实际价格', linewidth=2)
                ax.plot(timestamps, predicted_prices, label='预测价格', linewidth=2, linestyle='--')

                ax.set_xlabel('时间')
                ax.set_ylabel('价格 ($)')
                ax.set_title('预测结果时间序列')
                ax.legend()
                ax.grid(True, alpha=0.3)

                # 旋转x轴标签
                plt.xticks(rotation=45)
                plt.tight_layout()

                prediction_path = self.results_dir / 'prediction_timeline.png'
                plt.savefig(prediction_path, dpi=self.visualization_config['dpi'])
                plt.close()

                visualizations['prediction_timeline'] = str(prediction_path)

            logger.info(f"生成了 {len(visualizations)} 个可视化图表")
            return visualizations

        except Exception as e:
            logger.error(f"可视化生成失败: {e}")
            return {}

    def get_status(self):
        """获取系统状态"""
        return {
            'running': True,
            'is_trained': self.is_trained,
            'last_training_time': self.last_training_time.isoformat() if self.last_training_time else None,
            'config': self.config,
            'performance_metrics': self.performance_metrics,
            'training_history_count': len(self.training_history),
            'prediction_history_count': len(self.prediction_history),
            'available_models': list(self.available_models.keys()),
            'current_model': self.config['model_type']
        }

    def save_model(self, filepath=None):
        """保存模型"""
        try:
            if not self.is_trained:
                return False

            filepath = filepath or self.results_dir / f"model_{self.config['model_type']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.joblib"

            model_data = {
                'models': self.models,
                'scalers': self.scalers,
                'config': self.config,
                'performance_metrics': self.performance_metrics,
                'feature_importance': self.feature_importance,
                'training_time': self.last_training_time.isoformat() if self.last_training_time else None
            }

            joblib.dump(model_data, filepath)
            logger.info(f"模型已保存到: {filepath}")
            return True

        except Exception as e:
            logger.error(f"模型保存失败: {e}")
            return False

    def load_model(self, filepath):
        """加载模型"""
        try:
            model_data = joblib.load(filepath)

            self.models = model_data['models']
            self.scalers = model_data['scalers']
            self.config.update(model_data['config'])
            self.performance_metrics = model_data['performance_metrics']
            self.feature_importance = model_data.get('feature_importance', {})

            if model_data.get('training_time'):
                self.last_training_time = datetime.fromisoformat(model_data['training_time'])

            self.is_trained = True
            logger.info(f"模型已从 {filepath} 加载")
            return True

        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            return False

    def run_full_pipeline(self):
        """运行完整的训练和预测流程"""
        try:
            # 检查是否正在训练，避免重复执行
            if self.training_progress['current_stage'] not in ['idle', 'completed', 'failed']:
                logger.warning("训练正在进行中，跳过重复执行")
                return {'success': False, 'message': '训练正在进行中，请等待完成'}

            # 设置训练状态
            self.training_progress['current_stage'] = 'preparing'
            self.training_progress['stage_progress'] = 0

            logger.info("开始运行完整的ML流程...")

            # 1. 收集数据
            data = self.collect_data()
            if data is None:
                self.training_progress['current_stage'] = 'failed'
                return {'success': False, 'message': '数据收集失败'}

            # 2. 特征工程
            if self.config.get('feature_engineering', True):
                data = self.engineer_features(data)

            # 3. 准备训练数据
            training_data = self.prepare_training_data(data)
            if training_data is None:
                return {'success': False, 'message': '训练数据准备失败'}

            # 4. 训练模型
            if not self.train_model(training_data):
                return {'success': False, 'message': '模型训练失败'}

            # 5. 进行预测
            prediction = self.make_prediction()
            if not prediction['success']:
                return {'success': False, 'message': '预测失败'}

            # 6. 验证预测
            validation = self.validate_predictions()

            # 7. 生成可视化
            visualizations = self.generate_visualizations()

            # 8. 保存模型
            self.save_model()

            # 设置训练完成状态
            self.training_progress['current_stage'] = 'completed'
            self.training_progress['stage_progress'] = 100

            return {
                'success': True,
                'message': '完整流程执行成功',
                'prediction': prediction,
                'validation': validation,
                'visualizations': visualizations,
                'performance_metrics': self.performance_metrics
            }

        except Exception as e:
            logger.error(f"完整流程执行失败: {e}")
            self.training_progress['current_stage'] = 'failed'
            return {'success': False, 'message': str(e)}
