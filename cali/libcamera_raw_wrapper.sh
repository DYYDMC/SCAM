#!/bin/bash
source "$(dirname "${BASH_SOURCE[0]}")/../cam_roi/camera_config.sh"
CAM_ROI_PATH="$(dirname "${BASH_SOURCE[0]}")/../cam_roi"
CALI_PATH="$(dirname "${BASH_SOURCE[0]}")/../cali"
CAMERA_CONFIG_PATH="${CAM_ROI_PATH}/camera_config.sh"
source "$CAMERA_CONFIG_PATH"
SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"

# Main execution logic
echo "capture raw1?: $1" # caputre_raw
echo "camera id2?: $2" # 0 camera id
echo "gain3?: $3" # 1.2 gain
echo "shutterms4?: $4" # 30 ms
echo "outputdir5?: $5" # output dir
echo "imgid6?: $6" # image index

# using configs from the energy folder, flipping applied
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
        --shutter "${4}"ms \
        --config "$RAW_CONFIG_PATH" \
        --metadata "${5}/cam${2}_gain${3}_${4}ms_${6}.json" \
        --timeout "$TIMEOUT_MS" \
        -o "${5}/cam${2}_gain${3}_${4}ms_${6}.raw"

elif [[ -z "$1" ]]; then
    echo "Default capture"
else
    echo "Unknown command: $1"
    exit 1
fi