# code 1
# Changes:
# - Added backup_output_folder and passed it to station2.main for optional timestamped backups.
# - Fallback now also writes a timestamped backup copy if the backup folder is provided.
# - Legacy behavior (cam2_bmp.bmp in output_folder) remains unchanged.

from station2 import main
import cv2
import numpy as np
import os
from datetime import datetime

# ==== Load Test Image ====
# image_path = r"D:\Pravi\burr_images\new_glass\station4\dataset\5_9_25\VCXG.2-32C\image0000504.bmp"
image_path = r"D:\PIM_25-09-25\Pravi_Flask\static\Cam1InputImages\input_backup_cam2\2025-10-05\12\cam2_2025-10-05_12-02-16.png.bmp"
frame = cv2.imread(image_path)

# ==== Parameters ====
part = "SUPPORT PISTON"
subpart = "28.10.019"
thick_min = "0.01"
thick_max = "5.70"
pixel_to_micron = "44"

# Primary output folder (legacy location for cam2_bmp.bmp)
output_folder = r"D:\PIM_25-09-25\Pravi_Flask\static\OutputImages\cam2output"

# New: configurable backup folder for timestamped copies
backup_output_folder = r"D:\PIM_25-09-25\Pravi_Flask\static\OutputImages\cam2output\cam2_output_backup"

# New threshold parameters (software-controlled)
min_thresh = "35"
max_thresh = "255"

# ==== Call the main() Function ====
result = main(
    part=part,
    subpart=subpart,
    frame=frame,
    thick_min=thick_min,
    thick_max=thick_max,
    pixel_to_micron=pixel_to_micron,
    output_folder=output_folder,
    min_thresh=min_thresh,
    max_thresh=max_thresh,
    backup_output_folder=backup_output_folder  # NEW
)

# ==== Output ====
print("\n--- Final Returned Output ---")
print(result)

# ==== Fallback: ensure cam2_bmp.bmp exists and write a backup copy ====
try:
    os.makedirs(output_folder, exist_ok=True)
    cam2_path = os.path.join(output_folder, "cam2_bmp.bmp")
    if not os.path.exists(cam2_path):
        if frame is not None:
            ok = cv2.imwrite(cam2_path, frame)
            print(f"Fallback wrote original to {cam2_path}: {ok}")
            # Write a timestamped backup copy as well
            try:
                if backup_output_folder:
                    os.makedirs(backup_output_folder, exist_ok=True)
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_name = f"cam2_bmp_{ts}.bmp"
                    backup_path = os.path.join(backup_output_folder, backup_name)
                    ok2 = cv2.imwrite(backup_path, frame)
                    print(f"Fallback backup wrote to {backup_path}: {ok2}")
            except Exception as _be:
                print(f"Fallback backup error: {_be}")
        else:
            print("Fallback skipped: original frame is None")
except Exception as _e:
    print(f"Fallback error in code 1: {_e}")







# ## working 3 oct 25
# # code 1

# from station2 import main
# import cv2
# import numpy as np
# import os

# # ==== Load Test Image ====
# #image_path = r"D:\Pravi\burr_images\new_glass\station4\dataset\5_9_25\VCXG.2-32C\image0000504.bmp"
# image_path = r"D:\PIM_25-09-25\Pravi_Flask\static\Cam1InputImages\cam2.bmp"
# #D:\PIM_15-09-25\Pravi_Flask\static\Cam1InputImages

# frame = cv2.imread(image_path)

# # ==== Parameters ====
# part = "SUPPORT PISTON"
# subpart = "28.10.019"
# thick_min = "0.01"          # Example minimum thickness in mm
# thick_max = "5.70"          # Example maximum thickness in mm
# pixel_to_micron = "44"      # Example conversion factor (microns per pixel)

# # Force save location for cam2 image as requested
# output_folder = r"D:\PIM_25-09-25\Pravi_Flask\static\OutputImages\cam2output"

# # New threshold parameters for software control
# min_thresh = "50"           # Threshold value (can be changed by software) 60
# max_thresh = "255"          # Maximum value for thresholding (can be changed by software)

# # ==== Call the main() Function ====
# result = main(
#     part=part,
#     subpart=subpart,
#     frame=frame,
#     thick_min=thick_min,
#     thick_max=thick_max,
#     pixel_to_micron=pixel_to_micron,
#     output_folder=output_folder,
#     min_thresh=min_thresh,
#     max_thresh=max_thresh
# )

# # ==== Output ====
# print("\n--- Final Returned Output ---")
# print(result)

# # ==== Fallback: ensure cam2_bmp.bmp exists ====
# try:
#     os.makedirs(output_folder, exist_ok=True)
#     cam2_path = os.path.join(output_folder, "cam2_bmp.bmp")
#     if not os.path.exists(cam2_path):
#         if frame is not None:
#             ok = cv2.imwrite(cam2_path, frame)
#             print(f"Fallback wrote original to {cam2_path}: {ok}")
#         else:
#             print("Fallback skipped: original frame is None")
# except Exception as _e:
#     print(f"Fallback error in code 1: {_e}")

















### working 30 sep 25

# from station2 import main
# import cv2
# import numpy as np

# # ==== Load Test Image ====
# #image_path = r"D:\Pravi\burr_images\new_glass\station4\dataset\5_9_25\VCXG.2-32C\image0000504.bmp"
# image_path = r"D:\Pravi\burr_images\new_glass\station2\dataset\29_9_25\VCXG.2-32C\image0000579.bmp" 
# #D:\PIM_15-09-25\Pravi_Flask\static\Cam1InputImages

# frame = cv2.imread(image_path)

# # ==== Parameters ====
# part = "O RING"
# subpart = "28.10.039"
# thick_min = "2.30"          # Example minimum thickness in mm
# thick_max = "2.70"          # Example maximum thickness in mm
# pixel_to_micron = "44"    # Example conversion factor (microns per pixel)
# output_folder = r"output\output_image"

# # New threshold parameters for software control
# min_thresh = "70"         # Threshold value (can be changed by software) 60
# max_thresh = "255"         # Maximum value for thresholding (can be changed by software)

# # ==== Call the main() Function ====
# result = main(
#     part=part,
#     subpart=subpart,
#     frame=frame,
#     thick_min=thick_min,
#     thick_max=thick_max,
#     pixel_to_micron=pixel_to_micron,
#     output_folder=output_folder,
#     min_thresh=min_thresh,
#     max_thresh=max_thresh
# )

# # ==== Output ====
# print("\n--- Final Returned Output ---")
# print(result)



