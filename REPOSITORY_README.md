# 🏆 GoldPredict V2.0 - 智能黄金价格预测系统

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-2.0.0-orange.svg)](CHANGELOG.md)

> **🚀 完整的智能黄金价格预测系统**: 集成AI增强预测、传统ML、自动交易、微信推送于一体

## 📦 仓库内容

### 🎯 **核心系统** (11 个)
- `unified_prediction_platform_fixed_ver2.0.py` - 统一管理平台
- `traditional_ml_system_ver2.py` - 传统机器学习系统
- `auto_trading_system.py` - 自动交易系统
- `wechat_sender.py` - 微信集成系统
- `standalone_launcher.py` - 独立启动器

### 🛠️ **工具脚本** (11 个)
- `start.py` - 快速启动脚本
- `install.py` - 自动安装脚本
- `build_executable_v2.py` - 可执行文件打包
- `fix_dependencies.py` - 依赖修复工具

### 📚 **文档** (6 个)
- `README_V2.md` - 详细使用文档 (1900+ 行)
- `ENVIRONMENT_SETUP_V2.md` - 环境配置指南
- `PACKAGING_VERIFICATION_REPORT.md` - 打包验证报告

### ⚙️ **配置文件**
- `pyproject.toml` - 项目配置 (uv包管理)
- `requirements.txt` - 依赖列表 (pip兼容)
- `config/` - 系统配置目录

## 🚀 快速开始

### 方法1: 使用uv (推荐)
```bash
# 1. 克隆仓库
git clone <repository-url>
cd goldpredict

# 2. 安装依赖
uv sync

# 3. 启动系统
uv run python start.py
```

### 方法2: 使用pip
```bash
# 1. 克隆仓库
git clone <repository-url>
cd goldpredict

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动系统
python start.py
```

### 方法3: 自动安装
```bash
# 运行自动安装脚本
python install.py
```

## 🌐 访问系统

启动后访问: **http://localhost:5000**

- 主页面: 系统状态和控制
- `/traditional` - 传统ML预测
- `/auto_trading` - 自动交易管理
- `/wechat` - 微信推送管理

## 📊 仓库统计

- **总文件数**: 97
- **Python文件**: 66
- **配置文件**: 10
- **文档文件**: 6

## 🎯 主要功能

### ✅ **已实现功能**
- 🤖 AI增强预测系统
- 📈 传统ML多模型集成
- 🔄 MT5自动交易
- 📱 微信智能推送
- 🌐 统一Web管理平台
- 📦 独立可执行文件打包

### 🔧 **系统要求**
- Python 3.10+
- 4GB+ 内存
- Windows 10/11 (推荐)
- 稳定网络连接

## 📖 详细文档

查看 `README_V2.md` 获取完整的使用指南，包括：
- 详细安装说明
- 功能使用教程
- 参数配置指南
- API接口文档
- 故障排除指南

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🤝 贡献

欢迎贡献代码、报告问题或提出建议！

---

**🎉 享受智能预测的乐趣，祝您投资顺利！**

*构建时间: 2025-07-28 00:02:20*
