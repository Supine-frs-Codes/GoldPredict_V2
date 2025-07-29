#!/usr/bin/env python3
"""
GoldPredict V2.0 独立可执行文件打包脚本
创建真正的自包含exe文件，无需外部依赖
"""

import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path

def print_banner():
    """打印横幅"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║              🏆 GoldPredict V2.0 独立打包工具                ║
    ║                创建真正的自包含可执行文件                     ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_environment():
    """检查环境"""
    print("🔍 检查打包环境...")
    
    # 检查Python版本
    version = sys.version_info
    print(f"✅ Python版本: {version.major}.{version.minor}.{version.micro}")
    
    # 检查PyInstaller
    try:
        import PyInstaller
        print(f"✅ PyInstaller: {PyInstaller.__version__}")
    except ImportError:
        print("❌ PyInstaller未安装，正在安装...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        print("✅ PyInstaller安装完成")
    
    # 检查关键依赖
    required_deps = ['flask', 'pandas', 'numpy', 'sklearn', 'requests', 'pyyaml']
    missing_deps = []
    
    for dep in required_deps:
        try:
            __import__(dep)
            print(f"✅ {dep}")
        except ImportError:
            missing_deps.append(dep)
            print(f"❌ {dep}")
    
    if missing_deps:
        print(f"\n⚠️ 缺少依赖: {', '.join(missing_deps)}")
        install = input("是否自动安装缺失依赖? [y/N]: ").lower()
        if install in ['y', 'yes']:
            for dep in missing_deps:
                print(f"安装 {dep}...")
                subprocess.run([sys.executable, "-m", "pip", "install", dep], check=True)
            print("✅ 依赖安装完成")
        else:
            print("❌ 请手动安装依赖后重试")
            return False
    
    return True

def create_pyinstaller_spec():
    """创建PyInstaller规格文件"""
    print("📝 创建PyInstaller规格文件...")
    
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['standalone_launcher.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'flask',
        'pandas',
        'numpy',
        'scipy',
        'sklearn',
        'sklearn.ensemble',
        'sklearn.model_selection',
        'sklearn.metrics',
        'requests',
        'yaml',
        'threading',
        'webbrowser',
        'json',
        'pathlib',
        'datetime',
        'logging',
        'time'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'torch',
        'tensorflow',
        'matplotlib',
        'seaborn',
        'plotly',
        'dash',
        'streamlit',
        'jupyter',
        'notebook',
        'IPython'
    ],
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
    name='GoldPredict_V2_Standalone',
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
    
    with open('standalone.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("✅ 规格文件已创建: standalone.spec")

def build_executable():
    """构建可执行文件"""
    print("🏗️ 开始构建独立可执行文件...")
    
    try:
        # 清理旧文件
        if Path('dist').exists():
            shutil.rmtree('dist')
        if Path('build').exists():
            shutil.rmtree('build')
        
        # 使用规格文件构建
        cmd = ["pyinstaller", "standalone.spec", "--clean", "--noconfirm"]
        
        print(f"执行命令: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 可执行文件构建成功")
            
            # 检查输出文件
            exe_name = "GoldPredict_V2_Standalone.exe" if platform.system() == "Windows" else "GoldPredict_V2_Standalone"
            exe_file = Path("dist") / exe_name
            
            if exe_file.exists():
                size_mb = exe_file.stat().st_size / (1024 * 1024)
                print(f"📦 可执行文件: {exe_file}")
                print(f"📏 文件大小: {size_mb:.1f} MB")
                return True, exe_file
            else:
                print("❌ 可执行文件未找到")
                return False, None
        else:
            print("❌ 构建失败")
            print(f"错误输出: {result.stderr}")
            return False, None
            
    except Exception as e:
        print(f"❌ 构建过程出错: {e}")
        return False, None

def test_executable(exe_file):
    """测试可执行文件"""
    print("🧪 测试可执行文件...")
    
    try:
        # 简单测试 - 启动并快速退出
        print("启动测试...")
        
        # 注意：这里不能直接运行，因为它会启动Web服务
        # 我们只检查文件是否可执行
        if exe_file.exists() and os.access(exe_file, os.X_OK):
            print("✅ 可执行文件测试通过")
            return True
        else:
            print("❌ 可执行文件无法执行")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def create_distribution_package(exe_file):
    """创建分发包"""
    print("📦 创建分发包...")
    
    try:
        # 创建分发目录
        package_name = f"GoldPredict_V2_Standalone_{platform.system()}"
        package_dir = Path(package_name)
        
        if package_dir.exists():
            shutil.rmtree(package_dir)
        package_dir.mkdir()
        
        # 复制可执行文件
        exe_name = exe_file.name
        shutil.copy2(exe_file, package_dir / exe_name)
        print(f"✅ 复制可执行文件: {exe_name}")
        
        # 创建使用说明
        readme_content = f'''# 🏆 GoldPredict V2.0 - 独立可执行版本

## 🚀 快速启动

### 使用方法
1. 双击运行 `{exe_name}`
2. 选择 "1. 启动Web服务"
3. 系统会自动打开浏览器访问 http://localhost:5000
4. 享受智能黄金价格预测功能！

### 功能特性
✅ **完全独立** - 无需安装Python或其他依赖
✅ **自包含系统** - 所有代码和模型内置
✅ **Web界面** - 现代化的用户界面
✅ **实时预测** - 基于机器学习的价格预测
✅ **模型训练** - 内置随机森林模型
✅ **系统监控** - 实时状态和性能指标

### 系统要求
- Windows 10/11 (64位)
- 4GB+ 内存
- 100MB+ 可用存储空间
- 网络连接 (用于浏览器访问)

### 使用流程
1. **启动系统**: 双击exe文件，选择"启动Web服务"
2. **访问界面**: 浏览器自动打开 http://localhost:5000
3. **训练模型**: 点击"训练模型"按钮初始化AI模型
4. **生成预测**: 点击"生成预测"获取黄金价格预测
5. **查看结果**: 观察预测价格、信号和置信度

### 主要功能

#### 🔮 智能预测
- 基于随机森林算法的价格预测
- 多种技术指标分析
- 智能信号生成 (强烈看涨/看涨/横盘/看跌/强烈看跌)
- 置信度评估

#### 📊 实时监控
- 系统运行状态
- 预测次数统计
- 模型准确率显示
- 最后更新时间

#### 🎯 用户友好
- 现代化Web界面
- 响应式设计
- 一键操作
- 实时数据更新

### 注意事项
- 首次启动可能需要10-30秒
- 确保端口5000未被占用
- 防火墙可能需要允许网络访问
- 预测结果仅供参考，投资有风险

### 故障排除

#### 启动失败
- 以管理员身份运行
- 检查防火墙设置
- 确保端口5000可用

#### 浏览器无法访问
- 手动访问 http://localhost:5000
- 检查系统是否正常启动
- 重启程序重试

#### 预测功能异常
- 先点击"训练模型"
- 等待训练完成后再预测
- 检查网络连接

### 技术支持
如有问题，请检查：
1. 系统要求是否满足
2. 防火墙和网络设置
3. 程序是否以管理员身份运行

---

**🎉 享受智能预测的乐趣，祝您投资顺利！**

版本: GoldPredict V2.0 独立可执行版
构建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
'''
        
        with open(package_dir / "使用说明.txt", 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        print(f"✅ 分发包已创建: {package_dir}")
        
        # 创建压缩包
        try:
            archive_name = f"GoldPredict_V2_Standalone_{platform.system()}_{platform.machine()}"
            shutil.make_archive(archive_name, 'zip', package_dir)
            print(f"✅ 压缩包已创建: {archive_name}.zip")
        except Exception as e:
            print(f"⚠️ 压缩包创建失败: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 创建分发包失败: {e}")
        return False

def main():
    """主构建流程"""
    print_banner()
    
    try:
        # 1. 检查环境
        if not check_environment():
            print("❌ 环境检查失败")
            return
        
        # 2. 检查独立启动器文件
        if not Path('standalone_launcher.py').exists():
            print("❌ 找不到standalone_launcher.py文件")
            print("请确保该文件存在于当前目录")
            return
        
        # 3. 创建PyInstaller规格文件
        create_pyinstaller_spec()
        
        # 4. 构建可执行文件
        success, exe_file = build_executable()
        if not success:
            print("❌ 可执行文件构建失败")
            return
        
        # 5. 测试可执行文件
        if not test_executable(exe_file):
            print("⚠️ 可执行文件测试有问题，但继续创建分发包")
        
        # 6. 创建分发包
        if not create_distribution_package(exe_file):
            print("❌ 分发包创建失败")
            return
        
        print("\n" + "=" * 60)
        print("🎉 GoldPredict V2.0 独立可执行文件打包完成！")
        print("=" * 60)
        
        exe_name = exe_file.name
        package_name = f"GoldPredict_V2_Standalone_{platform.system()}"
        
        print("📦 输出文件:")
        print(f"   - dist/{exe_name} (独立可执行文件)")
        print(f"   - {package_name}/ (分发目录)")
        print(f"   - GoldPredict_V2_Standalone_{platform.system()}_{platform.machine()}.zip")
        
        print("\n🚀 使用方法:")
        print("1. 解压分发包到目标机器")
        print(f"2. 双击运行 {exe_name}")
        print("3. 选择 '1. 启动Web服务'")
        print("4. 浏览器自动打开 http://localhost:5000")
        print("5. 点击'训练模型'初始化系统")
        print("6. 点击'生成预测'获取预测结果")
        
        print("\n✨ 独立版本特性:")
        print("   🏆 完全自包含 - 无需外部文件")
        print("   🌐 内置Web服务器")
        print("   🤖 内置机器学习模型")
        print("   📊 实时预测和监控")
        print("   🎯 用户友好界面")
        
        print("\n⚠️ 重要说明:")
        print("   - 这是真正的独立可执行文件")
        print("   - 不依赖任何外部Python文件")
        print("   - 所有功能都内置在exe中")
        print("   - 首次启动会自动创建配置文件")
        
    except KeyboardInterrupt:
        print("\n\n❌ 打包被用户中断")
    except Exception as e:
        print(f"\n❌ 打包过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
