#!/usr/bin/env python3
"""
简单预测系统
基于原始web_interface.py的简化版本，保持原有功能和界面
"""

from flask import Flask, render_template_string, jsonify, request, send_file
import subprocess
import threading
import json
import os
import time
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class SimpleTaskRunner:
    """简单任务执行器"""
    
    def __init__(self):
        self.base_dir = Path(".")
        self.results_dir = Path("results")
        self.task_status = {}
        self.task_results = {}
        
    def run_command(self, command, task_id, description):
        """运行命令"""
        try:
            self.task_status[task_id] = 'running'
            self.task_results[task_id] = {
                'description': description,
                'start_time': datetime.now().isoformat(),
                'status': 'running',
                'output': []
            }
            
            # 执行命令
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=self.base_dir
            )
            
            # 读取输出
            output_lines = []
            for line in iter(process.stdout.readline, ''):
                if line:
                    output_lines.append(line.strip())
                    self.task_results[task_id]['output'].append(line.strip())
            
            process.wait()
            
            # 更新状态
            if process.returncode == 0:
                self.task_status[task_id] = 'completed'
                self.task_results[task_id]['status'] = 'completed'
            else:
                self.task_status[task_id] = 'failed'
                self.task_results[task_id]['status'] = 'failed'
                
            self.task_results[task_id]['end_time'] = datetime.now().isoformat()
            self.task_results[task_id]['return_code'] = process.returncode
            
        except Exception as e:
            self.task_status[task_id] = 'failed'
            self.task_results[task_id]['status'] = 'failed'
            self.task_results[task_id]['error'] = str(e)
    
    def get_task_status(self, task_id):
        """获取任务状态"""
        return {
            'status': self.task_status.get(task_id, 'unknown'),
            'result': self.task_results.get(task_id, {})
        }


class SimplePredictionSystem:
    """简单预测系统"""
    
    def __init__(self):
        self.task_runner = SimpleTaskRunner()
        self.is_running = False
        
        print(f"[简单预测] 简单预测系统初始化完成")
    
    def start(self) -> bool:
        """启动系统（统一接口）"""
        return self.start_system()

    def start_system(self) -> bool:
        """启动系统"""
        try:
            self.is_running = True
            print(f"[简单预测] 系统启动成功")
            return True
        except Exception as e:
            logger.error(f"启动简单预测系统失败: {e}")
            return False
    
    def stop_system(self) -> bool:
        """停止系统"""
        try:
            self.is_running = False
            print(f"[简单预测] 系统停止成功")
            return True
        except Exception as e:
            logger.error(f"停止简单预测系统失败: {e}")
            return False
    
    def get_status(self) -> dict:
        """获取系统状态"""
        try:
            # 检查数据文件
            data_files = list(Path("results/data").glob("*.csv")) if Path("results/data").exists() else []
            model_files = list(Path("results/models").glob("**/*.pth")) if Path("results/models").exists() else []
            
            return {
                'running': self.is_running,
                'data_files': len(data_files),
                'model_files': len(model_files),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"获取简单预测系统状态失败: {e}")
            return {'running': False, 'error': str(e)}
    
    def run_task(self, task_type: str, config: dict = None) -> dict:
        """运行任务"""
        try:
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
                'simple_prediction': {
                    'command': 'uv run python web_predict.py --mode simple',
                    'description': '简单预测'
                },
                'multiple_prediction': {
                    'command': 'uv run python web_predict.py --mode multiple',
                    'description': '多模型预测'
                },
                'uncertainty_prediction': {
                    'command': 'uv run python web_predict.py --mode uncertainty',
                    'description': '不确定性预测'
                },
                'organize_files': {
                    'command': 'uv run python organize_results.py',
                    'description': '整理结果文件'
                }
            }
            
            if task_type not in commands:
                return {'success': False, 'message': f'未知任务类型: {task_type}'}
            
            command_info = commands[task_type]
            
            # 在后台运行任务
            thread = threading.Thread(
                target=self.task_runner.run_command,
                args=(command_info['command'], task_id, command_info['description'])
            )
            thread.daemon = True
            thread.start()
            
            return {
                'success': True,
                'task_id': task_id,
                'description': command_info['description']
            }
            
        except Exception as e:
            logger.error(f"运行任务失败: {e}")
            return {'success': False, 'message': str(e)}
    
    def get_task_status(self, task_id: str) -> dict:
        """获取任务状态"""
        return self.task_runner.get_task_status(task_id)


# 简单预测系统的HTML模板
SIMPLE_PREDICTION_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🥇 简单预测系统 - 操作界面</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh; color: #333;
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; color: white; margin-bottom: 30px; }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
        
        .status-panel {
            background: white; border-radius: 15px; padding: 20px; margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        }
        .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
        .status-item {
            text-align: center; padding: 15px; background: #f8f9fa; border-radius: 10px;
            border-left: 4px solid #007bff;
        }
        
        .control-panel { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-bottom: 30px; }
        .panel {
            background: white; border-radius: 15px; padding: 25px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        }
        .panel h2 {
            color: #333; margin-bottom: 20px; font-size: 1.5em;
            border-bottom: 2px solid #007bff; padding-bottom: 10px;
        }
        
        .button-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
        .action-btn {
            padding: 15px 20px; border: none; border-radius: 10px; font-size: 14px;
            font-weight: 600; cursor: pointer; transition: all 0.3s ease;
            position: relative; overflow: hidden;
        }
        .btn-primary { background: linear-gradient(45deg, #007bff, #0056b3); color: white; }
        .btn-success { background: linear-gradient(45deg, #28a745, #1e7e34); color: white; }
        .btn-warning { background: linear-gradient(45deg, #ffc107, #e0a800); color: #212529; }
        .btn-info { background: linear-gradient(45deg, #17a2b8, #138496); color: white; }
        .btn-secondary { background: linear-gradient(45deg, #6c757d, #545b62); color: white; }
        
        .action-btn:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.2); }
        .action-btn:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
        
        .log-panel {
            background: white; border-radius: 15px; padding: 25px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        }
        .log-container {
            background: #1e1e1e; color: #00ff00; padding: 20px; border-radius: 10px;
            height: 400px; overflow-y: auto; font-family: 'Courier New', monospace;
            font-size: 14px; line-height: 1.4;
        }
        .log-entry { margin-bottom: 5px; }
        .log-timestamp { color: #888; }
        .log-success { color: #00ff00; }
        .log-error { color: #ff4444; }
        .log-warning { color: #ffaa00; }
        
        .back-btn {
            position: fixed; top: 20px; left: 20px; z-index: 1000;
            background: rgba(0,0,0,0.5); padding: 10px 15px; border-radius: 25px;
            text-decoration: none; color: white; font-weight: bold;
        }
        .back-btn:hover { background: rgba(0,0,0,0.7); }
        
        @media (max-width: 768px) {
            .control-panel { grid-template-columns: 1fr; }
            .button-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <a href="/" class="back-btn">← 返回主页</a>
    
    <div class="container">
        <div class="header">
            <h1>🥇 简单预测系统</h1>
            <p>原始功能完整保留 - 丰富操作按钮和文件管理</p>
        </div>
        
        <!-- 系统状态面板 -->
        <div class="status-panel">
            <h2>📊 系统状态</h2>
            <div class="status-grid">
                <div class="status-item">
                    <h3>系统状态</h3>
                    <p id="system-status">未知</p>
                </div>
                <div class="status-item">
                    <h3>数据文件</h3>
                    <p id="data-files">0</p>
                </div>
                <div class="status-item">
                    <h3>模型文件</h3>
                    <p id="model-files">0</p>
                </div>
                <div class="status-item">
                    <h3>最后更新</h3>
                    <p id="last-update">--</p>
                </div>
            </div>
        </div>
        
        <!-- 控制面板 -->
        <div class="control-panel">
            <!-- 数据和测试操作 -->
            <div class="panel">
                <h2>🔧 数据和测试操作</h2>
                <div class="button-grid">
                    <button class="action-btn btn-info" onclick="runTask('gpu_test')">
                        🖥️ GPU兼容性测试
                    </button>
                    <button class="action-btn btn-primary" onclick="runTask('data_collection')">
                        📊 数据收集
                    </button>
                    <button class="action-btn btn-success" onclick="runTask('quick_demo')">
                        ⚡ 快速预测演示
                    </button>
                    <button class="action-btn btn-secondary" onclick="runTask('organize_files')">
                        📁 整理结果文件
                    </button>
                </div>
            </div>
            
            <!-- 预测操作 -->
            <div class="panel">
                <h2>🔮 预测操作</h2>
                <div class="button-grid">
                    <button class="action-btn btn-primary" onclick="runTask('simple_prediction')">
                        🎯 简单预测
                    </button>
                    <button class="action-btn btn-warning" onclick="runTask('multiple_prediction')">
                        🔄 多模型预测
                    </button>
                    <button class="action-btn btn-info" onclick="runTask('uncertainty_prediction')">
                        📈 不确定性预测
                    </button>
                    <button class="action-btn btn-success" onclick="refreshStatus()">
                        🔄 刷新状态
                    </button>
                </div>
            </div>
        </div>
        
        <!-- 日志面板 -->
        <div class="log-panel">
            <h2>📝 操作日志</h2>
            <div class="log-container" id="log-container">
                <div class="log-entry log-success">
                    <span class="log-timestamp">[等待]</span> 简单预测系统准备就绪
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let currentTasks = new Set();
        
        function runTask(taskType) {
            if (currentTasks.has(taskType)) {
                addLog('任务正在运行中...', 'warning');
                return;
            }
            
            addLog(`启动任务: ${taskType}`, 'info');
            currentTasks.add(taskType);
            
            fetch('/api/simple/run_task', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({task_type: taskType})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    addLog(`任务启动成功: ${data.description}`, 'success');
                    monitorTask(data.task_id, taskType);
                } else {
                    addLog(`任务启动失败: ${data.message}`, 'error');
                    currentTasks.delete(taskType);
                }
            })
            .catch(error => {
                addLog(`请求失败: ${error}`, 'error');
                currentTasks.delete(taskType);
            });
        }
        
        function monitorTask(taskId, taskType) {
            const checkStatus = () => {
                fetch(`/api/simple/task_status/${taskId}`)
                .then(response => response.json())
                .then(data => {
                    const status = data.status;
                    const result = data.result;
                    
                    if (status === 'running') {
                        setTimeout(checkStatus, 2000);
                    } else {
                        currentTasks.delete(taskType);
                        if (status === 'completed') {
                            addLog(`任务完成: ${taskType}`, 'success');
                        } else {
                            addLog(`任务失败: ${taskType}`, 'error');
                        }
                        refreshStatus();
                    }
                })
                .catch(error => {
                    currentTasks.delete(taskType);
                    addLog(`监控任务失败: ${error}`, 'error');
                });
            };
            
            setTimeout(checkStatus, 1000);
        }
        
        function refreshStatus() {
            fetch('/api/simple/status')
            .then(response => response.json())
            .then(data => {
                document.getElementById('system-status').textContent = data.running ? '运行中' : '已停止';
                document.getElementById('data-files').textContent = data.data_files || 0;
                document.getElementById('model-files').textContent = data.model_files || 0;
                document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
                
                addLog('状态已刷新', 'info');
            })
            .catch(error => {
                addLog(`状态刷新失败: ${error}`, 'error');
            });
        }
        
        function addLog(message, type = 'info') {
            const logContainer = document.getElementById('log-container');
            const timestamp = new Date().toLocaleTimeString();
            
            const logEntry = document.createElement('div');
            logEntry.className = `log-entry log-${type}`;
            logEntry.innerHTML = `<span class="log-timestamp">[${timestamp}]</span> ${message}`;
            
            logContainer.appendChild(logEntry);
            logContainer.scrollTop = logContainer.scrollHeight;
            
            // 保持最近100条日志
            while (logContainer.children.length > 100) {
                logContainer.removeChild(logContainer.firstChild);
            }
        }
        
        // 初始化
        addLog('简单预测系统界面加载完成', 'success');
        refreshStatus();
        
        // 定期刷新状态
        setInterval(refreshStatus, 30000);
    </script>
</body>
</html>
'''


def main():
    """测试函数"""
    print("简单预测系统测试")
    print("=" * 40)
    
    system = SimplePredictionSystem()
    
    # 测试启动
    if system.start_system():
        print("✅ 系统启动成功")
        
        # 测试状态
        status = system.get_status()
        print(f"📊 系统状态: {status}")
        
        # 测试任务
        result = system.run_task('gpu_test')
        print(f"🔧 任务结果: {result}")
        
        print("✅ 简单预测系统测试完成!")
    else:
        print("❌ 系统启动失败")


if __name__ == "__main__":
    main()
