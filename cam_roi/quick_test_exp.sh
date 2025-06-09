#!/bin/bash
source camera_config.sh
SHUTTER_CAM0=16000
SHUTTER_CAM1=1000
# echo $SHUTTER_CAM1
# ## ?exposure detection
# echo $MIN_AGAIN
# # Parallel calls
# over_exposure_check_new "0" "$SHUTTER_CAM0" "$MIN_AGAIN" 2>/dev/null > cam0_tmp.txt
# over_exposure_check_new "1" "$SHUTTER_CAM1" "$MIN_AGAIN" 2>/dev/null > cam1_tmp.txt &
# wait

# # Read back both shutter and gain values
# read SHUTTER_CAM0 AGAIN_CAM0 < <(tail -n 1 cam0_tmp.txt)
# read SHUTTER_CAM1 AGAIN_CAM1 < <(tail -n 1 cam1_tmp.txt)


# # # rm cam0_tmp.txt cam1_tmp.txt
# # echo "!!!!!!FINISHED ADJUSTING EXPOSURE TIME SHUTTER_CAM0: $SHUTTER_CAM0 !!!!!!!!!"
# # echo "!!!!!!FINISHED ADJUSTING EXPOSURE TIME SHUTTER_CAM1: $SHUTTER_CAM1 !!!!!!!!!"
# echo $SHUTTER_CAM0
# echo $AGAIN_CAM0
# # echo $SHUTTER_CAM1
# # echo "Both cameras have finished adjusting exposure."

#!/bin/bash


while [[ "$CAM0_goodExp" != true || "$CAM1_goodExp" != true ]]; do
    echo "Running exposure checks..."

    # Launch exposure checks in parallel
    over_exposure_check_new "0" "$SHUTTER_CAM0" "$MIN_AGAIN" > cam0_tmp.txt 2>/dev/null
    echo $? > cam0_status.txt &

    over_exposure_check_new "1" "$SHUTTER_CAM1" "$MIN_AGAIN" > cam1_tmp.txt 2>/dev/null
    echo $? > cam1_status.txt &

    wait  # Wait for both checks to finish

    # Evaluate cam0
    if [[ $(cat cam0_status.txt) -eq 0 ]]; then
        read SHUTTER_CAM0 AGAIN_CAM0 < <(tail -n 1 cam0_tmp.txt)
        echo "Cam 0 exposure success: $SHUTTER_CAM0 $AGAIN_CAM0"
        CAM0_goodExp=true
    else
        echo "Cam 0 exposure FAILED"
        CAM0_goodExp=false
    fi

    # Evaluate cam1
    if [[ $(cat cam1_status.txt) -eq 0 ]]; then
        read SHUTTER_CAM1 AGAIN_CAM1 < <(tail -n 1 cam1_tmp.txt)
        echo "Cam 1 exposure success: $SHUTTER_CAM1 $AGAIN_CAM1"
        CAM1_goodExp=true
    else
        echo "Cam 1 exposure FAILED"
        CAM1_goodExp=false
    fi

    # If either one failed, wait and try again
    if [[ "$CAM0_goodExp" != true || "$CAM1_goodExp" != true ]]; then
        echo "Waiting 30 seconds before retrying..."
        sleep 30
    fi
done

# Cleanup
# rm -f cam0_tmp.txt cam1_tmp.txt cam0_status.txt cam1_status.txt

echo "✅ Both cameras successfully calibrated!"
