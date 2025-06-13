# code to visualize the pure spectral calibration data (3,41,1024)
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

# --- Load Calibration Data ---
folder = './timestamp_folder'  # replace with actual folder
data = np.load(os.path.join(folder, 'spec_calibration.npz'), allow_pickle=True)
v_min = data['v_min']
v_max = data['v_max']
h_min = data['h_min']
h_max = data['h_max']
wavelengths = data['wavelengths']
measurements = data['measurements'].item()  # dict with keys (h,v)

# --- Parameters ---
v_values = sorted(set([v for (_, v) in measurements.keys()]))
h_values = sorted(set([h for (h, _) in measurements.keys()]))

# --- Convert to Matrix ---
spectra_matrix = np.zeros((len(v_values), len(h_values), len(wavelengths)))
for i_v, v in enumerate(v_values):
    for i_h, h in enumerate(h_values):
        spectra_matrix[i_v, i_h, :] = measurements[(h, v)]

# --- analyze the spectra ---
# turn v,h,1024 into v,h,3 RGB image
# Define RGB band ranges in nm
r_band = (600, 660)
g_band = (495, 570)
b_band = (420, 490)

# Find indices corresponding to each band
r_idx = np.where((wavelengths >= r_band[0]) & (wavelengths <= r_band[1]))[0]
g_idx = np.where((wavelengths >= g_band[0]) & (wavelengths <= g_band[1]))[0]
b_idx = np.where((wavelengths >= b_band[0]) & (wavelengths <= b_band[1]))[0]

# Integrate over the bands (sum of intensities)
rgb_image = np.zeros((*spectra_matrix.shape[:2], 3))
rgb_image[..., 0] = spectra_matrix[..., r_idx].sum(axis=-1)  # Red
rgb_image[..., 1] = spectra_matrix[..., g_idx].sum(axis=-1)  # Green
rgb_image[..., 2] = spectra_matrix[..., b_idx].sum(axis=-1)  # Blue

# Normalize for visualization

rgb_image_normalized = rgb_image / rgb_image.max()
rows, cols = rgb_image_normalized.shape[:2]

# Compute physical spacing
v_ticks = np.linspace(v_min, v_max, rows)
h_ticks = np.linspace(h_min, h_max, cols)

plt.figure(figsize=(8, 6))
plt.imshow(rgb_image_normalized),extent=[h_min, h_max, v_max, v_min]
plt.title("RGB Inferred from Spectral Scan")
plt.axis("off")
plt.savefig(os.path.join(folder, 'rgb_inferred.png'), dpi=300)

# # --- Plotting: Spectra by Row ---
# fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
# for i, ax in enumerate(axes):
#     ax.imshow(spectra_matrix[i].T, aspect='auto', extent=[h_values[0], h_values[-1], wavelengths[-1], wavelengths[0]])
#     ax.set_title(f'Row {i} Spectra (v={v_values[i]})')
#     ax.set_ylabel('Wavelength (nm)')
#     ax.set_xlabel('Horizontal position (deg)')

# plt.tight_layout()
# plt.show()

# # --- Extract Spectral Signatures from Columns ---
# center_idx = len(h_values) // 2
# color_labels = ['Red', 'Green', 'Blue', 'White']
# positions = [center_idx - 15, center_idx - 5, center_idx + 5, center_idx + 15]

# plt.figure(figsize=(10, 6))
# for pos, label in zip(positions, color_labels):
#     spectrum = spectra_matrix[1, pos]  # Middle row
#     plt.plot(wavelengths, spectrum, label=f'{label} (h={h_values[pos]})')

# plt.title('Extracted Spectral Signatures')
# plt.xlabel('Wavelength (nm)')
# plt.ylabel('Intensity')
# plt.legend()
# plt.grid(True)
# plt.tight_layout()
# plt.show()


