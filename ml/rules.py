WARNING_LEVEL_NONE = 0
WARNING_LEVEL_INFO = 1
WARNING_LEVEL_CAUTION = 2
WARNING_LEVEL_WARNING = 3
WARNING_LEVEL_CRITICAL = 4

DEFAULT_THRESHOLDS = {
    'rssi_good': -50,
    'rssi_warning': -60,
    'rssi_critical': -75,
    'rssi_danger': -85,
    'rssi_trend_warning': -3,
    'rssi_trend_critical': -5,
    'rssi_std_warning': 5,
    'rtt_warning': 100,
    'rtt_critical': 200,
    'rtt_trend_warning': 20,
    'latency_warning': 50,
    'latency_critical': 100,
    'quality_drop_warning': 1,
    'quality_drop_critical': 2,
    'window_size': 5,
}


class RuleBasedPredictor:

    def __init__(self, thresholds=None):
        self.thresholds = DEFAULT_THRESHOLDS.copy()
        if thresholds:
            self.thresholds.update(thresholds)

        self.history = []
        self.max_history = 20

    def add_measurement(self, rssi, rtt, latency, quality_score):
        self.history.append({
            'rssi': rssi,
            'rtt': rtt,
            'latency': latency,
            'quality_score': quality_score
        })

        if len(self.history) > self.max_history:
            self.history.pop(0)

    def get_rssi_trend(self):
        window = self.thresholds['window_size']
        if len(self.history) < window:
            return 0

        recent = self.history[-window:]
        rssi_values = [m['rssi'] for m in recent if m['rssi'] is not None]

        if len(rssi_values) < 2:
            return 0

        trend = (rssi_values[-1] - rssi_values[0]) / (len(rssi_values) - 1)
        return trend

    def get_rssi_delta(self):
        window = self.thresholds['window_size']
        if len(self.history) < window:
            return 0

        recent = self.history[-window:]
        rssi_values = [m['rssi'] for m in recent if m['rssi'] is not None]

        if len(rssi_values) < 2:
            return 0

        return rssi_values[-1] - rssi_values[0]

    def get_rssi_std(self):
        window = self.thresholds['window_size']
        if len(self.history) < window:
            return 0

        recent = self.history[-window:]
        rssi_values = [m['rssi'] for m in recent if m['rssi'] is not None]

        if len(rssi_values) < 2:
            return 0

        avg = sum(rssi_values) / len(rssi_values)
        variance = sum((x - avg) ** 2 for x in rssi_values) / len(rssi_values)
        return variance ** 0.5

    def get_quality_trend(self):
        window = self.thresholds['window_size']
        if len(self.history) < window:
            return 0

        recent = self.history[-window:]
        quality_values = [m['quality_score'] for m in recent if m['quality_score'] is not None]

        if len(quality_values) < 2:
            return 0

        return quality_values[-1] - quality_values[0]

    def get_rtt_trend(self):
        window = self.thresholds['window_size']
        if len(self.history) < window:
            return 0

        recent = self.history[-window:]
        rtt_values = [m['rtt'] for m in recent if m['rtt'] is not None and m['rtt'] > 0]

        if len(rtt_values) < 2:
            return 0

        return rtt_values[-1] - rtt_values[0]

    def get_quality_label(self, score):
        labels = {4: 'Mükemmel', 3: 'İyi', 2: 'Orta', 1: 'Zayıf', 0: 'Çok Zayıf'}
        return labels.get(score, 'Bilinmiyor')

    def predict(self, rssi=None, rtt=None, latency=None, quality_score=None):
        if rssi is not None:
            self.add_measurement(rssi, rtt, latency, quality_score)

        messages = []
        max_level = WARNING_LEVEL_NONE

        # RSSI seviye kontrolleri
        if rssi is not None:
            if rssi < self.thresholds['rssi_danger']:
                messages.append('Sinyal çok zayıf ({} dBm)! Cihaz AP\'den çok uzakta veya engel var. Bağlantı her an kopabilir!'.format(rssi))
                max_level = max(max_level, WARNING_LEVEL_CRITICAL)

            elif rssi < self.thresholds['rssi_critical']:
                messages.append('Sinyal kritik seviyede ({} dBm). Yakın zamanda kopma riski yüksek.'.format(rssi))
                max_level = max(max_level, WARNING_LEVEL_WARNING)

            elif rssi < self.thresholds['rssi_warning']:
                messages.append('Sinyal gücü düşük ({} dBm). Bağlantı kalitesi azalıyor.'.format(rssi))
                max_level = max(max_level, WARNING_LEVEL_CAUTION)

        # RSSI trend analizi
        trend = self.get_rssi_trend()
        delta = self.get_rssi_delta()

        if trend < self.thresholds['rssi_trend_critical']:
            messages.append('Sinyal hızla düşüyor! Son {} ölçümde {} dBm kayıp. Cihaz uzaklaşıyor olabilir.'.format(
                self.thresholds['window_size'], int(abs(delta))))
            max_level = max(max_level, WARNING_LEVEL_WARNING)

        elif trend < self.thresholds['rssi_trend_warning']:
            messages.append('Sinyal düşüş eğiliminde. Son {} ölçümde {} dBm azaldı.'.format(
                self.thresholds['window_size'], int(abs(delta))))
            max_level = max(max_level, WARNING_LEVEL_CAUTION)

        elif trend < -1 and max_level == WARNING_LEVEL_NONE:
            messages.append('Sinyalde hafif dalgalanma gözleniyor ({} dBm değişim).'.format(int(abs(delta))))
            max_level = max(max_level, WARNING_LEVEL_INFO)

        # Sinyal stabilitesi (standart sapma)
        rssi_std = self.get_rssi_std()
        if rssi_std > self.thresholds['rssi_std_warning']:
            messages.append('Sinyal dengesiz. Dalgalanma yüksek (±{:.1f} dBm).'.format(rssi_std))
            max_level = max(max_level, WARNING_LEVEL_CAUTION)

        # RTT kontrolleri
        if rtt is not None and rtt > 0:
            if rtt > self.thresholds['rtt_critical']:
                messages.append('Gecikme çok yüksek ({} ms)! Ağ tıkanıklığı veya paket kaybı olabilir.'.format(rtt))
                max_level = max(max_level, WARNING_LEVEL_WARNING)

            elif rtt > self.thresholds['rtt_warning']:
                messages.append('Gecikme normalin üzerinde ({} ms). Yanıt süreleri uzuyor.'.format(rtt))
                max_level = max(max_level, WARNING_LEVEL_CAUTION)

        # RTT trend analizi
        rtt_trend = self.get_rtt_trend()
        if rtt_trend > self.thresholds['rtt_trend_warning']:
            messages.append('Gecikme artış eğiliminde (+{} ms). Ağ yavaşlıyor.'.format(int(rtt_trend)))
            max_level = max(max_level, WARNING_LEVEL_CAUTION)

        # Latency kontrolleri
        if latency is not None and latency > 0:
            if latency > self.thresholds['latency_critical']:
                messages.append('Tek yön gecikme kritik ({} ms). Veri iletimi yavaş.'.format(latency))
                max_level = max(max_level, WARNING_LEVEL_WARNING)

            elif latency > self.thresholds['latency_warning']:
                messages.append('Tek yön gecikme yükseliyor ({} ms).'.format(latency))
                max_level = max(max_level, WARNING_LEVEL_CAUTION)

        # Quality score trend analizi
        quality_trend = self.get_quality_trend()
        if quality_trend <= -self.thresholds['quality_drop_critical']:
            old_quality = quality_score - int(quality_trend) if quality_score is not None else None
            if old_quality is not None:
                messages.append('Sinyal kalitesi hızla düştü: {} → {}. Bağlantı bozuluyor.'.format(
                    self.get_quality_label(old_quality), self.get_quality_label(quality_score)))
            else:
                messages.append('Sinyal kalitesi hızla düşüyor. Bağlantı bozuluyor.')
            max_level = max(max_level, WARNING_LEVEL_WARNING)

        elif quality_trend <= -self.thresholds['quality_drop_warning']:
            old_quality = quality_score - int(quality_trend) if quality_score is not None else None
            if old_quality is not None:
                messages.append('Sinyal kalitesi düşüyor: {} → {}.'.format(
                    self.get_quality_label(old_quality), self.get_quality_label(quality_score)))
            else:
                messages.append('Sinyal kalitesi düşüş eğiliminde.')
            max_level = max(max_level, WARNING_LEVEL_CAUTION)

        return max_level, messages

    def get_warning_prefix(self, level):
        prefixes = {
            WARNING_LEVEL_NONE: '',
            WARNING_LEVEL_INFO: '[i]',
            WARNING_LEVEL_CAUTION: '[!] DIKKAT:',
            WARNING_LEVEL_WARNING: '[!!] UYARI:',
            WARNING_LEVEL_CRITICAL: '[!!!] KRITIK:'
        }
        return prefixes.get(level, '')

    def format_warnings(self, level, messages):
        if not messages:
            return None

        prefix = self.get_warning_prefix(level)
        return ' '.join([prefix] + messages)

    def clear_history(self):
        self.history = []
