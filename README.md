# Two-site-Automated-Testbed-for-Evaluating-ADCs

## Overview
The Two-site Automated Test System (ATS-2) is a custom-designed testbed for evaluating ADCs, specifically focused on testing the ADS7816. This comprehensive testing solution consists of a custom-designed device interface board, National Instruments VirtualBench integration, and automated test programs implemented in Python.

### Key Features:
- **Dual Testing Sites**: Capability to test two ADC devices simultaneously
- **Comprehensive Test Suite**: Includes all relevant parametric and functional tests
- **Automated Control**: Python-based test automation for consistent results
- **Relay-Based Interface**: Flexible configuration using G5NB-1A4 DC24 and J104D2C24VDC.15S relays
- **Power Management**: External 24V power supply for relay control

## Test Capabilities
The ATS-2 supports a comprehensive suite of tests including:
- Continuity Testing
- Power Supply Current Testing (Normal and Power-down modes)
- Leakage Current Testing
- Input Impedance Testing
- Linear Histogram Method for Code Edge Measurements
- Sinusoidal Histogram Method for Code Edge Measurements
- Offset and Offset Error Analysis
- Gain and Gain Error Analysis
- Missing Code Detection
- Integral Nonlinearity (INL) Analysis
- Differential Nonlinearity (DNL) Analysis
- Maximum Sampling Frequency Verification

## Hardware Specifications
### Device Under Test (DUT)
- **Target Device**: ADS7816
- **Features**: 
  - 200kHz sampling rate
  - Low power operation
  - Differential input
  - Serial interface
  - External reference and clock requirements
  - 5V power source operation

### Relay System
- **SPST-NO Relay**: G5NB-1A4 DC24
  - Power consumption: ~200mW
  - Operating current: ~8.3mA at 24V
  - Cost: $1.32

- **DPDT Relay**: J104D2C24VDC.15S
  - Power consumption: 150mW
  - Operating current: ~6.25mA at 24V
  - Cost: $1.21

## Software
The testbed includes a comprehensive suite of Python scripts for automated testing:
- `Combined_Hist_Tests.py`: Manages both linear and sinusoidal histogram testing
- `Continuity.py`: Performs continuity testing across all pins
- `InputImpedanceTest.py`: Measures input impedance characteristics
- `LeakageCurrents.py`: Tests for current leakage under various conditions
- `PwrSupplyCurrents.py`: Evaluates power supply current in different operating modes
- `Testing_Comb.py`: Main test orchestration script

## Getting Started
1. **Hardware Setup**:
   - Connect the VirtualBench device (VB8012-30DF182)
   - Apply 24V external power for relay control
   - Connect the DUT to the test board

2. **Software Requirements**:
   - Python 3.x
   - PyVirtualBench library
   - Required Python packages: numpy, matplotlib, tqdm, pandas

3. **Running Tests**:
   ```bash
   python Testing_Comb.py
