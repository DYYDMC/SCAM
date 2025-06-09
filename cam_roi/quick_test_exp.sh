#!/bin/bash
source camera_config.sh

# Set initial values and max shutter (10s = 10,000,000 µs)
SHUTTER_CAM0=16000
SHUTTER_CAM1=1000
MAX_SHUTTER=10000000

while [[ "$CAM0_goodExp" != true || "$CAM1_goodExp" != true ]]; do
    echo "Running exposure checks..."

    over_exposure_check_new "0" "$SHUTTER_CAM0" "$MIN_AGAIN" > cam0_tmp.txt 2>/dev/null
    echo $? > cam0_status.txt &

    over_exposure_check_new "1" "$SHUTTER_CAM1" "$MIN_AGAIN" > cam1_tmp.txt 2>/dev/null
    echo $? > cam1_status.txt &

    wait

    if [[ $(cat cam0_status.txt) -eq 0 ]]; then
        read NEW_SHUTTER0 NEW_AGAIN0 < <(tail -n 1 cam0_tmp.txt)
        if (( NEW_SHUTTER0 <= MAX_SHUTTER )); then
            SHUTTER_CAM0=$NEW_SHUTTER0
            AGAIN_CAM0=$NEW_AGAIN0
        else
            SHUTTER_CAM0=$MAX_SHUTTER
        fi
        echo "Cam 0 exposure success: $SHUTTER_CAM0 $AGAIN_CAM0"
        CAM0_goodExp=true
    else
        echo "Cam 0 exposure FAILED"
        CAM0_goodExp=false
    fi

    if [[ $(cat cam1_status.txt) -eq 0 ]]; then
        read NEW_SHUTTER1 NEW_AGAIN1 < <(tail -n 1 cam1_tmp.txt)
        if (( NEW_SHUTTER1 <= MAX_SHUTTER )); then
            SHUTTER_CAM1=$NEW_SHUTTER1
            AGAIN_CAM1=$NEW_AGAIN1
        else
            SHUTTER_CAM1=$MAX_SHUTTER
        fi
        echo "Cam 1 exposure success: $SHUTTER_CAM1 $AGAIN_CAM1"
        CAM1_goodExp=true
    else
        echo "Cam 1 exposure FAILED"
        CAM1_goodExp=false
    fi

    if [[ "$CAM0_goodExp" != true || "$CAM1_goodExp" != true ]]; then
        echo "Waiting 30 seconds before retrying..."
        sleep 30
    fi
done

echo "✅ Both cameras successfully calibrated!"

