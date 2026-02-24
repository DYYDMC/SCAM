import numpy as np
import matplotlib.pyplot as plt
def cut_raw_black_lines(img_filename,stride=8128,height=3040,width=4056):
    ## parse the bytes
    ## take the H,W part only (the rest columns are black for ?
    row_bytes = stride
    frame_bytes = row_bytes * height
    with open(img_filename, 'rb') as f:
        f.seek(0 * frame_bytes)
        raw_frame = f.read(frame_bytes)
    raw_data = np.frombuffer(raw_frame, dtype=np.uint16)
    full_width = stride // 2  # since each pixel is 2 bytes
    raw_2d_16bit = raw_data.reshape((height, full_width))[:, :width]
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
def save_as_jpg(input_2d,output_file):
        plt.imshow(input_2d,cmap='gray')
        if "cam0" in output_file:
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
    
    
