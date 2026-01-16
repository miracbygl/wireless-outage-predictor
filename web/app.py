#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import signal
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web import create_app, socketio
from web.socket_client import APSocketClient, set_client
from web.data_manager import DataManager


def signal_handler(signum, frame):
    print('\n[App] Kapatiliyor...')

    client = APSocketClient._instance
    if client:
        client.stop()

    dm = DataManager()
    dm.close()

    print('[App] Kapatildi')
    sys.exit(0)


def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    app = create_app()

    AP_IP = os.environ.get('AP_IP', '192.168.4.1')
    AP_PORT = int(os.environ.get('AP_PORT', '12346'))

    print('=' * 60)
    print('       Wi-Fi RSSI/RTT Monitor - Web Dashboard')
    print('=' * 60)
    print()
    print(f'  AP Baglanti: {AP_IP}:{AP_PORT}')
    print(f'  Web Arayuz:  http://localhost:5001')
    print()
    print('  Kapatmak icin: Ctrl+C')
    print('=' * 60)
    print()

    client = APSocketClient(AP_IP, AP_PORT)
    set_client(client)

    client_thread = threading.Thread(target=client.start, daemon=True)
    client_thread.start()

    try:
        socketio.run(
            app,
            host='0.0.0.0',
            port=5001,
            debug=False,
            use_reloader=False,
            allow_unsafe_werkzeug=True
        )
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)


if __name__ == '__main__':
    main()
