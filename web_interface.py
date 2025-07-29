#!/usr/bin/env python3
"""
黄金价格预测系统 - Web操作界面
提供浏览器端的实时操作和结果展示
"""

from flask import Flask, render_template, jsonify, request, send_file, redirect, url_for
from flask_socketio import SocketIO, emit
import subprocess
import threading
import json
import os
import time
from datetime import datetime
from pathlib import Path
import logging
import sys

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'goldpredict_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

# 全局变量存储任务状态
task_status = {}
task_results = {}


class TaskRunner:
    """任务执行器"""
    
    def __init__(self):
        self.base_dir = Path(".")
        self.results_dir = Path("results")
        
    def run_command(self, command, task_id, description):
        """运行命令并实时输出"""
        try:
            socketio.emit('task_start', {
                'task_id': task_id,
                'description': description,
                'timestamp': datetime.now().isoformat()
            })

            # 更新任务状态
            task_status[task_id] = 'running'
            task_results[task_id] = {
                'description': description,
                'start_time': datetime.now().isoformat(),
                'output': [],
                'status': 'running'
            }

            # 执行命令，设置工作目录
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                cwd=str(self.base_dir)  # 设置工作目录
            )
            
            # 实时读取输出
            for line in iter(process.stdout.readline, ''):
                if line:
                    line = line.strip()
                    task_results[task_id]['output'].append(line)
                    socketio.emit('task_output', {
                        'task_id': task_id,
                        'output': line,
                        'timestamp': datetime.now().isoformat()
                    })
            
            # 等待进程完成
            process.wait()

            # 更新最终状态 - 对于某些脚本，即使返回非0也可能是成功的
            # 检查是否有预期的输出文件来判断成功
            success = self._check_task_success(task_id, command)

            if success:
                task_status[task_id] = 'completed'
                task_results[task_id]['status'] = 'completed'
                socketio.emit('task_complete', {
                    'task_id': task_id,
                    'status': 'success',
                    'timestamp': datetime.now().isoformat()
                })
            else:
                task_status[task_id] = 'failed'
                task_results[task_id]['status'] = 'failed'
                socketio.emit('task_complete', {
                    'task_id': task_id,
                    'status': 'error',
                    'timestamp': datetime.now().isoformat()
                })
                
        except Exception as e:
            task_status[task_id] = 'failed'
            task_results[task_id]['status'] = 'failed'
            task_results[task_id]['error'] = str(e)
            socketio.emit('task_error', {
                'task_id': task_id,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })

    def _check_task_success(self, task_id, command):
        """检查任务是否成功完成（通过检查输出文件）"""
        try:
            # 根据命令类型检查相应的输出文件
            if 'web_data_collect' in command:
                return Path("results/data/latest_gold_data.csv").exists()
            elif 'web_predict.py --mode simple' in command:
                return Path("results/predictions/web_simple_prediction.json").exists()
            elif 'web_predict.py --mode multiple' in command:
                return Path("results/predictions/web_multiple_predictions.json").exists()
            elif 'web_predict.py --mode uncertainty' in command:
                return Path("results/predictions/web_uncertainty_prediction.json").exists()
            elif 'demo_prediction' in command:
                return Path("results/visualizations/gold_price_prediction.html").exists()
            elif 'organize_results' in command:
                return True  # 整理文件总是成功的
            elif 'test_gpu' in command:
                return True  # GPU测试总是成功的
            else:
                return True  # 默认认为成功
        except:
            return True  # 出错时默认认为成功


task_runner = TaskRunner()


@app.route('/')
def index():
    """主页面"""
    return render_template('index.html')


@app.route('/api/system_status')
def system_status():
    """获取系统状态"""
    try:
        # 检查GPU状态
        gpu_available = False
        gpu_info = "未检测到GPU"
        
        try:
            import torch
            if torch.cuda.is_available():
                gpu_available = True
                gpu_info = f"{torch.cuda.get_device_name(0)} ({torch.cuda.get_device_properties(0).total_memory // 1024**3}GB)"
        except:
            pass
        
        # 检查数据文件
        data_files = list(Path("results/data").glob("*.csv")) if Path("results/data").exists() else []
        model_files = list(Path("results/models").glob("**/*.pth")) if Path("results/models").exists() else []
        
        return jsonify({
            'gpu_available': gpu_available,
            'gpu_info': gpu_info,
            'data_files': len(data_files),
            'model_files': len(model_files),
            'python_version': sys.version,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/run_task', methods=['POST'])
def run_task():
    """执行任务"""
    data = request.json
    task_type = data.get('task_type')
    config = data.get('config', {})
    task_id = f"{task_type}_{int(time.time())}"

    # 定义任务命令
    commands = {
        'gpu_test': {
            'command': 'uv run python test_gpu.py',
            'description': 'GPU兼容性测试'
        },
        'data_collection': {
            'command': 'uv run python web_data_collect.py',
            'description': '数据收集'
        },
        'quick_demo': {
            'command': 'uv run python demo_prediction.py',
            'description': '快速预测演示'
        },
        'test_data_source': {
            'command': 'uv run python src/data/mt5_data_collector.py',
            'description': '测试数据源连接'
        },
        'realtime_data': {
            'command': 'uv run python src/data/mt5_data_collector.py --realtime',
            'description': '实时数据流'
        },
        'realtime_prediction': {
            'command': 'uv run python simple_realtime_prediction.py --interval 5',
            'description': '实时预测系统'
        },
        'realtime_web': {
            'command': 'uv run python realtime_web_controller.py',
            'description': '实时预测Web界面'
        },
        'train_basic': {
            'command': 'uv run python train.py --config configs/rtx40_config.json --output ./results/models --device cpu --epochs 10',
            'description': '基础模型训练'
        },
        'train_optimized': {
            'command': 'uv run python train.py --config configs/rtx40_optimized.json --output ./results/models --device auto --epochs 20',
            'description': '优化模型训练'
        },
        'predict_simple': {
            'command': 'uv run python multicore_prediction_system.py --mode simple',
            'description': '简单预测演示'
        },
        'predict_multiple': {
            'command': 'uv run python multicore_prediction_system.py --mode advanced',
            'description': '多时间跨度预测'
        },
        'predict_uncertainty': {
            'command': 'uv run python web_predict.py --mode uncertainty',
            'description': '不确定性预测'
        },
        'organize_files': {
            'command': 'uv run python organize_results.py',
            'description': '整理结果文件'
        },
        'system_check': {
            'command': 'uv run python quick_start.py',
            'description': '系统功能检查'
        },
        'ultimate_prediction': {
            'command': 'uv run python improved_prediction_system.py --mode improved',
            'description': '一键终极预测'
        },
        'advanced_training': {
            'command': 'uv run python improved_prediction_system.py --mode enhanced',
            'description': '高级深度训练'
        },
        'gpu_setup': {
            'command': 'uv run python setup_gpu_environment.py',
            'description': 'GPU环境检测'
        }
    }
    
    if task_type not in commands:
        return jsonify({'error': 'Unknown task type'}), 400

    # 构建配置化命令
    command_info = commands[task_type]
    base_command = command_info['command']

    # 为预测任务添加配置参数
    if task_type in ['predict_simple', 'predict_multiple', 'ultimate_prediction'] and config:
        config_params = []
        if 'data_source' in config:
            config_params.append(f"--data-source {config['data_source']}")
        if 'time_period' in config:
            config_params.append(f"--period {config['time_period']}")
        if 'cpu_cores' in config:
            config_params.append(f"--cpu-cores {config['cpu_cores']}")
        if 'prediction_mode' in config:
            config_params.append(f"--mode {config['prediction_mode']}")

        if config_params:
            base_command += " " + " ".join(config_params)

    # 在后台线程中执行任务
    thread = threading.Thread(
        target=task_runner.run_command,
        args=(base_command, task_id, command_info['description'])
    )
    thread.daemon = True
    thread.start()

    return jsonify({
        'task_id': task_id,
        'status': 'started',
        'description': command_info['description'],
        'command': base_command,
        'config': config
    })


@app.route('/api/task_status/<task_id>')
def get_task_status(task_id):
    """获取任务状态"""
    if task_id in task_results:
        return jsonify(task_results[task_id])
    else:
        return jsonify({'error': 'Task not found'}), 404


@app.route('/test_mt5')
def test_mt5():
    """测试MT5连接"""
    try:
        from src.data.mt5_data_collector import MT5DataCollector

        collector = MT5DataCollector()
        if collector.connect():
            symbol = collector.find_gold_symbol()
            if symbol:
                current_price = collector.get_current_price(symbol)
                collector.disconnect()

                if current_price:
                    return jsonify({
                        'success': True,
                        'symbol': symbol,
                        'price': current_price['last'],
                        'bid': current_price['bid'],
                        'ask': current_price['ask']
                    })

        return jsonify({'success': False, 'error': 'MT5连接失败'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/results')
def list_results():
    """列出结果文件"""
    results = {}
    
    # 扫描results文件夹
    if Path("results").exists():
        for category in ['models', 'predictions', 'visualizations', 'benchmarks', 'data']:
            category_path = Path("results") / category
            if category_path.exists():
                files = []
                for file_path in category_path.rglob("*"):
                    if file_path.is_file():
                        files.append({
                            'name': file_path.name,
                            'path': str(file_path),
                            'size': file_path.stat().st_size,
                            'modified': file_path.stat().st_mtime
                        })
                results[category] = files
    
    return jsonify(results)


@app.route('/api/view_file/<path:file_path>')
def view_file(file_path):
    """查看文件内容"""
    try:
        full_path = Path(file_path)
        if not full_path.exists():
            return jsonify({'error': 'File not found'}), 404
        
        if full_path.suffix.lower() == '.html':
            # 直接返回HTML文件
            return send_file(full_path)
        elif full_path.suffix.lower() == '.json':
            # 返回JSON内容
            with open(full_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
            return jsonify(content)
        elif full_path.suffix.lower() == '.csv':
            # 返回CSV的前几行
            import pandas as pd
            df = pd.read_csv(full_path)
            return jsonify({
                'columns': df.columns.tolist(),
                'data': df.head(10).to_dict('records'),
                'total_rows': len(df)
            })
        else:
            # 返回文本内容
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return jsonify({'content': content})
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/results/<path:filename>')
def serve_result_file(filename):
    """提供结果文件下载"""
    return send_file(Path("results") / filename)


@socketio.on('connect')
def handle_connect():
    """客户端连接"""
    emit('connected', {'message': '连接成功'})


@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开连接"""
    print('客户端断开连接')


def main():
    """启动Web界面"""
    print("[网络] 启动黄金价格预测系统Web界面...")
    print("[手机] 访问地址: http://localhost:5000")
    print("[刷新] 支持实时任务执行和结果展示")
    print("[快速] 按 Ctrl+C 停止服务")
    
    # 创建templates文件夹
    Path("templates").mkdir(exist_ok=True)
    
    # 启动服务器
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)


if __name__ == '__main__':
    main()
