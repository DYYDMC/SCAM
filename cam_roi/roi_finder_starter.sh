#!/bin/bash

# Load configuration from same directory
source "$(dirname "${BASH_SOURCE[0]}")/camera_config.sh"

# Parse input
IDX="$1"
SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"
OUTFILE="${SCRIPT_DIR}/roi_${IDX}"

# Parameters
SHUTTER_CAM0=1000000
SHUTTER_CAM1=1000000
AGAIN_CAM0=1.12
AGAIN_CAM1=1.12

# Function to capture still image
capture_still() {
    local output_file="$1"
    local record_time="$2"
    local exposure_time="$3"
    local camera_id="$4"
    local again="$5"

    libcamera-still \
        --width 4608 \
        --height 2592 \
        --roi 0,0,1,1 \
        --awb custom \
        --awbgain 1,1 \
        --analoggain "$again" \
        --denoise off \
        --hdr off \
        --brightness 0 \
        --contrast 1 \
        --saturation 1 \
        --sharpness 1 \
        --autofocus-mode manual \
        --lens-position "$LENS" \
        --camera "$camera_id" \
        --timeout "$record_time" \
        --shutter "$exposure_time" \
        --output "$output_file"
}

# Start
echo "++++++++++++++ Official recording starts ++++++++++++++"
check_and_kill_libcamera

capture_still "${OUTFILE}cam0.jpg" 1000 "$SHUTTER_CAM0" 0 "$AGAIN_CAM0" &
capture_still "${OUTFILE}cam1.jpg" 1000 "$SHUTTER_CAM1" 1 "$AGAIN_CAM1" &
wait

