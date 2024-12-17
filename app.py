from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
import threading
import time
from bleak import BleakScanner

app = Flask(__name__)
socketio = SocketIO(app)

# BLE device data storage
detected_devices = []

def scan_ble_devices():
    """Scan for BLE devices and update detected_devices."""
    global detected_devices
    while True:
        devices = BleakScanner.discover()  # Discover nearby BLE devices
        detected_devices = [{"id": d.address, "rssi": d.rssi} for d in devices]
        time.sleep(2)  # Scan interval

def calculate_distance(rssi):
    """Approximates the distance based on RSSI."""
    tx_power = -59  # RSSI at 1 meter, adjust based on your hardware
    if rssi == 0:
        return -1  # Unable to determine
    return round(10 ** ((tx_power - rssi) / 20), 2)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scan')
def scan():
    """API endpoint to fetch nearby devices."""
    global detected_devices
    devices = [
        {"id": d["id"], "distance": calculate_distance(d["rssi"])}
        for d in detected_devices
        if calculate_distance(d["rssi"]) <= 10  # Filter devices within 10 meters
    ]
    return jsonify(devices)

@app.route('/trigger_alarm', methods=['POST'])
def trigger_alarm():
    """Endpoint to notify a specific device."""
    data = request.get_json()
    target_device = data.get("device_id")
    socketio.emit('alarm', {'device_id': target_device}, broadcast=True)
    return jsonify({"message": "Alarm triggered"}), 200

if __name__ == '__main__':
    # Start the BLE scanning in a separate thread
    threading.Thread(target=scan_ble_devices, daemon=True).start()

    # Run the Flask app with SocketIO
    socketio.run(app, debug=True)
