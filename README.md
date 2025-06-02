# CSI Data Collection Using ESP32

**Course:** ELE529E Embedded Systems  
**Objective:** Ensure reliable CSI data collection and meaningful visualization.

## Project Milestones & Delivery Plan

| Milestone | Tasks | Deadline | Status<br>(✓/✗) |
|-----------|-------|----------|-----------------|
| 1. Requirement Analysis | Define project scope, objectives, and CSI data collection requirements. | [02/05/2025] | ✓ |
| 2. System Design | ESP32 configuration, study Wi-Fi CSI architecture. | [16/05/2025] | ✓ |
| 3. Prototype Development | Implement ESP32 firmware for CSI data collection and Python visualization script. | [30/05/2025] | ✓ |
| 4. Testing & Debugging | Verify data accuracy, optimize capture rate, debug communication issues. | [05/06/2025] | ✗ |
| 5. Final Demo & Report | Prepare presentation with live visualization, data flow diagrams and submit final report. | [09/06/2025] | ✗ |

---

#### Notes
ESP-IDF version: 5.4
About build errors:
- if seeing squiggly lines, clean the build, then build till succeeds
- also if there are include errors related to cmake, disable the "cmake tools" extension. delete the build folder completely, then rebuild  

#### en faydalı kaynaklar
[How to create your First ESP IDF project](https://www.youtube.com/watch?v=oHHOCdmLiII)
https://github.com/espressif/esp-csi
[Getting Started with ESP32 Wireless Networking in C](https://www.youtube.com/watch?v=_dRrarmQiAM)





---

## Example folder contents

The project **sample_project** contains one source file in C language [main.c](main/main.c). The file is located in folder [main](main).

ESP-IDF projects are built using CMake. The project build configuration is contained in `CMakeLists.txt`
files that provide set of directives and instructions describing the project's source files and targets
(executable, library, or both). 

Below is short explanation of remaining files in the project folder.

```
├── CMakeLists.txt
├── main
│   ├── CMakeLists.txt
│   └── main.c
└── README.md                  This is the file you are currently reading
```
Additionally, the sample project contains Makefile and component.mk files, used for the legacy Make based build system. 
They are not used or needed when building with CMake and idf.py.
