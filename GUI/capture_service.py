import os
import subprocess
import time

from raw.raw_prepro import cut_raw_black_lines, extract_B_raw, extract_G_raw, save_as_jpg


class CaptureService:
    def __init__(self, wrapper_script_path):
        self.wrapper_script_path = wrapper_script_path

    def call_libcamera_raw(self, camera_id, shutter, gain, output_dir, img_idx):
        cmd = [
            "/bin/bash",
            self.wrapper_script_path,
            "capture_raw",
            str(camera_id),
            str(gain),
            str(shutter),
            output_dir,
            str(img_idx),
        ]
        fname = f"{output_dir}/cam{camera_id}_gain{gain}_{shutter}ms_{img_idx}.raw"
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                if attempt > 1:
                    backoff = 0.4 * attempt
                    print(f"Retrying capture attempt {attempt}/{max_attempts} after {backoff:.1f}s backoff")
                    time.sleep(backoff)
                else:
                    # Small pacing delay reduces camera pipeline thrash between rapid calls.
                    time.sleep(0.25)

                subprocess.run(
                    cmd,
                    check=True,
                    timeout=35,
                    capture_output=True,
                    text=True,
                )
                for _ in range(10):
                    if os.path.exists(fname):
                        break
                    time.sleep(0.3)
                if os.path.exists(fname):
                    return fname
                print(f"Capture succeeded but output file not found yet: {fname}")
            except subprocess.TimeoutExpired:
                print("Photo capture timed out")
            except subprocess.CalledProcessError as e:
                print(f"Error: {e.stderr}")
            except Exception as e:
                print(f"Unexpected error: {e}")
        return fname

    def call_libcamera_raw_pair(self, green_shutter, green_gain, green_output_dir,
                                uv_shutter, uv_gain, uv_output_dir, img_idx):
        try:
            cmd = [
                "/bin/bash",
                self.wrapper_script_path,
                "capture_raw_pair",
                str(green_gain),
                str(green_shutter),
                green_output_dir,
                str(uv_gain),
                str(uv_shutter),
                uv_output_dir,
                str(img_idx),
            ]
            subprocess.run(
                cmd,
                check=True,
                timeout=45,
                capture_output=True,
                text=True,
            )
            green_raw = f"{green_output_dir}/cam0_gain{green_gain}_{green_shutter}ms_{img_idx}.raw"
            uv_raw = f"{uv_output_dir}/cam1_gain{uv_gain}_{uv_shutter}ms_{img_idx}.raw"
            return green_raw, uv_raw
        except subprocess.TimeoutExpired:
            print("Simultaneous photo capture timed out")
        except subprocess.CalledProcessError as e:
            print(f"Simultaneous capture failed: {e.stderr}")
        except Exception as e:
            print(f"Unexpected simultaneous capture error: {e}")
        return None, None

    def remove_capture_pair(self, raw_file):
        if raw_file and os.path.exists(raw_file):
            os.remove(raw_file)
        meta_file = raw_file.replace(".raw", ".json") if raw_file else None
        if meta_file and os.path.exists(meta_file):
            os.remove(meta_file)
        if raw_file:
            base = raw_file.replace(".raw", "")
            for jpg_file in (f"{base}_G.jpg", f"{base}_B.jpg", f"{base}.jpg"):
                if os.path.exists(jpg_file):
                    os.remove(jpg_file)

    def save_jpg_from_raw(self, raw_file, camera_id):
        if not raw_file or not os.path.exists(raw_file):
            return
        raw_2d = cut_raw_black_lines(raw_file)
        if int(camera_id) == 0:
            chan = extract_G_raw(raw_2d)
            save_as_jpg(chan, raw_file.replace(".raw", "_G.jpg"))
        else:
            chan = extract_B_raw(raw_2d)
            save_as_jpg(chan, raw_file.replace(".raw", "_B.jpg"))

    def promote_capture_pair(self, raw_file, final_dir):
        if not raw_file:
            return None
        final_raw = os.path.join(final_dir, os.path.basename(raw_file))
        meta_src = raw_file.replace(".raw", ".json")
        meta_dst = final_raw.replace(".raw", ".json")
        if os.path.exists(raw_file):
            os.replace(raw_file, final_raw)
        if os.path.exists(meta_src):
            os.replace(meta_src, meta_dst)
        return final_raw
