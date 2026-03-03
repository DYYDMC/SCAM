import json
import os
import time

import numpy as np


class ScanWorkflows:
    def __init__(self, point_scan_data_path, pano_data_path, full_scam_path, one_scam_data_path,
                 full_scan_path, spec_tilt_pos):
        self.point_scan_data_path = point_scan_data_path
        self.pano_data_path = pano_data_path
        self.full_scam_path = full_scam_path
        self.one_scam_data_path = one_scam_data_path
        self.full_scan_path = full_scan_path
        self.spec_tilt_pos = spec_tilt_pos

    def start_full_scan(self, w):
        print("I AM HERE!! FULL SCAN!")
        start_time = time.strftime("%Y%m%d_%H%M%S")
        full_scan_save_path = os.path.join(self.full_scan_path, f"FULL_SCAN_{start_time}")
        os.makedirs(full_scan_save_path, exist_ok=True)
        try:
            w.on_update_parameters()
            w.pan_step = 1
            w.tilt_step = 1
            w.cam_path = w.calculate_pano_positions()
            np.savez(os.path.join(full_scan_save_path, "scan_positions.npz"), positions=w.cam_path)
            for idx, (pan, tilt) in enumerate(w.cam_path):
                w.current_pan, w.current_tilt = w.stepper_controller.read_pos()
                w.next_pan = pan
                w.next_tilt = tilt
                w.stepper_controller.move_to(w.next_pan, w.next_tilt)
                w.motor_wait()
                print(f"Moving to Pan: {pan}, Tilt: {tilt} ({idx+1}/{len(w.cam_path)})")
                w.int_oneScan = w.adjust_int_t(w.int_oneScan)
                result_ = w.spec_controller.scan(w.int_oneScan)
                result_["motor_pan"] = pan
                result_["motor_tilt"] = tilt
                result_["ts"] = time.strftime("%Y%m%d_%H%M%S")
                np.save(os.path.join(full_scan_save_path, f"full_scan_{idx}_{pan}_{tilt}"), result_)
                time.sleep(w.isi_oneScan)
        except Exception as e:
            print(f"Error during full scan: {str(e)}")

    def start_point_scan(self, w):
        start_time = time.strftime("%Y%m%d_%H%M%S")
        point_scan_save_path = os.path.join(self.point_scan_data_path, f"POINT_SCAN_{start_time}")
        sky_save_path = os.path.join(point_scan_save_path, "sky_scan")
        ground_save_path = os.path.join(point_scan_save_path, "ground_scan")
        loc_save_dict = {"sky": sky_save_path, "ground": ground_save_path}

        os.makedirs(point_scan_save_path, exist_ok=True)
        os.makedirs(sky_save_path, exist_ok=True)
        os.makedirs(ground_save_path, exist_ok=True)
        try:
            w.on_update_parameters()
            sky_tilt = w.tilt_max
            ground_tilt = w.tilt_min
            pan = w.pan_oneScan
            point_scan_iteration = 3
            point_scan_config = {
                "pan": pan,
                "sky_tilt": sky_tilt,
                "ground_tilt": ground_tilt,
                "num_iteration": point_scan_iteration,
            }
            with open(os.path.join(point_scan_save_path, "point_scan_config.json"), "w") as f:
                json.dump(point_scan_config, f, indent=4)

            print("Starting POINT SCAN:")
            int_t_dict = {"sky": w.int_oneScan, "ground": w.int_oneScan}
            for ii in range(point_scan_iteration):
                for tt, key in zip([sky_tilt, ground_tilt], ["sky", "ground"]):
                    w.current_pan, w.current_tilt = w.stepper_controller.read_pos()
                    w.next_pan = pan
                    w.next_tilt = tt
                    w.stepper_controller.move_to(w.next_pan, w.next_tilt)
                    w.motor_wait()
                    int_t_dict[key] = w.adjust_int_t(int_t_dict[key])
                    print(f"finished adjust_int_t(), now int_t for {key} tilt is {int_t_dict[key]}")
                    result_ = w.spec_controller.scan(int_t_dict[key])
                    result_["motor_pan"] = pan
                    result_["motor_tilt"] = tt
                    result_["ts"] = time.strftime("%Y%m%d_%H%M%S")
                    np.save(os.path.join(loc_save_dict[key], f"{key}_scan_{ii}"), result_)
                    time.sleep(w.isi_oneScan)
        except Exception as e:
            print(f"Error during POINT SCAN: {str(e)}")

    def start_pano(self, w):
        w.on_update_parameters()
        start_time = time.strftime("%Y%m%d_%H%M%S")
        pano_data_path = os.path.join(self.pano_data_path, f"PANO_{start_time}")
        os.makedirs(pano_data_path, exist_ok=True)
        cam0_data_path = os.path.join(pano_data_path, "cam0")
        cam1_data_path = os.path.join(pano_data_path, "cam1")
        os.makedirs(cam0_data_path, exist_ok=True)
        os.makedirs(cam1_data_path, exist_ok=True)

        print("Starting PANO...")
        w.cam_path = w.calculate_pano_positions()
        w.save_config(os.path.join(pano_data_path, "pano_config.json"))
        print(f"Total positions to take CAM photos: {len(w.cam_path)}")
        recalibrate_every = 4
        for idx, (pan, tilt) in enumerate(w.cam_path):
            w.current_pan, w.current_tilt = w.stepper_controller.read_pos()
            w.next_pan = pan
            w.next_tilt = tilt
            w.stepper_controller.move_to(w.next_pan, w.next_tilt)
            if w.current_tilt == w.next_tilt:
                pan_delta = abs(w.next_pan - w.current_pan)
                time.sleep(max(0.35, 0.08 * pan_delta + 0.25))
            else:
                w.motor_wait()
            print(f"Moving to Pan: {pan}, Tilt: {tilt} ({idx+1}/{len(w.cam_path)})")
            print(f"Taking pano (UV) photo no.{idx+1}/{len(w.cam_path)} at Pan: {pan}, Tilt: {tilt}")

            need_recalibrate = (
                idx == 0
                or (idx % recalibrate_every == 0)
                or w.cam0_shutter00 is None
                or w.cam0_gain00 is None
                or w.shutter1 is None
                or w.gain1 is None
            )
            if need_recalibrate:
                w.on_both_shoot(green_output_path=cam0_data_path, uv_output_path=cam1_data_path, img_idx=idx)
            else:
                sim_green_raw, sim_uv_raw = w.call_libcamera_raw_pair(
                    green_shutter=w.cam0_shutter00,
                    green_gain=w.cam0_gain00,
                    green_output_dir=cam0_data_path,
                    uv_shutter=w.shutter1,
                    uv_gain=w.gain1,
                    uv_output_dir=cam1_data_path,
                    img_idx=idx,
                )
                if sim_green_raw and sim_uv_raw and os.path.exists(sim_green_raw) and os.path.exists(sim_uv_raw):
                    w._save_jpg_from_raw(sim_green_raw, camera_id=0)
                    w._save_jpg_from_raw(sim_uv_raw, camera_id=1)
                else:
                    w.on_both_shoot(green_output_path=cam0_data_path, uv_output_path=cam1_data_path, img_idx=idx)
            print(f"Waiting for ISI: {w.isi}s before next position...")
        print("the full pano session completed.")

    def start_point_scam(self, w):
        num_cam = 80
        num_scan_iteration = 3
        start_time = time.strftime("%Y%m%d_%H%M%S")
        scam_data_path = os.path.join(self.one_scam_data_path, f"SCAM_{start_time}")
        os.makedirs(scam_data_path, exist_ok=True)
        cam0_data_path = os.path.join(scam_data_path, "cam0")
        cam1_data_path = os.path.join(scam_data_path, "cam1")
        scan_data_path = os.path.join(scam_data_path, "scan_data")
        os.makedirs(cam0_data_path, exist_ok=True)
        os.makedirs(cam1_data_path, exist_ok=True)
        os.makedirs(scan_data_path, exist_ok=True)

        print(f"Data will be saved to: {scam_data_path}")
        w.on_update_parameters()
        w.current_pan, w.current_tilt = w.stepper_controller.read_pos()
        w.next_pan = w.pan_oneScan
        w.next_tilt = w.tilt_oneScan
        print(f"Taking CAM at Pan: {w.pan_oneScan}, Tilt: {w.tilt_oneScan}")
        w.stepper_controller.move_to(w.pan_oneScan, w.tilt_oneScan)
        w.motor_wait()
        for cc in range(num_cam):
            w.current_pan, w.current_tilt = w.stepper_controller.read_pos()
            w.next_pan, w.next_tilt = w.pan_oneScan, w.tilt_oneScan
            w.stepper_controller.move_to(w.pan_oneScan, w.tilt_oneScan)
            w.motor_wait()
            w.cam1_mean1 = None
            print(f"Taking pano (UV) photo no.{cc+1}/{num_cam} at Pan: {w.pan_oneScan}, Tilt: {w.pan_oneScan}")
            w.on_both_shoot(green_output_path=cam0_data_path, uv_output_path=cam1_data_path, img_idx=cc)
            for ii in range(num_scan_iteration):
                for tilt in self.spec_tilt_pos:
                    w.current_pan, w.current_tilt = w.stepper_controller.read_pos()
                    w.next_pan, w.next_tilt = w.pan_oneScan, tilt
                    w.stepper_controller.move_to(w.next_pan, w.next_tilt)
                    w.motor_wait()
                    for _ in range(3):
                        measurement = w.spec_controller.scan(w.int_oneScan)
                        peak = measurement["intensity"].max()
                        if 0.25 * 16383 <= peak <= 0.75 * 16383:
                            break
                        factor = 0.5 * 16383 / peak
                        factor = max(0.5, min(2.0, factor))
                        new_int = int(w.int_oneScan * factor)
                        new_int = max(1, min(6000, new_int))
                        if new_int == w.int_oneScan:
                            break
                        w.int_oneScan = new_int
                    print(f"Integration time: {w.int_oneScan} ms")
                    result_ = w.spec_controller.scan(w.int_oneScan)
                    result_["motor_pan"] = w.pan_oneScan
                    result_["motor_tilt"] = tilt
                    result_["ts"] = time.strftime("%Y%m%d_%H%M%S")
                    np.save(os.path.join(scan_data_path, f"scan_iter{cc}_{ii}_pan{w.pan_oneScan}_tilt{tilt}"), result_)

    def start_full_scam(self, w):
        start_time = time.strftime("%Y%m%d_%H%M%S")
        full_scam_data_path = os.path.join(self.full_scam_path, f"SCAM_{start_time}")
        os.makedirs(full_scam_data_path, exist_ok=True)
        cam0_data_path = os.path.join(full_scam_data_path, "cam0")
        cam1_data_path = os.path.join(full_scam_data_path, "cam1")
        scan_data_path = os.path.join(full_scam_data_path, "scan_data")
        os.makedirs(cam0_data_path, exist_ok=True)
        os.makedirs(cam1_data_path, exist_ok=True)
        os.makedirs(scan_data_path, exist_ok=True)
        print(f"Data will be saved to: {full_scam_data_path}")
        w.on_update_parameters()
        w.cam_path = w.calculate_pano_positions()
        w.save_config(os.path.join(full_scam_data_path, "scam_config.json"))
        print(f"Total positions to take CAM photos: {len(w.cam_path)}")
        for idx, (pan, tilt) in enumerate(w.cam_path):
            print(f"Moving to Pan: {pan}, Tilt: {tilt} ({idx+1}/{len(w.cam_path)})")
            w.current_pan, w.current_tilt = w.stepper_controller.read_pos()
            w.next_pan = pan
            w.next_tilt = tilt
            w.stepper_controller.move_to(w.next_pan, w.next_tilt)
            w.motor_wait()
            print(f"Taking photo scan no.{idx+1}/{len(w.cam_path)} at Pan: {pan}, Tilt: {tilt}")
            w.on_both_shoot(green_output_path=cam0_data_path, uv_output_path=cam1_data_path, img_idx=idx)
            print("finished simultaneous replacement photo pair")
            if len(self.spec_tilt_pos) > 0:
                print("Performing spectral scan...")
                for tilt_scan in self.spec_tilt_pos:
                    w.current_pan, w.current_tilt = w.stepper_controller.read_pos()
                    w.next_pan = pan
                    w.next_tilt = tilt_scan
                    w.stepper_controller.move_to(w.next_pan, w.next_tilt)
                    w.motor_wait()
                    w.int_oneScan = w.adjust_int_t(w.int_oneScan)
                    result = w.spec_controller.scan(w.int_oneScan)
                    if result:
                        data_filename = os.path.join(scan_data_path, f"photo{idx}_scan_pan{pan}_tilt{tilt_scan}.npz")
                        np.savez(data_filename, wavelength=result["wavelengths"], intensity=result["intensity"])
                    else:
                        print(f"Scan failed at Pan: {pan}, Tilt: {tilt} - {result['error']}")
                    print(f"Waiting for ISI: {w.isi}s before next position...")
                    time.sleep(w.isi)
        print("the full SCAM session completed.")
