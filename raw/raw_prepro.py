import numpy as np
import matplotlib.pyplot as plt
import os

HOME = os.path.expanduser("~")
SCAM_PATH = os.path.join(HOME, "Github", "SCAM")
CAM0_ROI_NPY = os.path.join(SCAM_PATH, "matlab_roi_extraction","cam0_mask.npy")
CAM1_ROI_NPY = os.path.join(SCAM_PATH, "matlab_roi_extraction","cam1_mask.npy")
def cut_raw_black_lines(img_filename,stride=8128,height=3040,width=4056):
    # Parse RAW bytes and robustly extract one frame even if:
    # 1) file contains multiple concatenated frames, or
    # 2) per-frame byte count differs slightly from nominal stride*height.
    with open(img_filename, 'rb') as f:
        raw_bytes = f.read()
    raw_data = np.frombuffer(raw_bytes, dtype=np.uint16)

    nominal_full_width = stride // 2
    nominal_frame_elems = height * nominal_full_width

    # Fast path: one or more complete nominal frames -> keep last frame.
    if raw_data.size >= nominal_frame_elems:
        n_full_frames = raw_data.size // nominal_frame_elems
        if n_full_frames >= 1:
            start = (n_full_frames - 1) * nominal_frame_elems
            frame = raw_data[start:start + nominal_frame_elems]
            raw_2d_16bit = frame.reshape((height, nominal_full_width))[:, :width]
            return raw_2d_16bit

    # Fallback: infer row width from available data (handles slightly short frame).
    inferred_full_width = raw_data.size // height
    usable_elems = inferred_full_width * height
    if inferred_full_width < width or usable_elems <= 0:
        raise ValueError(
            f"RAW frame too small or malformed: elems={raw_data.size}, "
            f"inferred_full_width={inferred_full_width}, required_width={width}"
        )
    frame = raw_data[:usable_elems]
    raw_2d_16bit = frame.reshape((height, inferred_full_width))[:, :width]
    return raw_2d_16bit
    
def extract_B_raw(sensor_raw,height=3040,width=4056):
    H,W = sensor_raw.shape
    assert H ==height and W==width
    B = sensor_raw[0::2, 0::2]
    output_b = np.empty_like(sensor_raw)
    output_b[0::2, 0::2] = B
    output_b[0::2, 1::2] = B
    output_b[1::2, 0::2] = B
    output_b[1::2, 1::2] = B
    return output_b

def extract_R_raw(sensor_raw,height=3040,width=4056):
    H,W = sensor_raw.shape
    assert H ==height and W==width
    R = sensor_raw[1::2, 1::2]
    output_r = np.empty_like(sensor_raw)
    output_r[0::2, 0::2] = R
    output_r[0::2, 1::2] = R
    output_r[1::2, 0::2] = R
    output_r[1::2, 1::2] = R
    return output_r

def extract_G_raw(sensor_raw,height=3040,width=4056):
    H,W = sensor_raw.shape
    assert H ==height and W==width
    G1 = sensor_raw[0::2, 1::2]
    G2 = sensor_raw[1::2, 0::2]

    # prevent overflow
    G = ((G1.astype(np.uint32) + G2.astype(np.uint32)) // 2).astype(sensor_raw.dtype)
    output_g = np.empty_like(sensor_raw)
    output_g[0::2, 0::2] = G
    output_g[0::2, 1::2] = G
    output_g[1::2, 0::2] = G
    output_g[1::2, 1::2] = G
    return output_g

def extract_G1_raw(sensor_raw,height=3040,width=4056):
    H,W = sensor_raw.shape
    assert H ==height and W==width
    G1 = sensor_raw[0::2, 1::2]
    output_g = np.empty_like(sensor_raw)
    output_g[0::2, 0::2] = G1
    output_g[0::2, 1::2] = G1
    output_g[1::2, 0::2] = G1
    output_g[1::2, 1::2] = G1
    return output_g

def extract_G2_raw(sensor_raw,height=3040,width=4056):
    H,W = sensor_raw.shape
    assert H ==height and W==width
    G2 = sensor_raw[1::2, 0::2]
    output_g = np.empty_like(sensor_raw)
    output_g[0::2, 0::2] = G2
    output_g[0::2, 1::2] = G2
    output_g[1::2, 0::2] = G2
    output_g[1::2, 1::2] = G2
    return output_g
def extract_masked_mean(raw_chan,camera):
    if camera=='cam1':
        ROI_PATH = CAM1_ROI_NPY
    if camera=='cam0':
        ROI_PATH= CAM0_ROI_NPY
    roi = np.load(ROI_PATH)
    if camera == 'cam0':
        roi = np.fliplr(roi)
    mean_ = raw_chan[roi==1].mean()
    return mean_
    
def save_as_jpg(input_2d,output_file):
    plt.imshow(input_2d,cmap='gray')
    plt.savefig(output_file)
def adjust_shutter_gain(shutter,gain, change_factor):
    min_shutter, max_shutter = 1.0, 1000.0
    min_gain, max_gain = 1.12, 8.0

    shutter = float(shutter)
    gain = float(gain)
    factor = float(change_factor)

    if not np.isfinite(factor) or factor <= 0:
        factor = 1.0

    target_shutter = shutter * factor
    if min_shutter <= target_shutter <= max_shutter:
        print('adjust the shutter')
        new_shutter = target_shutter
        new_gain = gain
    else:
        # Saturate shutter first, then apply residual factor on gain.
        if target_shutter > max_shutter:
            new_shutter = max_shutter
        else:
            new_shutter = min_shutter

        if shutter > 0:
            residual_factor = factor / (new_shutter / shutter)
        else:
            residual_factor = factor

        target_gain = gain * residual_factor
        new_gain = min(max(target_gain, min_gain), max_gain)

        if new_gain != gain:
            print('adjust the gain')
        else:
            print('cannot adjust further (at limits)')

    new_shutter = str(int(round(new_shutter)))
    new_gain = f"{new_gain:.2f}".rstrip("0").rstrip(".")
    return new_shutter, new_gain
    
    
