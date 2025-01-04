from pyvirtualbench import PyVirtualBench, DmmFunction, Waveform, PyVirtualBenchException
from time import sleep
import numpy as np


# VB8012-30DF182

VB_DEVICE = "VB8012-30DF182"
pwr_channel_1 = "ps/+6V"

WAVE_TYPE = Waveform.DC
AMPLITUDE = 0.0
FREQ = 400.0  # Hz
DUTY_CYCLE = 50.0  # %
DC_OFFSET = 0.00

VREF = 5.0  # Reference voltage in Volts
currents = []


def initialize_virtualbench():
    """Initialize VirtualBench and acquire resources."""
    vb = PyVirtualBench(VB_DEVICE)
    fgen = vb.acquire_function_generator()
    dmm = vb.acquire_digital_multimeter()
    dmm.configure_measurement(DmmFunction.DC_CURRENT, True, 0.1)
    return fgen, dmm

def run_input_impedace(fgen, dmm):
    total = 0
    fgen.configure_standard_waveform(WAVE_TYPE, AMPLITUDE, 0.1, FREQ, DUTY_CYCLE)
    fgen.run()
    sleep(2)
    for i in range(50):
        total += dmm.read()
    current_init = total / 50
    fgen.configure_standard_waveform(WAVE_TYPE, AMPLITUDE, 5.0, FREQ, DUTY_CYCLE)
    sleep(2)
    total = 0
    for i in range(50):
        total += dmm.read()
    current_final = total / 50
    fgen.stop()
    print(f"Current at 0.1V: {current_init}")
    print(f"Current at 5.0 V: {current_final}")
    return (5.0 - 0.1) / (current_final - current_init)


def main():
    try:
        vb, pwr_sup, fgen, dmm = initialize_virtualbench()

        pwr_sup.enable_all_outputs(True)
        pwr_sup.configure_voltage_output(pwr_channel_1, 5, 1)
        sleep(5)
        for i in range(3):
            Z = run_input_impedace(fgen, dmm)
            print(f"Found Input Impedace for pin {i}: {Z / 1000000} MΩ")
            input("Press Enter to continue to the next measurement...")
    except PyVirtualBenchException as e:
        print(e)
    except KeyboardInterrupt:
        print("User Exit. ")


    pwr_sup.enable_all_outputs(False)
    pwr_sup.configure_voltage_output(pwr_channel_1, 0.1, 0.5)
    pwr_sup.release()
    dmm.release()
    fgen.release()
    vb.release()
