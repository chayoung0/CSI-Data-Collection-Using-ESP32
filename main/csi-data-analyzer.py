import pandas as pd
import json
import numpy as np
import matplotlib.pyplot as plt

class CSIAnalyzer:
    def __init__(self, csv_filename):
        self.df = pd.read_csv(csv_filename)
        print(f"Loaded {len(self.df)} CSI packets from {csv_filename}")
    
    def basic_stats(self):
        print("\n=== Basic CSI Statistics ===")
        print(f"Total packets: {len(self.df)}")
        print(f"RSSI range: {self.df['rssi'].min()} to {self.df['rssi'].max()} dBm")
        print(f"Average RSSI: {self.df['rssi'].mean():.2f} dBm")
        print(f"Channels seen: {sorted(self.df['channel'].unique())}")
        print(f"Data rates: {sorted(self.df['rate'].unique())}")
        print(f"CSI data lengths: {sorted(self.df['data_length'].unique())}")
    
    def extract_csi_amplitudes(self, packet_index=0):
        """Extract amplitude data from a CSI packet"""
        if packet_index >= len(self.df):
            print(f"Packet index {packet_index} out of range")
            return None
        
        # Get CSI data (stored as JSON string)
        csi_json = self.df.iloc[packet_index]['csi_data']
        csi_raw = json.loads(csi_json)
        
        # Convert to numpy array
        csi_array = np.array(csi_raw, dtype=np.int8)
        
        # CSI data is interleaved: [real0, imag0, real1, imag1, ...]
        # Split into real and imaginary parts
        real_parts = csi_array[0::2]  # Even indices
        imag_parts = csi_array[1::2]  # Odd indices
        
        # Calculate amplitude (magnitude)
        amplitudes = np.sqrt(real_parts**2 + imag_parts**2)
        
        return {
            'real': real_parts,
            'imag': imag_parts,
            'amplitude': amplitudes,
            'phase': np.arctan2(imag_parts, real_parts)
        }
    
    def plot_csi_amplitude(self, packet_index=0):
        """Plot CSI amplitude for a specific packet"""
        csi_data = self.extract_csi_amplitudes(packet_index)
        
        if csi_data is None:
            return
        
        plt.figure(figsize=(12, 6))
        
        plt.subplot(2, 1, 1)
        plt.plot(csi_data['amplitude'])
        plt.title(f'CSI Amplitude - Packet {packet_index}')
        plt.xlabel('Subcarrier Index')
        plt.ylabel('Amplitude')
        plt.grid(True)
        
        plt.subplot(2, 1, 2)
        plt.plot(csi_data['phase'])
        plt.title(f'CSI Phase - Packet {packet_index}')
        plt.xlabel('Subcarrier Index')
        plt.ylabel('Phase (radians)')
        plt.grid(True)
        
        plt.tight_layout()
        plt.show()
    
    def plot_rssi_over_time(self):
        """Plot RSSI variation over time"""
        plt.figure(figsize=(12, 6))
        plt.plot(range(len(self.df)), self.df['rssi'])
        plt.title('RSSI Over Time')
        plt.xlabel('Packet Number')
        plt.ylabel('RSSI (dBm)')
        plt.grid(True)
        plt.show()
    
    def export_matlab_format(self, output_filename):
        """Export CSI data in a format suitable for MATLAB"""
        # This creates a simplified format for MATLAB analysis
        matlab_data = []
        
        for idx, row in self.df.iterrows():
            csi_raw = json.loads(row['csi_data'])
            csi_array = np.array(csi_raw, dtype=np.int8)
            
            # Reshape to complex numbers
            real_parts = csi_array[0::2]
            imag_parts = csi_array[1::2]
            
            matlab_data.append({
                'timestamp': row['timestamp'],
                'rssi': row['rssi'],
                'real': real_parts.tolist(),
                'imag': imag_parts.tolist()
            })
        
        # Save as JSON for easy MATLAB import
        with open(output_filename, 'w') as f:
            json.dump(matlab_data, f, indent=2)
        
        print(f"Exported {len(matlab_data)} packets to {output_filename}")

# Usage example
if __name__ == "__main__":
    # Replace with your actual CSV filename
    csv_file = "csi_data_20250602_002621.csv"  # Update this!
    
    try:
        analyzer = CSIAnalyzer(csv_file)
        analyzer.basic_stats()
        
        # Plot first packet's CSI data
        analyzer.plot_csi_amplitude(0)
        
        # Plot RSSI over time
        analyzer.plot_rssi_over_time()
        
        # Export for MATLAB (optional)
        # analyzer.export_matlab_format("csi_data_matlab.json")
        
    except FileNotFoundError:
        print(f"CSV file '{csv_file}' not found. Make sure to run the logger first!")
    except Exception as e:
        print(f"Error: {e}")