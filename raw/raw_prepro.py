import numpy as np
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
    G = ((G1.astype(np.uint16) + G2.astype(np.uint16)) // 2).astype(sensor_raw.dtype)
    output_g = np.empty_like(sensor_raw)
    output_g[0::2, 0::2] = G
    output_g[0::2, 1::2] = G
    output_g[1::2, 0::2] = G
    output_g[1::2, 1::2] = G
    return output_g

def adjust_shutter_gain(shutter,gain, increase_factor):
    if float(shutter)*increase_factor<=1000:
        new_shutter = str(shutter*increase_factor)
        new_gain = gain
    elif float(gain)*increase_factor<8:
        new_gain = str(int(gain*increase_factor*0.8)+1)
        new_shutter = shutter
    else:
        new_shutter="1000"
        new_gain="8"
    return new_shutter,new_gain
    
    