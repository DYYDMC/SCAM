#!/bin/bash
shutters1=(1ms 5ms 10ms 20ms 30ms 50ms 100ms 300ms)
shutters2=(500ms 999ms)
shutters3=(1ms 30ms)
shutters4=(999ms)

# ags=(1 4 8)
ags=(1 1.1 1.2 1.5 2 4 6 8)
for ag in "${ags[@]}"; do
    for s in "${shutters1[@]}"; do
        libcamera-raw \
            --analoggain "$ag" \
            --shutter "$s" \
            --config ./green_raw_config.txt \
            --metadata "g_${s}_gain${ag}.json" \
            --timeout 1000ms \
            -o "g_${s}_gain${ag}.raw"
        sleep 2
    done
    for s in "${shutters2[@]}"; do
        libcamera-raw \
            --analoggain "$ag" \
            --shutter "$s" \
            --config ./green_raw_config.txt \
            --metadata "g_${s}_gain${ag}.json" \
            --timeout 2000ms \
            -o "g_${s}_gain${ag}.raw"
        sleep 2
    done
done
