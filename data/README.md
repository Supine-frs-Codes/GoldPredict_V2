# 🥇 Gold Price Prediction System

一个基于深度学习和强化学习的高级黄金价格预测系统，专门优化支持RTX 50系列显卡。

## ✨ 特性

- 🤖 **多模型集成**: LSTM、GRU、Transformer等深度学习模型
- 🎯 **强化学习**: DQN、PPO等算法优化交易策略
- 🚀 **RTX 50系列优化**: 专门针对最新GPU架构优化
- 📊 **技术指标**: 50+种技术分析指标
- 📈 **实时预测**: 支持多时间跨度预测
- 🎨 **可视化**: 交互式图表和仪表板
- ⚡ **高性能**: GPU/多核CPU并行训练

## 🔧 系统要求

### 硬件要求
- **推荐**: RTX 50系列显卡 (RTX 5090/5080/5070/5060)
- **最低**: 8GB GPU内存或16GB系统内存
- **CPU**: 多核处理器 (推荐8核以上)

### 软件要求
- Python 3.10+
- CUDA 12.0+ (RTX 50系列)
- Windows 10/11, Linux, macOS

## 🚀 快速开始

### 1. 环境设置

使用uv创建虚拟环境（推荐）：

```bash
# 安装uv
pip install uv

# 创建项目环境
cd goldpredict
uv venv
uv sync
```

或使用conda：

```bash
conda create -n goldpredict python=3.10
conda activate goldpredict
pip install -r requirements.txt
```

### 2. GPU兼容性检查

检查RTX 50系列兼容性：

```bash
uv run python test_gpu.py
```

这将：
- 检测GPU型号和驱动
- 测试CUDA兼容性
- 运行性能基准测试
- 提供优化建议

### 3. 数据收集测试

```bash
uv run python src/data/data_collector.py
```

### 4. 训练模型

#### 基础训练
```bash
uv run python train.py --config configs/rtx50_config.json --output ./models --visualize
```

#### 自定义配置训练
```bash
uv run python train.py \
    --config configs/rtx50_config.json \
    --output ./models \
    --device auto \
    --visualize
```

### 5. 进行预测

#### 多时间跨度预测
```bash
uv run python predict.py \
    --model ./models/ensemble \
    --mode multiple \
    --visualize \
    --output-dir ./predictions
```

#### 不确定性预测
```bash
uv run python predict.py \
    --model ./models/ensemble \
    --mode uncertainty \
    --samples 1000 \
    --visualize
```

#### 实时预测
```bash
uv run python predict.py \
    --model ./models/ensemble \
    --mode realtime
```

## 📋 详细使用指南

### 配置文件

系统使用JSON配置文件控制训练参数。RTX 50系列优化配置位于 `configs/rtx50_config.json`。

主要配置项：

```json
{
  "models": {
    "types": ["lstm", "gru", "transformer"],
    "lstm": {
      "hidden_size": 256,
      "num_layers": 3,
      "bidirectional": true
    }
  },
  "training": {
    "batch_size": 64,
    "epochs": 200,
    "use_mixed_precision": true
  },
  "rtx50_specific": {
    "use_torch_compile": true,
    "compile_mode": "max-autotune",
    "enable_tf32": true
  }
}
```

### RTX 50系列优化

系统自动检测RTX 50系列显卡并启用以下优化：

1. **torch.compile**: 模型编译优化
2. **Mixed Precision**: FP16训练加速
3. **Flash Attention**: 高效注意力机制
4. **CUDA Graphs**: 减少CPU开销
5. **TensorFloat-32**: 提升计算性能

### 训练参数说明

| 参数 | 说明 | RTX 5090 | RTX 5080 | RTX 5070 |
|------|------|----------|----------|----------|
| batch_size | 批次大小 | 64-128 | 32-64 | 16-32 |
| hidden_size | 隐藏层大小 | 512 | 256 | 128 |
| num_layers | 层数 | 4-6 | 3-4 | 2-3 |
| sequence_length | 序列长度 | 128 | 64 | 32 |