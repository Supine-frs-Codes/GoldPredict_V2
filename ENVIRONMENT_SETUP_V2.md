# 🔧 GoldPredict V2.0 环境配置指南

## 📋 概述

本文档详细说明了GoldPredict V2.0版本的环境配置要求、依赖更新和安装方法。

---

## 🆕 V2.0版本更新内容

### 📦 **新增依赖包**

#### **核心功能依赖**
```toml
# 新增MT5数据源支持
"metatrader5>=5.0.5120"

# 新增微信集成功能
"watchdog>=3.0.0"
"wxauto>=39.1.14"

# 增强Web界面
"jinja2>=3.1.0"
"werkzeug>=2.3.0"
"flask-socketio>=5.3.0"

# 数据库支持
"sqlalchemy>=2.0.0"

# 工具库
"python-dateutil>=2.8.0"
```

#### **可选依赖包**
```toml
# AI增强功能 (可选)
[project.optional-dependencies]
deep-learning = [
    "torch>=2.5.0",
    "torchvision>=0.20.0", 
    "torchaudio>=2.5.0",
    "transformers>=4.40.0",
    "stable-baselines3>=2.0.0",
    "gymnasium>=0.28.0",
]

# 高级技术分析 (可选)
advanced-ta = [
    "ta-lib>=0.6.4",
    "catboost>=1.2.0",
]

# GPU加速 (可选)
gpu = [
    "cupy-cuda11x>=12.0.0",
    "numba>=0.58.0",
]

# 开发工具 (可选)
dev = [
    "pytest>=7.0.0",
    "black>=23.0.0",
    "flake8>=6.0.0",
    "mypy>=1.0.0",
]
```

### 🔄 **版本更新**
- **项目版本**: 0.1.0 → 2.0.0
- **Python要求**: >=3.10 (保持不变)
- **核心依赖**: 优化版本要求
- **新增功能**: 5大核心系统集成

---

## 🚀 安装方法

### 方法1: 自动安装 (推荐)

```bash
# 1. 克隆项目
git clone https://github.com/goldpredict/goldpredict.git
cd goldpredict

# 2. 运行自动安装脚本
python install.py

# 3. 按提示完成配置
```

### 方法2: 使用uv包管理器

```bash
# 1. 安装uv (如果未安装)
pip install uv

# 2. 克隆项目
git clone https://github.com/goldpredict/goldpredict.git
cd goldpredict

# 3. 安装核心依赖
uv sync

# 4. 安装可选依赖 (根据需要选择)
uv sync --extra deep-learning    # AI增强功能
uv sync --extra advanced-ta      # 高级技术分析
uv sync --extra gpu              # GPU加速
uv sync --extra dev              # 开发工具
uv sync --extra all              # 所有功能
```

### 方法3: 使用传统pip

```bash
# 1. 克隆项目
git clone https://github.com/goldpredict/goldpredict.git
cd goldpredict

# 2. 创建虚拟环境 (推荐)
python -m venv goldpredict-env
source goldpredict-env/bin/activate  # Linux/Mac
# 或
goldpredict-env\Scripts\activate     # Windows

# 3. 安装核心依赖
pip install -r requirements.txt

# 4. 安装可选依赖 (手动)
# AI增强功能
pip install torch torchvision torchaudio transformers stable-baselines3 gymnasium

# 高级技术分析
pip install ta-lib catboost

# GPU加速
pip install cupy-cuda11x numba
```

---

## ⚙️ 配置文件

### 📁 **配置文件结构**
```
config/
├── config.yaml          # 主配置文件
├── trading.yaml          # 交易配置
├── wechat.json           # 微信配置
└── .env                  # 环境变量
```

### 🔧 **主配置文件 (config/config.yaml)**
```yaml
# 系统基础配置
system:
  name: "GoldPredict V2.0"
  version: "2.0.0"
  debug: false
  log_level: "INFO"

# 数据源配置
data_sources:
  primary: "mt5"              # 主数据源
  backup: ["yahoo", "alpha_vantage"]
  update_interval: 30         # 更新间隔(秒)

# 预测配置
prediction:
  lookback_days: 30          # 历史数据天数
  prediction_horizon: 24     # 预测时间范围(小时)
  confidence_threshold: 0.7  # 置信度阈值

# 模型配置
models:
  traditional_ml:
    enabled: true
    models: ["random_forest", "xgboost", "lightgbm"]
    ensemble_method: "voting"
    cross_validation_folds: 5
    
  ai_enhanced:
    enabled: false            # 可选功能
    models: ["lstm", "transformer", "cnn"]
    training_epochs: 100
    batch_size: 32

# 性能配置
performance:
  threading:
    max_workers: 4
    prediction_workers: 2
    data_workers: 2
  cache:
    enabled: true
    ttl: 300
    max_size: 1000
  gpu:
    enabled: false
    device: "cuda:0"
    memory_fraction: 0.8
```

### 💼 **交易配置文件 (config/trading.yaml)**
```yaml
# 交易基础配置
trading:
  enabled: false             # 是否启用自动交易
  symbol: "XAUUSD"          # 交易品种
  timeframe: "H1"           # 时间框架

# MT5连接配置
mt5:
  login: ""                 # MT5账号
  password: ""              # MT5密码
  server: ""                # MT5服务器
  timeout: 10               # 连接超时(秒)

# 风险管理
risk_management:
  max_position_size: 0.1    # 最大仓位比例
  stop_loss_pips: 200      # 止损点数
  take_profit_pips: 400    # 止盈点数
  max_daily_trades: 10     # 日最大交易次数
  max_daily_loss: 0.05     # 日最大亏损比例

# 交易策略
strategy:
  signal_threshold: 0.7     # 信号强度阈值
  position_sizing: "fixed"  # 仓位管理方式
  trade_on_signals: ["强烈看涨", "强烈看跌"]
```

### 📱 **微信配置文件 (config/wechat.json)**
```json
{
  "enabled": false,
  "target_groups": [
    "黄金预测群1",
    "黄金预测群2"
  ],
  "send_conditions": {
    "min_confidence": 0.8,
    "signals": ["强烈看涨", "强烈看跌", "看涨", "看跌"],
    "send_interval": 300
  },
  "message_template": {
    "title": "🔮 黄金价格预测",
    "format": "📊 当前价格: ${current_price}\n🎯 预测价格: ${predicted_price}\n📈 预测信号: ${signal}\n🎲 置信度: ${confidence}%\n⏰ 时间: ${timestamp}"
  },
  "retry_settings": {
    "max_retries": 3,
    "retry_delay": 5
  }
}
```

### 🔐 **环境变量文件 (.env)**
```bash
# API密钥配置
ALPHA_VANTAGE_API_KEY=your_api_key_here
YAHOO_FINANCE_API_KEY=your_api_key_here

# MT5配置
MT5_LOGIN=your_mt5_login
MT5_PASSWORD=your_mt5_password
MT5_SERVER=your_mt5_server

# 系统配置
DEBUG=False
LOG_LEVEL=INFO
DATA_PATH=./data
MODEL_PATH=./models

# 安全配置
SECRET_KEY=your_secret_key_here
ENCRYPTION_KEY=your_encryption_key_here
```

---

## 🔍 环境验证

### 🧪 **安装验证脚本**
```python
# verify_installation.py
import sys
import importlib

def verify_core_dependencies():
    """验证核心依赖"""
    core_modules = [
        'pandas', 'numpy', 'scipy', 'sklearn',
        'flask', 'requests', 'matplotlib'
    ]
    
    for module in core_modules:
        try:
            importlib.import_module(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module} - 未安装")

def verify_optional_dependencies():
    """验证可选依赖"""
    optional_modules = {
        'MetaTrader5': 'MT5数据源',
        'wxauto': '微信集成',
        'torch': 'AI增强功能',
        'ta': '高级技术分析',
        'cupy': 'GPU加速'
    }
    
    for module, description in optional_modules.items():
        try:
            importlib.import_module(module)
            print(f"✅ {description}")
        except ImportError:
            print(f"⚠️  {description} - 未安装 (可选)")

if __name__ == "__main__":
    print("🔍 验证GoldPredict V2.0环境...")
    print(f"Python版本: {sys.version}")
    print("\n核心依赖:")
    verify_core_dependencies()
    print("\n可选依赖:")
    verify_optional_dependencies()
```

### 🚀 **快速测试**
```bash
# 运行验证脚本
python verify_installation.py

# 测试系统启动
python unified_prediction_platform_fixed_ver2.0.py --test

# 测试API接口
curl http://localhost:5000/api/status
```

---

## 🛠️ 故障排除

### ❌ **常见问题**

#### **1. uv sync失败**
```bash
# 解决方案
pip install --upgrade uv
uv cache clean
uv sync --reinstall
```

#### **2. MetaTrader5安装失败**
```bash
# Windows解决方案
pip install --upgrade pip
pip install MetaTrader5

# 如果仍然失败，手动下载whl文件
# https://pypi.org/project/MetaTrader5/#files
```

#### **3. wxauto安装失败**
```bash
# 使用特定版本
pip install wxauto==39.1.14

# 或使用替代库
pip install itchat
```

#### **4. ta-lib安装失败**
```bash
# Windows: 下载预编译包
# https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib

# Linux: 安装系统依赖
sudo apt-get install libta-lib-dev
pip install ta-lib

# macOS: 使用brew
brew install ta-lib
pip install ta-lib
```

### 🔧 **性能优化**

#### **内存优化**
```yaml
# config/config.yaml
performance:
  cache:
    max_size: 500          # 减少缓存大小
  threading:
    max_workers: 2         # 减少线程数

prediction:
  lookback_days: 15        # 减少历史数据
```

#### **CPU优化**
```yaml
models:
  traditional_ml:
    models: ["random_forest"]  # 使用单一模型
    cross_validation_folds: 3  # 减少交叉验证折数
```

---

## 📊 系统要求对比

| 项目 | V1.0要求 | V2.0要求 | 变化 |
|------|----------|----------|------|
| **Python版本** | >=3.8 | >=3.10 | ⬆️ 提升 |
| **内存** | 2GB | 4GB+ | ⬆️ 增加 |
| **存储** | 1GB | 2GB+ | ⬆️ 增加 |
| **核心依赖** | 15个 | 25个+ | ⬆️ 增加 |
| **可选依赖** | 5个 | 20个+ | ⬆️ 大幅增加 |
| **功能模块** | 2个 | 5个 | ⬆️ 大幅增加 |

---

## 🎯 下一步

1. **完成环境配置**: 按照本指南完成安装
2. **阅读用户手册**: 查看README_V2.md
3. **配置系统参数**: 编辑配置文件
4. **启动系统**: 运行统一平台
5. **功能测试**: 验证各模块功能

---

**🎉 环境配置完成后，您就可以开始使用GoldPredict V2.0的强大功能了！**
