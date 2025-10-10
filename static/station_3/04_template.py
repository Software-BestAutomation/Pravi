# python 04_template.py

import cv2 as cv
import numpy as np
from pathlib import Path

# ---- Configuration ----
ID_AREA_MIN, ID_AREA_MAX = 15000, 25000        # inner-hole contour area
OD_AREA_MIN, OD_AREA_MAX = 90000, 180000       # outer-disk contour area
IN_DIR  = Path("input_images")                 # folder with images
OUT_DIR = Path("output"); OUT_DIR.mkdir(exist_ok=True)

# Display/save size for all shown outputs
SHOW_SIZE = (1000, 700)  # (width, height)

# Or process explicit files (comment IN_DIR usage if using this list)
FILES = [
    "D:/Pravi/burr_images/new_glass/station3/dataset/9_oct_25/VCXG.2-32C/image0000389.bmp",
    "D:/Pravi/burr_images/new_glass/station3/dataset/9_oct_25/VCXG.2-32C/image0000388.bmp",
    "D:/Pravi/burr_images/new_glass/station3/dataset/9_oct_25/VCXG.2-32C/image0000384.bmp",
]

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

def find_best_contour_by_area(cnts, area_min, area_max):
    best_idx, best_area = None, -1.0
    for i, c in enumerate(cnts):
        a = cv.contourArea(c)
        if area_min <= a <= area_max and a > best_area:
            best_idx, best_area = i, a
    return best_idx, best_area

def process_one(path):
    img = cv.imread(str(path))
    if img is None:
        print(f"Skip unreadable: {path}")
        return
    vis = img.copy()
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    gray = cv.medianBlur(gray, 5)

    # Optional: detect bright ring (for context/annotation)
    ring = detect_ring_center(gray)
    if ring is not None:
        x,y,r = ring
        cv.circle(vis, (x,y), r, (0,128,255), 2)
        cv.circle(vis, (x,y), 3, (0,128,255), -1)

    # Segment bright objects (washer + ring lobes)
    _, thr = cv.threshold(gray, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)

    # Morphology to suppress thin ring lobes and consolidate the washer
    k_open  = cv.getStructuringElement(cv.MORPH_ELLIPSE, (5,5))
    k_close = cv.getStructuringElement(cv.MORPH_ELLIPSE, (11,11))
    binm = cv.morphologyEx(thr, cv.MORPH_OPEN,  k_open)
    binm = cv.morphologyEx(binm, cv.MORPH_CLOSE, k_close)

    # Find contours with hierarchy so that ID can be found as a child of OD
    cnts, hier = cv.findContours(binm, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
    hier = hier if hier is not None else np.zeros((1,0,4), dtype=np.int32)

    # Pick OD by area
    od_idx, od_area = find_best_contour_by_area(cnts, OD_AREA_MIN, OD_AREA_MAX)

    id_idx, id_area = None, None
    if od_idx is not None and hier.size:
        # Children whose parent == od_idx
        for j, c in enumerate(cnts):
            if hier[0][j][3] == od_idx:
                a = cv.contourArea(c)
                if ID_AREA_MIN <= a <= ID_AREA_MAX:
                    id_idx, id_area = j, a
                    break

    # If ID not found as a child (edge cases), fall back to global search
    if id_idx is None:
        id_idx, id_area = find_best_contour_by_area(cnts, ID_AREA_MIN, ID_AREA_MAX)

    # Draw results and label
    status = "PART ABSENT"
    if od_idx is not None:
        cv.drawContours(vis, [cnts[od_idx]], -1, (0,255,0), 2)
        M = cv.moments(cnts[od_idx])
        if M["m00"] != 0:
            cx = int(M["m10"]/M["m00"]); cy = int(M["m01"]/M["m00"])
            cv.circle(vis, (cx,cy), 3, (0,255,0), -1)
        status = "OD OK"
        if id_idx is not None:
            cv.drawContours(vis, [cnts[id_idx]], -1, (255,0,0), 2)
            status = "OD+ID OK"
    elif id_idx is not None:
        cv.drawContours(vis, [cnts[id_idx]], -1, (255,0,0), 2)
        status = "ID ONLY"

    # Put text and areas
    y0 = 30
    cv.putText(vis, status, (20,y0), cv.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,255), 2)
    y0 += 28
    cv.putText(vis, f"OD area: {int(od_area) if od_idx is not None else 0}", (20,y0),
               cv.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
    y0 += 24
    cv.putText(vis, f"ID area: {int(id_area) if id_idx is not None else 0}", (20,y0),
               cv.FONT_HERSHEY_SIMPLEX, 0.7, (255,0,0), 2)

    # ---- Resize all shown/saved outputs ----
    vis_show = cv.resize(vis, SHOW_SIZE, interpolation=cv.INTER_AREA)
    binm_color = cv.cvtColor(binm, cv.COLOR_GRAY2BGR)
    binm_show = cv.resize(binm_color, SHOW_SIZE, interpolation=cv.INTER_AREA)

    # Save outputs (resized)
    out_path = OUT_DIR / (Path(path).stem + "_out.png")
    dbg_path = OUT_DIR / (Path(path).stem + "_bin.png")
    cv.imwrite(str(out_path), vis_show)
    cv.imwrite(str(dbg_path), binm_show)

    # Show (press any key to advance)
    cv.imshow("result", vis_show)
    # cv.imshow("binary", binm_show)
    cv.waitKey(0); cv.destroyAllWindows()

# ---- Run on a folder or explicit files ----
if IN_DIR.exists():
    images = sorted([*IN_DIR.glob("*.jpg"), *IN_DIR.glob("*.png"),
                     *IN_DIR.glob("*.jpeg"), *IN_DIR.glob("*.bmp")])
else:
    images = [Path(f) for f in FILES]

for p in images:
    process_one(p)
