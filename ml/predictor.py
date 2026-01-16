import os
from .rules import RuleBasedPredictor, WARNING_LEVEL_NONE, WARNING_LEVEL_INFO, WARNING_LEVEL_CAUTION, WARNING_LEVEL_WARNING, WARNING_LEVEL_CRITICAL

try:
    from .features import extract_features, features_to_array
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    extract_features = None
    features_to_array = None

MIN_DISCONNECTS_FOR_ML = 100
MIN_DATA_POINTS_FOR_ML = 500


class ConnectionPredictor:

    def __init__(self, model_path=None, thresholds=None):
        self.rule_predictor = RuleBasedPredictor(thresholds)
        self.ml_model = None
        self.model_path = model_path
        self.ml_enabled = False

        self.window = []
        self.window_size = 10

        self.total_predictions = 0
        self.warnings_given = 0

        if model_path and os.path.exists(model_path) and NUMPY_AVAILABLE:
            self._load_model(model_path)
        elif model_path and os.path.exists(model_path) and not NUMPY_AVAILABLE:
            print('[ML] numpy bulunamadi - sadece kural tabanli sistem aktif')

    def _load_model(self, path):
        try:
            import joblib
            self.ml_model = joblib.load(path)
            self.ml_enabled = True
            print('[ML] Model yuklendi:', path)
        except Exception as e:
            print('[ML] Model yuklenemedi:', e)
            self.ml_enabled = False

    def add_measurement(self, rssi, rtt, latency, quality_score):
        measurement = {
            'rssi': rssi,
            'rtt': rtt,
            'latency': latency,
            'quality_score': quality_score
        }

        self.window.append(measurement)

        if len(self.window) > self.window_size:
            self.window.pop(0)

    def predict(self, rssi, rtt, latency, quality_score):
        self.total_predictions += 1

        self.add_measurement(rssi, rtt, latency, quality_score)

        result = {
            'warning_level': WARNING_LEVEL_NONE,
            'messages': [],
            'ml_probability': None,
            'source': 'rules'
        }

        rule_level, rule_messages = self.rule_predictor.predict(
            rssi=rssi,
            rtt=rtt,
            latency=latency,
            quality_score=quality_score
        )

        result['warning_level'] = rule_level
        result['messages'] = rule_messages

        if self.ml_enabled and NUMPY_AVAILABLE and len(self.window) >= self.window_size:
            try:
                import numpy as np
                features = extract_features(self.window)
                feature_vector = features_to_array(features).reshape(1, -1)

                probability = self.ml_model.predict_proba(feature_vector)[0][1]
                result['ml_probability'] = probability

                # 4 kademeli ML tahmin sistemi
                if probability >= 0.85:
                    if result['warning_level'] < WARNING_LEVEL_CRITICAL:
                        result['warning_level'] = WARNING_LEVEL_CRITICAL
                        result['messages'].append(
                            'ML Tahmini: Çok yüksek risk (%{:.0f})! Bağlantı her an kopabilir.'.format(probability * 100)
                        )
                    result['source'] = 'hybrid'

                elif probability >= 0.70:
                    if result['warning_level'] < WARNING_LEVEL_WARNING:
                        result['warning_level'] = WARNING_LEVEL_WARNING
                        result['messages'].append(
                            'ML Tahmini: Yüksek kopma riski (%{:.0f}). Önlem alınması önerilir.'.format(probability * 100)
                        )
                    result['source'] = 'hybrid'

                elif probability >= 0.50:
                    if result['warning_level'] < WARNING_LEVEL_CAUTION:
                        result['warning_level'] = WARNING_LEVEL_CAUTION
                        result['messages'].append(
                            'ML Tahmini: Bağlantı stabilitesi düşüyor (%{:.0f}). İzlenmeli.'.format(probability * 100)
                        )
                    result['source'] = 'hybrid'

                elif probability >= 0.30:
                    if result['warning_level'] < WARNING_LEVEL_INFO:
                        result['warning_level'] = WARNING_LEVEL_INFO
                        result['messages'].append(
                            'ML Tahmini: Hafif dalgalanma tespit edildi (%{:.0f}).'.format(probability * 100)
                        )
                    result['source'] = 'hybrid'

            except Exception as e:
                pass

        if result['warning_level'] > WARNING_LEVEL_NONE:
            self.warnings_given += 1

        return result

    def format_warning(self, result):
        if result['warning_level'] == WARNING_LEVEL_NONE:
            return None

        level = result['warning_level']
        messages = result['messages']

        if level >= WARNING_LEVEL_CRITICAL:
            prefix = '[!!!] KRITIK:'
        elif level >= WARNING_LEVEL_WARNING:
            prefix = '[!!] UYARI:'
        elif level >= WARNING_LEVEL_CAUTION:
            prefix = '[!] DIKKAT:'
        else:
            prefix = '[i]'

        return '{} {}'.format(prefix, ' | '.join(messages))

    def get_status(self):
        if self.ml_enabled:
            mode = 'Hibrit (Kural + ML)'
        elif not NUMPY_AVAILABLE:
            mode = 'Kural Tabanlı (numpy yükleyin ML için)'
        else:
            mode = 'Kural Tabanlı'

        return {
            'ml_enabled': self.ml_enabled,
            'numpy_available': NUMPY_AVAILABLE,
            'window_size': len(self.window),
            'total_predictions': self.total_predictions,
            'warnings_given': self.warnings_given,
            'mode': mode
        }

    def clear(self):
        self.window = []
        self.rule_predictor.clear_history()
        self.total_predictions = 0
        self.warnings_given = 0
