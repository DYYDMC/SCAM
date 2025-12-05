#!/bin/bash

# Load configuration from same directory
source "$(dirname "${BASH_SOURCE[0]}")/camera_config.sh"

SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"

SHUTTER_CAM0=500000
SHUTTER_CAM1=1000000
AGAIN_CAM0=5.82
AGAIN_CAM1=5.12

capture_still() {
    local img_index=$1
    local camera_id=$2
    local exposure_time=$3
    local again=$4
    local output_file="${SCRIPT_DIR}/secondTry9x6${camera_id}_${img_index}.jpg"
    libcamera-still \
        --width 4056 \
        --height 3040 \
        --roi 0,0,1,1 \
        --awb custom \
        --awbgain 1,1 \
        --denoise off \
        --hdr off \
        --brightness 0 \
        --contrast 1 \
        --saturation 1 \
        --sharpness 1 \
        --timeout 3000 \
        --autofocus-mode manual \
        --lens-position $LENS \
        --shutter "$exposure_time" \
        --analoggain "$again" \
        --camera $camera_id \
        --output "$output_file"
}

## official recording start
echo "+++++++++++++++++official recording starts+++++++++++++++++++++++++++++"

check_and_kill_libcamera
# capture_still "cali" 0 
for i in {0..1}; do
    for cam in 1; do
        capture_still "$i" "$cam" "$SHUTTER_CAM1" "$AGAIN_CAM0"
        sleep 2
    done
done
# shutter0=$1
# shutter1=$2

# capture_still 0 0 "$shutter0" &
# capture_still 0 1 "$shutter1" &
wait

