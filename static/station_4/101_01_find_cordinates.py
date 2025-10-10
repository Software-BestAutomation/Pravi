# python 101_01_find_cordinates.py

"""
Use: Move mouse pointer on image & it will show gray color
"""
import cv2
import numpy as np
import matplotlib.pyplot as plt


#image_path = "trials\\bg_removed_img_gray_IMG_20240215_170211564.png"
image_path = r"D:\PIM_25-09-25\Pravi_Flask\static\Cam1InputImages\input_backup_cam2\2025-10-07\15\VCXG.2-32C\image0000585.bmp"
brown_ring_image = cv2.imread(image_path)

# Display the image using matplotlib
plt.figure(figsize=(12, 6))
plt.imshow(cv2.cvtColor(brown_ring_image, cv2.COLOR_BGR2GRAY))
plt.axis('off')
plt.title('Brown Ring with White Spot')
plt.show()
