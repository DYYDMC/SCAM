#!/bin/bash
source /home/ydeng/GitHub/rgbCamera/bash_scripts/camera_config.sh

OUTFILE="/home/ydeng/GitHub/rgbCamera/bash_scripts/cam0_deskAgain"
capture_still() {
    local output_file=$1
    local camera_id=$2
    ROI=$(set_roi "$camera_id")
    echo $ROI
    libcamera-still \
        --width 2304 \
        --height 2592 \
        --roi "$ROI" \
        --awb custom \
        --awbgain 1,1 \
        --denoise off \
        --hdr off \
        --brightness 0 \
        --contrast 1 \
        --saturation 1 \
        --sharpness 1 \
        --autofocus-mode manual \
        --lens-position $LENS \
        --camera $camera_id \
        --output "$output_file"
}
## offical recording start
echo "+++++++++++++++++official recording starts   +++++++++++++++++++++++++++++"

check_and_kill_libcamera

for i in {0..10}
do
echo $OUTFILE"$i.jpg"
capture_still $OUTFILE"$i.jpg" 0
done