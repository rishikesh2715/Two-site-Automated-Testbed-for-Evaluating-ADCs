import numpy as np
import time
import matplotlib.pyplot as plt
from tqdm import tqdm
from pyvirtualbench import (
    PyVirtualBench, Polarity, ClockPhase, PyVirtualBenchException, Waveform, DmmFunction
)
import math


# Configuration Parameters
VB_DEVICE = "VB8012-30DF182"
BUS = f"{VB_DEVICE}/spi/0"
PWR_CHANNEL = "ps/+6V"
CLOCK_RATE = 200000 * 16
CHIP_SELECT_POLARITY = Polarity.IDLE_HIGH
CLOCK_PHASE = ClockPhase.FIRST_EDGE
CLOCK_POLARITY = Polarity.IDLE_LOW

WAVE_TYPE = Waveform.DC
AMPLITUDE = 5 #Amplitude shown in Pk-2-Pk Voltage. Actual peak voltage is 2.5 V
FREQ = 1.0  # Hz
DUTY_CYCLE = 50.0  # %
DC_OFFSET = 5.0

SAMPLE_COUNT = 500
VREF = 5.0  # Reference voltage in Volts
HITS_PER_VALUE = 1
VLSB = VREF/4094

PEAK = AMPLITUDE


def run_Leakage_low(dmm):
    total = 0
    for _ in range(50):
        total += dmm.read()
    leakage_curr = total / 50
    return leakage_curr

def run_Leakage_high(dmm):
    total = 0
    for _ in range(50):
        total += dmm.read()
    leakage_curr = total / 50
    return leakage_curr

if __name__ == "__main__":
    try:
        vb = PyVirtualBench(VB_DEVICE)
        fgen = vb.acquire_function_generator()
        fgen.configure_standard_waveform(WAVE_TYPE, AMPLITUDE, DC_OFFSET, FREQ, DUTY_CYCLE)
        dmm = vb.acquire_digital_multimeter()
        dmm.configure_measurement(DmmFunction.DC_CURRENT, True, 0.1)
        pwr_sup = vb.acquire_power_supply()
        pwr_sup.enable_all_outputs(True)
        pwr_sup.configure_voltage_output(PWR_CHANNEL, VREF, 0.5)
        input("prep for low leakage test...")
        leakage_curr_low = run_Leakage_low(dmm)

        input("prep for High leakage test...")
        fgen.run()
        leakage_curr_high = run_Leakage_high(dmm)

        fgen.stop()
        print(f"Results for low input voltage: {leakage_curr_low * 1000} mA")
        print(f"Results for high input voltage: {leakage_curr_high * 1000} mA")


    except:
        pass
    dmm.release()
    pwr_sup.enable_all_outputs(False)
    pwr_sup.release()
    fgen.release()
    vb.release()