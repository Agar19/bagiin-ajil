from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
import threading
import time
from bleak import BleakScanner
import asyncio

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # Allow connections from all origins

# BLE device data storage
detected_devices = []

def calculate_distance(rssi):
    """Approximates the distance based on RSSI."""
    tx_power = -59  # Adjust this value based on your hardware
    if rssi == 0:
        return -1  # Unknown distance
    return round(10 ** ((tx_power - rssi) / 20), 2)

async def scan_ble_devices():
    """Scans for BLE devices and emits updates."""
    global detected_devices
    while True:
        devices = await BleakScanner.discover()
        detected_devices = [
            {"id": d.address, "rssi": d.rssi, "distance": calculate_distance(d.rssi)}
            for d in devices
        ]
        # Filter devices within 10 meters
        nearby_devices = [d for d in detected_devices if d["distance"] <= 10]
        socketio.emit("devices_update", {"devices": nearby_devices})
        await asyncio.sleep(2)  # Scan interval

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scan')
def scan():
    """API endpoint to fetch nearby devices."""
    global detected_devices
    nearby_devices = [d for d in detected_devices if d["distance"] <= 10]
    return jsonify(nearby_devices)

@app.route('/trigger_alarm', methods=['POST'])
def trigger_alarm():
    """Endpoint to trigger an alarm for a specific device."""
    data = request.get_json()
    target_device = data.get("device_id")
    socketio.emit('alarm', {'device_id': target_device})
    return jsonify({"message": f"Alarm triggered for {target_device}"}), 200

if __name__ == '__main__':
    # Start BLE scanning in a background thread
    threading.Thread(target=lambda: asyncio.run(scan_ble_devices()), daemon=True).start()
    # Run Flask app
    socketio.run(app, host="10.3.130.92", debug=True)
