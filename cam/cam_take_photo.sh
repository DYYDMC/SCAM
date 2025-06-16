#!/bin/bash
# bash takes:
# $1 absolute path of the output image file as the first argument
# $2 camera ID as the second argument
# $3 shutter speed in microseconds as the third argument
# $4 analog gain as the fourth argument
CAMERA_CONFIG_FILE="$(dirname "${BASH_SOURCE[0]}")/../cam_roi/camera_config.sh"
if [[ -r "$CAMERA_CONFIG_FILE" ]]; then
    source "$CAMERA_CONFIG_FILE"
else
    echo "Error: Cannot find or read $CAMERA_CONFIG_FILE"
    exit 1
fi
CAM_ROI_PATH="$(dirname "${BASH_SOURCE[0]}")/../cam_roi"
CAMERA_CONFIG_PATH="${CAM_ROI_PATH}/camera_config.sh"
source "$CAMERA_CONFIG_PATH"
SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"

echo 'HA inside of cam_take_photo.sh'
check_and_kill_libcamera

output_file=$1
camera_id=$2
shutter=$3
again=$4
echo $output_file

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
    --shutter $shutter \
    --analoggain $again \
    --camera $camera_id \
    -n 1 \
    -t 3000 \
    --output "$output_file"
