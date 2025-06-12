from flask import Flask, render_template, jsonify, request
import serial
import json
import re
import datetime
import csv
import threading
import time
from collections import deque

app = Flask(__name__)

class CSIDataLogger:
    def __init__(self, port, baud_rate=115200):
        self.port = port
        self.baud_rate = baud_rate
        self.serial_conn = None
        self.csv_writer = None
        self.csv_file = None
        self.is_running = False
        self.packet_count = 0
        
        # Store recent data for web display (keep last 100 packets)
        self.recent_data = deque(maxlen=100)
        self.latest_packet = {}
        
    def connect(self):
        try:
            self.serial_conn = serial.Serial(self.port, self.baud_rate, timeout=1)
            print(f"Connected to ESP32 on {self.port}")
            return True
        except serial.SerialException as e:
            print(f"Failed to connect: {e}")
            return False

    def setup_csv_file(self):
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"csi_data_{timestamp}.csv"
        
        self.csv_file = open(filename, 'w', newline='')
        
        fieldnames = [
            'timestamp', 'rssi', 'rate', 'channel', 'bandwidth', 
            'data_length', 'esp_timestamp', 'csi_data'
        ]
        
        self.csv_writer = csv.DictWriter(self.csv_file, fieldnames=fieldnames)
        self.csv_writer.writeheader()
        
        print(f"Created CSV file: {filename}")
        return filename
    
    def parse_csi_line(self, line):
        match = re.search(r'CSI_START(\{.*?\})CSI_END', line)
        
        if match:
            try:
                json_str = match.group(1)
                data = json.loads(json_str)
                return data
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
        
        return None
    
    def start_logging(self):
        if not self.serial_conn:
            print("Not connected to ESP32")
            return False
        
        if self.is_running:
            print("Already logging")
            return False
            
        self.is_running = True
        self.csv_filename = self.setup_csv_file()
        
        # Start logging in a separate thread
        self.logging_thread = threading.Thread(target=self._log_loop)
        self.logging_thread.daemon = True
        self.logging_thread.start()
        
        return True
    
    def _log_loop(self):
        try:
            print("Starting CSI data collection...")
            
            while self.is_running:
                if self.serial_conn and self.serial_conn.in_waiting > 0:
                    line = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                    
                    if line:
                        csi_data = self.parse_csi_line(line)
                        
                        if csi_data:
                            python_timestamp = datetime.datetime.now().isoformat()
                            
                            row = {
                                'timestamp': python_timestamp,
                                'rssi': csi_data.get('rssi', ''),
                                'rate': csi_data.get('rate', ''),
                                'channel': csi_data.get('channel', ''),
                                'bandwidth': csi_data.get('bandwidth', ''),
                                'data_length': csi_data.get('len', ''),
                                'esp_timestamp': csi_data.get('timestamp', ''),
                                'csi_data': json.dumps(csi_data.get('csi_data', []))
                            }
                            
                            # Write to CSV
                            if self.csv_writer:
                                self.csv_writer.writerow(row)
                                self.csv_file.flush()
                            
                            # Store for web display
                            self.packet_count += 1
                            display_data = {
                                'packet_num': self.packet_count,
                                'timestamp': python_timestamp,
                                'rssi': csi_data.get('rssi', 0),
                                'rate': csi_data.get('rate', 0),
                                'channel': csi_data.get('channel', 0),
                                'bandwidth': csi_data.get('bandwidth', 0),
                                'data_length': csi_data.get('len', 0),
                                'esp_timestamp': csi_data.get('timestamp', 0)
                            }
                            
                            self.recent_data.append(display_data)
                            self.latest_packet = display_data
                            
                            print(f"CSI packet #{self.packet_count} - RSSI: {csi_data.get('rssi')}dBm")
                        
                        else:
                            # Handle other ESP32 output
                            if line and not line.startswith('CSI_START'):
                                print(f"ESP32: {line}")
                
                time.sleep(0.01)  # Small delay to prevent excessive CPU usage
                
        except Exception as e:
            print(f"Logging error: {e}")
        finally:
            self.is_running = False
    
    def stop_logging(self):
        self.is_running = False
        if hasattr(self, 'logging_thread'):
            self.logging_thread.join(timeout=1)
    
    def get_status(self):
        return {
            'connected': self.serial_conn and self.serial_conn.is_open,
            'logging': self.is_running,
            'packet_count': self.packet_count,
            'port': self.port
        }
    
    def get_recent_data(self):
        return list(self.recent_data)
    
    def get_latest_packet(self):
        return self.latest_packet
    
    def close(self):
        self.stop_logging()
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
        if self.csv_file:
            self.csv_file.close()

# Global logger instance
logger = None

@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>ESP32 CSI Data Monitor</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; }
            .card { background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .status { display: flex; gap: 20px; align-items: center; }
            .status-item { padding: 10px 15px; border-radius: 5px; font-weight: bold; }
            .connected { background: #d4edda; color: #155724; }
            .disconnected { background: #f8d7da; color: #721c24; }
            .logging { background: #d1ecf1; color: #0c5460; }
            .stopped { background: #fff3cd; color: #856404; }
            button { padding: 10px 20px; margin: 5px; border: none; border-radius: 5px; cursor: pointer; font-size: 14px; }
            .btn-primary { background: #007bff; color: white; }
            .btn-success { background: #28a745; color: white; }
            .btn-danger { background: #dc3545; color: white; }
            .btn-warning { background: #ffc107; color: black; }
            .data-display { font-family: monospace; font-size: 12px; }
            .latest-data { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; }
            .data-item { background: #e9ecef; padding: 10px; border-radius: 5px; }
            #data-log { height: 400px; overflow-y: scroll; border: 1px solid #ddd; padding: 10px; background: #f8f9fa; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>ESP32 CSI Data Monitor</h1>
            
            <div class="card">
                <h3>Connection Status</h3>
                <div class="status" id="status">
                    <div class="status-item disconnected">Disconnected</div>
                    <div class="status-item stopped">Not Logging</div>
                    <div>Packets: <span id="packet-count">0</span></div>
                </div>
                
                <div style="margin-top: 15px;">
                    <input type="text" id="port-input" placeholder="COM3 or /dev/ttyUSB0" style="padding: 8px; width: 200px;">
                    <button class="btn-primary" onclick="connect()">Connect</button>
                    <button class="btn-danger" onclick="disconnect()">Disconnect</button>
                    <button class="btn-success" onclick="startLogging()">Start Logging</button>
                    <button class="btn-warning" onclick="stopLogging()">Stop Logging</button>
                </div>
            </div>
            
            <div class="card">
                <h3>Latest CSI Data</h3>
                <div class="latest-data" id="latest-data">
                    <div class="data-item">No data yet...</div>
                </div>
            </div>
            
            <div class="card">
                <h3>Data Log</h3>
                <div id="data-log"></div>
            </div>
        </div>
        
        <script>
            function updateStatus() {
                fetch('/api/status')
                    .then(response => response.json())
                    .then(data => {
                        const statusDiv = document.getElementById('status');
                        const connClass = data.connected ? 'connected' : 'disconnected';
                        const connText = data.connected ? 'Connected' : 'Disconnected';
                        const logClass = data.logging ? 'logging' : 'stopped';
                        const logText = data.logging ? 'Logging' : 'Not Logging';
                        
                        statusDiv.innerHTML = `
                            <div class="status-item ${connClass}">${connText} ${data.port ? '(' + data.port + ')' : ''}</div>
                            <div class="status-item ${logClass}">${logText}</div>
                            <div>Packets: <span id="packet-count">${data.packet_count}</span></div>
                        `;
                    });
            }
            
            function updateLatestData() {
                fetch('/api/latest')
                    .then(response => response.json())
                    .then(data => {
                        if (Object.keys(data).length > 0) {
                            const latestDiv = document.getElementById('latest-data');
                            latestDiv.innerHTML = `
                                <div class="data-item"><strong>Packet #:</strong> ${data.packet_num}</div>
                                <div class="data-item"><strong>RSSI:</strong> ${data.rssi} dBm</div>
                                <div class="data-item"><strong>Rate:</strong> ${data.rate}</div>
                                <div class="data-item"><strong>Channel:</strong> ${data.channel}</div>
                                <div class="data-item"><strong>Bandwidth:</strong> ${data.bandwidth}</div>
                                <div class="data-item"><strong>Data Length:</strong> ${data.data_length}</div>
                                <div class="data-item"><strong>Timestamp:</strong> ${data.timestamp}</div>
                            `;
                        }
                    });
            }
            
            function updateDataLog() {
                fetch('/api/recent')
                    .then(response => response.json())
                    .then(data => {
                        const logDiv = document.getElementById('data-log');
                        if (data.length > 0) {
                            logDiv.innerHTML = data.slice(-20).reverse().map(packet => 
                                `<div>Packet #${packet.packet_num}: RSSI=${packet.rssi}dBm, Ch=${packet.channel}, Rate=${packet.rate}, Len=${packet.data_length} [${packet.timestamp.split('T')[1].split('.')[0]}]</div>`
                            ).join('');
                            logDiv.scrollTop = 0;
                        }
                    });
            }
            
            function connect() {
                const port = document.getElementById('port-input').value || 'COM3';
                fetch('/api/connect', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({port: port})
                });
            }
            
            function disconnect() {
                fetch('/api/disconnect', {method: 'POST'});
            }
            
            function startLogging() {
                fetch('/api/start', {method: 'POST'});
            }
            
            function stopLogging() {
                fetch('/api/stop', {method: 'POST'});
            }
            
            // Update every second
            setInterval(() => {
                updateStatus();
                updateLatestData();
                updateDataLog();
            }, 1000);
            
            // Initial update
            updateStatus();
        </script>
    </body>
    </html>
    '''

@app.route('/api/status')
def api_status():
    if logger:
        return jsonify(logger.get_status())
    return jsonify({'connected': False, 'logging': False, 'packet_count': 0, 'port': ''})

@app.route('/api/latest')
def api_latest():
    if logger:
        return jsonify(logger.get_latest_packet())
    return jsonify({})

@app.route('/api/recent')
def api_recent():
    if logger:
        return jsonify(logger.get_recent_data())
    return jsonify([])

@app.route('/api/connect', methods=['POST'])
def api_connect():
    global logger
    data = request.get_json()
    port = data.get('port', 'COM3')
    
    # Close existing connection
    if logger:
        logger.close()
    
    logger = CSIDataLogger(port)
    success = logger.connect()
    
    return jsonify({'success': success, 'port': port})

@app.route('/api/disconnect', methods=['POST'])
def api_disconnect():
    global logger
    if logger:
        logger.close()
        logger = None
    return jsonify({'success': True})

@app.route('/api/start', methods=['POST'])
def api_start():
    if logger:
        success = logger.start_logging()
        return jsonify({'success': success})
    return jsonify({'success': False, 'error': 'Not connected'})

@app.route('/api/stop', methods=['POST'])
def api_stop():
    if logger:
        logger.stop_logging()
        return jsonify({'success': True})
    return jsonify({'success': False})

if __name__ == '__main__':
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    finally:
        if logger:
            logger.close()