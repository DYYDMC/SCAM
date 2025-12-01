#!/bin/bash

source "$(dirname "${BASH_SOURCE[0]}")/../cam_roi/camera_config.sh"
CAM_ROI_PATH="$(dirname "${BASH_SOURCE[0]}")/../cam_roi"
CALI_PATH="$(dirname "${BASH_SOURCE[0]}")/../cali"
CAMERA_CONFIG_PATH="${CAM_ROI_PATH}/camera_config.sh"
source "$CAMERA_CONFIG_PATH"
SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"

capture_still() {
    local camera_id=$1
    local exposure_time=$2
    local analoggain=$3
    local output_file="${CALI_PATH}/SCAM_skt_cam${camera_id}.jpg"
    echo "Capturing to: $output_file"
    
    libcamera-still \
        --width 4056 \
        --height 3040 \
        --awb custom \
        --awbgain 1,1 \
        --denoise off \
        --hdr off \
        --brightness 0 \
        --contrast 1 \
        --saturation 1 \
        --sharpness 1 \
        --autofocus-mode manual \
        --shutter "$exposure_time" \
        --analoggain "$analoggain" \
        --camera $camera_id \
        -n 1 \
        --output "$output_file"
}

# Main execution logic
if [[ "$1" == "capture_still" ]]; then
    echo 'take a photo with the green camera'
    check_and_kill_libcamera
    #  ... camera_id, exposure_time, gain
    capture_still "$2" "$3" "$3"
elif [[ "$1" == "" ]]; then
    echo 'Default capture'
    capture_still 0 33000
else
    echo "Unknown command: $1"
    exit 1
fi