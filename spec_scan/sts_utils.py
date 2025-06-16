import numpy as np
import os

HOME = os.path.expanduser("~")
SCAM_PATH = os.path.join(HOME, "Github", "SCAM")
DARK_NOISES_PATH = os.path.join(SCAM_PATH,'dark_noises')
DATA_PATH = os.path.join(SCAM_PATH, 'data')

def load_darknoise_npz(file_path):
    data = np.load(file_path)
    wavelength = data['wavelength']
    dark_avg = data['dark_avg']
    return wavelength, dark_avg

ACCEPT_SPEC_LOW = 2000 # the lower limit for the acceptable spectral reading
ACCEPT_SPEC_HIGH = 8000  # the upper limit for the acceptable spectral reading
ACCEPT_MAX=16383
def extract_integration_times(dark_noises_folder, output_file):
    print(os.listdir(dark_noises_folder))
    integration_times = set()
    # Extract integration times from filenames
    for filename in os.listdir(dark_noises_folder):
        if filename.startswith("dark_") and filename.endswith(".npz"):
            # print(filename)
            try:
                # file format: "dark_100ms.npz"
                if filename.startswith("dark_") and filename.endswith("ms.npz"):
                    time_str = filename[5:-6]  # Remove "dark_" prefix and "ms.npz" suffix
                    try:
                        time_s = float(time_str)  # Convert to float (seconds)
                        integration_times.add(time_s)
                    except ValueError:
                        print(f"Skipping invalid time format in filename: {filename}")
                integration_times.add(time_s)
            except ValueError:
                continue  # Skip files with invalid format
    # Convert the set to a sorted 1D array
    integration_times_array = np.array(sorted(integration_times))
    print(integration_times_array)

    output_dir = os.path.dirname(output_file)
    if output_dir:  # Only create the directory if it is not empty
        os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    np.save(output_file, integration_times_array)
    print(f"Integration times saved to {output_file}")
# # how to use this function
# # Define paths
HOME = os.path.expanduser("~")
SCAM_PATH = os.path.join(HOME, "Github", "SCAM")
DARK_NOISES_PATH = os.path.join(SCAM_PATH,'dark_noises')
DATA_PATH = os.path.join(SCAM_PATH, 'data')
output_file = os.path.join(DATA_PATH,'all_int_times.npy')

# # Run the function
# extract_integration_times(DARK_NOISES_PATH, output_file)


def get_optimal_integration_time(all_int_times, spectrometer,previous_ints=None):
    """
    Finds the optimal integration time to achieve a spectral reading between 8000 and 15000.

    Parameters:
        all_int_times (list): List of available integration times in milliseconds.
        spectrometer (object): Spectrometer device with a `set_integration_time` and `read` method.

    Returns:
        int: Optimal integration time in milliseconds.
    """
    
    sorted_times = sorted(all_int_times)
    if previous_ints is None:
        median_index = len(sorted_times) // 2
        print(f'{len(sorted_times)} integrationtime')
        current_int = sorted_times[median_index]
        print(f'current int time {current_int}ms:')
    else:
        median_index = sorted_times.index(previous_ints) if previous_ints in sorted_times else len(sorted_times) // 2
        current_int = sorted_times[median_index]

    while True:
        spectrometer.integration_time_micros(current_int*1e3)
        _,raw_value = spectrometer.spectrum()
        print(np.max(raw_value))
        if np.max(raw_value) > ACCEPT_MAX:
            # check if the raw_value is too high
            # decrease the integration time
           median_index -= 1
        else:
            if ACCEPT_SPEC_LOW <= np.mean(raw_value) <= ACCEPT_SPEC_HIGH:
                return current_int
            elif np.mean(raw_value) > ACCEPT_SPEC_HIGH:
                print("OVEREXPOSED, mean of raw :",np.mean(raw_value))
                median_index -= 1
            elif np.mean(raw_value) < ACCEPT_SPEC_LOW:
                print("UNDEREXPOSED, mean of raw :",np.mean(raw_value))
                median_index += 1
        print(f'median_indx {median_index}, current int time {sorted_times[median_index]}ms:')
        if median_index < 0 or median_index >= len(sorted_times):
            print("No suitable integration time found within the range.")
            print("MEASURE SOME MORE INTEGRATION TIMES")
            return None
        else:
            # Update the current integration time
            current_int = sorted_times[median_index]
