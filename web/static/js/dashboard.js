// Dashboard Ana Controller
// SocketIO baglantisi ve UI guncellemeleri

class Dashboard {
    constructor() {
        // SocketIO
        this.socket = null;
        this.connected = false;

        // Gauge'lar
        this.rssiGauge = null;
        this.rttGauge = null;
        this.signalBars = null;
        this.qualityMeter = null;

        // Chart'lar
        this.rssiChart = null;
        this.rttChart = null;
        this.qualityChart = null;

        // Istatistik sekme
        this.currentStatsTab = 'rssi';

        // Baslangic zamani
        this.startTime = Date.now();

        // Audio Context (tek seferlik olustur)
        this.audioContext = null;
        this.audioEnabled = false;

        this.init();
    }

    init() {
        // SocketIO baglantisi
        this.initSocketIO();

        // UI bilesenlerini olustur
        this.initGauges();
        this.initCharts();
        this.initEventListeners();

        // Oturum sure sayaci
        this.startDurationTimer();

        console.log('[Dashboard] Baslatildi');
    }

    initSocketIO() {
        this.socket = io({
            transports: ['websocket', 'polling'],
            reconnection: true,
            reconnectionAttempts: Infinity,
            reconnectionDelay: 1000
        });

        // Baglanti eventleri
        this.socket.on('connect', () => {
            console.log('[SocketIO] Baglandi');
            this.connected = true;
            this.updateConnectionBadge(true, 'Server Bağlı');
        });

        this.socket.on('disconnect', () => {
            console.log('[SocketIO] Baglanti koptu');
            this.connected = false;
            this.updateConnectionBadge(false, 'Bağlantı Kesildi');
        });

        // Veri eventleri
        this.socket.on('initial_data', (data) => {
            console.log('[SocketIO] Baslangic verisi alindi');
            this.handleInitialData(data);
        });

        this.socket.on('new_measurement', (data) => {
            this.handleNewMeasurement(data);
        });

        this.socket.on('status_change', (data) => {
            this.handleStatusChange(data);
        });

        this.socket.on('warning', (data) => {
            this.handleWarning(data);
        });

        this.socket.on('stats_update', (data) => {
            this.handleStatsUpdate(data);
        });

        this.socket.on('pong', () => {
            // Ping yaniti
        });
    }

    initGauges() {
        // RSSI Gauge
        const rssiContainer = document.getElementById('rssi-gauge');
        if (rssiContainer) {
            this.rssiGauge = new RSSIGauge(rssiContainer);
        }

        // RTT Gauge
        const rttContainer = document.getElementById('rtt-gauge');
        if (rttContainer) {
            this.rttGauge = new RTTGauge(rttContainer);
        }

        // Sinyal barlari
        const signalContainer = document.getElementById('signal-bars');
        if (signalContainer) {
            this.signalBars = new SignalBars(signalContainer);
        }

        // Kalite gostergesi
        const qualityContainer = document.querySelector('.quality-display');
        if (qualityContainer) {
            this.qualityMeter = new QualityMeter(qualityContainer);
        }
    }

    initCharts() {
        // RSSI Chart
        this.rssiChart = createRSSIChart('rssi-chart');
        console.log('[Dashboard] RSSI chart:', this.rssiChart ? 'OK' : 'HATA');

        // RTT Chart
        this.rttChart = createRTTChart('rtt-chart');
        console.log('[Dashboard] RTT chart:', this.rttChart ? 'OK' : 'HATA');

        // Kalite Dagilimi Chart
        this.qualityChart = createQualityChart('quality-chart');
        console.log('[Dashboard] Quality chart:', this.qualityChart ? 'OK' : 'HATA');
    }

    initEventListeners() {
        // Istatistik sekme degisimi
        const tabs = document.querySelectorAll('.stats-tabs .tab');
        tabs.forEach(tab => {
            tab.addEventListener('click', (e) => {
                this.switchStatsTab(e.target.dataset.tab);
            });
        });

        // Ilk kullanici etkilesiminde AudioContext'i baslat
        const enableAudio = () => {
            this.initAudio();
            // Bir kez calistiktan sonra listener'i kaldir
            document.removeEventListener('click', enableAudio);
            document.removeEventListener('keydown', enableAudio);
        };
        document.addEventListener('click', enableAudio);
        document.addEventListener('keydown', enableAudio);
    }

    startDurationTimer() {
        setInterval(() => {
            this.updateDuration();
        }, 1000);
    }

    // --- Veri Isleyicileri ---

    handleInitialData(data) {
        if (!data) return;

        // Guncel degerleri guncelle
        if (data.current) {
            this.updateCurrentValues(data.current);
        }

        // Grafik gecmisini yukle
        if (data.chart_data) {
            if (data.chart_data.rssi) {
                console.log('[Dashboard] RSSI gecmisi yukleniyor:', data.chart_data.rssi.length, 'nokta');
                updateChartBulk(this.rssiChart, data.chart_data.rssi);
            }
            if (data.chart_data.rtt) {
                console.log('[Dashboard] RTT gecmisi yukleniyor:', data.chart_data.rtt.length, 'nokta');
                console.log('[Dashboard] RTT ornek veri:', data.chart_data.rtt.slice(0, 3));
                // RTT degerlerini pozitife cevir
                const rttData = data.chart_data.rtt.map(item => ({
                    time: item.time,
                    value: Math.abs(item.value)
                }));
                updateChartBulk(this.rttChart, rttData);
            }
        }

        // Istatistikleri guncelle
        if (data.stats) {
            this.updateStatsTable(data.stats);
        }

        // Kalite dagilimi
        if (data.quality_distribution) {
            updateQualityChart(this.qualityChart, data.quality_distribution);
        }

        // Baglanti sorunlari
        if (data.issues) {
            this.updateIssues(data.issues);
        }

        // Uyarilar
        if (data.warnings) {
            this.renderWarnings(data.warnings);
        }

        // Uyari sayilari
        if (data.warning_counts) {
            this.updateWarningCounts(data.warning_counts);
        }

        // Predictor durumu
        if (data.predictor) {
            this.updatePredictorStatus(data.predictor);
        }

        // Baglanti durumu
        if (data.connection_status) {
            const isConnected = data.connection_status === 'CONNECTED';
            this.updateConnectionBadge(isConnected,
                isConnected ? 'AP Bağlı' : 'AP Bağlantısı Yok');
        }

        // Olcum sayisi
        if (data.current && data.current.count) {
            document.getElementById('measurement-count').textContent = data.current.count;
        }
    }

    handleNewMeasurement(data) {
        if (!data) return;

        console.log('[Dashboard] Yeni olcum:', data.rssi, 'dBm,', data.rtt, 'ms');

        // Guncel degerleri guncelle
        this.updateCurrentValues({
            rssi: data.rssi,
            rtt: data.rtt,
            latency: data.latency,
            quality: data.quality,
            count: data.count
        });

        // Grafiklere ekle
        const timeLabel = this.formatTime(data.timestamp);

        // RSSI grafigi
        if (this.rssiChart && data.rssi !== null && data.rssi !== undefined) {
            addChartData(this.rssiChart, timeLabel, data.rssi);
        }

        // RTT grafigi - null/undefined kontrolu ve pozitif deger garantisi
        if (this.rttChart && data.rtt !== null && data.rtt !== undefined) {
            const rttValue = Math.abs(data.rtt); // RTT her zaman pozitif olmali
            addChartData(this.rttChart, timeLabel, rttValue);
            console.log('[Dashboard] RTT grafige eklendi:', rttValue, 'ms, label:', timeLabel);
        } else {
            console.warn('[Dashboard] RTT grafik ATLANDI - chart:', !!this.rttChart, 'rtt:', data.rtt);
        }

        // Olcum sayisi
        document.getElementById('measurement-count').textContent = data.count;

        // Uyari varsa
        if (data.warning) {
            this.handleWarning(data.warning);
        }
    }

    handleStatusChange(data) {
        if (!data) return;

        const isConnected = data.status === 'CONNECTED';
        this.updateConnectionBadge(isConnected,
            isConnected ? 'AP Bagli' : 'AP Baglantisi Yok');

        // Kopma durumunda
        if (!isConnected) {
            // Gauge'lari sifirla
            if (this.rssiGauge) this.rssiGauge.setValue(-100);
            if (this.rttGauge) this.rttGauge.setValue(0);
            if (this.signalBars) this.signalBars.setLevel(0);

            // Guncel deger alanlarini temizle
            document.getElementById('rssi-value').textContent = '-- dBm';
            document.getElementById('rtt-value').textContent = '-- ms';
            document.getElementById('latency-value').textContent = '--';
        }

        // Kopma sayisi guncelle
        if (data.disconnect_count !== undefined) {
            const el = document.getElementById('disconnect-count');
            if (el) el.textContent = data.disconnect_count;
        }
    }

    handleWarning(data) {
        if (!data) return;

        // Listeye ekle
        this.addWarningToList(data);

        // Uyari gostergesi ve ses
        this.showWarningIndicator(data.level);
        this.playWarningSound(data.level);

        // Sayaclari guncelle (eger mesajlar varsa)
        // Not: Sayaclar stats_update ile guncellenecek
    }

    handleStatsUpdate(data) {
        if (!data) return;

        if (data.stats) {
            this.updateStatsTable(data.stats);
        }

        if (data.quality_distribution) {
            updateQualityChart(this.qualityChart, data.quality_distribution);
        }

        if (data.issues) {
            this.updateIssues(data.issues);
        }

        if (data.warning_counts) {
            this.updateWarningCounts(data.warning_counts);
        }

        if (data.predictor) {
            this.updatePredictorStatus(data.predictor);
        }
    }

    // --- UI Guncelleyicileri ---

    updateCurrentValues(data) {
        // RSSI
        if (data.rssi !== null && data.rssi !== undefined) {
            document.getElementById('rssi-value').textContent = `${data.rssi} dBm`;
            if (this.rssiGauge) this.rssiGauge.setValue(data.rssi);
            if (this.signalBars) this.signalBars.setFromRSSI(data.rssi);
        }

        // RTT (her zaman pozitif)
        if (data.rtt !== null && data.rtt !== undefined) {
            const rttValue = Math.abs(data.rtt);
            document.getElementById('rtt-value').textContent = `${rttValue} ms`;
            if (this.rttGauge) this.rttGauge.setValue(rttValue);
        }

        // Latency (her zaman pozitif)
        if (data.latency !== null && data.latency !== undefined) {
            const latencyValue = Math.abs(data.latency);
            document.getElementById('latency-value').textContent = `~${latencyValue}ms`;
        }

        // Kalite
        if (data.quality) {
            const score = this.getQualityScore(data.quality);
            if (this.qualityMeter) {
                this.qualityMeter.setQuality(data.quality, score);
            }
        }
    }

    updateConnectionBadge(connected, text) {
        const badge = document.getElementById('connection-badge');
        if (!badge) return;

        badge.classList.remove('connected', 'disconnected');
        badge.classList.add(connected ? 'connected' : 'disconnected');

        const textEl = badge.querySelector('span:last-child');
        if (textEl) textEl.textContent = text;
    }

    updateDuration() {
        const el = document.getElementById('session-duration');
        if (!el) return;

        // Server'dan gelen sure yerine lokal hesapla
        const duration = Math.floor((Date.now() - this.startTime) / 1000);
        const hours = Math.floor(duration / 3600);
        const minutes = Math.floor((duration % 3600) / 60);
        const seconds = duration % 60;

        if (hours > 0) {
            el.textContent = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
        } else {
            el.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
        }
    }

    updateStatsTable(stats) {
        const currentStats = stats[this.currentStatsTab];
        if (!currentStats) return;

        const unit = this.getStatUnit();

        const setElement = (id, value, addUnit = true) => {
            const el = document.getElementById(id);
            if (el) el.textContent = addUnit ? `${value}${unit}` : value;
        };

        setElement('stat-min', currentStats.min || 0);
        setElement('stat-max', currentStats.max || 0);
        setElement('stat-avg', currentStats.avg || 0);
        setElement('stat-median', currentStats.median || 0);
        setElement('stat-std', currentStats.std || 0, false);
    }

    switchStatsTab(tab) {
        this.currentStatsTab = tab;

        // Tab butonlarini guncelle
        document.querySelectorAll('.stats-tabs .tab').forEach(t => {
            t.classList.toggle('active', t.dataset.tab === tab);
        });

        // Tabloyu guncelle
        this.socket.emit('request_stats');
    }

    getStatUnit() {
        switch (this.currentStatsTab) {
            case 'rssi': return ' dBm';
            case 'rtt': return ' ms';
            case 'latency': return ' ms';
            default: return '';
        }
    }

    updateIssues(issues) {
        const setElement = (id, value) => {
            const el = document.getElementById(id);
            if (el) el.textContent = value;
        };

        setElement('packet-loss', issues.packet_loss || 0);
        setElement('packet-loss-rate', `%${issues.packet_loss_rate || 0}`);
        setElement('disconnect-count', issues.disconnects || 0);
        setElement('total-downtime', `${issues.total_downtime || 0}s`);
        setElement('avg-disconnect', `${issues.avg_disconnect || 0}s`);
    }

    updateWarningCounts(counts) {
        const setCount = (id, value) => {
            const el = document.getElementById(id);
            if (el) el.textContent = value || 0;
        };

        setCount('wb-bilgi', counts['BILGI']);
        setCount('wb-dikkat', counts['DIKKAT']);
        setCount('wb-uyari', counts['UYARI']);
        setCount('wb-kritik', counts['KRITIK']);

        // Badge
        const total = (counts['BILGI'] || 0) + (counts['DIKKAT'] || 0) + (counts['UYARI'] || 0) + (counts['KRITIK'] || 0);
        const badge = document.getElementById('warning-count');
        if (badge) badge.textContent = total;
    }

    updatePredictorStatus(predictor) {
        const modeEl = document.getElementById('predictor-mode');
        const totalEl = document.getElementById('pred-total');
        const warningsEl = document.getElementById('pred-warnings');

        if (modeEl) modeEl.textContent = predictor.mode || 'Bilinmiyor';
        if (totalEl) totalEl.textContent = predictor.total_predictions || 0;
        if (warningsEl) warningsEl.textContent = predictor.warnings_given || 0;
    }

    addWarningToList(warning) {
        const list = document.getElementById('warnings-list');
        if (!list) return;

        // "Uyari yok" mesajini kaldir
        const noWarnings = list.querySelector('.no-warnings');
        if (noWarnings) noWarnings.remove();

        // Uyari elementi olustur
        const item = document.createElement('div');
        item.className = `warning-item level-${warning.level}`;

        const time = this.formatTime(warning.timestamp);
        const messages = Array.isArray(warning.messages)
            ? warning.messages.join(', ')
            : warning.messages;

        item.innerHTML = `
            <span class="warning-time">${time}</span>
            <span class="warning-text">${messages}</span>
        `;

        // Basa ekle
        list.insertBefore(item, list.firstChild);

        // Maksimum 50 uyari
        while (list.children.length > 50) {
            list.removeChild(list.lastChild);
        }
    }

    renderWarnings(warnings) {
        const list = document.getElementById('warnings-list');
        if (!list) return;

        if (!warnings || warnings.length === 0) {
            list.innerHTML = '<div class="no-warnings">Henüz uyarı yok</div>';
            return;
        }

        list.innerHTML = '';
        warnings.forEach(w => this.addWarningToList(w));
    }

    // --- Uyari Gostergesi ve Ses ---

    showWarningIndicator(level) {
        const indicator = document.getElementById('warning-indicator');
        if (!indicator) return;

        // Onceki timeout'u temizle
        if (this.warningTimeout) {
            clearTimeout(this.warningTimeout);
        }

        // Seviyeye gore class ayarla
        indicator.className = 'warning-indicator level-' + level;
        indicator.style.display = 'block';

        // 3 saniye sonra gizle
        this.warningTimeout = setTimeout(() => {
            indicator.style.display = 'none';
        }, 3000);
    }

    initAudio() {
        // Kullanici etkilesimi ile AudioContext'i baslat
        if (this.audioContext) return;

        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            this.audioEnabled = true;
            console.log('[Dashboard] AudioContext baslatildi');
        } catch (e) {
            console.warn('[Dashboard] AudioContext olusturulamadi:', e);
        }
    }

    playWarningSound(level) {
        // AudioContext yoksa olustur
        if (!this.audioContext) {
            this.initAudio();
        }

        if (!this.audioContext) {
            console.warn('[Dashboard] Ses calinamadi - AudioContext yok');
            return;
        }

        // Suspended durumunda ise resume et
        if (this.audioContext.state === 'suspended') {
            this.audioContext.resume().then(() => {
                this._playBeeps(level);
            });
        } else {
            this._playBeeps(level);
        }
    }

    _playBeeps(level) {
        try {
            const ctx = this.audioContext;

            // Seviyeye gore ayarlar
            const config = {
                2: { freq: 440, beeps: 2, duration: 0.15 },   // DIKKAT: 2 bip
                3: { freq: 600, beeps: 3, duration: 0.12 },   // UYARI: 3 bip
                4: { freq: 800, beeps: 4, duration: 0.10 }    // KRITIK: 4 bip
            };
            const settings = config[level] || config[2];

            // Her bip icin oscillator olustur
            for (let i = 0; i < settings.beeps; i++) {
                const oscillator = ctx.createOscillator();
                const gainNode = ctx.createGain();

                oscillator.connect(gainNode);
                gainNode.connect(ctx.destination);

                oscillator.frequency.value = settings.freq;
                oscillator.type = 'square'; // Daha sert, alarm benzeri ses

                const startTime = ctx.currentTime + (i * 0.25); // Her bip 250ms arayla
                const endTime = startTime + settings.duration;

                // Ani basla, ani bitir (zonk sesi icin)
                gainNode.gain.setValueAtTime(0, startTime);
                gainNode.gain.linearRampToValueAtTime(0.4, startTime + 0.01);
                gainNode.gain.setValueAtTime(0.4, endTime - 0.01);
                gainNode.gain.linearRampToValueAtTime(0, endTime);

                oscillator.start(startTime);
                oscillator.stop(endTime);
            }
        } catch (e) {
            console.warn('[Dashboard] Ses calinamadi:', e);
        }
    }

    // --- Yardimci Fonksiyonlar ---

    formatTime(isoString) {
        if (!isoString) return '';
        try {
            const date = new Date(isoString);
            return date.toLocaleTimeString('tr-TR', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        } catch (e) {
            return isoString.split('T')[1]?.split('.')[0] || '';
        }
    }

    getQualityScore(quality) {
        const scores = {
            'Mükemmel': 4,
            'İyi': 3,
            'Orta': 2,
            'Zayıf': 1,
            'Çok Zayıf': 0
        };
        return scores[quality] !== undefined ? scores[quality] : null;
    }
}


// Sayfa yuklendiginde baslat
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new Dashboard();
});
