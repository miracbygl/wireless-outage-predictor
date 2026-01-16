#!/usr/bin/env python3

import os
import sys
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix
import joblib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.features import create_training_data, FEATURE_NAMES

DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'rssi_data.csv')
MODEL_FILE = os.path.join(os.path.dirname(__file__), 'model.pkl')
WINDOW_SIZE = 10
PREDICTION_HORIZON = 5
MIN_SAMPLES = 100


def load_data():
    if not os.path.exists(DATA_FILE):
        print('HATA: Veri dosyasi bulunamadi:', DATA_FILE)
        print('Once veri toplayin (pc/main.py calistirin)')
        sys.exit(1)

    df = pd.read_csv(DATA_FILE)
    print('Veri yuklendi: {} satir'.format(len(df)))

    data_count = len(df[df['event_type'] == 'DATA'])
    disconnect_count = len(df[df['event_type'] == 'DISCONNECTED'])
    packet_loss_count = len(df[df['event_type'] == 'PACKET_LOST'])

    print('\nVeri Istatistikleri:')
    print('  DATA olcumleri:', data_count)
    print('  DISCONNECTED eventi:', disconnect_count)
    print('  PACKET_LOST eventi:', packet_loss_count)

    return df, data_count, disconnect_count, packet_loss_count


def check_data_quality(data_count, disconnect_count, packet_loss_count):
    total_problems = disconnect_count + packet_loss_count

    if data_count < MIN_SAMPLES:
        print('\nUYARI: Yetersiz veri!')
        print('  Mevcut: {} olcum'.format(data_count))
        print('  Gerekli: {} olcum'.format(MIN_SAMPLES))
        print('\nDaha fazla veri toplayin.')
        return False

    if total_problems < 10:
        print('\nUYARI: Yetersiz problem ornegi!')
        print('  Mevcut: {} problem (DISCONNECTED + PACKET_LOST)'.format(total_problems))
        print('  Onerilen: En az 10 problem')
        print('\nFarkli kosullarda daha fazla veri toplayin.')
        return False

    return True


def train_model(X, y):
    print('\n' + '='*50)
    print('MODEL EGITIMI')
    print('='*50)

    print('\nVeri boyutu: {} ornek, {} ozellik'.format(X.shape[0], X.shape[1]))
    print('Sinif dagilimi:')
    print('  Normal (0): {}'.format(np.sum(y == 0)))
    print('  Problem (1): {}'.format(np.sum(y == 1)))

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y if np.sum(y) > 1 else None
    )

    print('\nEgitim seti: {} ornek'.format(len(X_train)))
    print('Test seti: {} ornek'.format(len(X_test)))

    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        class_weight='balanced'
    )

    print('\nModel egitiliyor...')
    model.fit(X_train, y_train)

    print('\n' + '-'*50)
    print('DEGERLENDIRME')
    print('-'*50)

    y_pred = model.predict(X_test)
    print('\nSiniflandirma Raporu:')
    print(classification_report(y_test, y_pred, target_names=['Normal', 'Problem']))

    print('\nKarisiklik Matrisi:')
    cm = confusion_matrix(y_test, y_pred)
    print('                 Tahmin')
    print('               Normal  Problem')
    print('Gercek Normal    {:4d}     {:4d}'.format(cm[0][0], cm[0][1]))
    print('       Problem   {:4d}     {:4d}'.format(cm[1][0], cm[1][1]))

    print('\n5-Fold Cross Validation:')
    cv_scores = cross_val_score(model, X, y, cv=5, scoring='f1')
    print('  F1 Skorlari:', ['{:.3f}'.format(s) for s in cv_scores])
    print('  Ortalama F1: {:.3f} (+/- {:.3f})'.format(cv_scores.mean(), cv_scores.std() * 2))

    print('\nOzellik Onemleri:')
    importances = sorted(zip(FEATURE_NAMES, model.feature_importances_),
                        key=lambda x: x[1], reverse=True)
    for name, importance in importances:
        bar = '#' * int(importance * 50)
        print('  {:15s} {:.3f} {}'.format(name, importance, bar))

    return model


def save_model(model):
    joblib.dump(model, MODEL_FILE)
    print('\n' + '='*50)
    print('Model kaydedildi:', MODEL_FILE)
    print('='*50)


def main():
    print('='*50)
    print('  RSSI/RTT Baglanti Tahmini - ML Egitimi')
    print('='*50)

    df, data_count, disconnect_count, packet_loss_count = load_data()

    if not check_data_quality(data_count, disconnect_count, packet_loss_count):
        print('\nEgitim iptal edildi.')
        sys.exit(1)

    print('\nEgitim verisi olusturuluyor...')
    print('  Pencere boyutu: {}'.format(WINDOW_SIZE))
    print('  Tahmin ufku: {} olcum'.format(PREDICTION_HORIZON))

    X, y = create_training_data(df, window_size=WINDOW_SIZE, prediction_horizon=PREDICTION_HORIZON)

    if len(X) < MIN_SAMPLES:
        print('\nHATA: Yeterli egitim ornegi olusturulamadi.')
        print('  Olusturulan: {} ornek'.format(len(X)))
        print('  Gerekli: {} ornek'.format(MIN_SAMPLES))
        sys.exit(1)

    model = train_model(X, y)

    save_model(model)

    print('\nEgitim tamamlandi!')
    print('Simdi pc/main.py calistirarak ML tahminlerini gorebilirsiniz.')


if __name__ == '__main__':
    main()
