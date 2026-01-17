#!/bin/bash
source "$(dirname "${BASH_SOURCE[0]}")/../cam_roi/camera_config.sh"
CAM_ROI_PATH="$(dirname "${BASH_SOURCE[0]}")/../cam_roi"
CALI_PATH="$(dirname "${BASH_SOURCE[0]}")/../cali"
CAMERA_CONFIG_PATH="${CAM_ROI_PATH}/camera_config.sh"
source "$CAMERA_CONFIG_PATH"
SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"

# Main execution logic
echo "$1" # caputre_raw
echo "$2" # 0 camera id
echo "$3" # 1.2 gain
echo "$4" # 30 ms
#
if [[ "$2" == "0" ]]; then
    echo "Using camera 0"
    RAW_CONFIG_PATH="$(dirname "${BASH_SOURCE[0]}")/../energy/green_raw_config.txt"
else
    echo "Using camera 1"
    RAW_CONFIG_PATH="$(dirname "${BASH_SOURCE[0]}")/../energy/uv_raw_config.txt"
fi

echo "$4"
if [[ "$4" -ge 500 ]]; then
    TIMEOUT_MS=2000
else
    TIMEOUT_MS=1000
fi
if [[ "$1" == "capture_raw" ]]; then
    echo "take a RAW photo with the green camera"
    check_and_kill_libcamera

    libcamera-raw \
        --analoggain "${3}" \
        --shutter "${4}" \
        --config "$RAW_CONFIG_PATH" \
        --metadata "./cam${2}_gain${3}_${4}ms.json" \
        --timeout "$TIMEOUT_MS" \
        -o "./cam${2}_gain${3}_${4}ms.raw"

elif [[ -z "$1" ]]; then
    echo "Default capture"
else
    echo "Unknown command: $1"
    exit 1
fi