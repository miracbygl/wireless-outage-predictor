import numpy as np

FEATURE_NAMES = [
    'rssi_mean',
    'rssi_std',
    'rssi_min',
    'rssi_max',
    'rssi_trend',
    'rssi_delta',
    'rtt_mean',
    'rtt_std',
    'rtt_min',
    'rtt_max',
    'rtt_trend',
    'quality_mean',
    'quality_std',
]


def extract_features(window_data):
    rssi = [d['rssi'] for d in window_data if d.get('rssi') is not None]
    rtt = [d['rtt'] for d in window_data if d.get('rtt') is not None and d['rtt'] > 0]
    quality = [d['quality_score'] for d in window_data if d.get('quality_score') is not None]

    features = {}

    if len(rssi) >= 2:
        features['rssi_mean'] = np.mean(rssi)
        features['rssi_std'] = np.std(rssi)
        features['rssi_min'] = np.min(rssi)
        features['rssi_max'] = np.max(rssi)

        x = np.arange(len(rssi))
        features['rssi_trend'] = np.polyfit(x, rssi, 1)[0]

        features['rssi_delta'] = rssi[-1] - rssi[0]
    else:
        features['rssi_mean'] = rssi[0] if rssi else 0
        features['rssi_std'] = 0
        features['rssi_min'] = rssi[0] if rssi else 0
        features['rssi_max'] = rssi[0] if rssi else 0
        features['rssi_trend'] = 0
        features['rssi_delta'] = 0

    if len(rtt) >= 2:
        features['rtt_mean'] = np.mean(rtt)
        features['rtt_std'] = np.std(rtt)
        features['rtt_min'] = np.min(rtt)
        features['rtt_max'] = np.max(rtt)

        x = np.arange(len(rtt))
        features['rtt_trend'] = np.polyfit(x, rtt, 1)[0]
    else:
        features['rtt_mean'] = rtt[0] if rtt else 0
        features['rtt_std'] = 0
        features['rtt_min'] = rtt[0] if rtt else 0
        features['rtt_max'] = rtt[0] if rtt else 0
        features['rtt_trend'] = 0

    if quality:
        features['quality_mean'] = np.mean(quality)
        features['quality_std'] = np.std(quality) if len(quality) >= 2 else 0
    else:
        features['quality_mean'] = 0
        features['quality_std'] = 0

    return features


def features_to_array(features):
    return np.array([features.get(name, 0) for name in FEATURE_NAMES])


def create_training_data(df, window_size=10, prediction_horizon=5):
    data_df = df[df['event_type'] == 'DATA'].copy()
    data_df = data_df.reset_index(drop=True)

    problem_indices = set()
    for idx, row in df.iterrows():
        if row['event_type'] in ['DISCONNECTED', 'PACKET_LOST']:
            problem_time = row['unix_time']
            for data_idx, data_row in data_df.iterrows():
                if data_row['unix_time'] < problem_time:
                    time_diff = problem_time - data_row['unix_time']
                    estimated_measurements = time_diff / 4
                    if estimated_measurements <= prediction_horizon:
                        problem_indices.add(data_idx)

    X = []
    y = []

    for i in range(window_size, len(data_df)):
        window = data_df.iloc[i-window_size:i]

        window_data = []
        for _, row in window.iterrows():
            window_data.append({
                'rssi': row['rssi'] if not np.isnan(row['rssi']) else None,
                'rtt': row['rtt'] if not np.isnan(row['rtt']) else None,
                'latency': row['latency'] if not np.isnan(row['latency']) else None,
                'quality_score': row['quality_score'] if not np.isnan(row['quality_score']) else None,
            })

        features = extract_features(window_data)
        feature_vector = features_to_array(features)

        label = 1 if i in problem_indices else 0

        X.append(feature_vector)
        y.append(label)

    return np.array(X), np.array(y)
