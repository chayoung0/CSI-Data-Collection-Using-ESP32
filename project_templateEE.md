**Istanbul Technical University**  
**Graduate Program in Embedded Systems**  
**Course Code: ELE529E**  
**Final Project Template**  
  
**Student Name(s):** Meliha Çağla Kara - **Everyone is welcome to join!**
**Student ID(s):** 504241262  
**Proposal Date:** 02.04.2025
---
  
## **1. Introduction**  
The first project involves capturing Channel State Information (CSI) using the ESP32, which provides valuable insights into network behavior. Although no immediate data analysis is performed, this project lays the groundwork for gathering precise network metrics. The second project examines the vulnerabilities in STM32 microcontrollers, specifically focusing on debugger-related exploits.  
  
## **2. Project Ideas**  

### **2.1 Project Idea 1**  
#### **Project Description**  
**Title:** CSI Data Collection Using ESP32  
**Description:** Channel State Information (CSI) represents detailed measurements of how Wi-Fi signals propagate between a transmitter (access point) and a receiver (station). This project aims to collect CSI data using an ESP32 microcontroller, which will act as the station, receiving packets from an access point. The gathered CSI data will be logged for potential future analysis.  
**Key Components & Technologies:** ESP32, ESP-IDF framework, Python for data logging and visualization  
**Potential Use Cases:** Wi-Fi performance diagnostics by monitoring channel characteristics in different conditions.  
  
#### **Project Challenges**  
- **Technical Challenges:** Properly configuring the ESP32 to extract and log CSI data efficiently, managing the large volume of data generated, and ensuring minimal packet loss.  
- **Hardware Constraints:** The ESP32 has limited memory and processing power, so data storage must be handled efficiently without overwhelming the device.  
- **Software/Algorithmic Complexity:** Mid. The raw data must be formatted and structured for easy future analysis.  
- **Integration Issues:** Ensuring that the access point operates in a stable mode to consistently send packets suitable for CSI extraction.  
  
#### **Non-Functional Requirements (NFRs)**  
- **Performance:** The system should log CSI data in real-time without excessive delays or buffering issues.  
- **Scalability:** While initially designed for a single station, the system should be adaptable for multi-device data collection in larger networks.   
- **Reliability & Fault Tolerance:** The system should handle occasional Wi-Fi disruptions and automatically resume logging when connectivity is restored.  
- **Security Considerations:** Deploying secure transmission methods.  
- **Power Efficiency:** The ESP32 should operate in a lightweight mode to minimize overheating.  



### **2.2 Project Idea 2**  
#### **Project Description**  
**Title:** STM32 Debugger Exploit Demonstration  
**Description:** This project aims to demonstrate and analyze known security vulnerabilities in STM32 microcontrollers, particularly focusing on debugger-related attacks. Inspired by research from "Microcontroller Exploits" by Travis Goodspeed (2024), this project will explore various weaknesses in STM32 devices, such as the STM32F217 DFU Exit, STM32F0 SWD Word Leak, STM32F1 Interrupt Jigsaw, STM32 FPB Glitch, and STM32 Ultraviolet Downgrade. The project will help illustrate the impact of these exploits and potential mitigation techniques.  
**Key Components & Technologies:** STM32, debugging interfaces, custom scripts for exploit execution and analysis  
**Potential Use Cases:** Educational demonstrations for understanding microcontroller vulnerabilities
  
#### **Project Challenges**  
- **Technical Challenges:** Understanding low-level STM32 architecture and debugging protocols, implementing known exploits correctly, and ensuring repeatability of the attacks. 
- **Hardware Constraints:** Requires **specific** STM32 models that contain the documented vulnerabilities, access to debugging interfaces, and potential hardware modifications. 
- **Software/Algorithmic Complexity:** Mid-Hard. Developing scripts to automate exploit execution and logging, analyzing debugging output, and reversing proprietary firmware protections.
- **Integration Issues:** Combining different debugging tools and ensuring compatibility with various STM32 firmware versions.
  
#### **Non-Functional Requirements (NFRs)**  
- **Performance:** The attack demonstrations should be repeatable and accurate within a reasonable time frame for educational purposes.
- **Scalability:** The project’s approach _can_ be extended to cover additional STM32 models or even other microcontrollers with similar vulnerabilities. However, the project’s focus will remain on demonstrating specific known exploits in STM32 devices.
- **Reliability & Fault Tolerance:** The exploits should be repeatable and tested under controlled conditions to ensure accuracy.
- **Security Considerations:** Ethical considerations must be maintained, ensuring that the project is used only for research and educational purposes.
- **Power Efficiency:** Not a primary concern, but the setup should avoid excessive power consumption to maintain stability during testing.
  
## **3. Conclusion**  
The proposed projects both address important aspects of embedded systems but differ significantly in focus and complexity. The first project, using the ESP32 to capture Channel State Information (CSI), focuses on gathering precise network data for future analysis. It presents challenges related to efficient data collection and minimizing power consumption. However it does not require complex data processing, keeping it relatively straightforward. This project is highly relevant in the context of wireless sensing and IoT, offering a foundational step in data gathering without requiring heavy computational resources.  
On the other hand, the STM32 Debugger Exploit Demonstration project delves into the vulnerabilities of embedded systems, particularly focusing on debugger-related attacks. This project is more technically complex due to the need to implement known exploits and analyze debugging interfaces, but it offers significant value in understanding embedded system security risks.  
Despite the value of both projects, the ESP32-based CSI collection project is the more promising option. CSI data is crucial in wireless communication research, providing insights into network performance and behavior. The ESP32, being one of the most affordable devices capable of gathering CSI data, makes this project an ideal starting point for those looking to explore the field without significant hardware investment.  

---  

**Instructor:** Dr. Özen Özkaya  
**Course Code:** ELE529E - Embedded Systems  

  
<br />  
<br />  
<br />  
<br />   

---  



### Previous Project Ideas Considered
**Title:** Secure IoT Data Logging with STM32 and HTTPS over TLS  
**Description:** This project aims to develop an STM32-based **secure HTTPS client** that can communicate with a remote web server using **TLS (SSL encryption)**. The system will collect sensor data, establish a **secure HTTPS connection**, send **GET/POST requests**, and log the data to a web server for storage and further processing. The implementation ensures **end-to-end encryption**, preventing unauthorized access to transmitted data.  

**Title:** STM32-based Encrypted Chat Application with TLS Security  
**Description:** This project aims to develop a secure communication platform using STM32 microcontrollers. The application will enable encrypted messaging over a network using the TLS (Transport Layer Security) protocol. The primary objective is to ensure confidentiality and integrity in embedded system communications by preventing eavesdropping and data tampering. The project will involve implementing TLS libraries on STM32 to establish secure connections, encrypt messages, and handle authentication.  