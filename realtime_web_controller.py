#!/usr/bin/env python3
"""
实时预测Web控制器
管理实时预测引擎的启动、停止和状态监控
"""

import json
import threading
import time
from datetime import datetime
from pathlib import Path
from flask import Flask, jsonify, request, render_template
from flask_socketio import SocketIO, emit
import logging

from realtime_prediction_engine import RealTimePredictionEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = 'realtime_prediction_secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# 全局变量
prediction_engine = None
engine_thread = None
status_thread = None


class RealTimeWebController:
    """实时预测Web控制器"""
    
    def __init__(self):
        self.engine = None
        self.running = False
        self.config = {
            'interval_minutes': 5,
            'predictor_types': ['lightweight', 'complex', 'deep'],
            'auto_start': False
        }
    
    def start_engine(self, config):
        """启动预测引擎"""
        global prediction_engine, engine_thread
        
        if prediction_engine and prediction_engine.running:
            return {'success': False, 'message': '引擎已在运行中'}
        
        try:
            # 更新配置
            self.config.update(config)
            
            # 创建预测引擎
            prediction_engine = RealTimePredictionEngine(self.config)
            
            # 启动引擎
            prediction_engine.start_engine()
            
            # 启动状态监控线程
            self._start_status_monitoring()
            
            return {'success': True, 'message': '实时预测引擎已启动'}
            
        except Exception as e:
            logger.error(f"启动引擎失败: {e}")
            return {'success': False, 'message': f'启动失败: {str(e)}'}
    
    def stop_engine(self):
        """停止预测引擎"""
        global prediction_engine
        
        if prediction_engine:
            prediction_engine.stop_engine()
            prediction_engine = None
            return {'success': True, 'message': '实时预测引擎已停止'}
        
        return {'success': False, 'message': '引擎未运行'}
    
    def get_status(self):
        """获取引擎状态"""
        global prediction_engine
        
        if not prediction_engine:
            return {
                'running': False,
                'config': self.config,
                'stats': {'total_predictions': 0, 'average_accuracy': 0}
            }
        
        stats = prediction_engine.get_accuracy_stats()
        
        return {
            'running': prediction_engine.running,
            'config': self.config,
            'stats': stats,
            'uptime': self._get_uptime()
        }
    
    def get_latest_prediction(self):
        """获取最新预测"""
        global prediction_engine
        
        if prediction_engine:
            return prediction_engine.get_latest_prediction()
        return None
    
    def _start_status_monitoring(self):
        """启动状态监控"""
        global status_thread
        
        def monitor_status():
            while prediction_engine and prediction_engine.running:
                try:
                    # 获取最新预测
                    latest_prediction = self.get_latest_prediction()
                    if latest_prediction:
                        socketio.emit('new_prediction', latest_prediction)
                    
                    # 发送状态更新
                    status = self.get_status()
                    socketio.emit('status_update', status)
                    
                    time.sleep(5)  # 每5秒更新一次
                    
                except Exception as e:
                    logger.error(f"状态监控错误: {e}")
                    time.sleep(10)
        
        status_thread = threading.Thread(target=monitor_status, daemon=True)
        status_thread.start()
    
    def _get_uptime(self):
        """获取运行时间"""
        # 简化实现，实际应该记录启动时间
        return "运行中"


# 创建控制器实例
controller = RealTimeWebController()


@app.route('/')
def index():
    """实时预测系统主页"""
    return render_template('realtime_prediction.html')


@app.route('/api/realtime/start', methods=['POST'])
def start_realtime_prediction():
    """启动实时预测"""
    try:
        config = request.json or {}
        result = controller.start_engine(config)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/realtime/stop', methods=['POST'])
def stop_realtime_prediction():
    """停止实时预测"""
    try:
        result = controller.stop_engine()
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/realtime/status')
def get_realtime_status():
    """获取实时预测状态"""
    try:
        status = controller.get_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/api/realtime/prediction/latest')
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


@app.route('/api/realtime/history')
def get_prediction_history():
    """获取预测历史"""
    try:
        global prediction_engine
        
        if not prediction_engine:
            return jsonify({'predictions': []})
        
        # 从数据库获取历史预测
        cursor = prediction_engine.conn.execute('''
            SELECT timestamp, current_price, predicted_price, signal, confidence, accuracy
            FROM predictions 
            ORDER BY timestamp DESC 
            LIMIT 50
        ''')
        
        predictions = []
        for row in cursor.fetchall():
            predictions.append({
                'timestamp': row[0],
                'current_price': row[1],
                'predicted_price': row[2],
                'signal': row[3],
                'confidence': row[4],
                'accuracy': row[5]
            })
        
        return jsonify({'predictions': predictions})
        
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/api/realtime/config', methods=['GET', 'POST'])
def manage_config():
    """管理配置"""
    if request.method == 'GET':
        return jsonify(controller.config)
    
    elif request.method == 'POST':
        try:
            new_config = request.json
            controller.config.update(new_config)
            
            # 保存配置到文件
            config_path = Path("configs/realtime_config.json")
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w') as f:
                json.dump(controller.config, f, indent=2)
            
            return jsonify({'success': True, 'config': controller.config})
            
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})


@socketio.on('connect')
def handle_connect():
    """WebSocket连接"""
    print(f"[WebSocket] 客户端连接: {request.sid}")
    emit('connected', {'message': '实时预测系统已连接'})


@socketio.on('disconnect')
def handle_disconnect():
    """WebSocket断开"""
    print(f"[WebSocket] 客户端断开: {request.sid}")


@socketio.on('request_status')
def handle_status_request():
    """处理状态请求"""
    status = controller.get_status()
    emit('status_update', status)


@socketio.on('request_prediction')
def handle_prediction_request():
    """处理预测请求"""
    prediction = controller.get_latest_prediction()
    if prediction:
        emit('new_prediction', prediction)
    else:
        emit('no_prediction', {'message': '暂无预测数据'})


def load_config():
    """加载配置"""
    config_path = Path("configs/realtime_config.json")
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                controller.config.update(config)
                print(f"[配置] 已加载配置: {config}")
        except Exception as e:
            print(f"[配置] 加载配置失败: {e}")


def main():
    """主函数"""
    print("实时预测Web控制器")
    print("=" * 40)
    
    # 加载配置
    load_config()
    
    # 如果配置了自动启动
    if controller.config.get('auto_start', False):
        print("[自动] 启动实时预测引擎...")
        result = controller.start_engine(controller.config)
        print(f"[结果] {result['message']}")
    
    # 启动Web服务器
    print(f"[启动] Web控制器服务器...")
    print(f"[地址] http://localhost:5001")
    
    try:
        socketio.run(app, host='0.0.0.0', port=5001, debug=False)
    except KeyboardInterrupt:
        print("\n[停止] 服务器已停止")
        controller.stop_engine()


if __name__ == "__main__":
    main()
