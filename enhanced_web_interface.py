#!/usr/bin/env python3
"""
增强Web界面
集成自适应预测引擎和所有功能
"""

import json
import threading
import time
from datetime import datetime
from pathlib import Path
from flask import Flask, jsonify, request, render_template
from flask_socketio import SocketIO, emit
import logging

from adaptive_prediction_engine import AdaptivePredictionEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = 'enhanced_prediction_secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# 全局变量
prediction_engine = None
status_thread = None


class EnhancedWebController:
    """增强Web控制器"""
    
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
        self.load_config()
    
    def load_config(self):
        """加载配置"""
        config_path = Path("configs/enhanced_config.json")
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    saved_config = json.load(f)
                    self.default_config.update(saved_config)
                    print(f"[配置] 已加载配置: {saved_config}")
            except Exception as e:
                print(f"[配置] 加载配置失败: {e}")
    
    def save_config(self):
        """保存配置"""
        config_path = Path("configs/enhanced_config.json")
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(config_path, 'w') as f:
                json.dump(self.default_config, f, indent=2)
            print(f"[配置] 配置已保存")
        except Exception as e:
            print(f"[配置] 保存配置失败: {e}")
    
    def start_engine(self, config=None):
        """启动预测引擎"""
        global prediction_engine, status_thread
        
        if prediction_engine and prediction_engine.running:
            return {'success': False, 'message': '引擎已在运行中'}
        
        try:
            # 更新配置
            if config:
                self.default_config.update(config)
                self.save_config()
            
            # 创建自适应预测引擎
            prediction_engine = AdaptivePredictionEngine(self.default_config)
            
            # 启动引擎
            if prediction_engine.start_engine():
                self.running = True
                
                # 启动状态监控线程
                self._start_status_monitoring()
                
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
    
    def update_config(self, new_config):
        """更新配置"""
        try:
            self.default_config.update(new_config)
            self.save_config()
            
            # 如果引擎正在运行，更新其配置
            if prediction_engine and prediction_engine.running:
                prediction_engine.update_config(new_config)
            
            return {'success': True, 'config': self.default_config}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
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


# 创建控制器实例
controller = EnhancedWebController()


@app.route('/')
def index():
    """主页"""
    return render_template('enhanced_prediction.html')


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


@app.route('/api/config', methods=['GET', 'POST'])
def manage_config():
    """管理配置"""
    if request.method == 'GET':
        return jsonify(controller.default_config)
    
    elif request.method == 'POST':
        try:
            new_config = request.json
            result = controller.update_config(new_config)
            return jsonify(result)
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})


@app.route('/api/history/predictions')
def get_prediction_history():
    """获取预测历史"""
    try:
        global prediction_engine
        
        if not prediction_engine:
            return jsonify({'predictions': []})
        
        # 从数据库获取历史预测
        cursor = prediction_engine.conn.execute('''
            SELECT timestamp, current_price, predicted_price, signal, confidence, accuracy, verified_at
            FROM predictions 
            ORDER BY timestamp DESC 
            LIMIT 100
        ''')
        
        predictions = []
        for row in cursor.fetchall():
            predictions.append({
                'timestamp': row[0],
                'current_price': row[1],
                'predicted_price': row[2],
                'signal': row[3],
                'confidence': row[4],
                'accuracy': row[5],
                'verified_at': row[6]
            })
        
        return jsonify({'predictions': predictions})
        
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/api/history/performance')
def get_performance_history():
    """获取性能历史"""
    try:
        global prediction_engine
        
        if not prediction_engine:
            return jsonify({'performance': []})
        
        # 从数据库获取性能历史
        cursor = prediction_engine.conn.execute('''
            SELECT timestamp, total_predictions, correct_predictions, average_accuracy, recent_accuracy, confidence_level
            FROM performance_metrics 
            ORDER BY timestamp DESC 
            LIMIT 50
        ''')
        
        performance = []
        for row in cursor.fetchall():
            performance.append({
                'timestamp': row[0],
                'total_predictions': row[1],
                'correct_predictions': row[2],
                'average_accuracy': row[3],
                'recent_accuracy': row[4],
                'confidence_level': row[5]
            })
        
        return jsonify({'performance': performance})
        
    except Exception as e:
        return jsonify({'error': str(e)})


@socketio.on('connect')
def handle_connect():
    """WebSocket连接"""
    print(f"[WebSocket] 客户端连接: {request.sid}")
    emit('connected', {'message': '增强预测系统已连接'})


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


def main():
    """主函数"""
    print("增强Web界面")
    print("=" * 40)
    
    # 如果配置了自动启动
    if controller.default_config.get('auto_start', False):
        print("[自动] 启动自适应预测引擎...")
        result = controller.start_engine()
        print(f"[结果] {result['message']}")
    
    # 启动Web服务器
    print(f"[启动] 增强Web界面服务器...")
    print(f"[地址] http://localhost:5002")
    
    try:
        socketio.run(app, host='0.0.0.0', port=5002, debug=False)
    except KeyboardInterrupt:
        print("\n[停止] 服务器已停止")
        controller.stop_engine()


if __name__ == "__main__":
    main()
