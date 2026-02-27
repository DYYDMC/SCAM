#!/bin/bash
BASE_DIR="$(dirname "${BASH_SOURCE[0]}")"
CAM_ROI_PATH="${BASE_DIR}/../cam_roi"
CALI_PATH="${BASE_DIR}/../cali"
CAMERA_CONFIG_PATH="${CAM_ROI_PATH}/camera_config.sh"
source "$CAMERA_CONFIG_PATH"

# Function to check and kill any existing libcamera-vid process
check_and_kill_libcamera() {
    local device_path="/dev/video4"
    local retries=5

    # Gracefully terminate libcamera-vid
    if pkill -15 -f libcamera-vid >/dev/null 2>&1; then
        sleep 1
        if pgrep -f libcamera-vid >/dev/null 2>&1; then
            pkill -9 -f libcamera-vid >/dev/null 2>&1
            sleep 1
        fi
    fi

    # Ensure the device is free
    while lsof "$device_path" >/dev/null 2>&1 && (( retries-- > 0 )); do
        sudo fuser -k "$device_path" >/dev/null 2>&1
        sleep 1
    done

    # Reload kernel module as a last resort
    if lsof "$device_path" >/dev/null 2>&1; then
        sudo modprobe -r bcm2835-v4l2 >/dev/null 2>&1 && sudo modprobe bcm2835-v4l2 >/dev/null 2>&1
        sleep 1
    fi
}

# Main execution logic
echo "capture raw1?: $1"
echo "camera id2?: $2"
echo "gain3?: $3"
echo "shutterms4?: $4"
echo "outputdir5?: $5"
echo "imgid6?: $6"

RAW_CONFIG_PATH="${BASE_DIR}/../energy/$( [[ "$2" == "0" ]] && echo "green" || echo "uv" )_raw_config.txt"

TIMEOUT_MS=$(( $4 >= 500 ? 2000 : 1000 ))

if [[ "$1" == "capture_raw" ]]; then
    if ! lsof /dev/video4 >/dev/null 2>&1; then
        check_and_kill_libcamera
    fi

    libcamera-raw \
        --analoggain "${3}" \
        --shutter "${4}"ms \
        --config "$RAW_CONFIG_PATH" \
        --metadata "${5}/cam${2}_gain${3}_${4}ms_${6}.json" \
        --timeout "$TIMEOUT_MS" \
        -o "${5}/cam${2}_gain${3}_${4}ms_${6}.raw"

    if [[ $? -ne 0 ]]; then
        echo "Error: libcamera-raw failed" >&2
        exit 1
    fi
elif [[ -z "$1" ]]; then
    echo "Default capture"
else
    echo "Unknown command: $1"
    exit 1
fi