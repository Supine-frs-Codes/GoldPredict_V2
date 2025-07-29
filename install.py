#!/usr/bin/env python3
"""
GoldPredict V2.0 自动安装脚本
自动检测环境并安装所需依赖
"""

import sys
import os
import subprocess
import platform
import importlib.util
from pathlib import Path

def print_banner():
    """打印安装横幅"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                    🏆 GoldPredict V2.0                       ║
    ║                   智能黄金价格预测系统                        ║
    ║                      自动安装程序                            ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_python_version():
    """检查Python版本"""
    print("🐍 检查Python版本...")
    version = sys.version_info
    print(f"   当前Python版本: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print("❌ Python版本过低，需要Python 3.10+")
        print("   请升级Python版本后重新运行安装程序")
        return False
    else:
        print("✅ Python版本符合要求")
        return True

def check_system_info():
    """检查系统信息"""
    print("\n💻 系统信息:")
    print(f"   操作系统: {platform.system()} {platform.release()}")
    print(f"   架构: {platform.machine()}")
    print(f"   处理器: {platform.processor()}")
    
    # 检查内存
    try:
        import psutil
        memory = psutil.virtual_memory()
        print(f"   内存: {memory.total // (1024**3)} GB")
        
        if memory.total < 4 * (1024**3):  # 4GB
            print("⚠️  内存不足4GB，可能影响性能")
        else:
            print("✅ 内存充足")
    except ImportError:
        print("   内存: 无法检测")

def check_package_manager():
    """检查包管理器"""
    print("\n📦 检查包管理器...")
    
    # 检查uv
    try:
        result = subprocess.run(['uv', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ uv已安装: {result.stdout.strip()}")
            return 'uv'
    except FileNotFoundError:
        pass
    
    # 检查pip
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ pip已安装: {result.stdout.strip()}")
            return 'pip'
    except FileNotFoundError:
        pass
    
    print("❌ 未找到可用的包管理器")
    return None

def install_uv():
    """安装uv包管理器"""
    print("\n🚀 安装uv包管理器...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'uv'], check=True)
        print("✅ uv安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ uv安装失败: {e}")
        return False

def install_dependencies(package_manager):
    """安装依赖"""
    print(f"\n📚 使用{package_manager}安装依赖...")
    
    if package_manager == 'uv':
        try:
            # 使用uv安装
            subprocess.run(['uv', 'sync'], check=True, cwd=Path(__file__).parent)
            print("✅ 核心依赖安装成功")
            
            # 询问是否安装可选依赖
            install_optional = input("\n是否安装可选依赖? (AI增强/GPU加速等) [y/N]: ").lower()
            if install_optional in ['y', 'yes']:
                extras = []
                
                if input("安装AI增强功能? [y/N]: ").lower() in ['y', 'yes']:
                    extras.append('deep-learning')
                
                if input("安装高级技术分析? [y/N]: ").lower() in ['y', 'yes']:
                    extras.append('advanced-ta')
                
                if input("安装GPU加速? [y/N]: ").lower() in ['y', 'yes']:
                    extras.append('gpu')
                
                if input("安装开发工具? [y/N]: ").lower() in ['y', 'yes']:
                    extras.append('dev')
                
                if extras:
                    extra_str = ','.join(extras)
                    subprocess.run(['uv', 'sync', '--extra', extra_str], check=True)
                    print(f"✅ 可选依赖安装成功: {extra_str}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ uv安装失败: {e}")
            return False
    
    elif package_manager == 'pip':
        try:
            # 使用pip安装
            subprocess.run([
                sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
            ], check=True, cwd=Path(__file__).parent)
            print("✅ 核心依赖安装成功")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ pip安装失败: {e}")
            return False
    
    return False

def check_optional_software():
    """检查可选软件"""
    print("\n🔧 检查可选软件...")
    
    # 检查MetaTrader 5
    mt5_paths = [
        "C:\\Program Files\\MetaTrader 5\\terminal64.exe",
        "C:\\Program Files (x86)\\MetaTrader 5\\terminal.exe",
        "/Applications/MetaTrader 5.app",
        "/usr/bin/metatrader5"
    ]
    
    mt5_found = any(os.path.exists(path) for path in mt5_paths)
    if mt5_found:
        print("✅ MetaTrader 5已安装")
    else:
        print("⚠️  MetaTrader 5未安装 (实盘交易需要)")
        print("   下载地址: https://www.metatrader5.com/")
    
    # 检查微信PC版
    wechat_paths = [
        "C:\\Program Files\\Tencent\\WeChat\\WeChat.exe",
        "C:\\Program Files (x86)\\Tencent\\WeChat\\WeChat.exe",
        "/Applications/WeChat.app"
    ]
    
    wechat_found = any(os.path.exists(path) for path in wechat_paths)
    if wechat_found:
        print("✅ 微信PC版已安装")
    else:
        print("⚠️  微信PC版未安装 (消息推送需要)")
        print("   下载地址: https://pc.weixin.qq.com/")

def create_config_files():
    """创建配置文件"""
    print("\n⚙️ 创建配置文件...")
    
    config_dir = Path(__file__).parent / 'config'
    config_dir.mkdir(exist_ok=True)
    
    # 创建主配置文件
    main_config = config_dir / 'config.yaml'
    if not main_config.exists():
        config_content = """# GoldPredict V2.0 主配置文件
system:
  name: "GoldPredict V2.0"
  version: "2.0.0"
  debug: false
  log_level: "INFO"

data_sources:
  primary: "mt5"
  backup: ["yahoo", "alpha_vantage"]
  update_interval: 30

prediction:
  lookback_days: 30
  prediction_horizon: 24
  confidence_threshold: 0.7

models:
  traditional_ml:
    enabled: true
    models: ["random_forest", "xgboost", "lightgbm"]
    ensemble_method: "voting"
    cross_validation_folds: 5
    
  ai_enhanced:
    enabled: false
    models: ["lstm", "transformer", "cnn"]
    training_epochs: 100
    batch_size: 32
"""
        main_config.write_text(config_content, encoding='utf-8')
        print("✅ 主配置文件已创建")
    
    # 创建交易配置文件
    trading_config = config_dir / 'trading.yaml'
    if not trading_config.exists():
        trading_content = """# 交易配置文件
trading:
  enabled: false
  symbol: "XAUUSD"
  timeframe: "H1"

mt5:
  login: ""
  password: ""
  server: ""
  timeout: 10

risk_management:
  max_position_size: 0.1
  stop_loss_pips: 200
  take_profit_pips: 400
  max_daily_trades: 10
  max_daily_loss: 0.05

strategy:
  signal_threshold: 0.7
  position_sizing: "fixed"
  trade_on_signals: ["强烈看涨", "强烈看跌"]
"""
        trading_config.write_text(trading_content, encoding='utf-8')
        print("✅ 交易配置文件已创建")
    
    # 创建微信配置文件
    wechat_config = config_dir / 'wechat.json'
    if not wechat_config.exists():
        wechat_content = """{
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
    "format": "📊 当前价格: ${current_price}\\n🎯 预测价格: ${predicted_price}\\n📈 预测信号: ${signal}\\n🎲 置信度: ${confidence}%\\n⏰ 时间: ${timestamp}"
  },
  "retry_settings": {
    "max_retries": 3,
    "retry_delay": 5
  }
}"""
        wechat_config.write_text(wechat_content, encoding='utf-8')
        print("✅ 微信配置文件已创建")

def create_env_file():
    """创建环境变量文件"""
    print("\n🔐 创建环境变量文件...")
    
    env_file = Path(__file__).parent / '.env'
    if not env_file.exists():
        env_content = """# GoldPredict V2.0 环境变量配置
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
"""
        env_file.write_text(env_content, encoding='utf-8')
        print("✅ 环境变量文件已创建")
        print("⚠️  请编辑.env文件，填入您的API密钥和配置信息")

def test_installation():
    """测试安装"""
    print("\n🧪 测试安装...")
    
    try:
        # 测试核心模块导入
        import pandas
        import numpy
        import sklearn
        import flask
        print("✅ 核心模块导入成功")
        
        # 测试可选模块
        optional_modules = {
            'MetaTrader5': 'MT5数据源',
            'wxauto': '微信集成',
            'torch': 'AI增强功能',
            'ta': '高级技术分析'
        }
        
        for module, description in optional_modules.items():
            try:
                importlib.import_module(module)
                print(f"✅ {description}模块可用")
            except ImportError:
                print(f"⚠️  {description}模块未安装 (可选)")
        
        return True
        
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False

def print_next_steps():
    """打印后续步骤"""
    print("\n🎉 安装完成！")
    print("\n📋 后续步骤:")
    print("1. 编辑配置文件:")
    print("   - config/config.yaml (主配置)")
    print("   - config/trading.yaml (交易配置)")
    print("   - config/wechat.json (微信配置)")
    print("   - .env (环境变量)")
    
    print("\n2. 启动系统:")
    print("   uv run python unified_prediction_platform_fixed_ver2.0.py")
    print("   或")
    print("   python unified_prediction_platform_fixed_ver2.0.py")
    
    print("\n3. 访问Web界面:")
    print("   http://localhost:5000")
    
    print("\n4. 可选配置:")
    print("   - 安装MetaTrader 5 (实盘交易)")
    print("   - 配置微信PC版 (消息推送)")
    print("   - 申请API密钥 (数据源)")
    
    print("\n📚 文档:")
    print("   - README_V2.md (完整文档)")
    print("   - docs/ (详细文档)")
    
    print("\n🆘 获取帮助:")
    print("   - GitHub: https://github.com/goldpredict/goldpredict")
    print("   - 邮件: goldpredict@example.com")

def main():
    """主函数"""
    print_banner()
    
    # 检查Python版本
    if not check_python_version():
        sys.exit(1)
    
    # 检查系统信息
    check_system_info()
    
    # 检查包管理器
    package_manager = check_package_manager()
    if not package_manager:
        print("\n🚀 尝试安装uv包管理器...")
        if install_uv():
            package_manager = 'uv'
        else:
            print("❌ 无法安装包管理器，请手动安装pip或uv")
            sys.exit(1)
    
    # 安装依赖
    if not install_dependencies(package_manager):
        print("❌ 依赖安装失败")
        sys.exit(1)
    
    # 检查可选软件
    check_optional_software()
    
    # 创建配置文件
    create_config_files()
    
    # 创建环境变量文件
    create_env_file()
    
    # 测试安装
    if test_installation():
        print_next_steps()
    else:
        print("❌ 安装测试失败，请检查错误信息")
        sys.exit(1)

if __name__ == "__main__":
    main()
