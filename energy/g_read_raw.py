import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import os
HOME = os.path.expanduser("~")
SCAM_PATH = os.path.join(HOME, "Github", "SCAM")
ENERGY_PATH = os.path.join(SCAM_PATH, 'energy')

def read_frame_with_stride(raw_file, frame_idx=0, width=4056, height=3040, stride=8128, dtype=np.uint16):
    """
    Reads a single frame from a multi-frame raw file with stride-aware unpacking.
    Assumes 16-bit unpacked SBGGR16 format.
    
    Parameters:
        raw_file (str): Path to the .raw file.
        frame_idx (int): Index of the frame to read (0-based).
        width (int): Width of the image in pixels.
        height (int): Height of the image in pixels.
        stride (int): Bytes per row (may be more than width * 2).
        dtype: Data type of the pixel values (np.uint16 for SBGGR16).
    Returns:
        np.ndarray: Image array of shape (height, width).
    """
    row_bytes = stride
    frame_bytes = row_bytes * height

    with open(raw_file, 'rb') as f:
        f.seek(frame_idx * frame_bytes)
        raw_frame = f.read(frame_bytes)

    # Convert to 1D array of 16-bit unsigned ints
    raw_data = np.frombuffer(raw_frame, dtype=dtype)

    # Reshape to (height, stride//2) and crop to (height, width)
    full_width = stride // 2  # since each pixel is 2 bytes
    raw_2d = raw_data.reshape((height, full_width))
    image = raw_2d[:, :width]  # Crop to actual width

    return image

#clean_gain_toPlot = []
shutters=[1,5,10,20,30,50,100,300,500,999] # green has fewer shutter times
ags= [1,1.1,1.2,1.5,2,4,6,8]
#shutters1=[1,5,10,15,20,30,40,50,80,100]
#shutters1=np.arange(100,2100,100)
#ags = [1,1.1,1.2,1.3,1.4,1.5,1.8,2,2.5,3,4,5,6,7,8]
#for powerLevel in [10]:
for powerLevel in [10,20,50,75,100]:
    G_RAW_PATH = os.path.join(ENERGY_PATH,f'G{powerLevel}')
    mean_pxl = np.zeros((len(shutters),len(ags)))
    for mm,ms in enumerate(shutters):
    #for ms in [1,30,999]:#:shutters1:
        #for ag in [1]:
        for aa,ag in enumerate(ags):
            raw_path = os.path.join(G_RAW_PATH,f"g_{str(ms)}ms_gain{str(ag)}.raw")
            print(raw_path)
            frame = read_frame_with_stride(raw_path, frame_idx=0)
            deNoise_frame = np.where(frame<4096,0,frame-4096)
            
            plt.figure(figsize=(10, 4)) 
            ax = plt.subplot(121)

            im = ax.imshow(deNoise_frame, cmap='gray')
            plt.colorbar(im)
            ax.set_title('raw', fontsize=16)

            # square definition
            y_center, x_center = 1000, 3000
            half_size = 500

            x0 = x_center - half_size
            y0 = y_center - half_size
            width = height = 2 * half_size

            rect = Rectangle(
                (x0, y0),
                width,
                height,
                linewidth=1,
                edgecolor='red',
                facecolor='none'
            )

            ax.add_patch(rect)
            figname = raw_path.replace('.raw','.png')

            plt.subplot(122)
            selected_area = deNoise_frame[y_center-half_size:y_center+half_size,x_center-half_size:x_center+half_size]
            print(selected_area.shape)
            data =selected_area.flatten()
            print(y_center-half_size,y_center+half_size)
            print(data.shape)
            # data = deNoise_frame.flatten()
            bin_edges = np.linspace(0, 65520-4096, 50)
            counts, edges = np.histogram(data, bins=bin_edges)
            plt.hist(data, bins=edges, edgecolor='black')
            plt.xlim([0,65520-4096])
            plt.savefig(figname)
            mean_deNoise_pxelValue = np.sum(data)/half_size/2/half_size/2
            # print(f'min: {np.min(frame)}, max: {np.max(frame)}, max_wo_darkNoise: {np.max(frame)-np.min(frame)}, gain: {ag}, shutter: {ms}ms')
            # clean_gain_toPlot.append(np.max(frame)-np.min(frame))
            print(f'min: {np.min(data)}, max: {np.max(data)}, mean_pxlValue: {mean_deNoise_pxelValue}, gain: {ag}, shutter: {ms}ms')
            #clean_gain_toPlot.append(np.sum(deNoise_frame/3040/4056))

            del frame
            mean_pxl[mm,aa]=mean_deNoise_pxelValue
            plt.close()
    print(mean_pxl.shape,mean_pxl)
    np.save(os.path.join(G_RAW_PATH,f'G{powerLevel}_mean_pxlValue.npy'),mean_pxl)