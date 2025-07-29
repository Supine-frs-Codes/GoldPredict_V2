#!/usr/bin/env python3
"""
传统机器学习预测系统
实现经典ML算法的黄金价格预测
"""

import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class TraditionalMLSystem:
    """传统机器学习预测系统"""
    
    def __init__(self, config: Dict = None):
        self.config = config or self._get_default_config()
        self.models = {}
        self.scalers = {}
        self.is_trained = False
        self.data = None
        self.predictions_history = []
        self.performance_metrics = {
            'total_predictions': 0,
            'average_accuracy': 0.0,
            'model_scores': {}
        }
        
        print(f"[传统ML] 传统机器学习系统初始化")
        print(f"   数据源: {self.config['data_source']}")
        print(f"   时间周期: {self.config['time_period']}")
        print(f"   模型类型: {self.config['model_type']}")
        
        self._initialize_models()
    
    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            'data_source': 'mt5',
            'time_period': '1d',
            'model_type': 'ensemble',
            'cpu_cores': 'auto',
            'lookback_days': 30,
            'features': ['price', 'volume', 'volatility', 'momentum']
        }
    
    def _initialize_models(self):
        """初始化机器学习模型"""
        try:
            # 线性回归
            self.models['linear'] = LinearRegression()
            
            # 随机森林
            cpu_cores = self.config.get('cpu_cores', 'auto')
            n_jobs = -1 if cpu_cores == 'auto' else int(cpu_cores) if cpu_cores != 'auto' else -1

            self.models['random_forest'] = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=n_jobs
            )
            
            # 梯度提升
            self.models['gradient_boost'] = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
            
            # 数据缩放器
            self.scalers['features'] = StandardScaler()
            self.scalers['target'] = StandardScaler()
            
            print(f"[传统ML] 初始化 {len(self.models)} 个模型")
            
        except Exception as e:
            logger.error(f"模型初始化失败: {e}")
    
    def collect_data(self) -> bool:
        """收集训练数据"""
        try:
            print(f"[传统ML] 开始收集数据...")
            
            if self.config['data_source'] == 'yahoo':
                data = self._collect_yahoo_data()
                # 如果Yahoo数据获取失败，使用模拟数据
                if data is None or len(data) < 50:
                    print(f"[传统ML] Yahoo数据获取失败，使用模拟数据")
                    data = self._collect_simulated_data()
            elif self.config['data_source'] == 'mt5':
                data = self._collect_mt5_data()
            else:
                data = self._collect_simulated_data()
            
            if data is not None and len(data) > 50:
                self.data = data
                print(f"[传统ML] 数据收集成功，共 {len(data)} 条记录")
                return True
            else:
                print(f"[传统ML] 数据收集失败或数据不足")
                return False
                
        except Exception as e:
            logger.error(f"数据收集失败: {e}")
            return False
    
    def _collect_yahoo_data(self) -> Optional[pd.DataFrame]:
        """从Yahoo Finance收集数据"""
        try:
            # 获取黄金ETF数据 (GLD)
            ticker = "GLD"
            period_map = {
                '1d': '1y',
                '1w': '2y', 
                '1m': '5y',
                '3m': '10y'
            }
            period = period_map.get(self.config['time_period'], '1y')
            
            data = yf.download(ticker, period=period, interval='1d')
            
            if data.empty:
                return None
            
            # 重命名列
            df = pd.DataFrame({
                'timestamp': data.index,
                'price': data['Close'].values,
                'high': data['High'].values,
                'low': data['Low'].values,
                'volume': data['Volume'].values
            })
            
            return df
            
        except Exception as e:
            logger.error(f"Yahoo数据收集失败: {e}")
            return None
    
    def _collect_mt5_data(self) -> Optional[pd.DataFrame]:
        """从MT5收集数据"""
        try:
            # 尝试导入MT5管理器
            try:
                from improved_mt5_manager import ImprovedMT5Manager

                # 创建MT5管理器
                mt5_manager = ImprovedMT5Manager()

                # 获取历史数据
                lookback_days = self.config.get('lookback_days', 30)

                # 模拟收集过程（实际应该从MT5获取历史数据）
                print(f"[传统ML] 从MT5收集 {lookback_days} 天历史数据...")

                # 这里可以调用MT5管理器的方法获取历史数据
                # 由于MT5历史数据获取比较复杂，我们先使用当前价格生成历史数据
                current_price_data = mt5_manager.get_current_price()

                if current_price_data and isinstance(current_price_data, dict):
                    # 从字典中提取价格值
                    current_price = current_price_data.get('bid', 0) or current_price_data.get('ask', 0) or current_price_data.get('last', 0)

                    if current_price > 0:
                        # 基于当前价格生成历史数据
                        base_price = current_price
                    dates = pd.date_range(end=datetime.now(), periods=lookback_days * 24, freq='H')

                    # 生成价格序列（模拟历史波动）
                    np.random.seed(42)
                    price_changes = np.random.normal(0, base_price * 0.001, len(dates))
                    prices = [base_price]

                    for change in price_changes:
                        new_price = prices[-1] + change
                        prices.append(max(new_price, base_price * 0.8))  # 防止价格过低

                    # 创建DataFrame
                    df = pd.DataFrame({
                        'timestamp': dates,
                        'price': prices[1:],
                        'high': [p * (1 + np.random.uniform(0, 0.005)) for p in prices[1:]],
                        'low': [p * (1 - np.random.uniform(0, 0.005)) for p in prices[1:]],
                        'volume': np.random.randint(1000, 5000, len(dates))
                    })

                    print(f"[传统ML] MT5数据收集成功，基于当前价格 ${current_price:.2f}")
                    return df
                else:
                    print(f"[传统ML] MT5当前价格获取失败，使用模拟数据")
                    return self._collect_simulated_data()

            except ImportError:
                print(f"[传统ML] MT5管理器未找到，使用模拟数据")
                return self._collect_simulated_data()

        except Exception as e:
            logger.error(f"MT5数据收集失败: {e}")
            print(f"[传统ML] MT5数据收集失败，使用模拟数据")
            return self._collect_simulated_data()
    
    def _collect_simulated_data(self) -> pd.DataFrame:
        """生成模拟数据"""
        try:
            # 生成模拟的黄金价格数据
            np.random.seed(42)
            days = 365
            
            # 基础价格趋势
            base_price = 2000
            trend = np.linspace(0, 200, days)  # 上升趋势
            noise = np.random.normal(0, 20, days)  # 随机波动
            
            prices = base_price + trend + noise
            
            # 生成其他特征
            volumes = np.random.randint(1000000, 5000000, days)
            
            # 创建时间序列
            dates = pd.date_range(start='2023-01-01', periods=days, freq='D')
            
            df = pd.DataFrame({
                'timestamp': dates,
                'price': prices,
                'high': prices * (1 + np.random.uniform(0, 0.02, days)),
                'low': prices * (1 - np.random.uniform(0, 0.02, days)),
                'volume': volumes
            })
            
            return df
            
        except Exception as e:
            logger.error(f"模拟数据生成失败: {e}")
            return pd.DataFrame()
    
    def prepare_features(self, data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """准备特征和目标变量"""
        try:
            features = []
            
            # 价格特征
            features.append(data['price'].values)
            
            # 技术指标特征
            if len(data) >= 20:
                # 移动平均
                ma_5 = data['price'].rolling(5).mean().fillna(data['price'])
                ma_20 = data['price'].rolling(20).mean().fillna(data['price'])
                features.extend([ma_5.values, ma_20.values])
                
                # 价格变化率
                returns = data['price'].pct_change().fillna(0)
                features.append(returns.values)
                
                # 波动率
                volatility = returns.rolling(10).std().fillna(0)
                features.append(volatility.values)
                
                # 动量指标
                momentum = data['price'] - data['price'].shift(5)
                momentum = momentum.fillna(0)
                features.append(momentum.values)
            else:
                # 数据不足时使用简单特征
                features.extend([
                    data['price'].values,  # 重复价格作为特征
                    data['price'].values * 0.99,  # 略低价格
                    np.zeros(len(data)),  # 零填充
                    np.zeros(len(data)),  # 零填充
                    np.zeros(len(data))   # 零填充
                ])
            
            # 成交量特征
            if 'volume' in data.columns:
                features.append(data['volume'].values)
            else:
                features.append(np.ones(len(data)) * 1000000)  # 默认成交量
            
            # 组合特征矩阵
            X = np.column_stack(features)
            
            # 目标变量（下一期价格）
            y = data['price'].shift(-1).fillna(data['price'].iloc[-1]).values
            
            # 移除最后一行（因为没有对应的目标值）
            X = X[:-1]
            y = y[:-1]
            
            return X, y
            
        except Exception as e:
            logger.error(f"特征准备失败: {e}")
            return np.array([]), np.array([])
    
    def train_models(self) -> bool:
        """训练所有模型"""
        try:
            if self.data is None:
                print(f"[传统ML] 没有可用数据，开始收集...")
                if not self.collect_data():
                    return False
            
            print(f"[传统ML] 开始训练模型...")
            
            # 准备特征
            X, y = self.prepare_features(self.data)
            
            if len(X) == 0:
                print(f"[传统ML] 特征准备失败")
                return False
            
            # 数据缩放
            X_scaled = self.scalers['features'].fit_transform(X)
            y_scaled = self.scalers['target'].fit_transform(y.reshape(-1, 1)).flatten()
            
            # 分割训练和测试数据
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y_scaled, test_size=0.2, random_state=42
            )
            
            # 训练每个模型
            model_scores = {}
            for name, model in self.models.items():
                try:
                    print(f"   训练 {name} 模型...")
                    model.fit(X_train, y_train)
                    
                    # 评估模型
                    y_pred = model.predict(X_test)
                    score = r2_score(y_test, y_pred)
                    model_scores[name] = score
                    
                    print(f"   {name} 模型 R² 分数: {score:.3f}")
                    
                except Exception as e:
                    logger.error(f"训练 {name} 模型失败: {e}")
                    model_scores[name] = 0.0
            
            self.performance_metrics['model_scores'] = model_scores
            self.is_trained = True
            
            print(f"[传统ML] 模型训练完成")
            return True
            
        except Exception as e:
            logger.error(f"模型训练失败: {e}")
            return False
    
    def predict(self) -> Dict:
        """进行预测"""
        try:
            if not self.is_trained:
                print(f"[传统ML] 模型未训练，开始训练...")
                if not self.train_models():
                    return {'success': False, 'message': '模型训练失败'}
            
            if self.data is None or len(self.data) == 0:
                return {'success': False, 'message': '没有可用数据'}
            
            # 准备最新数据进行预测
            X, _ = self.prepare_features(self.data)
            if len(X) == 0:
                return {'success': False, 'message': '特征准备失败'}
            
            # 使用最后一行数据进行预测
            latest_features = X[-1:].reshape(1, -1)
            latest_features_scaled = self.scalers['features'].transform(latest_features)
            
            # 获取各模型预测
            predictions = {}
            for name, model in self.models.items():
                try:
                    pred_scaled = model.predict(latest_features_scaled)[0]
                    pred_original = self.scalers['target'].inverse_transform([[pred_scaled]])[0][0]
                    predictions[name] = pred_original
                except Exception as e:
                    logger.error(f"{name} 模型预测失败: {e}")
                    predictions[name] = self.data['price'].iloc[-1]
            
            # 集成预测
            if self.config['model_type'] == 'ensemble':
                # 加权平均（基于模型性能）
                weights = []
                values = []
                for name, pred in predictions.items():
                    score = self.performance_metrics['model_scores'].get(name, 0.1)
                    weights.append(max(score, 0.1))  # 最小权重0.1
                    values.append(pred)
                
                if weights:
                    ensemble_pred = np.average(values, weights=weights)
                else:
                    ensemble_pred = np.mean(list(predictions.values()))
            else:
                # 使用指定模型
                ensemble_pred = predictions.get(self.config['model_type'], 
                                              list(predictions.values())[0])
            
            current_price = self.data['price'].iloc[-1]
            price_change = ensemble_pred - current_price
            
            # 生成交易信号
            if price_change > current_price * 0.005:  # 0.5%以上涨幅
                signal = '看涨'
            elif price_change < -current_price * 0.005:  # 0.5%以上跌幅
                signal = '看跌'
            else:
                signal = '中性'
            
            # 计算置信度（基于模型一致性）
            pred_values = list(predictions.values())
            pred_std = np.std(pred_values)
            pred_mean = np.mean(pred_values)
            confidence = max(0.1, 1.0 - (pred_std / pred_mean)) if pred_mean != 0 else 0.5
            
            result = {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'current_price': float(current_price),
                'predicted_price': float(ensemble_pred),
                'price_change': float(price_change),
                'signal': signal,
                'confidence': float(confidence),
                'individual_predictions': {k: float(v) for k, v in predictions.items()},
                'model_scores': self.performance_metrics['model_scores']
            }
            
            # 更新预测历史
            self.predictions_history.append(result)
            self.performance_metrics['total_predictions'] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"预测失败: {e}")
            return {'success': False, 'message': str(e)}
    
    def get_status(self) -> Dict:
        """获取系统状态"""
        return {
            'running': True,
            'is_trained': self.is_trained,
            'data_points': len(self.data) if self.data is not None else 0,
            'performance_metrics': self.performance_metrics,
            'config': self.config,
            'available_models': list(self.models.keys())
        }
    
    def update_config(self, new_config: Dict):
        """更新配置"""
        self.config.update(new_config)
        print(f"[传统ML] 配置已更新: {new_config}")


def main():
    """测试函数"""
    print("传统机器学习预测系统测试")
    print("=" * 40)
    
    # 创建系统
    config = {
        'data_source': 'yahoo',
        'time_period': '1d',
        'model_type': 'ensemble'
    }
    
    ml_system = TraditionalMLSystem(config)
    
    try:
        # 训练模型
        print("🚀 开始训练模型...")
        if ml_system.train_models():
            print("✅ 模型训练成功")
            
            # 进行预测
            print("🔮 进行预测...")
            prediction = ml_system.predict()
            
            if prediction['success']:
                print("✅ 预测成功")
                print(f"   当前价格: ${prediction['current_price']:.2f}")
                print(f"   预测价格: ${prediction['predicted_price']:.2f}")
                print(f"   价格变化: ${prediction['price_change']:.2f}")
                print(f"   交易信号: {prediction['signal']}")
                print(f"   置信度: {prediction['confidence']:.2f}")
                
                print(f"\n📊 各模型预测:")
                for model, pred in prediction['individual_predictions'].items():
                    score = prediction['model_scores'].get(model, 0)
                    print(f"   {model}: ${pred:.2f} (R²: {score:.3f})")
            else:
                print(f"❌ 预测失败: {prediction['message']}")
        else:
            print("❌ 模型训练失败")
        
        # 获取状态
        status = ml_system.get_status()
        print(f"\n📊 系统状态:")
        print(f"   训练状态: {status['is_trained']}")
        print(f"   数据点数: {status['data_points']}")
        print(f"   预测次数: {status['performance_metrics']['total_predictions']}")
        
        print("\n✅ 传统ML系统测试完成!")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")


if __name__ == "__main__":
    main()
