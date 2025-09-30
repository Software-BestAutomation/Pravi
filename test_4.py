import cv2
import numpy as np
import math
from datetime import datetime
import os

# ------------------------------
# Debug utilities
# ------------------------------

class DebugSaver:
    def __init__(self, root="debug_output", session_name=None):
        self.session = session_name or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.root = os.path.join(root, self.session)
        os.makedirs(self.root, exist_ok=True)
        self.saved = []

    def _subdir(self, name):
        path = os.path.join(self.root, name)
        os.makedirs(path, exist_ok=True)
        return path

    def save(self, subfolder, filename, image):
        folder = self._subdir(subfolder)
        path = os.path.join(folder, filename)
        try:
            cv2.imwrite(path, image)
            self.saved.append(path)
        except Exception as e:
            # Ensure debugging never crashes pipeline
            pass
        return path

    def base_dir(self):
        return self.root

# ------------------------------
# Core functions (instrumented)
# ------------------------------

def preprocess_image(frame, debug: DebugSaver = None):
    # Original
    if debug:
        debug.save("preprocess", "00_original.bmp", frame)

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    if debug:
        debug.save("preprocess", "01_gray.bmp", gray)

    _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)
    if debug:
        debug.save("preprocess", "02_binary.bmp", binary)

    contours, hierarchy = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

    # Draw all contours
    all_ctrs = frame.copy()
    if len(contours) > 0:
        cv2.drawContours(all_ctrs, contours, -1, (0, 255, 0), 2)
    if debug:
        debug.save("preprocess", "03_all_contours.bmp", all_ctrs)

    # Keep top 3 non-background contours (skip largest if present)
    sorted_contours = sorted(contours, key=cv2.contourArea, reverse=True)[1:4] if len(contours) > 1 else []

    # Draw selected contours with labels
    sel = frame.copy()
    for i, c in enumerate(sorted_contours):
        cv2.drawContours(sel, [c], -1, (0, 255, 255), 3)
        M = cv2.moments(c)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            cv2.putText(sel, f"sorted[{i}]", (cx - 30, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    if debug:
        debug.save("preprocess", "04_sorted_top3.bmp", sel)

    return {
        "image": frame.copy(),
        "original_gray": gray,
        "binary": binary,
        "contours": contours,
        "hierarchy": hierarchy,
        "sorted_contours": sorted_contours
    }

def _get_center(contour):
    M = cv2.moments(contour)
    if M["m00"] == 0:
        return (0, 0)
    return (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

def _equivalent_radius(contour):
    area = cv2.contourArea(contour)
    return int(np.sqrt(area / np.pi)) if area > 0 else 0

def _avg_diameter_from_center_radius(cx, cy, radius, step_deg=10):
    diameters = []
    for angle in range(0, 360, step_deg):
        rad = math.radians(angle)
        pt1 = (int(cx + radius * math.cos(rad)), int(cy + radius * math.sin(rad)))
        pt2 = (int(cx - radius * math.cos(rad)), int(cy - radius * math.sin(rad)))
        diameters.append(math.hypot(pt2[0] - pt1[0], pt2[1] - pt1[1]))
    return sum(diameters) / len(diameters) if diameters else 0.0

def id_od_dimension(frame, sorted_contours, id_min=None, id_max=None, od_min=None, od_max=None,
                    pixel_to_micron_id=None, pixel_to_micron_od=None, debug: DebugSaver = None):
    if len(sorted_contours) < 2:
        raise ValueError("Not enough contours found for ID/OD measurement")

    od_contour = sorted_contours[0]
    id_contour = sorted_contours[1]

    # Centers and equivalent radii
    center_x_od, center_y_od = _get_center(od_contour)
    center_x_id, center_y_id = _get_center(id_contour)
    radius_od = _equivalent_radius(od_contour)
    radius_id = _equivalent_radius(id_contour)

    # Visualize OD/ID contours and centers
    vis = frame.copy()
    cv2.drawContours(vis, [od_contour], -1, (0, 0, 255), 2)
    cv2.drawContours(vis, [id_contour], -1, (255, 0, 0), 2)
    cv2.circle(vis, (center_x_od, center_y_od), 5, (0, 255, 0), -1)
    cv2.circle(vis, (center_x_id, center_y_id), 5, (0, 255, 0), -1)
    if debug:
        debug.save("dimensions", "00_od_id_contours_centers.bmp", vis)

    # Draw 36 chords for OD and ID
    chords = frame.copy()
    for angle in range(0, 360, 10):
        rad = math.radians(angle)
        # OD
        pt1_od = (int(center_x_od + radius_od * math.cos(rad)), int(center_y_od + radius_od * math.sin(rad)))
        pt2_od = (int(center_x_od - radius_od * math.cos(rad)), int(center_y_od - radius_od * math.sin(rad)))
        cv2.line(chords, pt1_od, pt2_od, (255, 0, 0), 1)
        # ID
        pt1_id = (int(center_x_id + radius_id * math.cos(rad)), int(center_y_id + radius_id * math.sin(rad)))
        pt2_id = (int(center_x_id - radius_id * math.cos(rad)), int(center_y_id - radius_id * math.sin(rad)))
        cv2.line(chords, pt1_id, pt2_id, (0, 0, 255), 1)
    if debug:
        debug.save("dimensions", "01_chords_both.bmp", chords)

    # Optional: equivalent-circle masks for ID/OD
    h, w = frame.shape[:2]
    id_mask = np.zeros((h, w), dtype=np.uint8)
    od_mask = np.zeros((h, w), dtype=np.uint8)
    cv2.circle(id_mask, (center_x_id, center_y_id), radius_id, 255, thickness=cv2.FILLED)
    cv2.circle(od_mask, (center_x_od, center_y_od), radius_od, 255, thickness=cv2.FILLED)
    if debug:
        debug.save("dimensions", "02_id_equiv_circle_mask.bmp", id_mask)
        debug.save("dimensions", "03_od_equiv_circle_mask.bmp", od_mask)

    # Diameter estimation via chord sampling on equivalent circle
    diameter_od_px = _avg_diameter_from_center_radius(center_x_od, center_y_od, radius_od)
    diameter_id_px = _avg_diameter_from_center_radius(center_x_id, center_y_id, radius_id)

    # Scale to mm
    px_to_mm_id = (pixel_to_micron_id or 0.0) / 1000.0
    px_to_mm_od = (pixel_to_micron_od or 0.0) / 1000.0
    diameter_od_mm = diameter_od_px * px_to_mm_od
    diameter_id_mm = diameter_id_px * px_to_mm_id

    # Annotate measured values
    ann = vis.copy()
    cv2.putText(ann, f"ID_px: {diameter_id_px:.2f}, ID_mm: {diameter_id_mm:.2f}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
    cv2.putText(ann, f"OD_px: {diameter_od_px:.2f}, OD_mm: {diameter_od_mm:.2f}", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    if debug:
        debug.save("dimensions", "04_dimensions_annotation.bmp", ann)

    return {
        "diameter_id_mm": round(diameter_id_mm, 2),
        "id_status": "OK" if (id_min is not None and id_max is not None and id_min <= diameter_id_mm <= id_max) else "NOK",
        "diameter_od_mm": round(diameter_od_mm, 2),
        "od_status": "OK" if (od_min is not None and od_max is not None and od_min <= diameter_od_mm <= od_max) else "NOK",
        "center_x_od": center_x_od,
        "center_y_od": center_y_od,
        "center_x_id": center_x_id,
        "center_y_id": center_y_id,
        "id_contour": id_contour,
        "od_contour": od_contour,
        "radius_od": radius_od,
        "radius_id": radius_id
    }

def concentricity(center_x_od, center_y_od, center_x_id, center_y_id, frame=None,
                  concentricity_max=None, pixel_to_micron=None, debug: DebugSaver = None):
    dist_px = math.hypot(center_x_od - center_x_id, center_y_od - center_y_id)
    dist_mm = (dist_px * (pixel_to_micron or 0.0)) / 1000.0
    result = {
        "concentricity_mm": round(dist_mm, 2),
        "concentricity_status": "OK" if (concentricity_max is not None and dist_mm <= concentricity_max) else "NOK"
    }

    if frame is not None:
        vis = frame.copy()
        cv2.circle(vis, (center_x_od, center_y_od), 5, (0, 255, 0), -1)
        cv2.circle(vis, (center_x_id, center_y_id), 5, (0, 255, 0), -1)
        cv2.line(vis, (center_x_od, center_y_od), (center_x_id, center_y_id), (0, 255, 0), 2)
        cv2.putText(vis, f"d_px: {dist_px:.2f}, d_mm: {dist_mm:.2f}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        if debug:
            debug.save("concentricity", "00_centers_line.bmp", vis)

    return result

def flash_detection(frame, id_contour, od_contour, threshold_id2, threshold_id3, threshold_od2, threshold_od3, debug: DebugSaver = None):
    fod_found = 0
    fid_found = 0

    img = frame.copy()
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    if debug:
        debug.save("flash", "00_original.bmp", img)
        debug.save("flash", "01_gray.bmp", gray_img)

    _, binary_image = cv2.threshold(gray_img, 128, 255, cv2.THRESH_BINARY)
    if debug:
        debug.save("flash", "02_binary.bmp", binary_image)

    contours, _ = cv2.findContours(binary_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    all_contours_img = img.copy()
    cv2.drawContours(all_contours_img, contours, -1, (0, 255, 0), 2)
    if debug:
        debug.save("flash", "03_all_contours.bmp", all_contours_img)

    # Build ID rings
    M = cv2.moments(id_contour)
    if M["m00"] != 0:
        id_center_x = int(M["m10"] / M["m00"])
        id_center_y = int(M["m01"] / M["m00"])
        id1_radius = int(np.sqrt(cv2.contourArea(id_contour) / np.pi))

        id_center_vis = img.copy()
        cv2.drawContours(id_center_vis, [id_contour], -1, (0, 255, 0), 2)
        cv2.circle(id_center_vis, (id_center_x, id_center_y), 5, (255, 0, 0), -1)
        cv2.circle(id_center_vis, (id_center_x, id_center_y), id1_radius, (255, 0, 0), 2)
        cv2.putText(id_center_vis, f"ID Center: ({id_center_x},{id_center_y}) R:{id1_radius}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        if debug:
            debug.save("flash", "04_id_center_radius.bmp", id_center_vis)

        h, w = gray_img.shape[:2]
        id1_mask = np.zeros((h, w), dtype=np.uint8)
        cv2.drawContours(id1_mask, [id_contour], -1, 255, thickness=cv2.FILLED)
        cv2.circle(id1_mask, (id_center_x, id_center_y), id1_radius, 255, thickness=cv2.FILLED)
        if debug:
            debug.save("flash", "05_id1_mask.bmp", id1_mask)

        id2_mask = np.zeros((h, w), dtype=np.uint8)
        id2_radius = max(0, id1_radius - int(threshold_id2))
        cv2.drawContours(id2_mask, [id_contour], -1, 255, thickness=cv2.FILLED)
        cv2.circle(id2_mask, (id_center_x, id_center_y), id2_radius, 255, thickness=cv2.FILLED)
        if debug:
            debug.save("flash", "06_id2_mask.bmp", id2_mask)

        id2_ring_mask = cv2.subtract(id1_mask, id2_mask)
        if debug:
            debug.save("flash", "07_id2_ring_mask.bmp", id2_ring_mask)

        id3_mask = np.zeros((h, w), dtype=np.uint8)
        id3_radius = id2_radius + int(threshold_id3)
        cv2.drawContours(id3_mask, [id_contour], -1, 255, thickness=cv2.FILLED)
        cv2.circle(id3_mask, (id_center_x, id_center_y), id3_radius, 255, thickness=cv2.FILLED)
        if debug:
            debug.save("flash", "08_id3_mask.bmp", id3_mask)

        id3_ring_mask = cv2.subtract(id3_mask, id2_mask)
        if debug:
            debug.save("flash", "09_id3_ring_mask.bmp", id3_ring_mask)

        # Contours in ID ring
        id3_gray = id3_ring_mask.copy()
        id3_ring_mask_contours, _ = cv2.findContours(id3_gray, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
        roi_id = img.copy()
        cv2.drawContours(roi_id, id3_ring_mask_contours, -1, (255, 0, 0), 2)
        if debug:
            debug.save("flash", "10_id_ring_contours.bmp", roi_id)

        id_sorted_flash_contour_lst = []
        for (i, c) in enumerate(id3_ring_mask_contours):
            id_perimeter = cv2.arcLength(c, True)
            if id_perimeter < 40:
                id_sorted_flash_contour_lst.append(c)
                fid_found = 1

        id_flash_contours_img = img.copy()
        cv2.drawContours(id_flash_contours_img, id_sorted_flash_contour_lst, -1, (0, 0, 255), 2)
        if debug:
            debug.save("flash", "11_id_flash_contours.bmp", id_flash_contours_img)

        id_boxes = img.copy()
        for (c) in id_sorted_flash_contour_lst:
            (x, y, w1, h1) = cv2.boundingRect(c)
            x1 = x - 10
            y1 = y - 3
            w2 = w1 + 30
            h2 = h1 + 30
            cv2.rectangle(id_boxes, (x1, y1), (x1 + w2, y1 + h2), (0, 0, 255), 2)
        if debug:
            debug.save("flash", "12_id_flash_boxes.bmp", id_boxes)

    # Build OD rings
    M = cv2.moments(od_contour)
    if M["m00"] != 0:
        od_center_x = int(M["m10"] / M["m00"])
        od_center_y = int(M["m01"] / M["m00"])
        od1_radius = int(np.sqrt(cv2.contourArea(od_contour) / np.pi))

        od_center_vis = img.copy()
        cv2.drawContours(od_center_vis, [od_contour], -1, (0, 255, 0), 2)
        cv2.circle(od_center_vis, (od_center_x, od_center_y), 5, (0, 255, 255), -1)
        cv2.circle(od_center_vis, (od_center_x, od_center_y), od1_radius, (0, 255, 255), 2)
        cv2.putText(od_center_vis, f"OD Center: ({od_center_x},{od_center_y}) R:{od1_radius}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        if debug:
            debug.save("flash", "13_od_center_radius.bmp", od_center_vis)

        h, w = gray_img.shape[:2]
        od1_mask = np.zeros((h, w), dtype=np.uint8)
        cv2.drawContours(od1_mask, [od_contour], -1, 255, thickness=cv2.FILLED)
        cv2.circle(od1_mask, (od_center_x, od_center_y), od1_radius, 255, thickness=cv2.FILLED)
        if debug:
            debug.save("flash", "14_od1_mask.bmp", od1_mask)

        od2_mask = np.zeros((h, w), dtype=np.uint8)
        od2_radius = od1_radius + int(threshold_od2)
        cv2.drawContours(od2_mask, [od_contour], -1, 255, thickness=cv2.FILLED)
        cv2.circle(od2_mask, (od_center_x, od_center_y), od2_radius, 255, thickness=cv2.FILLED)
        if debug:
            debug.save("flash", "15_od2_mask.bmp", od2_mask)

        od2_ring_mask = cv2.subtract(od2_mask, od1_mask)
        if debug:
            debug.save("flash", "16_od2_ring_mask.bmp", od2_ring_mask)

        od3_mask = np.zeros((h, w), dtype=np.uint8)
        od3_radius = max(0, od2_radius - int(threshold_od3))
        cv2.drawContours(od3_mask, [od_contour], -1, 255, thickness=cv2.FILLED)
        cv2.circle(od3_mask, (od_center_x, od_center_y), od3_radius, 255, thickness=cv2.FILLED)
        if debug:
            debug.save("flash", "17_od3_mask.bmp", od3_mask)

        od3_ring_mask = cv2.subtract(od2_mask, od3_mask)
        if debug:
            debug.save("flash", "18_od3_ring_mask.bmp", od3_ring_mask)

        # Contours in OD ring
        od3_gray = od3_ring_mask.copy()
        od3_ring_mask_contours, _ = cv2.findContours(od3_gray, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
        roi_od = img.copy()
        cv2.drawContours(roi_od, od3_ring_mask_contours, -1, (255, 0, 255), 2)
        if debug:
            debug.save("flash", "19_od_ring_contours.bmp", roi_od)

        od_sorted_flash_contour_lst = []
        for (i, c) in enumerate(od3_ring_mask_contours):
            od_perimeter = cv2.arcLength(c, True)
            if od_perimeter < 40:
                od_sorted_flash_contour_lst.append(c)
                fod_found = 1

        od_flash_contours_img = img.copy()
        cv2.drawContours(od_flash_contours_img, od_sorted_flash_contour_lst, -1, (255, 0, 255), 2)
        if debug:
            debug.save("flash", "20_od_flash_contours.bmp", od_flash_contours_img)

        od_boxes = img.copy()
        for (c) in od_sorted_flash_contour_lst:
            (x, y, w1, h1) = cv2.boundingRect(c)
            x1 = x - 10
            y1 = y - 5
            w2 = w1 + 30
            h2 = h1 + 30
            cv2.rectangle(od_boxes, (x1, y1), (x1 + w2, y1 + h2), (0, 0, 255), 2)
        if debug:
            debug.save("flash", "21_od_flash_boxes.bmp", od_boxes)

    defect_result = "OK"
    defect_position = "None"
    if fod_found:
        defect_result = "NOK"
        defect_position = "FOD"
    elif fid_found:
        defect_result = "NOK"
        defect_position = "FID"

    # Final combined overlay for flash
    final_flash = img.copy()
    txt = f"Flash: {defect_result} ({defect_position})"
    cv2.putText(final_flash, txt, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
    if debug:
        debug.save("flash", "22_flash_final_overlay.bmp", final_flash)

    return {
        "Defect_Result": defect_result,
        "defect_position": defect_position,
        "defect_type": "Flash",
        "flash_marked_image": final_flash
    }

def measure_orifice_from_sorted(frame, sorted_contours, orifice_min=None, orifice_max=None, pixel_to_micron=None, debug: DebugSaver = None):
    if sorted_contours is None or len(sorted_contours) < 3:
        return {"orifice_diameter_mm": 0.0, "orifice_status": "NOK", "orifice_contour": None,
                "center_x": 0, "center_y": 0, "radius": 0}

    contour = sorted_contours[2]
    M = cv2.moments(contour)
    if M["m00"] == 0:
        return {"orifice_diameter_mm": 0.0, "orifice_status": "NOK", "orifice_contour": None,
                "center_x": 0, "center_y": 0, "radius": 0}

    cx, cy = int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"])
    radius = _equivalent_radius(contour)

    # Visualize contour, center, radius
    vis = frame.copy()
    cv2.drawContours(vis, [contour], -1, (255, 0, 255), 2)
    cv2.circle(vis, (cx, cy), 5, (255, 0, 255), -1)
    cv2.circle(vis, (cx, cy), radius, (255, 0, 255), 1)
    if debug:
        debug.save("orifice_sorted", "00_orifice_contour_center_radius.bmp", vis)

    # 36 chords
    chords = frame.copy()
    for angle in range(0, 360, 10):
        rad = math.radians(angle)
        pt1 = (int(cx + radius * math.cos(rad)), int(cy + radius * math.sin(rad)))
        pt2 = (int(cx - radius * math.cos(rad)), int(cy - radius * math.sin(rad)))
        cv2.line(chords, pt1, pt2, (255, 0, 255), 1)
    if debug:
        debug.save("orifice_sorted", "01_orifice_chords.bmp", chords)

    diam_px = _avg_diameter_from_center_radius(cx, cy, radius)
    d_mm = (diam_px * (pixel_to_micron or 0.0)) / 1000.0
    status = "NOK"
    if orifice_min is not None and orifice_max is not None:
        status = "OK" if orifice_min <= d_mm <= orifice_max else "NOK"

    ann = vis.copy()
    cv2.putText(ann, f"Orifice_px: {diam_px:.2f}, Orifice_mm: {d_mm:.2f}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 255), 2)
    if debug:
        debug.save("orifice_sorted", "02_orifice_measurement_annotation.bmp", ann)

    return {
        "orifice_diameter_mm": round(d_mm, 2),
        "orifice_status": status,
        "orifice_contour": contour,
        "center_x": cx,
        "center_y": cy,
        "radius": radius
    }

def measure_orifice_legacy(frame, orifice_min=None, orifice_max=None, pixel_to_micron=None, min_area=50, debug: DebugSaver = None):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)
    if debug:
        debug.save("orifice_legacy", "00_gray.bmp", gray)
        debug.save("orifice_legacy", "01_binary.bmp", binary)

    contours, _ = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    all_ctrs = frame.copy()
    cv2.drawContours(all_ctrs, contours, -1, (0, 255, 0), 2)
    if debug:
        debug.save("orifice_legacy", "02_all_contours.bmp", all_ctrs)

    valid = []
    valid_vis = frame.copy()
    for c in contours:
        area = cv2.contourArea(c)
        if area >= min_area:
            perimeter = cv2.arcLength(c, True)
            if perimeter > 0:
                circ = 4 * np.pi * area / (perimeter ** 2)
                if 0.5 < circ < 1.5:
                    valid.append(c)
                    cv2.drawContours(valid_vis, [c], -1, (0, 255, 255), 2)
    if debug:
        debug.save("orifice_legacy", "03_valid_circularity_contours.bmp", valid_vis)

    if not valid:
        return {"orifice_diameter_mm": 0.0, "orifice_status": "NOK"}

    contour = sorted(valid, key=cv2.contourArea)[0]
    M = cv2.moments(contour)
    if M["m00"] == 0:
        return {"orifice_diameter_mm": 0.0, "orifice_status": "NOK"}

    cx, cy = int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"])
    radius = _equivalent_radius(contour)

    sel = frame.copy()
    cv2.drawContours(sel, [contour], -1, (0, 255, 255), 2)
    cv2.circle(sel, (cx, cy), 5, (0, 255, 255), -1)
    cv2.circle(sel, (cx, cy), radius, (0, 255, 255), 1)
    if debug:
        debug.save("orifice_legacy", "04_selected_orifice_contour.bmp", sel)

    chords = frame.copy()
    for angle in range(0, 360, 10):
        rad = math.radians(angle)
        pt1 = (int(cx + radius * math.cos(rad)), int(cy + radius * math.sin(rad)))
        pt2 = (int(cx - radius * math.cos(rad)), int(cy - radius * math.sin(rad)))
        cv2.line(chords, pt1, pt2, (0, 255, 255), 1)
    if debug:
        debug.save("orifice_legacy", "05_orifice_chords.bmp", chords)

    diam_px = _avg_diameter_from_center_radius(cx, cy, radius)
    d_mm = (diam_px * (pixel_to_micron or 0.0)) / 1000.0
    status = "OK" if (orifice_min is not None and orifice_max is not None and orifice_min <= d_mm <= orifice_max) else "NOK"

    ann = sel.copy()
    cv2.putText(ann, f"Orifice_px: {diam_px:.2f}, Orifice_mm: {d_mm:.2f}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
    if debug:
        debug.save("orifice_legacy", "06_orifice_measurement_annotation.bmp", ann)

    return {
        "orifice_diameter_mm": round(d_mm, 2),
        "orifice_status": status,
        "orifice_contour": contour,
        "center_x": cx,
        "center_y": cy,
        "radius": radius
    }

def save_final_result_image(image, dim_data, flash_data, concentricity_data=None, orifice_data=None, debug: DebugSaver = None):
    try:
        result_img = flash_data.get("flash_marked_image", image.copy())

        # Draw ID/OD contours
        cv2.drawContours(result_img, [dim_data["od_contour"]], -1, (0, 0, 255), 2)
        cv2.drawContours(result_img, [dim_data["id_contour"]], -1, (255, 0, 0), 2)

        # Draw centers
        cv2.circle(result_img, (dim_data["center_x_od"], dim_data["center_y_od"]), 5, (0, 255, 0), -1)
        cv2.circle(result_img, (dim_data["center_x_id"], dim_data["center_y_id"]), 5, (0, 255, 0), -1)

        # Draw diameter lines
        for angle in range(0, 360, 10):
            rad = math.radians(angle)
            # OD
            pt1_od = (int(dim_data["center_x_od"] + dim_data["radius_od"] * math.cos(rad)),
                      int(dim_data["center_y_od"] + dim_data["radius_od"] * math.sin(rad)))
            pt2_od = (int(dim_data["center_x_od"] - dim_data["radius_od"] * math.cos(rad)),
                      int(dim_data["center_y_od"] - dim_data["radius_od"] * math.sin(rad)))
            cv2.line(result_img, pt1_od, pt2_od, (255, 0, 0), 1)
            # ID
            pt1_id = (int(dim_data["center_x_id"] + dim_data["radius_id"] * math.cos(rad)),
                      int(dim_data["center_y_id"] + dim_data["radius_id"] * math.sin(rad)))
            pt2_id = (int(dim_data["center_x_id"] - dim_data["radius_id"] * math.cos(rad)),
                      int(dim_data["center_y_id"] - dim_data["radius_id"] * math.sin(rad)))
            cv2.line(result_img, pt1_id, pt2_id, (0, 0, 255), 1)

        # Concentricity
        if concentricity_data:
            cv2.line(result_img,
                     (dim_data["center_x_od"], dim_data["center_y_od"]),
                     (dim_data["center_x_id"], dim_data["center_y_id"]),
                     (0, 255, 0), 2)

        # Orifice chords
        if orifice_data and orifice_data.get("orifice_contour") is not None:
            cx, cy = orifice_data["center_x"], orifice_data["center_y"]
            radius = orifice_data["radius"]
            for angle in range(0, 360, 10):
                rad = math.radians(angle)
                pt1 = (int(cx + radius * math.cos(rad)), int(cy + radius * math.sin(rad)))
                pt2 = (int(cx - radius * math.cos(rad)), int(cy - radius * math.sin(rad)))
                cv2.line(result_img, pt1, pt2, (255, 0, 255), 1)

        # Annotations
        font = cv2.FONT_HERSHEY_SIMPLEX
        y = 50
        lh = 40
        cv2.putText(result_img, f"ID: {dim_data['diameter_id_mm']}mm ({dim_data['id_status']})", (50, y), font, 1.2, (255, 0, 0), 2); y += lh
        cv2.putText(result_img, f"OD: {dim_data['diameter_od_mm']}mm ({dim_data['od_status']})", (50, y), font, 1.2, (0, 0, 255), 2); y += lh
        if concentricity_data:
            cv2.putText(result_img, f"Concentricity: {concentricity_data['concentricity_mm']}mm ({concentricity_data['concentricity_status']})", (50, y), font, 1.2, (0, 255, 0), 2); y += lh
        if orifice_data:
            cv2.putText(result_img, f"Orifice: {orifice_data['orifice_diameter_mm']}mm ({orifice_data['orifice_status']})", (50, y), font, 1.2, (255, 0, 255), 2); y += lh
        cv2.putText(result_img, f"Flash: {flash_data['Defect_Result']} ({flash_data['defect_position']})", (50, y), font, 1.2, (0, 255, 0), 2)

        # Save final into debug_output/final
        if debug:
            out_path = debug.save("final", "cam1_bmp.bmp", result_img)
            return {"output_path": out_path, "success": True}
        else:
            # fallback local save
            os.makedirs("debug_output/final", exist_ok=True)
            out_path = os.path.join("debug_output/final", "cam1_bmp.bmp")
            cv2.imwrite(out_path, result_img)
            return {"output_path": out_path, "success": True}
    except Exception as e:
        return {"output_path": None, "success": False, "error": str(e)}

# ------------------------------
# Orchestrator (example usage)
# ------------------------------

def process_frame(
    frame,
    id_min, id_max,
    od_min, od_max,
    pixel_to_micron_id, pixel_to_micron_od,
    conc_max, conc_pixel_to_micron,
    thr_id2, thr_id3, thr_od2, thr_od3,
    orifice_min=None, orifice_max=None, orifice_pixel_to_micron=None,
    session_name=None
):
    debug = DebugSaver(root="debug_output", session_name=session_name)

    pre = preprocess_image(frame, debug=debug)

    dim = id_od_dimension(
        pre["image"],
        pre["sorted_contours"],
        id_min=id_min, id_max=id_max,
        od_min=od_min, od_max=od_max,
        pixel_to_micron_id=pixel_to_micron_id,
        pixel_to_micron_od=pixel_to_micron_od,
        debug=debug
    )

    conc = concentricity(
        dim["center_x_od"], dim["center_y_od"], dim["center_x_id"], dim["center_y_id"],
        frame=pre["image"],
        concentricity_max=conc_max,
        pixel_to_micron=conc_pixel_to_micron,
        debug=debug
    )

    flash = flash_detection(
        pre["image"],
        dim["id_contour"], dim["od_contour"],
        threshold_id2=thr_id2, threshold_id3=thr_id3,
        threshold_od2=thr_od2, threshold_od3=thr_od3,
        debug=debug
    )

    orifice_sorted = measure_orifice_from_sorted(
        pre["image"], pre["sorted_contours"],
        orifice_min=orifice_min, orifice_max=orifice_max,
        pixel_to_micron=orifice_pixel_to_micron,
        debug=debug
    )

    # Optional: legacy orifice (kept for comparison)
    orifice_legacy = measure_orifice_legacy(
        pre["image"],
        orifice_min=orifice_min, orifice_max=orifice_max,
        pixel_to_micron=orifice_pixel_to_micron,
        min_area=50,
        debug=debug
    )

    final_save = save_final_result_image(
        pre["image"], dim, flash, concentricity_data=conc, orifice_data=orifice_sorted, debug=debug
    )

    return {
        "debug_root": debug.base_dir(),
        "preprocess": pre,
        "dimensions": dim,
        "concentricity": conc,
        "flash": flash,
        "orifice_sorted": orifice_sorted,
        "orifice_legacy": orifice_legacy,
        "final": final_save,
        "all_saved_paths": debug.saved
    }


















# # updated 20_9_2025 (adds circularity/aspect ratio controls)
# # Test file example usage
# from station_4 import main
# import cv2

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

# output_folder = r"output\output_image"

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

























# # updated 20_9_2025 (adds circularity/aspect ratio controls)
# # Test file example usage
# from station_4 import main
# import cv2

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

# # Burr Detection Parameters
# ID2_OFFSET = "20"
# HIGHLIGHT_SIZE = "20"
# id_BURR_MIN_AREA = "60"
# id_BURR_MAX_AREA = "400"
# id_BURR_MIN_PERIMETER = "30"
# id_BURR_MAX_PERIMETER = "300"

# output_folder = r"output\output_image"

# # Call main function with all parameters
# result = main(
#     part, subpart, frame,
#     ID2_OFFSET, HIGHLIGHT_SIZE,
#     id_BURR_MIN_AREA, id_BURR_MAX_AREA,
#     id_BURR_MIN_PERIMETER, id_BURR_MAX_PERIMETER,
#     min_id_area, max_id_area,
#     min_od_area, max_od_area,
#     # NEW: shape filters
#     min_circularity, max_circularity, min_aspect_ratio, max_aspect_ratio,
#     output_folder
# )

# print("--- Final Result ---")
# print(result)


















# # updated 14_9_2025
# # Test file example usage
# from station_4 import main
# import cv2

# # Load test image
# image_path = r"D:\PIM_15-09-25\Pravi_Flask\static\Cam1InputImages\cam4.bmp"
# frame = cv2.imread(image_path)

# # ==== Configurable Parameters ====
# part = "SUPPORT PISTON"
# subpart = "28.10.019"

# # ID/OD Contour Area Parameters (Easy to modify)
# min_id_area = "14000"      # Minimum area for ID contour detection
# max_id_area = "16200"      # Maximum area for ID contour detection
# min_od_area = "95000"     # Minimum area for OD contour detection  
# max_od_area = "130000"     # Maximum area for OD contour detection

# # Burr Detection Parameters
# ID2_OFFSET = "20"
# HIGHLIGHT_SIZE = "20"
# id_BURR_MIN_AREA = "60"
# id_BURR_MAX_AREA = "400"
# id_BURR_MIN_PERIMETER = "30"
# id_BURR_MAX_PERIMETER = "300"

# output_folder = r"output\output_image"

# # Call main function with all parameters
# result = main(
#     part, subpart, frame,
#     ID2_OFFSET, HIGHLIGHT_SIZE, 
#     id_BURR_MIN_AREA, id_BURR_MAX_AREA, 
#     id_BURR_MIN_PERIMETER, id_BURR_MAX_PERIMETER,
#     min_id_area, max_id_area, 
#     min_od_area, max_od_area,
#     output_folder
# )

# print("--- Final Result ---")
# print(result)






















# old 13_9_2025

# # python station_4.py
# from station_4 import main
# import cv2

# # Load test image
# # image_path = r"D:\pravi\burr\burr_july\9_july_25\support_piston\16_06_012\VCXG.2-32C\VCXG.2-32C\VCXG.2-32C\image0000323.bmp"
# image_path = r"D:\Pravi\burr_images\new_glass\station1\dataset\19_9_25\VCXG.2-32C\image0000314.bmp"
# #image_path = r"D:\Pravi\burr_images\new_glass\station4\dataset\5_9_25\VCXG.2-32C\image0000292.bmp"
# frame = cv2.imread(image_path)
# print(f"DEBUG: Loaded image from: {image_path}")  # Debug: Image loading confirmation

# # ==== Parameters ====  # Parameters passed as strings as in production environment
# part = "SUPPORT PISTON"
# subpart = " 28.10.019"
# ID2_OFFSET = "20"
# HIGHLIGHT_SIZE = "80"
# id_BURR_MIN_AREA = "20"
# id_BURR_MAX_AREA = "400"
# id_BURR_MIN_PERIMETER = "30"
# id_BURR_MAX_PERIMETER = "300"
# output_folder = r"output\\output_image"

# print("DEBUG: Parameters set:", part, subpart, ID2_OFFSET, HIGHLIGHT_SIZE, id_BURR_MIN_AREA, id_BURR_MAX_AREA, id_BURR_MIN_PERIMETER, id_BURR_MAX_PERIMETER)  # Debug: Parameter confirmation

# # ==== Call the main() function from station_4 ====
# result = main(
#     part, subpart, frame,
#     ID2_OFFSET, HIGHLIGHT_SIZE, id_BURR_MIN_AREA,
#     id_BURR_MAX_AREA, id_BURR_MIN_PERIMETER, id_BURR_MAX_PERIMETER,
#     output_folder
# )

# # ==== Output ====
# print("\n--- Final Returned Output ---")
# print(result)
