#!/usr/bin/env python3
"""
深度学习模型集成模块
集成Transformer、GRU、CNN-LSTM等先进模型
"""

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import MinMaxScaler
from typing import Dict, List, Optional, Tuple
import logging
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class TransformerPredictor(nn.Module):
    """Transformer预测模型"""
    
    def __init__(self, input_dim=5, d_model=64, nhead=8, num_layers=3, dropout=0.1):
        super(TransformerPredictor, self).__init__()
        self.input_dim = input_dim
        self.d_model = d_model
        
        # 输入投影层
        self.input_projection = nn.Linear(input_dim, d_model)
        
        # 位置编码
        self.pos_encoding = PositionalEncoding(d_model, dropout)
        
        # Transformer编码器
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=d_model * 4,
            dropout=dropout,
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        # 输出层
        self.output_layer = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_model // 2, 1)
        )
    
    def forward(self, x):
        # x shape: (batch_size, seq_len, input_dim)
        x = self.input_projection(x)
        x = self.pos_encoding(x)
        x = self.transformer(x)
        
        # 使用最后一个时间步的输出
        x = x[:, -1, :]
        output = self.output_layer(x)
        return output


class PositionalEncoding(nn.Module):
    """位置编码"""
    
    def __init__(self, d_model, dropout=0.1, max_len=5000):
        super(PositionalEncoding, self).__init__()
        self.dropout = nn.Dropout(p=dropout)
        
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-np.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0).transpose(0, 1)
        self.register_buffer('pe', pe)
    
    def forward(self, x):
        x = x + self.pe[:x.size(1), :].transpose(0, 1)
        return self.dropout(x)


class GRUPredictor(nn.Module):
    """GRU预测模型"""
    
    def __init__(self, input_dim=5, hidden_dim=64, num_layers=2, dropout=0.1):
        super(GRUPredictor, self).__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        
        self.gru = nn.GRU(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0,
            batch_first=True
        )
        
        self.output_layer = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 1)
        )
    
    def forward(self, x):
        # x shape: (batch_size, seq_len, input_dim)
        gru_out, _ = self.gru(x)
        
        # 使用最后一个时间步的输出
        last_output = gru_out[:, -1, :]
        output = self.output_layer(last_output)
        return output


class CNNLSTMPredictor(nn.Module):
    """CNN-LSTM预测模型"""
    
    def __init__(self, input_dim=5, cnn_filters=32, lstm_hidden=64, dropout=0.1):
        super(CNNLSTMPredictor, self).__init__()
        
        # CNN层
        self.conv1 = nn.Conv1d(input_dim, cnn_filters, kernel_size=3, padding=1)
        self.conv2 = nn.Conv1d(cnn_filters, cnn_filters * 2, kernel_size=3, padding=1)
        self.pool = nn.MaxPool1d(2)
        self.dropout_cnn = nn.Dropout(dropout)
        
        # LSTM层
        self.lstm = nn.LSTM(
            input_size=cnn_filters * 2,
            hidden_size=lstm_hidden,
            num_layers=2,
            dropout=dropout,
            batch_first=True
        )
        
        # 输出层
        self.output_layer = nn.Sequential(
            nn.Linear(lstm_hidden, lstm_hidden // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(lstm_hidden // 2, 1)
        )
    
    def forward(self, x):
        # x shape: (batch_size, seq_len, input_dim)
        # 转换为CNN输入格式: (batch_size, input_dim, seq_len)
        x = x.transpose(1, 2)
        
        # CNN特征提取
        x = torch.relu(self.conv1(x))
        x = self.dropout_cnn(x)
        x = torch.relu(self.conv2(x))
        x = self.pool(x)
        x = self.dropout_cnn(x)
        
        # 转换回LSTM输入格式: (batch_size, seq_len, features)
        x = x.transpose(1, 2)
        
        # LSTM处理
        lstm_out, _ = self.lstm(x)
        
        # 使用最后一个时间步的输出
        last_output = lstm_out[:, -1, :]
        output = self.output_layer(last_output)
        return output


class AutoEncoder(nn.Module):
    """自编码器异常检测模型"""
    
    def __init__(self, input_dim=5, encoding_dim=16):
        super(AutoEncoder, self).__init__()
        
        # 编码器
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, encoding_dim * 2),
            nn.ReLU(),
            nn.Linear(encoding_dim * 2, encoding_dim),
            nn.ReLU()
        )
        
        # 解码器
        self.decoder = nn.Sequential(
            nn.Linear(encoding_dim, encoding_dim * 2),
            nn.ReLU(),
            nn.Linear(encoding_dim * 2, input_dim)
        )
    
    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded


class DeepLearningEnsemble:
    """深度学习模型集成"""
    
    def __init__(self, device=None):
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.models = {}
        self.scalers = {}
        self.is_trained = False
        self.sequence_length = 20
        
        print(f"[深度学习] 模型集成初始化，设备: {self.device}")
        
        # 初始化模型
        self._initialize_models()
    
    def _initialize_models(self):
        """初始化所有模型"""
        try:
            # Transformer模型
            self.models['transformer'] = TransformerPredictor().to(self.device)
            
            # GRU模型
            self.models['gru'] = GRUPredictor().to(self.device)
            
            # CNN-LSTM模型
            self.models['cnn_lstm'] = CNNLSTMPredictor().to(self.device)
            
            # 自编码器
            self.models['autoencoder'] = AutoEncoder().to(self.device)
            
            # 数据缩放器
            self.scalers['price'] = MinMaxScaler()
            self.scalers['features'] = MinMaxScaler()
            
            print(f"[深度学习] 初始化 {len(self.models)} 个模型")
            
        except Exception as e:
            logger.error(f"模型初始化失败: {e}")
            # 使用CPU作为备选
            self.device = 'cpu'
            self._initialize_models()
    
    def prepare_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """准备训练数据"""
        try:
            if len(df) < self.sequence_length + 1:
                raise ValueError(f"数据不足，需要至少 {self.sequence_length + 1} 个数据点")
            
            # 特征工程
            features = self._extract_features(df)
            
            # 数据缩放
            features_scaled = self.scalers['features'].fit_transform(features)
            prices = df['price'].values.reshape(-1, 1)
            prices_scaled = self.scalers['price'].fit_transform(prices)
            
            # 创建序列数据
            X, y = self._create_sequences(features_scaled, prices_scaled.flatten())
            
            return X, y
            
        except Exception as e:
            logger.error(f"数据准备失败: {e}")
            return np.array([]), np.array([])
    
    def _extract_features(self, df: pd.DataFrame) -> np.ndarray:
        """提取特征"""
        features = []
        
        # 价格特征
        features.append(df['price'].values)
        features.append(df['bid'].values)
        features.append(df['ask'].values)
        
        # 技术指标特征
        prices = df['price'].values
        
        # 移动平均
        if len(prices) >= 5:
            ma5 = pd.Series(prices).rolling(5).mean().fillna(prices[0])
            features.append(ma5.values)
        else:
            features.append(prices)
        
        # 价格变化率
        if len(prices) >= 2:
            returns = pd.Series(prices).pct_change().fillna(0)
            features.append(returns.values)
        else:
            features.append(np.zeros_like(prices))
        
        return np.column_stack(features)
    
    def _create_sequences(self, features: np.ndarray, targets: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """创建序列数据"""
        X, y = [], []
        
        for i in range(len(features) - self.sequence_length):
            X.append(features[i:i + self.sequence_length])
            y.append(targets[i + self.sequence_length])
        
        return np.array(X), np.array(y)
    
    def train_models(self, df: pd.DataFrame, epochs=50, batch_size=32) -> Dict:
        """训练所有模型"""
        try:
            print(f"[训练] 开始训练深度学习模型...")
            
            # 准备数据
            X, y = self.prepare_data(df)
            if len(X) == 0:
                return {'success': False, 'message': '数据准备失败'}
            
            # 转换为PyTorch张量
            X_tensor = torch.FloatTensor(X).to(self.device)
            y_tensor = torch.FloatTensor(y).to(self.device)
            
            # 创建数据加载器
            dataset = TensorDataset(X_tensor, y_tensor)
            dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
            
            # 训练结果
            training_results = {}
            
            # 训练每个模型
            for model_name, model in self.models.items():
                if model_name == 'autoencoder':
                    continue  # 自编码器单独训练
                
                print(f"   训练 {model_name}...")
                result = self._train_single_model(model, dataloader, epochs)
                training_results[model_name] = result
            
            # 训练自编码器
            print(f"   训练 autoencoder...")
            ae_result = self._train_autoencoder(X_tensor, epochs)
            training_results['autoencoder'] = ae_result
            
            self.is_trained = True
            
            print(f"[训练] 深度学习模型训练完成")
            return {'success': True, 'results': training_results}
            
        except Exception as e:
            logger.error(f"模型训练失败: {e}")
            return {'success': False, 'message': str(e)}
    
    def _train_single_model(self, model: nn.Module, dataloader: DataLoader, epochs: int) -> Dict:
        """训练单个模型"""
        try:
            optimizer = optim.Adam(model.parameters(), lr=0.001)
            criterion = nn.MSELoss()
            
            model.train()
            losses = []
            
            for epoch in range(epochs):
                epoch_loss = 0
                for batch_X, batch_y in dataloader:
                    optimizer.zero_grad()
                    
                    outputs = model(batch_X)
                    loss = criterion(outputs.squeeze(), batch_y)
                    
                    loss.backward()
                    optimizer.step()
                    
                    epoch_loss += loss.item()
                
                avg_loss = epoch_loss / len(dataloader)
                losses.append(avg_loss)
                
                if epoch % 10 == 0:
                    print(f"     Epoch {epoch}/{epochs}, Loss: {avg_loss:.6f}")
            
            return {'final_loss': losses[-1], 'losses': losses}
            
        except Exception as e:
            logger.error(f"单模型训练失败: {e}")
            return {'final_loss': float('inf'), 'losses': []}
    
    def _train_autoencoder(self, X_tensor: torch.Tensor, epochs: int) -> Dict:
        """训练自编码器"""
        try:
            model = self.models['autoencoder']
            optimizer = optim.Adam(model.parameters(), lr=0.001)
            criterion = nn.MSELoss()
            
            model.train()
            losses = []
            
            # 使用最后一个时间步的数据训练自编码器
            X_last = X_tensor[:, -1, :]
            
            for epoch in range(epochs):
                optimizer.zero_grad()
                
                reconstructed = model(X_last)
                loss = criterion(reconstructed, X_last)
                
                loss.backward()
                optimizer.step()
                
                losses.append(loss.item())
                
                if epoch % 10 == 0:
                    print(f"     Epoch {epoch}/{epochs}, Loss: {loss.item():.6f}")
            
            return {'final_loss': losses[-1], 'losses': losses}
            
        except Exception as e:
            logger.error(f"自编码器训练失败: {e}")
            return {'final_loss': float('inf'), 'losses': []}
    
    def predict(self, df: pd.DataFrame) -> Dict:
        """使用集成模型进行预测"""
        try:
            if not self.is_trained:
                return {'success': False, 'message': '模型未训练'}
            
            if len(df) < self.sequence_length:
                return {'success': False, 'message': f'数据不足，需要至少 {self.sequence_length} 个数据点'}
            
            # 准备预测数据
            features = self._extract_features(df)
            features_scaled = self.scalers['features'].transform(features)
            
            # 获取最后一个序列
            X_pred = features_scaled[-self.sequence_length:].reshape(1, self.sequence_length, -1)
            X_tensor = torch.FloatTensor(X_pred).to(self.device)
            
            # 获取各模型预测
            predictions = {}
            
            for model_name, model in self.models.items():
                if model_name == 'autoencoder':
                    continue
                
                model.eval()
                with torch.no_grad():
                    pred = model(X_tensor)
                    pred_scaled = pred.cpu().numpy()[0, 0]
                    
                    # 反缩放
                    pred_original = self.scalers['price'].inverse_transform([[pred_scaled]])[0, 0]
                    predictions[model_name] = pred_original
            
            # 异常检测
            anomaly_score = self._detect_anomaly(X_tensor[:, -1, :])
            
            # 集成预测
            ensemble_pred = self._ensemble_predictions(predictions)
            
            return {
                'success': True,
                'ensemble_prediction': ensemble_pred,
                'individual_predictions': predictions,
                'anomaly_score': anomaly_score,
                'confidence': self._calculate_confidence(predictions, anomaly_score)
            }
            
        except Exception as e:
            logger.error(f"预测失败: {e}")
            return {'success': False, 'message': str(e)}
    
    def _detect_anomaly(self, X_tensor: torch.Tensor) -> float:
        """异常检测"""
        try:
            model = self.models['autoencoder']
            model.eval()
            
            with torch.no_grad():
                reconstructed = model(X_tensor)
                mse = nn.MSELoss()(reconstructed, X_tensor)
                
                # 归一化异常分数
                anomaly_score = min(mse.item() * 100, 1.0)
                return anomaly_score
                
        except Exception as e:
            logger.error(f"异常检测失败: {e}")
            return 0.5
    
    def _ensemble_predictions(self, predictions: Dict) -> float:
        """集成预测结果"""
        if not predictions:
            return 0.0
        
        # 简单平均集成
        values = list(predictions.values())
        return np.mean(values)
    
    def _calculate_confidence(self, predictions: Dict, anomaly_score: float) -> float:
        """计算预测置信度"""
        if not predictions:
            return 0.0
        
        # 基于预测一致性和异常分数计算置信度
        values = list(predictions.values())
        std = np.std(values)
        mean_val = np.mean(values)
        
        # 一致性分数（标准差越小，一致性越高）
        consistency = 1.0 / (1.0 + std / abs(mean_val)) if mean_val != 0 else 0.5
        
        # 异常分数影响（异常分数越高，置信度越低）
        anomaly_factor = 1.0 - anomaly_score
        
        # 综合置信度
        confidence = (consistency * 0.7 + anomaly_factor * 0.3)
        return max(0.1, min(0.95, confidence))
    
    def get_model_info(self) -> Dict:
        """获取模型信息"""
        return {
            'device': self.device,
            'models': list(self.models.keys()),
            'is_trained': self.is_trained,
            'sequence_length': self.sequence_length,
            'cuda_available': torch.cuda.is_available()
        }


def main():
    """测试函数"""
    print("深度学习模型集成测试")
    print("=" * 40)
    
    # 创建测试数据
    np.random.seed(42)
    n_points = 200
    base_price = 3400
    
    # 生成模拟价格数据
    price_changes = np.random.normal(0, 5, n_points)
    prices = [base_price]
    for change in price_changes:
        prices.append(prices[-1] + change)
    
    # 创建DataFrame
    df = pd.DataFrame({
        'price': prices[1:],
        'bid': [p - 0.05 for p in prices[1:]],
        'ask': [p + 0.05 for p in prices[1:]],
        'volume': np.random.randint(1000, 5000, n_points)
    })
    
    # 测试深度学习模型
    ensemble = DeepLearningEnsemble()
    
    try:
        # 显示模型信息
        info = ensemble.get_model_info()
        print(f"✅ 模型信息:")
        print(f"   设备: {info['device']}")
        print(f"   模型数量: {len(info['models'])}")
        print(f"   CUDA可用: {info['cuda_available']}")
        
        # 训练模型
        print(f"\n🚀 开始训练...")
        train_result = ensemble.train_models(df, epochs=20, batch_size=16)
        
        if train_result['success']:
            print(f"✅ 训练成功")
            
            # 进行预测
            print(f"\n🔮 进行预测...")
            pred_result = ensemble.predict(df)
            
            if pred_result['success']:
                print(f"✅ 预测成功")
                print(f"   集成预测: ${pred_result['ensemble_prediction']:.2f}")
                print(f"   置信度: {pred_result['confidence']:.2f}")
                print(f"   异常分数: {pred_result['anomaly_score']:.3f}")
                
                print(f"\n📊 各模型预测:")
                for model_name, pred in pred_result['individual_predictions'].items():
                    print(f"   {model_name}: ${pred:.2f}")
            else:
                print(f"❌ 预测失败: {pred_result['message']}")
        else:
            print(f"❌ 训练失败: {train_result['message']}")
        
        print("\n✅ 深度学习模型测试完成!")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")


if __name__ == "__main__":
    main()
