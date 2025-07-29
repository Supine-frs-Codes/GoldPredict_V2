#!/usr/bin/env python3
"""
自动交易系统Web界面
提供自动模拟EA交易的Web管理界面
"""

from flask import Flask, jsonify, request, render_template_string
from auto_trading_system import AutoTradingSystem
import logging
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'auto_trading_secret_key'

# 全局交易系统实例
trading_system = None

# HTML模板
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🤖 自动模拟EA交易系统</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; min-height: 100vh; padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 30px; }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; color: #ffd700; }
        .panel {
            background: rgba(255,255,255,0.1); padding: 20px; border-radius: 15px;
            backdrop-filter: blur(10px); margin-bottom: 20px;
        }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .btn {
            padding: 12px 24px; border: none; border-radius: 25px; font-weight: bold;
            cursor: pointer; margin: 5px; transition: all 0.3s ease; text-decoration: none;
            display: inline-flex; align-items: center; justify-content: center;
        }
        .btn-primary { background: linear-gradient(45deg, #e74c3c, #c0392b); color: white; }
        .btn-secondary { background: linear-gradient(45deg, #3498db, #2980b9); color: white; }
        .btn-success { background: linear-gradient(45deg, #27ae60, #229954); color: white; }
        .btn-warning { background: linear-gradient(45deg, #f39c12, #e67e22); color: white; }
        .btn-danger { background: linear-gradient(45deg, #e74c3c, #c0392b); color: white; }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.3); }
        
        .status-item { text-align: center; padding: 15px; background: rgba(255,255,255,0.1); border-radius: 10px; margin: 10px; }
        .status-value { font-size: 1.8em; font-weight: bold; color: #ffd700; margin-bottom: 5px; }
        .status-label { font-size: 0.9em; opacity: 0.8; }
        
        .config-row { display: flex; align-items: center; margin: 10px 0; }
        .config-row label { flex: 1; margin-right: 10px; font-weight: bold; }
        .config-row input, .config-row select {
            flex: 1; padding: 8px; border: none; border-radius: 5px;
            background: rgba(255,255,255,0.2); color: white;
        }
        .config-row input::placeholder { color: rgba(255,255,255,0.7); }
        
        .trade-table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        .trade-table th, .trade-table td { padding: 10px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.2); }
        .trade-table th { background: rgba(255,255,255,0.1); font-weight: bold; }
        .trade-table tr:hover { background: rgba(255,255,255,0.05); }
        
        .profit-positive { color: #27ae60; font-weight: bold; }
        .profit-negative { color: #e74c3c; font-weight: bold; }
        .profit-neutral { color: #f39c12; font-weight: bold; }
        
        .log-container {
            background: rgba(0,0,0,0.3); padding: 15px; border-radius: 10px;
            height: 300px; overflow-y: auto; font-family: monospace; font-size: 0.9em;
        }
        .log-entry { margin-bottom: 8px; padding: 5px 0; border-bottom: 1px solid rgba(255,255,255,0.1); }
        .log-timestamp { color: #3498db; font-weight: bold; }
        .log-success { color: #27ae60; }
        .log-error { color: #e74c3c; }
        .log-warning { color: #f39c12; }
        
        .back-btn {
            position: fixed; top: 20px; left: 20px; z-index: 1000;
            background: rgba(0,0,0,0.5); padding: 10px 15px; border-radius: 25px;
            text-decoration: none; color: white; font-weight: bold;
        }
        .back-btn:hover { background: rgba(0,0,0,0.7); }
        
        .emergency-stop {
            position: fixed; top: 20px; right: 20px; z-index: 1000;
            background: linear-gradient(45deg, #e74c3c, #c0392b);
            padding: 15px 20px; border-radius: 25px; border: none;
            color: white; font-weight: bold; font-size: 1.1em;
            cursor: pointer; box-shadow: 0 5px 15px rgba(231, 76, 60, 0.4);
        }
        .emergency-stop:hover { transform: scale(1.05); }
        
        @media (max-width: 768px) {
            .grid { grid-template-columns: 1fr; }
            .grid-2 { grid-template-columns: 1fr; }
            .header h1 { font-size: 2em; }
        }
    </style>
</head>
<body>
    <a href="/" class="back-btn">← 返回主页</a>
    <button class="emergency-stop" onclick="emergencyStop()">🚨 紧急停止</button>
    
    <div class="container">
        <div class="header">
            <h1>🤖 自动模拟EA交易系统</h1>
            <p>专注黄金(XAUUSD)的全自动交易，集成强化学习机制</p>
        </div>
        
        <!-- 系统控制面板 -->
        <div class="panel">
            <h2>🎮 系统控制</h2>
            <div style="text-align: center; margin: 20px 0;">
                <button class="btn btn-success" onclick="startTrading()">🚀 启动自动交易</button>
                <button class="btn btn-warning" onclick="stopTrading()">⏹️ 停止交易</button>
                <button class="btn btn-secondary" onclick="connectMT5()">🔗 连接MT5</button>
                <button class="btn btn-secondary" onclick="refreshStatus()">🔄 刷新状态</button>
            </div>
            <div style="text-align: center;">
                <span id="system-status" style="font-size: 1.2em; font-weight: bold;">系统状态: 未知</span>
            </div>
        </div>
        
        <!-- 账户信息 -->
        <div class="grid">
            <div class="panel">
                <h2>💰 账户信息</h2>
                <div class="grid" style="grid-template-columns: repeat(2, 1fr);">
                    <div class="status-item">
                        <div class="status-value" id="account-balance">$0.00</div>
                        <div class="status-label">账户余额</div>
                    </div>
                    <div class="status-item">
                        <div class="status-value" id="account-equity">$0.00</div>
                        <div class="status-label">账户净值</div>
                    </div>
                    <div class="status-item">
                        <div class="status-value" id="account-margin">$0.00</div>
                        <div class="status-label">已用保证金</div>
                    </div>
                    <div class="status-item">
                        <div class="status-value" id="margin-level">0%</div>
                        <div class="status-label">保证金水平</div>
                    </div>
                </div>
            </div>
            
            <div class="panel">
                <h2>📊 交易统计</h2>
                <div class="grid" style="grid-template-columns: repeat(2, 1fr);">
                    <div class="status-item">
                        <div class="status-value" id="total-trades">0</div>
                        <div class="status-label">总交易数</div>
                    </div>
                    <div class="status-item">
                        <div class="status-value" id="win-rate">0%</div>
                        <div class="status-label">胜率</div>
                    </div>
                    <div class="status-item">
                        <div class="status-value" id="total-profit">$0.00</div>
                        <div class="status-label">总盈亏</div>
                    </div>
                    <div class="status-item">
                        <div class="status-value" id="position-count">0</div>
                        <div class="status-label">持仓数量</div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- 当前持仓 -->
        <div class="panel">
            <h2>📈 当前持仓</h2>
            <div id="positions-container">
                <table class="trade-table">
                    <thead>
                        <tr>
                            <th>订单号</th>
                            <th>类型</th>
                            <th>手数</th>
                            <th>开仓价</th>
                            <th>当前价</th>
                            <th>盈亏</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody id="positions-table">
                        <tr><td colspan="7" style="text-align: center; opacity: 0.7;">暂无持仓</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- 风险管理配置 -->
        <div class="grid-2">
            <div class="panel">
                <h2>⚙️ 风险管理配置</h2>
                <div class="config-row">
                    <label>最大仓位 (手):</label>
                    <input type="number" id="max-position" value="10.0" step="0.1" min="0.1">
                </div>
                <div class="config-row">
                    <label>止损点数:</label>
                    <input type="number" id="stop-loss-pips" value="50" min="10">
                </div>
                <div class="config-row">
                    <label>止盈点数:</label>
                    <input type="number" id="take-profit-pips" value="100" min="10">
                </div>
                <div class="config-row">
                    <label>每笔风险 (%):</label>
                    <input type="number" id="risk-per-trade" value="2" step="0.1" min="0.1" max="10">
                </div>
                <div class="config-row">
                    <label>最大日亏损:</label>
                    <input type="number" id="max-daily-loss" value="50000" step="1000">
                </div>
                <div style="text-align: center; margin-top: 15px;">
                    <button class="btn btn-primary" onclick="updateRiskConfig()">💾 保存配置</button>
                </div>
            </div>
            
            <div class="panel">
                <h2>🧠 强化学习状态</h2>
                <div class="status-item">
                    <div class="status-value" id="q-table-size">0</div>
                    <div class="status-label">Q表状态数</div>
                </div>
                <div class="status-item">
                    <div class="status-value" id="learning-rate">0.1</div>
                    <div class="status-label">学习率</div>
                </div>
                <div class="status-item">
                    <div class="status-value" id="exploration-rate">0.1</div>
                    <div class="status-label">探索率</div>
                </div>
                <div style="text-align: center; margin-top: 15px;">
                    <button class="btn btn-secondary" onclick="resetRL()">🔄 重置学习</button>
                </div>
            </div>
        </div>
        
        <!-- 交易历史 -->
        <div class="panel">
            <h2>📋 交易历史</h2>
            <div style="text-align: right; margin-bottom: 10px;">
                <button class="btn btn-secondary" onclick="loadTradeHistory()">🔄 刷新历史</button>
            </div>
            <div id="trade-history-container">
                <table class="trade-table">
                    <thead>
                        <tr>
                            <th>时间</th>
                            <th>订单号</th>
                            <th>类型</th>
                            <th>手数</th>
                            <th>开仓价</th>
                            <th>平仓价</th>
                            <th>盈亏</th>
                        </tr>
                    </thead>
                    <tbody id="trade-history-table">
                        <tr><td colspan="7" style="text-align: center; opacity: 0.7;">暂无交易历史</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- 系统日志 -->
        <div class="panel">
            <h2>📝 系统日志</h2>
            <div class="log-container" id="system-log">
                <div class="log-entry">
                    <span class="log-timestamp">[等待]</span>
                    <span>自动交易系统准备就绪</span>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let statusUpdateInterval;
        
        function startTrading() {
            addLog('启动自动交易系统...');
            
            fetch('/api/trading/start', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    addLog('自动交易系统启动成功', 'success');
                    updateSystemStatus('运行中');
                    startStatusUpdates();
                } else {
                    addLog('启动失败: ' + data.message, 'error');
                }
            })
            .catch(error => {
                addLog('启动错误: ' + error.message, 'error');
                console.error('启动错误详情:', error);
            });
        }
        
        function stopTrading() {
            addLog('停止自动交易系统...');
            
            fetch('/api/trading/stop', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    addLog('自动交易系统已停止', 'success');
                    updateSystemStatus('已停止');
                    stopStatusUpdates();
                } else {
                    addLog('停止失败: ' + data.message, 'error');
                }
            })
            .catch(error => {
                addLog('停止错误: ' + error, 'error');
            });
        }
        
        function connectMT5() {
            addLog('连接MT5...');
            
            fetch('/api/trading/connect-mt5', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    addLog('MT5连接成功', 'success');
                    refreshStatus();
                } else {
                    addLog('MT5连接失败: ' + data.message, 'error');
                }
            })
            .catch(error => {
                addLog('连接错误: ' + error.message, 'error');
                console.error('MT5连接错误详情:', error);
            });
        }
        
        function emergencyStop() {
            if (confirm('确定要执行紧急停止吗？这将关闭所有持仓并停止交易！')) {
                addLog('执行紧急停止...', 'warning');
                
                fetch('/api/trading/emergency-stop', {
                    method: 'POST'
                })
                .then(response => response.json())
                .then(data => {
                    addLog('紧急停止完成', 'warning');
                    updateSystemStatus('紧急停止');
                    stopStatusUpdates();
                    refreshStatus();
                })
                .catch(error => {
                    addLog('紧急停止错误: ' + error, 'error');
                });
            }
        }
        
        function refreshStatus() {
            fetch('/api/trading/status')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    updateAccountInfo(data);
                    updatePositions(data.positions || []);
                    updateTradingStats(data);

                    if (data.running) {
                        updateSystemStatus('运行中');
                    } else if (data.connected) {
                        updateSystemStatus('已连接');
                    } else {
                        updateSystemStatus('未连接');
                    }
                } else {
                    addLog('状态获取失败: ' + data.message, 'error');
                    updateSystemStatus('状态未知');
                }
            })
            .catch(error => {
                addLog('状态更新错误: ' + error.message, 'error');
                console.error('状态更新错误详情:', error);
                updateSystemStatus('连接错误');
            });
        }
        
        function updateAccountInfo(data) {
            const accountInfo = data.account_info || {};
            
            document.getElementById('account-balance').textContent = 
                '$' + (accountInfo.balance || 0).toLocaleString('en-US', {minimumFractionDigits: 2});
            document.getElementById('account-equity').textContent = 
                '$' + (accountInfo.equity || 0).toLocaleString('en-US', {minimumFractionDigits: 2});
            document.getElementById('account-margin').textContent = 
                '$' + (accountInfo.margin || 0).toLocaleString('en-US', {minimumFractionDigits: 2});
            document.getElementById('margin-level').textContent = 
                (accountInfo.margin_level || 0).toFixed(1) + '%';
        }
        
        function updatePositions(positions) {
            const tbody = document.getElementById('positions-table');
            
            if (positions.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; opacity: 0.7;">暂无持仓</td></tr>';
                return;
            }
            
            tbody.innerHTML = positions.map(pos => `
                <tr>
                    <td>${pos.ticket}</td>
                    <td>${pos.type === 0 ? '买入' : '卖出'}</td>
                    <td>${pos.volume}</td>
                    <td>${pos.price_open.toFixed(5)}</td>
                    <td>${pos.price_current.toFixed(5)}</td>
                    <td class="${pos.profit >= 0 ? 'profit-positive' : 'profit-negative'}">
                        $${pos.profit.toFixed(2)}
                    </td>
                    <td>
                        <button class="btn btn-danger" onclick="closePosition(${pos.ticket})">平仓</button>
                    </td>
                </tr>
            `).join('');
        }
        
        function updateTradingStats(data) {
            document.getElementById('total-trades').textContent = data.total_trades || 0;
            document.getElementById('win-rate').textContent = (data.win_rate || 0).toFixed(1) + '%';
            document.getElementById('total-profit').textContent = 
                '$' + (data.total_profit || 0).toLocaleString('en-US', {minimumFractionDigits: 2});
            document.getElementById('position-count').textContent = data.position_count || 0;
            document.getElementById('q-table-size').textContent = data.q_table_size || 0;
        }
        
        function updateSystemStatus(status) {
            document.getElementById('system-status').textContent = '系统状态: ' + status;
        }
        
        function startStatusUpdates() {
            if (statusUpdateInterval) clearInterval(statusUpdateInterval);
            statusUpdateInterval = setInterval(refreshStatus, 5000); // 每5秒更新
        }
        
        function stopStatusUpdates() {
            if (statusUpdateInterval) {
                clearInterval(statusUpdateInterval);
                statusUpdateInterval = null;
            }
        }
        
        function addLog(message, type = 'info') {
            const logContainer = document.getElementById('system-log');
            const timestamp = new Date().toLocaleTimeString();
            
            const logEntry = document.createElement('div');
            logEntry.className = 'log-entry';
            logEntry.innerHTML = `
                <span class="log-timestamp">[${timestamp}]</span>
                <span class="log-${type}">${message}</span>
            `;
            
            logContainer.appendChild(logEntry);
            logContainer.scrollTop = logContainer.scrollHeight;
            
            // 保持最近100条日志
            while (logContainer.children.length > 100) {
                logContainer.removeChild(logContainer.firstChild);
            }
        }
        
        // 初始化
        addLog('自动交易系统界面加载完成', 'success');
        refreshStatus();
        
        // 定期更新状态
        setInterval(() => {
            if (document.getElementById('system-status').textContent.includes('运行中')) {
                refreshStatus();
            }
        }, 10000); // 每10秒检查一次
    </script>
</body>
</html>
'''


@app.route('/')
def index():
    """主页面"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/trading/start', methods=['POST'])
def start_trading():
    """启动自动交易"""
    global trading_system
    
    try:
        if trading_system is None:
            config = request.json or {}
            trading_system = AutoTradingSystem(config)
        
        success = trading_system.start_trading()
        
        return jsonify({
            'success': success,
            'message': '自动交易启动成功' if success else '自动交易启动失败'
        })
        
    except Exception as e:
        logger.error(f"启动自动交易失败: {e}")
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/trading/stop', methods=['POST'])
def stop_trading():
    """停止自动交易"""
    global trading_system
    
    try:
        if trading_system is None:
            return jsonify({'success': False, 'message': '交易系统未初始化'})
        
        success = trading_system.stop_trading()
        
        return jsonify({
            'success': success,
            'message': '自动交易停止成功' if success else '自动交易停止失败'
        })
        
    except Exception as e:
        logger.error(f"停止自动交易失败: {e}")
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/trading/connect', methods=['POST'])
def connect_mt5():
    """连接MT5"""
    global trading_system
    
    try:
        if trading_system is None:
            trading_system = AutoTradingSystem()
        
        success = trading_system.connect_mt5()
        
        return jsonify({
            'success': success,
            'message': 'MT5连接成功' if success else 'MT5连接失败'
        })
        
    except Exception as e:
        logger.error(f"连接MT5失败: {e}")
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/trading/status')
def get_trading_status():
    """获取交易状态"""
    global trading_system
    
    try:
        if trading_system is None:
            return jsonify({
                'running': False,
                'connected': False,
                'message': '交易系统未初始化'
            })
        
        status = trading_system.get_status()
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"获取交易状态失败: {e}")
        return jsonify({'error': str(e)})


@app.route('/api/trading/emergency-stop', methods=['POST'])
def emergency_stop():
    """紧急停止"""
    global trading_system
    
    try:
        if trading_system:
            trading_system.emergency_stop()
        
        return jsonify({'success': True, 'message': '紧急停止完成'})
        
    except Exception as e:
        logger.error(f"紧急停止失败: {e}")
        return jsonify({'success': False, 'message': str(e)})


def main():
    """主函数"""
    print("🤖 自动模拟EA交易系统")
    print("=" * 50)
    print("专注黄金(XAUUSD)的全自动交易")
    print("集成强化学习机制")
    print("=" * 50)
    print(f"[启动] 自动交易Web界面...")
    print(f"[地址] http://localhost:5005")
    print(f"[功能] 自动交易管理和监控")
    
    try:
        app.run(host='0.0.0.0', port=5005, debug=False)
    except KeyboardInterrupt:
        print("\n[停止] 自动交易系统已停止")
        if trading_system:
            trading_system.emergency_stop()


if __name__ == "__main__":
    main()
