import socket
import threading
import time

from . import socketio
from .data_manager import DataManager


class APSocketClient:

    _instance = None

    def __init__(self, host='192.168.4.1', port=12346):
        self.host = host
        self.port = port
        self.running = False
        self.connected = False
        self._thread = None
        self._socket = None
        self.data_manager = DataManager()

        self.is_client_disconnected = False
        self.last_count = 0

        self._alarm_thread = None
        self._alarm_running = False

    def start(self):
        if self.running:
            return

        self.running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        print('[APSocketClient] Thread baslatildi')

    def stop(self):
        self.running = False
        self._stop_alarm()
        if self._socket:
            try:
                self._socket.close()
            except:
                pass
        print('[APSocketClient] Durduruldu')

    def _start_alarm(self):
        if self._alarm_running:
            return

        self._alarm_running = True
        self._alarm_thread = threading.Thread(target=self._alarm_loop, daemon=True)
        self._alarm_thread.start()
        print('[APSocketClient] Kritik alarm baslatildi')

    def _stop_alarm(self):
        self._alarm_running = False
        print('[APSocketClient] Kritik alarm durduruldu')

    def _alarm_loop(self):
        from datetime import datetime

        while self._alarm_running and self.is_client_disconnected:
            time.sleep(5)

            if not self._alarm_running or not self.is_client_disconnected:
                break

            timestamp = datetime.now().isoformat(timespec='milliseconds')
            warning_data = {
                'timestamp': timestamp,
                'level': 4,
                'messages': ['BAĞLANTI HALA KOPUK! Client ile iletişim yok.'],
                'source': 'system'
            }

            socketio.emit('warning', warning_data)
            print('[APSocketClient] Tekrar eden kritik alarm gonderildi')

    def _run(self):
        backoff = 1
        max_backoff = 30

        while self.running:
            try:
                self._connect_and_receive()
                backoff = 1
            except Exception as e:
                print('[APSocketClient] Hata:', e)
                socketio.emit('connection_error', {'error': str(e)})

                if self.running:
                    print('[APSocketClient] {} saniye sonra tekrar deneniyor...'.format(backoff))
                    time.sleep(backoff)
                    backoff = min(backoff * 2, max_backoff)

    def _connect_and_receive(self):
        print('[APSocketClient] Baglaniyor: {}:{}'.format(self.host, self.port))

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.settimeout(2)

        try:
            self._socket.connect((self.host, self.port))
            self.connected = True
            print('[APSocketClient] Baglanti kuruldu!')
            socketio.emit('ap_connected', {'host': self.host, 'port': self.port})

            buffer = ''

            while self.running:
                try:
                    data = self._socket.recv(1024)
                    if not data:
                        print('[APSocketClient] Baglanti kapandi')
                        break

                    buffer += data.decode()

                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip()
                        self._process_message(line)

                except socket.timeout:
                    continue

        finally:
            self.connected = False
            self._socket.close()
            socketio.emit('ap_disconnected', {})

    def _process_message(self, message):
        if not message:
            return

        if message.startswith('STATUS:'):
            status = message[7:]

            if status == 'DISCONNECTED':
                self.is_client_disconnected = True
                result = self.data_manager.set_disconnected()
                socketio.emit('status_change', result)
                if result.get('warning'):
                    socketio.emit('warning', result['warning'])
                    socketio.emit('stats_update', {
                        'warning_counts': dict(self.data_manager.warning_counts)
                    })
                self._start_alarm()
                print('[APSocketClient] Client koptu!')

            elif status == 'CONNECTED':
                self._stop_alarm()
                result = self.data_manager.set_connected()
                self.is_client_disconnected = False
                socketio.emit('status_change', result)
                print('[APSocketClient] Client baglandi!')

        elif message.startswith('DATA:'):
            parts = message[5:].split(',')
            if len(parts) >= 3:
                try:
                    rssi = int(parts[0])
                    rtt = int(parts[1])
                    count = int(parts[2])

                    if self.last_count > 0 and count > self.last_count + 1:
                        missing = count - self.last_count - 1
                        socketio.emit('packet_loss', {
                            'count': missing,
                            'from': self.last_count + 1,
                            'to': count - 1
                        })

                    self.last_count = count

                    result = self.data_manager.add_measurement(rssi, rtt, count)

                    socketio.emit('new_measurement', result)

                    dm = self.data_manager
                    with dm.data_lock:
                        total_measurements = len(dm.rssi_values) + dm.lost_packets
                        stats_data = {
                            'quality_distribution': dict(dm.quality_counts),
                            'warning_counts': dict(dm.warning_counts),
                            'stats': {
                                'rssi': dm.calculate_stats(list(dm.rssi_values)),
                                'rtt': dm.calculate_stats(list(dm.rtt_values)),
                                'latency': dm.calculate_stats(list(dm.latency_values))
                            },
                            'issues': {
                                'packet_loss': dm.lost_packets,
                                'packet_loss_rate': round(dm.lost_packets / total_measurements * 100, 2) if total_measurements > 0 else 0,
                                'disconnects': dm.disconnects,
                                'total_downtime': round(sum(dm.disconnect_durations), 1) if dm.disconnect_durations else 0,
                                'avg_disconnect': round(sum(dm.disconnect_durations) / len(dm.disconnect_durations), 1) if dm.disconnect_durations else 0
                            }
                        }
                    socketio.emit('stats_update', stats_data)

                except ValueError as e:
                    print('[APSocketClient] Veri parse hatasi:', e)

    def get_status(self):
        return {
            'connected': self.connected,
            'host': self.host,
            'port': self.port,
            'running': self.running
        }


_client_instance = None


def get_client():
    global _client_instance
    return _client_instance


def set_client(client):
    global _client_instance
    _client_instance = client
    APSocketClient._instance = client


def start_client(host='192.168.4.1', port=12346):
    global _client_instance
    _client_instance = APSocketClient(host, port)
    APSocketClient._instance = _client_instance
    _client_instance.start()
    return _client_instance
