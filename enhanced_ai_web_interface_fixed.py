#!/usr/bin/env python3
"""
修复版增强AI Web界面
确保前后端数据格式完全匹配
"""

# 修复版HTML模板 - 适配统一平台的API格式
ENHANCED_AI_WEB_TEMPLATE = '''
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
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .header p { font-size: 1.2em; opacity: 0.9; }
        
        .dashboard { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px; }
        .card { background: rgba(255,255,255,0.1); border-radius: 15px; padding: 20px; backdrop-filter: blur(10px); }
        .card h3 { margin-bottom: 15px; color: #ecf0f1; }
        
        .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
        .status-item { background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; text-align: center; }
        .status-value { font-size: 1.5em; font-weight: bold; margin-top: 5px; }
        .status-running { color: #2ecc71; }
        .status-stopped { color: #e74c3c; }
        
        .prediction-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; }
        .prediction-item { background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; text-align: center; }
        .prediction-value { font-size: 1.3em; font-weight: bold; margin-top: 5px; }
        .price-up { color: #2ecc71; }
        .price-down { color: #e74c3c; }
        .price-neutral { color: #f39c12; }
        
        .controls { display: flex; gap: 15px; margin-bottom: 20px; flex-wrap: wrap; }
        .btn { padding: 12px 24px; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; transition: all 0.3s; }
        .btn-primary { background: #3498db; color: white; }
        .btn-danger { background: #e74c3c; color: white; }
        .btn-success { background: #2ecc71; color: white; }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.3); }
        
        .modules-section { margin-top: 20px; }
        .modules-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; }
        .module-card { background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; }
        .module-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
        .module-toggle { position: relative; display: inline-block; width: 60px; height: 34px; }
        .module-toggle input { opacity: 0; width: 0; height: 0; }
        .slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #ccc; transition: .4s; border-radius: 34px; }
        .slider:before { position: absolute; content: ""; height: 26px; width: 26px; left: 4px; bottom: 4px; background-color: white; transition: .4s; border-radius: 50%; }
        input:checked + .slider { background-color: #2ecc71; }
        input:checked + .slider:before { transform: translateX(26px); }
        
        .module-enabled { border-left: 4px solid #2ecc71; }
        .module-disabled { border-left: 4px solid #e74c3c; }
        
        .log-section { margin-top: 30px; }
        .log-container { background: rgba(0,0,0,0.3); border-radius: 10px; padding: 20px; height: 200px; overflow-y: auto; font-family: monospace; }
        .log-entry { margin-bottom: 5px; padding: 5px; border-radius: 3px; }
        .log-info { background: rgba(52, 152, 219, 0.2); }
        .log-success { background: rgba(46, 204, 113, 0.2); }
        .log-error { background: rgba(231, 76, 60, 0.2); }
        
        @media (max-width: 768px) {
            .dashboard { grid-template-columns: 1fr; }
            .controls { flex-direction: column; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 增强AI预测系统</h1>
            <p>智能黄金价格预测与分析平台</p>
        </div>
        
        <div class="dashboard">
            <!-- 系统状态卡片 -->
            <div class="card">
                <h3>📊 系统状态</h3>
                <div class="status-grid">
                    <div class="status-item">
                        <div>系统状态</div>
                        <div class="status-value" id="ai-status">检查中...</div>
                    </div>
                    <div class="status-item">
                        <div>启用模块</div>
                        <div class="status-value" id="enabled-features">0</div>
                    </div>
                    <div class="status-item">
                        <div>预测次数</div>
                        <div class="status-value" id="prediction-count">0</div>
                    </div>
                    <div class="status-item">
                        <div>系统置信度</div>
                        <div class="status-value" id="system-confidence">0%</div>
                    </div>
                </div>
            </div>
            
            <!-- 预测结果卡片 -->
            <div class="card">
                <h3>🔮 最新预测</h3>
                <div class="prediction-grid">
                    <div class="prediction-item">
                        <div>当前价格</div>
                        <div class="prediction-value" id="current-price">$0.00</div>
                    </div>
                    <div class="prediction-item">
                        <div>预测价格</div>
                        <div class="prediction-value" id="ai-predicted-price">$0.00</div>
                    </div>
                    <div class="prediction-item">
                        <div>价格变化</div>
                        <div class="prediction-value" id="ai-price-change">$0.00</div>
                    </div>
                    <div class="prediction-item">
                        <div>交易信号</div>
                        <div class="prediction-value" id="ai-trading-signal">等待中</div>
                    </div>
                    <div class="prediction-item">
                        <div>置信度</div>
                        <div class="prediction-value" id="ai-confidence-value">0%</div>
                    </div>
                    <div class="prediction-item">
                        <div>贡献模型</div>
                        <div class="prediction-value" id="contributing-models">0</div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- 控制按钮 -->
        <div class="controls">
            <button class="btn btn-success" onclick="startAISystem()">🚀 启动系统</button>
            <button class="btn btn-danger" onclick="stopAISystem()">⏹️ 停止系统</button>
            <button class="btn btn-primary" onclick="manualPredict()">🔮 手动预测</button>
            <button class="btn btn-primary" onclick="refreshStatus()">🔄 刷新状态</button>
        </div>
        
        <!-- 模块配置 -->
        <div class="card modules-section">
            <h3>⚙️ 模块配置</h3>
            <div class="modules-grid" id="modules-container">
                <!-- 模块将通过JavaScript动态生成 -->
            </div>
        </div>
        
        <!-- 系统日志 -->
        <div class="card log-section">
            <h3>📝 系统日志</h3>
            <div class="log-container" id="log-container">
                <!-- 日志将通过JavaScript动态添加 -->
            </div>
        </div>
    </div>

    <script>
        // 全局变量
        let systemRunning = false;
        let currentConfig = {};
        
        // 启动AI系统
        async function startAISystem() {
            try {
                addLog('正在启动增强AI系统...', 'info');
                const response = await fetch('/api/ai_enhanced/start', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(currentConfig)
                });
                const result = await response.json();
                
                if (result.success) {
                    addLog('✅ 增强AI系统启动成功', 'success');
                    systemRunning = true;
                } else {
                    addLog(`❌ 启动失败: ${result.message}`, 'error');
                }
                
                refreshStatus();
            } catch (error) {
                addLog(`❌ 启动错误: ${error.message}`, 'error');
            }
        }
        
        // 停止AI系统
        async function stopAISystem() {
            try {
                addLog('正在停止增强AI系统...', 'info');
                const response = await fetch('/api/ai_enhanced/stop', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                const result = await response.json();
                
                if (result.success) {
                    addLog('✅ 增强AI系统已停止', 'success');
                    systemRunning = false;
                } else {
                    addLog(`❌ 停止失败: ${result.message}`, 'error');
                }
                
                refreshStatus();
            } catch (error) {
                addLog(`❌ 停止错误: ${error.message}`, 'error');
            }
        }
        
        // 手动预测
        async function manualPredict() {
            try {
                addLog('正在执行手动预测...', 'info');
                const response = await fetch('/api/ai_enhanced/predict');
                const result = await response.json();
                
                if (result.success) {
                    addLog('✅ 预测完成', 'success');
                    updatePredictionDisplay(result);
                } else {
                    addLog(`❌ 预测失败: ${result.message || '未知错误'}`, 'error');
                }
            } catch (error) {
                addLog(`❌ 预测错误: ${error.message}`, 'error');
            }
        }
        
        // 刷新状态
        async function refreshStatus() {
            try {
                const response = await fetch('/api/ai_enhanced/status');
                const data = await response.json();

                // 更新系统状态显示
                updateStatusDisplay(data);

                // 更新模块配置显示
                updateModulesDisplay(data);

            } catch (error) {
                addLog(`❌ 状态更新错误: ${error.message}`, 'error');
            }
        }

        // 更新状态显示
        function updateStatusDisplay(data) {
            const statusElement = document.getElementById('ai-status');
            const isRunning = data.running || data.system_running || false;

            statusElement.textContent = isRunning ? '运行中' : '已停止';
            statusElement.className = `status-value ${isRunning ? 'status-running' : 'status-stopped'}`;

            // 更新其他状态信息
            document.getElementById('enabled-features').textContent =
                (data.enabled_features && data.enabled_features.length) || 0;

            document.getElementById('prediction-count').textContent =
                (data.performance_metrics && data.performance_metrics.total_predictions) || 0;

            const avgConfidence = data.performance_metrics && data.performance_metrics.average_confidence;
            document.getElementById('system-confidence').textContent =
                avgConfidence ? `${(avgConfidence * 100).toFixed(1)}%` : '0%';

            systemRunning = isRunning;
        }

        // 更新预测显示
        function updatePredictionDisplay(data) {
            if (!data || !data.success) return;

            // 更新当前价格
            if (data.current_price) {
                document.getElementById('current-price').textContent = `$${data.current_price.toFixed(2)}`;
            }

            // 更新预测价格
            if (data.predicted_price) {
                document.getElementById('ai-predicted-price').textContent = `$${data.predicted_price.toFixed(2)}`;

                // 计算价格变化
                const currentPrice = data.current_price || 0;
                const predictedPrice = data.predicted_price || 0;
                const priceChange = predictedPrice - currentPrice;
                const priceChangeElement = document.getElementById('ai-price-change');

                priceChangeElement.textContent = `${priceChange >= 0 ? '+' : ''}$${priceChange.toFixed(2)}`;
                priceChangeElement.className = `prediction-value ${
                    priceChange > 0 ? 'price-up' : priceChange < 0 ? 'price-down' : 'price-neutral'
                }`;
            }

            // 更新交易信号
            if (data.signal) {
                const signalElement = document.getElementById('ai-trading-signal');
                signalElement.textContent = data.signal;
                signalElement.className = `prediction-value ${
                    data.signal.includes('涨') || data.signal.includes('买') ? 'price-up' :
                    data.signal.includes('跌') || data.signal.includes('卖') ? 'price-down' : 'price-neutral'
                }`;
            }

            // 更新置信度
            if (data.confidence !== undefined) {
                document.getElementById('ai-confidence-value').textContent = `${(data.confidence * 100).toFixed(1)}%`;
            }

            // 更新贡献模型数量
            const contributingModels = data.individual_predictions ? Object.keys(data.individual_predictions).length : 0;
            document.getElementById('contributing-models').textContent = contributingModels;
        }

        // 更新模块显示
        function updateModulesDisplay(data) {
            const container = document.getElementById('modules-container');
            const enabledFeatures = data.enabled_features || [];
            const availableModules = data.available_modules || ['advanced_technical', 'deep_learning', 'gpu_acceleration', 'sentiment_analysis'];

            const moduleNames = {
                'advanced_technical': '高级技术指标',
                'deep_learning': '深度学习',
                'gpu_acceleration': 'GPU加速',
                'sentiment_analysis': '情绪分析'
            };

            container.innerHTML = '';

            availableModules.forEach(moduleId => {
                const isEnabled = enabledFeatures.includes(moduleId);
                const moduleName = moduleNames[moduleId] || moduleId;

                const moduleCard = document.createElement('div');
                moduleCard.className = `module-card ${isEnabled ? 'module-enabled' : 'module-disabled'}`;
                moduleCard.innerHTML = `
                    <div class="module-header">
                        <span><strong>${moduleName}</strong></span>
                        <label class="module-toggle">
                            <input type="checkbox" ${isEnabled ? 'checked' : ''}
                                   onchange="toggleModule('${moduleId}', this.checked)">
                            <span class="slider"></span>
                        </label>
                    </div>
                    <div style="font-size: 0.9em; opacity: 0.8;">
                        状态: ${isEnabled ? '✅ 已启用' : '❌ 已禁用'}
                    </div>
                `;

                container.appendChild(moduleCard);
            });
        }

        // 切换模块
        async function toggleModule(moduleId, enabled) {
            try {
                addLog(`正在${enabled ? '启用' : '禁用'}模块: ${moduleId}`, 'info');

                // 获取当前配置
                const configResponse = await fetch('/api/ai_enhanced/config');
                const currentConfig = await configResponse.json();

                // 更新配置
                if (!currentConfig.optional_features) {
                    currentConfig.optional_features = {};
                }
                currentConfig.optional_features[moduleId] = enabled;

                // 保存配置
                const response = await fetch('/api/ai_enhanced/config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(currentConfig)
                });

                const result = await response.json();

                if (result.success) {
                    addLog(`✅ 模块 ${moduleId} ${enabled ? '启用' : '禁用'}成功`, 'success');
                    // 延迟刷新状态，给系统时间处理配置更改
                    setTimeout(refreshStatus, 1000);
                } else {
                    addLog(`❌ 模块配置失败: ${result.message}`, 'error');
                    // 恢复复选框状态
                    event.target.checked = !enabled;
                }

            } catch (error) {
                addLog(`❌ 模块配置错误: ${error.message}`, 'error');
                // 恢复复选框状态
                event.target.checked = !enabled;
            }
        }

        // 添加日志
        function addLog(message, type = 'info') {
            const logContainer = document.getElementById('log-container');
            const timestamp = new Date().toLocaleTimeString();
            const logEntry = document.createElement('div');
            logEntry.className = `log-entry log-${type}`;
            logEntry.textContent = `[${timestamp}] ${message}`;

            logContainer.appendChild(logEntry);
            logContainer.scrollTop = logContainer.scrollHeight;

            // 限制日志条数
            while (logContainer.children.length > 50) {
                logContainer.removeChild(logContainer.firstChild);
            }
        }

        // 自动更新预测
        async function autoUpdatePrediction() {
            if (systemRunning) {
                try {
                    const response = await fetch('/api/ai_enhanced/predict');
                    const result = await response.json();

                    if (result.success) {
                        updatePredictionDisplay(result);
                    }
                } catch (error) {
                    // 静默处理自动更新错误
                    console.error('自动预测更新错误:', error);
                }
            }
        }

        // 初始化和定期更新
        document.addEventListener('DOMContentLoaded', function() {
            addLog('🚀 增强AI预测系统界面加载完成', 'success');
            refreshStatus();

            // 定期更新
            setInterval(refreshStatus, 10000);  // 每10秒更新状态
            setInterval(autoUpdatePrediction, 5000);  // 每5秒更新预测
        });
    </script>
</body>
</html>
'''
