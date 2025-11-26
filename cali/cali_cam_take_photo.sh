#!/bin/bash
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
    local output_file="${CALI_PATH}/SCAM_skt_cam${camera_id}.jpg"
    echo "Capturing to: $output_file"
    ROI=$(set_roi "$camera_id")
    echo "ROI: $ROI"
    
    libcamera-still \
        --width 2028 \
        --height 3040 \
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
        --shutter "$exposure_time" \
        --camera $camera_id \
        -n 1 \
        --output "$output_file"
}

# Main execution logic
if [[ "$1" == "capture_still" ]]; then
    echo 'take a photo with the green camera'
    check_and_kill_libcamera
    capture_still "$2" "$3"
elif [[ "$1" == "" ]]; then
    echo 'Default capture'
    capture_still 0 33000
else
    echo "Unknown command: $1"
    exit 1
fi
