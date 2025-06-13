from flask import Flask, render_template, jsonify, request
import serial
import json
import re
import datetime
import csv
import threading
import time
import os
from collections import deque
import math
import uuid

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
        self.session_start_time = None
        
        # Create session directory
        self.session_id = str(uuid.uuid4())[:8]
        self.session_dir = f"sessions/session-{self.session_id}"
        os.makedirs(self.session_dir, exist_ok=True)
        
        # Store recent data for web display (keep last 100 packets)
        self.recent_data = deque(maxlen=100)
        self.latest_packet = {}
        
        # Store plotting data (keep last 200 points for smoother plots)
        self.plot_data = deque(maxlen=200)
        
        # Track available subcarriers for dropdown
        self.available_subcarriers = set()
        
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
        filepath = os.path.join(self.session_dir, filename)
        
        self.csv_file = open(filepath, 'w', newline='')
        
        fieldnames = [
            'timestamp', 'rssi', 'rate', 'channel', 'bandwidth', 
            'data_length', 'esp_timestamp', 'csi_data'
        ]
        
        self.csv_writer = csv.DictWriter(self.csv_file, fieldnames=fieldnames)
        self.csv_writer.writeheader()
        
        print(f"Created CSV file: {filepath}")
        return filepath
    
    def parse_csi_line(self, line):
        print(f"Attempting to parse line: {line[:200]}...")  # Debug log
        match = re.search(r'CSI_START(\{.*?\})CSI_END', line)
        
        if match:
            try:
                json_str = match.group(1)
                print(f"Found JSON string: {json_str[:200]}...")  # Debug log
                data = json.loads(json_str)
                print(f"Successfully parsed JSON data: {str(data)[:200]}...")  # Debug log
                return data
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                print(f"Problematic JSON string: {json_str}")  # Debug log
        else:
            print("No CSI_START/CSI_END markers found in line")  # Debug log
        
        return None
    
    def analyze_csi_structure(self, csi_data):
        """Analyze CSI data structure to identify amplitude/phase pairs"""
        if not csi_data or not isinstance(csi_data, list):
            return {}
        
        # Update available subcarriers
        for i in range(len(csi_data)):
            self.available_subcarriers.add(i)
        
        return {'total_subcarriers': len(csi_data)}
    
    def extract_subcarrier_data(self, csi_data, subcarrier_indices):
        """Extract raw subcarrier values directly from CSI data array"""
        if not csi_data:
            print("No CSI data provided")
            return {}
        
        print(f"Processing subcarriers {subcarrier_indices} with CSI data length {len(csi_data)}")
        print(f"First 10 CSI values: {csi_data[:10]}")  # Debug log
        result = {}
        
        for idx in subcarrier_indices:
            try:
                if idx < len(csi_data):
                    # Use raw value directly without any transformation
                    value = csi_data[idx]
                    result[f'subcarrier_{idx}'] = value
                    print(f"Subcarrier {idx} value: {value}")
                else:
                    print(f"Subcarrier {idx} index out of range (idx={idx}, len={len(csi_data)})")
                    result[f'subcarrier_{idx}'] = 0
                    
            except (TypeError, ValueError, IndexError) as e:
                print(f"Error processing subcarrier {idx}: {e}")
                print(f"Problematic value: {csi_data[idx] if idx < len(csi_data) else 'out of range'}")  # Debug log
                result[f'subcarrier_{idx}'] = 0
        
        return result
    
    def start_logging(self):
        if not self.serial_conn:
            print("Not connected to ESP32")
            return False
        
        if self.is_running:
            print("Already logging")
            return False
            
        self.is_running = True
        self.session_start_time = time.time()
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
                    try:
                        line = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                        print(f"Raw line from serial: {line[:200]}...")  # Debug log
                        
                        if line:
                            csi_data = self.parse_csi_line(line)
                            
                            if csi_data:
                                print(f"Successfully parsed CSI data with keys: {list(csi_data.keys())}")  # Debug log
                                python_timestamp = datetime.datetime.now().isoformat()
                                current_time = time.time()
                                
                                # Analyze CSI structure
                                csi_array = csi_data.get('csi_data', [])
                                print(f"CSI array length: {len(csi_array)}")  # Debug log
                                print(f"First 10 CSI values: {csi_array[:10]}")  # Debug log
                                self.analyze_csi_structure(csi_array)
                                
                                row = {
                                    'timestamp': python_timestamp,
                                    'rssi': csi_data.get('rssi', ''),
                                    'rate': csi_data.get('rate', ''),
                                    'channel': csi_data.get('channel', ''),
                                    'bandwidth': csi_data.get('bandwidth', ''),
                                    'data_length': csi_data.get('len', ''),
                                    'esp_timestamp': csi_data.get('timestamp', ''),
                                    'csi_data': json.dumps(csi_array)
                                }
                                
                                # Write to CSV
                                if self.csv_writer:
                                    self.csv_writer.writerow(row)
                                    self.csv_file.flush()
                                    print(f"Wrote packet #{self.packet_count} to CSV")  # Debug log
                                
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
                                    'esp_timestamp': csi_data.get('esp_timestamp', 0),
                                    'time_passed': current_time - self.session_start_time if self.session_start_time else 0
                                }
                                
                                # Store plotting data with timestamp
                                plot_point = {
                                    'time': current_time,
                                    'rssi': csi_data.get('rssi', 0)
                                }
                                
                                # Add all CSI data points to plot data
                                for i in range(len(csi_array)):
                                    plot_point[f'subcarrier_{i}'] = csi_array[i]
                                
                                self.plot_data.append(plot_point)
                                print(f"Added plot point: {plot_point}")  # Debug log
                                
                                print(f"CSI packet #{self.packet_count} - RSSI: {csi_data.get('rssi')}dBm")
                            
                            else:
                                # Handle other ESP32 output
                                if line and not line.startswith('CSI_START'):
                                    print(f"ESP32: {line}")
                    except Exception as e:
                        print(f"Error processing serial line: {e}")
                        import traceback
                        traceback.print_exc()
                
                time.sleep(0.01)  # Small delay to prevent excessive CPU usage
                
        except Exception as e:
            print(f"Logging error: {e}")
            import traceback
            traceback.print_exc()
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
            'port': self.port,
            'session_id': self.session_id,
            'session_dir': self.session_dir
        }
    
    def get_recent_data(self):
        return list(self.recent_data)
    
    def get_latest_packet(self):
        return self.latest_packet
    
    def get_available_subcarriers(self):
        return sorted(list(self.available_subcarriers))
    
    def get_plot_data(self, selected_subcarriers=None):
        """Return data formatted for plotting with configurable subcarriers"""
        if not self.plot_data:
            return {'time': [], 'rssi': [], 'subcarriers': {}}
        
        if selected_subcarriers is None:
            selected_subcarriers = [1, 5, 9, 13]  # Default
        
        print(f"Getting plot data for subcarriers: {selected_subcarriers}")  # Debug log
        
        # Get current time to calculate relative timestamps
        current_time = time.time()
        
        # Convert to relative time (seconds ago) for easier plotting
        plot_formatted = {
            'time': [],
            'rssi': [],
            'subcarriers': {}
        }
        
        # Initialize subcarrier data
        for sc in selected_subcarriers:
            key = f'subcarrier_{sc}'
            plot_formatted['subcarriers'][key] = []
        
        # Only use the last 100 points
        recent_points = list(self.plot_data)[-100:]
        print(f"Number of recent points: {len(recent_points)}")  # Debug log
        
        for point in recent_points:
            relative_time = point['time'] - current_time  # This will be negative (seconds ago)
            plot_formatted['time'].append(relative_time)
            plot_formatted['rssi'].append(point.get('rssi', 0))
            
            # Add subcarrier data
            for sc in selected_subcarriers:
                key = f'subcarrier_{sc}'
                value = point.get(key, 0)
                plot_formatted['subcarriers'][key].append(value)
                if len(plot_formatted['subcarriers'][key]) == 1:  # Debug log first value
                    print(f"First value for {key}: {value}")
        
        return plot_formatted
    
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
        <title>ESP32 CSI Data Monitor with Configurable Plots</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 1400px; margin: 0 auto; }
            .card { background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .status { display: flex; gap: 20px; align-items: center; flex-wrap: wrap; }
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
            #data-log { height: 300px; overflow-y: scroll; border: 1px solid #ddd; padding: 10px; background: #f8f9fa; }
            .chart-container { height: 400px; margin: 20px 0; }
            .plots-container { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
            .plot-controls { display: flex; gap: 15px; align-items: center; margin-bottom: 15px; flex-wrap: wrap; }
            .control-group { display: flex; align-items: center; gap: 5px; }
            select, input[type="text"] { padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
            .multi-select { min-width: 200px; }
            @media (max-width: 1200px) {
                .plots-container { grid-template-columns: 1fr; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>ESP32 CSI Data Monitor with Configurable Real-time Plots</h1>
            
            <div class="card">
                <h3>Connection Status</h3>
                <div class="status" id="status">
                    <div class="status-item disconnected">Disconnected</div>
                    <div class="status-item stopped">Not Logging</div>
                    <div>Packets: <span id="packet-count">0</span></div>
                    <div>Session: <span id="session-id">None</span></div>
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
                <h3>Real-time Plots</h3>
                <div class="plot-controls">
                    <div class="control-group">
                        <label>Subcarriers:</label>
                        <select id="subcarrier1" class="subcarrier-select">
                            <option value="0">Subcarrier 0</option>
                            <option value="1" selected>Subcarrier 1</option>
                            <option value="2">Subcarrier 2</option>
                            <!-- Add options 3-127 -->
                        </select>
                        <select id="subcarrier2" class="subcarrier-select">
                            <option value="0">Subcarrier 0</option>
                            <option value="1">Subcarrier 1</option>
                            <option value="2">Subcarrier 2</option>
                            <!-- Add options 3-127 -->
                        </select>
                        <select id="subcarrier3" class="subcarrier-select">
                            <option value="0">Subcarrier 0</option>
                            <option value="1">Subcarrier 1</option>
                            <option value="2">Subcarrier 2</option>
                            <!-- Add options 3-127 -->
                        </select>
                        <select id="subcarrier4" class="subcarrier-select">
                            <option value="0">Subcarrier 0</option>
                            <option value="1">Subcarrier 1</option>
                            <option value="2">Subcarrier 2</option>
                            <!-- Add options 3-127 -->
                        </select>
                    </div>
                    <button class="btn-primary" onclick="updatePlotConfig()">Update Plots</button>
                </div>
                <div class="plots-container">
                    <div class="chart-container">
                        <canvas id="rssiChart"></canvas>
                    </div>
                    <div class="chart-container">
                        <canvas id="subcarrierChart"></canvas>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h3>Data Log</h3>
                <div id="data-log"></div>
            </div>
        </div>
        
        <script>
            let selectedSubcarriers = [1, 5, 9, 13];
            
            // Chart configurations
            const rssiChart = new Chart(document.getElementById('rssiChart'), {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'RSSI (dBm)',
                        data: [],
                        borderColor: 'rgb(255, 99, 132)',
                        backgroundColor: 'rgba(255, 99, 132, 0.2)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'RSSI over Time'
                        }
                    },
                    scales: {
                        x: {
                            title: {
                                display: true,
                                text: 'Time (seconds ago)'
                            }
                        },
                        y: {
                            title: {
                                display: true,
                                text: 'RSSI (dBm)'
                            }
                        }
                    },
                    animation: {
                        duration: 0
                    }
                }
            });
            
            const subcarrierChart = new Chart(document.getElementById('subcarrierChart'), {
                type: 'line',
                data: {
                    labels: [],
                    datasets: []
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Subcarrier Values over Time'
                        }
                    },
                    scales: {
                        x: {
                            title: {
                                display: true,
                                text: 'Time (seconds ago)'
                            }
                        },
                        y: {
                            title: {
                                display: true,
                                text: 'Value'
                            }
                        }
                    },
                    animation: {
                        duration: 0
                    }
                }
            });
            
            // Initialize subcarrier dropdowns with all 128 options
            function initializeSubcarrierDropdowns() {
                const dropdowns = ['subcarrier1', 'subcarrier2', 'subcarrier3', 'subcarrier4'];
                dropdowns.forEach((id, index) => {
                    const select = document.getElementById(id);
                    select.innerHTML = '';
                    for (let i = 0; i < 128; i++) {
                        const option = document.createElement('option');
                        option.value = i;
                        option.textContent = `Subcarrier ${i}`;
                        if (i === selectedSubcarriers[index]) {
                            option.selected = true;
                        }
                        select.appendChild(option);
                    }
                });
            }
            
            function updatePlotConfig() {
                selectedSubcarriers = [
                    parseInt(document.getElementById('subcarrier1').value),
                    parseInt(document.getElementById('subcarrier2').value),
                    parseInt(document.getElementById('subcarrier3').value),
                    parseInt(document.getElementById('subcarrier4').value)
                ];
                
                // Update chart title
                subcarrierChart.options.plugins.title.text = 'Subcarrier Values over Time';
                subcarrierChart.options.scales.y.title.text = 'Value';
                
                // Clear existing datasets
                subcarrierChart.data.datasets = [];
                
                // Create new datasets
                const colors = [
                    'rgb(54, 162, 235)',
                    'rgb(255, 205, 86)', 
                    'rgb(75, 192, 192)',
                    'rgb(153, 102, 255)'
                ];
                
                selectedSubcarriers.forEach((sc, index) => {
                    const color = colors[index % colors.length];
                    subcarrierChart.data.datasets.push({
                        label: `Subcarrier ${sc}`,
                        data: [],
                        borderColor: color,
                        backgroundColor: color.replace('rgb', 'rgba').replace(')', ', 0.2)'),
                        tension: 0.1
                    });
                });
                
                subcarrierChart.update();
            }
            
            function updateCharts() {
                const params = new URLSearchParams({
                    subcarriers: selectedSubcarriers.join(',')
                });
                
                fetch('/api/plot_data?' + params)
                    .then(response => response.json())
                    .then(data => {
                        if (data.time && data.time.length > 0) {
                            // Update RSSI chart
                            rssiChart.data.labels = data.time;
                            rssiChart.data.datasets[0].data = data.rssi;
                            rssiChart.update('none');
                            
                            // Update subcarrier chart
                            subcarrierChart.data.labels = data.time;
                            selectedSubcarriers.forEach((sc, index) => {
                                const key = `subcarrier_${sc}`;
                                if (subcarrierChart.data.datasets[index] && data.subcarriers[key]) {
                                    subcarrierChart.data.datasets[index].data = data.subcarriers[key];
                                }
                            });
                            subcarrierChart.update('none');
                        }
                    })
                    .catch(error => console.error('Error updating charts:', error));
            }
            
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
                            <div>Session: <span id="session-id">${data.session_id || 'None'}</span></div>
                        `;
                    });
            }
            
            function formatTimePassed(seconds) {
                if (seconds < 60) {
                    return `${seconds.toFixed(1)}s`;
                } else if (seconds < 3600) {
                    const minutes = Math.floor(seconds / 60);
                    const secs = Math.floor(seconds % 60);
                    return `${minutes}m ${secs}s`;
                } else {
                    const hours = Math.floor(seconds / 3600);
                    const minutes = Math.floor((seconds % 3600) / 60);
                    return `${hours}h ${minutes}m`;
                }
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
                                <div class="data-item"><strong>Timestamp:</strong> ${data.timestamp ? data.timestamp.split('T')[1].split('.')[0] : 'N/A'}</div>
                                <div class="data-item"><strong>Time Passed:</strong> ${data.time_passed ? formatTimePassed(data.time_passed) : 'N/A'}</div>
                                <div class="data-item"><strong>SC1 Value:</strong> ${data.subcarrier_1 ? data.subcarrier_1.toFixed(2) : 'N/A'}</div>
                                <div class="data-item"><strong>SC5 Value:</strong> ${data.subcarrier_5 ? data.subcarrier_5.toFixed(2) : 'N/A'}</div>
                                <div class="data-item"><strong>SC9 Value:</strong> ${data.subcarrier_9 ? data.subcarrier_9.toFixed(2) : 'N/A'}</div>
                                <div class="data-item"><strong>SC13 Value:</strong> ${data.subcarrier_13 ? data.subcarrier_13.toFixed(2) : 'N/A'}</div>
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
                            logDiv.innerHTML = data.slice(-15).reverse().map(packet => 
                                `<div>Packet #${packet.packet_num}: Value=${packet.subcarrier_1 ? packet.subcarrier_1.toFixed(2) : 'N/A'}, Time=${packet.time_passed ? formatTimePassed(packet.time_passed) : 'N/A'} [${packet.timestamp ? packet.timestamp.split('T')[1].split('.')[0] : 'N/A'}]</div>`
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
                }).then(() => {
                    // Update available subcarriers after connection
                    setTimeout(initializeSubcarrierDropdowns, 2000);
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
            
            // Initialize plot configuration and dropdowns
            initializeSubcarrierDropdowns();
            updatePlotConfig();
            
            // Update every second
            setInterval(() => {
                updateStatus();
                updateLatestData();
                updateDataLog();
                updateCharts();
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
    return jsonify({'connected': False, 'logging': False, 'packet_count': 0, 'port': '', 'session_id': None, 'session_dir': None})

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

@app.route('/api/subcarriers')
def api_subcarriers():
    if logger:
        return jsonify(logger.get_available_subcarriers())
    return jsonify([])

@app.route('/api/plot_data')
def api_plot_data():
    if logger:
        # Get parameters from query string
        subcarriers_param = request.args.get('subcarriers', '1,5,9,13')
        
        try:
            selected_subcarriers = [int(x.strip()) for x in subcarriers_param.split(',') if x.strip()]
            print(f"Plot data requested for subcarriers: {selected_subcarriers}")  # Debug log
            
            # Validate subcarrier indices
            selected_subcarriers = [sc for sc in selected_subcarriers if 0 <= sc < 128]
            
            if not selected_subcarriers:
                selected_subcarriers = [1, 5, 9, 13]  # Default fallback
                
        except ValueError:
            selected_subcarriers = [1, 5, 9, 13]  # Default fallback
        
        plot_data = logger.get_plot_data(selected_subcarriers)
        print(f"Returning plot data: {plot_data}")  # Debug log
        return jsonify(plot_data)
    return jsonify({'time': [], 'rssi': [], 'subcarriers': {}})

@app.route('/api/connect', methods=['POST'])
def api_connect():
    global logger
    data = request.get_json()
    port = data.get('port', 'COM3')
    
    # Close existing connection
    if logger:
        logger.close()
        time.sleep(1)  # Give extra time for cleanup
    
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