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
elif [[ "$1" == "capture_raw_pair" ]]; then
    # Args:
    #   $2  cam0 gain
    #   $3  cam0 shutter (ms)
    #   $4  cam0 output dir
    #   $5  cam1 gain
    #   $6  cam1 shutter (ms)
    #   $7  cam1 output dir
    #   $8  image index
    if ! lsof /dev/video4 >/dev/null 2>&1; then
        check_and_kill_libcamera
    fi

    RAW_CONFIG_CAM0="${BASE_DIR}/../energy/green_raw_config.txt"
    RAW_CONFIG_CAM1="${BASE_DIR}/../energy/uv_raw_config.txt"

    TIMEOUT_CAM0=$(( $3 >= 500 ? 2000 : 1000 ))
    TIMEOUT_CAM1=$(( $6 >= 500 ? 2000 : 1000 ))

    libcamera-raw \
        --analoggain "${2}" \
        --shutter "${3}"ms \
        --config "$RAW_CONFIG_CAM0" \
        --metadata "${4}/cam0_gain${2}_${3}ms_${8}.json" \
        --timeout "$TIMEOUT_CAM0" \
        -o "${4}/cam0_gain${2}_${3}ms_${8}.raw" &
    PID_CAM0=$!

    libcamera-raw \
        --analoggain "${5}" \
        --shutter "${6}"ms \
        --config "$RAW_CONFIG_CAM1" \
        --metadata "${7}/cam1_gain${5}_${6}ms_${8}.json" \
        --timeout "$TIMEOUT_CAM1" \
        -o "${7}/cam1_gain${5}_${6}ms_${8}.raw" &
    PID_CAM1=$!

    wait "$PID_CAM0"
    STATUS_CAM0=$?
    wait "$PID_CAM1"
    STATUS_CAM1=$?

    if [[ $STATUS_CAM0 -ne 0 || $STATUS_CAM1 -ne 0 ]]; then
        echo "Error: simultaneous libcamera-raw capture failed (cam0=$STATUS_CAM0, cam1=$STATUS_CAM1)" >&2
        exit 1
    fi
elif [[ -z "$1" ]]; then
    echo "Default capture"
else
    echo "Unknown command: $1"
    exit 1
fi
