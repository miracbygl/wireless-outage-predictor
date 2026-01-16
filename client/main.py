from network import WLAN
import pycom
import time
import usocket

pycom.heartbeat(False)

SSID = 'LoPy4-Network'
PASSWORD = 'lopy4pass123'
AP_IP = '192.168.4.1'
AP_PORT = 12345

measurement_count = 0

print('Wi-Fi Client + RSSI + RTT Monitor baslatiliyor...')
print('Baglanilacak ag:', SSID)

pycom.rgbled(0xFF0000)

wlan = WLAN(mode=WLAN.STA)   # Station Mode (istemci modu )

wlan.connect(ssid=SSID, auth=(WLAN.WPA2, PASSWORD))

print('Baglaniliyor...')
while not wlan.isconnected():
    pycom.rgbled(0xFF0000)
    time.sleep(0.3)
    pycom.rgbled(0x000000)
    time.sleep(0.3)

print('Baglanti basarili!')
print('IP:', wlan.ifconfig()[0])


def get_rssi():
    try:
        networks = wlan.scan()  # Çevredeki tüm ağları tara
        for net in networks:
            if net.ssid == SSID: # AP mizi  bulur 
                return net.rssi  # Sinay gücünü  döndürür
        return None
    except:
        return None


def send_rssi_with_rtt(rssi, count):
    try:
        sock = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
        sock.settimeout(3)

        t1 = time.ticks_ms()  #Başlangıç Zamanı 

        sock.connect((AP_IP, AP_PORT))  # AP ye bağlan

        msg = 'RSSI:{}'.format(rssi)
        sock.send(msg.encode())  #RSSI VER 

        ack = sock.recv(16)   # ACK bekle  ACK AP den gelir 

        t2 = time.ticks_ms()  # Bitiş zamanı
        rtt = time.ticks_diff(t2, t1)  # RTT Farkı hesapla ve döndürü

        sock.close()

        sock2 = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
        sock2.settimeout(3)
        sock2.connect((AP_IP, AP_PORT))
        msg2 = 'DATA:{},{},{}'.format(rssi, rtt, count) # Tüm verileri gönder 
        sock2.send(msg2.encode())
        sock2.close()

        return rtt
    except Exception as e:
        print('Gonderme hatasi:', e)
        return None


print('RSSI + RTT olcumu basliyor...')

while True:
    if wlan.isconnected():
        rssi = get_rssi()
        if rssi is not None:
            measurement_count += 1
            rtt = send_rssi_with_rtt(rssi, measurement_count)
            if rtt is not None:
                print('[#{}] RSSI: {} dBm, RTT: {} ms'.format(measurement_count, rssi, rtt))
            else:
                print('[#{}] RSSI: {} dBm, RTT: hata'.format(measurement_count, rssi))
            pycom.rgbled(0x0000FF)
        else:
            print('[#{}] RSSI okunamadi'.format(measurement_count))
            pycom.rgbled(0xFFFF00)
    else:
        print('Baglanti kesildi!')
        pycom.rgbled(0xFF0000)
        wlan.connect(ssid=SSID, auth=(WLAN.WPA2, PASSWORD))

    time.sleep(1)  # Her saniye aynı döngü devam eder
