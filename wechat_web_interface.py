#!/usr/bin/env python3
"""
微信发送功能Web管理界面
提供微信群聊配置、消息模板设置、发送历史查看等功能
"""

import sys
import json
import threading
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template_string, jsonify, request

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from wechat_sender import WeChatSender
from prediction_listener import PredictionListener
from demo_wechat_prediction_system import DemoWeChatPredictionSystem

app = Flask(__name__)

# 全局实例
wechat_sender = WeChatSender()
prediction_listener = PredictionListener()
demo_system = DemoWeChatPredictionSystem()

# Web界面HTML模板
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>微信发送功能管理界面</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .content {
            padding: 30px;
        }
        
        .tabs {
            display: flex;
            border-bottom: 2px solid #eee;
            margin-bottom: 30px;
        }
        
        .tab {
            padding: 15px 25px;
            cursor: pointer;
            border: none;
            background: none;
            font-size: 16px;
            color: #666;
            border-bottom: 3px solid transparent;
            transition: all 0.3s;
        }
        
        .tab.active {
            color: #667eea;
            border-bottom-color: #667eea;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .card {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 20px;
            border-left: 4px solid #667eea;
        }
        
        .status-card {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: white;
            border: 1px solid #ddd;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 15px;
        }
        
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 10px;
        }
        
        .status-online { background: #28a745; }
        .status-offline { background: #dc3545; }
        .status-warning { background: #ffc107; }
        
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s;
            margin: 5px;
        }
        
        .btn-primary {
            background: #667eea;
            color: white;
        }
        
        .btn-primary:hover {
            background: #5a6fd8;
        }
        
        .btn-success {
            background: #28a745;
            color: white;
        }
        
        .btn-danger {
            background: #dc3545;
            color: white;
        }
        
        .btn-warning {
            background: #ffc107;
            color: #212529;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #333;
        }
        
        .form-control {
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-size: 14px;
        }
        
        .form-control:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        textarea.form-control {
            resize: vertical;
            min-height: 120px;
        }
        
        .group-list {
            max-height: 300px;
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 6px;
            padding: 10px;
        }
        
        .group-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            border-bottom: 1px solid #eee;
        }
        
        .group-item:last-child {
            border-bottom: none;
        }
        
        .history-item {
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 10px;
        }
        
        .history-time {
            color: #666;
            font-size: 12px;
            margin-bottom: 5px;
        }
        
        .history-content {
            font-size: 14px;
            line-height: 1.4;
        }
        
        .alert {
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
        }
        
        .alert-success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .alert-danger {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .alert-warning {
            background: #fff3cd;
            color: #856404;
            border: 1px solid #ffeaa7;
        }
        
        .loading {
            text-align: center;
            padding: 20px;
            color: #666;
        }
        
        @media (max-width: 768px) {
            .container {
                margin: 10px;
                border-radius: 10px;
            }
            
            .content {
                padding: 20px;
            }
            
            .tabs {
                flex-wrap: wrap;
            }
            
            .tab {
                flex: 1;
                min-width: 120px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 微信发送功能管理</h1>
            <p>黄金价格预测微信自动发送系统</p>
        </div>
        
        <div class="content">
            <div class="tabs">
                <button class="tab active" onclick="showTab('status')">系统状态</button>
                <button class="tab" onclick="showTab('config')">配置管理</button>
                <button class="tab" onclick="showTab('groups')">群聊管理</button>
                <button class="tab" onclick="showTab('test')">测试发送</button>
                <button class="tab" onclick="showTab('history')">发送历史</button>
                <button class="tab" onclick="showTab('demo')">Demo系统</button>
            </div>
            
            <!-- 系统状态 -->
            <div id="status" class="tab-content active">
                <div class="card">
                    <h3>🔧 系统状态监控</h3>
                    <div id="system-status">
                        <div class="loading">正在加载系统状态...</div>
                    </div>
                </div>
            </div>
            
            <!-- 配置管理 -->
            <div id="config" class="tab-content">
                <div class="card">
                    <h3>⚙️ 微信发送配置</h3>
                    <div class="form-group">
                        <label>消息模板</label>
                        <textarea id="message-template" class="form-control" placeholder="消息模板..."></textarea>
                    </div>
                    <div class="form-group">
                        <label>最小置信度</label>
                        <input type="number" id="min-confidence" class="form-control" step="0.1" min="0" max="1">
                    </div>
                    <div class="form-group">
                        <label>最小价格变化百分比</label>
                        <input type="number" id="min-price-change" class="form-control" step="0.1" min="0">
                    </div>
                    <div class="form-group">
                        <label>发送冷却时间（分钟）</label>
                        <input type="number" id="cooldown-minutes" class="form-control" min="1">
                    </div>
                    <button class="btn btn-primary" onclick="saveConfig()">保存配置</button>
                    <button class="btn btn-warning" onclick="loadConfig()">重新加载</button>
                </div>
            </div>
            
            <!-- 群聊管理 -->
            <div id="groups" class="tab-content">
                <div class="card">
                    <h3>👥 微信群聊管理</h3>
                    <button class="btn btn-primary" onclick="refreshGroups()">刷新群聊列表</button>
                    <button class="btn btn-success" onclick="connectWechat()">连接微信</button>
                    <button class="btn btn-danger" onclick="disconnectWechat()">断开连接</button>
                    
                    <div id="groups-list" style="margin-top: 20px;">
                        <div class="loading">点击"刷新群聊列表"获取群聊</div>
                    </div>
                </div>
            </div>
            
            <!-- 测试发送 -->
            <div id="test" class="tab-content">
                <div class="card">
                    <h3>🧪 测试消息发送</h3>
                    <div class="form-group">
                        <label>测试消息内容</label>
                        <textarea id="test-message" class="form-control" placeholder="输入测试消息...">这是一条测试消息，发送时间：当前时间</textarea>
                    </div>
                    <button class="btn btn-primary" onclick="sendTestMessage()">发送测试消息</button>
                    <button class="btn btn-success" onclick="sendTestPrediction()">发送测试预测</button>
                    
                    <div id="test-result" style="margin-top: 20px;"></div>
                </div>
            </div>
            
            <!-- 发送历史 -->
            <div id="history" class="tab-content">
                <div class="card">
                    <h3>📋 发送历史记录</h3>
                    <button class="btn btn-primary" onclick="refreshHistory()">刷新历史</button>
                    <button class="btn btn-warning" onclick="clearHistory()">清空历史</button>
                    
                    <div id="history-list" style="margin-top: 20px;">
                        <div class="loading">点击"刷新历史"查看发送记录</div>
                    </div>
                </div>
            </div>
            
            <!-- Demo系统 -->
            <div id="demo" class="tab-content">
                <div class="card">
                    <h3>🎮 Demo预测系统</h3>
                    <div id="demo-status">
                        <div class="loading">正在加载Demo系统状态...</div>
                    </div>
                    <div style="margin-top: 20px;">
                        <button class="btn btn-success" onclick="startDemo()">启动Demo系统</button>
                        <button class="btn btn-danger" onclick="stopDemo()">停止Demo系统</button>
                        <button class="btn btn-primary" onclick="manualPredict()">手动预测</button>
                        <button class="btn btn-warning" onclick="refreshDemoStatus()">刷新状态</button>
                    </div>
                    <div id="demo-result" style="margin-top: 20px;"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // 标签页切换
        function showTab(tabName) {
            // 隐藏所有标签页内容
            const contents = document.querySelectorAll('.tab-content');
            contents.forEach(content => content.classList.remove('active'));
            
            // 移除所有标签页的active类
            const tabs = document.querySelectorAll('.tab');
            tabs.forEach(tab => tab.classList.remove('active'));
            
            // 显示选中的标签页
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
            
            // 根据标签页加载相应数据
            if (tabName === 'status') {
                loadSystemStatus();
            } else if (tabName === 'config') {
                loadConfig();
            } else if (tabName === 'demo') {
                refreshDemoStatus();
            }
        }
        
        // 加载系统状态
        function loadSystemStatus() {
            fetch('/api/status')
            .then(response => response.json())
            .then(data => {
                const statusHtml = `
                    <div class="status-card">
                        <div>
                            <span class="status-indicator ${data.wechat_connected ? 'status-online' : 'status-offline'}"></span>
                            微信连接状态
                        </div>
                        <div>${data.wechat_connected ? '已连接' : '未连接'}</div>
                    </div>
                    <div class="status-card">
                        <div>
                            <span class="status-indicator ${data.listener_running ? 'status-online' : 'status-offline'}"></span>
                            预测监听器
                        </div>
                        <div>${data.listener_running ? '运行中' : '已停止'}</div>
                    </div>
                    <div class="status-card">
                        <div>目标群聊数量</div>
                        <div>${data.target_groups_count}</div>
                    </div>
                    <div class="status-card">
                        <div>最后错误</div>
                        <div>${data.last_error || '无'}</div>
                    </div>
                `;
                document.getElementById('system-status').innerHTML = statusHtml;
            })
            .catch(error => {
                document.getElementById('system-status').innerHTML = 
                    '<div class="alert alert-danger">加载系统状态失败: ' + error + '</div>';
            });
        }
        
        // 页面加载时初始化
        document.addEventListener('DOMContentLoaded', function() {
            loadSystemStatus();
        });
        
        // 加载配置
        function loadConfig() {
            fetch('/api/config')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const config = data.config;
                    document.getElementById('message-template').value = config.message_template.format;
                    document.getElementById('min-confidence').value = config.send_conditions.min_confidence;
                    document.getElementById('min-price-change').value = config.send_conditions.min_price_change_pct;
                    document.getElementById('cooldown-minutes').value = config.send_conditions.cooldown_minutes;
                } else {
                    showAlert('danger', '加载配置失败: ' + data.message);
                }
            })
            .catch(error => showAlert('danger', '加载配置失败: ' + error));
        }

        // 保存配置
        function saveConfig() {
            const config = {
                message_template: {
                    format: document.getElementById('message-template').value
                },
                send_conditions: {
                    min_confidence: parseFloat(document.getElementById('min-confidence').value),
                    min_price_change_pct: parseFloat(document.getElementById('min-price-change').value),
                    cooldown_minutes: parseInt(document.getElementById('cooldown-minutes').value)
                }
            };

            fetch('/api/config', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(config)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showAlert('success', '配置保存成功');
                } else {
                    showAlert('danger', '配置保存失败: ' + data.message);
                }
            })
            .catch(error => showAlert('danger', '配置保存失败: ' + error));
        }

        // 连接微信
        function connectWechat() {
            fetch('/api/wechat/connect', {method: 'POST'})
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showAlert('success', data.message);
                    loadSystemStatus();
                } else {
                    showAlert('danger', data.message);
                }
            })
            .catch(error => showAlert('danger', '连接微信失败: ' + error));
        }

        // 断开微信连接
        function disconnectWechat() {
            fetch('/api/wechat/disconnect', {method: 'POST'})
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showAlert('success', data.message);
                    loadSystemStatus();
                } else {
                    showAlert('danger', data.message);
                }
            })
            .catch(error => showAlert('danger', '断开连接失败: ' + error));
        }

        // 刷新群聊列表
        function refreshGroups() {
            document.getElementById('groups-list').innerHTML = '<div class="loading">正在获取群聊列表...</div>';

            fetch('/api/wechat/groups')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const groupsHtml = data.groups.map(group => `
                        <div class="group-item">
                            <span>${group}</span>
                            <button class="btn btn-primary" onclick="addToTargets('${group}')">添加到目标</button>
                        </div>
                    `).join('');

                    document.getElementById('groups-list').innerHTML =
                        '<div class="group-list">' + groupsHtml + '</div>';
                } else {
                    document.getElementById('groups-list').innerHTML =
                        '<div class="alert alert-danger">' + data.message + '</div>';
                }
            })
            .catch(error => {
                document.getElementById('groups-list').innerHTML =
                    '<div class="alert alert-danger">获取群聊列表失败: ' + error + '</div>';
            });
        }

        // 发送测试消息
        function sendTestMessage() {
            const message = document.getElementById('test-message').value;

            fetch('/api/test/message', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: message})
            })
            .then(response => response.json())
            .then(data => {
                const resultDiv = document.getElementById('test-result');
                if (data.success) {
                    resultDiv.innerHTML = `
                        <div class="alert alert-success">
                            <strong>发送成功!</strong><br>
                            成功发送到: ${data.sent_groups.join(', ')}<br>
                            ${data.failed_groups.length > 0 ? '发送失败: ' + data.failed_groups.join(', ') : ''}
                        </div>
                    `;
                } else {
                    resultDiv.innerHTML = `
                        <div class="alert alert-danger">
                            <strong>发送失败:</strong> ${data.message || data.errors.join(', ')}
                        </div>
                    `;
                }
            })
            .catch(error => {
                document.getElementById('test-result').innerHTML =
                    '<div class="alert alert-danger">发送失败: ' + error + '</div>';
            });
        }

        // 发送测试预测
        function sendTestPrediction() {
            sendTestMessage(); // 复用测试消息发送功能
        }

        // 刷新发送历史
        function refreshHistory() {
            document.getElementById('history-list').innerHTML = '<div class="loading">正在加载发送历史...</div>';

            fetch('/api/history')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const historyHtml = data.history.map(record => `
                        <div class="history-item">
                            <div class="history-time">${record.created_at}</div>
                            <div class="history-content">
                                <strong>${record.signal}</strong> -
                                $${record.current_price} → $${record.predicted_price}<br>
                                发送到: ${JSON.parse(record.sent_groups || '[]').join(', ')}
                            </div>
                        </div>
                    `).join('');

                    document.getElementById('history-list').innerHTML =
                        historyHtml || '<div class="alert alert-warning">暂无发送历史</div>';
                } else {
                    document.getElementById('history-list').innerHTML =
                        '<div class="alert alert-danger">' + data.message + '</div>';
                }
            })
            .catch(error => {
                document.getElementById('history-list').innerHTML =
                    '<div class="alert alert-danger">加载历史失败: ' + error + '</div>';
            });
        }

        // 刷新Demo状态
        function refreshDemoStatus() {
            document.getElementById('demo-status').innerHTML = '<div class="loading">正在加载Demo状态...</div>';

            fetch('/api/demo/status')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const status = data.status;
                    const statusHtml = `
                        <div class="status-card">
                            <div>
                                <span class="status-indicator ${status.running ? 'status-online' : 'status-offline'}"></span>
                                Demo系统状态
                            </div>
                            <div>${status.running ? '运行中' : '已停止'}</div>
                        </div>
                        <div class="status-card">
                            <div>预测间隔</div>
                            <div>${status.prediction_interval}秒</div>
                        </div>
                        <div class="status-card">
                            <div>预测数量</div>
                            <div>${status.predictions_count}</div>
                        </div>
                        ${status.last_prediction ? `
                        <div class="status-card">
                            <div>最新预测</div>
                            <div>${status.last_prediction.signal} ($${status.last_prediction.current_price.toFixed(2)} → $${status.last_prediction.predicted_price.toFixed(2)})</div>
                        </div>
                        ` : ''}
                    `;
                    document.getElementById('demo-status').innerHTML = statusHtml;
                } else {
                    document.getElementById('demo-status').innerHTML =
                        '<div class="alert alert-danger">' + data.message + '</div>';
                }
            })
            .catch(error => {
                document.getElementById('demo-status').innerHTML =
                    '<div class="alert alert-danger">加载Demo状态失败: ' + error + '</div>';
            });
        }

        // 启动Demo系统
        function startDemo() {
            fetch('/api/demo/start', {method: 'POST'})
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showAlert('success', data.message);
                    refreshDemoStatus();
                } else {
                    showAlert('danger', data.message);
                }
            })
            .catch(error => showAlert('danger', '启动Demo失败: ' + error));
        }

        // 停止Demo系统
        function stopDemo() {
            fetch('/api/demo/stop', {method: 'POST'})
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showAlert('success', data.message);
                    refreshDemoStatus();
                } else {
                    showAlert('danger', data.message);
                }
            })
            .catch(error => showAlert('danger', '停止Demo失败: ' + error));
        }

        // 手动预测
        function manualPredict() {
            fetch('/api/demo/predict', {method: 'POST'})
            .then(response => response.json())
            .then(data => {
                const resultDiv = document.getElementById('demo-result');
                if (data.success) {
                    const pred = data.prediction;
                    const wechatResult = data.wechat_result;
                    resultDiv.innerHTML = `
                        <div class="alert alert-success">
                            <strong>预测生成成功!</strong><br>
                            当前价格: $${pred.current_price.toFixed(2)}<br>
                            预测价格: $${pred.predicted_price.toFixed(2)}<br>
                            交易信号: ${pred.signal}<br>
                            置信度: ${(pred.confidence * 100).toFixed(1)}%<br>
                            微信发送: ${wechatResult.success ? '成功 → ' + wechatResult.sent_groups.join(', ') : '失败'}
                        </div>
                    `;
                } else {
                    resultDiv.innerHTML = `
                        <div class="alert alert-danger">
                            <strong>预测失败:</strong> ${data.message}
                        </div>
                    `;
                }
            })
            .catch(error => {
                document.getElementById('demo-result').innerHTML =
                    '<div class="alert alert-danger">手动预测失败: ' + error + '</div>';
            });
        }

        // 显示提示消息
        function showAlert(type, message) {
            const alertDiv = document.createElement('div');
            alertDiv.className = `alert alert-${type}`;
            alertDiv.innerHTML = message;
            alertDiv.style.position = 'fixed';
            alertDiv.style.top = '20px';
            alertDiv.style.right = '20px';
            alertDiv.style.zIndex = '9999';
            alertDiv.style.minWidth = '300px';

            document.body.appendChild(alertDiv);

            setTimeout(() => {
                document.body.removeChild(alertDiv);
            }, 5000);
        }

        // 清空历史
        function clearHistory() {
            if (confirm('确定要清空发送历史吗？')) {
                // 这里可以添加清空历史的API调用
                showAlert('warning', '清空历史功能待实现');
            }
        }

        // 添加群聊到目标列表
        function addToTargets(groupName) {
            // 这里可以添加将群聊添加到目标列表的逻辑
            showAlert('success', `已添加群聊: ${groupName}`);
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """主页"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/status')
def get_status():
    """获取系统状态"""
    try:
        wechat_status = wechat_sender.get_status()
        listener_status = prediction_listener.get_status()

        return jsonify({
            'wechat_connected': wechat_status['connected'],
            'target_groups_count': len(wechat_status['target_groups']),
            'last_error': wechat_status['last_error'],
            'listener_running': listener_status['running'],
            'file_monitoring': listener_status['file_monitoring'],
            'api_monitoring': listener_status['api_monitoring']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/wechat/connect', methods=['POST'])
def connect_wechat():
    """连接微信"""
    try:
        if wechat_sender.connect_wechat():
            return jsonify({'success': True, 'message': '微信连接成功'})
        else:
            return jsonify({'success': False, 'message': f'微信连接失败: {wechat_sender.last_error}'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/wechat/disconnect', methods=['POST'])
def disconnect_wechat():
    """断开微信连接"""
    try:
        wechat_sender.disconnect_wechat()
        return jsonify({'success': True, 'message': '微信连接已断开'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/wechat/groups')
def get_wechat_groups():
    """获取微信群聊列表"""
    try:
        if not wechat_sender.is_connected:
            if not wechat_sender.connect_wechat():
                return jsonify({'success': False, 'message': '微信连接失败'})

        groups = wechat_sender.get_group_list()
        return jsonify({'success': True, 'groups': groups})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/config', methods=['GET', 'POST'])
def manage_config():
    """管理配置"""
    if request.method == 'GET':
        try:
            return jsonify({
                'success': True,
                'config': wechat_sender.config
            })
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})

    elif request.method == 'POST':
        try:
            new_config = request.json
            if wechat_sender.update_config(new_config):
                return jsonify({'success': True, 'message': '配置更新成功'})
            else:
                return jsonify({'success': False, 'message': '配置更新失败'})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})

@app.route('/api/test/message', methods=['POST'])
def send_test_message():
    """发送测试消息"""
    try:
        data = request.json
        message = data.get('message', '这是一条测试消息')

        if not wechat_sender.is_connected:
            if not wechat_sender.connect_wechat():
                return jsonify({'success': False, 'message': '微信连接失败'})

        # 创建测试预测数据
        test_prediction = {
            'timestamp': datetime.now().isoformat(),
            'current_price': 2650.50,
            'predicted_price': 2675.25,
            'signal': '测试信号',
            'confidence': 0.75,
            'method': 'Web测试',
            'target_time': datetime.now().isoformat()
        }

        result = wechat_sender.send_prediction_to_groups(test_prediction)
        return jsonify(result)

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/history')
def get_send_history():
    """获取发送历史"""
    try:
        history = prediction_listener.get_send_history(50)
        return jsonify({'success': True, 'history': history})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/listener/start', methods=['POST'])
def start_listener():
    """启动预测监听器"""
    try:
        if prediction_listener.start_monitoring():
            return jsonify({'success': True, 'message': '监听器启动成功'})
        else:
            return jsonify({'success': False, 'message': '监听器启动失败'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/listener/stop', methods=['POST'])
def stop_listener():
    """停止预测监听器"""
    try:
        prediction_listener.stop_monitoring()
        return jsonify({'success': True, 'message': '监听器已停止'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/demo/status')
def get_demo_status():
    """获取Demo系统状态"""
    try:
        status = demo_system.get_status()
        return jsonify({'success': True, 'status': status})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/demo/start', methods=['POST'])
def start_demo():
    """启动Demo系统"""
    try:
        if demo_system.start_system():
            return jsonify({'success': True, 'message': 'Demo系统启动成功'})
        else:
            return jsonify({'success': False, 'message': 'Demo系统启动失败'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/demo/stop', methods=['POST'])
def stop_demo():
    """停止Demo系统"""
    try:
        demo_system.stop_system()
        return jsonify({'success': True, 'message': 'Demo系统已停止'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/demo/predict', methods=['POST'])
def manual_predict():
    """手动生成预测"""
    try:
        result = demo_system.manual_prediction()
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

if __name__ == "__main__":
    print("🌐 微信发送功能Web管理界面")
    print("=" * 50)
    print("启动Web服务器...")
    print("访问地址: http://localhost:5005")
    print("=" * 50)
    
    try:
        app.run(host='0.0.0.0', port=5005, debug=False)
    except KeyboardInterrupt:
        print("\n服务器已停止")
    except Exception as e:
        print(f"启动失败: {e}")
