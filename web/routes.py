from flask import Blueprint, render_template, jsonify
from .data_manager import DataManager
from .socket_client import get_client

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def dashboard():
    return render_template('dashboard.html')


@main_bp.route('/api/stats')
def get_stats():
    dm = DataManager()
    return jsonify(dm.get_current_data())


@main_bp.route('/api/status')
def get_status():
    dm = DataManager()
    client = get_client()

    return jsonify({
        'session': {
            'id': dm.session_id,
            'duration': dm.get_duration_formatted(),
            'measurement_count': dm.measurement_count
        },
        'connection': {
            'ap_connected': client.connected if client else False,
            'client_status': dm.connection_status
        },
        'predictor': dm.predictor.get_status()
    })


@main_bp.route('/api/history')
def get_history():
    dm = DataManager()
    return jsonify({
        'rssi': list(dm.rssi_history),
        'rtt': list(dm.rtt_history)
    })


@main_bp.route('/api/warnings')
def get_warnings():
    dm = DataManager()
    return jsonify({
        'warnings': list(dm.warnings),
        'counts': dm.warning_counts
    })
