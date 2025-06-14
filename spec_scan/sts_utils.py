import numpy as np
import os

def load_darknoise_npz(file_path):
    data = np.load(file_path)
    wavelength = data['wavelength']
    dark_avg = data['dark_avg']
    return wavelength, dark_avg

def extract_integration_times(dark_noises_folder, output_file):
    print(os.listdir(dark_noises_folder))
    integration_times = set()
    # Extract integration times from filenames
    for filename in os.listdir(dark_noises_folder):
        if filename.startswith("dark_") and filename.endswith(".npz"):
            print(filename)
            try:
                # file format: "dark_100ms.npz"
                if filename.startswith("dark_") and filename.endswith("ms.npz"):
                    time_str = filename[5:-7]  # Remove "dark_" prefix and "ms.npz" suffix
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
# HOME = os.path.expanduser("~")
# SCAM_PATH = os.path.join(HOME, "Github", "SCAM")
# DARK_NOISES_PATH = os.path.join(SCAM_PATH,'dark_noises')
# DATA_PATH = os.path.join(SCAM_PATH, 'data')
# dark_noises_folder = "/Users/dengyuyao/Github/SCAM/dark_noises"
# output_file = os.path.join(DATA_PATH,'all_int_times.npy')

# # Run the function
# extract_integration_times(DARK_NOISES_PATH, output_file)