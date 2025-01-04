import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
from pyvirtualbench import (
    PyVirtualBench, Polarity, ClockPhase, PyVirtualBenchException, Waveform
)

# Configuration Parameters
VB_DEVICE = "VB8012-30DF182"
BUS = f"{VB_DEVICE}/spi/0"
PWR_CHANNEL = "ps/+6V"
CLOCK_RATE = 200000 * 16
CHIP_SELECT_POLARITY = Polarity.IDLE_HIGH
CLOCK_PHASE = ClockPhase.FIRST_EDGE
CLOCK_POLARITY = Polarity.IDLE_LOW

WAVE_TYPE = Waveform.DC
AMPLITUDE = 0.0
FREQ = 400.0  # Hz
DUTY_CYCLE = 50.0  # %
DC_OFFSET = 0.00

VREF = 5.0  # Reference voltage in Volts
HITS_PER_VALUE = 1
STEP_SIZE = 0.0002  # 0.1 mV step size
VLSB = VREF/4094


def generate_voltage_steps():
    """Generate expected voltage values for ascending and descending ramps."""
    num_steps = int(VREF / STEP_SIZE) + 1
    up = [i * STEP_SIZE * 1000 for i in range(num_steps)]
    down = [(num_steps - i - 1) * STEP_SIZE * 1000 for i in range(num_steps)]
    return up, down

def initialize_virtualbench():
    """Initialize VirtualBench and acquire resources."""
    vb = PyVirtualBench(VB_DEVICE)
    fgen = vb.acquire_function_generator()
    spi = vb.acquire_serial_peripheral_interface(BUS)
    return vb, fgen, spi

def configure_instruments(fgen, spi):
    """Configure power supply, function generator, and SPI interface."""
    spi.configure_bus(CLOCK_RATE, CLOCK_POLARITY, CLOCK_PHASE, CHIP_SELECT_POLARITY)
    fgen.configure_standard_waveform(WAVE_TYPE, AMPLITUDE, DC_OFFSET, FREQ, DUTY_CYCLE)
    fgen.run()

def perform_measurement(spi, fgen, voltage_mv, output_codes_list):
    """Perform a single ADC measurement."""
    dc_offset = voltage_mv / 1000.0  # Convert mV to V
    fgen.configure_standard_waveform(WAVE_TYPE, AMPLITUDE, dc_offset, FREQ, DUTY_CYCLE)

    total = 0
    for _ in range(HITS_PER_VALUE):
        read = spi.write_read([0xFF, 0x00], 2, 2)
        masked_upper = read[0] & 0x1F
        merged = (masked_upper << 8) | read[1]
        merged = merged >> 1
        total += merged

    averaged_code = np.round(total / HITS_PER_VALUE)
    #averaged_code = np.round(((1+0.000663 -0.000138)*(total/HITS_PER_VALUE))+(-7.991106-1.264181))
    output_codes_list.append(averaged_code)

def cleanup_instruments(vb, fgen, spi):
    """Release and reset all instruments."""
    try:
        fgen.stop()
        fgen.release()
        spi.release()
        vb.release()
    except Exception as e:
        print(f"Error during cleanup: {e}")

def calculate_best_fit_inl_dnl(inl):
    """Calculate best-fit INL and DNL using linear regression."""
    codes = np.arange(len(inl))
    best_fit = np.polyfit(codes, inl, 1)  # Linear regression
    gain, offset = best_fit
    best_fit_func = gain * codes + offset

    best_fit_inl = inl - best_fit_func
    best_fit_dnl = np.diff(best_fit_inl, prepend=0)

    return best_fit_inl, best_fit_dnl, gain, offset

def calculate_metrics(output_codes_up, output_codes_down, up):
    """Calculate metrics: Combined Codes, Code Widths, INL/DNL."""
    output_codes_down.reverse()
    combined_codes = [(up + down) // 2 for up, down in zip(output_codes_up, output_codes_down)]
    print(len(combined_codes))
    print(len(range(0,int(VREF/STEP_SIZE))))
    ideal_gain, ideal_offset = np.polyfit(range(0,int(VREF/STEP_SIZE) + 1), up, 1)
    #actual_gain, actual_offset = np.polyfit(range(0,int(VREF/STEP_SIZE) + 1), combined_codes, 1)
    #print(f"Ideal Gain of the Transfer Curve: {ideal_gain}")
    #print(f"Ideal Offset of the Transfer Curve: {ideal_offset}")
    hits = [0] * 4096
    for code in combined_codes:
        hits[int(code)] += 1

    avg_hits = sum(hits) / (4096 - 2)
    cw_combined = [hit / avg_hits for hit in hits[1:-1]]
    avg_code_width = np.mean(cw_combined)


    dnl = [cw - 1 for cw in cw_combined]
    inl = np.cumsum(dnl)

    best_fit_inl, best_fit_dnl, gain, offset = calculate_best_fit_inl_dnl(inl)
    avg_best_fit_inl = np.mean(np.abs(best_fit_inl))
    avg_best_fit_dnl = np.mean(np.abs(best_fit_dnl))

    avg_volts_per_code = VREF / 4096 * avg_code_width

    return (combined_codes, cw_combined, dnl, inl, best_fit_inl, best_fit_dnl, 
            gain, offset, avg_code_width, avg_volts_per_code, avg_best_fit_inl, avg_best_fit_dnl, ideal_gain, ideal_offset)

def print_metrics(gain, offset, avg_code_width, avg_volts_per_code, avg_best_fit_inl, avg_best_fit_dnl, ideal_gain, ideal_offset):
    """Print calculated metrics."""
    #print(f"Actual Gain of the Transfer Curve: {actual_gain}")
    #print(f"Actual Offset of the Transfer Curve: {actual_offset}")
    #gain_error = 100*((gain/ideal_gain) - 1)
    #offset_error = 100*((offset/ideal_offset) - 1)
    
    print(f"Gain (Best-Fit Slope): {gain:.6f} LSBs")
    print(f"Offset (Best-Fit Intercept): {offset:.6f} LSBs")
    #print(f"Gain Error: {gain_error} %")
    #print(f"Offset Error: {offset_error} %")
    print(f"Average Code Width: {avg_code_width:.6f} LSBs")
    print(f"Average Volts per Code: {avg_volts_per_code:.6f} V")
    print(f"Average Best-Fit INL: {avg_best_fit_inl:.6f} LSBs")
    print(f"Average Best-Fit DNL: {avg_best_fit_dnl:.6f} LSBs")

def plot_inl_dnl(inl, dnl, best_fit_inl, best_fit_dnl):
    """Plot INL and DNL curves with best-fit lines."""
    plt.figure(figsize=(14, 6))
    plt.plot(inl, label='Endpoint INL (LSBs)', color='blue')
    plt.plot(best_fit_inl, label='Best-Fit INL (LSBs)', linestyle='--', color='green')
    plt.title('INL Curve')
    plt.xlabel('Output Code')
    plt.ylabel('INL (LSBs)')
    plt.legend()
    plt.grid(True)
    plt.show()

    plt.figure(figsize=(14, 6))
    plt.plot(dnl, label='Endpoint DNL (LSBs)', color='red')
    plt.plot(best_fit_dnl, label='Best-Fit DNL (LSBs)', linestyle='--', color='orange')
    plt.title('DNL Curve')
    plt.xlabel('Output Code')
    plt.ylabel('DNL (LSBs)')
    plt.legend()
    plt.grid(True)
    plt.show()

def plot_transfer_curve(expected, combined, ideal):
    """Plot the transfer curve with the ideal line."""
    plt.figure(figsize=(14, 8))
    plt.plot(expected, combined, linestyle='-', label='Combined Measured Output')
    plt.step(expected, ideal, where='post', linestyle='--', label='Ideal Transfer Line')
    plt.title('Transfer Curve of the ADC')
    plt.xlabel('Input Voltage (mV)')
    plt.ylabel('Output Code')
    plt.legend()
    plt.grid(True)
    plt.show()

def plot_code_width_histogram(cw_combined):
    """Plot histogram of code widths."""
    plt.figure(figsize=(14, 6))
    plt.bar(range(len(cw_combined)), cw_combined, color='blue', alpha=0.7, edgecolor='black')
    plt.title('Code Width Histogram')
    plt.xlabel('Output Code')
    plt.ylabel('Code Width (LSBs)')
    plt.grid(True)
    plt.show()

def plot_code_edges(cw_combined):
    """Plot code edges with output code on the x-axis and voltage on the y-axis."""
    v_cw = [0] * 4094
    v_cw_ideal = [0] * 4094
    for i in range(1, 2**12 - 2):
        v_cw[i] = VLSB * cw_combined[i]
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


def run_linear():
    expected_voltage_values_up = []
    expected_voltage_values_down = []
    output_codes_up = []
    output_codes_down = []
    expected_voltage_values_up, expected_voltage_values_down = generate_voltage_steps()

    vb = None
    try:
        vb, fgen, spi = initialize_virtualbench()
        configure_instruments(fgen, spi)
        ideal_transfer_line = [int((v / 1000.0) * (4096 / VREF)) for v in expected_voltage_values_up]
        for voltage_mv in tqdm(expected_voltage_values_up, desc="Ascending Ramp"):
            perform_measurement(spi, fgen, voltage_mv, output_codes_up)

        for voltage_mv in tqdm(expected_voltage_values_down, desc="Descending Ramp"):
            perform_measurement(spi, fgen, voltage_mv, output_codes_down)

        (combined_codes, cw_combined, dnl, inl, best_fit_inl, best_fit_dnl, 
         gain, offset, avg_code_width, avg_volts_per_code, 
         avg_best_fit_inl, avg_best_fit_dnl, ideal_gain, ideal_offset) = calculate_metrics(output_codes_up, output_codes_down, ideal_transfer_line)

        print_metrics(gain, offset, avg_code_width, avg_volts_per_code, avg_best_fit_inl, avg_best_fit_dnl, ideal_gain, ideal_offset)
        #return (cw_combined, best_fit_inl, best_fit_dnl, inl, dnl, v_ce_combined)
        plot_transfer_curve(expected_voltage_values_up, combined_codes, ideal_transfer_line)
        plot_inl_dnl(inl, dnl, best_fit_inl, best_fit_dnl)
        plot_code_width_histogram(cw_combined)
        plot_code_edges(cw_combined)

    except KeyboardInterrupt:
        print("Measurement interrupted by user.")
    except PyVirtualBenchException as e:
        print(f"PyVirtualBench error: {e}")
    finally:
        if vb:
            cleanup_instruments(vb, fgen, spi)

if __name__ == "__main__":
    run_linear()
