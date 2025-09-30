


# # working  28/9/25 11pm
#### updated 27/9/25 
from station1 import main
import cv2
import numpy as np
import os

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
image_path = r"D:\Pravi\burr_images\new_glass\station1\dataset\5mp\28_9_25\VCXU.2-57C\image0000456.bmp"
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

output_folder = create_output_folder_name(part, subpart)
print(f"Output folder: {output_folder}")

# ==== Parameters (adjust based on part type) ====
id_min = "8.02"
id_max = "8.08"
od_min = "23.85"
od_max = "23.95"
concentricity_max = "0.10"
orifice_min = "0"
orifice_max = "1.07"
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
    output_folder=output_folder
)

# ==== Output ====
print("\n--- Final Returned Output ---")
print(result)
print("=" * 60)
print(f"{part} Test Completed!")
print(f"Results saved in: {output_folder}")



















# #### updated 20\9\2025  11:PM   upto 27_sep_25   
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
# image_path = r"D:\Pravi\burr_images\new_glass\station1\dataset\5mp\27_9_25\VCXU.2-57C\image0000122.bmp" 
# frame = cv2.imread(image_path)

# # ==== CHANGE THESE VALUES TO TEST DIFFERENT PARTS ====
# part = "PISTON RING"           # Change this: "SPACER", "PISTON", "O RING", etc.   SEPEARTING PISTON
# subpart = "16.06.013"     # Change this to any subpart number

# print(f"Testing {part} Part - {subpart}")
# print("=" * 50)

# # ==== Auto-Generate Output Folder Name ====
# def create_output_folder_name(part_name, subpart_name, base_folder="output"):
#     """Create a safe folder name from part and subpart names"""
#     # Clean part name (replace spaces and special chars with underscores)
#     safe_part = part_name.replace(" ", "_").replace("/", "_").replace("\\", "_").replace(".", "_")
#     safe_subpart = subpart_name.replace(".", "_").replace("/", "_").replace("\\", "_")
    
#     # Create folder path
#     folder_name = f"{safe_part}_{safe_subpart}_test"
#     return os.path.join(base_folder, folder_name)

# output_folder = create_output_folder_name(part, subpart)
# print(f"Output folder: {output_folder}")

# # ==== Parameters (adjust based on part type) ====
# id_min = "9.80"
# id_max = "9.90"
# od_min = "13.15"
# od_max = "13.25"
# concentricity_max = "0.10"
# orifice_min = "0"
# orifice_max = "1.07"
# threshold_id2 = "25"
# threshold_id3 = "10"
# threshold_od2 = "25"
# threshold_od3 = "10"
# pixel_to_micron = "19.91425565034393"    #17.1236021752451                6.5 19.85677083333334
# pixel_to_micron_id = "19.91425565034393"
# pixel_to_micron_od = "19.91425565034393"     #25.1236021752451     17.41536458333334

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















# # Imports

# from station1 import main
# import cv2
# import numpy as np

# # ==== Load Test Image ====
# image_path = r"D:\PIM_08-07-2025\Pravi_Flask\static\Cam1InputImages\Cam1.bmp"

# frame = cv2.imread(image_path)

# print("Testing SPACER Part - 28.14.152")
# print("=" * 50)

# # ==== Parameters for SPACER ====
# part = "SPACER"
# subpart = "28.14.152"
# id_min = "14.05"          # Minimum ID in mm
# id_max = "14.12"          # Maximum ID in mm  
# od_min = "24.10"          # Minimum OD in mm
# od_max = "24.20"          # Maximum OD in mm
# concentricity_max = "0.09"  # Maximum concentricity deviation in mm
# orifice_min = "NA"          # Not applicable for SPACER
# orifice_max = "NA"          # Not applicable for SPACER
# threshold_id2 = "25"        # ID flash detection threshold 2
# threshold_id3 = "15"        # ID flash detection threshold 3
# threshold_od2 = "25"        # OD flash detection threshold 2
# threshold_od3 = "10"        # OD flash detection threshold 3
# pixel_to_micron = "17"   # Conversion factor (microns per pixel)
# pixel_to_micron_id = "17"  # ID-specific conversion
# pixel_to_micron_od = "17"  # OD-specific conversion
# output_folder = r"output\spacer_test"

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
# print("=" * 50)
# print("SPACER Test Completed!")
