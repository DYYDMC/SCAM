import subprocess
import sys

def run_shell_script(script_path):
    try:
        subprocess.run(['bash', script_path], check=True)
        print(f"Successfully ran {script_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error running {script_path}: {e}")
        sys.exit(1)

def run_python_script(script_path):
    try:
        subprocess.run(['python3', script_path], check=True)
        print(f"Successfully ran {script_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error running {script_path}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_shell_script('./roi_finder_starter.sh')         # This .sh calls another .sh and generates 2 .jpg files
    run_python_script('./extract_cam_roi.py')       # This .py processes the images
