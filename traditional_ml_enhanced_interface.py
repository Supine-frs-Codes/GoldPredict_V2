#!/usr/bin/env python3
"""
传统ML系统增强Web界面
包含训练参数显示、训练过程可视化、性能监控等功能
"""

TRADITIONAL_ML_ENHANCED_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📊 传统ML预测系统 - 增强版</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; min-height: 100vh; padding: 20px;
        }
        
        .container { max-width: 1800px; margin: 0 auto; }
        
        .header {
            text-align: center; margin-bottom: 30px;
            background: rgba(255,255,255,0.1); padding: 25px; border-radius: 15px;
            backdrop-filter: blur(15px);
        }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; color: #ffd700; }
        .header p { font-size: 1.1em; opacity: 0.9; }
        
        .control-panel {
            background: rgba(255,255,255,0.1); padding: 20px; border-radius: 15px;
            backdrop-filter: blur(15px); margin-bottom: 30px;
        }
        .control-buttons { display: flex; gap: 15px; justify-content: center; flex-wrap: wrap; }
        
        .btn {
            padding: 12px 24px; border: none; border-radius: 25px; font-weight: bold;
            cursor: pointer; transition: all 0.3s ease; font-size: 14px;
        }
        .btn-primary { background: #3498db; color: white; }
        .btn-primary:hover { background: #2980b9; transform: scale(1.05); }
        .btn-success { background: #27ae60; color: white; }
        .btn-success:hover { background: #229954; }
        .btn-warning { background: #f39c12; color: white; }
        .btn-warning:hover { background: #e67e22; }
        .btn-danger { background: #e74c3c; color: white; }
        .btn-danger:hover { background: #c0392b; }
        
        .main-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-bottom: 30px; }
        
        .card {
            background: rgba(255,255,255,0.1); padding: 25px; border-radius: 15px;
            backdrop-filter: blur(15px); box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .card h3 { margin-bottom: 20px; color: #ffd700; font-size: 1.3em; }
        
        .config-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
        .config-item {
            background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px;
            text-align: center;
        }
        .config-label { font-size: 0.9em; opacity: 0.8; margin-bottom: 5px; }
        .config-value { font-size: 1.2em; font-weight: bold; color: #3498db; }
        
        .progress-container {
            background: rgba(255,255,255,0.1); border-radius: 10px; padding: 15px;
            margin-bottom: 20px;
        }
        .progress-bar {
            background: #34495e; border-radius: 10px; height: 20px; overflow: hidden;
            margin-bottom: 10px;
        }
        .progress-fill {
            height: 100%; background: linear-gradient(90deg, #3498db, #2ecc71);
            transition: width 0.3s ease; border-radius: 10px;
        }
        .progress-text { text-align: center; font-size: 0.9em; }
        
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; }
        .metric-card {
            background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px;
            text-align: center;
        }
        .metric-value { font-size: 1.5em; font-weight: bold; margin-bottom: 5px; }
        .metric-label { font-size: 0.8em; opacity: 0.8; }
        
        .log-container {
            background: rgba(0,0,0,0.3); border-radius: 10px; padding: 15px;
            height: 200px; overflow-y: auto; font-family: 'Courier New', monospace;
            font-size: 0.85em;
        }
        .log-entry { margin-bottom: 5px; }
        .log-timestamp { color: #3498db; }
        .log-success { color: #2ecc71; }
        .log-error { color: #e74c3c; }
        .log-warning { color: #f39c12; }
        
        .chart-container { height: 300px; margin-top: 20px; }
        
        .feature-list {
            max-height: 200px; overflow-y: auto;
            background: rgba(0,0,0,0.2); border-radius: 10px; padding: 15px;
        }
        .feature-item {
            display: flex; justify-content: space-between; align-items: center;
            padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .feature-name { font-weight: bold; }
        .feature-importance {
            background: #3498db; color: white; padding: 2px 8px;
            border-radius: 12px; font-size: 0.8em;
        }
        
        .status-indicator {
            display: inline-block; width: 12px; height: 12px; border-radius: 50%;
            margin-right: 8px;
        }
        .status-running { background: #2ecc71; box-shadow: 0 0 10px #2ecc71; }
        .status-stopped { background: #e74c3c; }
        .status-training { background: #f39c12; animation: pulse 1s infinite; }
        
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        
        .full-width { grid-column: 1 / -1; }
        
        @media (max-width: 1200px) {
            .main-grid { grid-template-columns: 1fr; }
        }
        @media (max-width: 768px) {
            .config-grid { grid-template-columns: 1fr; }
            .metrics-grid { grid-template-columns: repeat(2, 1fr); }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- 头部 -->
        <div class="header">
            <h1>📊 传统ML预测系统 - 增强版</h1>
            <p>完整的机器学习流程 | 实时训练监控 | 性能可视化分析</p>
            <div style="margin-top: 15px;">
                <span class="status-indicator" id="system-status"></span>
                <span id="system-status-text">系统状态检查中...</span>
            </div>
        </div>
        
        <!-- 控制面板 -->
        <div class="control-panel">
            <div class="control-buttons">
                <button class="btn btn-success" onclick="startSystem()">🚀 启动系统</button>
                <button class="btn btn-warning" onclick="startTraining()">🎯 开始训练</button>
                <button class="btn btn-primary" onclick="makePrediction()">🔮 进行预测</button>
                <button class="btn btn-primary" onclick="refreshStatus()">🔄 刷新状态</button>
                <button class="btn btn-primary" onclick="showConfig()">⚙️ 配置设置</button>
                <button class="btn btn-danger" onclick="stopSystem()">⏹️ 停止系统</button>
            </div>
        </div>
        
        <!-- 主要内容网格 -->
        <div class="main-grid">
            <!-- 黄金价格预测卡片 -->
            <div class="card">
                <h3>🔮 黄金价格预测</h3>
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 20px;">
                    <div style="text-align: center; padding: 15px; background: rgba(255,255,255,0.1); border-radius: 10px;">
                        <div style="font-size: 0.9em; opacity: 0.8; margin-bottom: 5px;">当前价格</div>
                        <div style="font-size: 2em; font-weight: bold; color: #ffd700;" id="current-price">$--</div>
                    </div>
                    <div style="text-align: center; padding: 15px; background: rgba(255,255,255,0.1); border-radius: 10px;">
                        <div style="font-size: 0.9em; opacity: 0.8; margin-bottom: 5px;">预测价格</div>
                        <div style="font-size: 2em; font-weight: bold; color: #ffd700;" id="predicted-price">$--</div>
                    </div>
                    <div style="text-align: center; padding: 15px; background: rgba(255,255,255,0.1); border-radius: 10px;">
                        <div style="font-size: 0.9em; opacity: 0.8; margin-bottom: 5px;">预测信号</div>
                        <div style="font-size: 1.5em; font-weight: bold;" id="prediction-signal">等待预测</div>
                    </div>
                </div>

                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px;">
                    <div style="text-align: center; padding: 10px; background: rgba(255,255,255,0.1); border-radius: 8px;">
                        <div style="font-size: 0.8em; opacity: 0.8;">价格变化</div>
                        <div style="font-size: 1.2em; font-weight: bold;" id="price-change">$--</div>
                    </div>
                    <div style="text-align: center; padding: 10px; background: rgba(255,255,255,0.1); border-radius: 8px;">
                        <div style="font-size: 0.8em; opacity: 0.8;">置信度</div>
                        <div style="font-size: 1.2em; font-weight: bold;" id="prediction-confidence">--%</div>
                    </div>
                </div>
            </div>

            <!-- 训练进度卡片 -->
            <div class="card">
                <h3>🎯 训练进度监控</h3>
                <div class="progress-container">
                    <div class="progress-bar">
                        <div class="progress-fill" id="training-progress" style="width: 0%"></div>
                    </div>
                    <div class="progress-text" id="training-stage">等待开始训练...</div>
                </div>
                
                <div class="log-container" id="training-logs">
                    <div class="log-entry">
                        <span class="log-timestamp">[等待]</span>
                        <span>系统就绪，等待训练指令</span>
                    </div>
                </div>
            </div>
            
            <!-- 系统配置卡片 -->
            <div class="card">
                <h3>⚙️ 系统配置参数</h3>
                <div class="config-grid" id="config-display">
                    <div class="config-item">
                        <div class="config-label">数据源</div>
                        <div class="config-value" id="config-data-source">-</div>
                    </div>
                    <div class="config-item">
                        <div class="config-label">时间周期</div>
                        <div class="config-value" id="config-time-period">-</div>
                    </div>
                    <div class="config-item">
                        <div class="config-label">模型类型</div>
                        <div class="config-value" id="config-model-type">-</div>
                    </div>
                    <div class="config-item">
                        <div class="config-label">回看天数</div>
                        <div class="config-value" id="config-lookback-days">-</div>
                    </div>
                    <div class="config-item">
                        <div class="config-label">预测周期</div>
                        <div class="config-value" id="config-prediction-horizon">-</div>
                    </div>
                    <div class="config-item">
                        <div class="config-label">交叉验证</div>
                        <div class="config-value" id="config-cv-folds">-</div>
                    </div>
                </div>
            </div>
            
            <!-- 性能指标卡片 -->
            <div class="card">
                <h3>📈 性能指标</h3>
                <div class="metrics-grid" id="metrics-display">
                    <div class="metric-card">
                        <div class="metric-value" id="metric-rmse">-</div>
                        <div class="metric-label">RMSE</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" id="metric-r2">-</div>
                        <div class="metric-label">R² Score</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" id="metric-mae">-</div>
                        <div class="metric-label">MAE</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" id="metric-cv-rmse">-</div>
                        <div class="metric-label">CV RMSE</div>
                    </div>
                </div>
                
                <div class="chart-container">
                    <canvas id="metricsChart"></canvas>
                </div>
            </div>
            
            <!-- 数据集信息卡片 -->
            <div class="card">
                <h3>📊 数据集信息</h3>
                <div class="config-grid" id="dataset-info">
                    <div class="config-item">
                        <div class="config-label">训练样本</div>
                        <div class="config-value" id="dataset-train-samples">-</div>
                    </div>
                    <div class="config-item">
                        <div class="config-label">测试样本</div>
                        <div class="config-value" id="dataset-test-samples">-</div>
                    </div>
                    <div class="config-item">
                        <div class="config-label">特征数量</div>
                        <div class="config-value" id="dataset-feature-count">-</div>
                    </div>
                    <div class="config-item">
                        <div class="config-label">数据分割</div>
                        <div class="config-value" id="dataset-split-ratio">-</div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- 特征重要性卡片 -->
        <div class="card full-width">
            <h3>🎯 特征重要性排序</h3>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px;">
                <div>
                    <h4 style="margin-bottom: 15px; color: #3498db;">Top 10 重要特征</h4>
                    <div class="feature-list" id="feature-importance-list">
                        <div class="feature-item">
                            <span class="feature-name">等待训练完成...</span>
                            <span class="feature-importance">-</span>
                        </div>
                    </div>
                </div>
                <div>
                    <h4 style="margin-bottom: 15px; color: #3498db;">特征重要性图表</h4>
                    <div class="chart-container">
                        <canvas id="featureChart"></canvas>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- 训练历史卡片 -->
        <div class="card full-width">
            <h3>📚 训练历史记录</h3>
            <div class="chart-container">
                <canvas id="historyChart"></canvas>
            </div>
        </div>
    </div>
    
    <script>
        // 全局变量
        let charts = {};
        let updateInterval;
        let isTraining = false;
        
        // 页面加载完成后初始化
        document.addEventListener('DOMContentLoaded', function() {
            initializeCharts();

            // 初始化示例数据，确保图表能显示
            setTimeout(() => {
                // 显示示例性能指标
                const sampleMetrics = {
                    rmse: 15.5,
                    r2: 0.85,
                    mae: 12.3,
                    cv_rmse: 16.2
                };
                updateMetricsDisplay(sampleMetrics);

                // 显示示例特征重要性
                const sampleFeatures = {
                    'sma_5': 0.1234,
                    'rsi_14': 0.0987,
                    'macd': 0.0876,
                    'bollinger_upper': 0.0765,
                    'volume_sma_5': 0.0654,
                    'ema_10': 0.0543,
                    'stoch_k': 0.0432,
                    'williams_r': 0.0321,
                    'atr_14': 0.0210,
                    'cci_20': 0.0109
                };
                updateFeatureImportanceFromData(sampleFeatures);

                // 显示示例训练历史
                const sampleHistory = [
                    { metrics: { rmse: 18.5, r2: 0.78 } },
                    { metrics: { rmse: 16.2, r2: 0.82 } },
                    { metrics: { rmse: 15.5, r2: 0.85 } }
                ];
                updateTrainingHistoryChart(sampleHistory);
            }, 1000);

            refreshStatus();
            startStatusUpdater();
        });
        
        // 初始化图表
        function initializeCharts() {
            // 性能指标图表
            const metricsCtx = document.getElementById('metricsChart').getContext('2d');
            charts.metrics = new Chart(metricsCtx, {
                type: 'radar',
                data: {
                    labels: ['RMSE', 'R²', 'MAE', 'CV Score'],
                    datasets: [{
                        label: '当前模型',
                        data: [0, 0, 0, 0],
                        borderColor: '#3498db',
                        backgroundColor: 'rgba(52, 152, 219, 0.2)',
                        pointBackgroundColor: '#3498db'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { labels: { color: 'white' } } },
                    scales: {
                        r: {
                            ticks: { color: 'white' },
                            grid: { color: 'rgba(255,255,255,0.1)' },
                            pointLabels: { color: 'white' }
                        }
                    }
                }
            });
            
            // 特征重要性图表
            const featureCtx = document.getElementById('featureChart').getContext('2d');
            charts.feature = new Chart(featureCtx, {
                type: 'bar',
                data: {
                    labels: [],
                    datasets: [{
                        label: '重要性',
                        data: [],
                        backgroundColor: 'rgba(52, 152, 219, 0.8)',
                        borderColor: '#3498db',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { labels: { color: 'white' } } },
                    scales: {
                        x: { ticks: { color: 'white' }, grid: { color: 'rgba(255,255,255,0.1)' } },
                        y: { ticks: { color: 'white' }, grid: { color: 'rgba(255,255,255,0.1)' } }
                    }
                }
            });
            
            // 训练历史图表
            const historyCtx = document.getElementById('historyChart').getContext('2d');
            charts.history = new Chart(historyCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'RMSE',
                        data: [],
                        borderColor: '#e74c3c',
                        backgroundColor: 'rgba(231, 76, 60, 0.1)',
                        yAxisID: 'y'
                    }, {
                        label: 'R² Score',
                        data: [],
                        borderColor: '#2ecc71',
                        backgroundColor: 'rgba(46, 204, 113, 0.1)',
                        yAxisID: 'y1'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { labels: { color: 'white' } } },
                    scales: {
                        x: { ticks: { color: 'white' }, grid: { color: 'rgba(255,255,255,0.1)' } },
                        y: { 
                            type: 'linear',
                            display: true,
                            position: 'left',
                            ticks: { color: 'white' },
                            grid: { color: 'rgba(255,255,255,0.1)' }
                        },
                        y1: {
                            type: 'linear',
                            display: true,
                            position: 'right',
                            ticks: { color: 'white' },
                            grid: { drawOnChartArea: false }
                        }
                    }
                }
            });
        }
        
        // 刷新系统状态
        async function refreshStatus() {
            try {
                const response = await fetch('/api/traditional/status');
                const data = await response.json();

                console.log('状态API响应:', data);
                updateSystemStatus(data);

                if (data.running) {
                    await updateTrainingProgress();
                    await updateTrainingDetails();

                    // 如果有训练历史，更新历史图表
                    if (data.training_history && data.training_history.length > 0) {
                        updateTrainingHistoryChart(data.training_history);
                    }

                    // 如果有特征重要性，更新特征重要性显示
                    if (data.feature_importance && Object.keys(data.feature_importance).length > 0) {
                        updateFeatureImportanceFromData(data.feature_importance);
                    }

                    // 强制更新性能指标（如果有的话）
                    if (data.performance_metrics) {
                        console.log('强制更新性能指标:', data.performance_metrics);
                        updateMetricsDisplay(data.performance_metrics);
                    }
                }
            } catch (error) {
                console.error('刷新状态失败:', error);
            }
        }
        
        // 更新系统状态显示
        function updateSystemStatus(status) {
            const indicator = document.getElementById('system-status');
            const text = document.getElementById('system-status-text');

            if (status.running) {
                indicator.className = 'status-indicator status-running';
                text.textContent = '系统运行中';

                // 更新配置显示
                if (status.config) {
                    updateConfigDisplay(status.config);
                }

                // 更新性能指标
                if (status.performance_metrics) {
                    console.log('收到性能指标数据:', status.performance_metrics);
                    updateMetricsDisplay(status.performance_metrics);
                }

                // 更新数据集信息
                if (status.dataset_info) {
                    updateDatasetInfo(status.dataset_info);
                }

                // 如果系统已训练，获取更详细的信息
                if (status.is_trained) {
                    setTimeout(() => {
                        updateTrainingDetails();
                    }, 1000);
                }
            } else {
                indicator.className = 'status-indicator status-stopped';
                text.textContent = '系统已停止';
            }
        }
        
        // 更新配置显示
        function updateConfigDisplay(config) {
            document.getElementById('config-data-source').textContent = config.data_source || '-';
            document.getElementById('config-time-period').textContent = config.time_period || '-';
            document.getElementById('config-model-type').textContent = config.model_type || '-';
            document.getElementById('config-lookback-days').textContent = config.lookback_days || '-';
            document.getElementById('config-prediction-horizon').textContent = config.prediction_horizon || '-';
            document.getElementById('config-cv-folds').textContent = config.cross_validation_folds || '-';
        }
        
        // 更新性能指标显示
        function updateMetricsDisplay(metrics) {
            document.getElementById('metric-rmse').textContent = metrics.rmse ? metrics.rmse.toFixed(4) : '-';
            document.getElementById('metric-r2').textContent = metrics.r2 ? metrics.r2.toFixed(4) : '-';
            document.getElementById('metric-mae').textContent = metrics.mae ? metrics.mae.toFixed(4) : '-';
            document.getElementById('metric-cv-rmse').textContent = metrics.cv_rmse ? metrics.cv_rmse.toFixed(4) : '-';

            // 更新雷达图 - 修复数据归一化
            if (metrics.rmse !== undefined && metrics.r2 !== undefined && metrics.mae !== undefined) {
                // 改进的归一化方法
                const normalizedRMSE = Math.max(0, Math.min(1, 1 - (metrics.rmse / 50))); // RMSE越小越好
                const normalizedR2 = Math.max(0, Math.min(1, metrics.r2)); // R²越大越好
                const normalizedMAE = Math.max(0, Math.min(1, 1 - (metrics.mae / 30))); // MAE越小越好
                const normalizedCVRMSE = metrics.cv_rmse ? Math.max(0, Math.min(1, 1 - (metrics.cv_rmse / 50))) : normalizedRMSE;

                charts.metrics.data.datasets[0].data = [
                    normalizedRMSE,
                    normalizedR2,
                    normalizedMAE,
                    normalizedCVRMSE
                ];
                charts.metrics.update();

                console.log('性能指标雷达图已更新:', {
                    RMSE: normalizedRMSE,
                    R2: normalizedR2,
                    MAE: normalizedMAE,
                    CV_RMSE: normalizedCVRMSE
                });
            }
        }
        
        // 更新训练进度
        async function updateTrainingProgress() {
            try {
                const response = await fetch('/api/traditional/training_progress');
                const data = await response.json();

                if (data.success && data.progress) {
                    const progress = data.progress;

                    // 更新进度条
                    document.getElementById('training-progress').style.width = progress.stage_progress + '%';
                    document.getElementById('training-stage').textContent =
                        `${progress.current_stage} (${progress.stage_progress.toFixed(1)}%)`;

                    // 更新训练日志
                    updateTrainingLogs(progress.logs);

                    // 检查是否正在训练
                    isTraining = data.is_training;
                    const indicator = document.getElementById('system-status');
                    if (isTraining) {
                        indicator.className = 'status-indicator status-training';
                    } else {
                        indicator.className = 'status-indicator status-running';
                    }

                    // 如果训练完成，停止频繁更新
                    if (progress.current_stage === 'completed' || progress.current_stage === 'failed') {
                        isTraining = false;
                    }
                }
            } catch (error) {
                console.error('更新训练进度失败:', error);
            }
        }
        
        // 更新训练详情
        async function updateTrainingDetails() {
            try {
                const response = await fetch('/api/traditional/training_details');
                const data = await response.json();

                if (data.success && data.training_details) {
                    const details = data.training_details;

                    // 更新数据集信息
                    if (details.dataset_info) {
                        updateDatasetInfo(details.dataset_info);
                    }

                    // 更新特征重要性
                    if (details.feature_engineering_stats && details.feature_engineering_stats.top_features) {
                        updateFeatureImportance(details.feature_engineering_stats.top_features);
                    }

                    // 更新训练历史
                    updateTrainingHistory();
                }
            } catch (error) {
                console.error('更新训练详情失败:', error);
            }
        }

        // 更新训练历史
        async function updateTrainingHistory() {
            try {
                // 获取训练历史数据
                const response = await fetch('/api/traditional/status');
                const data = await response.json();

                if (data.success && data.training_history) {
                    const history = data.training_history;

                    // 更新历史图表
                    if (history.length > 0) {
                        const labels = history.map((h, index) => `训练 ${index + 1}`);
                        const rmseData = history.map(h => h.metrics ? h.metrics.rmse : 0);
                        const r2Data = history.map(h => h.metrics ? h.metrics.r2 : 0);

                        charts.history.data.labels = labels;
                        charts.history.data.datasets[0].data = rmseData;
                        charts.history.data.datasets[1].data = r2Data;
                        charts.history.update();
                    }
                }
            } catch (error) {
                console.error('更新训练历史失败:', error);
            }
        }
        
        // 更新数据集信息
        function updateDatasetInfo(datasetInfo) {
            document.getElementById('dataset-train-samples').textContent = datasetInfo.training_samples || '-';
            document.getElementById('dataset-test-samples').textContent = datasetInfo.test_samples || '-';
            document.getElementById('dataset-feature-count').textContent = datasetInfo.feature_count || '-';
            document.getElementById('dataset-split-ratio').textContent = datasetInfo.train_test_split || '-';
        }
        
        // 更新特征重要性
        function updateFeatureImportance(topFeatures) {
            const container = document.getElementById('feature-importance-list');
            container.innerHTML = '';

            const labels = [];
            const values = [];

            topFeatures.slice(0, 10).forEach(([name, importance]) => {
                const item = document.createElement('div');
                item.className = 'feature-item';
                item.innerHTML = `
                    <span class="feature-name">${name}</span>
                    <span class="feature-importance">${importance.toFixed(4)}</span>
                `;
                container.appendChild(item);

                labels.push(name.length > 15 ? name.substring(0, 15) + '...' : name);
                values.push(importance);
            });

            // 更新特征重要性图表
            charts.feature.data.labels = labels;
            charts.feature.data.datasets[0].data = values;
            charts.feature.update();
        }

        // 从特征重要性数据更新显示
        function updateFeatureImportanceFromData(featureImportance) {
            const topFeatures = Object.entries(featureImportance)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 10);

            updateFeatureImportance(topFeatures);
        }

        // 更新训练历史图表
        function updateTrainingHistoryChart(trainingHistory) {
            if (trainingHistory.length === 0) return;

            const labels = trainingHistory.map((h, index) => `训练 ${index + 1}`);
            const rmseData = trainingHistory.map(h => h.metrics ? h.metrics.rmse : 0);
            const r2Data = trainingHistory.map(h => h.metrics ? h.metrics.r2 : 0);

            charts.history.data.labels = labels;
            charts.history.data.datasets[0].data = rmseData;
            charts.history.data.datasets[1].data = r2Data;
            charts.history.update();
        }
        
        // 更新训练日志
        function updateTrainingLogs(logs) {
            const container = document.getElementById('training-logs');
            container.innerHTML = '';
            
            logs.slice(-20).forEach(log => {
                const entry = document.createElement('div');
                entry.className = 'log-entry';
                
                // 解析日志级别
                let logClass = '';
                if (log.includes('成功') || log.includes('完成')) {
                    logClass = 'log-success';
                } else if (log.includes('失败') || log.includes('错误')) {
                    logClass = 'log-error';
                } else if (log.includes('警告')) {
                    logClass = 'log-warning';
                }
                
                entry.innerHTML = `<span class="${logClass}">${log}</span>`;
                container.appendChild(entry);
            });
            
            // 滚动到底部
            container.scrollTop = container.scrollHeight;
        }
        
        // 开始训练
        async function startTraining() {
            try {
                const response = await fetch('/api/traditional/train', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                const data = await response.json();

                if (data.success) {
                    alert('训练已开始！');
                    isTraining = true;

                    // 开始预测更新
                    setTimeout(updatePrediction, 5000);
                    if (window.predictionInterval) {
                        clearInterval(window.predictionInterval);
                    }
                    window.predictionInterval = setInterval(updatePrediction, 30000);

                    // 训练完成后刷新特征重要性和历史记录
                    setTimeout(() => {
                        console.log('训练完成，开始刷新状态和数据...');
                        refreshStatus();
                        updateTrainingDetails();

                        // 再次延迟刷新，确保数据完全更新
                        setTimeout(() => {
                            refreshStatus();
                        }, 5000);
                    }, 10000); // 10秒后刷新状态，获取训练结果
                } else {
                    alert('训练启动失败: ' + data.message);
                }
            } catch (error) {
                alert('训练启动失败: ' + error.message);
            }
        }

        // 更新预测结果
        async function updatePrediction() {
            try {
                const response = await fetch('/api/traditional/predict', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                const data = await response.json();

                if (data.success) {
                    // 更新价格显示
                    document.getElementById('current-price').textContent = `$${data.current_price.toFixed(2)}`;
                    document.getElementById('predicted-price').textContent = `$${data.predicted_price.toFixed(2)}`;

                    // 计算价格变化
                    const priceChange = data.predicted_price - data.current_price;
                    const priceChangeElement = document.getElementById('price-change');
                    priceChangeElement.textContent = `${priceChange >= 0 ? '+' : ''}$${priceChange.toFixed(2)}`;
                    priceChangeElement.style.color = priceChange >= 0 ? '#2ecc71' : '#e74c3c';

                    // 更新信号显示
                    const signalElement = document.getElementById('prediction-signal');
                    signalElement.textContent = data.signal;

                    // 根据信号设置颜色
                    if (data.signal.includes('看涨')) {
                        signalElement.style.color = '#2ecc71';
                    } else if (data.signal.includes('看跌')) {
                        signalElement.style.color = '#e74c3c';
                    } else {
                        signalElement.style.color = '#f39c12';
                    }

                    // 更新置信度
                    const confidencePercent = (data.confidence * 100).toFixed(1);
                    document.getElementById('prediction-confidence').textContent = `${confidencePercent}%`;

                    // 添加预测日志
                    const timestamp = new Date().toLocaleTimeString();
                    const logs = document.getElementById('training-logs');
                    const logEntry = document.createElement('div');
                    logEntry.className = 'log-entry';
                    logEntry.innerHTML = `<span class="log-success">[${timestamp}] 预测完成: ${data.signal}, 置信度: ${confidencePercent}%</span>`;
                    logs.appendChild(logEntry);
                    logs.scrollTop = logs.scrollHeight;
                } else {
                    console.error('预测失败:', data.message);
                }
            } catch (error) {
                console.error('预测更新失败:', error);
            }
        }
        
        // 进行预测
        async function makePrediction() {
            try {
                // 直接调用预测更新函数
                await updatePrediction();

                // 获取最新的预测结果显示
                const currentPrice = document.getElementById('current-price').textContent;
                const predictedPrice = document.getElementById('predicted-price').textContent;
                const signal = document.getElementById('prediction-signal').textContent;
                const confidence = document.getElementById('prediction-confidence').textContent;

                if (currentPrice !== '$--' && predictedPrice !== '$--') {
                    alert(`🔮 预测完成！\\n\\n📊 当前价格: ${currentPrice}\\n🎯 预测价格: ${predictedPrice}\\n📈 预测信号: ${signal}\\n🎲 置信度: ${confidence}`);
                } else {
                    alert('⚠️ 预测失败，请先启动并训练系统');
                }
            } catch (error) {
                alert('预测失败: ' + error.message);
            }
        }
        
        // 显示配置设置
        function showConfig() {
            const newDataSource = prompt('数据源 (mt5/yahoo/alpha_vantage):', 'mt5');
            const newTimePeriod = prompt('时间周期 (H1/H4/D1):', 'H1');
            const newModelType = prompt('模型类型 (random_forest/gradient_boosting/neural_network/ensemble):', 'random_forest');
            
            if (newDataSource && newTimePeriod && newModelType) {
                updateConfig({
                    data_source: newDataSource,
                    time_period: newTimePeriod,
                    model_type: newModelType
                });
            }
        }
        
        // 更新配置
        async function updateConfig(config) {
            try {
                const response = await fetch('/api/traditional/config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(config)
                });
                const data = await response.json();
                
                if (data.success) {
                    alert('配置已更新！');
                    refreshStatus();
                } else {
                    alert('配置更新失败: ' + data.message);
                }
            } catch (error) {
                alert('配置更新失败: ' + error.message);
            }
        }
        
        // 停止系统
        async function stopSystem() {
            if (confirm('确定要停止传统ML系统吗？')) {
                try {
                    const response = await fetch('/api/stop/traditional', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' }
                    });
                    const data = await response.json();
                    
                    if (data.success) {
                        alert('系统已停止！');
                        refreshStatus();
                    } else {
                        alert('停止失败: ' + data.message);
                    }
                } catch (error) {
                    alert('停止失败: ' + error.message);
                }
            }
        }
        
        // 启动状态更新器
        function startStatusUpdater() {
            updateInterval = setInterval(() => {
                refreshStatus();
                // 只有在训练时才频繁更新训练进度
                if (isTraining) {
                    updateTrainingProgress();
                }
            }, 5000); // 改为每5秒更新一次，减少频率
        }

        // 启动系统（传统ML）
        async function startSystem() {
            try {
                const response = await fetch('/api/start/traditional', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({})
                });
                const data = await response.json();

                if (data.success) {
                    alert('传统ML系统启动成功！');

                    // 延迟启动预测更新
                    setTimeout(() => {
                        updatePrediction();
                        if (window.predictionInterval) {
                            clearInterval(window.predictionInterval);
                        }
                        window.predictionInterval = setInterval(updatePrediction, 30000);
                    }, 3000);
                } else {
                    alert('系统启动失败: ' + data.message);
                }
            } catch (error) {
                alert('系统启动失败: ' + error.message);
            }
        }
        
        // 页面卸载时清理
        window.addEventListener('beforeunload', function() {
            if (updateInterval) {
                clearInterval(updateInterval);
            }
        });
    </script>
</body>
</html>
'''

if __name__ == "__main__":
    print("传统ML系统增强Web界面模板已定义")
