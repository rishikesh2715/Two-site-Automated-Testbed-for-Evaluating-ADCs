import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
from pyvirtualbench import (
    PyVirtualBench, Polarity, ClockPhase, PyVirtualBenchException, Waveform
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

SAMPLE_COUNT = (2**12) * 32 #getting 32 samples per ADC code (16 is a good minimum)
VREF = 5.0  # Reference voltage in Volts
HITS_PER_VALUE = 1
VLSB = VREF/4094

PEAK = AMPLITUDE

output_codes = []

def initialize_virtualbench():
    """Initialize VirtualBench and acquire resources."""
    vb = PyVirtualBench(VB_DEVICE)
    fgen = vb.acquire_function_generator()
    spi = vb.acquire_serial_peripheral_interface(BUS)
    return vb, fgen, spi

def configure_instruments(fgen, spi):
    """Configure power supply, function generator, and SPI interface."""
    spi.configure_bus(CLOCK_RATE, CLOCK_POLARITY, CLOCK_PHASE, CHIP_SELECT_POLARITY)
    #pwr_sup.enable_all_outputs(True)
    #pwr_sup.configure_voltage_output(PWR_CHANNEL, VREF, 0.5)
    #pwr_sup.configure_voltage_output("ps/+25V", 5, 0.5)
    fgen.configure_standard_waveform(WAVE_TYPE, AMPLITUDE, DC_OFFSET, FREQ, DUTY_CYCLE)
    fgen.run()

def perform_measurement(spi, output_codes_list):
    """Perform a single ADC measurement."""
    total = 0
    for _ in range(HITS_PER_VALUE):
        read = spi.write_read([0xFF, 0x00], 2, 2)
        masked_upper = read[0] & 0x1F
        merged = (masked_upper << 8) | read[1]
        merged = merged >> 1
        total += merged
    
    averaged_code = np.floor((total / HITS_PER_VALUE))
    
    output_codes_list.append(averaged_code)

def get_dnl_inl(cw_LSB):
    inl = [0] * 4096
    total = 0
    dnl = []
    for i in range(1, 4094):
        dnl.append(cw_LSB[i] - 1)
    inl[1] = 0   
    for i in range(1, min(len(dnl) + 1, 4094)):
        total = sum(dnl[:i]) 
        inl[i] = total
    inl[4095] = 0
    codes = []
    for i in range(4096):
        codes.append(i)
    gain, offset = np.polyfit(codes, inl, 1)
    #print(f"Calculated Gain : {gain} LSBs")
    #print(f"Calculated Offset: {offset} LSBs")

    best_fit_endINL_func = [0]
    for i in range(1, 4095):
        best_fit_endINL_func.append((gain*i) + offset)
        #best_fit_endINL_func.append((gain*i) + offset)
    best_fit_inl = []
    for i in range(1, 4095):
        best_fit_inl.append(inl[i] - best_fit_endINL_func[i])
    
    best_fit_dnl = []
    for i in range(1, 4094):
        best_fit_dnl.append(best_fit_inl[i] - best_fit_inl[i-1])

    print(f"Average DNL (Best-Fit): {sum(best_fit_dnl)/len(best_fit_dnl)} LSBs")
    print(f"Average INL (Best-Fit): {sum(best_fit_inl)/len(best_fit_inl)} LSBs")

    return best_fit_inl, best_fit_dnl, inl, dnl

    
def cleanup_instruments(fgen, spi):
    """Release and reset all instruments."""
    try:
        fgen.stop()
        fgen.release()
        spi.release()
        #vb.release()
    except Exception as e:
        print(f"Error during cleanup: {e}")

def get_ideal_sin_hits(peak):
    hits_sine = [0] * 4096
    VFS = 5.0
    N=12

    for i in range(1,4096):
        hits_sine[i] = ((SAMPLE_COUNT/math.pi)*(math.asin((VFS*(i-((2**(N-1)))))/(peak*(2**N))) - math.asin((VFS*((i - 1) - ((2**(N-1)))))/(peak*(2**N)))))
    return hits_sine

def get_code_width_hist(output_codes):
    cw_LSB = [0] * 4096
    hits = [0] * 4096
    peak = 0
    offset = 0
    c1 = 0
    c2 = 0
    for i in range(len(output_codes)):
        #if(output_codes[i] > 4095):
            #output_codes[i] = 4095
        hits[int(output_codes[i])] += 1
    c1 = math.cos(math.pi * (hits[4095]/SAMPLE_COUNT))
    c2 = math.cos(math.pi * (hits[0]/SAMPLE_COUNT))
    peak = (2/(c2 + c1)) * ((2**11)-1) * VLSB
    offset = ((c2 - c1)/(c2 + c1)) * ((2**11)-1) * VLSB
    print(f"Peak Voltage: {peak} V")
    print(f"Offset: {offset} V")

    hits_sine = get_ideal_sin_hits(peak)
    hits_sine[0] = hits[0]
    hits_sine[4095] = hits[4095]
    print(min(hits_sine))
    print(max(hits_sine))
    for i in range(1, 4094):
        cw_LSB[i] = abs(hits[i]/hits_sine[i]) 
    print(f"Average code width (LSBs): {sum(cw_LSB)/len(cw_LSB)}")
    return cw_LSB 

def get_code_edges(cw_LSB):
    v_cw = [0] * 4094
    v_cw_ideal = [0] * 4094
    for i in range(1, 2**12 - 2):
        v_cw[i] = VLSB * cw_LSB[i]
        v_cw_ideal[i] = VLSB * 1
    v_ce = [0] * 4096
    v_ce_ideal = [0] * 4096
    for i in range(1, 4094):
        total = 0
        total_ideal = 0
        for j in range(i):
            total += v_cw[j]
            total_ideal += v_cw_ideal[j] 
        v_ce[i] = total
        v_ce_ideal[i] = total_ideal

    print(f"Average Volts per LSB: {sum(v_cw)/len(v_cw)} V")
    return v_ce, v_ce_ideal

def plot_output_codes(output_codes):
    """Plot the collected ADC output codes."""
    plt.figure(figsize=(10, 6))
    plt.plot(output_codes[0:4096], marker=None, linestyle='-', markersize=4)
    plt.title('ADC Output Codes')
    plt.xlabel('Sample Number')
    plt.ylabel('ADC Output Code')
    plt.grid(True)
    plt.show()

def plot_code_width_histogram(cw_LSB):
    """Plot a histogram of the code widths for each ADC code."""
    plt.figure(figsize=(12, 6))
    
    # Plotting the code widths vs. code values (0 to 4095).
    plt.bar(range(4096), cw_LSB, width=1.0, edgecolor='black')
    
    plt.title('Code Widths for Each ADC Code')
    plt.xlabel('ADC Code')
    plt.ylabel('Code Width (LSBs)')
    plt.grid(True, linestyle='--', alpha=0.7)

    plt.show()

def plot_inl(inl, best_fit_inl):
    """Plot end INL and best-fit INL on the same plot."""
    plt.figure(figsize=(12, 6))

    plt.plot(inl, label='End INL', linestyle='-', marker=None)
    plt.plot(best_fit_inl, label='Best-Fit INL', linestyle='--', marker=None)

    plt.title('INL (Integral Non-Linearity)')
    plt.xlabel('ADC Code')
    plt.ylabel('INL (LSBs)')
    plt.legend(loc='best')
    plt.grid(True, linestyle='--', alpha=0.7)

    plt.show()

def plot_dnl(dnl, best_fit_dnl):
    """Plot end DNL and best-fit DNL on the same plot."""
    plt.figure(figsize=(12, 6))

    plt.plot(dnl, label='End DNL', linestyle='-', marker=None)
    plt.plot(best_fit_dnl, label='Best-Fit DNL', linestyle='--', marker=None)

    plt.title('DNL (Differential Non-Linearity)')
    plt.xlabel('ADC Code')
    plt.ylabel('DNL (LSBs)')
    plt.legend(loc='best')
    plt.grid(True, linestyle='--', alpha=0.7)

    plt.show()

def plot_code_edges(v_ce, v_ce_ideal):
    """Plot code edges with output code on the x-axis and voltage on the y-axis."""
    gain, offset = np.polyfit(range(4096), v_ce, 1)
    gain_ideal, offset_ideal = np.polyfit(range(4096), v_ce_ideal, 1)
    print(f"Actual gain and offset: {gain} , {offset}")
    print(f"Ideal gain and offset: {gain_ideal} , {offset_ideal}")
    print(f"Gain Error: {100*(abs(gain_ideal - gain)/gain)} %")
    print(f"Offset Error: {100*(abs(offset_ideal - offset)/offset)} %")
    plt.figure(figsize=(12, 6))
    
    # Plotting actual and ideal voltage at each code edge vs. output code.
    plt.plot(range(4096), v_ce, label="Measured V_ce", linestyle='-', marker=None)
    plt.plot(range(4096), v_ce_ideal, label="Ideal V_ce", linestyle='--', marker=None)

    plt.title('Code Edges: Voltage vs. Output Code')
    plt.xlabel('Output Code')
    plt.ylabel('Voltage (V)')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)

    plt.show()

def run_Sine():
    #global ced_voltage_values_up, expected_voltage_values_down
    #expected_voltage_values_up, expected_voltage_values_down = generate_voltage_steps()
    cw_LSB = []
    bfDNL = []
    bfINL = []
    endDNL = []
    endINL = []
    v_ce = []
    v_ce_ideal = []
    vb = None
    try:
        vb, fgen, spi = initialize_virtualbench()
        configure_instruments(fgen, spi)

        for _ in tqdm(range(SAMPLE_COUNT), desc="Measuring Sine...", unit=" Samples"):
            perform_measurement(spi, output_codes)
        cw_LSB = get_code_width_hist(output_codes)
        bfINL, bfDNL, endINL, endDNL = get_dnl_inl(cw_LSB)
        v_ce, v_ce_ideal = get_code_edges(cw_LSB)
        plot_output_codes(output_codes)
        plot_code_width_histogram(cw_LSB)
        plot_inl(endINL,bfINL)
        plot_dnl(endDNL, bfDNL)
        plot_code_edges(v_ce, v_ce_ideal)
    except KeyboardInterrupt:
        print("Measurement interrupted by user.")
    except PyVirtualBenchException as e:
        print(f"PyVirtualBench error: {e}")
    finally:
        if vb:
            cleanup_instruments(fgen, spi)

if __name__ == "__main__":
    run_Sine()
