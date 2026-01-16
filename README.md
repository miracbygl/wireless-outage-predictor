# Proje Grubu - 2

# LoPy4 Tabanlı Kablosuz Ağ Kesintisi Tahmin Sistemi

Wi-Fi bağlantı kalitesini gerçek zamanlı izleyen ve makine öğrenmesi ile bağlantı kesintilerini önceden tahmin eden IoT tabanlı bir sistem.

---

## Proje Ekibi

| İsim |
|------|
| **Duha Keskin https://github.com/DuhaKeskin** |
| **Miraç Bayoğlu https://github.com/miracbygl** |
| **Eren Bezek** |
| **Yunus Alim Avşar https://github.com/YunusAlim** |
| **Ahmet Güldaş https://github.com/guldasahmet** |

**Ders:** BM-5 Kablosuz Ağlar
**Kurum:** Bursa Teknik Üniversitesi

---

## İçindekiler

- [Proje Hakkında](#proje-hakkında)
- [Temel Özellikler](#temel-özellikler)
- [Sistem Mimarisi](#sistem-mimarisi)
- [Kullanılan Teknolojiler](#kullanılan-teknolojiler)
- [Proje Yapısı](#proje-yapısı)
- [Kurulum](#kurulum)
- [Kullanım](#kullanım)
- [Özellikler Detayı](#özellikler-detayı)
- [API Referansı](#api-referansı)
- [Konfigürasyon](#konfigürasyon)
- [Veri Formatı](#veri-formatı)

---

## Proje Hakkında

Bu proje, **LoPy4 mikrodenetleyici platformu** kullanarak kablosuz ağ bağlantısının kalitesini gerçek zamanlı olarak izleyen ve bağlantı kopmasını/kesintisini önceden tahmin eden kapsamlı bir sistemdir.

### Motivasyon

Kablosuz ağlarda bağlantı kesintileri kullanıcı deneyimini olumsuz etkiler. Bu sistem:
- Kesinti **olmadan önce** uyarı verir
- Sinyal kalitesini sürekli izler
- Makine öğrenmesi ile kesinti riskini tahmin eder
- Gerçek zamanlı web dashboard ile görselleştirme sağlar

### Ne Yapar?

1. **Veri Toplama**: LoPy4 cihazları ile RSSI (sinyal gücü) ve RTT (gecikme) ölçümü
2. **Analiz**: Kural tabanlı ve ML tabanlı hibrit tahmin sistemi
3. **Uyarı**: 5 seviyeli uyarı sistemi ile proaktif bilgilendirme
4. **Görselleştirme**: Web tabanlı gerçek zamanlı dashboard

---

## Temel Özellikler

- **Gerçek Zamanlı İzleme**: RSSI, RTT ve latency değerlerinin anlık takibi
- **Hibrit Tahmin Sistemi**: Kural tabanlı + Random Forest ML modeli
- **5 Seviyeli Uyarı**: NONE → INFO → CAUTION → WARNING → CRITICAL
- **Web Dashboard**: Socket.IO ile canlı grafik ve göstergeler
- **Veri Kaydı**: Tüm ölçümler CSV formatında saklanır
- **Paket Kaybı Takibi**: Kayıp paketlerin otomatik tespiti
- **Bağlantı Kopma Algılama**: Kesinti süresi ve sayısı takibi
- **Cross-Platform**: LoPy4 (MicroPython) + PC (Python 3) desteği

---

## Sistem Mimarisi

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SISTEM MİMARİSİ                                 │
└─────────────────────────────────────────────────────────────────────────┘

                    ┌──────────────────┐
                    │   LoPy4 Client   │
                    │  (client/main.py)│
                    │                  │
                    │  • RSSI Ölçümü   │
                    │  • RTT Hesabı    │
                    │  • LED Durumu    │
                    └────────┬─────────┘
                             │
                             │ Wi-Fi (TCP Port: 12345)
                             │ SSID: LoPy4-Network
                             ▼
                    ┌──────────────────┐
                    │   LoPy4 AP       │
                    │   (ap/main.py)   │
                    │                  │
                    │  • Access Point  │
                    │  • Veri Relay    │
                    │  • Durum İzleme  │
                    └────────┬─────────┘
                             │
                             │ TCP Socket (Port: 12346)
                             │ IP: 192.168.4.1
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            PC / WEB SUNUCU                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐      │
│  │  Socket Client  │───▶│  Data Manager   │───▶│   Predictor     │      │
│  │                 │    │   (Singleton)   │    │   (Hibrit ML)   │      │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘      │
│           │                      │                      │               │
│           │                      ▼                      │               │
│           │              ┌─────────────────┐            │               │
│           │              │   CSV Dosyası   │            │               │
│           │              │ (rssi_data.csv) │            │               │
│           │              └─────────────────┘            │               │
│           │                                             │               │
│           └──────────────┬──────────────────────────────┘               │
│                          │                                              │
│                          ▼                                              │
│                 ┌─────────────────┐                                     │
│                 │  Flask Server   │                                     │
│                 │  + Socket.IO    │                                     │
│                 │  (Port: 5001)   │                                     │
│                 └────────┬────────┘                                     │
│                          │                                              │
└──────────────────────────┼──────────────────────────────────────────────┘
                           │
                           │ HTTP + WebSocket
                           ▼
                  ┌─────────────────┐
                  │  Web Dashboard  │
                  │   (Tarayıcı)    │
                  │                 │
                  │  • RSSI Grafik  │
                  │  • RTT Grafik   │
                  │  • Gauge'lar    │
                  │  • Uyarılar     │
                  │  • İstatistik   │
                  └─────────────────┘
```

### Veri Akışı

1. **Client** → Wi-Fi taraması yaparak RSSI ölçer, RTT hesaplar
2. **AP** → Client'tan gelen veriyi alır, PC'ye iletir
3. **Backend** → Veriyi işler, tahmin yapar, CSV'ye yazar
4. **Frontend** → WebSocket ile anlık güncelleme alır

---

## Kullanılan Teknolojiler

### Donanım

| Bileşen | Açıklama |
|---------|----------|
| **LoPy4** | Pycom IoT geliştirme kartı (ESP32 tabanlı) |
| **Wi-Fi Anteni** | Dahili Wi-Fi anteni ile RSSI ölçümü |

### Yazılım

| Kategori | Teknoloji | Kullanım Alanı |
|----------|-----------|----------------|
| **Gömülü Sistem** | MicroPython | LoPy4 cihazlarda çalışan kod |
| **Backend** | Python 3.x | Sunucu tarafı işlemler |
| **Web Framework** | Flask | HTTP API ve sayfa sunumu |
| **Real-time** | Flask-SocketIO | WebSocket iletişimi |
| **ML Framework** | scikit-learn | Random Forest sınıflandırıcı |
| **Veri İşleme** | pandas, numpy | Veri analizi ve özellik çıkarma |
| **Model Kaydetme** | joblib | ML model serileştirme |
| **Frontend** | HTML5, CSS3, JS | Web arayüzü |
| **Grafik** | Chart.js 4.4.1 | Zaman serisi grafikleri |
| **Veri Depolama** | CSV | Ölçüm verisi saklama |

### İletişim Protokolleri

| Protokol | Port | Kullanım |
|----------|------|----------|
| **Wi-Fi 802.11** | - | Client-AP arası kablosuz bağlantı |
| **TCP Socket** | 12345 | Client → AP veri iletimi |
| **TCP Socket** | 12346 | AP → PC veri iletimi |
| **HTTP** | 5001 | Web API |
| **WebSocket** | 5001 | Gerçek zamanlı veri push |

---

## Proje Yapısı

```
V2/
├── ap/                              # LoPy4 Access Point
│   └── main.py                      # AP firmware (Wi-Fi AP + veri relay)
│
├── client/                          # LoPy4 Client
│   └── main.py                      # Client firmware (RSSI/RTT ölçümü)
│
├── pc/                              # PC Monitör Uygulaması
│   └── main.py                      # Komut satırı izleme aracı
│
├── web/                             # Web Dashboard
│   ├── __init__.py                  # Flask app factory
│   ├── app.py                       # Ana giriş noktası
│   ├── routes.py                    # HTTP endpoint'leri
│   ├── events.py                    # Socket.IO event handler'ları
│   ├── socket_client.py             # AP bağlantı yöneticisi
│   ├── data_manager.py              # Veri ve durum yönetimi
│   ├── templates/
│   │   ├── base.html                # Temel şablon
│   │   └── dashboard.html           # Dashboard arayüzü
│   └── static/
│       ├── css/
│       │   └── dashboard.css        # Stil dosyası (Dark Theme)
│       └── js/
│           ├── dashboard.js         # Ana JavaScript
│           ├── charts.js            # Chart.js konfigürasyonu
│           └── gauges.js            # Gauge göstergeleri
│
├── ml/                              # Machine Learning Modülü
│   ├── __init__.py
│   ├── predictor.py                 # Hibrit tahmin motoru
│   ├── rules.py                     # Kural tabanlı tahminleyici
│   ├── features.py                  # Özellik çıkarma (13 feature)
│   ├── train.py                     # Model eğitim betiği
│   └── model.pkl                    # Eğitilmiş Random Forest modeli
│
├── data/                            # Veri Dosyaları
│   └── rssi_data.csv                # Toplanan ölçüm verileri
│
├── boot.py                          # LoPy4 boot script
├── pymakr.conf                      # PyMakr IDE konfigürasyonu
└── README.md                        # Bu dosya
```

### Modül Açıklamaları

| Modül | Dosya Sayısı | Açıklama |
|-------|--------------|----------|
| **ap/** | 1 | Access Point olarak çalışan LoPy4 kodu |
| **client/** | 1 | RSSI/RTT ölçümü yapan LoPy4 kodu |
| **pc/** | 1 | Komut satırı tabanlı izleme aracı |
| **web/** | 10+ | Flask tabanlı web dashboard |
| **ml/** | 5 | Makine öğrenmesi tahmin sistemi |
| **data/** | 1 | CSV veri dosyası |

---

## Kurulum

### Gereksinimler

#### Donanım
- 2x LoPy4 geliştirme kartı (veya uyumlu Pycom cihazı)
- USB kabloları
- Bilgisayar (Windows/macOS/Linux)

#### Yazılım
- Python 3.8+
- PyMakr (VS Code veya Atom eklentisi)

### 1. Python Bağımlılıkları

```bash
# requirements.txt oluşturun ve yükleyin
pip install flask
pip install flask-socketio
pip install pandas
pip install numpy
pip install scikit-learn
pip install joblib
```

Veya tek satırda:

```bash
pip install flask flask-socketio pandas numpy scikit-learn joblib
```

### 2. LoPy4 Kurulumu

#### Access Point (AP) Cihazı

1. PyMakr ile `ap/` klasörünü LoPy4'e yükleyin
2. Cihaz otomatik olarak Wi-Fi AP modunda başlayacak
3. LED yeşil yanıyorsa hazır demektir

#### Client Cihazı

1. PyMakr ile `client/` klasörünü ikinci LoPy4'e yükleyin
2. Cihaz otomatik olarak AP'ye bağlanacak
3. LED mavi yanıyorsa ölçüm yapılıyor demektir

### 3. Ağ Yapılandırması

Varsayılan ayarlar:

| Parametre | Değer |
|-----------|-------|
| SSID | `LoPy4-Network` |
| Şifre | `lopy4pass123` |
| AP IP | `192.168.4.1` |
| Client Port | `12345` |
| PC Port | `12346` |
| Web Port | `5001` |

---

## Kullanım

### 1. LoPy4 Cihazlarını Başlatma

```
1. AP LoPy4'ü USB ile bağlayın → Otomatik başlar
2. Client LoPy4'ü USB ile bağlayın → AP'ye bağlanır
3. AP'nin LED'i yeşil, Client'ın LED'i mavi yanmalı
```

### 2. Web Dashboard'u Başlatma

```bash
# Proje dizinine gidin
cd V2/

# Web sunucuyu başlatın
python web/app.py
```

Çıktı:
```
[INFO] Starting Wi-Fi RSSI/RTT Monitor Server...
[INFO] AP Socket Client started
[INFO] Server running on http://localhost:5001
```

### 3. Dashboard'a Erişim

Tarayıcınızda açın: **http://localhost:5001**

### 4. Komut Satırı Monitörü (Opsiyonel)

```bash
python pc/main.py
```

Terminal'de gerçek zamanlı ölçümler görüntülenir.

### 5. ML Modeli Eğitimi (Opsiyonel)

Yeterli veri toplandıktan sonra:

```bash
python ml/train.py
```

Gereksinimler:
- Minimum 100 ölçüm
- Minimum 10 problem olayı (DISCONNECTED veya PACKET_LOST)

---

## Özellikler Detayı

### 1. Sinyal İzleme

#### RSSI (Received Signal Strength Indicator)
- **Birim**: dBm (desibel-miliwatt)
- **Aralık**: -100 dBm (çok zayıf) → 0 dBm (mükemmel)
- **Ölçüm Sıklığı**: 1 saniye

#### RTT (Round Trip Time)
- **Birim**: ms (milisaniye)
- **Hesaplama**: Gönderim ve alım arasındaki süre
- **Latency**: RTT / 2

#### Sinyal Kalitesi Sınıflandırması

| RSSI Değeri | Kalite | Skor |
|-------------|--------|------|
| ≥ -50 dBm | Mükemmel | 4 |
| -50 ile -60 dBm | İyi | 3 |
| -60 ile -70 dBm | Orta | 2 |
| -70 ile -80 dBm | Zayıf | 1 |
| < -80 dBm | Çok Zayıf | 0 |

### 2. Hibrit Tahmin Sistemi

Sistem iki katmanlı tahmin kullanır:

#### Kural Tabanlı Tahmin

Anlık değerlere göre uyarı üretir:

| Koşul | Uyarı Seviyesi |
|-------|----------------|
| RSSI < -85 dBm | CRITICAL |
| RSSI < -75 dBm | WARNING |
| RSSI < -60 dBm | CAUTION |
| RSSI trendi < -5 dBm/ölçüm | WARNING |
| RSSI trendi < -3 dBm/ölçüm | CAUTION |
| RTT > 200 ms | WARNING |
| RTT > 100 ms | CAUTION |

#### ML Tahmin (Random Forest)

13 özellik kullanarak kesinti olasılığı hesaplar:

**Özellikler:**
1. `rssi_mean` - Ortalama RSSI
2. `rssi_std` - RSSI standart sapması
3. `rssi_min` - Minimum RSSI
4. `rssi_max` - Maksimum RSSI
5. `rssi_trend` - RSSI eğilimi
6. `rssi_delta` - RSSI değişimi
7. `rtt_mean` - Ortalama RTT
8. `rtt_std` - RTT standart sapması
9. `rtt_min` - Minimum RTT
10. `rtt_max` - Maksimum RTT
11. `rtt_trend` - RTT eğilimi
12. `quality_mean` - Ortalama kalite
13. `quality_std` - Kalite standart sapması

**ML Olasılık Eşikleri:**

| Olasılık | Uyarı Seviyesi | Açıklama |
|----------|----------------|----------|
| ≥ 0.85 | CRITICAL | Bağlantı her an kopabilir |
| ≥ 0.70 | WARNING | Yüksek kopma riski |
| ≥ 0.50 | CAUTION | Stabilite düşüyor |
| ≥ 0.30 | INFO | Hafif dalgalanma |

### 3. Uyarı Sistemi

5 seviyeli uyarı sistemi:

| Seviye | Kod | Simge | Açıklama |
|--------|-----|-------|----------|
| 0 | NONE | - | Uyarı yok |
| 1 | INFO | (i) | Bilgilendirme |
| 2 | CAUTION | [!] | Dikkat |
| 3 | WARNING | [!!] | Uyarı |
| 4 | CRITICAL | [!!!] | Kritik |

### 4. Web Dashboard Bileşenleri

- **Header**: Bağlantı durumu badge'i, oturum bilgisi
- **RSSI Gauge**: Anlık sinyal gücü göstergesi
- **RTT Gauge**: Anlık gecikme göstergesi
- **Kalite Kartı**: Sinyal kalitesi skoru
- **RSSI Grafiği**: Son 300 ölçümün zaman serisi
- **RTT Grafiği**: Son 300 ölçümün zaman serisi
- **İstatistik Paneli**: Min, Max, Avg, Median, Std
- **Kalite Dağılımı**: Kalite seviyelerine göre dağılım
- **Uyarılar Listesi**: Son 50 uyarı
- **Sorunlar Paneli**: Paket kaybı ve kesinti istatistikleri
- **Tahmin Durumu**: ML model performans metrikleri

---

## API Referansı

### HTTP Endpoints

| Endpoint | Metod | Açıklama |
|----------|-------|----------|
| `/` | GET | Dashboard ana sayfası |
| `/api/stats` | GET | Güncel istatistikler (JSON) |
| `/api/status` | GET | Bağlantı durumu |
| `/api/history` | GET | RSSI/RTT geçmişi |
| `/api/warnings` | GET | Uyarı listesi |

### WebSocket Events (Socket.IO)

#### Sunucudan İstemciye

| Event | Veri | Açıklama |
|-------|------|----------|
| `connect` | - | Bağlantı kuruldu |
| `initial_data` | JSON | İlk veri seti |
| `new_measurement` | JSON | Yeni ölçüm verisi |
| `status_change` | JSON | Bağlantı durumu değişti |
| `warning` | JSON | Yeni uyarı |
| `stats_update` | JSON | İstatistik güncellendi |
| `packet_loss` | JSON | Paket kaybı tespit edildi |

#### İstemciden Sunucuya

| Event | Veri | Açıklama |
|-------|------|----------|
| `request_stats` | - | İstatistik talep et |
| `request_history` | - | Geçmiş talep et |
| `ping` | - | Bağlantı kontrolü |

### Örnek API Yanıtları

#### GET /api/stats

```json
{
  "rssi": {
    "min": -75,
    "max": -45,
    "avg": -58.5,
    "median": -57,
    "std": 8.2
  },
  "rtt": {
    "min": 5,
    "max": 150,
    "avg": 25.3,
    "median": 20,
    "std": 15.7
  },
  "quality_distribution": {
    "Mükemmel": 45,
    "İyi": 120,
    "Orta": 80,
    "Zayıf": 30,
    "Çok Zayıf": 5
  },
  "issues": {
    "packet_loss": 12,
    "packet_loss_rate": 0.043,
    "disconnects": 2,
    "total_downtime": 15.5,
    "avg_disconnect": 7.75
  }
}
```

#### GET /api/status

```json
{
  "connected": true,
  "last_rssi": -52,
  "last_rtt": 18,
  "last_quality": "Mükemmel",
  "session_duration": "00:15:32",
  "measurement_count": 280
}
```

---

## Konfigürasyon

### Ağ Ayarları

**Dosya:** `ap/main.py` ve `client/main.py`

```python
SSID = 'LoPy4-Network'        # Wi-Fi ağ adı
PASSWORD = 'lopy4pass123'      # Wi-Fi şifresi
AP_IP = '192.168.4.1'          # AP IP adresi
CLIENT_PORT = 12345            # Client bağlantı portu
PC_PORT = 12346                # PC bağlantı portu
```

### Web Sunucu Ayarları

**Dosya:** `web/app.py`

```python
# Ortam değişkenleri ile ayarlanabilir
AP_IP = os.environ.get('AP_IP', '192.168.4.1')
AP_PORT = int(os.environ.get('AP_PORT', '12346'))
WEB_PORT = 5001
```

### ML Model Parametreleri

**Dosya:** `ml/train.py`

```python
WINDOW_SIZE = 10              # Kayma penceresi boyutu
PREDICTION_HORIZON = 5        # Tahmin ufku

# Random Forest parametreleri
n_estimators = 100            # Ağaç sayısı
max_depth = 10                # Maksimum derinlik
min_samples_split = 5         # Minimum bölme örneği
min_samples_leaf = 2          # Yapraktaki minimum örnek
class_weight = 'balanced'     # Sınıf dengeleme
```

### Kural Tabanlı Eşikler

**Dosya:** `ml/rules.py`

```python
DEFAULT_THRESHOLDS = {
    'rssi_good': -50,              # İyi sinyal eşiği
    'rssi_warning': -60,           # Uyarı eşiği
    'rssi_critical': -75,          # Kritik eşik
    'rssi_danger': -85,            # Tehlike eşiği
    'rssi_trend_warning': -3,      # Trend uyarı (dBm/ölçüm)
    'rssi_trend_critical': -5,     # Trend kritik
    'rssi_std_warning': 5,         # Stabilite uyarısı
    'rtt_warning': 100,            # RTT uyarı (ms)
    'rtt_critical': 200,           # RTT kritik
    'latency_warning': 50,         # Latency uyarı
    'latency_critical': 100,       # Latency kritik
    'window_size': 5               # Analiz pencere boyutu
}
```

---

## Veri Formatı

### CSV Yapısı

**Dosya:** `data/rssi_data.csv`

| Kolon | Tip | Açıklama |
|-------|-----|----------|
| session_id | string | Oturum kimliği (YYYYMMDD_HHMMSS) |
| timestamp | string | ISO 8601 zaman damgası |
| unix_time | float | Unix timestamp |
| measurement_id | int | Ölçüm numarası |
| event_type | string | Olay tipi |
| rssi | int | Sinyal gücü (dBm) |
| rtt | int | Round Trip Time (ms) |
| latency | int | Tek yön gecikme (ms) |
| quality | string | Kalite etiketi |
| quality_score | int | Kalite skoru (0-4) |
| disconnect_duration | float | Kesinti süresi (sn) |

### Event Tipleri

| Tip | Açıklama |
|-----|----------|
| DATA | Normal ölçüm |
| CONNECTED | Bağlantı kuruldu |
| DISCONNECTED | Bağlantı koptu |
| PACKET_LOST | Paket kaybı tespit edildi |

### Örnek CSV Satırları

```csv
session_id,timestamp,unix_time,measurement_id,event_type,rssi,rtt,latency,quality,quality_score,disconnect_duration
20260115_143022,2026-01-15T14:30:23.338,1768481423.338,1,DATA,-52,18,9,Mükemmel,4,
20260115_143022,2026-01-15T14:30:24.342,1768481424.342,2,DATA,-54,20,10,Mükemmel,4,
20260115_143022,2026-01-15T14:30:25.300,1768481425.300,3,DATA,-58,22,11,İyi,3,
20260115_143022,2026-01-15T14:30:30.100,1768481430.100,,DISCONNECTED,,,,,5.2
```

---

## LED Göstergeleri

### LoPy4 Access Point

| Renk | Durum |
|------|-------|
| Yeşil | Normal çalışma |
| Turuncu | Client'tan veri yok (5 sn) |

### LoPy4 Client

| Renk | Durum |
|------|-------|
| Kırmızı | AP'ye bağlanıyor |
| Mavi | Ölçüm yapılıyor |
| Sarı | Ölçüm hatası |

---

## Sorun Giderme

### Sık Karşılaşılan Sorunlar

| Sorun | Çözüm |
|-------|-------|
| Client AP'ye bağlanamıyor | SSID ve şifreyi kontrol edin |
| Web dashboard açılmıyor | Port 5001'in boş olduğundan emin olun |
| Veri gelmiyor | AP IP adresini kontrol edin (192.168.4.1) |
| ML modeli yüklenmiyor | `ml/model.pkl` dosyasının var olduğundan emin olun |
| Paket kaybı yüksek | Cihazlar arasındaki mesafeyi azaltın |

### Log Kontrolü

```bash
# Web sunucu logları terminalde görüntülenir
python web/app.py

# Detaylı log için
export FLASK_DEBUG=1
python web/app.py
```

---

## Performans Metrikleri

### Tipik Değerler

| Metrik | İyi | Orta | Kötü |
|--------|-----|------|------|
| RSSI | > -60 dBm | -60 ile -75 dBm | < -75 dBm |
| RTT | < 50 ms | 50-100 ms | > 100 ms |
| Paket Kaybı | < 1% | 1-5% | > 5% |
| Stabilite (Std) | < 3 dBm | 3-8 dBm | > 8 dBm |

---

## Lisans

Bu proje **Bursa Teknik Üniversitesi - BM-5 Kablosuz Ağlar** dersi kapsamında eğitim amaçlı geliştirilmiştir.

---

## İletişim

Sorularınız için proje ekibi ile iletişime geçebilirsiniz.

---

*Son Güncelleme: Ocak 2026*
