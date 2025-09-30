from station2 import main
import cv2
import numpy as np

# ==== Load Test Image ====
#image_path = r"D:\Pravi\burr_images\new_glass\station4\dataset\5_9_25\VCXG.2-32C\image0000504.bmp"
image_path = r"D:\Pravi\burr_images\new_glass\station2\dataset\29_9_25\VCXG.2-32C\image0000579.bmp" 
#D:\PIM_15-09-25\Pravi_Flask\static\Cam1InputImages

frame = cv2.imread(image_path)

# ==== Parameters ====
part = "O RING"
subpart = "28.10.039"
thick_min = "2.30"          # Example minimum thickness in mm
thick_max = "2.70"          # Example maximum thickness in mm
pixel_to_micron = "44"    # Example conversion factor (microns per pixel)
output_folder = r"output\output_image"

# New threshold parameters for software control
min_thresh = "70"         # Threshold value (can be changed by software) 60
max_thresh = "255"         # Maximum value for thresholding (can be changed by software)

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
    max_thresh=max_thresh
)

# ==== Output ====
print("\n--- Final Returned Output ---")
print(result)






# # # 18_sep_25
# from station2 import main
# import cv2
# import numpy as np

# # ==== Load Test Image ====
# #image_path = r"D:\Pravi\burr_images\new_glass\station4\dataset\5_9_25\VCXG.2-32C\image0000504.bmp"
# image_path = r"D:\PIM_15-09-25\Pravi_Flask\static\Cam1InputImages\image0000563.bmp" 
# #D:\PIM_15-09-25\Pravi_Flask\static\Cam1InputImages

# frame = cv2.imread(image_path)

# # ==== Parameters ====
# part = "PISTON"
# subpart = "22.10.015"
# thick_min = "0.1"          # Example minimum thickness in mm
# thick_max = "6.10"          # Example maximum thickness in mm
# pixel_to_micron = "44"    # Example conversion factor (microns per pixel)
# output_folder = r"output\\output_image"

# # ==== Call the main() Function ====
# result = main(
#     part=part,
#     subpart=subpart,
#     frame=frame,
#     thick_min=thick_min,
#     thick_max=thick_max,
#     pixel_to_micron=pixel_to_micron,
#     output_folder=output_folder
# )

# # ==== Output ====
# print("\n--- Final Returned Output ---")
# print(result)



























# from station2 import main
# import cv2
# import numpy as np

# # ==== Load Test Image ====
# image_path = r"D:\PIM_08-07-2025\Pravi_Flask\static\Cam1InputImages\Cam2.bmp"
# frame = cv2.imread(image_path)

# # ==== Parameters ====
# part = "SPACER"
# subpart = "28.14.152"
# thick_min = "5.90"          # Example minimum thickness in mm
# thick_max = "6.10"          # Example maximum thickness in mm
# pixel_to_micron = "53.87"    # Example conversion factor (microns per pixel)
# output_folder = r"output\\output_image"

# # ==== Call the main() Function ====
# result = main(
#     part=part,
#     subpart=subpart,
#     frame=frame,
#     thick_min=thick_min,
#     thick_max=thick_max,
#     pixel_to_micron=pixel_to_micron,
#     output_folder=output_folder
# )



# # ==== Output ====
# print("\n--- Final Returned Output ---")
# print(result)
