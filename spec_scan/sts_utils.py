import numpy as np

def load_darknoise_npz(file_path):
    data = np.load(file_path)
    wavelength = data['wavelength']
    dark_avg = data['dark_avg']
    return wavelength, dark_avg
