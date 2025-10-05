
# code 1
# Changes:
# - Added backup_output_folder to save timestamped backups alongside legacy cam4_bmp.bmp.
# - Passed backup_output_folder to station_4.main.
# - Fallback now also writes a timestamped backup copy if cam4_bmp.bmp had to be created.
# - No behavioral change needed here for the processing-contour gating; gating is enforced in station_4_defect.

from station_4 import main
import cv2
import os
from datetime import datetime

# Load test image
image_path = r"D:\PIM_25-09-25\Pravi_Flask\static\Cam1InputImages\input_backup_cam4\2025-10-04\17\cam4_2025-10-04_17-07-31.png.bmp"
frame = cv2.imread(image_path)

# ==== Configurable Parameters ====
part = "SUPPORT PISTON"
subpart = "28.10.019"

# ID/OD Contour Area Parameters
min_id_area = "10000"
max_id_area = "22200"
min_od_area = "95000"
max_od_area = "150000"

# Shape filters ("NA" to disable)
min_circularity = "0.15"
max_circularity = "1.15"
min_aspect_ratio = "0.10"
max_aspect_ratio = "1.10"

# Burr Detection Parameters (ID)
ID2_OFFSET_ID = "20"
HIGHLIGHT_SIZE_ID = "20"
ID_BURR_MIN_AREA = "60"
ID_BURR_MAX_AREA = "400"
ID_BURR_MIN_PERIMETER = "30"
ID_BURR_MAX_PERIMETER = "300"

# Burr Detection Parameters (OD)
ID2_OFFSET_OD = "20"
HIGHLIGHT_SIZE_OD = "20"
OD_BURR_MIN_AREA = "60"
OD_BURR_MAX_AREA = "400"
OD_BURR_MIN_PERIMETER = "30"
OD_BURR_MAX_PERIMETER = "300"

# Target folders
output_folder = r"D:\PIM_25-09-25\Pravi_Flask\static\OutputImages\cam4output"
backup_output_folder = r"D:\PIM_25-09-25\Pravi_Flask\static\OutputImages\cam4output\cam4_output_backup"  # NEW (configurable)

# Call main
result = main(
    part, subpart, frame,
    # ID
    ID2_OFFSET_ID, HIGHLIGHT_SIZE_ID,
    ID_BURR_MIN_AREA, ID_BURR_MAX_AREA, ID_BURR_MIN_PERIMETER, ID_BURR_MAX_PERIMETER,
    # OD
    ID2_OFFSET_OD, HIGHLIGHT_SIZE_OD,
    OD_BURR_MIN_AREA, OD_BURR_MAX_AREA, OD_BURR_MIN_PERIMETER, OD_BURR_MAX_PERIMETER,
    # Contour selection
    min_id_area, max_id_area, min_od_area, max_od_area,
    # Shape filters
    min_circularity, max_circularity, min_aspect_ratio, max_aspect_ratio,
    output_folder,
    backup_output_folder=backup_output_folder  # NEW
)

print("--- Final Result ---")
print(result)

# Fallback: ensure cam4_bmp.bmp exists and also write a timestamped backup
try:
    os.makedirs(output_folder, exist_ok=True)
    cam4_path = os.path.join(output_folder, "cam4_bmp.bmp")
    if not os.path.exists(cam4_path):
        if frame is not None:
            ok = cv2.imwrite(cam4_path, frame)
            print(f"Fallback wrote original to {cam4_path}: {ok}")
            # Write backup too
            try:
                if backup_output_folder:
                    os.makedirs(backup_output_folder, exist_ok=True)
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_path = os.path.join(backup_output_folder, f"cam4_bmp_{ts}.bmp")
                    ok2 = cv2.imwrite(backup_path, frame)
                    print(f"Fallback backup wrote to {backup_path}: {ok2}")
            except Exception as _be:
                print(f"Fallback backup error: {_be}")
        else:
            print("Fallback skipped: original frame is None")
except Exception as _e:
    print(f"Fallback error in test_4.py: {_e}")




















# # code 1
# # Changes:
# # - Added backup_output_folder to save timestamped backups alongside legacy cam4_bmp.bmp.
# # - Passed backup_output_folder to station_4.main.
# # - Fallback now also writes a timestamped backup copy if cam4_bmp.bmp had to be created.

# from station_4 import main
# import cv2
# import os
# from datetime import datetime

# # Load test image
# image_path = r"D:\PIM_25-09-25\Pravi_Flask\static\Cam1InputImages\input_backup_cam4\2025-10-04\16\cam4_2025-10-04_16-26-25.png.bmp"
# frame = cv2.imread(image_path)

# # ==== Configurable Parameters ====
# part = "SUPPORT PISTON"
# subpart = "28.10.019"

# # ID/OD Contour Area Parameters
# min_id_area = "10000"
# max_id_area = "22200"
# min_od_area = "95000"
# max_od_area = "130000"

# # Shape filters ("NA" to disable)
# min_circularity = "0.85"
# max_circularity = "1.15"
# min_aspect_ratio = "0.90"
# max_aspect_ratio = "1.10"

# # Burr Detection Parameters (ID)
# ID2_OFFSET_ID = "20"
# HIGHLIGHT_SIZE_ID = "20"
# ID_BURR_MIN_AREA = "60"
# ID_BURR_MAX_AREA = "400"
# ID_BURR_MIN_PERIMETER = "30"
# ID_BURR_MAX_PERIMETER = "300"

# # Burr Detection Parameters (OD)
# ID2_OFFSET_OD = "20"
# HIGHLIGHT_SIZE_OD = "20"
# OD_BURR_MIN_AREA = "60"
# OD_BURR_MAX_AREA = "400"
# OD_BURR_MIN_PERIMETER = "30"
# OD_BURR_MAX_PERIMETER = "300"

# # Target folders
# output_folder = r"D:\PIM_25-09-25\Pravi_Flask\static\OutputImages\cam4output"
# backup_output_folder = r"D:\PIM_25-09-25\Pravi_Flask\static\OutputImages\cam4output\cam4_output_backup"  # NEW (configurable)

# # Call main
# result = main(
#     part, subpart, frame,
#     # ID
#     ID2_OFFSET_ID, HIGHLIGHT_SIZE_ID,
#     ID_BURR_MIN_AREA, ID_BURR_MAX_AREA, ID_BURR_MIN_PERIMETER, ID_BURR_MAX_PERIMETER,
#     # OD
#     ID2_OFFSET_OD, HIGHLIGHT_SIZE_OD,
#     OD_BURR_MIN_AREA, OD_BURR_MAX_AREA, OD_BURR_MIN_PERIMETER, OD_BURR_MAX_PERIMETER,
#     # Contour selection
#     min_id_area, max_id_area, min_od_area, max_od_area,
#     # Shape filters
#     min_circularity, max_circularity, min_aspect_ratio, max_aspect_ratio,
#     output_folder,
#     backup_output_folder=backup_output_folder  # NEW
# )

# print("--- Final Result ---")
# print(result)

# # Fallback: ensure cam4_bmp.bmp exists and also write a timestamped backup
# try:
#     os.makedirs(output_folder, exist_ok=True)
#     cam4_path = os.path.join(output_folder, "cam4_bmp.bmp")
#     if not os.path.exists(cam4_path):
#         if frame is not None:
#             ok = cv2.imwrite(cam4_path, frame)
#             print(f"Fallback wrote original to {cam4_path}: {ok}")
#             # Write backup too
#             try:
#                 if backup_output_folder:
#                     os.makedirs(backup_output_folder, exist_ok=True)
#                     ts = datetime.now().strftime("%Y%m%d_%H%M%S")
#                     backup_path = os.path.join(backup_output_folder, f"cam4_bmp_{ts}.bmp")
#                     ok2 = cv2.imwrite(backup_path, frame)
#                     print(f"Fallback backup wrote to {backup_path}: {ok2}")
#             except Exception as _be:
#                 print(f"Fallback backup error: {_be}")
#         else:
#             print("Fallback skipped: original frame is None")
# except Exception as _e:
#     print(f"Fallback error in test_4.py: {_e}")





















### working 3 oct 25
 # updated 03_10_2025
# # Test harness for station_4
# from station_4 import main
# import cv2
# import os

# # Load test image
# image_path = r"D:\PIM_15-09-25\Pravi_Flask\static\Cam1InputImages\cam4.bmp"
# frame = cv2.imread(image_path)

# # ==== Configurable Parameters ====
# part = "SUPPORT PISTON"
# subpart = "28.10.019"

# # ID/OD Contour Area Parameters
# min_id_area = "10000"
# max_id_area = "22200"
# min_od_area = "95000"
# max_od_area = "130000"

# # Shape filters ("NA" to disable)
# min_circularity = "0.85"
# max_circularity = "1.15"
# min_aspect_ratio = "0.90"
# max_aspect_ratio = "1.10"

# # Burr Detection Parameters (ID)
# ID2_OFFSET_ID = "20"
# HIGHLIGHT_SIZE_ID = "20"
# ID_BURR_MIN_AREA = "60"
# ID_BURR_MAX_AREA = "400"
# ID_BURR_MIN_PERIMETER = "30"
# ID_BURR_MAX_PERIMETER = "300"

# # Burr Detection Parameters (OD)
# ID2_OFFSET_OD = "20"
# HIGHLIGHT_SIZE_OD = "20"
# OD_BURR_MIN_AREA = "60"
# OD_BURR_MAX_AREA = "400"
# OD_BURR_MIN_PERIMETER = "30"
# OD_BURR_MAX_PERIMETER = "300"

# # Target folder
# output_folder = r"D:\PIM_25-09-25\Pravi_Flask\static\OutputImages\cam4output"

# # Call main
# result = main(
#     part, subpart, frame,
#     # ID
#     ID2_OFFSET_ID, HIGHLIGHT_SIZE_ID,
#     ID_BURR_MIN_AREA, ID_BURR_MAX_AREA, ID_BURR_MIN_PERIMETER, ID_BURR_MAX_PERIMETER,
#     # OD
#     ID2_OFFSET_OD, HIGHLIGHT_SIZE_OD,
#     OD_BURR_MIN_AREA, OD_BURR_MAX_AREA, OD_BURR_MIN_PERIMETER, OD_BURR_MAX_PERIMETER,
#     # Contour selection
#     min_id_area, max_id_area, min_od_area, max_od_area,
#     # Shape filters
#     min_circularity, max_circularity, min_aspect_ratio, max_aspect_ratio,
#     output_folder
# )

# print("--- Final Result ---")
# print(result)

# # Fallback: ensure cam4_bmp.bmp exists
# try:
#     os.makedirs(output_folder, exist_ok=True)
#     cam4_path = os.path.join(output_folder, "cam4_bmp.bmp")
#     if not os.path.exists(cam4_path):
#         if frame is not None:
#             ok = cv2.imwrite(cam4_path, frame)
#             print(f"Fallback wrote original to {cam4_path}: {ok}")
#         else:
#             print("Fallback skipped: original frame is None")
# except Exception as _e:
#     print(f"Fallback error in test_4.py: {_e}")






















    


###working 3 oct 25
# #
#  # code 1

# # updated 20_9_2025 (adds circularity/aspect ratio controls)
# # Test file example usage
# from station_4 import main
# import cv2
# import os

# # Load test image
# image_path = r"D:\PIM_15-09-25\Pravi_Flask\static\Cam1InputImages\cam4.bmp"
# frame = cv2.imread(image_path)

# # ==== Configurable Parameters ====
# part = "SUPPORT PISTON"
# subpart = "28.10.019"

# # ID/OD Contour Area Parameters (Easy to modify)
# min_id_area = "10000"      # Minimum area for ID contour detection
# max_id_area = "22200"      # Maximum area for ID contour detection
# min_od_area = "95000"      # Minimum area for OD contour detection
# max_od_area = "130000"     # Maximum area for OD contour detection

# # NEW: Shape filters for circular selection (use "NA" to disable)
# min_circularity = "0.85"   # 4*pi*A/P^2 lower bound (close to 1 for circles)
# max_circularity = "1.15"   # 4*pi*A/P^2 upper bound
# min_aspect_ratio = "0.90"  # w/h lower bound (≈1 for circles)
# max_aspect_ratio = "1.10"  # w/h upper bound

# # Burr Detection Parameters (ID)
# ID2_OFFSET_ID = "20"
# HIGHLIGHT_SIZE_ID = "20"
# ID_BURR_MIN_AREA = "60"
# ID_BURR_MAX_AREA = "400"
# ID_BURR_MIN_PERIMETER = "30"
# ID_BURR_MAX_PERIMETER = "300"

# # Burr Detection Parameters (OD)
# ID2_OFFSET_OD = "20"
# HIGHLIGHT_SIZE_OD = "20"
# OD_BURR_MIN_AREA = "60"
# OD_BURR_MAX_AREA = "400"
# OD_BURR_MIN_PERIMETER = "30"
# OD_BURR_MAX_PERIMETER = "300"

# # Force target folder for cam4 image
# output_folder = r"D:\PIM_25-09-25\Pravi_Flask\static\OutputImages\cam4output"

# # Call main function with all parameters
# result = main(
#     part, subpart, frame,
#     # ID parameters
#     ID2_OFFSET_ID, HIGHLIGHT_SIZE_ID,
#     ID_BURR_MIN_AREA, ID_BURR_MAX_AREA,
#     ID_BURR_MIN_PERIMETER, ID_BURR_MAX_PERIMETER,
#     # OD parameters
#     ID2_OFFSET_OD, HIGHLIGHT_SIZE_OD,
#     OD_BURR_MIN_AREA, OD_BURR_MAX_AREA,
#     OD_BURR_MIN_PERIMETER, OD_BURR_MAX_PERIMETER,
#     # Contour selection
#     min_id_area, max_id_area, min_od_area, max_od_area,
#     # Shape filters
#     min_circularity, max_circularity, min_aspect_ratio, max_aspect_ratio,
#     output_folder
# )

# print("--- Final Result ---")
# print(result)

# # Fallback: ensure cam4_bmp.bmp exists
# try:
#     os.makedirs(output_folder, exist_ok=True)
#     cam4_path = os.path.join(output_folder, "cam4_bmp.bmp")
#     if not os.path.exists(cam4_path):
#         if frame is not None:
#             ok = cv2.imwrite(cam4_path, frame)
#             print(f"Fallback wrote original to {cam4_path}: {ok}")
#         else:
#             print("Fallback skipped: original frame is None")
# except Exception as _e:
#     print(f"Fallback error in code 1: {_e}")












### working
# # code 1

# # updated 20_9_2025 (adds circularity/aspect ratio controls)
# # Test file example usage
# from station_4 import main
# import cv2
# import os

# # Load test image
# image_path = r"D:\PIM_15-09-25\Pravi_Flask\static\Cam1InputImages\cam4.bmp"
# frame = cv2.imread(image_path)

# # ==== Configurable Parameters ====
# part = "SUPPORT PISTON"
# subpart = "28.10.019"

# # ID/OD Contour Area Parameters (Easy to modify)
# min_id_area = "14000"      # Minimum area for ID contour detection
# max_id_area = "16200"      # Maximum area for ID contour detection
# min_od_area = "95000"      # Minimum area for OD contour detection
# max_od_area = "130000"     # Maximum area for OD contour detection

# # NEW: Shape filters for circular selection (use "NA" to disable)
# min_circularity = "0.85"   # 4*pi*A/P^2 lower bound (close to 1 for circles)
# max_circularity = "1.15"   # 4*pi*A/P^2 upper bound
# min_aspect_ratio = "0.90"  # w/h lower bound (≈1 for circles)
# max_aspect_ratio = "1.10"  # w/h upper bound

# # Burr Detection Parameters (ID)
# ID2_OFFSET_ID = "20"
# HIGHLIGHT_SIZE_ID = "20"
# ID_BURR_MIN_AREA = "60"
# ID_BURR_MAX_AREA = "400"
# ID_BURR_MIN_PERIMETER = "30"
# ID_BURR_MAX_PERIMETER = "300"

# # Burr Detection Parameters (OD)
# ID2_OFFSET_OD = "20"
# HIGHLIGHT_SIZE_OD = "20"
# OD_BURR_MIN_AREA = "60"
# OD_BURR_MAX_AREA = "400"
# OD_BURR_MIN_PERIMETER = "30"
# OD_BURR_MAX_PERIMETER = "300"

# # Force target folder for cam4 image
# output_folder = r"D:\PIM_25-09-25\Pravi_Flask\static\OutputImages\cam4output"

# # Call main function with all parameters
# result = main(
#     part, subpart, frame,
#     # ID parameters
#     ID2_OFFSET_ID, HIGHLIGHT_SIZE_ID,
#     ID_BURR_MIN_AREA, ID_BURR_MAX_AREA,
#     ID_BURR_MIN_PERIMETER, ID_BURR_MAX_PERIMETER,
#     # OD parameters
#     ID2_OFFSET_OD, HIGHLIGHT_SIZE_OD,
#     OD_BURR_MIN_AREA, OD_BURR_MAX_AREA,
#     OD_BURR_MIN_PERIMETER, OD_BURR_MAX_PERIMETER,
#     # Contour selection
#     min_id_area, max_id_area, min_od_area, max_od_area,
#     # Shape filters
#     min_circularity, max_circularity, min_aspect_ratio, max_aspect_ratio,
#     output_folder
# )

# print("--- Final Result ---")
# print(result)

# # Fallback: ensure cam4_bmp.bmp exists
# try:
#     os.makedirs(output_folder, exist_ok=True)
#     cam4_path = os.path.join(output_folder, "cam4_bmp.bmp")
#     if not os.path.exists(cam4_path):
#         if frame is not None:
#             ok = cv2.imwrite(cam4_path, frame)
#             print(f"Fallback wrote original to {cam4_path}: {ok}")
#         else:
#             print("Fallback skipped: original frame is None")
# except Exception as _e:
#     print(f"Fallback error in code 1: {_e}")
















