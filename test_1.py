
# code 1

# # working  28/9/25 11pm
#### updated 27/9/25
from station1 import main
import cv2
import numpy as np
import os
from datetime import datetime

# ==== Load Test Image ====
# image_path = r"D:\earth_tech\5mp\dataseet\21_sep_25\Image_20250921114258764.bmp"
# image_path = r"D:\Pravi\telecentric_exp\6_5mp_camara\dataset\7_9_25\o_ring\28.10.039\VCXG.2-65C.R\image0000379.bmp"
# image_path = r"D:\Pravi\telecentric_exp\6_5mp_camara\dataset\7_9_25\nrv_washer\28.10.727\VCXG.2-65C.R\image0000343.bmp"
# image_path = r"D:\Pravi\slip_gauge\5_mp\dataset\25_9_25\parts\VCXU.2-57C\support_piston\VCXU.2-57C\image0000079.bmp"
# image_path = r"D:\Pravi\slip_gauge\5_mp\dataset\25_9_25\parts\VCXU.2-57C\support_piston\22.10.013\VCXU.2-57C\image0000085.bmp"
# image_path = r"D:\Pravi\slip_gauge\5_mp\dataset\25_9_25\parts\VCXU.2-57C\support_piston\16.06.012\VCXU.2-57C\image0000091.bmp"
# image_path = r"D:\Pravi\slip_gauge\5_mp\dataset\25_9_25\parts\VCXU.2-57C\support_piston\28.10.019\VCXU.2-57C\image0000097.bmp"
# image_path = r"D:\Pravi\slip_gauge\5_mp\dataset\25_9_25\parts\VCXU.2-57C\PISTON\22.10.015\VCXU.2-57C\image0000105.bmp"
# image_path =   r"D:\Pravi\slip_gauge\5_mp\dataset\25_9_25\parts\VCXU.2-57C\PISTON\22.10.015\VCXU.2-57C\image0000105.bmp"
# image_path = r"D:\Pravi\burr_images\new_glass\station1\dataset\26_9_25\5mp\support_piston_ring\22.10.012\VCXU.2-57C\image0000112.bmp" SPP 28.10.020
# image_path = r"D:\Pravi\burr_images\new_glass\station1\dataset\26_9_25\5mp\support_piston_ring\22.10.012\VCXU.2-57C\image0000115.bmp"  # SPP 22.10.014
# image_path = r"D:\Pravi\burr_images\new_glass\station1\dataset\26_9_25\5mp\support_piston_ring\22.10.012\VCXU.2-57C\image0000118.bmp"  #  19.08.014
# image_path = r"D:\Pravi\burr_images\new_glass\station1\dataset\5mp\27_9_25\VCXU.2-57C\image0000435.bmp"
# image_path = r"D:\Pravi\slip_gauge\5_mp\dataset\25_9_25\parts\VCXU.2-57C\image0000071.bmp"
# image_path = r"D:\PIM_25-09-25\Pravi_Flask\static\Cam1InputImages\input_backup_cam1\2025-10-05\13\cam1_2025-10-05_13-23-25.png.bmp"
image_path = r"D:\Pravi\testing\dataset\8_10_25\VCXU.2-57C\image0000473.bmp"
frame = cv2.imread(image_path)

# ==== CHANGE THESE VALUES TO TEST DIFFERENT PARTS ====
# Notes:
# - "O RING": ID only (OD is NA)
# - "NRV SEAL": OD only (ID is NA)
# - "SEPEARTING PISTON": OD only (ID, Concentricity, Orifice NA)
part = "PISTON"           # Examples: "O RING", "NRV SEAL", "SEPEARTING PISTON", "PISTON", "SPACER"
subpart = "28.10.021"          # Subpart provided through test file

print(f"Testing {part} Part - {subpart}")
print("=" * 50)

# ==== Auto-Generate Output Folder Name ====
def create_output_folder_name(part_name, subpart_name, base_folder="output"):
    """Create a safe folder name from part and subpart names"""
    safe_part = part_name.replace(" ", "_").replace("/", "_").replace("\\", "_").replace(".", "_")
    safe_subpart = subpart_name.replace(".", "_").replace("/", "_").replace("\\", "_")
    folder_name = f"{safe_part}_{safe_subpart}_test"
    return os.path.join(base_folder, folder_name)

# Use requested static folder for cam1_bmp output
output_folder = r"D:\PIM_25-09-25\Pravi_Flask\static\OutputImages\cam1output"
# New: timestamped backup folder for extra save
backup_output_folder = r"D:\PIM_25-09-25\Pravi_Flask\static\OutputImages\cam1output\cam1_output_backup"
print(f"Output folder: {output_folder}")
print(f"Backup folder: {backup_output_folder}")

# ==== Parameters (adjust based on part type) ====
id_min = "8.05"
id_max = "8.15"
od_min = "22.80"
od_max = "23.10"
concentricity_max = "0.10"
orifice_min = "NA"
orifice_max = "NA"
threshold_id2 = "25"
threshold_id3 = "10"
threshold_od2 = "25"
threshold_od3 = "10"
pixel_to_micron = "19.91425565034393"
pixel_to_micron_id = "19.91425565034393"
pixel_to_micron_od = "19.91425565034393"

# ==== Call the main() Function ====
result = main(
    part=part,
    subpart=subpart,
    frame=frame,
    id_min=id_min,
    id_max=id_max,
    od_min=od_min,
    od_max=od_max,
    concentricity_max=concentricity_max,
    orifice_min=orifice_min,
    orifice_max=orifice_max,
    threshold_id2=threshold_id2,
    threshold_id3=threshold_id3,
    threshold_od2=threshold_od2,
    threshold_od3=threshold_od3,
    pixel_to_micron=pixel_to_micron,
    pixel_to_micron_id=pixel_to_micron_id,
    pixel_to_micron_od=pixel_to_micron_od,
    output_folder=output_folder,
    backup_output_folder=backup_output_folder  # new
)

# ==== Output ====
print("\n--- Final Returned Output ---")
print(result)
print("=" * 60)
print(f"{part} Test Completed!")
print(f"Results saved in: {output_folder}")
print(f"Backup copies in: {backup_output_folder}")

# ==== Fallback: ensure cam1_bmp.bmp exists and write a backup copy ====
try:
    os.makedirs(output_folder, exist_ok=True)
    cam1_path = os.path.join(output_folder, "cam1_bmp.bmp")
    if not os.path.exists(cam1_path):
        if frame is not None:
            ok = cv2.imwrite(cam1_path, frame)
            print(f"Fallback wrote original to {cam1_path}: {ok}")
            # Write a timestamped backup copy as well
            try:
                if backup_output_folder:
                    os.makedirs(backup_output_folder, exist_ok=True)
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_name = f"cam1_bmp_{ts}.bmp"
                    backup_path = os.path.join(backup_output_folder, backup_name)
                    ok2 = cv2.imwrite(backup_path, frame)
                    print(f"Fallback backup wrote to {backup_path}: {ok2}")
            except Exception as _be:
                print(f"Fallback backup error: {_be}")
        else:
            print("Fallback skipped: original frame is None")
except Exception as _e:
    print(f"Fallback error in code 1: {_e}")








### working 3  oct 2025
# # code 1

# # # working  28/9/25 11pm
# #### updated 27/9/25 
# from station1 import main
# import cv2
# import numpy as np
# import os

# # ==== Load Test Image ====
# # image_path = r"D:\earth_tech\5mp\dataseet\21_sep_25\Image_20250921114258764.bmp"
# # image_path = r"D:\Pravi\telecentric_exp\6_5mp_camara\dataset\7_9_25\o_ring\28.10.039\VCXG.2-65C.R\image0000379.bmp"
# # image_path = r"D:\Pravi\telecentric_exp\6_5mp_camara\dataset\7_9_25\nrv_washer\28.10.727\VCXG.2-65C.R\image0000343.bmp" 
# # image_path = r"D:\Pravi\slip_gauge\5_mp\dataset\25_9_25\parts\VCXU.2-57C\support_piston\VCXU.2-57C\image0000079.bmp"
# # image_path = r"D:\Pravi\slip_gauge\5_mp\dataset\25_9_25\parts\VCXU.2-57C\support_piston\22.10.013\VCXU.2-57C\image0000085.bmp"
# # image_path = r"D:\Pravi\slip_gauge\5_mp\dataset\25_9_25\parts\VCXU.2-57C\support_piston\16.06.012\VCXU.2-57C\image0000091.bmp"
# # image_path = r"D:\Pravi\slip_gauge\5_mp\dataset\25_9_25\parts\VCXU.2-57C\support_piston\28.10.019\VCXU.2-57C\image0000097.bmp"
# # image_path = r"D:\Pravi\slip_gauge\5_mp\dataset\25_9_25\parts\VCXU.2-57C\PISTON\22.10.015\VCXU.2-57C\image0000105.bmp"
# # image_path =   r"D:\Pravi\slip_gauge\5_mp\dataset\25_9_25\parts\VCXU.2-57C\PISTON\22.10.015\VCXU.2-57C\image0000105.bmp"
# # image_path = r"D:\Pravi\burr_images\new_glass\station1\dataset\26_9_25\5mp\support_piston_ring\22.10.012\VCXU.2-57C\image0000112.bmp" SPP 28.10.020
# # image_path = r"D:\Pravi\burr_images\new_glass\station1\dataset\26_9_25\5mp\support_piston_ring\22.10.012\VCXU.2-57C\image0000115.bmp"  # SPP 22.10.014
# # image_path = r"D:\Pravi\burr_images\new_glass\station1\dataset\26_9_25\5mp\support_piston_ring\22.10.012\VCXU.2-57C\image0000118.bmp"  #  19.08.014
# # image_path = r"D:\Pravi\burr_images\new_glass\station1\dataset\5mp\27_9_25\VCXU.2-57C\image0000435.bmp" 
# # image_path = r"D:\Pravi\slip_gauge\5_mp\dataset\25_9_25\parts\VCXU.2-57C\image0000071.bmp"
# image_path = r"D:\PIM_25-09-25\Pravi_Flask\static\Cam1InputImages\cam1.bmp"
# frame = cv2.imread(image_path)

# # ==== CHANGE THESE VALUES TO TEST DIFFERENT PARTS ====
# # Notes:
# # - "O RING": ID only (OD is NA)
# # - "NRV SEAL": OD only (ID is NA)
# # - "SEPEARTING PISTON": OD only (ID, Concentricity, Orifice NA)
# part = "PISTON"           # Examples: "O RING", "NRV SEAL", "SEPEARTING PISTON", "PISTON", "SPACER"
# subpart = "28.10.021"          # Subpart provided through test file

# print(f"Testing {part} Part - {subpart}")
# print("=" * 50)

# # ==== Auto-Generate Output Folder Name ====
# def create_output_folder_name(part_name, subpart_name, base_folder="output"):
#     """Create a safe folder name from part and subpart names"""
#     safe_part = part_name.replace(" ", "_").replace("/", "_").replace("\\", "_").replace(".", "_")
#     safe_subpart = subpart_name.replace(".", "_").replace("/", "_").replace("\\", "_")
#     folder_name = f"{safe_part}_{safe_subpart}_test"
#     return os.path.join(base_folder, folder_name)

# # Use requested static folder for cam1_bmp output
# output_folder = r"D:\PIM_25-09-25\Pravi_Flask\static\OutputImages\cam1output"
# print(f"Output folder: {output_folder}")

# # ==== Parameters (adjust based on part type) ====
# id_min = "8.02"
# id_max = "8.08"
# od_min = "23.85"
# od_max = "23.95"
# concentricity_max = "0.10"
# orifice_min = "0"
# orifice_max = "1.07"
# threshold_id2 = "25"
# threshold_id3 = "10"
# threshold_od2 = "25"
# threshold_od3 = "10"
# pixel_to_micron = "19.91425565034393"
# pixel_to_micron_id = "19.91425565034393"
# pixel_to_micron_od = "19.91425565034393"

# # ==== Call the main() Function ====
# result = main(
#     part=part,
#     subpart=subpart,
#     frame=frame,
#     id_min=id_min,
#     id_max=id_max,
#     od_min=od_min,
#     od_max=od_max,
#     concentricity_max=concentricity_max,
#     orifice_min=orifice_min,
#     orifice_max=orifice_max,
#     threshold_id2=threshold_id2,
#     threshold_id3=threshold_id3,
#     threshold_od2=threshold_od2,
#     threshold_od3=threshold_od3,
#     pixel_to_micron=pixel_to_micron,
#     pixel_to_micron_id=pixel_to_micron_id,
#     pixel_to_micron_od=pixel_to_micron_od,
#     output_folder=output_folder
# )

# # ==== Output ====
# print("\n--- Final Returned Output ---")
# print(result)
# print("=" * 60)
# print(f"{part} Test Completed!")
# print(f"Results saved in: {output_folder}")

# # ==== Fallback: ensure cam1_bmp.bmp exists ====
# try:
#     os.makedirs(output_folder, exist_ok=True)
#     cam1_path = os.path.join(output_folder, "cam1_bmp.bmp")
#     if not os.path.exists(cam1_path):
#         if frame is not None:
#             ok = cv2.imwrite(cam1_path, frame)
#             print(f"Fallback wrote original to {cam1_path}: {ok}")
#         else:
#             print("Fallback skipped: original frame is None")
# except Exception as _e:
#     print(f"Fallback error in code 1: {_e}")
























# # # working  30/9/25 4pm
# #### updated 27/9/25 
# from station1 import main
# import cv2
# import numpy as np
# import os

# # ==== Load Test Image ====
# # image_path = r"D:\earth_tech\5mp\dataseet\21_sep_25\Image_20250921114258764.bmp"
# # image_path = r"D:\Pravi\telecentric_exp\6_5mp_camara\dataset\7_9_25\o_ring\28.10.039\VCXG.2-65C.R\image0000379.bmp"
# # image_path = r"D:\Pravi\telecentric_exp\6_5mp_camara\dataset\7_9_25\nrv_washer\28.10.727\VCXG.2-65C.R\image0000343.bmp" 
# # image_path = r"D:\Pravi\slip_gauge\5_mp\dataset\25_9_25\parts\VCXU.2-57C\support_piston\VCXU.2-57C\image0000079.bmp"
# # image_path = r"D:\Pravi\slip_gauge\5_mp\dataset\25_9_25\parts\VCXU.2-57C\support_piston\22.10.013\VCXU.2-57C\image0000085.bmp"
# # image_path = r"D:\Pravi\slip_gauge\5_mp\dataset\25_9_25\parts\VCXU.2-57C\support_piston\16.06.012\VCXU.2-57C\image0000091.bmp"
# # image_path = r"D:\Pravi\slip_gauge\5_mp\dataset\25_9_25\parts\VCXU.2-57C\support_piston\28.10.019\VCXU.2-57C\image0000097.bmp"
# # image_path = r"D:\Pravi\slip_gauge\5_mp\dataset\25_9_25\parts\VCXU.2-57C\PISTON\22.10.015\VCXU.2-57C\image0000105.bmp"
# # image_path =   r"D:\Pravi\slip_gauge\5_mp\dataset\25_9_25\parts\VCXU.2-57C\PISTON\22.10.015\VCXU.2-57C\image0000105.bmp"
# # image_path = r"D:\Pravi\burr_images\new_glass\station1\dataset\26_9_25\5mp\support_piston_ring\22.10.012\VCXU.2-57C\image0000112.bmp" SPP 28.10.020
# # image_path = r"D:\Pravi\burr_images\new_glass\station1\dataset\26_9_25\5mp\support_piston_ring\22.10.012\VCXU.2-57C\image0000115.bmp"  # SPP 22.10.014
# # image_path = r"D:\Pravi\burr_images\new_glass\station1\dataset\26_9_25\5mp\support_piston_ring\22.10.012\VCXU.2-57C\image0000118.bmp"  #  19.08.014
# # image_path = r"D:\Pravi\burr_images\new_glass\station1\dataset\5mp\27_9_25\VCXU.2-57C\image0000435.bmp" 
# # image_path = r"D:\Pravi\slip_gauge\5_mp\dataset\25_9_25\parts\VCXU.2-57C\image0000071.bmp"
# image_path = r"D:\Pravi\burr_images\new_glass\station1\dataset\5mp\28_9_25\VCXU.2-57C\1.bmp"
# frame = cv2.imread(image_path)

# # ==== CHANGE THESE VALUES TO TEST DIFFERENT PARTS ====
# # Notes:
# # - "O RING": ID only (OD is NA)
# # - "NRV SEAL": OD only (ID is NA)
# # - "SEPEARTING PISTON": OD only (ID, Concentricity, Orifice NA)
# part = "PISTON"           # Examples: "O RING", "NRV SEAL", "SEPEARTING PISTON", "PISTON", "SPACER"
# subpart = "28.10.021"          # Subpart provided through test file

# print(f"Testing {part} Part - {subpart}")
# print("=" * 50)

# # ==== Auto-Generate Output Folder Name ====
# def create_output_folder_name(part_name, subpart_name, base_folder="output"):
#     """Create a safe folder name from part and subpart names"""
#     safe_part = part_name.replace(" ", "_").replace("/", "_").replace("\\", "_").replace(".", "_")
#     safe_subpart = subpart_name.replace(".", "_").replace("/", "_").replace("\\", "_")
#     folder_name = f"{safe_part}_{safe_subpart}_test"
#     return os.path.join(base_folder, folder_name)

# output_folder = create_output_folder_name(part, subpart)
# print(f"Output folder: {output_folder}")

# # ==== Parameters (adjust based on part type) ====
# id_min = "8.02"
# id_max = "8.08"
# od_min = "23.85"
# od_max = "23.95"
# concentricity_max = "0.10"
# orifice_min = "0"
# orifice_max = "1.07"
# threshold_id2 = "25"
# threshold_id3 = "10"
# threshold_od2 = "25"
# threshold_od3 = "10"
# pixel_to_micron = "19.91425565034393"
# pixel_to_micron_id = "19.91425565034393"
# pixel_to_micron_od = "19.91425565034393"

# # ==== Call the main() Function ====
# result = main(
#     part=part,
#     subpart=subpart,
#     frame=frame,
#     id_min=id_min,
#     id_max=id_max,
#     od_min=od_min,
#     od_max=od_max,
#     concentricity_max=concentricity_max,
#     orifice_min=orifice_min,
#     orifice_max=orifice_max,
#     threshold_id2=threshold_id2,
#     threshold_id3=threshold_id3,
#     threshold_od2=threshold_od2,
#     threshold_od3=threshold_od3,
#     pixel_to_micron=pixel_to_micron,
#     pixel_to_micron_id=pixel_to_micron_id,
#     pixel_to_micron_od=pixel_to_micron_od,
#     output_folder=output_folder
# )

# # ==== Output ====
# print("\n--- Final Returned Output ---")
# print(result)
# print("=" * 60)
# print(f"{part} Test Completed!")
# print(f"Results saved in: {output_folder}")









