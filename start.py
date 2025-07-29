#!/usr/bin/env python3
"""
GoldPredict V2.0 快速启动脚本
提供多种启动选项和系统检查
"""

import sys
import os
import subprocess
import argparse
import time
from pathlib import Path

def print_banner():
    """打印启动横幅"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                    🚀 GoldPredict V2.0                       ║
    ║                   智能黄金价格预测系统                        ║
    ║                      快速启动程序                            ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_environment():
    """检查运行环境"""
    print("🔍 检查运行环境...")
    
    # 检查Python版本
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print(f"❌ Python版本过低: {version.major}.{version.minor}")
        print("   需要Python 3.10+")
        return False
    
    print(f"✅ Python版本: {version.major}.{version.minor}.{version.micro}")
    
    # 检查核心文件
    required_files = [
        'unified_prediction_platform_fixed_ver2.0.py',
        'traditional_ml_system_ver2.py',
        'auto_trading_system.py',
        'wechat_sender.py',
        'pyproject.toml'
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ 缺少文件: {', '.join(missing_files)}")
        return False
    
    print("✅ 核心文件完整")
    
    # 检查配置文件
    config_dir = Path('config')
    if not config_dir.exists():
        print("⚠️  配置目录不存在，将创建默认配置")
        create_default_configs()
    else:
        print("✅ 配置目录存在")
    
    return True

def create_default_configs():
    """创建默认配置"""
    config_dir = Path('config')
    config_dir.mkdir(exist_ok=True)
    
    # 创建基本配置文件
    configs = {
        'config.yaml': """system:
  name: "GoldPredict V2.0"
  debug: false
  log_level: "INFO"
data_sources:
  primary: "mt5"
  update_interval: 30
prediction:
  lookback_days: 30
  confidence_threshold: 0.7
models:
  traditional_ml:
    enabled: true
    models: ["random_forest", "xgboost"]
""",
        'trading.yaml': """trading:
  enabled: false
  symbol: "XAUUSD"
risk_management:
  max_position_size: 0.1
  stop_loss_pips: 200
""",
        'wechat.json': """{
  "enabled": false,
  "target_groups": [],
  "send_conditions": {
    "min_confidence": 0.8
  }
}"""
    }
    
    for filename, content in configs.items():
        config_file = config_dir / filename
        if not config_file.exists():
            config_file.write_text(content, encoding='utf-8')
            print(f"✅ 创建配置文件: {filename}")

def start_unified_platform(port=5000, debug=False):
    """启动统一平台"""
    print(f"🚀 启动统一平台 (端口: {port})...")
    
    cmd = [sys.executable, 'unified_prediction_platform_fixed_ver2.0.py']
    if port != 5000:
        cmd.extend(['--port', str(port)])
    if debug:
        cmd.append('--debug')
    
    try:
        process = subprocess.Popen(cmd)
        print(f"✅ 统一平台已启动 (PID: {process.pid})")
        print(f"🌐 访问地址: http://localhost:{port}")
        return process
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return None

def start_individual_system(system_name):
    """启动单个系统"""
    system_files = {
        'traditional': 'traditional_ml_system_ver2.py',
        'auto_trading': 'auto_trading_system.py',
        'wechat': 'wechat_sender.py',
        'realtime': 'realtime_prediction_engine.py'
    }
    
    if system_name not in system_files:
        print(f"❌ 未知系统: {system_name}")
        print(f"可用系统: {', '.join(system_files.keys())}")
        return None
    
    script_file = system_files[system_name]
    if not Path(script_file).exists():
        print(f"❌ 系统文件不存在: {script_file}")
        return None
    
    print(f"🚀 启动{system_name}系统...")
    
    try:
        process = subprocess.Popen([sys.executable, script_file])
        print(f"✅ {system_name}系统已启动 (PID: {process.pid})")
        return process
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return None

def show_system_status():
    """显示系统状态"""
    print("📊 系统状态:")
    
    # 检查进程
    try:
        import psutil
        
        # 查找相关进程
        goldpredict_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if 'goldpredict' in cmdline.lower() or any(
                    script in cmdline for script in [
                        'unified_prediction_platform',
                        'traditional_ml_system',
                        'auto_trading_system',
                        'wechat_sender'
                    ]
                ):
                    goldpredict_processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if goldpredict_processes:
            print("🟢 运行中的进程:")
            for proc in goldpredict_processes:
                print(f"   PID {proc['pid']}: {proc['name']}")
        else:
            print("🔴 没有运行中的GoldPredict进程")
            
    except ImportError:
        print("⚠️  无法检查进程状态 (需要psutil)")
    
    # 检查端口
    try:
        import socket
        
        ports_to_check = [5000, 5001, 5002, 5003]
        for port in ports_to_check:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            
            if result == 0:
                print(f"🟢 端口 {port}: 使用中")
            else:
                print(f"🔴 端口 {port}: 空闲")
                
    except Exception as e:
        print(f"⚠️  端口检查失败: {e}")

def stop_all_processes():
    """停止所有相关进程"""
    print("🛑 停止所有GoldPredict进程...")
    
    try:
        import psutil
        
        stopped_count = 0
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if 'goldpredict' in cmdline.lower() or any(
                    script in cmdline for script in [
                        'unified_prediction_platform',
                        'traditional_ml_system',
                        'auto_trading_system',
                        'wechat_sender'
                    ]
                ):
                    proc.terminate()
                    proc.wait(timeout=5)
                    print(f"✅ 已停止进程 PID {proc.info['pid']}")
                    stopped_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                continue
        
        if stopped_count > 0:
            print(f"✅ 共停止 {stopped_count} 个进程")
        else:
            print("ℹ️  没有找到运行中的进程")
            
    except ImportError:
        print("❌ 无法停止进程 (需要psutil)")

def run_tests():
    """运行测试"""
    print("🧪 运行系统测试...")
    
    test_files = [
        'test_unified_v2.py',
        'test_traditional_ml.py',
        'test_auto_trading.py',
        'test_wechat_integration.py'
    ]
    
    available_tests = [f for f in test_files if Path(f).exists()]
    
    if not available_tests:
        print("⚠️  没有找到测试文件")
        return
    
    for test_file in available_tests:
        print(f"🔍 运行测试: {test_file}")
        try:
            result = subprocess.run([sys.executable, test_file], 
                                  capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                print(f"✅ {test_file}: 通过")
            else:
                print(f"❌ {test_file}: 失败")
                print(f"   错误: {result.stderr}")
        except subprocess.TimeoutExpired:
            print(f"⏰ {test_file}: 超时")
        except Exception as e:
            print(f"❌ {test_file}: 异常 - {e}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='GoldPredict V2.0 启动脚本')
    parser.add_argument('--mode', choices=['unified', 'traditional', 'auto_trading', 'wechat', 'realtime'], 
                       default='unified', help='启动模式')
    parser.add_argument('--port', type=int, default=5000, help='Web服务端口')
    parser.add_argument('--debug', action='store_true', help='调试模式')
    parser.add_argument('--status', action='store_true', help='显示系统状态')
    parser.add_argument('--stop', action='store_true', help='停止所有进程')
    parser.add_argument('--test', action='store_true', help='运行测试')
    parser.add_argument('--no-check', action='store_true', help='跳过环境检查')
    
    args = parser.parse_args()
    
    print_banner()
    
    # 处理特殊命令
    if args.status:
        show_system_status()
        return
    
    if args.stop:
        stop_all_processes()
        return
    
    if args.test:
        run_tests()
        return
    
    # 环境检查
    if not args.no_check:
        if not check_environment():
            print("❌ 环境检查失败")
            sys.exit(1)
    
    # 启动系统
    if args.mode == 'unified':
        process = start_unified_platform(args.port, args.debug)
    else:
        process = start_individual_system(args.mode)
    
    if process:
        try:
            print("\n📋 控制命令:")
            print("   Ctrl+C: 停止系统")
            print("   python start.py --status: 查看状态")
            print("   python start.py --stop: 停止所有进程")
            
            # 等待用户中断
            process.wait()
        except KeyboardInterrupt:
            print("\n🛑 收到停止信号...")
            process.terminate()
            process.wait()
            print("✅ 系统已停止")
    else:
        print("❌ 启动失败")
        sys.exit(1)

if __name__ == "__main__":
    main()
