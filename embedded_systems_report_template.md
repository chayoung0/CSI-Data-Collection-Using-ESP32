# ELE529E Embedded Systems Project Progress Report

**Course:** ELE529E Embedded Systems  
**Submission Date:** [02/05/2025]

## 1. Project Overview

| Project Title | CSI Data Collection Using ESP32 |
|---------------|---------------------|
| Team Members | Meliha Çağla Kara |
| Project Start Date | [18/04/2025] |
| Expected Completion | [09/06/2025] |

## 2. Project Milestones & Delivery Plan

| Milestone | Tasks | Deadline | Status<br>(✓/✗) |
|-----------|-------|----------|-----------------|
| 1. Requirement Analysis | Define project scope, objectives, and CSI data collection requirements. | [02/05/2025] | ✓ |
| 2. System Design | ESP32 configuration, study Wi-Fi CSI architecture. | [16/05/2025] | ✓ |
| 3. Prototype Development | Implement ESP32 firmware for CSI data collection and Python visualization script. | [30/05/2025] | ✓ |
| 4. Testing & Debugging | Verify data accuracy, optimize capture rate, debug communication issues. | [05/06/2025] | ✗ |
| 5. Final Demo & Report | Prepare presentation with live visualization, data flow diagrams and submit final report. | [09/06/2025] | ✗ |

## 3. Individual Contribution Plan

### Meliha Çağla Kara

| Task | Responsibility | Estimated Time |
|------|---------------|----------------|
| ESP32 Configuration | Configure ESP32 for CSI data capture, Wi-Fi parameter setup. | 1.5 weeks |
| CSI Data Collection | Implement firmware for Channel State Information extraction. | 2 weeks |
| Data Transfer Protocol | Design efficient protocol for transferring CSI data to computer. | 1 week |
| Python Visualization | Develop real-time visualization dashboard for CSI data. | 2 weeks |
| Testing & Validation | Verify accuracy across different environments, optimize performance. | 1 week |

## 4. Project Quality Utility Tree

**Objective:** Ensure reliable CSI data collection and meaningful visualization.

1. Functional Correctness
   ├── 1.1 CSI Data Accuracy (validated against reference measurements)
   ├── 1.2 Sampling Rate (minimum 10 samples/second)
   └── 1.3 Power Efficiency (<200mA in continuous operation)
2. Robustness
   ├── 2.1 Error Handling (packet loss recovery, connection reestablishment)
   └── 2.2 Fault Recovery (auto-restart on crash, data backup)
   └── 2.3 Real-time data logging. Don't lose data upon crashing
3. Maintainability
   ├── 3.1 Modular Code (separate modules for capture, processing, visualization)
   └── 3.2 Documentation (code comments, setup guide, usage instructions)

## 5. Project Structure Diagram (PlantUML)

```
@startuml
package "Hardware" {
  [ESP32] --> [Wi-Fi Environment]
  [ESP32] --> [USB/Serial Connection]
}
package "Firmware" {
  [ESP32 Framework] --> [CSI Collection Module]
  [ESP32 Framework] --> [Data Processing Module]
  [ESP32 Framework] --> [Serial Communication Module]
}
package "Software" {
  [Python Script] --> [Data Parsing]
  [Python Script] --> [Visualization Engine]
  [Python Script] --> [Data Storage]
}
[ESP32] <--> [Python Script] : Serial/USB Protocol
@enduml
```

## 6. Activity Diagram (PlantUML)

```
@startuml
start
:Initialize ESP32 Hardware;
:Configure Wi-Fi in Monitor Mode;
repeat
  :Capture CSI Data Packets;
  :Process Raw CSI Data;
  :Send Processed Data via Serial;
  :Python Script Receives Data;
  :Update Visualization;
repeat while (System Running?) is (Yes)
-> No;
:Save Collected Data;
stop
@enduml
```

## 7. Project Demo Setup

### Hardware Requirements
- ESP32 Development Board
- USB-to-Serial Cable
- Computer for running visualization software
- Secondary Wi-Fi device for generating network traffic (optional)

### Software Requirements
- ESP-IDF Development Framework
- Python Script (for CSI data visualization)

### Demo Steps
1. Power on the ESP32 system and establish serial connection.
2. Launch Python visualization script on the computer.
3. Verify real-time CSI data collection (amplitude and phase plots).
4. Demonstrate environmental changes affecting CSI measurements.
5. Show data export functionality and analysis features.

## 8. Risks & Mitigation

| Risk | Probability | Impact | Mitigation Strategy |
|------|------------|--------|---------------------|
| ESP32 CSI API Limitations | High | Medium | Use appropriate ESP-IDF version |
| Serial Communication Bottlenecks | Medium | High | Optimize transfer protocol |
| Wi-Fi Interference | High | Medium | Include filtering algorithms, environment baseline measurements |
| Visualization Performance | Medium | Medium | Implement efficient rendering, consider downsampling for display |

## 9. Conclusion

This report outlines the planned development of the ESP32 CSI Data Gathering and Visualization System:
- ✔ Quality assurance strategies focused on CSI data reliability.
- ✔ System architecture and data flow diagrams.

**Next Steps:** Begin implementing the ESP32 firmware for CSI data collection using the ESP-IDF framework.

## Appendices
- [A] [ESP32 CSI Functionality Documentation](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/wifi.html#wi-fi-channel-state-information)
- [B] [GitHub Repository](https://github.com/chayoung0/CSI-Data-Collection-Using-ESP32)
- [C] Reference Papers on CSI-based Applications: [Awesome WiFi CSI Sensing](https://github.com/Marsrocky/Awesome-WiFi-CSI-Sensing)
