# python 06_template_final.py

import cv2 as cv
import numpy as np
from pathlib import Path

# [P0] CONFIGURATION
ID_AREA_MIN, ID_AREA_MAX = 15000, 20000        # inner-hole contour area (ID)
OD_AREA_MIN, OD_AREA_MAX = 120000, 150000       # outer-disk contour area (OD)
IN_DIR  = Path("input_images")                 # folder with images
OUT_DIR = Path("output"); OUT_DIR.mkdir(exist_ok=True)

# Display/save size for all shown outputs (visualizations only)
SHOW_SIZE = (1000, 700)  # (width, height)

# [P0.1] Optional explicit file list if directory mode is not used
FILES = [
    "D:/Pravi/burr_images/new_glass/station4/dataset/10_oct_25/image0000328.bmp",
    "D:/Pravi/burr_images/new_glass/station4/dataset/10_oct_25/image0000329.bmp",
    "D:/Pravi/burr_images/new_glass/station4/dataset/10_oct_25/image0000330.bmp",
    "D:/Pravi/burr_images/new_glass/station4/dataset/10_oct_25/image0000331.bmp",
    "D:/Pravi/burr_images/new_glass/station4/dataset/10_oct_25/image0000332.bmp",
    "D:/Pravi/burr_images/new_glass/station4/dataset/10_oct_25/image0000333.bmp",
    "D:/Pravi/burr_images/new_glass/station4/dataset/10_oct_25/image0000334.bmp",
    "D:/Pravi/burr_images/new_glass/station4/dataset/10_oct_25/image0000335.bmp",
    "D:/Pravi/burr_images/new_glass/station4/dataset/10_oct_25/image0000336.bmp",
    "D:/Pravi/burr_images/new_glass/station4/dataset/10_oct_25/image0000337.bmp",
    "D:/Pravi/burr_images/new_glass/station4/dataset/10_oct_25/image0000338.bmp",
    "D:/Pravi/burr_images/new_glass/station4/dataset/10_oct_25/image0000339.bmp",
    "D:/Pravi/burr_images/new_glass/station4/dataset/10_oct_25/image0000340.bmp",
    "D:/Pravi/burr_images/new_glass/station4/dataset/10_oct_25/image0000341.bmp",
    "D:/Pravi/burr_images/new_glass/station4/dataset/10_oct_25/image0000342.bmp",
    "D:/Pravi/burr_images/new_glass/station4/dataset/10_oct_25/image0000343.bmp",
    "D:/Pravi/burr_images/new_glass/station4/dataset/10_oct_25/image0000344.bmp",
    "D:/Pravi/burr_images/new_glass/station4/dataset/10_oct_25/image0000345.bmp",
    "D:/Pravi/burr_images/new_glass/station4/dataset/10_oct_25/image0000346.bmp",

]

# [P1] Optional ring annotation for context
def detect_ring_center(gray):
    h, w = gray.shape
    circles = cv.HoughCircles(
        gray, cv.HOUGH_GRADIENT, dp=1.2, minDist=min(h, w)//3,
        param1=120, param2=50,
        minRadius=int(0.20*min(h,w)), maxRadius=int(0.48*min(h,w))
    )
    if circles is None:
        return None
    x, y, r = np.round(circles[0,0]).astype(int)
    return (x, y, r)

# [P2] Pick best contour by area
def find_best_contour_by_area(cnts, area_min, area_max):
    best_idx, best_area = None, -1.0
    for i, c in enumerate(cnts):
        a = cv.contourArea(c)
        if area_min <= a <= area_max and a > best_area:
            best_idx, best_area = i, a
    return best_idx, best_area

# [P3] MAIN PROCESSOR
def process_one(path):
    # Load and preprocess
    img = cv.imread(str(path))
    if img is None:
        print(f"Skip unreadable: {path}")
        return
    vis = img.copy()
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    gray = cv.medianBlur(gray, 5)

    # Optional ring overlay
    ring = detect_ring_center(gray)
    if ring is not None:
        x,y,r = ring
        cv.circle(vis, (x,y), r, (0,128,255), 2)
        cv.circle(vis, (x,y), 3, (0,128,255), -1)

    # Threshold + morphology
    _, thr = cv.threshold(gray, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)
    k_open  = cv.getStructuringElement(cv.MORPH_ELLIPSE, (5,5))
    k_close = cv.getStructuringElement(cv.MORPH_ELLIPSE, (11,11))
    binm = cv.morphologyEx(thr, cv.MORPH_OPEN,  k_open)
    binm = cv.morphologyEx(binm, cv.MORPH_CLOSE, k_close)

    # Contours + hierarchy
    cnts, hier = cv.findContours(binm, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
    hier = hier if hier is not None else np.zeros((1,0,4), dtype=np.int32)

    # Select OD and ID
    od_idx, od_area = find_best_contour_by_area(cnts, OD_AREA_MIN, OD_AREA_MAX)
    id_idx, id_area = None, None
    if od_idx is not None and hier.size:
        for j, c in enumerate(cnts):
            if hier[0][j][3] == od_idx:
                a = cv.contourArea(c)
                if ID_AREA_MIN <= a <= ID_AREA_MAX:
                    id_idx, id_area = j, a
                    break
    if id_idx is None:
        id_idx, id_area = find_best_contour_by_area(cnts, ID_AREA_MIN, ID_AREA_MAX)

    # Draw contours if found
    if od_idx is not None:
        cv.drawContours(vis, [cnts[od_idx]], -1, (0,255,0), 2)
        M = cv.moments(cnts[od_idx])
        if M["m00"] != 0:
            cx = int(M["m10"]/M["m00"]); cy = int(M["m01"]/M["m00"])
            cv.circle(vis, (cx,cy), 3, (0,255,0), -1)
    if id_idx is not None:
        cv.drawContours(vis, [cnts[id_idx]], -1, (255,0,0), 2)

    # NEW STATUS RULES:
    # - Both present -> PART PRESENT
    # - Only ID or only OD -> PART ABSENT
    # - Neither -> PART ABSENT
    if (od_idx is not None) and (id_idx is not None):
        status = "PART PRESENT"
    else:
        status = "PART ABSENT"

    # Text overlay
    y0 = 100
    cv.putText(vis, status, (20,y0), cv.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,255), 2)
    y0 += 100
    # cv.putText(vis, f"OD area: {int(od_area) if od_idx is not None else 0}", (20,y0),
    #            cv.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
    y0 += 24
    # cv.putText(vis, f"ID area: {int(id_area) if id_idx is not None else 0}", (20,y0),
    #            cv.FONT_HERSHEY_SIMPLEX, 0.7, (255,0,0), 2)

    # Resize and save visualizations
    vis_show = cv.resize(vis, SHOW_SIZE, interpolation=cv.INTER_AREA)
    binm_color = cv.cvtColor(binm, cv.COLOR_GRAY2BGR)
    binm_show = cv.resize(binm_color, SHOW_SIZE, interpolation=cv.INTER_AREA)

    out_path = OUT_DIR / (Path(path).stem + "_out.png")
    dbg_path = OUT_DIR / (Path(path).stem + "_bin.png")
    cv.imwrite(str(out_path), vis_show)
    cv.imwrite(str(dbg_path), binm_show)

    # Display
    cv.imshow("result", vis_show)
    # cv.imshow("binary", binm_show)
    cv.waitKey(0); cv.destroyAllWindows()

# [P13] DRIVER
if IN_DIR.exists():
    images = sorted([*IN_DIR.glob("*.jpg"), *IN_DIR.glob("*.png"),
                     *IN_DIR.glob("*.jpeg"), *IN_DIR.glob("*.bmp")])
else:
    images = [Path(f) for f in FILES]

for p in images:
    process_one(p)
