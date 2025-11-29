#!/bin/bash
# Shared Camera Configuration

# Default parameters
W=2018#2304
H=1520#2592
LENS=0.0
QUICK_W=1332#576
QUICK_H=990#324

# parameters for overexposure check
# SHUTTER_STEP=1000
SHUTTER_LIST=()
for (( val=1000; val<=33000; val+=2000 )); do
    SHUTTER_LIST+=($val)
done
OE_RECORD_TIME=300 # 300 ms for 1-3 frames

# parameter for segment recording
SEGMENT_DURATION=600000

# parameter for SHUTTER limits
CAM0_goodExp=false
CAM1_goodExp=false
MAX_SHUTTER=33000
MIN_SHUTTER=1000
MIN_AGAIN=1.12
GAIN_LIST=(1.12 2 3 4 5 6 7 8)

# Function to set ROI based on camera ID
set_roi() {
    local cam_id=$1
    local script_dir="$(dirname "${BASH_SOURCE[0]}")"
    local roi_file="${script_dir}/roi_cam${cam_id}.npy"
    if [[ -f "$roi_file" ]]; then
        python3 "${script_dir}/read_roi.py" "$roi_file"
    else
        echo "ROI file not found for camera ID $cam_id"
    fi
}

# Function to run libcamera-vid with predefined parameters
capture_video() {
    local output_file=$1
    local record_time=$2
    local exposure_time=$3
    local camera_id=$4
    local again=$5
    ROI=$(set_roi "$camera_id")

    libcamera-vid \
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

# Function to run libcamera-vid with predefined parameters
capture_EXP_video() {
    local output_file=$1
    local record_time=$2
    local exposure_time=$3
    local camera_id=$4
    local again=$5
    ROI=$(set_roi "$camera_id")
    echo "$ROI"
    # echo "I AM in capture_EXP_video for params: $output_file $record_time $exposure_time $camera_id $again"

    libcamera-vid \
        --width $QUICK_W \
        --height $QUICK_H \
        --roi "$ROI" \
        --awb custom \
        --awbgain 1,1 \
        --analoggain "$again" \
        --denoise off \
        --hdr off \
        -n 0 \
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
    
    # echo "finished!!!"
}

# Function to check and kill any existing libcamera-vid process
check_and_kill_libcamera() {
    # Gracefully terminate libcamera-vid
    if pkill -15 -f libcamera-vid >/dev/null 2>&1; then
        sleep 1
        if pgrep -f libcamera-vid >/dev/null 2>&1; then
            pkill -9 -f libcamera-vid >/dev/null 2>&1
            sleep 1
        fi
    fi

    # Ensure /dev/video4 is free
    if lsof /dev/video4 >/dev/null 2>&1; then
        sudo fuser -k /dev/video4 >/dev/null 2>&1  # Kill processes using it
        sleep 1
    fi

    # Wait for /dev/video4 to become available
    local retries=5
    while lsof /dev/video4 >/dev/null 2>&1 && (( retries-- > 0 )); do
        sleep 1
    done

    # Reload kernel module as a last resort
    if lsof /dev/video4 >/dev/null 2>&1; then
        sudo modprobe -r bcm2835-v4l2 >/dev/null 2>&1 && sudo modprobe bcm2835-v4l2 >/dev/null 2>&1
        sleep 1
    fi
}


# Function to get current time (HH:MM format)
get_current_time() {
    date +"%H:%M"
}

# Function to convert HH:MM to milliseconds since midnight
time_to_milliseconds() {
    echo $1 | awk -F: '{print ($1 * 3600000) + ($2 * 60000)}'
}

# Function to execute a recording segment
record_segment() {
    local segment_timeout=$1
    local segment_index=$2
    local camera_id=$3
    local shutter=$4
    local again=$5
    ROI=$(set_roi "$camera_id")

    local base_name="cam${camera_id}_${LOCATION}_${DATE}_${segment_index}"
    local video_file="${base_name}.${FORMAT}"
    local log_file="${base_name}.log"

    # Construct libcamera-vid command
    local cmd=(libcamera-vid
        --width "$W"
        --height "$H"
        --roi "$ROI"
        --awb custom
        --awbgain 1,1
        --analoggain "$again"
        --denoise off
        --hdr off
        --brightness 0
        --contrast 1
        --saturation 1
        --sharpness 1
        --autofocus-mode manual
        --shutter "$shutter"
        --lens-position "$LENS"
        --camera "$camera_id"
        --timeout "$segment_timeout"
        --framerate 30
        --output "$video_file"
        -n "$IFMETADATA"
        --info-text "Frame:%frame,Framerate:%fps,Exposure:%exp,Again:%ag,Dgain:%dg,Aelock:%aelock"
    )

    # Log and execute command
    echo "Executing: ${cmd[*]}" | tee -a "$log_file"
    "${cmd[@]}" 2>&1 | awk '{ print strftime("%Y%m%d_%H:%M:%S"), $0; fflush(); }' | tee -a "$log_file"
}
over_exposure_check_new() {
    local cam_id=$1
    local shutter=$2
    local again=$3
    local exposure_file="cam${cam_id}_overExp_tmp.h264"
    local result

    # Step 1: Try given shutter and min gain
    check_and_kill_libcamera
    capture_EXP_video "$exposure_file" "$OE_RECORD_TIME" "$shutter" "$cam_id" "$again"
    result=$(python3 over_exp_detect.py "$exposure_file" "$cam_id")
    echo "Initial result: $result with shutter=$shutter gain=$again"
    rm "$exposure_file"

    if [[ "$result" == "OK" ]]; then
        echo "$shutter $again"
        return 0

    elif [[ "$result" == "OVEREXPOSED" ]]; then
        # Binary search on SHUTTER_LIST
        local low_idx=0
        local high_idx=$((${#SHUTTER_LIST[@]} - 1))
        local mid_idx

        while (( high_idx - low_idx > 1 )); do
            mid_idx=$(( (low_idx + high_idx) / 2 ))
            shutter=${SHUTTER_LIST[$mid_idx]}
            echo "Binary shutter test: $shutter"

            check_and_kill_libcamera
            capture_EXP_video "$exposure_file" "$OE_RECORD_TIME" "$shutter" "$cam_id" "$again"
            result=$(python3 over_exp_detect.py "$exposure_file" "$cam_id")
            echo "Result: $result"
            rm "$exposure_file"

            if [[ "$result" == "OK" ]]; then
                echo "$shutter $again"
                return 0
            elif [[ "$result" == "OVEREXPOSED" ]]; then
                high_idx=$mid_idx
            else
                low_idx=$mid_idx
            fi
        done

        # Test high_idx as final attempt
        shutter=${SHUTTER_LIST[$high_idx]}
        check_and_kill_libcamera
        capture_EXP_video "$exposure_file" "$OE_RECORD_TIME" "$shutter" "$cam_id" "$again"
        result=$(python3 over_exp_detect.py "$exposure_file" "$cam_id")
        echo "Final shutter test: $shutter → $result"
        rm "$exposure_file"

        if [[ "$result" == "OK" ]]; then
            echo "$shutter $again"
        else
            echo "${SHUTTER_LIST[$low_idx]} $again"
        fi
        return 0

    elif [[ "$result" == "UNDEREXPOSED" ]]; then
        # Binary search on GAIN_LIST
        local low_idx=0
        local high_idx=$((${#GAIN_LIST[@]} - 1))
        local mid_idx

        while (( high_idx - low_idx > 1 )); do
            mid_idx=$(( (low_idx + high_idx) / 2 ))
            again=${GAIN_LIST[$mid_idx]}
            echo "Binary gain test: $again"

            check_and_kill_libcamera
            capture_EXP_video "$exposure_file" "$OE_RECORD_TIME" "$shutter" "$cam_id" "$again"
            result=$(python3 over_exp_detect.py "$exposure_file" "$cam_id")
            echo "Result: $result"
            rm "$exposure_file"

            if [[ "$result" == "OK" ]]; then
                echo "$shutter $again"
                return 0
            elif [[ "$result" == "UNDEREXPOSED" ]]; then
                low_idx=$mid_idx
            else
                high_idx=$mid_idx
            fi
        done

        # Test high_idx as final gain attempt
        again=${GAIN_LIST[$high_idx]}
        check_and_kill_libcamera
        capture_EXP_video "$exposure_file" "$OE_RECORD_TIME" "$shutter" "$cam_id" "$again"
        result=$(python3 over_exp_detect.py "$exposure_file" "$cam_id")
        echo "Final gain test: $again → $result"
        rm "$exposure_file"

        if [[ "$result" == "OK" ]]; then
            echo "$shutter $again"
        else
            echo "$shutter ${GAIN_LIST[$low_idx]}"
        fi
        return 0
    fi

    echo "No valid exposure found"
    echo "$shutter $again"
    return 1
}
