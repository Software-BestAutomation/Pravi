  # code 1
# Changes:
# - Added backup_output_folder variable for timestamped backup images.
# - Passes backup_output_folder to main().
# - Writes a timestamped backup copy in fallback if cam3_bmp.bmp doesn't exist.
# - Legacy save path of cam3_bmp.bmp unchanged.

from station_3 import main
import cv2
import os
from datetime import datetime

image_path = r"D:\PIM_25-09-25\Pravi_Flask\static\Cam1InputImages\cam3.bmp"
frame = cv2.imread(image_path)
print(f"DEBUG: Loaded image from: {image_path}")

part = "SUPPORT PISTON"
subpart = "28.10.019"

min_id_area = "13000"
max_id_area = "23000"
min_od_area = "110000"
max_od_area = "160000"

min_circularity = "0.50"
max_circularity = "1.15"
min_aspect_ratio = "0.30"
max_aspect_ratio = "1.10"

ID2_OFFSET_ID = "10"
HIGHLIGHT_SIZE_ID = "40"
ID_BURR_MIN_AREA = "60"
ID_BURR_MAX_AREA = "400"
ID_BURR_MIN_PERIMETER = "30"
ID_BURR_MAX_PERIMETER = "300"

ID2_OFFSET_OD = "10"
HIGHLIGHT_SIZE_OD = "40"
OD_BURR_MIN_AREA = "60"
OD_BURR_MAX_AREA = "400"
OD_BURR_MIN_PERIMETER = "30"
OD_BURR_MAX_PERIMETER = "300"

output_folder = r"D:\PIM_25-09-25\Pravi_Flask\static\OutputImages\cam3output"
backup_output_folder = r"D:\PIM_25-09-25\Pravi_Flask\static\OutputImages\cam3output\cam3_output_backup"  # Configurable backup folder path

print("DEBUG: Parameters set for both ID and OD")

result = main(
    part, subpart, frame,
    ID2_OFFSET_ID,
    HIGHLIGHT_SIZE_ID,
    ID_BURR_MIN_AREA,
    ID_BURR_MAX_AREA,
    ID_BURR_MIN_PERIMETER,
    ID_BURR_MAX_PERIMETER,
    ID2_OFFSET_OD,
    HIGHLIGHT_SIZE_OD,
    OD_BURR_MIN_AREA,
    OD_BURR_MAX_AREA,
    OD_BURR_MIN_PERIMETER,
    OD_BURR_MAX_PERIMETER,
    min_id_area,
    max_id_area,
    min_od_area,
    max_od_area,
    min_circularity,
    max_circularity,
    min_aspect_ratio,
    max_aspect_ratio,
    output_folder,
    backup_output_folder  # New param for backup folder path
)

print("\n--- Final Returned Output ---")
print(result)

# Fallback: ensure cam3_bmp.bmp exists and write a timestamped backup copy
try:
    os.makedirs(output_folder, exist_ok=True)
    cam3_path = os.path.join(output_folder, "cam3_bmp.bmp")
    if not os.path.exists(cam3_path):
        if frame is not None:
            ok = cv2.imwrite(cam3_path, frame)
            print(f"Fallback wrote original to {cam3_path}: {ok}")
            # Also write timestamped backup
            if backup_output_folder:
                try:
                    os.makedirs(backup_output_folder, exist_ok=True)
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_path = os.path.join(backup_output_folder, f"cam3_bmp_{ts}.bmp")
                    ok2 = cv2.imwrite(backup_path, frame)
                    print(f"Fallback backup wrote to {backup_path}: {ok2}")
                except Exception as be:
                    print(f"Fallback backup error: {be}")
        else:
            print("Fallback skipped: original frame is None")
except Exception as e:
    print(f"Fallback error in code 1: {e}")







# ## working 3 oct 25 
# # code 1

# # test_station_3.py   combine ID & OD
# # updated on 22_9_2025 (now also saves cam3_combined.bmp with both ID & OD)
# from station_3 import main
# import cv2
# import os

# # Load test image
# image_path = r"D:\PIM_25-09-25\Pravi_Flask\static\Cam1InputImages\cam3.bmp"
# frame = cv2.imread(image_path)
# print(f"DEBUG: Loaded image from: {image_path}")

# # Identification
# part = "SUPPORT PISTON"
# subpart = "28.10.019"

# # Contour area windows
# min_id_area = "13000"
# max_id_area = "23000"
# min_od_area = "110000"
# max_od_area = "160000"

# # Shape filters (use "NA" to disable)
# min_circularity = "0.50"
# max_circularity = "1.15"
# min_aspect_ratio = "0.30"
# max_aspect_ratio = "1.10"

# # Burr Detection Parameters (ID)
# ID2_OFFSET_ID = "10"
# HIGHLIGHT_SIZE_ID = "40"
# ID_BURR_MIN_AREA = "60"
# ID_BURR_MAX_AREA = "400"
# ID_BURR_MIN_PERIMETER = "30"
# ID_BURR_MAX_PERIMETER = "300"

# # Burr Detection Parameters (OD)
# ID2_OFFSET_OD = "10"
# HIGHLIGHT_SIZE_OD = "40"
# OD_BURR_MIN_AREA = "60"
# OD_BURR_MAX_AREA = "400"
# OD_BURR_MIN_PERIMETER = "30"
# OD_BURR_MAX_PERIMETER = "300"

# # Output folder
# # Force save location to requested cam3 output folder
# output_folder = r"D:\PIM_25-09-25\Pravi_Flask\static\OutputImages\cam3output"

# print("DEBUG: Parameters set for both ID and OD")

# result = main(
#     part, subpart, frame,
#     # ID parameters
#     ID2_OFFSET_ID, HIGHLIGHT_SIZE_ID,
#     ID_BURR_MIN_AREA, ID_BURR_MAX_AREA, ID_BURR_MIN_PERIMETER, ID_BURR_MAX_PERIMETER,
#     # OD parameters
#     ID2_OFFSET_OD, HIGHLIGHT_SIZE_OD,
#     OD_BURR_MIN_AREA, OD_BURR_MAX_AREA, OD_BURR_MIN_PERIMETER, OD_BURR_MAX_PERIMETER,
#     # Contour selection
#     min_id_area, max_id_area, min_od_area, max_od_area,
#     min_circularity, max_circularity, min_aspect_ratio, max_aspect_ratio,
#     output_folder
# )

# print("\n--- Final Returned Output ---")
# print(result)

# # Fallback: ensure cam3_bmp.bmp exists
# try:
#     os.makedirs(output_folder, exist_ok=True)
#     cam3_path = os.path.join(output_folder, "cam3_bmp.bmp")
#     if not os.path.exists(cam3_path):
#         if frame is not None:
#             ok = cv2.imwrite(cam3_path, frame)
#             print(f"Fallback wrote original to {cam3_path}: {ok}")
#         else:
#             print("Fallback skipped: original frame is None")
# except Exception as _e:
#     print(f"Fallback error in code 1: {_e}")






















# #### working 30sep25
# # test_station_3.py   combine ID & OD
# # updated on 22_9_2025 (now also saves cam3_combined.bmp with both ID & OD)
# from station_3 import main
# import cv2

# # Load test image
# image_path = r"D:\PIM_15-09-25\Pravi_Flask\static\Cam1InputImages\cam3.bmp"
# frame = cv2.imread(image_path)
# print(f"DEBUG: Loaded image from: {image_path}")

# # Identification
# part = "SUPPORT PISTON"
# subpart = "28.10.019"

# # Contour area windows
# min_id_area = "13000"
# max_id_area = "23000"
# min_od_area = "110000"
# max_od_area = "160000"

# # Shape filters (use "NA" to disable)
# min_circularity = "0.50"
# max_circularity = "1.15"
# min_aspect_ratio = "0.30"
# max_aspect_ratio = "1.10"

# # Burr Detection Parameters (ID)
# ID2_OFFSET_ID = "10"
# HIGHLIGHT_SIZE_ID = "40"
# ID_BURR_MIN_AREA = "60"
# ID_BURR_MAX_AREA = "400"
# ID_BURR_MIN_PERIMETER = "30"
# ID_BURR_MAX_PERIMETER = "300"

# # Burr Detection Parameters (OD)
# ID2_OFFSET_OD = "10"
# HIGHLIGHT_SIZE_OD = "40"
# OD_BURR_MIN_AREA = "60"
# OD_BURR_MAX_AREA = "400"
# OD_BURR_MIN_PERIMETER = "30"
# OD_BURR_MAX_PERIMETER = "300"

# # Output folder
# output_folder = r"output\output_image"

# print("DEBUG: Parameters set for both ID and OD")

# result = main(
#     part, subpart, frame,
#     # ID parameters
#     ID2_OFFSET_ID, HIGHLIGHT_SIZE_ID,
#     ID_BURR_MIN_AREA, ID_BURR_MAX_AREA, ID_BURR_MIN_PERIMETER, ID_BURR_MAX_PERIMETER,
#     # OD parameters
#     ID2_OFFSET_OD, HIGHLIGHT_SIZE_OD,
#     OD_BURR_MIN_AREA, OD_BURR_MAX_AREA, OD_BURR_MIN_PERIMETER, OD_BURR_MAX_PERIMETER,
#     # Contour selection
#     min_id_area, max_id_area, min_od_area, max_od_area,
#     min_circularity, max_circularity, min_aspect_ratio, max_aspect_ratio,
#     output_folder
# )

# print("\n--- Final Returned Output ---")
# print(result)





