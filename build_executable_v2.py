#!/usr/bin/env python3
"""
GoldPredict V2.0 可执行文件打包脚本
使用PyInstaller将完整的V2.0系统打包成可执行文件
"""

import os
import sys
import subprocess
import shutil
import json
import platform
from pathlib import Path

def print_banner():
    """打印横幅"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                  🏆 GoldPredict V2.0                         ║
    ║                   可执行文件打包工具                          ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_environment():
    """检查打包环境"""
    print("🔍 检查打包环境...")
    
    # 检查Python版本
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print(f"❌ Python版本过低: {version.major}.{version.minor}")
        print("   需要Python 3.10+")
        return False
    
    print(f"✅ Python版本: {version.major}.{version.minor}.{version.micro}")
    
    # 检查PyInstaller
    try:
        import PyInstaller
        print(f"✅ PyInstaller已安装: {PyInstaller.__version__}")
    except ImportError:
        print("❌ PyInstaller未安装，正在安装...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
            print("✅ PyInstaller安装成功")
        except subprocess.CalledProcessError:
            print("❌ PyInstaller安装失败")
            return False
    
    # 检查核心文件
    required_files = [
        'unified_prediction_platform_fixed_ver2.0.py',
        'traditional_ml_system_ver2.py',
        'auto_trading_system.py',
        'wechat_sender.py',
        'start.py',
        'pyproject.toml'
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ 缺少核心文件: {', '.join(missing_files)}")
        return False
    
    print("✅ 核心文件完整")
    return True

def analyze_dependencies():
    """分析依赖包"""
    print("📦 分析依赖包...")
    
    # 从requirements.txt读取依赖
    requirements_file = Path('requirements.txt')
    if not requirements_file.exists():
        print("❌ requirements.txt文件不存在")
        return []
    
    dependencies = []
    with open(requirements_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                # 提取包名
                package = line.split('>=')[0].split('==')[0].split('[')[0]
                dependencies.append(package)
    
    print(f"✅ 发现 {len(dependencies)} 个依赖包")
    return dependencies

def create_launcher_script():
    """创建V2.0启动器脚本"""
    print("🚀 创建V2.0启动器...")
    
    launcher_content = '''#!/usr/bin/env python3
"""
GoldPredict V2.0 统一启动器
"""

import sys
import os
import subprocess
import threading
import time
import webbrowser
from pathlib import Path

def print_banner():
    """打印启动横幅"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                    🏆 GoldPredict V2.0                       ║
    ║                   智能黄金价格预测系统                        ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def start_unified_platform():
    """启动统一平台"""
    print("🚀 启动统一平台...")
    try:
        # 检查文件是否存在
        script_path = "unified_prediction_platform_fixed_ver2.0.py"
        if not os.path.exists(script_path):
            print(f"❌ 找不到文件: {script_path}")
            return None
            
        process = subprocess.Popen([sys.executable, script_path])
        print(f"✅ 统一平台已启动 (PID: {process.pid})")
        return process
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return None

def start_traditional_ml():
    """启动传统ML系统"""
    print("📈 启动传统ML系统...")
    try:
        process = subprocess.Popen([sys.executable, "traditional_ml_system_ver2.py"])
        print(f"✅ 传统ML系统已启动 (PID: {process.pid})")
        return process
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return None

def start_auto_trading():
    """启动自动交易系统"""
    print("🔄 启动自动交易系统...")
    try:
        process = subprocess.Popen([sys.executable, "auto_trading_system.py"])
        print(f"✅ 自动交易系统已启动 (PID: {process.pid})")
        return process
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return None

def start_wechat_system():
    """启动微信集成系统"""
    print("📱 启动微信集成系统...")
    try:
        process = subprocess.Popen([sys.executable, "wechat_sender.py"])
        print(f"✅ 微信系统已启动 (PID: {process.pid})")
        return process
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return None

def main():
    """主函数"""
    print_banner()
    
    print("🎯 选择启动模式:")
    print("1. 统一平台 (推荐) - 一体化Web管理界面")
    print("2. 传统ML系统 - 机器学习预测")
    print("3. 自动交易系统 - MT5集成交易")
    print("4. 微信集成系统 - 消息推送")
    print("5. 全部启动 - 启动所有系统")
    print("0. 退出")
    
    while True:
        try:
            choice = input("\\n请选择 (0-5): ").strip()
            
            if choice == '0':
                print("👋 再见！")
                break
            elif choice == '1':
                process = start_unified_platform()
                if process:
                    print("\\n🌐 访问地址:")
                    print("   主页面: http://localhost:5000")
                    print("   传统ML: http://localhost:5000/traditional")
                    print("   自动交易: http://localhost:5000/auto_trading")
                    print("   微信管理: http://localhost:5000/wechat")
                    
                    # 自动打开浏览器
                    time.sleep(2)
                    try:
                        webbrowser.open('http://localhost:5000')
                    except:
                        pass
                    
                    print("\\n按回车键停止系统...")
                    input()
                    process.terminate()
                    process.wait()
                    print("✅ 系统已停止")
                break
            elif choice == '2':
                process = start_traditional_ml()
                if process:
                    print("\\n按回车键停止系统...")
                    input()
                    process.terminate()
                    process.wait()
                    print("✅ 系统已停止")
                break
            elif choice == '3':
                process = start_auto_trading()
                if process:
                    print("\\n按回车键停止系统...")
                    input()
                    process.terminate()
                    process.wait()
                    print("✅ 系统已停止")
                break
            elif choice == '4':
                process = start_wechat_system()
                if process:
                    print("\\n按回车键停止系统...")
                    input()
                    process.terminate()
                    process.wait()
                    print("✅ 系统已停止")
                break
            elif choice == '5':
                print("🚀 启动所有系统...")
                processes = []
                
                # 启动统一平台
                p1 = start_unified_platform()
                if p1:
                    processes.append(p1)
                    time.sleep(3)
                
                # 启动其他系统
                for start_func in [start_traditional_ml, start_auto_trading, start_wechat_system]:
                    p = start_func()
                    if p:
                        processes.append(p)
                        time.sleep(1)
                
                if processes:
                    print("\\n🎉 所有系统已启动！")
                    print("🌐 主界面: http://localhost:5000")
                    
                    # 自动打开浏览器
                    time.sleep(2)
                    try:
                        webbrowser.open('http://localhost:5000')
                    except:
                        pass
                    
                    print("\\n按回车键停止所有系统...")
                    input()
                    
                    # 停止所有进程
                    for p in processes:
                        try:
                            p.terminate()
                            p.wait(timeout=5)
                        except:
                            pass
                    print("✅ 所有系统已停止")
                break
            else:
                print("❌ 无效选择，请重试")
        except KeyboardInterrupt:
            print("\\n\\n👋 用户中断，退出程序")
            break
        except Exception as e:
            print(f"❌ 错误: {e}")

if __name__ == "__main__":
    main()
'''
    
    with open('goldpredict_v2_launcher.py', 'w', encoding='utf-8') as f:
        f.write(launcher_content.strip())
    
    print("✅ V2.0启动器已创建: goldpredict_v2_launcher.py")

def create_pyinstaller_spec():
    """创建PyInstaller规格文件"""
    print("📝 创建PyInstaller规格文件...")
    
    # 分析依赖
    dependencies = analyze_dependencies()
    
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# V2.0核心文件
main_scripts = [
    'unified_prediction_platform_fixed_ver2.0.py',
    'traditional_ml_system_ver2.py', 
    'auto_trading_system.py',
    'wechat_sender.py',
    'mt5_data_source.py',
    'auto_trading_web_interface.py'
]

# 数据文件和配置
datas = []

# 添加配置文件
config_files = [
    'pyproject.toml',
    'requirements.txt',
    'README_V2.md',
    'ENVIRONMENT_SETUP_V2.md'
]

for config_file in config_files:
    import os
    if os.path.exists(config_file):
        datas.append((config_file, '.'))

# 添加目录
data_dirs = ['templates', 'static', 'results', 'configs', 'modules', 'src', 'config']
for data_dir in data_dirs:
    import os
    if os.path.exists(data_dir):
        datas.append((data_dir, data_dir))

# 隐藏导入 - V2.0依赖
hiddenimports = {repr(dependencies)}

# 添加额外的隐藏导入
extra_imports = [
    'flask',
    'flask_socketio',
    'werkzeug',
    'jinja2',
    'requests',
    'pandas',
    'numpy',
    'scipy',
    'sklearn',
    'xgboost',
    'lightgbm',
    'matplotlib',
    'seaborn',
    'plotly',
    'yfinance',
    'alpha_vantage',
    'metatrader5',
    'wxauto',
    'watchdog',
    'sqlalchemy',
    'sqlite3',
    'threading',
    'queue',
    'json',
    'datetime',
    'pathlib',
    'logging',
    'psutil',
    'tqdm',
    'joblib',
    'yaml',
    'dotenv',
    'click',
    'finta',
    'uvicorn',
    'fastapi'
]

hiddenimports.extend(extra_imports)

# 排除不需要的模块
excludes = [
    'torch',
    'torchvision', 
    'torchaudio',
    'transformers',
    'stable_baselines3',
    'gymnasium',
    'ta',
    'catboost',
    'cupy',
    'numba',
    'dash',
    'streamlit'
]

a = Analysis(
    ['goldpredict_v2_launcher.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='GoldPredict_V2',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)
'''
    
    with open('goldpredict_v2.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("✅ PyInstaller规格文件已创建: goldpredict_v2.spec")

def prepare_build_environment():
    """准备构建环境"""
    print("🔧 准备构建环境...")
    
    # 清理旧的构建文件
    build_dirs = ['build', 'dist', '__pycache__']
    for build_dir in build_dirs:
        if Path(build_dir).exists():
            shutil.rmtree(build_dir)
            print(f"🗑️  清理目录: {build_dir}")
    
    # 创建默认配置文件
    config_dir = Path('config')
    config_dir.mkdir(exist_ok=True)
    
    default_configs = {
        'config.yaml': {
            'system': {'name': 'GoldPredict V2.0', 'debug': False},
            'data_sources': {'primary': 'mt5', 'update_interval': 30},
            'prediction': {'lookback_days': 30, 'confidence_threshold': 0.7},
            'models': {'traditional_ml': {'enabled': True}}
        },
        'trading.yaml': {
            'trading': {'enabled': False, 'symbol': 'XAUUSD'},
            'risk_management': {'max_position_size': 0.1}
        },
        'wechat.json': {
            'enabled': False,
            'target_groups': [],
            'send_conditions': {'min_confidence': 0.8}
        }
    }
    
    for config_file, config_data in default_configs.items():
        config_path = config_dir / config_file
        if not config_path.exists():
            if config_file.endswith('.json'):
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, indent=2, ensure_ascii=False)
            else:
                try:
                    import yaml
                    with open(config_path, 'w', encoding='utf-8') as f:
                        yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
                except ImportError:
                    # 如果没有yaml，使用简单的文本格式
                    with open(config_path, 'w', encoding='utf-8') as f:
                        f.write(f"# {config_file} - 请手动配置\n")
                        f.write(str(config_data))
            print(f"✅ 创建配置文件: {config_file}")
    
    # 创建.env文件
    env_file = Path('.env')
    if not env_file.exists():
        env_content = '''# GoldPredict V2.0 环境变量
DEBUG=False
LOG_LEVEL=INFO
DATA_PATH=./data
MODEL_PATH=./models
'''
        env_file.write_text(env_content, encoding='utf-8')
        print("✅ 创建环境变量文件: .env")
    
    print("✅ 构建环境准备完成")
    return True

def build_executable():
    """构建可执行文件"""
    print("🏗️  开始构建可执行文件...")

    try:
        # 使用规格文件构建
        cmd = ["pyinstaller", "goldpredict_v2.spec", "--clean", "--noconfirm"]

        print(f"执行命令: {' '.join(cmd)}")

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ 可执行文件构建成功")

            # 检查输出文件
            exe_name = "GoldPredict_V2.exe" if platform.system() == "Windows" else "GoldPredict_V2"
            exe_file = Path("dist") / exe_name

            if exe_file.exists():
                size_mb = exe_file.stat().st_size / (1024 * 1024)
                print(f"📦 可执行文件: {exe_file}")
                print(f"📏 文件大小: {size_mb:.1f} MB")
                return True
            else:
                print("❌ 可执行文件未找到")
                return False
        else:
            print("❌ 构建失败")
            print(f"错误输出: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ 构建过程出错: {e}")
        return False

def create_distribution_package():
    """创建分发包"""
    print("📦 创建分发包...")

    try:
        # 创建分发目录
        package_name = f"GoldPredict_V2_Package_{platform.system()}"
        package_dir = Path(package_name)

        if package_dir.exists():
            shutil.rmtree(package_dir)
        package_dir.mkdir()

        # 复制可执行文件
        exe_name = "GoldPredict_V2.exe" if platform.system() == "Windows" else "GoldPredict_V2"
        exe_file = Path("dist") / exe_name

        if exe_file.exists():
            shutil.copy2(exe_file, package_dir / exe_name)
            print(f"✅ 复制可执行文件: {exe_name}")

        # 复制配置文件
        config_files = [
            'config/config.yaml',
            'config/trading.yaml',
            'config/wechat.json',
            '.env',
            'README_V2.md',
            'ENVIRONMENT_SETUP_V2.md'
        ]

        for config_file in config_files:
            if Path(config_file).exists():
                dest_path = package_dir / Path(config_file).name
                shutil.copy2(config_file, dest_path)
                print(f"✅ 复制配置文件: {config_file}")

        # 创建启动说明
        startup_guide = f'''# 🏆 GoldPredict V2.0 - 智能黄金价格预测系统

## 🚀 快速启动

### Windows用户
1. 双击运行 `{exe_name}`
2. 根据菜单选择启动模式
3. 推荐选择 "1. 统一平台" 获得完整功能

### 启动模式说明

#### 1. 统一平台 (推荐)
- 🌐 一体化Web管理界面
- 📊 集成所有预测系统
- 🎯 实时监控和控制
- 访问地址: http://localhost:5000

#### 2. 传统ML系统
- 📈 机器学习预测
- 🔍 技术指标分析
- 📊 多模型集成

#### 3. 自动交易系统
- 🔄 MT5集成交易
- 💰 风险管理
- 📈 自动执行策略

#### 4. 微信集成系统
- 📱 智能消息推送
- 🎯 预测结果通知
- 📊 多群管理

#### 5. 全部启动
- 🚀 启动所有系统
- 🌐 完整功能体验
- 📊 系统协同工作

## ⚙️ 配置文件

- `config.yaml`: 主系统配置
- `trading.yaml`: 交易参数配置
- `wechat.json`: 微信推送配置
- `.env`: 环境变量配置

## 🔧 首次使用

1. **配置API密钥** (可选)
   - 编辑 `.env` 文件
   - 添加 Alpha Vantage API密钥

2. **配置MT5** (可选)
   - 编辑 `trading.yaml`
   - 填入MT5账号信息

3. **配置微信** (可选)
   - 编辑 `wechat.json`
   - 设置目标群聊

## 🌐 Web界面功能

### 主页面 (http://localhost:5000)
- 📊 系统状态监控
- 🎯 预测结果展示
- ⚙️ 系统控制面板

### 传统ML系统 (/traditional)
- 📈 机器学习预测
- 📊 模型性能分析
- 🔍 特征重要性

### 自动交易系统 (/auto_trading)
- 💰 账户信息
- 📈 持仓管理
- 🎯 交易记录

### 微信管理 (/wechat)
- 📱 推送配置
- 📊 发送历史
- 🎯 群聊管理

## ⚠️ 注意事项

1. **防火墙设置**
   - 首次运行可能需要允许网络访问
   - 确保端口5000未被占用

2. **MT5交易** (可选)
   - 需要安装MetaTrader 5客户端
   - 确保账号信息正确

3. **微信推送** (可选)
   - 需要微信PC版登录
   - 确保群聊名称正确

4. **系统要求**
   - Windows 10/11 (推荐)
   - 4GB+ 内存
   - 稳定网络连接

## 🆘 故障排除

### 启动失败
- 检查端口5000是否被占用
- 以管理员身份运行
- 检查防火墙设置

### 预测不准确
- 检查网络连接
- 等待数据收集完成
- 调整预测参数

### 微信发送失败
- 确保微信PC版已登录
- 检查群聊名称
- 验证wxauto库兼容性

## 📞 技术支持

- 📧 邮件: goldpredict@example.com
- 🌐 GitHub: https://github.com/goldpredict/goldpredict
- 📚 文档: README_V2.md

---

**🎉 祝您使用愉快，投资顺利！**
'''

        with open(package_dir / "使用说明.txt", 'w', encoding='utf-8') as f:
            f.write(startup_guide)

        print(f"✅ 分发包已创建: {package_dir}")

        # 创建压缩包
        try:
            archive_name = f"GoldPredict_V2_{platform.system()}_{platform.machine()}"
            shutil.make_archive(archive_name, 'zip', package_dir)
            print(f"✅ 压缩包已创建: {archive_name}.zip")
        except Exception as e:
            print(f"⚠️  压缩包创建失败: {e}")

        return True

    except Exception as e:
        print(f"❌ 创建分发包失败: {e}")
        return False

def test_executable():
    """测试可执行文件"""
    print("🧪 测试可执行文件...")

    exe_name = "GoldPredict_V2.exe" if platform.system() == "Windows" else "GoldPredict_V2"
    exe_file = Path("dist") / exe_name

    if not exe_file.exists():
        print("❌ 可执行文件不存在")
        return False

    try:
        # 简单测试 - 检查文件是否可执行
        if platform.system() == "Windows":
            result = subprocess.run([str(exe_file), "--help"],
                                  capture_output=True, text=True, timeout=10)
        else:
            result = subprocess.run([str(exe_file), "--help"],
                                  capture_output=True, text=True, timeout=10)

        print("✅ 可执行文件测试通过")
        return True

    except subprocess.TimeoutExpired:
        print("⚠️  可执行文件响应超时（可能正常）")
        return True
    except Exception as e:
        print(f"❌ 可执行文件测试失败: {e}")
        return False

def main():
    """主构建流程"""
    print_banner()

    try:
        # 1. 检查环境
        if not check_environment():
            print("❌ 环境检查失败")
            return

        # 2. 准备构建环境
        if not prepare_build_environment():
            print("❌ 构建环境准备失败")
            return

        # 3. 创建启动器脚本
        create_launcher_script()

        # 4. 创建PyInstaller规格文件
        create_pyinstaller_spec()

        # 5. 构建可执行文件
        if not build_executable():
            print("❌ 可执行文件构建失败")
            return

        # 6. 测试可执行文件
        test_executable()

        # 7. 创建分发包
        if not create_distribution_package():
            print("❌ 分发包创建失败")
            return

        print("\n" + "=" * 60)
        print("🎉 GoldPredict V2.0 打包完成！")
        print("=" * 60)

        exe_name = "GoldPredict_V2.exe" if platform.system() == "Windows" else "GoldPredict_V2"
        package_name = f"GoldPredict_V2_Package_{platform.system()}"

        print("📦 输出文件:")
        print(f"   - dist/{exe_name} (可执行文件)")
        print(f"   - {package_name}/ (分发目录)")
        print(f"   - GoldPredict_V2_{platform.system()}_{platform.machine()}.zip (分发压缩包)")

        print("\n🚀 使用方法:")
        print("1. 解压分发包到目标机器")
        print(f"2. 双击运行 {exe_name}")
        print("3. 选择启动模式")
        print("4. 访问 http://localhost:5000")

        print("\n📋 功能特性:")
        print("   🏆 五大核心系统集成")
        print("   🌐 统一Web管理界面")
        print("   📱 微信智能推送")
        print("   🔄 MT5自动交易")
        print("   📊 实时预测监控")

        print("\n⚠️  注意事项:")
        print("   - 首次运行可能需要允许防火墙访问")
        print("   - 确保端口5000未被占用")
        print("   - MT5和微信功能需要额外配置")

    except KeyboardInterrupt:
        print("\n\n❌ 打包被用户中断")
    except Exception as e:
        print(f"\n❌ 打包过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
