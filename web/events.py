from flask import request
from . import socketio
from .data_manager import DataManager


@socketio.on('connect')
def handle_connect():
    print('[SocketIO] Tarayici baglandi:', request.sid)

    dm = DataManager()
    current_data = dm.get_current_data()
    socketio.emit('initial_data', current_data, room=request.sid)


@socketio.on('disconnect')
def handle_disconnect():
    print('[SocketIO] Tarayici ayrildi:', request.sid)


@socketio.on('request_stats')
def handle_request_stats():
    dm = DataManager()
    current_data = dm.get_current_data()
    socketio.emit('stats_update', current_data, room=request.sid)


@socketio.on('request_history')
def handle_request_history():
    dm = DataManager()
    current_data = dm.get_current_data()
    socketio.emit('history_data', {
        'rssi': current_data['chart_data']['rssi'],
        'rtt': current_data['chart_data']['rtt']
    }, room=request.sid)


@socketio.on('ping')
def handle_ping():
    socketio.emit('pong', {'time': DataManager().get_duration_formatted()}, room=request.sid)
