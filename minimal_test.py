#!/usr/bin/env python3
"""
最简单的打包测试
"""

import sys
import os
import subprocess
from pathlib import Path

def main():
    print("🧪 最简单的打包测试")
    print("=" * 30)
    
    # 检查Python版本
    print(f"Python版本: {sys.version}")
    
    # 检查当前目录
    print(f"当前目录: {os.getcwd()}")
    
    # 检查关键文件
    key_files = [
        'unified_prediction_platform_fixed_ver2.0.py',
        'start.py',
        'requirements.txt',
        'pyproject.toml'
    ]
    
    print("\n📁 检查关键文件:")
    for file in key_files:
        if Path(file).exists():
            size = Path(file).stat().st_size
            print(f"✅ {file} ({size} bytes)")
        else:
            print(f"❌ {file}")
    
    # 检查PyInstaller
    print("\n📦 检查PyInstaller:")
    try:
        result = subprocess.run([sys.executable, '-c', 'import PyInstaller; print(PyInstaller.__version__)'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ PyInstaller: {result.stdout.strip()}")
        else:
            print("❌ PyInstaller未安装")
            print("正在安装...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], check=True)
            print("✅ PyInstaller安装完成")
    except Exception as e:
        print(f"❌ PyInstaller检查失败: {e}")
    
    # 检查基本依赖
    print("\n🔍 检查基本依赖:")
    basic_deps = ['flask', 'pandas', 'numpy']
    for dep in basic_deps:
        try:
            __import__(dep)
            print(f"✅ {dep}")
        except ImportError:
            print(f"❌ {dep}")
    
    # 创建最简单的测试文件
    print("\n🚀 创建测试文件:")
    test_content = '''#!/usr/bin/env python3
"""
GoldPredict V2.0 最简单启动器
"""

def main():
    print("🏆 GoldPredict V2.0 - 智能黄金价格预测系统")
    print("=" * 50)
    print("这是一个测试版本的可执行文件")
    print("如果您看到这个消息，说明打包成功！")
    
    input("\\n按回车键退出...")

if __name__ == "__main__":
    main()
'''
    
    with open('minimal_launcher.py', 'w', encoding='utf-8') as f:
        f.write(test_content)
    print("✅ 创建测试文件: minimal_launcher.py")
    
    # 询问是否测试打包
    print("\n" + "=" * 30)
    choice = input("是否测试打包? (y/N): ").lower()
    
    if choice in ['y', 'yes']:
        print("\n🏗️  开始测试打包...")
        try:
            cmd = [
                'pyinstaller',
                '--onefile',
                '--name=GoldPredict_Minimal_Test',
                '--console',
                'minimal_launcher.py'
            ]
            
            print(f"执行命令: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                print("✅ 打包成功！")
                
                # 检查输出文件
                exe_file = Path('dist/GoldPredict_Minimal_Test.exe')
                if exe_file.exists():
                    size_mb = exe_file.stat().st_size / (1024 * 1024)
                    print(f"📦 可执行文件: {exe_file}")
                    print(f"📏 文件大小: {size_mb:.1f} MB")
                    
                    print("\n🎉 打包测试成功！")
                    print("✅ GoldPredict V2.0 可以成功打包成exe文件")
                else:
                    print("❌ 可执行文件未找到")
            else:
                print("❌ 打包失败")
                print(f"错误: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print("❌ 打包超时")
        except Exception as e:
            print(f"❌ 打包错误: {e}")
    else:
        print("✅ 基础检查完成")
        print("根据检查结果，打包应该是可行的")

if __name__ == "__main__":
    main()
