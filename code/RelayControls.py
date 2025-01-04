#import pyvisa
from pyvirtualbench import PyVirtualBench, DmmFunction, PyVirtualBenchException
import time

# Pin configurations for controlling the shift registers
DATA_PIN = 'PIN_1'  # Pin for sending data to the shift register
CLOCK_PIN = 'PIN_2'  # Pin for the shift register clock
LATCH_PIN = 'PIN_3'  # Pin for latching the data into the shift registers

# Number of shift registers and relays
NUM_SHIFT_REGISTERS = 7
NUM_RELAYS = 56
CONFIGURATIONS = 34  # Number of configurations

# Define the configurations dictionary for easier access
#Relay 1 tests: 1-17
#Relay 2 tests: 18-34
#Continuity:       1, 2, 18, 19
#Pwr Sup Currents: 3, 4*, 20, 21*
#Leakage Currents: 5 - 14, 22 - 31
#Input Impedance:  15, 16, 32, 33
#Histogram:        17, 34
#1: [0,0,1,1,0,1,0,1,0,0,0,0,0,0,1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1],
#1: [0,0,1,1,0,1,0,1,0,0,0,0,0,0,1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1],
CONFIGS = {
    #   1,2,3,4,5,6,7,8,9
    1: [0,0,0,1,0,0,0,1,0,1,0,0,0,0,0,0,0,0,0,1,1,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0],
    2: [1,0,0,1,0,0,0,1,1,1,0,1,1,0,0,0,0,0,0,1,1,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,1,0,0,0,0,0,0],
    3: [0,0,0,0,1,1,1,0,0,0,0,0,0,1,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    4: [0,0,0,0,1,1,1,0,0,0,1,0,0,1,0,1,0,0,0,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0],
    5: [0,0,1,0,0,1,1,0,0,0,0,0,0,1,1,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0],
    6: [0,0,1,0,0,1,1,0,0,0,0,0,0,1,1,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,1,0,0,0,0,0,0],
    7: [0,1,0,0,0,1,1,0,0,0,0,0,0,1,1,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,1,0,0,0,0,0,0],
    8: [1,0,1,0,0,1,1,0,0,0,0,0,0,1,1,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0],
    9: [1,1,0,0,0,1,1,0,0,0,0,0,0,1,1,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0],
    10:[0,0,1,0,0,1,1,0,0,0,0,1,0,1,1,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0],
    11:[0,1,0,0,0,1,1,0,0,0,0,1,0,1,1,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0],
    12:[0,0,1,0,0,1,1,0,1,0,0,0,0,1,1,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0],
    13:[0,0,1,0,0,1,1,0,0,0,0,0,1,1,1,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0],
    14:[0,1,0,0,0,1,1,0,0,0,0,0,1,1,1,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0],
    15:[0,0,1,0,0,1,1,0,0,0,0,0,0,0,1,0,0,0,0,1,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0],
    16:[0,1,0,0,0,1,1,0,0,0,0,0,0,0,1,0,0,0,0,1,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0],
    17:[0,0,0,0,0,1,0,0,0,0,1,0,0,1,1,1,0,0,0,1,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,1,0,0,0,0,0],
    18:[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,1,0,0,0,0,1,1,0,1,0,1,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    19:[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,1,0,1,0,0,1,1,0,1,1,1,0,1,1,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0],
    20:[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,1,0,0,0,0,1,0,0,0,0,1,0,0,0,0],
    21:[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,1,1,0,1,0,0,0,0,1,0,0,0,0,1,1,0,0,0],
    22:[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,1,1,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,1],
    23:[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,1,0,0,0,1,0,0,0,0,0,0,0,1,1,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,1],
    24:[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,1,0,0,0,1,0,0,0,0,0,0,0,1,1,0,0,0,0,0,1,0,0,0,0,0,1,0,0,1,0],
    25:[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,1,0,0,0,0,0,1,0,0,0,0,0,1,0,1,0,1],
    26:[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,1,0,0,0,0,0,1,0,0,0,0,0,1,0,1,1,0],
    27:[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1,0,1,1,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,1],
    28:[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1,0,1,1,0,0,0,0,0,1,0,0,0,0,0,1,0,0,1,0],
    29:[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,1,0,0,1,0,0,0,0,1,1,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,1],
    30:[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,1,1,1,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,1],
    31:[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,1,1,1,0,0,0,0,0,1,0,0,0,0,0,1,0,0,1,0],
    32:[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,1,0,1,0,0,0,0,0,0,0,1],
    33:[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,1,0,1,0,0,0,0,0,0,1,0],
    34:[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,1,0,1,0,0,0,0,0,1,0,0,1,0,0,0,0,0,0,1,0,1,0,0,0,1,1,0,0,0]
}

CONFIGS_TEST = {
    i: [1 if j == i - 1 else 0 for j in range(58)]
    for i in range(0, 59)
}


# Function to send data to the shift register pins
def send_data_to_shift_register(config_num):
    config = CONFIGS.get(config_num)
    #config = CONFIGS_TEST.get(config_num)
    config.reverse()
    print(config)
    if config is None:
        print(f"Configuration {config_num} not found.")
        return
    
    # Send data via shift registers
    for bit in config:
        # Send each bit to the shift register
        if bit == 1:
            # Set DATA_PIN high
            dio_data.write(write_channel_data, [1])
        else:
            # Set DATA_PIN low
            dio_data.write(write_channel_data, [0])
        
        # Toggle the clock to shift the data
        dio_clk.write(write_channel_clk, [1])
        time.sleep(0.01)  # Short delay to simulate clock pulse
        dio_clk.write(write_channel_clk, [0])
    
    # Latch the data into the shift register
    dio_latch.write(write_channel_latch, [1])
    time.sleep(0.01)  # Short delay
    dio_latch.write(write_channel_latch, [0])
    print(f"Configuration {config_num} sent to shift registers.")

def set_relays(config_num, data, clk, latch):
    write_channel_data = "VB8012-30DF182/dig/5"
    write_channel_clk = "VB8012-30DF182/dig/6"
    write_channel_latch = "VB8012-30DF182/dig/7"
    config = CONFIGS.get(config_num)
    config.reverse()
    
    if config is None:
        print(f"Configuration {config_num} not found.")
        return
    
    # Send data via shift registers
    for bit in config:
        # Send each bit to the shift register
        if bit == 1:
            # Set DATA_PIN high
            data.write(write_channel_data, [1])
        else:
            # Set DATA_PIN low
            data.write(write_channel_data, [0])
        
        # Toggle the clock to shift the data
        clk.write(write_channel_clk, [1])
        time.sleep(0.01)  # Short delay to simulate clock pulse
        clk.write(write_channel_clk, [0])
    
    # Latch the data into the shift register
    latch.write(write_channel_latch, [1])
    time.sleep(0.01)  # Short delay
    latch.write(write_channel_latch, [0])
    print(f"Configuration {config_num} sent to shift registers.")

# Test the function by sending configuration 1
if __name__ == "__main__":
    vb = PyVirtualBench("VB8012-30DF182")
    write_channel_data = "VB8012-30DF182/dig/5"
    write_channel_clk = "VB8012-30DF182/dig/6"
    write_channel_latch = "VB8012-30DF182/dig/7"
    PWR_CHANNEL = "ps/+25V"
    dio_data = vb.acquire_digital_input_output(write_channel_data)
    dio_clk = vb.acquire_digital_input_output(write_channel_clk)
    dio_latch = vb.acquire_digital_input_output(write_channel_latch)
    dio_data.write(write_channel_data, [0])
    dio_clk.write(write_channel_clk, [0])
    dio_latch.write(write_channel_latch, [0])
    try:
        while( True):
            setup = int(input("stuff: "))
            #for i in range(1,35):
            #    send_data_to_shift_register(i)
            #    time.sleep(0.5)
            send_data_to_shift_register(setup)
    except Exception as e:
        print(e)
        dio_clk.release()
        dio_data.release()
        dio_latch.release()
        vb.release()
    #pwr_sup.enable_all_outputs(False)
