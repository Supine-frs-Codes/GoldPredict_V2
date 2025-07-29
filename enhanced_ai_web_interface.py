#!/usr/bin/env python3
"""
增强AI预测系统Web界面
专门用于管理和展示AI预测系统的高级功能
"""

import json
import threading
import time
from datetime import datetime
from pathlib import Path
from flask import Flask, jsonify, request, render_template_string
import logging

from enhanced_ai_prediction_system import EnhancedAIPredictionSystem

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 全局变量
ai_system = None


class EnhancedAIWebController:
    """增强AI Web控制器"""
    
    def __init__(self):
        self.ai_system = None
        self.running = False
        self.default_config = {
            'core': {
                'interval_minutes': 5,
                'data_collection_seconds': 5,
                'min_data_points': 10,
                'auto_optimize': True
            },
            'optional_features': {
                'advanced_technical': True,
                'deep_learning': False,
                'gpu_acceleration': False,
                'sentiment_analysis': False
            },
            'feature_weights': {
                'core_prediction': 0.5,
                'advanced_technical': 0.2,
                'deep_learning': 0.2,
                'sentiment_analysis': 0.1
            }
        }
        self.load_config()
    
    def load_config(self):
        """加载配置"""
        config_path = Path("configs/enhanced_ai_config.json")
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    saved_config = json.load(f)
                    self.default_config.update(saved_config)
                    print(f"[配置] 已加载AI配置: {saved_config}")
            except Exception as e:
                print(f"[配置] 加载AI配置失败: {e}")
    
    def save_config(self):
        """保存配置"""
        config_path = Path("configs/enhanced_ai_config.json")
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(config_path, 'w') as f:
                json.dump(self.default_config, f, indent=2)
            print(f"[配置] AI配置已保存")
        except Exception as e:
            print(f"[配置] 保存AI配置失败: {e}")
    
    def start_ai_system(self, config=None):
        """启动AI系统"""
        global ai_system
        
        if ai_system and hasattr(ai_system, 'core_engine') and ai_system.core_engine and ai_system.core_engine.running:
            return {'success': False, 'message': 'AI系统已在运行中'}
        
        try:
            if config:
                self.default_config.update(config)
                self.save_config()
            
            ai_system = EnhancedAIPredictionSystem(self.default_config)
            
            if ai_system.start_system():
                self.running = True
                return {'success': True, 'message': '增强AI预测系统已启动', 'config': self.default_config}
            else:
                return {'success': False, 'message': 'AI系统启动失败'}
            
        except Exception as e:
            logger.error(f"启动AI系统失败: {e}")
            return {'success': False, 'message': f'启动失败: {str(e)}'}
    
    def stop_ai_system(self):
        """停止AI系统"""
        global ai_system
        
        if ai_system:
            ai_system.stop_system()
            ai_system = None
            self.running = False
            return {'success': True, 'message': '增强AI预测系统已停止'}
        
        return {'success': False, 'message': 'AI系统未运行'}
    
    def get_ai_status(self):
        """获取AI系统状态"""
        global ai_system
        
        if not ai_system:
            return {
                'running': False,
                'config': self.default_config,
                'enabled_features': [],
                'available_modules': []
            }
        
        return ai_system.get_system_status()
    
    def get_enhanced_prediction(self):
        """获取增强预测"""
        global ai_system
        
        if ai_system:
            return ai_system.make_enhanced_prediction()
        return {'success': False, 'message': 'AI系统未运行'}
    
    def update_ai_config(self, new_config):
        """更新AI配置"""
        try:
            self.default_config.update(new_config)
            self.save_config()
            
            if ai_system:
                ai_system.update_configuration(new_config)
            
            return {'success': True, 'config': self.default_config}
        except Exception as e:
            return {'success': False, 'message': str(e)}


# 创建控制器实例
controller = EnhancedAIWebController()

# 简化的HTML模板
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🤖 增强AI预测系统</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
            color: white; min-height: 100vh; padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 30px; }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; color: #f39c12; }
        .panel {
            background: rgba(255,255,255,0.1); padding: 20px; border-radius: 15px;
            backdrop-filter: blur(10px); margin-bottom: 20px;
        }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .btn {
            padding: 10px 20px; border: none; border-radius: 25px; font-weight: bold;
            cursor: pointer; margin: 5px; transition: all 0.3s ease;
        }
        .btn-primary { background: linear-gradient(45deg, #e74c3c, #c0392b); color: white; }
        .btn-secondary { background: linear-gradient(45deg, #3498db, #2980b9); color: white; }
        .btn-success { background: linear-gradient(45deg, #27ae60, #229954); color: white; }
        .btn:hover { transform: translateY(-2px); }
        .status-item { text-align: center; padding: 15px; background: rgba(255,255,255,0.1); border-radius: 10px; margin: 10px; }
        .status-value { font-size: 1.5em; font-weight: bold; color: #f39c12; }
        .config-row { display: flex; align-items: center; margin: 10px 0; }
        .config-row label { flex: 1; margin-right: 10px; }
        .config-row select, .config-row input {
            flex: 1; padding: 8px; border: none; border-radius: 5px;
            background: rgba(255,255,255,0.2); color: white;
        }
        .feature-toggle { display: flex; align-items: center; margin: 10px 0; }
        .feature-toggle input[type="checkbox"] { margin-right: 10px; }
        .prediction-card {
            text-align: center; padding: 20px; background: rgba(255,255,255,0.1);
            border-radius: 15px; margin: 10px;
        }
        .price-display { font-size: 2em; font-weight: bold; margin: 10px 0; color: #f39c12; }
        .signal-display {
            padding: 8px 16px; border-radius: 20px; font-weight: bold; margin: 10px 0;
            background: linear-gradient(45deg, #3498db, #2980b9);
        }
        .log-container {
            background: rgba(0,0,0,0.3); padding: 15px; border-radius: 10px;
            height: 200px; overflow-y: auto; font-family: monospace; font-size: 0.9em;
        }
        .module-status { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; }
        .module-item { padding: 10px; background: rgba(255,255,255,0.1); border-radius: 8px; }
        .module-enabled { border-left: 4px solid #27ae60; }
        .module-disabled { border-left: 4px solid #e74c3c; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 增强AI预测系统</h1>
            <p>集成高级技术指标、深度学习和情绪分析</p>
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
                
                <h3>🔧 可选功能</h3>
                <div class="feature-toggle">
                    <input type="checkbox" id="advanced-technical" checked>
                    <label>高级技术指标分析</label>
                </div>
                <div class="feature-toggle">
                    <input type="checkbox" id="deep-learning">
                    <label>深度学习模型</label>
                </div>
                <div class="feature-toggle">
                    <input type="checkbox" id="gpu-acceleration">
                    <label>GPU加速计算</label>
                </div>
                <div class="feature-toggle">
                    <input type="checkbox" id="sentiment-analysis">
                    <label>市场情绪分析</label>
                </div>
                
                <div style="text-align: center; margin-top: 20px;">
                    <button class="btn btn-primary" onclick="startAISystem()">🚀 启动AI系统</button>
                    <button class="btn btn-secondary" onclick="stopAISystem()">⏹️ 停止AI系统</button>
                    <button class="btn btn-success" onclick="saveAIConfig()">💾 保存配置</button>
                </div>
            </div>
            
            <div class="panel">
                <h2>📊 系统状态</h2>
                <div class="status-item">
                    <div class="status-value" id="ai-status">未启动</div>
                    <div>AI系统状态</div>
                </div>
                <div class="status-item">
                    <div class="status-value" id="enabled-features">0</div>
                    <div>启用功能数</div>
                </div>
                <div class="status-item">
                    <div class="status-value" id="prediction-models">0</div>
                    <div>预测模型数</div>
                </div>
            </div>
        </div>
        
        <div class="grid">
            <div class="prediction-card">
                <h3>💰 当前价格</h3>
                <div class="price-display" id="current-price">$--</div>
            </div>
            <div class="prediction-card">
                <h3>🤖 AI增强预测</h3>
                <div class="price-display" id="ai-predicted-price">$--</div>
                <div class="signal-display" id="ai-trading-signal">等待预测</div>
                <div>置信度: <span id="ai-confidence-value">--%</span></div>
                <div>贡献模型: <span id="contributing-models">0</span>个</div>
            </div>
            <div class="prediction-card">
                <h3>📈 价格变化</h3>
                <div class="price-display" id="ai-price-change">--</div>
                <div id="ai-price-change-pct">--%</div>
            </div>
        </div>
        
        <div class="panel">
            <h2>🔧 模块状态</h2>
            <div class="module-status" id="module-status">
                <div class="module-item module-disabled">
                    <div><strong>高级技术指标</strong></div>
                    <div>状态: 未启用</div>
                </div>
                <div class="module-item module-disabled">
                    <div><strong>深度学习</strong></div>
                    <div>状态: 未启用</div>
                </div>
                <div class="module-item module-disabled">
                    <div><strong>GPU加速</strong></div>
                    <div>状态: 未启用</div>
                </div>
                <div class="module-item module-disabled">
                    <div><strong>情绪分析</strong></div>
                    <div>状态: 未启用</div>
                </div>
            </div>
        </div>
        
        <div class="panel">
            <h2>📊 各模型预测对比</h2>
            <div id="model-predictions" class="grid">
                <div class="prediction-card">
                    <h4>核心预测</h4>
                    <div id="core-prediction">等待数据</div>
                </div>
                <div class="prediction-card">
                    <h4>技术指标</h4>
                    <div id="technical-prediction">未启用</div>
                </div>
                <div class="prediction-card">
                    <h4>深度学习</h4>
                    <div id="dl-prediction">未启用</div>
                </div>
                <div class="prediction-card">
                    <h4>情绪分析</h4>
                    <div id="sentiment-prediction">未启用</div>
                </div>
            </div>
        </div>
        
        <div class="panel">
            <h2>📝 系统日志</h2>
            <div class="log-container" id="ai-log-container">
                <div>[等待] 增强AI预测系统准备就绪</div>
            </div>
        </div>
    </div>
    
    <script>
        function getAIConfig() {
            return {
                core: {
                    interval_minutes: parseInt(document.getElementById('interval-minutes').value),
                    data_collection_seconds: parseInt(document.getElementById('data-collection-seconds').value),
                    min_data_points: 10,
                    auto_optimize: true
                },
                optional_features: {
                    advanced_technical: document.getElementById('advanced-technical').checked,
                    deep_learning: document.getElementById('deep-learning').checked,
                    gpu_acceleration: document.getElementById('gpu-acceleration').checked,
                    sentiment_analysis: document.getElementById('sentiment-analysis').checked
                }
            };
        }
        
        function startAISystem() {
            const config = getAIConfig();
            addAILog(`启动AI系统: ${JSON.stringify(config.optional_features)}`);
            
            fetch('/api/ai/start', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(config)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    addAILog('增强AI预测系统启动成功');
                } else {
                    addAILog(`启动失败: ${data.message}`);
                }
            })
            .catch(error => addAILog(`启动错误: ${error}`));
        }
        
        function stopAISystem() {
            fetch('/api/ai/stop', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    addAILog('增强AI预测系统已停止');
                } else {
                    addAILog(`停止失败: ${data.message}`);
                }
            })
            .catch(error => addAILog(`停止错误: ${error}`));
        }
        
        function saveAIConfig() {
            const config = getAIConfig();
            
            fetch('/api/ai/config', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(config)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    addAILog('AI配置已保存');
                } else {
                    addAILog(`配置保存失败: ${data.message}`);
                }
            })
            .catch(error => addAILog(`配置错误: ${error}`));
        }
        
        function updateAIStatus() {
            fetch('/api/ai/status')
            .then(response => response.json())
            .then(data => {
                document.getElementById('ai-status').textContent = data.system_running ? '运行中' : '已停止';
                document.getElementById('enabled-features').textContent = data.enabled_features ? data.enabled_features.length : 0;
                
                // 更新模块状态
                updateModuleStatus(data);
            })
            .catch(error => console.error('AI状态更新错误:', error));
        }
        
        function updateModuleStatus(data) {
            const moduleContainer = document.getElementById('module-status');
            const enabledFeatures = data.enabled_features || [];
            
            const modules = [
                {id: 'advanced_technical', name: '高级技术指标'},
                {id: 'deep_learning', name: '深度学习'},
                {id: 'gpu_acceleration', name: 'GPU加速'},
                {id: 'sentiment_analysis', name: '情绪分析'}
            ];
            
            moduleContainer.innerHTML = '';
            modules.forEach(module => {
                const isEnabled = enabledFeatures.includes(module.id);
                const moduleDiv = document.createElement('div');
                moduleDiv.className = `module-item ${isEnabled ? 'module-enabled' : 'module-disabled'}`;
                moduleDiv.innerHTML = `
                    <div><strong>${module.name}</strong></div>
                    <div>状态: ${isEnabled ? '已启用' : '未启用'}</div>
                `;
                moduleContainer.appendChild(moduleDiv);
            });
        }
        
        function updateAIPrediction() {
            fetch('/api/ai/prediction')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const final = data.final_prediction;
                    document.getElementById('current-price').textContent = `$${data.current_price.toFixed(2)}`;
                    document.getElementById('ai-predicted-price').textContent = `$${final.price.toFixed(2)}`;
                    document.getElementById('ai-trading-signal').textContent = final.signal;
                    document.getElementById('ai-confidence-value').textContent = `${(final.confidence * 100).toFixed(1)}%`;
                    document.getElementById('contributing-models').textContent = final.contributing_models;
                    
                    const priceChange = final.price - data.current_price;
                    const priceChangePct = (priceChange / data.current_price * 100);
                    document.getElementById('ai-price-change').textContent = 
                        `${priceChange >= 0 ? '+' : ''}$${priceChange.toFixed(2)}`;
                    document.getElementById('ai-price-change-pct').textContent = 
                        `${priceChangePct >= 0 ? '+' : ''}${priceChangePct.toFixed(3)}%`;
                    
                    // 更新各模型预测
                    updateModelPredictions(data.individual_predictions);
                }
            })
            .catch(error => console.error('AI预测更新错误:', error));
        }
        
        function updateModelPredictions(predictions) {
            const models = ['core', 'advanced_technical', 'deep_learning', 'sentiment_analysis'];
            const elements = ['core-prediction', 'technical-prediction', 'dl-prediction', 'sentiment-prediction'];
            
            models.forEach((model, index) => {
                const element = document.getElementById(elements[index]);
                if (predictions[model] && predictions[model].price) {
                    element.textContent = `$${predictions[model].price.toFixed(2)} (${predictions[model].signal})`;
                } else if (predictions[model]) {
                    element.textContent = `信号: ${predictions[model].signal}`;
                } else {
                    element.textContent = '未启用';
                }
            });
        }
        
        function addAILog(message) {
            const logContainer = document.getElementById('ai-log-container');
            const timestamp = new Date().toLocaleTimeString();
            const logEntry = document.createElement('div');
            logEntry.textContent = `[${timestamp}] ${message}`;
            logContainer.appendChild(logEntry);
            logContainer.scrollTop = logContainer.scrollHeight;
            
            while (logContainer.children.length > 50) {
                logContainer.removeChild(logContainer.firstChild);
            }
        }
        
        // 定期更新
        setInterval(updateAIStatus, 5000);
        setInterval(updateAIPrediction, 3000);
        
        // 初始化
        addAILog('增强AI预测系统界面加载完成');
        updateAIStatus();
    </script>
</body>
</html>
'''


@app.route('/')
def index():
    """主页"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/ai/start', methods=['POST'])
def start_ai_system():
    """启动AI系统"""
    try:
        config = request.json or {}
        result = controller.start_ai_system(config)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/ai/stop', methods=['POST'])
def stop_ai_system():
    """停止AI系统"""
    try:
        result = controller.stop_ai_system()
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/ai/status')
def get_ai_status():
    """获取AI系统状态"""
    try:
        status = controller.get_ai_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/api/ai/prediction')
def get_ai_prediction():
    """获取AI增强预测"""
    try:
        prediction = controller.get_enhanced_prediction()
        return jsonify(prediction)
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/api/ai/config', methods=['GET', 'POST'])
def manage_ai_config():
    """管理AI配置"""
    if request.method == 'GET':
        return jsonify(controller.default_config)
    
    elif request.method == 'POST':
        try:
            new_config = request.json
            result = controller.update_ai_config(new_config)
            return jsonify(result)
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})


def main():
    """主函数"""
    print("增强AI预测系统Web界面")
    print("=" * 40)
    print(f"[启动] 增强AI Web界面服务器...")
    print(f"[地址] http://localhost:5004")
    print(f"[功能] 高级技术指标、深度学习、GPU加速、情绪分析")
    
    try:
        app.run(host='0.0.0.0', port=5004, debug=False)
    except KeyboardInterrupt:
        print("\n[停止] 服务器已停止")
        controller.stop_ai_system()


if __name__ == "__main__":
    main()
