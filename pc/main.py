import socket
import sys
import time
import csv
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.predictor import ConnectionPredictor

AP_IP = '192.168.4.1'
AP_PORT = 12346

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
CSV_FILE = os.path.join(DATA_DIR, 'rssi_data.csv')
CSV_HEADERS = ['session_id', 'timestamp', 'unix_time', 'measurement_id', 'event_type',
               'rssi', 'rtt', 'latency', 'quality', 'quality_score', 'disconnect_duration']

ML_MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ml', 'model.pkl')


def get_signal_quality(rssi):
    if rssi >= -50:
        return 'Mukemmel'
    elif rssi >= -60:
        return 'Iyi'
    elif rssi >= -70:
        return 'Orta'
    elif rssi >= -80:
        return 'Zayif'
    else:
        return 'Cok Zayif'


def get_signal_bar(rssi):
    if rssi >= -50:
        return '[#####]'
    elif rssi >= -60:
        return '[#### ]'
    elif rssi >= -70:
        return '[###  ]'
    elif rssi >= -80:
        return '[##   ]'
    else:
        return '[#    ]'


def get_quality_score(quality):
    scores = {
        'Mukemmel': 4,
        'Iyi': 3,
        'Orta': 2,
        'Zayif': 1,
        'Cok Zayif': 0
    }
    return scores.get(quality, -1)


class SessionStatistics:

    def __init__(self):
        self.start_time = time.time()
        self.rssi_values = []
        self.rtt_values = []
        self.latency_values = []
        self.quality_counts = {
            'Mukemmel': 0,
            'Iyi': 0,
            'Orta': 0,
            'Zayif': 0,
            'Cok Zayif': 0
        }
        self.total_measurements = 0
        self.lost_packets = 0
        self.disconnects = 0
        self.disconnect_durations = []
        self.warnings_by_level = {
            'DIKKAT': 0,
            'UYARI': 0,
            'KRITIK': 0
        }

    def add_measurement(self, rssi, rtt, latency, quality):
        self.rssi_values.append(rssi)
        self.rtt_values.append(rtt)
        self.latency_values.append(latency)
        self.quality_counts[quality] = self.quality_counts.get(quality, 0) + 1
        self.total_measurements += 1

    def add_packet_loss(self, count=1):
        self.lost_packets += count

    def add_disconnect(self, duration=None):
        self.disconnects += 1
        if duration is not None:
            self.disconnect_durations.append(duration)

    def add_warning(self, warning_msg):
        if warning_msg:
            if 'KRITIK' in warning_msg:
                self.warnings_by_level['KRITIK'] += 1
            elif 'UYARI' in warning_msg:
                self.warnings_by_level['UYARI'] += 1
            elif 'DIKKAT' in warning_msg:
                self.warnings_by_level['DIKKAT'] += 1

    def get_duration(self):
        return time.time() - self.start_time

    def get_duration_formatted(self):
        duration = self.get_duration()
        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        seconds = int(duration % 60)
        if hours > 0:
            return '{}s {}dk {}sn'.format(hours, minutes, seconds)
        elif minutes > 0:
            return '{}dk {}sn'.format(minutes, seconds)
        else:
            return '{}sn'.format(seconds)

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
            'avg': avg,
            'std': std,
            'median': median
        }

    def print_summary(self, csv_file_path, records_written, predictor_status):
        duration = self.get_duration()

        print('\n')
        print('=' * 70)
        print('                    OTURUM ISTATISTIKLERI')
        print('=' * 70)

        print('\n--- GENEL BILGILER ---')
        print('  Oturum suresi:        {}'.format(self.get_duration_formatted()))
        print('  Toplam olcum:         {}'.format(self.total_measurements))
        if duration > 0:
            rate = self.total_measurements / duration * 60
            print('  Olcum hizi:           {:.1f} olcum/dakika'.format(rate))

        if self.rssi_values:
            print('\n--- RSSI ISTATISTIKLERI (dBm) ---')
            rssi_stats = self.calculate_stats(self.rssi_values)
            print('  Minimum:              {} dBm'.format(rssi_stats['min']))
            print('  Maksimum:             {} dBm'.format(rssi_stats['max']))
            print('  Ortalama:             {:.1f} dBm'.format(rssi_stats['avg']))
            print('  Medyan:               {:.1f} dBm'.format(rssi_stats['median']))
            print('  Standart Sapma:       {:.2f} dBm'.format(rssi_stats['std']))
            ranges = {'< -80': 0, '-80 ile -70': 0, '-70 ile -60': 0, '-60 ile -50': 0, '>= -50': 0}
            for r in self.rssi_values:
                if r < -80:
                    ranges['< -80'] += 1
                elif r < -70:
                    ranges['-80 ile -70'] += 1
                elif r < -60:
                    ranges['-70 ile -60'] += 1
                elif r < -50:
                    ranges['-60 ile -50'] += 1
                else:
                    ranges['>= -50'] += 1
            print('  Aralik Dagilimi:')
            for rng, cnt in ranges.items():
                pct = (cnt / len(self.rssi_values) * 100) if self.rssi_values else 0
                bar = '#' * int(pct / 5)
                print('    {:15s}  {:4d} ({:5.1f}%) {}'.format(rng, cnt, pct, bar))

        if self.rtt_values:
            print('\n--- RTT ISTATISTIKLERI (ms) ---')
            rtt_stats = self.calculate_stats(self.rtt_values)
            print('  Minimum:              {} ms'.format(rtt_stats['min']))
            print('  Maksimum:             {} ms'.format(rtt_stats['max']))
            print('  Ortalama:             {:.1f} ms'.format(rtt_stats['avg']))
            print('  Medyan:               {:.1f} ms'.format(rtt_stats['median']))
            print('  Standart Sapma:       {:.2f} ms'.format(rtt_stats['std']))

        if self.latency_values:
            print('\n--- GECIKME (LATENCY) ISTATISTIKLERI (ms) ---')
            lat_stats = self.calculate_stats(self.latency_values)
            print('  Minimum:              {} ms'.format(lat_stats['min']))
            print('  Maksimum:             {} ms'.format(lat_stats['max']))
            print('  Ortalama:             {:.1f} ms'.format(lat_stats['avg']))
            print('  Medyan:               {:.1f} ms'.format(lat_stats['median']))
            print('  Standart Sapma:       {:.2f} ms'.format(lat_stats['std']))

        print('\n--- SINYAL KALITESI DAGILIMI ---')
        total_q = sum(self.quality_counts.values())
        for quality in ['Mukemmel', 'Iyi', 'Orta', 'Zayif', 'Cok Zayif']:
            cnt = self.quality_counts[quality]
            pct = (cnt / total_q * 100) if total_q > 0 else 0
            bar = '#' * int(pct / 5)
            print('  {:12s}  {:4d} ({:5.1f}%) {}'.format(quality, cnt, pct, bar))

        print('\n--- BAGLANTI SORUNLARI ---')
        print('  Kayip paket:          {}'.format(self.lost_packets))
        if self.total_measurements > 0:
            loss_rate = self.lost_packets / (self.total_measurements + self.lost_packets) * 100
            print('  Paket kayip orani:    {:.2f}%'.format(loss_rate))
        print('  Baglanti kopma:       {}'.format(self.disconnects))
        if self.disconnect_durations:
            avg_disc = sum(self.disconnect_durations) / len(self.disconnect_durations)
            print('  Ort. kopma suresi:    {:.1f} saniye'.format(avg_disc))
            print('  Toplam kopma suresi:  {:.1f} saniye'.format(sum(self.disconnect_durations)))

        total_warnings = sum(self.warnings_by_level.values())
        if total_warnings > 0:
            print('\n--- UYARI ISTATISTIKLERI ---')
            print('  DIKKAT uyarilari:     {}'.format(self.warnings_by_level['DIKKAT']))
            print('  UYARI uyarilari:      {}'.format(self.warnings_by_level['UYARI']))
            print('  KRITIK uyarilari:     {}'.format(self.warnings_by_level['KRITIK']))
            print('  Toplam uyari:         {}'.format(total_warnings))

        print('\n--- TAHMIN SISTEMI ---')
        print('  Mod:                  {}'.format(predictor_status['mode']))
        print('  Toplam tahmin:        {}'.format(predictor_status['total_predictions']))
        print('  Verilen uyari:        {}'.format(predictor_status['warnings_given']))

        print('\n--- VERI KAYIT ---')
        print('  CSV kayit sayisi:     {}'.format(records_written))
        print('  CSV dosyasi:          {}'.format(csv_file_path))

        print('\n' + '=' * 70)


def init_csv_file():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print('Veri klasoru olusturuldu:', DATA_DIR)

    file_exists = os.path.exists(CSV_FILE)

    csv_file = open(CSV_FILE, 'a', newline='', encoding='utf-8')
    csv_writer = csv.writer(csv_file)

    if not file_exists:
        csv_writer.writerow(CSV_HEADERS)
        csv_file.flush()
        print('CSV dosyasi olusturuldu:', CSV_FILE)
    else:
        print('CSV dosyasina ekleniyor:', CSV_FILE)

    return csv_file, csv_writer


def write_data_row(csv_writer, csv_file, session_id, measurement_id, event_type,
                   rssi=None, rtt=None, latency=None, quality=None, disconnect_duration=None):
    now = datetime.now()
    timestamp = now.isoformat(timespec='milliseconds')
    unix_time = time.time()

    quality_score = get_quality_score(quality) if quality else ''

    row = [
        session_id,
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

    csv_writer.writerow(row)
    csv_file.flush()


def main():
    print('=' * 70)
    print('           LoPy4 RSSI + RTT Monitor - Bilgisayar')
    print('=' * 70)
    print()
    print('AP IP:', AP_IP)
    print('AP Port:', AP_PORT)
    print('Baglanti durumu: AP tarafindan bildirilir')
    print()

    session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_file, csv_writer = init_csv_file()
    records_written = 0
    print('Oturum ID:', session_id)

    stats = SessionStatistics()

    predictor = ConnectionPredictor(model_path=ML_MODEL_PATH)
    status = predictor.get_status()
    print('Tahmin sistemi:', status['mode'])
    print()
    print('Baglanti kuruluyor...')
    print()

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        sock.connect((AP_IP, AP_PORT))

        print('Baglanildi! Veri bekleniyor...')
        print()
        print('-' * 70)
        print('{:^10} {:^8} {:^8} {:^10} {:^8} {:^10} {:^10}'.format(
            'PC Zaman', 'Olcum#', 'Bar', 'RSSI', 'RTT', 'Gecikme', 'Kalite'
        ))
        print('-' * 70)

        buffer = ''
        last_count = 0
        lost_packets = 0
        disconnects = 0

        is_disconnected = False
        disconnect_time = None

        while True:
            try:
                data = sock.recv(1024)
                if not data:
                    print('Baglanti kesildi!')
                    break

                buffer += data.decode()

                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()

                    if line.startswith('STATUS:'):
                        status = line[7:]
                        pc_time = datetime.now().strftime('%H:%M:%S')

                        if status == 'DISCONNECTED':
                            is_disconnected = True
                            disconnect_time = time.time()
                            disconnects += 1
                            stats.add_disconnect()
                            print('{:^10} {:^8} {:^8} {:^10} {:^8} {:^10} {:^10}'.format(
                                pc_time,
                                '--',
                                '[     ]',
                                '-- dBm',
                                '--ms',
                                '--ms',
                                'KOPTU! (#{})'.format(disconnects)
                            ))
                            write_data_row(csv_writer, csv_file, session_id, None, 'DISCONNECTED')
                            records_written += 1

                        elif status == 'CONNECTED':
                            duration = None
                            if is_disconnected and disconnect_time:
                                duration = time.time() - disconnect_time
                                stats.disconnect_durations.append(duration)
                                print('{:^10} {:^8} {:^8} {:^10} {:^8} {:^10} {:^10}'.format(
                                    pc_time,
                                    '--',
                                    '[+++++]',
                                    '++ dBm',
                                    '++ms',
                                    '++ms',
                                    'DUZELD! ({:.1f}s)'.format(duration)
                                ))
                            write_data_row(csv_writer, csv_file, session_id, None, 'CONNECTED',
                                         disconnect_duration=duration)
                            records_written += 1
                            is_disconnected = False
                            disconnect_time = None

                    elif line.startswith('DATA:'):
                        parts = line[5:].split(',')
                        if len(parts) >= 3:
                            rssi = int(parts[0])
                            rtt = int(parts[1])
                            count = int(parts[2])
                            latency = rtt // 2

                            if last_count > 0 and count > last_count + 1:
                                missing = count - last_count - 1
                                lost_packets += missing
                                stats.add_packet_loss(missing)
                                for i in range(last_count + 1, count):
                                    pc_time = datetime.now().strftime('%H:%M:%S')
                                    print('{:^10} {:^8} {:^8} {:^10} {:^8} {:^10} {:^10}'.format(
                                        pc_time,
                                        '#{}'.format(i),
                                        '[XXXXX]',
                                        '-- dBm',
                                        '--ms',
                                        '--ms',
                                        'KAYIP!'
                                    ))
                                    write_data_row(csv_writer, csv_file, session_id, i, 'PACKET_LOST')
                                    records_written += 1

                            last_count = count

                            quality = get_signal_quality(rssi)
                            quality_score = get_quality_score(quality)
                            bar = get_signal_bar(rssi)
                            pc_time = datetime.now().strftime('%H:%M:%S')

                            stats.add_measurement(rssi, rtt, latency, quality)

                            print('{:^10} {:^8} {:^8} {:^10} {:^8} {:^10} {:^10}'.format(
                                pc_time,
                                '#{}'.format(count),
                                bar,
                                '{} dBm'.format(rssi),
                                '{}ms'.format(rtt),
                                '~{}ms'.format(latency),
                                quality
                            ))

                            prediction = predictor.predict(
                                rssi=rssi,
                                rtt=rtt,
                                latency=latency,
                                quality_score=quality_score
                            )

                            warning_msg = predictor.format_warning(prediction)
                            if warning_msg:
                                print(warning_msg)
                                stats.add_warning(warning_msg)

                            write_data_row(csv_writer, csv_file, session_id, count, 'DATA',
                                         rssi=rssi, rtt=rtt, latency=latency, quality=quality)
                            records_written += 1

            except socket.timeout:
                continue

            except KeyboardInterrupt:
                pred_status = predictor.get_status()
                stats.print_summary(CSV_FILE, records_written, pred_status)
                break

        sock.close()
        csv_file.close()

    except socket.timeout:
        print()
        print('HATA: Baglanti zaman asimina ugradi!')
        print('Kontrol edin:')
        print('  1. Bilgisayar "LoPy4-Network" Wi-Fi agina bagli mi?')
        print('  2. LoPy4 AP cihazi calisiyor mu?')
        csv_file.close()
        sys.exit(1)

    except ConnectionRefusedError:
        print()
        print('HATA: Baglanti reddedildi!')
        print('LoPy4 AP cihazinin calistigini kontrol edin.')
        csv_file.close()
        sys.exit(1)

    except Exception as e:
        print()
        print('HATA:', str(e))
        csv_file.close()
        sys.exit(1)


if __name__ == '__main__':
    main()
