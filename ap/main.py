from network import WLAN
import pycom
import time
import usocket
import _thread

pycom.heartbeat(False)

SSID = 'LoPy4-Network'
PASSWORD = 'lopy4pass123'
CHANNEL = 7

CLIENT_PORT = 12345
PC_PORT = 12346

last_rssi = None
last_rtt = 0
last_count = 0
last_update_time = 0
client_connected = False

print('Wi-Fi Access Point + RSSI + RTT Relay baslatiliyor...')
print('SSID:', SSID)

wlan = WLAN(mode=WLAN.AP, ssid=SSID, auth=(WLAN.WPA2, PASSWORD), channel=CHANNEL)

wlan.ifconfig(id=1, config=('192.168.4.1', '255.255.255.0', '192.168.4.1', '8.8.8.8'))

print('Access Point aktif!')
print('IP:', wlan.ifconfig(id=1)[0])


def client_server():
    global last_rssi, last_rtt, last_count, last_update_time, client_connected
    server = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
    server.setsockopt(usocket.SOL_SOCKET, usocket.SO_REUSEADDR, 1)
    server.bind(('192.168.4.1', CLIENT_PORT))
    server.listen(5)
    print('Client Server port {} dinleniyor...'.format(CLIENT_PORT))

    while True:
        try:
            client, addr = server.accept()
            data = client.recv(64) # Veri al
            if data:
                msg = data.decode().strip()

                if msg.startswith('RSSI:'):
                    client.send(b'ACK')

                elif msg.startswith('DATA:'):
                    parts = msg[5:].split(',')
                    if len(parts) >= 3:
                        last_rssi = int(parts[0])
                        last_rtt = int(parts[1])
                        last_count = int(parts[2])
                        last_update_time = time.time()
                        client_connected = True
                        print('[CLIENT] #{} RSSI: {} dBm, RTT: {} ms'.format(
                            last_count, last_rssi, last_rtt))

            client.close()
        except Exception as e:
            print('Client server hatasi:', e)


def pc_server():
    global last_rssi, last_rtt, last_count, last_update_time, client_connected
    server = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
    server.setsockopt(usocket.SOL_SOCKET, usocket.SO_REUSEADDR, 1)
    server.bind(('192.168.4.1', PC_PORT))
    server.listen(5)
    print('PC Server port {} dinleniyor...'.format(PC_PORT))

    while True:
        try:
            client, addr = server.accept()
            print('[PC] Bilgisayar baglandi:', addr[0])

            prev_count = -1
            was_connected = False
            disconnect_sent = False

            while True:
                try:
                    current_time = time.time()
                    elapsed = current_time - last_update_time if last_update_time > 0 else 999

                    is_connected = elapsed < 5

                    if was_connected and not is_connected and not disconnect_sent:
                        client_connected = False
                        msg = 'STATUS:DISCONNECTED\n'
                        client.send(msg.encode())
                        print('[PC] Client koptu bildirimi gonderildi')
                        disconnect_sent = True

                    elif not was_connected and is_connected:
                        client_connected = True
                        msg = 'STATUS:CONNECTED\n'
                        client.send(msg.encode())
                        print('[PC] Client baglandi bildirimi gonderildi')
                        disconnect_sent = False

                    was_connected = is_connected

                    if last_rssi is not None and last_count != prev_count:
                        msg = 'DATA:{},{},{}\n'.format(last_rssi, last_rtt, last_count)
                        client.send(msg.encode())
                        prev_count = last_count

                    time.sleep(0.5)
                except:
                    print('[PC] Bilgisayar baglantisi kesildi')
                    break
            client.close()
        except Exception as e:
            print('PC server hatasi:', e)


_thread.start_new_thread(client_server, ())
_thread.start_new_thread(pc_server, ())

print('Sistem hazir!')
print('- LoPy4 Client RSSI + RTT gonderecek (port {})'.format(CLIENT_PORT))
print('- Bilgisayar veri alacak (port {})'.format(PC_PORT))

while True:
    if last_rssi is not None and (time.time() - last_update_time) < 10:
        pycom.rgbled(0x00FF00) # Yeşil Bağlı
    else:
        pycom.rgbled(0xFF8000) # Turunuc : Bağlantı yok /zayıf

    time.sleep(1)
