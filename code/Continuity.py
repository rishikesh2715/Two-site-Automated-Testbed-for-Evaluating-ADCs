from pyvirtualbench import PyVirtualBench, DmmFunction, PyVirtualBenchException
from time import sleep
import matplotlib.pyplot as plt
import numpy as np


# VB8012-30DF182
vb = PyVirtualBench("VB8012-30DF182")

pwr_channel = "ps/+6V"
resistor = 1.0
dut_pass = False
pin_count = 4  # Leave as 1 for single pin testing. Adjust for number of pins if testing in parallel.


def find_diode_voltage(vin, i):
    if i < 0.001:
        return 0
    V_diode = vin - (resistor * i)
    return V_diode


def test_single_pin(pwr_sup):
    global dut_pass
    for i in range(700, 800, 1):
        actual_voltage, actual_current, _ = pwr_sup.read_output(pwr_channel)
        DV = find_diode_voltage(actual_voltage, actual_current)
        if (actual_current * 1000) >= 1:
            print(f"Found Diode Voltage (Single): {DV * 1000} mV")
            print(f"Voltage Input: {actual_voltage * 1000} mV")
            print(f"Current Draw: {actual_current * 1000} mA")
            dut_pass = True
            break
        pwr_sup.configure_voltage_output(pwr_channel, i / 1000, 1)
        sleep(0.1)
    return actual_voltage, actual_current * 1000, DV * 1000


def test_all_pins(pwr_sup, single_pin_voltage):
    global dut_pass
    err = 0.15 * pin_count
    pwr_sup.configure_voltage_output(pwr_channel, single_pin_voltage, 1)
    sleep(2)
    full_voltage, full_current, _ = pwr_sup.read_output(pwr_channel)
    if (pin_count - err) < (full_current * 1000) < (pin_count + err):
        dut_pass = True
        DV = find_diode_voltage(full_voltage, full_current)
        return full_voltage, full_current * 1000, DV
    else:
        dut_pass = False
        return full_voltage, full_current * 1000, 0

def main():
    try:
        pwr_sup = vb.acquire_power_supply()
        pwr_sup.enable_all_outputs(True)

        # Wait for key press before starting the test
        input("Press Enter to start testing single pin...")

        v, i, VD = test_single_pin()
        if not dut_pass:
            print("Device Did not Pass Single-Pin Continuity Test! Check All Connections")
        else:
            print(f"Single Pin Results: Passed!\r\nInput Voltage: {v * 1000} mV\r\nFound Current Value: {i} mA\r\nFound Diode Voltage: {VD} mV")

            # Wait for key press before proceeding with the parallel test
            input("Press Enter to continue testing all pins...")

            sleep(5)
            v_full, i_full, VD = test_all_pins(v)
            if not dut_pass:
                print(f"Device Did not Pass Full Parallel Continuity Tests! Check All Connections. Results: \r\nInput Voltage: {v_full * 1000} mV\r\nFound Current Value: {i_full} mA")
            else:
                print(f"Full Parallel Results: Passed!\r\nInput Voltage: {v_full * 1000} mV\r\nFound Current Value: {i_full } mA\r\nFound Diode Voltage: {VD} mV")

    except PyVirtualBenchException as e:
        print(e)
    except KeyboardInterrupt:
        pass
    finally:
        pwr_sup.configure_voltage_output(pwr_channel, 0, 0.1)
        
        pwr_sup.enable_all_outputs(False)
        pwr_sup.release()
        vb.release()
