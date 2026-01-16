// Chart.js Konfigurasyonlari
// RSSI ve RTT zaman serisi grafikleri

// Ortak varsayilan ayarlar
Chart.defaults.color = '#8b949e';
Chart.defaults.borderColor = '#30363d';
Chart.defaults.font.family = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";


// RSSI Chart olustur
function createRSSIChart(canvasId) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) {
        console.error('RSSI chart canvas not found:', canvasId);
        return null;
    }

    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'RSSI (dBm)',
                data: [],
                borderColor: '#58a6ff',
                backgroundColor: 'rgba(88, 166, 255, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.3,
                pointRadius: 0,
                pointHoverRadius: 4,
                pointHoverBackgroundColor: '#58a6ff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
                duration: 300
            },
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: '#161b22',
                    borderColor: '#30363d',
                    borderWidth: 1,
                    titleColor: '#c9d1d9',
                    bodyColor: '#8b949e',
                    padding: 10,
                    displayColors: false,
                    callbacks: {
                        title: function(context) {
                            return context[0].label;
                        },
                        label: function(context) {
                            return `RSSI: ${context.parsed.y} dBm`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    display: true,
                    grid: {
                        display: false
                    },
                    ticks: {
                        maxTicksLimit: 6,
                        maxRotation: 0,
                        font: {
                            size: 10
                        }
                    }
                },
                y: {
                    display: true,
                    min: -100,
                    max: 0,
                    grid: {
                        color: '#21262d'
                    },
                    ticks: {
                        stepSize: 20,
                        font: {
                            size: 10
                        },
                        callback: function(value) {
                            return value + ' dBm';
                        }
                    }
                }
            }
        }
    });
}


// RTT Chart olustur
function createRTTChart(canvasId) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) {
        console.error('RTT chart canvas not found:', canvasId);
        return null;
    }

    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'RTT (ms)',
                data: [],
                borderColor: '#3fb950',
                backgroundColor: 'rgba(63, 185, 80, 0.15)',
                borderWidth: 2,
                fill: true,
                tension: 0.3,
                pointRadius: 2,
                pointBackgroundColor: '#3fb950',
                pointHoverRadius: 5,
                pointHoverBackgroundColor: '#3fb950'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
                duration: 300
            },
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: '#161b22',
                    borderColor: '#30363d',
                    borderWidth: 1,
                    titleColor: '#c9d1d9',
                    bodyColor: '#8b949e',
                    padding: 10,
                    displayColors: false,
                    callbacks: {
                        title: function(context) {
                            return context[0].label;
                        },
                        label: function(context) {
                            return `RTT: ${context.parsed.y} ms`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    display: true,
                    grid: {
                        display: false
                    },
                    ticks: {
                        maxTicksLimit: 6,
                        maxRotation: 0,
                        font: {
                            size: 10
                        }
                    }
                },
                y: {
                    display: true,
                    beginAtZero: true,
                    suggestedMin: 0,
                    suggestedMax: 100,
                    grid: {
                        color: '#21262d'
                    },
                    ticks: {
                        font: {
                            size: 10
                        },
                        callback: function(value) {
                            return value + ' ms';
                        }
                    }
                }
            }
        }
    });
}


// Kalite Dagilimi Pie Chart
function createQualityChart(canvasId) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) {
        console.error('Quality chart canvas not found:', canvasId);
        return null;
    }

    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Mükemmel', 'İyi', 'Orta', 'Zayıf', 'Çok Zayıf'],
            datasets: [{
                data: [0, 0, 0, 0, 0],
                backgroundColor: [
                    '#3fb950',
                    '#7ee787',
                    '#d29922',
                    '#f0883e',
                    '#f85149'
                ],
                borderColor: '#161b22',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '60%',
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        boxWidth: 12,
                        padding: 8,
                        font: {
                            size: 11
                        }
                    }
                },
                tooltip: {
                    backgroundColor: '#161b22',
                    borderColor: '#30363d',
                    borderWidth: 1,
                    titleColor: '#c9d1d9',
                    bodyColor: '#8b949e',
                    callbacks: {
                        label: function(context) {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = total > 0 ? Math.round((context.raw / total) * 100) : 0;
                            return `${context.label}: ${context.raw} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}


// Chart'a veri ekle
function addChartData(chart, label, value, maxPoints = 60) {
    if (!chart) {
        console.warn('[Chart] Chart nesnesi yok!');
        return;
    }

    // Deger kontrolu - null/undefined olmasin, sayi olsun
    const numValue = parseFloat(value);
    if (isNaN(numValue)) {
        console.warn('[Chart] Gecersiz deger:', value);
        return;
    }

    chart.data.labels.push(label);
    chart.data.datasets[0].data.push(numValue);

    // Maksimum nokta sayisini asma
    if (chart.data.labels.length > maxPoints) {
        chart.data.labels.shift();
        chart.data.datasets[0].data.shift();
    }

    chart.update('none');
}


// Chart'i toplu veri ile guncelle
function updateChartBulk(chart, data, maxPoints = 60) {
    if (!chart) {
        console.warn('[Chart] Bulk update - chart nesnesi yok!');
        return;
    }
    if (!data || !Array.isArray(data)) {
        console.warn('[Chart] Bulk update - veri yok veya array degil:', data);
        return;
    }

    const labels = [];
    const values = [];

    // Son maxPoints veriyi al
    const slicedData = data.slice(-maxPoints);

    slicedData.forEach(item => {
        // Zaman formatla
        const time = item.time ? formatTime(item.time) : '';
        // Deger sayiya cevir
        const numValue = parseFloat(item.value);
        if (!isNaN(numValue)) {
            labels.push(time);
            values.push(numValue);
        }
    });

    console.log('[Chart] Bulk update:', values.length, 'nokta yuklendi');

    chart.data.labels = labels;
    chart.data.datasets[0].data = values;
    chart.update('none');
}


// Kalite chart'ini guncelle
function updateQualityChart(chart, distribution) {
    if (!chart || !distribution) return;

    const data = [
        distribution['Mükemmel'] || 0,
        distribution['İyi'] || 0,
        distribution['Orta'] || 0,
        distribution['Zayıf'] || 0,
        distribution['Çok Zayıf'] || 0
    ];

    chart.data.datasets[0].data = data;
    chart.update('none');
}


// Zaman formatla (ISO -> HH:MM:SS)
function formatTime(isoString) {
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


// Export
window.createRSSIChart = createRSSIChart;
window.createRTTChart = createRTTChart;
window.createQualityChart = createQualityChart;
window.addChartData = addChartData;
window.updateChartBulk = updateChartBulk;
window.updateQualityChart = updateQualityChart;
