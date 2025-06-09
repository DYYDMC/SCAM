#!/bin/bash
source camera_config.sh

# Prompt for common parameters
echo "=== Common Parameters ==="
echo "recording location: "
read LOCATION
LOCATION=${LOCATION:-test}

FORMAT=h264
IFMETADATA=0


## Overexposure detection
echo "!!!!!!!!!!!!!!!2 Overexposure detection starts!!!!!!!!!!!!!!."
# Launch both exposure checks in parallel
over_exposure_check_new "0" "$MAX_SHUTTER" "$MIN_AGAIN" > cam0_tmp.txt 2>/dev/null
echo $? > cam0_status.txt &

over_exposure_check_new "1" "$MAX_SHUTTER" "$MIN_AGAIN" > cam1_tmp.txt 2>/dev/null
echo $? > cam1_status.txt &

wait  # wait for both jobs to finish

# Check return status before reading shutter/gain
if [[ $(cat cam0_status.txt) -eq 0 ]]; then
    read SHUTTER_CAM0 AGAIN_CAM0 < <(tail -n 1 cam0_tmp.txt)
    echo "Cam 0 exposure success: $SHUTTER_CAM0 $AGAIN_CAM0"
else
    echo "Cam 0 exposure FAILED"
fi

if [[ $(cat cam1_status.txt) -eq 0 ]]; then
    read SHUTTER_CAM1 AGAIN_CAM1 < <(tail -n 1 cam1_tmp.txt)
    echo "Cam 1 exposure success: $SHUTTER_CAM1 $AGAIN_CAM1"
else
    echo "Cam 1 exposure FAILED"
fi

# ## offical recording start
echo "+++++++++++++++++official recording starts   +++++++++++++++++++++++++++++"
# Get current date in format like "22Feb25_14-30-15"
DATE=$(date '+%d%b%y_%H%M%S')

check_and_kill_libcamera
capture_still() {
    local output_file=$1
    local record_time=$2
    local exposure_time=$3
    local camera_id=$4
    local again=$5
    ROI=$(set_roi "$camera_id")

    libcamera-still \
        --width $W \
        --height $H \
        --roi "$ROI" \
        --awb custom \
        --awbgain 1,1 \
        --analoggain $again \
        --denoise off \
        --hdr off \
        --brightness 0 \
        --contrast 1 \
        --saturation 1 \
        --sharpness 1 \
        --autofocus-mode manual \
        --lens-position $LENS \
        --camera "$camera_id" \
        --timeout "$record_time" \
        --shutter "$exposure_time" \
        --output "$output_file"
}


capture_still "cam0."$FORMAT 1000 $SHUTTER_CAM0 0 $AGAIN_CAM0
