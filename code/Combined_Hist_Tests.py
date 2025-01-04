
import Linear_Hist_Cleaned as Linear
import Sine_Hist as Sine

from pyvirtualbench import (
    PyVirtualBench,
    Polarity,
    ClockPhase,
    PyVirtualBenchException,
    Waveform
)
import time

#VB8012-30DF182
# Configuration Parameters
VB_DEVICE = "VB8012-30DF182"
#BUS = f"{VB_DEVICE}/spi/0"
PWR_CHANNEL = "ps/+25V"
vb = PyVirtualBench(VB_DEVICE)
write_channels = f"{VB_DEVICE}/dig/4:7"

def int_to_bool_array(val):
    binary = bin(val)
    binary_str = binary[2:]
    padded = binary_str.zfill(4)
    #print(padded)
    bool_bin = [int(digit) for digit in padded]
    bool_bin.reverse()
    return bool_bin

def main():
    try:
        dio = vb.acquire_digital_input_output(write_channels)
        dio.write(write_channels, [0,0,0,0])
        Linear.run_linear()
        print("Linear Test Complete!")
        time.sleep(5)
        dio.write(write_channels, int_to_bool_array(1))
        time.sleep(5)
        Sine.run_Sine()
        print("Sinusoidal Testing Complete!")
        time.sleep(5)
        dio.write(write_channels, int_to_bool_array(2))
        time.sleep(5)
    except KeyboardInterrupt:
        pass
    except PyVirtualBenchException as e:
        print(e)
    dio.write(write_channels, [0,0,0,0])
    vb.release()
    dio.release()

if __name__ == "__main__":
    main()
