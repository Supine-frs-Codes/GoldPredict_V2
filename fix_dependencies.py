#!/usr/bin/env python3
"""
GoldPredict V2.0 依赖修复脚本
自动检测和安装缺失的依赖包
"""

import sys
import subprocess
import importlib
from pathlib import Path

def print_banner():
    """打印横幅"""
    print("🔧 GoldPredict V2.0 依赖修复工具")
    print("=" * 40)

def check_and_install_package(package_name, import_name=None):
    """检查并安装单个包"""
    if import_name is None:
        import_name = package_name
    
    try:
        # 尝试导入包
        importlib.import_module(import_name)
        print(f"✅ {package_name}: 已安装")
        return True
    except ImportError:
        print(f"❌ {package_name}: 未安装，正在安装...")
        try:
            # 安装包
            subprocess.run([sys.executable, "-m", "pip", "install", package_name], 
                         check=True, capture_output=True)
            print(f"✅ {package_name}: 安装成功")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ {package_name}: 安装失败 - {e}")
            return False

def install_core_dependencies():
    """安装核心依赖"""
    print("\n📦 安装核心依赖包...")
    
    # 核心依赖列表 (包名, 导入名)
    core_deps = [
        ("flask", "flask"),
        ("pandas", "pandas"),
        ("numpy", "numpy"),
        ("scipy", "scipy"),
        ("requests", "requests"),
        ("scikit-learn", "sklearn"),
        ("matplotlib", "matplotlib"),
        ("seaborn", "seaborn"),
        ("plotly", "plotly"),
        ("yfinance", "yfinance"),
        ("beautifulsoup4", "bs4"),
        ("tqdm", "tqdm"),
        ("joblib", "joblib"),
        ("python-dotenv", "dotenv"),
        ("pyyaml", "yaml"),
        ("click", "click"),
        ("psutil", "psutil"),
        ("python-dateutil", "dateutil"),
        ("jinja2", "jinja2"),
        ("werkzeug", "werkzeug"),
        ("sqlalchemy", "sqlalchemy"),
    ]
    
    success_count = 0
    failed_packages = []
    
    for package, import_name in core_deps:
        if check_and_install_package(package, import_name):
            success_count += 1
        else:
            failed_packages.append(package)
    
    print(f"\n📊 核心依赖安装结果:")
    print(f"✅ 成功: {success_count}/{len(core_deps)}")
    if failed_packages:
        print(f"❌ 失败: {', '.join(failed_packages)}")
    
    return len(failed_packages) == 0

def install_ml_dependencies():
    """安装机器学习依赖"""
    print("\n🤖 安装机器学习依赖...")
    
    ml_deps = [
        ("xgboost", "xgboost"),
        ("lightgbm", "lightgbm"),
        ("finta", "finta"),
    ]
    
    success_count = 0
    for package, import_name in ml_deps:
        if check_and_install_package(package, import_name):
            success_count += 1
    
    print(f"✅ ML依赖安装完成: {success_count}/{len(ml_deps)}")
    return success_count == len(ml_deps)

def install_optional_dependencies():
    """安装可选依赖"""
    print("\n⚙️ 安装可选依赖...")
    
    # 询问用户是否安装可选依赖
    install_optional = input("是否安装可选依赖? (MT5, 微信集成等) [y/N]: ").lower()
    
    if install_optional not in ['y', 'yes']:
        print("⏭️ 跳过可选依赖安装")
        return True
    
    optional_deps = [
        ("metatrader5", "MetaTrader5"),
        ("watchdog", "watchdog"),
        ("wxauto", "wxauto"),
        ("flask-socketio", "flask_socketio"),
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
        ("alpha-vantage", "alpha_vantage"),
    ]
    
    success_count = 0
    for package, import_name in optional_deps:
        if check_and_install_package(package, import_name):
            success_count += 1
    
    print(f"✅ 可选依赖安装完成: {success_count}/{len(optional_deps)}")
    return True

def install_from_requirements():
    """从requirements.txt安装依赖"""
    print("\n📄 从requirements.txt安装依赖...")
    
    req_file = Path('requirements.txt')
    if not req_file.exists():
        print("❌ requirements.txt文件不存在")
        return False
    
    try:
        print("正在执行: pip install -r requirements.txt")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ requirements.txt安装成功")
            return True
        else:
            print("❌ requirements.txt安装失败")
            print(f"错误信息: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ 安装超时")
        return False
    except Exception as e:
        print(f"❌ 安装过程出错: {e}")
        return False

def verify_installation():
    """验证安装结果"""
    print("\n🧪 验证安装结果...")
    
    # 关键依赖验证
    critical_packages = [
        ("flask", "flask"),
        ("pandas", "pandas"), 
        ("numpy", "numpy"),
        ("requests", "requests"),
        ("sklearn", "scikit-learn"),
        ("matplotlib", "matplotlib")
    ]
    
    all_good = True
    for import_name, package_name in critical_packages:
        try:
            module = importlib.import_module(import_name)
            version = getattr(module, '__version__', 'unknown')
            print(f"✅ {package_name}: {version}")
        except ImportError:
            print(f"❌ {package_name}: 仍然缺失")
            all_good = False
    
    return all_good

def update_pip():
    """更新pip"""
    print("🔄 更新pip...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                      check=True, capture_output=True)
        print("✅ pip更新成功")
        return True
    except subprocess.CalledProcessError:
        print("⚠️ pip更新失败，但继续安装")
        return False

def main():
    """主修复流程"""
    print_banner()
    
    try:
        # 1. 更新pip
        update_pip()
        
        # 2. 选择安装方式
        print("\n🎯 选择依赖安装方式:")
        print("1. 从requirements.txt安装 (推荐)")
        print("2. 逐个安装核心依赖")
        print("3. 完整安装 (核心+ML+可选)")
        
        choice = input("\n请选择 (1-3): ").strip()
        
        if choice == '1':
            # 从requirements.txt安装
            success = install_from_requirements()
            
        elif choice == '2':
            # 逐个安装核心依赖
            success = install_core_dependencies()
            
        elif choice == '3':
            # 完整安装
            success1 = install_core_dependencies()
            success2 = install_ml_dependencies()
            success3 = install_optional_dependencies()
            success = success1 and success2 and success3
            
        else:
            print("❌ 无效选择")
            return
        
        # 3. 验证安装
        print("\n" + "=" * 40)
        if verify_installation():
            print("🎉 依赖修复完成！")
            print("✅ 所有关键依赖已正确安装")
            
            # 询问是否重新运行打包测试
            retest = input("\n是否重新运行打包测试? [y/N]: ").lower()
            if retest in ['y', 'yes']:
                print("\n🧪 重新运行打包测试...")
                try:
                    subprocess.run([sys.executable, "test_packaging.py"], check=True)
                except subprocess.CalledProcessError:
                    print("❌ 打包测试运行失败")
                except FileNotFoundError:
                    print("❌ 找不到test_packaging.py文件")
        else:
            print("❌ 依赖修复未完全成功")
            print("请检查错误信息并手动安装缺失的包")
            
    except KeyboardInterrupt:
        print("\n\n❌ 修复被用户中断")
    except Exception as e:
        print(f"\n❌ 修复过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
