#!/usr/bin/env python3
"""
简化版增强Web界面
不依赖复杂库，专注核心功能
"""

import json
import threading
import time
from datetime import datetime
from pathlib import Path
from flask import Flask, jsonify, request, render_template_string
import logging

from adaptive_prediction_engine import AdaptivePredictionEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 全局变量
prediction_engine = None


class SimpleEnhancedController:
    """简化增强控制器"""
    
    def __init__(self):
        self.engine = None
        self.running = False
        self.default_config = {
            'interval_minutes': 5,
            'data_collection_seconds': 5,
            'min_data_points': 10,
            'auto_optimize': True,
            'confidence_threshold': 0.6
        }
    
    def start_engine(self, config=None):
        """启动预测引擎"""
        global prediction_engine
        
        if prediction_engine and prediction_engine.running:
            return {'success': False, 'message': '引擎已在运行中'}
        
        try:
            if config:
                self.default_config.update(config)
            
            prediction_engine = AdaptivePredictionEngine(self.default_config)
            
            if prediction_engine.start_engine():
                self.running = True
                return {'success': True, 'message': '自适应预测引擎已启动', 'config': self.default_config}
            else:
                return {'success': False, 'message': '引擎启动失败'}
            
        except Exception as e:
            logger.error(f"启动引擎失败: {e}")
            return {'success': False, 'message': f'启动失败: {str(e)}'}
    
    def stop_engine(self):
        """停止预测引擎"""
        global prediction_engine
        
        if prediction_engine:
            prediction_engine.stop_engine()
            prediction_engine = None
            self.running = False
            return {'success': True, 'message': '自适应预测引擎已停止'}
        
        return {'success': False, 'message': '引擎未运行'}
    
    def get_status(self):
        """获取引擎状态"""
        global prediction_engine
        
        if not prediction_engine:
            return {
                'running': False,
                'config': self.default_config,
                'performance_metrics': {
                    'total_predictions': 0,
                    'average_accuracy': 0,
                    'recent_accuracy': 0
                }
            }
        
        return prediction_engine.get_status()
    
    def get_latest_prediction(self):
        """获取最新预测"""
        global prediction_engine
        
        if prediction_engine:
            return prediction_engine.get_latest_prediction()
        return None


# 创建控制器实例
controller = SimpleEnhancedController()

# 简化的HTML模板
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚀 增强预测系统</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; min-height: 100vh; padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 30px; }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; color: #ffd700; }
        .panel {
            background: rgba(255,255,255,0.1); padding: 20px; border-radius: 15px;
            backdrop-filter: blur(10px); margin-bottom: 20px;
        }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .btn {
            padding: 10px 20px; border: none; border-radius: 25px; font-weight: bold;
            cursor: pointer; margin: 5px; transition: all 0.3s ease;
        }
        .btn-primary { background: linear-gradient(45deg, #ff6b6b, #ee5a24); color: white; }
        .btn-secondary { background: linear-gradient(45deg, #74b9ff, #0984e3); color: white; }
        .btn:hover { transform: translateY(-2px); }
        .status-item { text-align: center; padding: 15px; background: rgba(255,255,255,0.1); border-radius: 10px; margin: 10px; }
        .status-value { font-size: 1.5em; font-weight: bold; color: #ffd700; }
        .config-row { display: flex; align-items: center; margin: 10px 0; }
        .config-row label { flex: 1; margin-right: 10px; }
        .config-row select, .config-row input {
            flex: 1; padding: 8px; border: none; border-radius: 5px;
            background: rgba(255,255,255,0.2); color: white;
        }
        .prediction-card {
            text-align: center; padding: 20px; background: rgba(255,255,255,0.1);
            border-radius: 15px; margin: 10px;
        }
        .price-display { font-size: 2em; font-weight: bold; margin: 10px 0; color: #ffd700; }
        .signal-display {
            padding: 8px 16px; border-radius: 20px; font-weight: bold; margin: 10px 0;
            background: linear-gradient(45deg, #74b9ff, #0984e3);
        }
        .log-container {
            background: rgba(0,0,0,0.3); padding: 15px; border-radius: 10px;
            height: 200px; overflow-y: auto; font-family: monospace; font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 增强预测系统</h1>
            <p>自适应AI预测引擎</p>
        </div>
        
        <div class="grid">
            <div class="panel">
                <h2>⚙️ 系统控制</h2>
                <div class="config-row">
                    <label>预测间隔 (分钟):</label>
                    <select id="interval-minutes">
                        <option value="1">1分钟</option>
                        <option value="5" selected>5分钟</option>
                        <option value="10">10分钟</option>
                    </select>
                </div>
                <div class="config-row">
                    <label>数据收集间隔 (秒):</label>
                    <select id="data-collection-seconds">
                        <option value="2">2秒</option>
                        <option value="5" selected>5秒</option>
                        <option value="10">10秒</option>
                    </select>
                </div>
                <div class="config-row">
                    <label>最少数据点:</label>
                    <select id="min-data-points">
                        <option value="5">5个</option>
                        <option value="10" selected>10个</option>
                        <option value="20">20个</option>
                    </select>
                </div>

                <hr style="margin: 15px 0; border: 1px solid rgba(255,255,255,0.2);">
                <h3 style="margin-bottom: 10px;">📱 微信推送设置</h3>

                <div class="config-row">
                    <label>启用微信推送:</label>
                    <select id="wechat-push-enabled">
                        <option value="false" selected>禁用</option>
                        <option value="true">启用</option>
                    </select>
                </div>

                <div class="config-row">
                    <label>推送间隔 (分钟):</label>
                    <select id="wechat-push-interval">
                        <option value="5">5分钟</option>
                        <option value="10">10分钟</option>
                        <option value="15">15分钟</option>
                        <option value="30" selected>30分钟</option>
                        <option value="60">60分钟</option>
                    </select>
                </div>

                <div style="text-align: center; margin-top: 20px;">
                    <button class="btn btn-primary" onclick="startEngine()">🚀 启动引擎</button>
                    <button class="btn btn-secondary" onclick="stopEngine()">⏹️ 停止引擎</button>
                    <button class="btn btn-success" onclick="testWechatPush()">📱 测试推送</button>
                    <button class="btn btn-warning" onclick="updateWechatConfig()">💾 保存配置</button>
                </div>
            </div>
            
            <div class="panel">
                <h2>📊 系统状态</h2>
                <div class="status-item">
                    <div class="status-value" id="engine-status">未启动</div>
                    <div>引擎状态</div>
                </div>
                <div class="status-item">
                    <div class="status-value" id="data-points">0</div>
                    <div>数据点数</div>
                </div>
                <div class="status-item">
                    <div class="status-value" id="predictions-count">0</div>
                    <div>预测次数</div>
                </div>
            </div>
        </div>
        
        <div class="grid">
            <div class="prediction-card">
                <h3>💰 当前价格</h3>
                <div class="price-display" id="current-price">$--</div>
            </div>
            <div class="prediction-card">
                <h3>🔮 AI预测</h3>
                <div class="price-display" id="predicted-price">$--</div>
                <div class="signal-display" id="trading-signal">等待预测</div>
                <div>置信度: <span id="confidence-value">--%</span></div>
            </div>
            <div class="prediction-card">
                <h3>📈 价格变化</h3>
                <div class="price-display" id="price-change">--</div>
                <div id="price-change-pct">--%</div>
            </div>
        </div>
        
        <div class="panel">
            <h2>📊 性能指标</h2>
            <div class="grid">
                <div class="status-item">
                    <div class="status-value" id="total-predictions">0</div>
                    <div>总预测数</div>
                </div>
                <div class="status-item">
                    <div class="status-value" id="average-accuracy">--%</div>
                    <div>平均准确率</div>
                </div>
                <div class="status-item">
                    <div class="status-value" id="recent-accuracy">--%</div>
                    <div>近期准确率</div>
                </div>
                <div class="status-item">
                    <div class="status-value" id="confidence-base">--%</div>
                    <div>基础置信度</div>
                </div>
            </div>
        </div>
        
        <div class="panel">
            <h2>📝 系统日志</h2>
            <div class="log-container" id="log-container">
                <div>[等待] 增强预测系统准备就绪</div>
            </div>
        </div>
    </div>
    
    <script>
        function getConfig() {
            return {
                interval_minutes: parseInt(document.getElementById('interval-minutes').value),
                data_collection_seconds: parseInt(document.getElementById('data-collection-seconds').value),
                min_data_points: parseInt(document.getElementById('min-data-points').value),
                auto_optimize: true
            };
        }
        
        function startEngine() {
            const config = getConfig();
            addLog(`启动引擎: 间隔${config.interval_minutes}分钟`);
            
            fetch('/api/engine/start', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(config)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    addLog('自适应预测引擎启动成功');
                } else {
                    addLog(`启动失败: ${data.message}`);
                }
            })
            .catch(error => addLog(`启动错误: ${error}`));
        }
        
        function stopEngine() {
            fetch('/api/engine/stop', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    addLog('预测引擎已停止');
                } else {
                    addLog(`停止失败: ${data.message}`);
                }
            })
            .catch(error => addLog(`停止错误: ${error}`));
        }
        
        function updateStatus() {
            fetch('/api/engine/status')
            .then(response => response.json())
            .then(data => {
                document.getElementById('engine-status').textContent = data.running ? '运行中' : '已停止';
                document.getElementById('data-points').textContent = data.data_points || 0;
                document.getElementById('predictions-count').textContent = data.predictions_count || 0;
                
                const metrics = data.performance_metrics || {};
                document.getElementById('total-predictions').textContent = metrics.total_predictions || 0;
                document.getElementById('average-accuracy').textContent = 
                    metrics.average_accuracy ? `${(metrics.average_accuracy * 100).toFixed(1)}%` : '--%';
                document.getElementById('recent-accuracy').textContent = 
                    metrics.recent_accuracy ? `${(metrics.recent_accuracy * 100).toFixed(1)}%` : '--%';
                document.getElementById('confidence-base').textContent = 
                    data.confidence_base ? `${(data.confidence_base * 100).toFixed(1)}%` : '--%';
            })
            .catch(error => console.error('状态更新错误:', error));
        }
        
        function updatePrediction() {
            fetch('/api/prediction/latest')
            .then(response => response.json())
            .then(data => {
                if (data.current_price) {
                    document.getElementById('current-price').textContent = `$${data.current_price.toFixed(2)}`;
                    document.getElementById('predicted-price').textContent = `$${data.predicted_price.toFixed(2)}`;
                    document.getElementById('trading-signal').textContent = data.signal;
                    document.getElementById('confidence-value').textContent = `${(data.confidence * 100).toFixed(1)}%`;
                    
                    const priceChange = data.predicted_price - data.current_price;
                    const priceChangePct = (priceChange / data.current_price * 100);
                    document.getElementById('price-change').textContent = 
                        `${priceChange >= 0 ? '+' : ''}$${priceChange.toFixed(2)}`;
                    document.getElementById('price-change-pct').textContent = 
                        `${priceChangePct >= 0 ? '+' : ''}${priceChangePct.toFixed(3)}%`;
                }
            })
            .catch(error => console.error('预测更新错误:', error));
        }
        
        function addLog(message) {
            const logContainer = document.getElementById('log-container');
            const timestamp = new Date().toLocaleTimeString();
            const logEntry = document.createElement('div');
            logEntry.textContent = `[${timestamp}] ${message}`;
            logContainer.appendChild(logEntry);
            logContainer.scrollTop = logContainer.scrollHeight;

            while (logContainer.children.length > 50) {
                logContainer.removeChild(logContainer.firstChild);
            }
        }

        function updateWechatConfig() {
            const wechatEnabled = document.getElementById('wechat-push-enabled').value === 'true';
            const wechatInterval = parseInt(document.getElementById('wechat-push-interval').value);

            addLog(`更新微信配置: ${wechatEnabled ? '启用' : '禁用'}, 间隔${wechatInterval}分钟`);

            fetch('/api/realtime/config', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    wechat_push_enabled: wechatEnabled,
                    wechat_push_interval_minutes: wechatInterval
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    addLog('微信推送配置更新成功');
                } else {
                    addLog(`配置更新失败: ${data.message}`);
                }
            })
            .catch(error => addLog(`配置更新错误: ${error}`));
        }

        function testWechatPush() {
            addLog('测试微信推送...');

            fetch('/api/realtime/wechat/test', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'}
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    addLog('微信推送测试成功');
                } else {
                    addLog(`微信推送测试失败: ${data.message}`);
                }
            })
            .catch(error => addLog(`微信推送测试错误: ${error}`));
        }

        function loadWechatConfig() {
            fetch('/api/realtime/config')
            .then(response => response.json())
            .then(data => {
                if (data.success && data.config) {
                    const config = data.config;
                    document.getElementById('wechat-push-enabled').value = config.wechat_push_enabled ? 'true' : 'false';
                    document.getElementById('wechat-push-interval').value = config.wechat_push_interval_minutes || 30;
                }
            })
            .catch(error => console.error('加载微信配置失败:', error));
        }
        
        // 定期更新
        setInterval(updateStatus, 5000);
        setInterval(updatePrediction, 3000);
        
        // 初始化
        addLog('增强预测系统界面加载完成');
        updateStatus();
        loadWechatConfig();
    </script>
</body>
</html>
'''


@app.route('/')
def index():
    """主页"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/engine/start', methods=['POST'])
def start_prediction_engine():
    """启动预测引擎"""
    try:
        config = request.json or {}
        result = controller.start_engine(config)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/engine/stop', methods=['POST'])
def stop_prediction_engine():
    """停止预测引擎"""
    try:
        result = controller.stop_engine()
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/engine/status')
def get_engine_status():
    """获取引擎状态"""
    try:
        status = controller.get_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/api/prediction/latest')
def get_latest_prediction():
    """获取最新预测"""
    try:
        prediction = controller.get_latest_prediction()
        if prediction:
            return jsonify(prediction)
        else:
            return jsonify({'message': '暂无预测数据'})
    except Exception as e:
        return jsonify({'error': str(e)})


def main():
    """主函数"""
    print("简化版增强Web界面")
    print("=" * 40)
    print(f"[启动] Web服务器...")
    print(f"[地址] http://localhost:5003")
    
    try:
        app.run(host='0.0.0.0', port=5003, debug=False)
    except KeyboardInterrupt:
        print("\n[停止] 服务器已停止")
        controller.stop_engine()


if __name__ == "__main__":
    main()
