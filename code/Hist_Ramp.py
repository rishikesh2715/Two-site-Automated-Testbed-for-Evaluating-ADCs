from pyvirtualbench import (
    PyVirtualBench,
    Polarity,
    ClockPhase,
    PyVirtualBenchException,
    Waveform
)
from time import sleep
import matplotlib.pyplot as plt
from tqdm import tqdm  # For progress bars
import pandas as pd   # For data logging (optional)
import numpy as np

# Configuration Parameters
bus = "VB8012-30DF182/spi/0"
pwr_channel_1 = "ps/+6V"
clock_rate = 200000 * 16
chip_select_polarity = Polarity.IDLE_HIGH
clock_phase = ClockPhase.FIRST_EDGE
clock_polarity = Polarity.IDLE_LOW

# Function Generator Configuration
wave_type = Waveform.DC
amplitude = 0.0        # P-2-P Voltage, adjust as needed
freq = 400.0           # Frequency in Hz, not critical for DC but required by the API
duty_cycle = 50.0      # Duty Cycle in %, irrelevant for DC but required by the API
dc_offset = 0.00

# Measurement Parameters
vRef = 5.0             # Reference voltage in Volts
hits_per_value = 1     # Number of ADC readings per voltage step (set to 1)
step_size = 0.0001     # 0.0001 V = 0.1 mV step size
expected_voltage_values_up = []
expected_voltage_values_down = []
output_codes_up = []
output_codes_down = []
v_avg_cw = vRef/(2**12 - 2)

def get_avg_hits(output_codes):
    D = 12  # Assuming 12-bit resolution, adjust if needed
    hits = [0] * (2**D)

    # Iterate over each possible output code
    for i in range(2**D):
        for j in range(1, len(output_codes) - 1):  # Exclude 0 and 4095
            if i == output_codes[j]:  # Matches the output code
                hits[i] += 1

    # Calculate average hits using the provided equation
    total_hits = sum(hits[1:-1])  # Exclude the first and last values (hits[0] and hits[4095])
    avg_hits = total_hits / (2**D - 2)  # Normalize by (2^D - 2)

    return avg_hits, hits

def get_code_width(avg_hits, hits):
    code_width = [0] * (2**12)
    for i in range(1,(2**12) - 2):
        code_width[i] = hits[i]/avg_hits
    #return code_width[1:-1]
    return code_width

def volts_per_code(code_width):
    v_cw = [0] * 4094
    for i in range(1, 2**12 - 2):
        v_cw[i] = v_avg_cw * code_width[i]
    return v_cw

def code_edge(v_cw):
    v_codeEdge = [0] * 4095
    for i in range(1, 4094):
        total = 0
        for j in range(i):
            total += v_cw[j]
        v_codeEdge[i] = int(1000*total)
    return v_codeEdge

def end_DNL(code_width):
    DNL = []
    for i in range(1, 4094):
        DNL.append(code_width[i] - 1)
    return DNL

def end_INL(DNL):
    INL = [0] * 4096
    INL[1] = 0   # Correct initialization
    for i in range(1, min(len(DNL) + 1, 4094)):  # Safe loop bound
        total = sum(DNL[:i])  # Use Python's sum() for clarity
        INL[i] = total
    INL[4095] = 0
    return INL

def avg_offset(codes, expected_values):
    offset = 0
    total = 0
    for i in range(len(codes)):
        total += (i/1000) - (expected_values[i]*(vRef/4096))/1000
    offset = total/len(codes)
    return offset

def get_Gain_Offset(samples):
    k1 = 0
    k2 = 0
    k3 = 0
    k4 = 0
    gain = 0
    offset = 0
    N = len(samples)
    for i in range(0, N - 1):
        k1 += i 
    for i in range(0, N - 1):
        k2 += samples[i]
    for i in range(0, N - 1):
        k3 += i*i
    for i in range(0, N - 1):
        k4 += i * samples[i]
    gain = ((N*k4) - (k1 * k2))/((N*k3) - (k1*k1))
    offset = (k2/N) - (gain *(k1/N))
    return gain, offset

# Populate expected voltage values for ascending ramp (0 V to vRef)
num_steps = int(vRef / step_size) + 1
print(f"Total steps per ramp: {num_steps}")

for i in range(num_steps):
    voltage_mv = i * step_size * 1000  # Convert to mV (0.0001 V * 1000 = 0.1 mV)
    expected_voltage_values_up.append(voltage_mv)

# Populate expected voltage values for descending ramp (vRef to 0 V)
for i in range(num_steps):
    voltage_mv = (num_steps - i - 1) * step_size * 1000  # Convert to mV
    expected_voltage_values_down.append(voltage_mv)

try:
    # Initialize PyVirtualBench
    vb = PyVirtualBench("VB8012-30DF182")
    
    # Acquire Power Supply and Function Generator
    pwr_sup = vb.acquire_power_supply()
    fgen = vb.acquire_function_generator()
    
    # Acquire SPI Interface
    spi = vb.acquire_serial_peripheral_interface(bus)
    spi.configure_bus(clock_rate, clock_polarity, clock_phase, chip_select_polarity)
    
    # Enable and configure power supplies
    pwr_sup.enable_all_outputs(True)
    pwr_sup.configure_voltage_output(pwr_channel_1, vRef, 0.5)
    
    # Configure Function Generator for DC output
    fgen.configure_standard_waveform(
        wave_type,
        amplitude,
        dc_offset,
        freq,
        duty_cycle
    )
    fgen.run()  # Start the Function Generator
    
    # Helper Function to Perform Measurements
    def perform_measurement(voltage_mv, output_codes_list):
        # Set the DC offset on the Function Generator (in Volts)
        dc_offset = voltage_mv / 1000.0  # Convert mV to V (0.0001 V * 1000 = 0.1 V)
        fgen.configure_standard_waveform(
            wave_type,
            amplitude,
            dc_offset,
            freq,
            duty_cycle
        )
        # Optional: Implement a dynamic stabilization check here
        #sleep(0.02)  # Wait for the voltage to stabilize
        total = 0
        numavg = 1
        for _ in range(numavg):
        # Collect a single ADC reading
            read = spi.write_read([0xFF, 0x00], 2, 2)
            masked_upper = read[0] & 0x1F
            merged = (masked_upper << 8) | read[1]
            merged = merged >> 1
            total += merged
        averaged_adc_code = np.round(((total / numavg)) + (-8.205275541856743) + (-1.0807953287039676) + (0.0012149353789482765 * ((total / numavg)))) 
        #averaged_adc_code = merged
        # Append the raw output code
        output_codes_list.append(averaged_adc_code)
    
    # Perform measurements for ascending ramp with progress bar
    print("Starting ascending voltage ramp measurements...")
    for voltage_mv in tqdm(expected_voltage_values_up, desc="Ascending Ramp", unit="step"):
        perform_measurement(voltage_mv, output_codes_up)
    
    # Perform measurements for descending ramp with progress bar
    print("Starting descending voltage ramp measurements...")
    for voltage_mv in tqdm(expected_voltage_values_down, desc="Descending Ramp", unit="step"):
        perform_measurement(voltage_mv, output_codes_down)
    
    # Create ideal transfer line
    ideal_transfer_line = [
        int((v / 1000.0) * (4096 / vRef)) for v in expected_voltage_values_up
    ]
    
    hits = []

    output_codes_down.reverse()
    combined_codes = []
    for i in range(len(output_codes_up)):
        combined = int((output_codes_down[i] + output_codes_up[i]) / 2)
        combined_codes.append(combined)

    offset_avg = avg_offset(combined_codes, expected_voltage_values_up)
    print(f"Average Offset: {offset_avg} mV")
    gain, offset = get_Gain_Offset(combined_codes)
    print(f"Gain (using K vals): {gain} LSBs\r\nOffset (using K vals): {offset} LSBs")
    avghits, hits = get_avg_hits(combined_codes)
    #avghits_down, hits = get_avg_hits(output_codes_down)
    #print(avghits_up)
    cw_combined = get_code_width(avghits, hits)
    #cw_down = get_code_width(avghits_down, hits)
    cw_avg = sum(cw_combined)/len(cw_combined)
    print(f"Average Code Width (in LSBs): {cw_avg}")
    v_cw_combined = volts_per_code(cw_combined)
    v_cw_avg = sum(v_cw_combined)/len(v_cw_combined)
    print(f"Average Volts per Code: {v_cw_avg}")
    v_ce_combined = code_edge(v_cw_combined)
    endDNL = end_DNL(cw_combined)
    endINL = end_INL(endDNL)
    codes = []
    for i in range(4096):
        codes.append(i)
    
    best_fit_endINL = np.polyfit(codes, endINL, 1)
    print(f"Calculated Gain (numpy regression line): {best_fit_endINL[0]} LSBs")
    print(f"Calculated Offset (numpy regression line): {best_fit_endINL[1]} LSBs")
    best_fit_endINL_func = [0]
    for i in range(1, 4095):
        best_fit_endINL_func.append((best_fit_endINL[0]*i) + best_fit_endINL[1])
        #best_fit_endINL_func.append((gain*i) + offset)
    best_fit_INL = []
    for i in range(1, 4095):
        best_fit_INL.append(endINL[i] - best_fit_endINL_func[i])
    
    best_fit_DNL = []
    for i in range(1, 4094):
        best_fit_DNL.append(best_fit_INL[i] - best_fit_INL[i-1])


    print(f"Max endpoint DNL: {max(endDNL)} LSB(s)")
    print(f"Max endpoint INL: {max(endINL)} LSB(s)")
    print(f"Max Best-Fit INL: {max(best_fit_INL[1:-1])} LSB(s)")
    print(f"Max Best-Fit DNL: {max(best_fit_DNL[1:-1])} LSB(s)")



    #print(cw_up)

        # Plot the combined transfer curve and ideal line
    plt.figure(figsize=(14, 8))

    # Combined Transfer Curve
    plt.plot(
        expected_voltage_values_up,
        combined_codes,
        linestyle='-',
        color='purple',
        alpha=0.7,
        label='Combined Measured Output'
    )

    # Ideal Transfer Line
    plt.step(
        expected_voltage_values_up,
        ideal_transfer_line,
        where='post',
        color='red',
        linestyle='--',
        linewidth=1.5,
        label='Ideal Transfer Line'
    )

    plt.title('Transfer Curve of the ADC Using Function Generator (Combined)')
    plt.xlabel('Input Voltage (mV)')
    plt.ylabel('Output Code')
    plt.grid(True)
    plt.xlim(0, vRef * 1000)    # X-axis in mV
    plt.ylim(0, 4096)            # Y-axis for the ADC output code
    plt.legend()
    plt.tight_layout()
    plt.show()

    # Plot Histogram of Code Widths for Combined Data
    plt.figure(figsize=(14, 6))

    # Histogram for Combined Data
    plt.bar(range(len(cw_combined)), cw_combined, color='blue', alpha=0.7, edgecolor='black')
    plt.title('Code Widths for Combined Output Codes')
    plt.xlabel('Output Code')
    plt.ylabel('Code Width (LSBs)')
    plt.grid(True)

    plt.tight_layout()
    plt.show()

    # Plot Voltage Code Edges for Combined Data in mV
    plt.figure(figsize=(14, 8))

    plt.plot(
        range(len(v_ce_combined)),           # X-axis: output codes
        [v for v in v_ce_combined],   # Y-axis: voltage code edges (in mV)
        linestyle='-',
        color='orange',
        alpha=0.7,
        label='Voltage Code Edges (Combined) in mV'
    )

    plt.title('Voltage Code Edges for Combined Ramp (in mV)')
    plt.xlabel('Output Code')
    plt.ylabel('Voltage Code Edges (mV)')
    plt.grid(True)

    # Ensure whole number ticks on x and y axes
    plt.xticks(np.arange(0, len(v_ce_combined), step=100))  # Adjust step size for readability
    plt.yticks(np.arange(0, max(v_ce_combined) + 1, step=100))  # Whole number steps in mV

    plt.tight_layout()
    plt.legend()
    plt.show()

    # Plot Combined INL (Endpoint and Best-Fit)
    plt.figure(figsize=(14, 6))
    plt.plot(
    range(len(endINL)),
    endINL,
    linestyle='-',
    color='blue',
    alpha=0.7,
    label='Endpoint INL'
    )
    plt.plot(
    range(len(best_fit_INL)),
    best_fit_INL,
    linestyle='--',
    color='red',
    alpha=0.7,
    label='Best-Fit INL'
    )
    plt.plot(
    range(1, 4095),
    best_fit_endINL_func[1:],  # Exclude index 0 for consistency
    linestyle=':',
    color='green',
    alpha=0.7,
    label='Best-Fit INL Function'
    )
    plt.title('INL: Endpoint vs. Best-Fit')
    plt.xlabel('Output Code')
    plt.ylabel('INL (LSBs)')
    plt.grid(True)
    plt.xticks(np.arange(0, len(endINL), step=100))
    plt.legend()
    plt.tight_layout()
    plt.show()

    # Plot Combined DNL (Endpoint and Best-Fit)
    plt.figure(figsize=(14, 6))
    plt.plot(
    range(len(endDNL)),
    endDNL,
    linestyle='-',
    color='blue',
    alpha=0.7,
    label='Endpoint DNL'
    )
    plt.plot(
    range(len(best_fit_DNL)),
    best_fit_DNL,
    linestyle='--',
    color='red',
    alpha=0.7,
    label='Best-Fit DNL'
    )
    plt.title('DNL: Endpoint vs. Best-Fit')
    plt.xlabel('Output Code')
    plt.ylabel('DNL (LSBs)')
    plt.grid(True)
    plt.xticks(np.arange(0, len(endDNL), step=100))
    plt.legend()
    plt.tight_layout()
    plt.show()

    #Save the transfer Curve data
    transfer_curve_data = pd.DataFrame({
    'Expected Voltage (mV)': expected_voltage_values_up,
    'Combined Output Code': combined_codes,
    'Ideal Output Code': ideal_transfer_line
    })
    transfer_curve_data.to_csv('transfer_curve_data.csv', index=False)
    print("Transfer curve data saved as 'transfer_curve_data.csv'")

    # Save Code Width Data
    code_width_data = pd.DataFrame({
    'Output Code': range(len(cw_combined)),
    'Code Width (LSBs)': cw_combined
    })
    code_width_data.to_csv('code_width_data.csv', index=False)
    print("Code width data saved as 'code_width_data.csv'")

    # Save Voltage Code Edges Data
    voltage_code_edges_data = pd.DataFrame({
        'Output Code': range(len(v_ce_combined)),
        'Voltage Code Edge (mV)': v_ce_combined
    })
    voltage_code_edges_data.to_csv('voltage_code_edges_data.csv', index=False)
    print("Voltage code edges data saved as 'voltage_code_edges_data.csv'")


except KeyboardInterrupt:
    print("Measurement interrupted by user.")
except PyVirtualBenchException as e:
    print(f"PyVirtualBench error: {e}")

finally:
    # Cleanup: Stop and release Function Generator
    try:
        fgen.stop()
        fgen.release()
        print("Function Generator stopped and released.")
    except Exception as e:
        print(f"Error stopping Function Generator: {e}")
    
    # Reset power supply outputs
    try:
        pwr_sup.configure_voltage_output(pwr_channel_1, 0.1, 0.1)
        pwr_sup.enable_all_outputs(False)
        pwr_sup.release()
        print("Power supplies reset and released.")
    except Exception as e:
        print(f"Error resetting Power Supply: {e}")
    
    # Release SPI Interface and VirtualBench
    try:
        spi.release()
    except Exception as e:
        print(f"Error releasing SPI Interface: {e}")
    try:
        vb.release()
    except Exception as e:
        print(f"Error releasing VirtualBench: {e}")
    
    print("All resources have been released.")
