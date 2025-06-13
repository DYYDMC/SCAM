#!/bin/bash
source "$(dirname "${BASH_SOURCE[0]}")/../cam_roi/camera_config.sh"
CAM_ROI_PATH="$(dirname "${BASH_SOURCE[0]}")/../cam_roi"
CAMERA_CONFIG_PATH="${CAM_ROI_PATH}/camera_config.sh"
source "$CAMERA_CONFIG_PATH"
SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"

capture_still() {
    local timestamp_folder=$1
    local index=$2
    local camera_id=$3
    local exposure_time=$4
    local output_file="${SCRIPT_DIR}/${timestamp_folder}/cali_cam${camera_id}_vPos${index}.jpg"
    
    ROI=$(set_roi "$camera_id")
    echo "$ROI"
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
        --shutter "$exposure_time" \
        --camera $camera_id \
        --output "$output_file"
}

if [[ "$1" == "capture_still" ]]; then
    check_and_kill_libcamera
    capture_still "$2" "$3" "$4" "$5"
fi
# p2 = subprocess.Popen([bash_script, "capture_still", timestamp_folder, str(vv), "1", shutter1])