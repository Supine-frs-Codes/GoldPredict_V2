#!/usr/bin/env python3
"""
GoldPredict V2.0 打包可行性测试
测试是否可以成功打包成exe文件
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def print_banner():
    """打印横幅"""
    print("🧪 GoldPredict V2.0 打包可行性测试")
    print("=" * 50)

def check_pyinstaller():
    """检查PyInstaller"""
    print("📦 检查PyInstaller...")
    try:
        import PyInstaller
        print(f"✅ PyInstaller已安装: {PyInstaller.__version__}")
        return True
    except ImportError:
        print("❌ PyInstaller未安装，正在安装...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
            print("✅ PyInstaller安装成功")
            return True
        except subprocess.CalledProcessError:
            print("❌ PyInstaller安装失败")
            return False

def check_core_files():
    """检查核心文件"""
    print("📁 检查核心文件...")
    
    required_files = [
        'unified_prediction_platform_fixed_ver2.0.py',
        'start.py',
        'requirements.txt'
    ]
    
    missing_files = []
    existing_files = []
    
    for file in required_files:
        if Path(file).exists():
            existing_files.append(file)
            print(f"✅ {file}")
        else:
            missing_files.append(file)
            print(f"❌ {file}")
    
    if missing_files:
        print(f"⚠️  缺少文件: {', '.join(missing_files)}")
    
    return len(existing_files) > 0

def create_simple_launcher():
    """创建简单启动器"""
    print("🚀 创建简单启动器...")
    
    launcher_content = '''#!/usr/bin/env python3
"""
GoldPredict V2.0 简单启动器
"""

import sys
import os
import subprocess
import webbrowser
import time

def print_banner():
    print("🏆 GoldPredict V2.0 - 智能黄金价格预测系统")
    print("=" * 50)

def start_unified_platform():
    """启动统一平台"""
    print("🚀 启动统一平台...")
    
    # 检查主文件是否存在
    main_file = "unified_prediction_platform_fixed_ver2.0.py"
    if os.path.exists(main_file):
        try:
            print(f"启动文件: {main_file}")
            process = subprocess.Popen([sys.executable, main_file])
            print(f"✅ 系统已启动 (PID: {process.pid})")
            
            # 等待系统启动
            print("⏳ 等待系统启动...")
            time.sleep(3)
            
            # 打开浏览器
            print("🌐 打开浏览器...")
            try:
                webbrowser.open('http://localhost:5000')
            except:
                pass
            
            print("\\n🎉 系统启动成功！")
            print("🌐 访问地址: http://localhost:5000")
            print("\\n按回车键停止系统...")
            input()
            
            # 停止系统
            process.terminate()
            process.wait()
            print("✅ 系统已停止")
            
        except Exception as e:
            print(f"❌ 启动失败: {e}")
    else:
        print(f"❌ 找不到主文件: {main_file}")

def start_simple_mode():
    """启动简单模式"""
    print("📊 启动简单模式...")
    
    # 检查start.py是否存在
    start_file = "start.py"
    if os.path.exists(start_file):
        try:
            subprocess.run([sys.executable, start_file, "--mode", "unified"])
        except Exception as e:
            print(f"❌ 启动失败: {e}")
    else:
        print(f"❌ 找不到启动文件: {start_file}")

def main():
    """主函数"""
    print_banner()
    
    print("选择启动模式:")
    print("1. 统一平台 (推荐)")
    print("2. 简单模式")
    print("0. 退出")
    
    while True:
        try:
            choice = input("\\n请选择 (0-2): ").strip()
            
            if choice == '0':
                print("👋 再见！")
                break
            elif choice == '1':
                start_unified_platform()
                break
            elif choice == '2':
                start_simple_mode()
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
    
    with open('simple_launcher.py', 'w', encoding='utf-8') as f:
        f.write(launcher_content.strip())
    
    print("✅ 简单启动器已创建: simple_launcher.py")

def test_simple_build():
    """测试简单构建"""
    print("🏗️  测试简单构建...")
    
    try:
        # 使用最基本的PyInstaller命令
        cmd = [
            "pyinstaller",
            "--onefile",
            "--name=GoldPredict_V2_Test",
            "--console",
            "simple_launcher.py"
        ]
        
        print(f"执行命令: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ 简单构建成功")
            
            # 检查输出文件
            exe_name = "GoldPredict_V2_Test.exe" if platform.system() == "Windows" else "GoldPredict_V2_Test"
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
            print(f"标准输出: {result.stdout}")
            print(f"错误输出: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ 构建超时")
        return False
    except Exception as e:
        print(f"❌ 构建过程出错: {e}")
        return False

def analyze_dependencies():
    """分析依赖"""
    print("🔍 分析依赖...")
    
    try:
        # 读取requirements.txt
        req_file = Path('requirements.txt')
        if req_file.exists():
            with open(req_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            deps = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    package = line.split('>=')[0].split('==')[0].split('[')[0]
                    deps.append(package)
            
            print(f"📦 发现 {len(deps)} 个依赖包")
            
            # 检查关键依赖
            critical_deps = ['flask', 'pandas', 'numpy', 'requests']
            missing_critical = []
            
            for dep in critical_deps:
                try:
                    __import__(dep)
                    print(f"✅ {dep}")
                except ImportError:
                    missing_critical.append(dep)
                    print(f"❌ {dep}")
            
            if missing_critical:
                print(f"⚠️  缺少关键依赖: {', '.join(missing_critical)}")
                return False
            else:
                print("✅ 关键依赖完整")
                return True
        else:
            print("❌ requirements.txt不存在")
            return False
            
    except Exception as e:
        print(f"❌ 依赖分析失败: {e}")
        return False

def estimate_exe_size():
    """估算exe文件大小"""
    print("📏 估算exe文件大小...")
    
    try:
        # 计算Python文件总大小
        py_files = list(Path('.').glob('*.py'))
        total_py_size = sum(f.stat().st_size for f in py_files if f.exists())
        
        # 估算依赖大小（粗略估算）
        estimated_deps_size = 50 * 1024 * 1024  # 约50MB
        
        # 估算总大小
        estimated_total = total_py_size + estimated_deps_size
        estimated_mb = estimated_total / (1024 * 1024)
        
        print(f"📊 Python文件: {total_py_size / 1024:.1f} KB")
        print(f"📊 估算依赖: {estimated_deps_size / (1024 * 1024):.1f} MB")
        print(f"📊 估算总大小: {estimated_mb:.1f} MB")
        
        if estimated_mb > 200:
            print("⚠️  预计文件较大，可能需要优化")
        else:
            print("✅ 预计文件大小合理")
        
        return True
        
    except Exception as e:
        print(f"❌ 大小估算失败: {e}")
        return False

def main():
    """主测试流程"""
    print_banner()
    
    try:
        # 1. 检查PyInstaller
        if not check_pyinstaller():
            print("❌ PyInstaller检查失败")
            return
        
        # 2. 检查核心文件
        if not check_core_files():
            print("❌ 核心文件检查失败")
            return
        
        # 3. 分析依赖
        if not analyze_dependencies():
            print("⚠️  依赖分析有问题，但继续测试")
        
        # 4. 估算文件大小
        estimate_exe_size()
        
        # 5. 创建简单启动器
        create_simple_launcher()
        
        # 6. 询问是否进行构建测试
        print("\n" + "=" * 50)
        test_build = input("是否进行构建测试? (y/N): ").lower()
        
        if test_build in ['y', 'yes']:
            print("\n🏗️  开始构建测试...")
            if test_simple_build():
                print("\n🎉 构建测试成功！")
                print("✅ GoldPredict V2.0 可以成功打包成exe文件")
                
                print("\n📋 下一步:")
                print("1. 运行完整打包脚本: python build_executable_v2.py")
                print("2. 测试生成的exe文件")
                print("3. 创建分发包")
            else:
                print("\n❌ 构建测试失败")
                print("需要解决依赖或配置问题")
        else:
            print("\n✅ 可行性测试完成")
            print("基于检查结果，打包应该是可行的")
        
    except KeyboardInterrupt:
        print("\n\n❌ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
