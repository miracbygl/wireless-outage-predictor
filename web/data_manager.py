import threading
import time
import os
import sys
import csv
from collections import deque
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.predictor import ConnectionPredictor

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
CSV_FILE = os.path.join(DATA_DIR, 'rssi_data.csv')
CSV_HEADERS = ['session_id', 'timestamp', 'unix_time', 'measurement_id', 'event_type',
               'rssi', 'rtt', 'latency', 'quality', 'quality_score', 'disconnect_duration']

ML_MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ml', 'model.pkl')


def get_signal_quality(rssi):
    if rssi >= -50:
        return 'Mükemmel'
    elif rssi >= -60:
        return 'İyi'
    elif rssi >= -70:
        return 'Orta'
    elif rssi >= -80:
        return 'Zayıf'
    else:
        return 'Çok Zayıf'


def get_quality_score(quality):
    scores = {
        'Mükemmel': 4,
        'İyi': 3,
        'Orta': 2,
        'Zayıf': 1,
        'Çok Zayıf': 0
    }
    return scores.get(quality, -1)


class DataManager:

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self.data_lock = threading.Lock()

        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.start_time = time.time()

        self.rssi_history = deque(maxlen=300)
        self.rtt_history = deque(maxlen=300)
        self.time_history = deque(maxlen=300)

        self.current_rssi = None
        self.current_rtt = None
        self.current_latency = None
        self.current_quality = None
        self.connection_status = 'DISCONNECTED'
        self.measurement_count = 0

        self.rssi_values = []
        self.rtt_values = []
        self.latency_values = []
        self.quality_counts = {
            'Mükemmel': 0,
            'İyi': 0,
            'Orta': 0,
            'Zayıf': 0,
            'Çok Zayıf': 0
        }

        self.lost_packets = 0
        self.disconnects = 0
        self.disconnect_durations = []
        self.last_disconnect_time = None

        self.warnings = deque(maxlen=50)
        self.warning_counts = {
            'BILGI': 0,
            'DIKKAT': 0,
            'UYARI': 0,
            'KRITIK': 0
        }

        self.predictor = ConnectionPredictor(model_path=ML_MODEL_PATH)

        self._init_csv()

        print('[DataManager] Baslatildi - Session:', self.session_id)

    def _init_csv(self):
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)

        file_exists = os.path.exists(CSV_FILE)
        self.csv_file = open(CSV_FILE, 'a', newline='', encoding='utf-8')
        self.csv_writer = csv.writer(self.csv_file)

        if not file_exists:
            self.csv_writer.writerow(CSV_HEADERS)
            self.csv_file.flush()

    def _write_csv_row(self, measurement_id, event_type, rssi=None, rtt=None,
                       latency=None, quality=None, disconnect_duration=None):
        now = datetime.now()
        timestamp = now.isoformat(timespec='milliseconds')
        unix_time = time.time()
        quality_score = get_quality_score(quality) if quality else ''

        row = [
            self.session_id,
            timestamp,
            unix_time,
            measurement_id if measurement_id else '',
            event_type,
            rssi if rssi is not None else '',
            rtt if rtt is not None else '',
            latency if latency is not None else '',
            quality if quality else '',
            quality_score if quality_score != -1 else '',
            disconnect_duration if disconnect_duration is not None else ''
        ]

        self.csv_writer.writerow(row)
        self.csv_file.flush()

    def add_measurement(self, rssi, rtt, count):
        with self.data_lock:
            timestamp = datetime.now().isoformat(timespec='milliseconds')
            latency = rtt // 2
            quality = get_signal_quality(rssi)
            quality_score = get_quality_score(quality)

            packet_loss = 0
            if self.measurement_count > 0 and count > self.measurement_count + 1:
                packet_loss = count - self.measurement_count - 1
                self.lost_packets += packet_loss

            self.current_rssi = rssi
            self.current_rtt = rtt
            self.current_latency = latency
            self.current_quality = quality
            self.measurement_count = count

            self.rssi_history.append({'time': timestamp, 'value': rssi})
            self.rtt_history.append({'time': timestamp, 'value': rtt})
            self.time_history.append(timestamp)

            self.rssi_values.append(rssi)
            self.rtt_values.append(rtt)
            self.latency_values.append(latency)
            self.quality_counts[quality] = self.quality_counts.get(quality, 0) + 1

            prediction = self.predictor.predict(
                rssi=rssi,
                rtt=rtt,
                latency=latency,
                quality_score=quality_score
            )

            warning_data = None
            if prediction['warning_level'] > 0:
                warning_data = {
                    'timestamp': timestamp,
                    'level': prediction['warning_level'],
                    'messages': prediction['messages'],
                    'source': prediction['source']
                }
                self.warnings.appendleft(warning_data)
                self._update_warning_counts(prediction['warning_level'])

            self._write_csv_row(count, 'DATA', rssi=rssi, rtt=rtt,
                               latency=latency, quality=quality)

            return {
                'rssi': rssi,
                'rtt': rtt,
                'latency': latency,
                'quality': quality,
                'quality_score': quality_score,
                'count': count,
                'timestamp': timestamp,
                'packet_loss': packet_loss,
                'warning': warning_data
            }

    def _update_warning_counts(self, warning_level):
        if warning_level == 4:
            self.warning_counts['KRITIK'] += 1
        elif warning_level == 3:
            self.warning_counts['UYARI'] += 1
        elif warning_level == 2:
            self.warning_counts['DIKKAT'] += 1
        elif warning_level == 1:
            self.warning_counts['BILGI'] += 1

    def set_disconnected(self):
        with self.data_lock:
            self.connection_status = 'DISCONNECTED'
            self.disconnects += 1
            self.last_disconnect_time = time.time()

            timestamp = datetime.now().isoformat(timespec='milliseconds')
            self._write_csv_row(None, 'DISCONNECTED')

            warning_data = {
                'timestamp': timestamp,
                'level': 4,
                'messages': ['BAĞLANTI KOPTU! Client ile iletişim kesildi.'],
                'source': 'system'
            }
            self.warnings.appendleft(warning_data)
            self._update_warning_counts(4)

            return {
                'status': 'DISCONNECTED',
                'timestamp': timestamp,
                'disconnect_count': self.disconnects,
                'warning': warning_data
            }

    def set_connected(self):
        with self.data_lock:
            duration = None
            if self.last_disconnect_time:
                duration = time.time() - self.last_disconnect_time
                self.disconnect_durations.append(duration)
                self.last_disconnect_time = None

            self.connection_status = 'CONNECTED'
            timestamp = datetime.now().isoformat(timespec='milliseconds')

            self._write_csv_row(None, 'CONNECTED', disconnect_duration=duration)

            return {
                'status': 'CONNECTED',
                'timestamp': timestamp,
                'duration': duration
            }

    def get_session_duration(self):
        return time.time() - self.start_time

    def get_duration_formatted(self):
        duration = self.get_session_duration()
        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        seconds = int(duration % 60)
        if hours > 0:
            return '{:02d}:{:02d}:{:02d}'.format(hours, minutes, seconds)
        else:
            return '{:02d}:{:02d}'.format(minutes, seconds)

    def calculate_stats(self, values):
        if not values:
            return {'min': 0, 'max': 0, 'avg': 0, 'std': 0, 'median': 0}

        n = len(values)
        sorted_vals = sorted(values)
        avg = sum(values) / n
        variance = sum((x - avg) ** 2 for x in values) / n
        std = variance ** 0.5
        median = sorted_vals[n // 2] if n % 2 == 1 else (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2

        return {
            'min': min(values),
            'max': max(values),
            'avg': round(avg, 1),
            'std': round(std, 2),
            'median': round(median, 1)
        }

    def get_current_data(self):
        with self.data_lock:
            return {
                'session_id': self.session_id,
                'duration': self.get_duration_formatted(),
                'duration_seconds': self.get_session_duration(),
                'connection_status': self.connection_status,
                'current': {
                    'rssi': self.current_rssi,
                    'rtt': self.current_rtt,
                    'latency': self.current_latency,
                    'quality': self.current_quality,
                    'count': self.measurement_count
                },
                'stats': {
                    'rssi': self.calculate_stats(self.rssi_values),
                    'rtt': self.calculate_stats(self.rtt_values),
                    'latency': self.calculate_stats(self.latency_values)
                },
                'quality_distribution': dict(self.quality_counts),
                'issues': {
                    'packet_loss': self.lost_packets,
                    'packet_loss_rate': round(self.lost_packets / (len(self.rssi_values) + self.lost_packets) * 100, 2) if (len(self.rssi_values) + self.lost_packets) > 0 else 0,
                    'disconnects': self.disconnects,
                    'total_downtime': round(sum(self.disconnect_durations), 1) if self.disconnect_durations else 0,
                    'avg_disconnect': round(sum(self.disconnect_durations) / len(self.disconnect_durations), 1) if self.disconnect_durations else 0
                },
                'warnings': list(self.warnings),
                'warning_counts': dict(self.warning_counts),
                'predictor': self.predictor.get_status(),
                'chart_data': {
                    'rssi': list(self.rssi_history),
                    'rtt': list(self.rtt_history)
                }
            }

    def close(self):
        if hasattr(self, 'csv_file') and self.csv_file:
            self.csv_file.close()
