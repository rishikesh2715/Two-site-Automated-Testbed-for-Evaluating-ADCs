import matplotlib.pyplot as plt
import numpy as np
from pyvirtualbench import PyVirtualBench, Waveform, DmmFunction, PyVirtualBenchException

# Importing the test modules
import Continuity
import InputImpedanceTest
import PwrSupplyCurrents
import Combined_Hist_Tests
import RelayControls
import LeakageCurrents


pwr_channel = "ps/+6V"

def plot_combined_histograms(cw_combined, best_fit_inl, best_fit_dnl, end_inl, end_dnl, v_ce_combined):
    """Plot all relevant histograms and graphs for combined histogram tests."""
    # Plot Code Width Histogram
    plt.figure(figsize=(12, 6))
    plt.bar(range(len(cw_combined)), cw_combined, color='blue', alpha=0.7, edgecolor='black')
    plt.title('Code Width Histogram')
    plt.xlabel('Output Code')
    plt.ylabel('Code Width (LSBs)')
    plt.grid(True)
    plt.show()

    # Plot INL (Endpoint vs. Best-Fit)
    plt.figure(figsize=(12, 6))
    plt.plot(end_inl, label='Endpoint INL', color='blue')
    plt.plot(best_fit_inl, label='Best-Fit INL', linestyle='--', color='green')
    plt.title('INL: Endpoint vs. Best-Fit')
    plt.xlabel('Output Code')
    plt.ylabel('INL (LSBs)')
    plt.legend()
    plt.grid(True)
    plt.show()

    # Plot DNL (Endpoint vs. Best-Fit)
    plt.figure(figsize=(12, 6))
    plt.plot(end_dnl, label='Endpoint DNL', color='red')
    plt.plot(best_fit_dnl, label='Best-Fit DNL', linestyle='--', color='orange')
    plt.title('DNL: Endpoint vs. Best-Fit')
    plt.xlabel('Output Code')
    plt.ylabel('DNL (LSBs)')
    plt.legend()
    plt.grid(True)
    plt.show()

    # Plot Voltage Code Edges
    plt.figure(figsize=(12, 6))
    plt.plot(range(len(v_ce_combined)), v_ce_combined, linestyle='-', color='purple')
    plt.title('Voltage Code Edges')
    plt.xlabel('Output Code')
    plt.ylabel('Voltage (mV)')
    plt.grid(True)
    plt.show()

def plot_sine_data(output_codes, cw_lsb, best_fit_inl, best_fit_dnl, inl, dnl, v_ce, v_ce_ideal):
    """Plot all relevant graphs for Sine Hist Tests."""
    # Plot Output Codes
    plt.figure(figsize=(10, 6))
    plt.plot(output_codes[0:4096], marker=None, linestyle='-', markersize=4)
    plt.title('ADC Output Codes')
    plt.xlabel('Sample Number')
    plt.ylabel('ADC Output Code')
    plt.grid(True)
    plt.show()

    # Plot Code Width Histogram
    plt.figure(figsize=(12, 6))
    plt.bar(range(4096), cw_lsb, width=1.0, edgecolor='black')
    plt.title('Code Widths for Each ADC Code')
    plt.xlabel('ADC Code')
    plt.ylabel('Code Width (LSBs)')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.show()

    # Plot INL
    plt.figure(figsize=(12, 6))
    plt.plot(inl, label='End INL', linestyle='-', marker=None)
    plt.plot(best_fit_inl, label='Best-Fit INL', linestyle='--', marker=None)
    plt.title('INL (Integral Non-Linearity)')
    plt.xlabel('ADC Code')
    plt.ylabel('INL (LSBs)')
    plt.legend(loc='best')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.show()

    # Plot DNL
    plt.figure(figsize=(12, 6))
    plt.plot(dnl, label='End DNL', linestyle='-', marker=None)
    plt.plot(best_fit_dnl, label='Best-Fit DNL', linestyle='--', marker=None)
    plt.title('DNL (Differential Non-Linearity)')
    plt.xlabel('ADC Code')
    plt.ylabel('DNL (LSBs)')
    plt.legend(loc='best')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.show()

    # Plot Voltage Code Edges
    plt.figure(figsize=(12, 6))
    plt.plot(range(4096), v_ce, label="Measured V_ce", linestyle='-', marker=None)
    plt.plot(range(4096), v_ce_ideal, label="Ideal V_ce", linestyle='--', marker=None)
    plt.title('Code Edges: Voltage vs. Output Code')
    plt.xlabel('Output Code')
    plt.ylabel('Voltage (V)')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.show()

def main():
    vb = PyVirtualBench("VB8012-30DF182")
    # Initialize result storage
    results = {}

    # Data for Linear Histogram plots
    cw_combined = []
    best_fit_inl = []
    best_fit_dnl = []
    end_inl = []
    end_dnl = []
    v_ce_combined = []

    # Data for Sine Histogram plots
    sine_output_codes = []
    sine_cw_lsb = []
    sine_best_fit_inl = []
    sine_best_fit_dnl = []
    sine_inl = []
    sine_dnl = []
    sine_v_ce = []
    sine_v_ce_ideal = []

    write_channel_data = "VB8012-30DF182/dig/5"
    write_channel_clk = "VB8012-30DF182/dig/6"
    write_channel_latch = "VB8012-30DF182/dig/7"
    PWR_CHANNEL_RELAY = "ps/+25V"
    PWR_CHANNEL_CHIP = "ps/+6V"
    WAVE_TYPE = Waveform.DC
    AMPLITUDE = 5 #Amplitude shown in Pk-2-Pk Voltage. Actual peak voltage is 2.5 V
    FREQ = 1.0  # Hz
    DUTY_CYCLE = 50.0  # %
    DC_OFFSET = 5.0

    
    VREF = 5.0  # Reference voltage in Volts
    HITS_PER_VALUE = 1
    VLSB = VREF/4094

    PEAK = AMPLITUDE

    try:
        #Configure VB Hardware
        pwr_sup = vb.acquire_power_supply()
        pwr_sup.enable_all_outputs(True)
        #pwr_sup.configure_voltage_output(PWR_CHANNEL_RELAY, 5, 0.5)
        dio_data = vb.acquire_digital_input_output(write_channel_data)
        dio_clk = vb.acquire_digital_input_output(write_channel_clk)
        dio_latch = vb.acquire_digital_input_output(write_channel_latch)
        #dio_data.write(write_channel_data, [0])
        #dio_clk.write(write_channel_clk, [0])
        #dio_latch.write(write_channel_latch, [0])
        skip = 1

        # Continuity Test
        RelayControls.set_relays(1, dio_data, dio_clk, dio_latch)
        print("Starting Continuity Test...")
        input("hit enter when ready")
        try:
            v, i, VD = Continuity.test_single_pin(pwr_sup)
            if not Continuity.dut_pass:
                raise Exception("Single-Pin Continuity Test failed.")
            
            results['Continuity Single-Pin'] = {
                "Voltage (mV)": v * 1000,
                "Current (mA)": i,
                "Diode Voltage (mV)": VD,
            }
            RelayControls.set_relays(2, dio_data, dio_clk, dio_latch)
            input("Prep for full Continuity")
            v_full, i_full, VD_full = Continuity.test_all_pins(pwr_sup, v)
            if not Continuity.dut_pass:
                print(i_full)
                raise Exception("Full-Pin Continuity Test failed.")

            results['Continuity Full'] = {
                "Voltage (mV)": v_full * 1000,
                "Current (mA)": i_full,
                "Diode Voltage (mV)": VD_full,
            }
            print("Continuity Test Completed.\n")
        except Exception as e:
            results['Continuity Test'] = f"Failed: {e}"
            print(f"Continuity Test failed: {e}. Aborting further tests.")
            return  # Abort execution if Continuity Test fails

        if(skip == 1):
            pwr_sup.configure_voltage_output(PWR_CHANNEL_CHIP, 5, 0.5)

        

        if(skip == 0):

            # Continuity Test
            RelayControls.set_relays(1, dio_data, dio_clk, dio_latch)
            print("Starting Continuity Test...")
            input("hit enter when ready")
            try:
                v, i, VD = Continuity.test_single_pin(pwr_sup)
                if not Continuity.dut_pass:
                    raise Exception("Single-Pin Continuity Test failed.")
                
                results['Continuity Single-Pin'] = {
                    "Voltage (mV)": v * 1000,
                    "Current (mA)": i,
                    "Diode Voltage (mV)": VD,
                }
                RelayControls.set_relays(2, dio_data, dio_clk, dio_latch)
                input("Prep for full Continuity")
                v_full, i_full, VD_full = Continuity.test_all_pins(pwr_sup, v)
                if not Continuity.dut_pass:
                    print(i_full)
                    raise Exception("Full-Pin Continuity Test failed.")

                results['Continuity Full'] = {
                    "Voltage (mV)": v_full * 1000,
                    "Current (mA)": i_full,
                    "Diode Voltage (mV)": VD_full,
                }
                print("Continuity Test Completed.\n")
            except Exception as e:
                results['Continuity Test'] = f"Failed: {e}"
                print(f"Continuity Test failed: {e}. Aborting further tests.")
                return  # Abort execution if Continuity Test fails
            #pwr_sup.enable_all_outputs(False)
            #pwr_sup.release()
            #vb.release()

            RelayControls.set_relays(15, dio_data, dio_clk, dio_latch)
            pwr_sup.configure_voltage_output(PWR_CHANNEL_CHIP, 5, 0.5)
            input("press enter to start input impedance testing")
            # Input Impedance Test
            print("Starting Input Impedance Test...")
            try:
                fgen, dmm = InputImpedanceTest.initialize_virtualbench()
                for i in range(4):
                    RelayControls.set_relays(15 + i, dio_data, dio_clk, dio_latch)
                    impedance = InputImpedanceTest.run_input_impedace(fgen, dmm)
                    results[f'Input Impedance (Pin {i})'] = f"{impedance:.2f} Ω"
                print("Input Impedance Test Completed.\n")
            except Exception as e:
                results['Input Impedance Test'] = f"Failed: {e}"
            #pwr_sup.enable_all_outputs(False)
            #pwr_sup.release()
            fgen.release()
            dmm.release()
            #spi.release()


            RelayControls.set_relays(3, dio_data, dio_clk, dio_latch)
            input("press enter to start power supply currents testing")
            # Power Supply Currents Test
            print("Starting Power Supply Currents Test...")
            try:
                fgen, spi, dmm = PwrSupplyCurrents.initialize_virtualbench()
                PwrSupplyCurrents.configure_instruments(pwr_sup, fgen, spi)

                # Step 1: Idle Current
                print("Measuring Idle Current...")
                idle_currents = PwrSupplyCurrents.run_idle(dmm)
                results['Idle Current (mA)'] = idle_currents


                # Step 2: Load Current
                print("Measuring Load Current...")
                running_currents = PwrSupplyCurrents.run_measurement(spi, dmm)
                results['Load Current (mA)'] = running_currents

                spi.release()

                # Step 3: Shutdown Current
                print("Measuring Shutdown Current...")
                dio = vb.acquire_digital_input_output(PwrSupplyCurrents.WRITE_CHANNELS)
                shutdown_currents = PwrSupplyCurrents.run_shutdown(dio, dmm)
                results['Shutdown Current (mA)'] = shutdown_currents


                dio.release()
                fgen.stop()
                fgen.release()
                #vb.release()
                print("Power Supply Currents Test Completed.\n")
            except Exception as e:
                results['Power Supply Currents Test'] = f"Failed: {e}"

            
            RelayControls.set_relays(5, dio_data, dio_clk, dio_latch)
            input("Prep for Leakage Current Testing")
            fgen = vb.acquire_function_generator()
            fgen.configure_standard_waveform(WAVE_TYPE, AMPLITUDE, DC_OFFSET, FREQ, DUTY_CYCLE)
            dmm = vb.acquire_digital_multimeter()
            dmm.configure_measurement(DmmFunction.DC_CURRENT, True, 0.1)
            results["Leakage Current for Pin 1 (Low)"] = LeakageCurrents.run_Leakage_low(dmm)
            print(f"Leakage Current (low): {results['Leakage Current for Pin 1 (Low)'] * 1000} mA)")
            fgen.run()
            results["Leakage Current for Pin 1 (High)"] = LeakageCurrents.run_Leakage_high(dmm)
            print(f"Leakage Current (low): {results['Leakage Current for Pin 1 (High)'] * 1000} mA)")
            fgen.stop()
            fgen.release()
            dmm.release()



        RelayControls.set_relays(17, dio_data, dio_clk, dio_latch)
        input("press enter to start histogram testing")
        # Combined Hist Tests
        print("Starting Combined Hist Tests...")
        try:
            #Combined_Hist_Tests.int_to_bool_array(0)  # Initialize digital output
            
            # Run Linear Test
            #linear_results = Combined_Hist_Tests.Linear.run_linear()
            Combined_Hist_Tests.Linear.run_linear()
            #cw_combined, best_fit_inl, best_fit_dnl, end_inl, end_dnl, v_ce_combined = linear_results
            results['Linear Hist Tests'] = "Completed Successfully"
            
            # Run Sine Test
            #sine_results = Combined_Hist_Tests.Sine.main()
            Combined_Hist_Tests.Sine.run_Sine()
            #(sine_output_codes, sine_cw_lsb, sine_best_fit_inl, 
             #sine_best_fit_dnl, sine_inl, sine_dnl, 
             #sine_v_ce, sine_v_ce_ideal) = sine_results
            results['Sine Hist Tests'] = "Completed Successfully"

            print("Combined Hist Tests Completed.\n")
        except Exception as e:
            results['Combined Hist Tests'] = f"Failed: {e}"
    
        #CHIP 2 Tests
        pwr_sup.configure_voltage_output(PWR_CHANNEL_CHIP, 0.01, 0.01)
        #pwr_sup.release()
        print("Beginning testing on Chip 2....")
        # Continuity Test
        RelayControls.set_relays(18, dio_data, dio_clk, dio_latch)
        print("Starting Continuity Test for chip 2...")
        input("hit enter when ready")
        try:
            v, i, VD = Continuity.test_single_pin(pwr_sup)
            if not Continuity.dut_pass:
                raise Exception("Single-Pin Continuity Test failed.")
            
            results['Continuity Single-Pin (Chip 2)'] = {
                "Voltage (mV)": v * 1000,
                "Current (mA)": i,
                "Diode Voltage (mV)": VD,
            }
            RelayControls.set_relays(19, dio_data, dio_clk, dio_latch)
            input("Prep for full Continuity")
            v_full, i_full, VD_full = Continuity.test_all_pins(pwr_sup, v)
            if not Continuity.dut_pass:
                print(i_full)
                raise Exception("Full-Pin Continuity Test failed.")

            results['Continuity Full (Chip 2)'] = {
                "Voltage (mV)": v_full * 1000,
                "Current (mA)": i_full,
                "Diode Voltage (mV)": VD_full,
            }
            print("Continuity Test Completed.\n")
        except Exception as e:
            results['Continuity Test (Chip 2)'] = f"Failed: {e}"
            print(f"Continuity Test failed: {e}. Aborting further tests.")
            return  # Abort execution if Continuity Test fails
        pwr_sup.configure_voltage_output(PWR_CHANNEL_CHIP, 5.0, 0.5)
        if(skip == 0):

            # Continuity Test
            RelayControls.set_relays(18, dio_data, dio_clk, dio_latch)
            print("Starting Continuity Test for chip 2...")
            input("hit enter when ready")
            try:
                v, i, VD = Continuity.test_single_pin(pwr_sup)
                if not Continuity.dut_pass:
                    raise Exception("Single-Pin Continuity Test failed.")
                
                results['Continuity Single-Pin (Chip 2)'] = {
                    "Voltage (mV)": v * 1000,
                    "Current (mA)": i,
                    "Diode Voltage (mV)": VD,
                }
                RelayControls.set_relays(19, dio_data, dio_clk, dio_latch)
                input("Prep for full Continuity")
                v_full, i_full, VD_full = Continuity.test_all_pins(pwr_sup, v)
                if not Continuity.dut_pass:
                    print(i_full)
                    raise Exception("Full-Pin Continuity Test failed.")

                results['Continuity Full (Chip 2)'] = {
                    "Voltage (mV)": v_full * 1000,
                    "Current (mA)": i_full,
                    "Diode Voltage (mV)": VD_full,
                }
                print("Continuity Test Completed.\n")
            except Exception as e:
                results['Continuity Test (Chip 2)'] = f"Failed: {e}"
                print(f"Continuity Test failed: {e}. Aborting further tests.")
                return  # Abort execution if Continuity Test fails
            #pwr_sup.enable_all_outputs(False)
            #pwr_sup.release()
            #vb.release()

            RelayControls.set_relays(32, dio_data, dio_clk, dio_latch)
            pwr_sup.configure_voltage_output(PWR_CHANNEL_CHIP, 5, 0.5)
            input("press enter to start input impedance testing")
            # Input Impedance Test
            print("Starting Input Impedance Test (Chip 2)...")
            try:
                fgen, dmm = InputImpedanceTest.initialize_virtualbench()
                for i in range(4):
                    RelayControls.set_relays(32 + i, dio_data, dio_clk, dio_latch)
                    impedance = InputImpedanceTest.run_input_impedace(fgen, dmm)
                    results[f'Input Impedance (Pin {i}) (Chip 2)'] = f"{impedance:.2f} Ω"
                print("Input Impedance Test Completed.\n")
            except Exception as e:
                results['Input Impedance Test (Chip 2)'] = f"Failed: {e}"
            #pwr_sup.enable_all_outputs(False)
            #pwr_sup.release()
            fgen.release()
            dmm.release()
            #spi.release()


            RelayControls.set_relays(20, dio_data, dio_clk, dio_latch)
            input("press enter to start power supply currents testing")
            # Power Supply Currents Test
            print("Starting Power Supply Currents Test (Chip 2)...")
            try:
                fgen, spi, dmm = PwrSupplyCurrents.initialize_virtualbench()
                PwrSupplyCurrents.configure_instruments(pwr_sup, fgen, spi)

                # Step 1: Idle Current
                print("Measuring Idle Current (Chip 2)...")
                idle_currents = PwrSupplyCurrents.run_idle(dmm)
                results['Idle Current (mA) (Chip 2)'] = idle_currents


                # Step 2: Load Current
                print("Measuring Load Current...")
                running_currents = PwrSupplyCurrents.run_measurement(spi, dmm)
                results['Load Current (mA) (Chip 2)'] = running_currents

                spi.release()

                # Step 3: Shutdown Current
                print("Measuring Shutdown Current (Chip 2)...")
                dio = vb.acquire_digital_input_output(PwrSupplyCurrents.WRITE_CHANNELS)
                shutdown_currents = PwrSupplyCurrents.run_shutdown(dio, dmm)
                results['Shutdown Current (mA) (Chip 2)'] = shutdown_currents


                dio.release()
                fgen.stop()
                fgen.release()
                #vb.release()
                print("Power Supply Currents Test Completed.\n")
            except Exception as e:
                results['Power Supply Currents Test (Chip 2)'] = f"Failed: {e}"

        RelayControls.set_relays(34, dio_data, dio_clk, dio_latch)
        input("press enter to start histogram testing")
        # Combined Hist Tests
        print("Starting Combined Hist Tests (Chip 2)...")
        try:
            #Combined_Hist_Tests.int_to_bool_array(0)  # Initialize digital output
            
            # Run Linear Test
            #linear_results = Combined_Hist_Tests.Linear.run_linear()
            Combined_Hist_Tests.Linear.run_linear()
            #cw_combined, best_fit_inl, best_fit_dnl, end_inl, end_dnl, v_ce_combined = linear_results
            results['Linear Hist Tests (Chip 2)'] = "Completed Successfully"
            
            # Run Sine Test
            #sine_results = Combined_Hist_Tests.Sine.main()
            Combined_Hist_Tests.Sine.run_Sine()
            #(sine_output_codes, sine_cw_lsb, sine_best_fit_inl, 
                #sine_best_fit_dnl, sine_inl, sine_dnl, 
                #sine_v_ce, sine_v_ce_ideal) = sine_results
            results['Sine Hist Tests (Chip 2)'] = "Completed Successfully"

            print("Combined Hist Tests Completed.\n")
        except Exception as e:
            results['Combined Hist Tests (Chip 2)'] = f"Failed: {e}"

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("\nSummary of Test Results:")
        for test, result in results.items():
            print(f"{test}: {result}")

        if cw_combined:
            print("\nGenerating Linear Histogram Plots...")
            plot_combined_histograms(cw_combined, best_fit_inl, best_fit_dnl, end_inl, end_dnl, v_ce_combined)

        if sine_output_codes:
            print("\nGenerating Sine Histogram Plots...")
            plot_sine_data(sine_output_codes, sine_cw_lsb, sine_best_fit_inl, 
                            sine_best_fit_dnl, sine_inl, sine_dnl, sine_v_ce, sine_v_ce_ideal)

    print("All tests completed or interrupted. Cleaning up resources if necessary.")
    pwr_sup.enable_all_outputs(False)
    pwr_sup.release()
    vb.release()

if __name__ == "__main__":
    main()
