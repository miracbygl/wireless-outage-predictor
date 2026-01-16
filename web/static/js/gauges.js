// SVG Arc Gauge Component
// RSSI ve RTT icin gorsel gostergeler

class ArcGauge {
    constructor(container, options = {}) {
        this.container = typeof container === 'string'
            ? document.querySelector(container)
            : container;

        if (!this.container) {
            console.error('Gauge container not found');
            return;
        }

        // Varsayilan ayarlar
        this.options = {
            min: options.min || 0,
            max: options.max || 100,
            value: options.value || 0,
            unit: options.unit || '',
            label: options.label || '',
            colorStops: options.colorStops || [
                { offset: 0, color: '#f85149' },
                { offset: 0.5, color: '#d29922' },
                { offset: 1, color: '#3fb950' }
            ],
            arcWidth: options.arcWidth || 12,
            startAngle: options.startAngle || -135,
            endAngle: options.endAngle || 135,
            animated: options.animated !== false
        };

        this.currentValue = this.options.min;
        this.targetValue = this.options.value;

        this.init();
    }

    init() {
        // SVG olustur
        const width = 180;
        const height = 140;  // Increased from 100 to show full arc
        const cx = width / 2;
        const cy = 85;
        const radius = 70;

        this.svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        this.svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
        this.svg.setAttribute('class', 'arc-gauge');

        // Gradient tanimla
        const gradientId = 'gauge-gradient-' + Math.random().toString(36).substr(2, 9);
        const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
        const gradient = document.createElementNS('http://www.w3.org/2000/svg', 'linearGradient');
        gradient.setAttribute('id', gradientId);
        gradient.setAttribute('x1', '0%');
        gradient.setAttribute('y1', '0%');
        gradient.setAttribute('x2', '100%');
        gradient.setAttribute('y2', '0%');

        this.options.colorStops.forEach(stop => {
            const stopEl = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
            stopEl.setAttribute('offset', `${stop.offset * 100}%`);
            stopEl.setAttribute('stop-color', stop.color);
            gradient.appendChild(stopEl);
        });

        defs.appendChild(gradient);
        this.svg.appendChild(defs);

        // Arka plan arc
        const bgArc = this.createArc(cx, cy, radius, this.options.startAngle, this.options.endAngle);
        bgArc.setAttribute('fill', 'none');
        bgArc.setAttribute('stroke', '#21262d');
        bgArc.setAttribute('stroke-width', this.options.arcWidth);
        bgArc.setAttribute('stroke-linecap', 'round');
        this.svg.appendChild(bgArc);

        // Deger arc
        this.valueArc = this.createArc(cx, cy, radius, this.options.startAngle, this.options.startAngle);
        this.valueArc.setAttribute('fill', 'none');
        this.valueArc.setAttribute('stroke', `url(#${gradientId})`);
        this.valueArc.setAttribute('stroke-width', this.options.arcWidth);
        this.valueArc.setAttribute('stroke-linecap', 'round');
        this.valueArc.style.transition = this.options.animated ? 'all 0.3s ease' : 'none';
        this.svg.appendChild(this.valueArc);

        // Tick isaretleri
        this.addTicks(cx, cy, radius);

        this.container.appendChild(this.svg);

        // Baslangic degeri
        this.setValue(this.options.value, false);
    }

    createArc(cx, cy, radius, startAngle, endAngle) {
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        const d = this.describeArc(cx, cy, radius, startAngle, endAngle);
        path.setAttribute('d', d);
        return path;
    }

    describeArc(cx, cy, radius, startAngle, endAngle) {
        const start = this.polarToCartesian(cx, cy, radius, endAngle);
        const end = this.polarToCartesian(cx, cy, radius, startAngle);
        const largeArcFlag = endAngle - startAngle <= 180 ? '0' : '1';

        return [
            'M', start.x, start.y,
            'A', radius, radius, 0, largeArcFlag, 0, end.x, end.y
        ].join(' ');
    }

    polarToCartesian(cx, cy, radius, angleDegrees) {
        const angleRadians = (angleDegrees - 90) * Math.PI / 180;
        return {
            x: cx + (radius * Math.cos(angleRadians)),
            y: cy + (radius * Math.sin(angleRadians))
        };
    }

    addTicks(cx, cy, radius) {
        const tickCount = 5;
        const angleRange = this.options.endAngle - this.options.startAngle;
        const tickRadius = radius + 8;

        for (let i = 0; i <= tickCount; i++) {
            const angle = this.options.startAngle + (angleRange * i / tickCount);
            const pos = this.polarToCartesian(cx, cy, tickRadius, angle);

            const tick = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            tick.setAttribute('cx', pos.x);
            tick.setAttribute('cy', pos.y);
            tick.setAttribute('r', 2);
            tick.setAttribute('fill', '#6e7681');
            this.svg.appendChild(tick);
        }
    }

    setValue(value, animate = true) {
        this.targetValue = Math.max(this.options.min, Math.min(this.options.max, value));

        const percentage = (this.targetValue - this.options.min) / (this.options.max - this.options.min);
        const angleRange = this.options.endAngle - this.options.startAngle;
        const targetAngle = this.options.startAngle + (angleRange * percentage);

        const cx = 90;
        const cy = 85;
        const radius = 70;

        const d = this.describeArc(cx, cy, radius, this.options.startAngle, targetAngle);
        this.valueArc.setAttribute('d', d);

        // Degere gore renk hesapla (gradient yerine tek renk)
        const color = this.getColorForPercentage(percentage);
        this.valueArc.setAttribute('stroke', color);

        this.currentValue = this.targetValue;
    }

    getColorForPercentage(percentage) {
        // colorStops'tan interpolasyon yap
        const stops = this.options.colorStops;

        // Percentage'a en yakin iki stop'u bul
        let lowerStop = stops[0];
        let upperStop = stops[stops.length - 1];

        for (let i = 0; i < stops.length - 1; i++) {
            if (percentage >= stops[i].offset && percentage <= stops[i + 1].offset) {
                lowerStop = stops[i];
                upperStop = stops[i + 1];
                break;
            }
        }

        // İki renk arasinda interpolasyon
        const range = upperStop.offset - lowerStop.offset;
        const localPercentage = range > 0 ? (percentage - lowerStop.offset) / range : 0;

        return this.interpolateColor(lowerStop.color, upperStop.color, localPercentage);
    }

    interpolateColor(color1, color2, factor) {
        // Hex renkleri RGB'ye cevir
        const r1 = parseInt(color1.slice(1, 3), 16);
        const g1 = parseInt(color1.slice(3, 5), 16);
        const b1 = parseInt(color1.slice(5, 7), 16);

        const r2 = parseInt(color2.slice(1, 3), 16);
        const g2 = parseInt(color2.slice(3, 5), 16);
        const b2 = parseInt(color2.slice(5, 7), 16);

        // Interpolasyon
        const r = Math.round(r1 + (r2 - r1) * factor);
        const g = Math.round(g1 + (g2 - g1) * factor);
        const b = Math.round(b1 + (b2 - b1) * factor);

        // RGB'yi hex'e cevir
        return '#' + [r, g, b].map(x => x.toString(16).padStart(2, '0')).join('');
    }

    getValue() {
        return this.currentValue;
    }
}


// RSSI Gauge - ozel renk skalasi (ters: dusuk deger kotu)
class RSSIGauge extends ArcGauge {
    constructor(container, options = {}) {
        super(container, {
            min: -100,
            max: -20,
            unit: 'dBm',
            label: 'RSSI',
            // RSSI icin: yesil (iyi, -20) -> kirmizi (kotu, -100)
            colorStops: [
                { offset: 0, color: '#f85149' },   // -100 dBm (kotu)
                { offset: 0.3, color: '#f0883e' }, // -76 dBm
                { offset: 0.5, color: '#d29922' }, // -60 dBm
                { offset: 0.75, color: '#7ee787' }, // -40 dBm
                { offset: 1, color: '#3fb950' }    // -20 dBm (iyi)
            ],
            ...options
        });
    }
}


// RTT Gauge - ozel renk skalasi (dusuk deger iyi)
class RTTGauge extends ArcGauge {
    constructor(container, options = {}) {
        super(container, {
            min: 0,
            max: 100,  // Max 100ms - tipik WiFi RTT icin daha uygun
            unit: 'ms',
            label: 'RTT',
            // RTT icin: yesil (iyi, 0) -> kirmizi (kotu, 100)
            colorStops: [
                { offset: 0, color: '#3fb950' },   // 0 ms (iyi)
                { offset: 0.3, color: '#7ee787' }, // 30 ms
                { offset: 0.5, color: '#d29922' },  // 50 ms
                { offset: 0.7, color: '#f0883e' }, // 70 ms
                { offset: 1, color: '#f85149' }    // 100 ms (kotu)
            ],
            ...options
        });
    }
}


// Sinyal Guc Barlari
class SignalBars {
    constructor(container, options = {}) {
        this.container = typeof container === 'string'
            ? document.querySelector(container)
            : container;

        this.barCount = options.barCount || 5;
        this.activeLevel = 0;

        this.init();
    }

    init() {
        this.container.innerHTML = '';
        this.container.classList.add('signal-bars');

        this.bars = [];
        for (let i = 0; i < this.barCount; i++) {
            const bar = document.createElement('div');
            bar.className = 'bar';
            bar.style.height = `${8 + (i * 6)}px`;
            this.container.appendChild(bar);
            this.bars.push(bar);
        }
    }

    setLevel(level) {
        this.activeLevel = Math.max(0, Math.min(this.barCount, level));

        // Tum level class'larini kaldir
        for (let i = 0; i <= this.barCount; i++) {
            this.container.classList.remove(`level-${i}`);
        }

        // Yeni level class'i ekle
        this.container.classList.add(`level-${this.activeLevel}`);
    }

    setFromRSSI(rssi) {
        let level;
        if (rssi >= -50) level = 5;
        else if (rssi >= -60) level = 4;
        else if (rssi >= -70) level = 3;
        else if (rssi >= -80) level = 2;
        else if (rssi >= -90) level = 1;
        else level = 0;

        this.setLevel(level);
        return level;
    }
}


// Kalite Skoru Gostergesi
class QualityMeter {
    constructor(container) {
        this.container = typeof container === 'string'
            ? document.querySelector(container)
            : container;

        this.score = 0;
        this.quality = '';
    }

    setQuality(quality, score) {
        this.quality = quality;
        this.score = score;

        const textEl = this.container.querySelector('.quality-text');
        const scoreEl = this.container.querySelector('.quality-score');
        const fillEl = this.container.querySelector('.quality-fill');

        if (textEl) textEl.textContent = quality || '-';
        if (scoreEl) scoreEl.textContent = score !== null ? score : '-';

        if (fillEl) {
            const percentage = score !== null ? (score / 4) * 100 : 0;
            fillEl.style.width = `${percentage}%`;
        }

        // Renk ayarla
        const colors = {
            'Mükemmel': 'var(--color-excellent)',
            'İyi': 'var(--color-good)',
            'Orta': 'var(--color-medium)',
            'Zayıf': 'var(--color-weak)',
            'Çok Zayıf': 'var(--color-critical)'
        };

        if (textEl) {
            textEl.style.color = colors[quality] || 'var(--text-primary)';
        }
    }
}


// Export
window.ArcGauge = ArcGauge;
window.RSSIGauge = RSSIGauge;
window.RTTGauge = RTTGauge;
window.SignalBars = SignalBars;
window.QualityMeter = QualityMeter;
