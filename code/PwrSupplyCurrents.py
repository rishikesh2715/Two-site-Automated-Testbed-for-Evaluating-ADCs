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

WAVE_TYPE = Waveform.SINE
AMPLITUDE = 5 #Amplitude shown in Pk-2-Pk Voltage. Actual peak voltage is 2.5 V
FREQ = 1.0  # Hz
DUTY_CYCLE = 50.0  # %
DC_OFFSET = 2.5

SAMPLE_COUNT = 500
VREF = 5.0  # Reference voltage in Volts
HITS_PER_VALUE = 1
VLSB = VREF/4094

PEAK = AMPLITUDE

WRITE_CHANNELS = f"{VB_DEVICE}/dig/3:3"


def initialize_virtualbench():
    """Initialize VirtualBench and acquire resources."""
    vb = PyVirtualBench(VB_DEVICE)
    #pwr_sup = vb.acquire_power_supply()
    fgen = vb.acquire_function_generator()
    spi = vb.acquire_serial_peripheral_interface(BUS)
    dmm = vb.acquire_digital_multimeter()
    dmm.configure_measurement(DmmFunction.DC_CURRENT, True, 0.1)
    return fgen, spi, dmm

def configure_instruments(pwr_sup, fgen, spi):
    """Configure power supply, function generator, and SPI interface."""
    spi.configure_bus(CLOCK_RATE, CLOCK_POLARITY, CLOCK_PHASE, CHIP_SELECT_POLARITY)
    pwr_sup.enable_all_outputs(True)
    pwr_sup.configure_voltage_output(PWR_CHANNEL, VREF, 0.5)
    #pwr_sup.configure_voltage_output("ps/+25V", 5, 0.5)
    fgen.configure_standard_waveform(WAVE_TYPE, AMPLITUDE, DC_OFFSET, FREQ, DUTY_CYCLE)
    #fgen.run()

def run_measurement(spi, dmm):
    total = 0
    for _ in range(SAMPLE_COUNT):
        read = spi.write_read([0xFF, 0x00], 2, 2)
        #volt, curr, _ = pwr_sup.read_output(PWR_CHANNEL)
        curr = dmm.read()
        total += curr * 1000
    return total/SAMPLE_COUNT

def run_idle(dmm):
    total = 0
    for _ in range(SAMPLE_COUNT):
        #volt, curr, _ = pwr_sup.read_output(PWR_CHANNEL)
        curr = dmm.read()
        #print(curr)
        total += curr * 1000
    return total/SAMPLE_COUNT

def run_shutdown(dio, dmm):
    dio.write(WRITE_CHANNELS, [1])
    total = 0
    for _ in range(SAMPLE_COUNT):
        #volt, curr, _ = pwr_sup.read_output(PWR_CHANNEL)
        curr = dmm.read()
        #print(curr)
        total += curr * 1000
    return total/SAMPLE_COUNT

def main():
    try:
        print("Starting Power Supply Current Testing....")
        vb, pwr_sup, fgen, spi, dmm = initialize_virtualbench()
        configure_instruments(pwr_sup, fgen, spi)
        time.sleep(5)
        print("Starting Idle Current Measurements...")
        idle_currents = run_idle(dmm)
        print(f"At {VREF} V the chip draws an average of {idle_currents:.4f} mA, or {round((VREF * (idle_currents/ 1000)) * 1000, 4)} mW")
        time.sleep(2)
        print("Starting measurements while under load....")
        fgen.run()
        running_currents = run_measurement(spi, dmm)
        print(f"Under load at {VREF} V, the chip draws an average of {running_currents:.4f} mA ({round((VREF * (idle_currents/ 1000)) * 1000, 4)} mW)" )
        fgen.stop()
        spi.reset_instrument()
        spi.release()
        dio = vb.acquire_digital_input_output(WRITE_CHANNELS)
        dio.write(WRITE_CHANNELS, [1])
        time.sleep(5)
        print("Running Shutdown Current Test....")
        shutdown_currents  = run_shutdown(dio, dmm)
        print(f"Under Shutdown at {VREF} V, the chip draws an average of {shutdown_currents:.4f} mA ({round((VREF * (shutdown_currents/ 1000)) * 1000, 4)} mW)")
        dio.release()



    except KeyboardInterrupt:
        pass

    except Exception as e:
        print(e)

    pwr_sup.enable_all_outputs(False)
    pwr_sup.release()
    #spi.reset_instrument()
    #spi.release()
    #fgen.stop()
    fgen.release()
    vb.release()