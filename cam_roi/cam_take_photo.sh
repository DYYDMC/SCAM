#!/bin/bash

# Load configuration from same directory
source "$(dirname "${BASH_SOURCE[0]}")/camera_config.sh"

SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"

capture_still() {
    local index=$1
    local camera_id=$2
    local output_file="${SCRIPT_DIR}/cam${camera_id}_${index}.jpg"
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
        --camera $camera_id \
        --output "$output_file"
}

## official recording start
echo "+++++++++++++++++official recording starts+++++++++++++++++++++++++++++"

check_and_kill_libcamera

for i in {0..1}; do
    for cam in 0 1; do
        capture_still "$i" "$cam"
    done
done

