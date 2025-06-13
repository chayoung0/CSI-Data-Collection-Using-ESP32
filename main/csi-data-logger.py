import serial
import json
import csv
import datetime
import re
import os

class CSIDataLogger:
    def __init__(self, port, baud_rate=115200):
        self.port = port
        self.baud_rate = baud_rate
        self.serial_conn = None
        self.csv_writer = None
        self.csv_file = None
        
    def connect(self):
        try:
            self.serial_conn = serial.Serial(self.port, self.baud_rate, timeout=1)
            print(f"Connected to ESP32 on {self.port}")
            return True
        except serial.SerialException as e:
            print(f"Failed to connect: {e}")
            return False
    
    def setup_csv_file(self):
        # Create filename with timestamp
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"csi_data_{timestamp}.csv"
        
        self.csv_file = open(filename, 'w', newline='')
        
        # CSV headers
        fieldnames = [
            'timestamp', 'rssi', 'rate', 'channel', 'bandwidth', 
            'data_length', 'esp_timestamp', 'csi_data'
        ]
        
        self.csv_writer = csv.DictWriter(self.csv_file, fieldnames=fieldnames)
        self.csv_writer.writeheader()
        
        print(f"Created CSV file: {filename}")
        return filename
    
    def parse_csi_line(self, line):
        """Parse CSI data from the ESP32 output"""
        # Look for CSI_START{...}CSI_END pattern
        match = re.search(r'CSI_START(\{.*?\})CSI_END', line)
        
        if match:
            try:
                json_str = match.group(1)
                data = json.loads(json_str)
                return data
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                print(f"Problematic line: {line}")
        
        return None
    
    def log_csi_data(self):
        if not self.serial_conn:
            print("Not connected to ESP32")
            return
        
        csv_filename = self.setup_csv_file()
        packet_count = 0
        
        try:
            print("Starting CSI data collection... Press Ctrl+C to stop")
            
            while True:
                if self.serial_conn.in_waiting > 0:
                    line = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                    
                    if line:
                        # Check if this line contains CSI data
                        csi_data = self.parse_csi_line(line)
                        
                        if csi_data:
                            # Add Python timestamp
                            python_timestamp = datetime.datetime.now().isoformat()
                            
                            # Prepare CSV row
                            row = {
                                'timestamp': python_timestamp,
                                'rssi': csi_data.get('rssi', ''),
                                'rate': csi_data.get('rate', ''),
                                'channel': csi_data.get('channel', ''),
                                'bandwidth': csi_data.get('bandwidth', ''),
                                'data_length': csi_data.get('len', ''),
                                'esp_timestamp': csi_data.get('timestamp', ''),
                                'csi_data': json.dumps(csi_data.get('csi_data', []))  # Store as JSON string
                            }
                            
                            # Write to CSV
                            self.csv_writer.writerow(row)
                            self.csv_file.flush()  # Ensure data is written immediately
                            
                            packet_count += 1
                            print(f"CSI packet #{packet_count} - RSSI: {csi_data.get('rssi')}dBm, "
                                  f"Length: {csi_data.get('len')} bytes")
                        
                        else:
                            # Print other ESP32 output (debug messages, etc.)
                            if line and not line.startswith('CSI_START'):
                                print(f"ESP32: {line}")
                
        except KeyboardInterrupt:
            print(f"\nStopping... Collected {packet_count} CSI packets")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            if self.csv_file:
                self.csv_file.close()
                print(f"CSV file saved: {csv_filename}")
    
    def close(self):
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
        if self.csv_file:
            self.csv_file.close()

# Usage
if __name__ == "__main__":
    # Change COM port to match your ESP32
    logger = CSIDataLogger('COM3')  # Windows
    # logger = CSIDataLogger('/dev/ttyUSB0')  # Linux
    
    if logger.connect():
        try:
            logger.log_csi_data()
        finally:
            logger.close()
    else:
        print("Failed to connect to ESP32")