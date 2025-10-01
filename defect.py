# code 3

# # working 28 sep 25 11pm
# changes because of support pistong ring part
# =============== Drawing / Visualization Parameters ===============
CONTOUR_THICKNESS = 1
DIAMETER_LINE_THICKNESS = 1
CENTER_DOT_RADIUS = 5
CENTER_DOT_THICKNESS = -1

PREPROCESS_CONTOUR_COLOR = (0, 255, 0)
ID_CONTOUR_COLOR = (0, 255, 0)
OD_CONTOUR_COLOR = (0, 0, 255)

DIAMETER_ID_COLOR = (0, 0, 255)
DIAMETER_OD_COLOR = (255, 0, 0)
CONCENTRICITY_COLOR = (255, 0, 0)
ORIFICE_DIAMETER_COLOR = (255, 0, 255)
CENTER_COLOR = (0, 255, 0)

DEFECT_CONTOUR_COLOR_ID = (0, 0, 255)
DEFECT_CONTOUR_COLOR_OD = (255, 0, 255)
DEFECT_BOX_COLOR = (0, 0, 255)

# ========== Library Imports ==============
import cv2
import numpy as np
import math
from datetime import datetime
import os
import time

ENABLE_TIMING = True

# ============ 1. Preprocessing Function ============
def preprocess_image(frame, output_folder=None):
    if ENABLE_TIMING:
        start_time = time.time()
    
    if output_folder:
        os.makedirs(output_folder, exist_ok=True)
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 190, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    sorted_contours = sorted(contours, key=cv2.contourArea, reverse=True)[1:3] if len(contours) > 1 else []
    contour_image = frame.copy()
    cv2.drawContours(contour_image, sorted_contours, -1, PREPROCESS_CONTOUR_COLOR, CONTOUR_THICKNESS)
    if output_folder:
        cv2.imwrite(os.path.join(output_folder, 'contours.bmp'), contour_image)
    
    if ENABLE_TIMING:
        elapsed = (time.time() - start_time) * 1000
        print(f"[preprocess_image] Time: {elapsed:.2f} ms")

    return {
        "image": frame.copy(),
        "sorted_contours": sorted_contours,
        "original_gray": gray
    }

# =========== 2. ID/OD Measurement ===========
def id_od_dimension(frame, sorted_contours, id_min=None, id_max=None, od_min=None, od_max=None,
                    pixel_to_micron_id=None, pixel_to_micron_od=None):
    if ENABLE_TIMING:
        start_time = time.time()
    
    if len(sorted_contours) < 2:
        raise ValueError("Not enough contours found for ID/OD measurement")
    
    od_contour, id_contour = sorted_contours[0], sorted_contours[1]

    def get_center(contour):
        M = cv2.moments(contour)
        if M["m00"] == 0:
            return (0, 0)
        return (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
    
    center_x_od, center_y_od = get_center(od_contour)
    center_x_id, center_y_id = get_center(id_contour)
    radius_od = int(np.sqrt(cv2.contourArea(od_contour) / np.pi))
    radius_id = int(np.sqrt(cv2.contourArea(id_contour) / np.pi))

    def get_avg_diameter(center_x, center_y, radius):
        diameters = []
        for angle in range(0, 360, 10):
            rad = math.radians(angle)
            pt1 = (int(center_x + radius * math.cos(rad)), int(center_y + radius * math.sin(rad)))
            pt2 = (int(center_x - radius * math.cos(rad)), int(center_y - radius * math.sin(rad)))
            diameters.append(math.hypot(pt2[0] - pt1[0], pt2[1] - pt1[1]))
        return sum(diameters) / len(diameters)

    diameter_od = get_avg_diameter(center_x_od, center_y_od, radius_od)
    diameter_id = get_avg_diameter(center_x_id, center_y_id, radius_id)
    diameter_od_mm = (diameter_od * pixel_to_micron_od) / 1000.0
    diameter_id_mm = (diameter_id * pixel_to_micron_id) / 1000.0
    diameter_od_px = round(diameter_od, 2)
    diameter_id_px = round(diameter_id, 2)
    
    if ENABLE_TIMING:
        elapsed = (time.time() - start_time) * 1000
        print(f"[id_od_dimension] Time: {elapsed:.2f} ms")
    
    return {
        "diameter_id_mm": round(diameter_id_mm, 2),
        "diameter_id_px": diameter_id_px,
        "id_status": "OK" if id_min <= diameter_id_mm <= id_max else "NOK",
        "diameter_od_mm": round(diameter_od_mm, 2),
        "diameter_od_px": diameter_od_px,
        "od_status": "OK" if od_min <= diameter_od_mm <= od_max else "NOK",
        "center_x_od": center_x_od,
        "center_y_od": center_y_od,
        "center_x_id": center_x_id,
        "center_y_id": center_y_id,
        "id_contour": id_contour,
        "od_contour": od_contour,
        "radius_od": radius_od,
        "radius_id": radius_id
    }

# =========== 3. Concentricity Measurement ===========
def concentricity(center_x_od, center_y_od, center_x_id, center_y_id, concentricity_max=None, pixel_to_micron=None):
    if ENABLE_TIMING:
        start_time = time.time()
    
    dist_px = math.hypot(center_x_od - center_x_id, center_y_od - center_y_id)
    dist_mm = (dist_px * pixel_to_micron) / 1000.0
    
    if ENABLE_TIMING:
        elapsed = (time.time() - start_time) * 1000
        print(f"[concentricity] Time: {elapsed:.2f} ms")
    
    return {
        "concentricity_mm": round(dist_mm, 2),
        "concentricity_status": "OK" if dist_mm <= concentricity_max else "NOK"
    }

# =========== 4. Flash (Defect) Detection ===========
def flash_detection(frame, id_contour, od_contour, threshold_id2, threshold_id3, threshold_od2, threshold_od3, output_folder=None):
    if ENABLE_TIMING:
        start_time = time.time()

    fod_found = 0
    fid_found = 0
    img = frame.copy()
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary_image = cv2.threshold(gray_img, 128, 255, cv2.THRESH_BINARY)

    if output_folder:
        cv2.imwrite(os.path.join(output_folder, "02_binary_threshold_ID.bmp"), binary_image)
    
    contours, _ = cv2.findContours(binary_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    all_contours_img = img.copy()
    cv2.drawContours(all_contours_img, contours, -1, PREPROCESS_CONTOUR_COLOR, CONTOUR_THICKNESS)
    
    if contours and len(contours) > 1:
        sorted_contours = sorted(contours, key=cv2.contourArea, reverse=True)[1:3]
        sorted_contours_img = img.copy()
        for i, contour in enumerate(sorted_contours):
            cv2.drawContours(sorted_contours_img, [contour], -1, PREPROCESS_CONTOUR_COLOR, CONTOUR_THICKNESS)
            M = cv2.moments(contour)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                cv2.putText(sorted_contours_img, f"Contour {i}", (cx-30, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        od_contours = sorted_contours[0]
        id_contours = sorted_contours[1]

        M = cv2.moments(id_contours)
        if M["m00"] != 0:
            id_center_x = int(M["m10"] / M["m00"])
            id_center_y = int(M["m01"] / M["m00"])
            id1_radius = int(np.sqrt(cv2.contourArea(id_contours) / np.pi))
            id1_mask = np.zeros_like(gray_img)
            cv2.drawContours(id1_mask, id_contours, -1, 255, thickness=cv2.FILLED)
            cv2.circle(id1_mask, (id_center_x, id_center_y), id1_radius, 255, thickness=cv2.FILLED)
            id2_mask = np.zeros_like(gray_img)
            id2_radius = id1_radius - threshold_id2
            cv2.drawContours(id2_mask, id_contours, -1, 255, thickness=cv2.FILLED)
            cv2.circle(id2_mask, (id_center_x, id_center_y), id2_radius, 255, thickness=cv2.FILLED)
            id2_ring_mask = cv2.subtract(id1_mask, id2_mask)
            id3_mask = np.zeros_like(gray_img)
            id3_radius = id2_radius + threshold_id3
            cv2.drawContours(id3_mask, id_contours, -1, 255, thickness=cv2.FILLED)
            cv2.circle(id3_mask, (id_center_x, id_center_y), id3_radius, 255, thickness=cv2.FILLED)
            id3_ring_mask = cv2.subtract(id3_mask, id2_mask)
            id3_mask_img = cv2.cvtColor(id3_ring_mask, cv2.COLOR_GRAY2BGR)
            gray = cv2.cvtColor(id3_mask_img, cv2.COLOR_BGR2GRAY)
            id3_ring_mask_contours, _ = cv2.findContours(gray, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
            roi_id_od = img.copy()
            cv2.drawContours(roi_id_od, id3_ring_mask_contours, -1, ID_CONTOUR_COLOR, CONTOUR_THICKNESS)
            id_sorted_flash_contour_lst = []
            for (i, c) in enumerate(id3_ring_mask_contours):
                id_perimeter = cv2.arcLength(c, True)
                print("Contour #{} --id_perimeter: {:.2f}".format(i + 1, id_perimeter))
                if id_perimeter < 40:
                    id_sorted_flash_contour_lst.append(c)
                    fid_found = 1
            id_flash_contours_img = img.copy()
            cv2.drawContours(id_flash_contours_img, id_sorted_flash_contour_lst, -1, DEFECT_CONTOUR_COLOR_ID, CONTOUR_THICKNESS)
            if output_folder:
                cv2.imwrite(os.path.join(output_folder, '08_id_flash_contours.bmp'), id_flash_contours_img)
            for (c) in id_sorted_flash_contour_lst:
                (x, y, w, h) = cv2.boundingRect(c)
                x1 = x - 10
                y1 = y - 3
                w1 = w + 30
                h1 = h + 30
                cv2.rectangle(img, (x1, y1), (x1 + w1, y1 + h1), DEFECT_BOX_COLOR, CONTOUR_THICKNESS)
        
        M = cv2.moments(od_contours)
        if M["m00"] != 0:
            od_center_x = int(M["m10"] / M["m00"])
            od_center_y = int(M["m01"] / M["m00"])
            od1_radius = int(np.sqrt(cv2.contourArea(od_contours) / np.pi))
            od1_mask = np.zeros_like(gray_img)
            cv2.drawContours(od1_mask, od_contours, -1, 255, thickness=cv2.FILLED)
            cv2.circle(od1_mask, (od_center_x, od_center_y), od1_radius, 255, thickness=cv2.FILLED)
            od2_mask = np.zeros_like(gray_img)
            od2_radius = od1_radius + threshold_od2
            cv2.drawContours(od2_mask, od_contours, -1, 255, thickness=cv2.FILLED)
            cv2.circle(od2_mask, (od_center_x, od_center_y), od2_radius, 255, thickness=cv2.FILLED)
            od2_ring_mask = cv2.subtract(od2_mask, od1_mask)
            od3_mask = np.zeros_like(gray_img)
            od3_radius = od2_radius - threshold_od3
            cv2.drawContours(od3_mask, od_contours, -1, 255, thickness=cv2.FILLED)
            cv2.circle(od3_mask, (od_center_x, od_center_y), od3_radius, 255, thickness=cv2.FILLED)
            od3_ring_mask = cv2.subtract(od2_mask, od3_mask)
            od3_mask_img = cv2.cvtColor(od3_ring_mask, cv2.COLOR_GRAY2BGR)
            gray = cv2.cvtColor(od3_mask_img, cv2.COLOR_BGR2GRAY)
            od3_ring_mask_contours, _ = cv2.findContours(gray, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
            try:
                roi_id_od
            except NameError:
                roi_id_od = img.copy()
            cv2.drawContours(roi_id_od, od3_ring_mask_contours, -1, OD_CONTOUR_COLOR, CONTOUR_THICKNESS)
            od_sorted_flash_contour_lst = []
            for (i, c) in enumerate(od3_ring_mask_contours):
                od_perimeter = cv2.arcLength(c, True)
                print("Contour OD #{}: perimeter: {:.2f}".format(i + 1, od_perimeter))
                if od_perimeter < 40:
                    od_sorted_flash_contour_lst.append(c)
                    fod_found = 1
                    print("fod found")
            od_flash_contours_img = img.copy()
            cv2.drawContours(od_flash_contours_img, od_sorted_flash_contour_lst, -1, DEFECT_CONTOUR_COLOR_OD, CONTOUR_THICKNESS)
            for (c) in od_sorted_flash_contour_lst:
                (x, y, w, h) = cv2.boundingRect(c)
                x1 = x - 10
                y1 = y - 5
                w1 = w + 30
                h1 = h + 30
                cv2.rectangle(img, (x1, y1), (x1 + w1, y1 + h1), DEFECT_BOX_COLOR, CONTOUR_THICKNESS)
        else:
            print("Warning: OD3 ring mask is empty - check radius calculations")

    if fod_found:
        defect_result = "NOK"
        defect_position = "FOD"
    elif fid_found:
        defect_result = "NOK"
        defect_position = "FID"
    else:
        defect_result = "OK"
        defect_position = "None"
    print(f"Flash detection complete - Result: {defect_result}, Position: {defect_position}")

    if ENABLE_TIMING:
        elapsed = (time.time() - start_time) * 1000
        print(f"[flash_detection] Time: {elapsed:.2f} ms")

    return {
        "Defect_Result": defect_result,
        "defect_position": defect_position,
        "defect_type": "Flash",
        "flash_marked_image": img
    }

# =========== 5. Orifice Measurement ===========
def measure_orifice(frame, orifice_min=None, orifice_max=None, pixel_to_micron=None, min_area=500):
    if ENABLE_TIMING:
        start_time = time.time()
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

    valid = []
    for c in contours:
        area = cv2.contourArea(c)
        if area >= min_area:
            perimeter = cv2.arcLength(c, True)
            if perimeter > 0:
                circ = 4 * np.pi * area / (perimeter**2)
                if 0.5 < circ < 1.5:
                    valid.append(c)

    if not valid:
        if ENABLE_TIMING:
            elapsed = (time.time() - start_time) * 1000
            print(f"[measure_orifice] Time: {elapsed:.2f} ms")
        return {"orifice_diameter_mm": 0.0, "orifice_status": "NOK"}

    contour = sorted(valid, key=cv2.contourArea)[0]
    M = cv2.moments(contour)
    if M["m00"] == 0:
        if ENABLE_TIMING:
            elapsed = (time.time() - start_time) * 1000
            print(f"[measure_orifice] Time: {elapsed:.2f} ms")
        return {"orifice_diameter_mm": 0.0, "orifice_status": "NOK"}

    cx, cy = int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"])
    radius = int(np.sqrt(cv2.contourArea(contour) / np.pi))

    diameters = []
    for angle in range(0, 360, 10):
        rad = math.radians(angle)
        pt1 = (int(cx + radius * math.cos(rad)), int(cy + radius * math.sin(rad)))
        pt2 = (int(cx - radius * math.cos(rad)), int(cy - radius * math.sin(rad)))
        diameters.append(math.hypot(pt2[0] - pt1[0], pt2[1] - pt1[1]))
    avg = sum(diameters) / len(diameters)
    d_mm = (avg * pixel_to_micron) / 1000.0

    if ENABLE_TIMING:
        elapsed = (time.time() - start_time) * 1000
        print(f"[measure_orifice] Time: {elapsed:.2f} ms")

    return {
        "orifice_diameter_mm": round(d_mm, 2),
        "orifice_status": "OK" if orifice_min <= d_mm <= orifice_max else "NOK",
        "orifice_contour": contour,
        "center_x": cx,
        "center_y": cy,
        "radius": radius
    }

# ========= 6. Save Annotated Result Image ==========
def save_final_result_image(image, dim_data, flash_data, concentricity_data=None, orifice_data=None, output_folder="output_images"):
    if ENABLE_TIMING:
        start_time = time.time()
    try:
        # Prefer flash-marked image; fallback to original image
        result_img = flash_data.get("flash_marked_image", None)
        if result_img is None:
            result_img = image.copy()

        os.makedirs(output_folder, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Draw overlays if possible
        try:
            cv2.drawContours(result_img, [dim_data["od_contour"]], -1, OD_CONTOUR_COLOR, CONTOUR_THICKNESS)
            cv2.drawContours(result_img, [dim_data["id_contour"]], -1, ID_CONTOUR_COLOR, CONTOUR_THICKNESS)
            cv2.circle(result_img, (int(dim_data["center_x_od"]), int(dim_data["center_y_od"])), CENTER_DOT_RADIUS, CENTER_COLOR, CENTER_DOT_THICKNESS)
            cv2.circle(result_img, (int(dim_data["center_x_id"]), int(dim_data["center_y_id"])), CENTER_DOT_RADIUS, CENTER_COLOR, CENTER_DOT_THICKNESS)
            for angle in range(0, 360, 10):
                rad = math.radians(angle)
                pt1_od = (int(dim_data["center_x_od"] + dim_data["radius_od"] * math.cos(rad)), int(dim_data["center_y_od"] + dim_data["radius_od"] * math.sin(rad)))
                pt2_od = (int(dim_data["center_x_od"] - dim_data["radius_od"] * math.cos(rad)), int(dim_data["center_y_od"] - dim_data["radius_od"] * math.sin(rad)))
                cv2.line(result_img, pt1_od, pt2_od, DIAMETER_OD_COLOR, DIAMETER_LINE_THICKNESS)
                pt1_id = (int(dim_data["center_x_id"] + dim_data["radius_id"] * math.cos(rad)), int(dim_data["center_y_id"] + dim_data["radius_id"] * math.sin(rad)))
                pt2_id = (int(dim_data["center_x_id"] - dim_data["radius_id"] * math.cos(rad)), int(dim_data["center_y_id"] - dim_data["radius_id"] * math.sin(rad)))
                cv2.line(result_img, pt1_id, pt2_id, DIAMETER_ID_COLOR, DIAMETER_LINE_THICKNESS)
            if concentricity_data:
                cv2.line(result_img,
                         (int(dim_data["center_x_od"]), int(dim_data["center_y_od"])),
                         (int(dim_data["center_x_id"]), int(dim_data["center_y_id"])),
                         CONCENTRICITY_COLOR, 2)
            if orifice_data and orifice_data.get("orifice_contour") is not None:
                cx, cy = int(orifice_data["center_x"]), int(orifice_data["center_y"])
                radius = int(orifice_data["radius"])
                for angle in range(0, 360, 10):
                    rad = math.radians(angle)
                    pt1 = (int(cx + radius * math.cos(rad)), int(cy + radius * math.sin(rad)))
                    pt2 = (int(cx - radius * math.cos(rad)), int(cy - radius * math.sin(rad)))
                    cv2.line(result_img, pt1, pt2, ORIFICE_DIAMETER_COLOR, DIAMETER_LINE_THICKNESS)
            font = cv2.FONT_HERSHEY_SIMPLEX
            y = 50
            lh = 40
            cv2.putText(
                result_img,
                f"ID: {dim_data['diameter_id_mm']}mm | {dim_data['diameter_id_px']}px ({dim_data['id_status']})",
                (50, y), font, 1.2, ID_CONTOUR_COLOR, 2
            ); y += lh
            cv2.putText(
                result_img,
                f"OD: {dim_data['diameter_od_mm']}mm | {dim_data['diameter_od_px']}px ({dim_data['od_status']})",
                (50, y), font, 1.2, OD_CONTOUR_COLOR, 2
            ); y += lh
            if concentricity_data:
                cv2.putText(result_img, f"Concentricity: {concentricity_data['concentricity_mm']}mm ({concentricity_data['concentricity_status']})",
                            (50, y), font, 1.2, CONCENTRICITY_COLOR, 2); y += lh
            if orifice_data:
                cv2.putText(result_img, f"Orifice: {orifice_data['orifice_diameter_mm']}mm ({orifice_data['orifice_status']})",
                            (50, y), font, 1.2, ORIFICE_DIAMETER_COLOR, 2); y += lh
            cv2.putText(result_img, f"Flash: {flash_data['Defect_Result']} ({flash_data['defect_position']})",
                        (50, y), font, 1.2, CONCENTRICITY_COLOR, 2)
        except Exception as _draw_e:
            print(f"Overlay drawing warning: {_draw_e}")

        # Attempt to write annotated image; else fallback to original
        filename = "cam1_bmp.bmp"
        output_path = os.path.join(output_folder, filename)

        write_ok = cv2.imwrite(output_path, result_img)
        if not write_ok:
            print("Annotated write failed, attempting fallback with original image")
            write_ok = cv2.imwrite(output_path, image)

        if ENABLE_TIMING:
            elapsed = (time.time() - start_time) * 1000
            print(f"[save_final_result_image] Time: {elapsed:.2f} ms")

        return {"output_path": output_path if write_ok else None, "success": bool(write_ok)}
    except Exception as e:
        # Last-resort fallback: try to save the original image anyway
        try:
            os.makedirs(output_folder, exist_ok=True)
            output_path = os.path.join(output_folder, "cam1_bmp.bmp")
            ok = cv2.imwrite(output_path, image)
            if ENABLE_TIMING:
                elapsed = (time.time() - start_time) * 1000
                print(f"[save_final_result_image] Time: {elapsed:.2f} ms")
            return {"output_path": output_path if ok else None, "success": bool(ok), "error": str(e)}
        except Exception as _e:
            if ENABLE_TIMING:
                elapsed = (time.time() - start_time) * 1000
                print(f"[save_final_result_image] Time: {elapsed:.2f} ms")
            return {"output_path": None, "success": False, "error": f"{e} | fallback: {_e}"}































# # # working  30/9/25 4pm
#  # # working 28 sep 25 11pm
# # changes because of support pistong ring part
# # =============== Drawing / Visualization Parameters ===============
# CONTOUR_THICKNESS = 1
# DIAMETER_LINE_THICKNESS = 1
# CENTER_DOT_RADIUS = 5
# CENTER_DOT_THICKNESS = -1

# PREPROCESS_CONTOUR_COLOR = (0, 255, 0)
# ID_CONTOUR_COLOR = (0, 255, 0)
# OD_CONTOUR_COLOR = (0, 0, 255)

# DIAMETER_ID_COLOR = (0, 0, 255)
# DIAMETER_OD_COLOR = (255, 0, 0)
# CONCENTRICITY_COLOR = (255, 0, 0)
# ORIFICE_DIAMETER_COLOR = (255, 0, 255)
# CENTER_COLOR = (0, 255, 0)

# DEFECT_CONTOUR_COLOR_ID = (0, 0, 255)
# DEFECT_CONTOUR_COLOR_OD = (255, 0, 255)
# DEFECT_BOX_COLOR = (0, 0, 255)

# # ========== Library Imports ==============
# import cv2
# import numpy as np
# import math
# from datetime import datetime
# import os
# import time

# ENABLE_TIMING = True

# # ============ 1. Preprocessing Function ============
# def preprocess_image(frame, output_folder=None):
#     if ENABLE_TIMING:
#         start_time = time.time()
    
#     if output_folder:
#         os.makedirs(output_folder, exist_ok=True)
    
#     gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#     _, binary = cv2.threshold(gray, 190, 255, cv2.THRESH_BINARY)
#     contours, _ = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
#     sorted_contours = sorted(contours, key=cv2.contourArea, reverse=True)[1:3] if len(contours) > 1 else []
#     contour_image = frame.copy()
#     cv2.drawContours(contour_image, sorted_contours, -1, PREPROCESS_CONTOUR_COLOR, CONTOUR_THICKNESS)
#     if output_folder:
#         cv2.imwrite(os.path.join(output_folder, 'contours.bmp'), contour_image)
    
#     if ENABLE_TIMING:
#         elapsed = (time.time() - start_time) * 1000
#         print(f"[preprocess_image] Time: {elapsed:.2f} ms")

#     return {
#         "image": frame.copy(),
#         "sorted_contours": sorted_contours,
#         "original_gray": gray
#     }

# # =========== 2. ID/OD Measurement ===========
# def id_od_dimension(frame, sorted_contours, id_min=None, id_max=None, od_min=None, od_max=None,
#                     pixel_to_micron_id=None, pixel_to_micron_od=None):
#     if ENABLE_TIMING:
#         start_time = time.time()
    
#     if len(sorted_contours) < 2:
#         raise ValueError("Not enough contours found for ID/OD measurement")
    
#     od_contour, id_contour = sorted_contours[0], sorted_contours[1]

#     def get_center(contour):
#         M = cv2.moments(contour)
#         if M["m00"] == 0:
#             return (0, 0)
#         return (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
    
#     center_x_od, center_y_od = get_center(od_contour)
#     center_x_id, center_y_id = get_center(id_contour)
#     radius_od = int(np.sqrt(cv2.contourArea(od_contour) / np.pi))
#     radius_id = int(np.sqrt(cv2.contourArea(id_contour) / np.pi))

#     def get_avg_diameter(center_x, center_y, radius):
#         diameters = []
#         for angle in range(0, 360, 10):
#             rad = math.radians(angle)
#             pt1 = (int(center_x + radius * math.cos(rad)), int(center_y + radius * math.sin(rad)))
#             pt2 = (int(center_x - radius * math.cos(rad)), int(center_y - radius * math.sin(rad)))
#             diameters.append(math.hypot(pt2[0] - pt1[0], pt2[1] - pt1[1]))
#         return sum(diameters) / len(diameters)

#     diameter_od = get_avg_diameter(center_x_od, center_y_od, radius_od)
#     diameter_id = get_avg_diameter(center_x_id, center_y_id, radius_id)
#     diameter_od_mm = (diameter_od * pixel_to_micron_od) / 1000.0
#     diameter_id_mm = (diameter_id * pixel_to_micron_id) / 1000.0
#     diameter_od_px = round(diameter_od, 2)
#     diameter_id_px = round(diameter_id, 2)
    
#     if ENABLE_TIMING:
#         elapsed = (time.time() - start_time) * 1000
#         print(f"[id_od_dimension] Time: {elapsed:.2f} ms")
    
#     return {
#         "diameter_id_mm": round(diameter_id_mm, 2),
#         "diameter_id_px": diameter_id_px,
#         "id_status": "OK" if id_min <= diameter_id_mm <= id_max else "NOK",
#         "diameter_od_mm": round(diameter_od_mm, 2),
#         "diameter_od_px": diameter_od_px,
#         "od_status": "OK" if od_min <= diameter_od_mm <= od_max else "NOK",
#         "center_x_od": center_x_od,
#         "center_y_od": center_y_od,
#         "center_x_id": center_x_id,
#         "center_y_id": center_y_id,
#         "id_contour": id_contour,
#         "od_contour": od_contour,
#         "radius_od": radius_od,
#         "radius_id": radius_id
#     }

# # =========== 3. Concentricity Measurement ===========
# def concentricity(center_x_od, center_y_od, center_x_id, center_y_id, concentricity_max=None, pixel_to_micron=None):
#     if ENABLE_TIMING:
#         start_time = time.time()
    
#     dist_px = math.hypot(center_x_od - center_x_id, center_y_od - center_y_id)
#     dist_mm = (dist_px * pixel_to_micron) / 1000.0
    
#     if ENABLE_TIMING:
#         elapsed = (time.time() - start_time) * 1000
#         print(f"[concentricity] Time: {elapsed:.2f} ms")
    
#     return {
#         "concentricity_mm": round(dist_mm, 2),
#         "concentricity_status": "OK" if dist_mm <= concentricity_max else "NOK"
#     }

# # =========== 4. Flash (Defect) Detection ===========
# def flash_detection(frame, id_contour, od_contour, threshold_id2, threshold_id3, threshold_od2, threshold_od3, output_folder=None):
#     if ENABLE_TIMING:
#         start_time = time.time()

#     fod_found = 0
#     fid_found = 0
#     img = frame.copy()
#     gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#     _, binary_image = cv2.threshold(gray_img, 128, 255, cv2.THRESH_BINARY)

#     if output_folder:
#         cv2.imwrite(os.path.join(output_folder, "02_binary_threshold_ID.bmp"), binary_image)
    
#     contours, _ = cv2.findContours(binary_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
#     all_contours_img = img.copy()
#     cv2.drawContours(all_contours_img, contours, -1, PREPROCESS_CONTOUR_COLOR, CONTOUR_THICKNESS)
    
#     if contours and len(contours) > 1:
#         sorted_contours = sorted(contours, key=cv2.contourArea, reverse=True)[1:3]
#         sorted_contours_img = img.copy()
#         for i, contour in enumerate(sorted_contours):
#             cv2.drawContours(sorted_contours_img, [contour], -1, PREPROCESS_CONTOUR_COLOR, CONTOUR_THICKNESS)
#             M = cv2.moments(contour)
#             if M["m00"] != 0:
#                 cx = int(M["m10"] / M["m00"])
#                 cy = int(M["m01"] / M["m00"])
#                 cv2.putText(sorted_contours_img, f"Contour {i}", (cx-30, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

#         od_contours = sorted_contours[0]
#         id_contours = sorted_contours[1]

#         M = cv2.moments(id_contours)
#         if M["m00"] != 0:
#             id_center_x = int(M["m10"] / M["m00"])
#             id_center_y = int(M["m01"] / M["m00"])
#             id1_radius = int(np.sqrt(cv2.contourArea(id_contours) / np.pi))
#             id1_mask = np.zeros_like(gray_img)
#             cv2.drawContours(id1_mask, id_contours, -1, 255, thickness=cv2.FILLED)
#             cv2.circle(id1_mask, (id_center_x, id_center_y), id1_radius, 255, thickness=cv2.FILLED)
#             id2_mask = np.zeros_like(gray_img)
#             id2_radius = id1_radius - threshold_id2
#             cv2.drawContours(id2_mask, id_contours, -1, 255, thickness=cv2.FILLED)
#             cv2.circle(id2_mask, (id_center_x, id_center_y), id2_radius, 255, thickness=cv2.FILLED)
#             id2_ring_mask = cv2.subtract(id1_mask, id2_mask)
#             id3_mask = np.zeros_like(gray_img)
#             id3_radius = id2_radius + threshold_id3
#             cv2.drawContours(id3_mask, id_contours, -1, 255, thickness=cv2.FILLED)
#             cv2.circle(id3_mask, (id_center_x, id_center_y), id3_radius, 255, thickness=cv2.FILLED)
#             id3_ring_mask = cv2.subtract(id3_mask, id2_mask)
#             id3_mask_img = cv2.cvtColor(id3_ring_mask, cv2.COLOR_GRAY2BGR)
#             gray = cv2.cvtColor(id3_mask_img, cv2.COLOR_BGR2GRAY)
#             id3_ring_mask_contours, _ = cv2.findContours(gray, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
#             roi_id_od = img.copy()
#             cv2.drawContours(roi_id_od, id3_ring_mask_contours, -1, ID_CONTOUR_COLOR, CONTOUR_THICKNESS)
#             id_sorted_flash_contour_lst = []
#             for (i, c) in enumerate(id3_ring_mask_contours):
#                 id_perimeter = cv2.arcLength(c, True)
#                 print("Contour #{} --id_perimeter: {:.2f}".format(i + 1, id_perimeter))
#                 if id_perimeter < 40:
#                     id_sorted_flash_contour_lst.append(c)
#                     fid_found = 1
#             id_flash_contours_img = img.copy()
#             cv2.drawContours(id_flash_contours_img, id_sorted_flash_contour_lst, -1, DEFECT_CONTOUR_COLOR_ID, CONTOUR_THICKNESS)
#             if output_folder:
#                 cv2.imwrite(os.path.join(output_folder, '08_id_flash_contours.bmp'), id_flash_contours_img)
#             for (c) in id_sorted_flash_contour_lst:
#                 (x, y, w, h) = cv2.boundingRect(c)
#                 x1 = x - 10
#                 y1 = y - 3
#                 w1 = w + 30
#                 h1 = h + 30
#                 cv2.rectangle(img, (x1, y1), (x1 + w1, y1 + h1), DEFECT_BOX_COLOR, CONTOUR_THICKNESS)
        
#         M = cv2.moments(od_contours)
#         if M["m00"] != 0:
#             od_center_x = int(M["m10"] / M["m00"])
#             od_center_y = int(M["m01"] / M["m00"])
#             od1_radius = int(np.sqrt(cv2.contourArea(od_contours) / np.pi))
#             od1_mask = np.zeros_like(gray_img)
#             cv2.drawContours(od1_mask, od_contours, -1, 255, thickness=cv2.FILLED)
#             cv2.circle(od1_mask, (od_center_x, od_center_y), od1_radius, 255, thickness=cv2.FILLED)
#             od2_mask = np.zeros_like(gray_img)
#             od2_radius = od1_radius + threshold_od2
#             cv2.drawContours(od2_mask, od_contours, -1, 255, thickness=cv2.FILLED)
#             cv2.circle(od2_mask, (od_center_x, od_center_y), od2_radius, 255, thickness=cv2.FILLED)
#             od2_ring_mask = cv2.subtract(od2_mask, od1_mask)
#             od3_mask = np.zeros_like(gray_img)
#             od3_radius = od2_radius - threshold_od3
#             cv2.drawContours(od3_mask, od_contours, -1, 255, thickness=cv2.FILLED)
#             cv2.circle(od3_mask, (od_center_x, od_center_y), od3_radius, 255, thickness=cv2.FILLED)
#             od3_ring_mask = cv2.subtract(od2_mask, od3_mask)
#             od3_mask_img = cv2.cvtColor(od3_ring_mask, cv2.COLOR_GRAY2BGR)
#             gray = cv2.cvtColor(od3_mask_img, cv2.COLOR_BGR2GRAY)
#             od3_ring_mask_contours, _ = cv2.findContours(gray, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
#             try:
#                 roi_id_od
#             except NameError:
#                 roi_id_od = img.copy()
#             cv2.drawContours(roi_id_od, od3_ring_mask_contours, -1, OD_CONTOUR_COLOR, CONTOUR_THICKNESS)
#             od_sorted_flash_contour_lst = []
#             for (i, c) in enumerate(od3_ring_mask_contours):
#                 od_perimeter = cv2.arcLength(c, True)
#                 print("Contour OD #{}: perimeter: {:.2f}".format(i + 1, od_perimeter))
#                 if od_perimeter < 40:
#                     od_sorted_flash_contour_lst.append(c)
#                     fod_found = 1
#                     print("fod found")
#             od_flash_contours_img = img.copy()
#             cv2.drawContours(od_flash_contours_img, od_sorted_flash_contour_lst, -1, DEFECT_CONTOUR_COLOR_OD, CONTOUR_THICKNESS)
#             for (c) in od_sorted_flash_contour_lst:
#                 (x, y, w, h) = cv2.boundingRect(c)
#                 x1 = x - 10
#                 y1 = y - 5
#                 w1 = w + 30
#                 h1 = h + 30
#                 cv2.rectangle(img, (x1, y1), (x1 + w1, y1 + h1), DEFECT_BOX_COLOR, CONTOUR_THICKNESS)
#         else:
#             print("Warning: OD3 ring mask is empty - check radius calculations")

#     if fod_found:
#         defect_result = "NOK"
#         defect_position = "FOD"
#     elif fid_found:
#         defect_result = "NOK"
#         defect_position = "FID"
#     else:
#         defect_result = "OK"
#         defect_position = "None"
#     print(f"Flash detection complete - Result: {defect_result}, Position: {defect_position}")

#     if ENABLE_TIMING:
#         elapsed = (time.time() - start_time) * 1000
#         print(f"[flash_detection] Time: {elapsed:.2f} ms")

#     return {
#         "Defect_Result": defect_result,
#         "defect_position": defect_position,
#         "defect_type": "Flash",
#         "flash_marked_image": img
#     }

# # =========== 5. Orifice Measurement ===========
# def measure_orifice(frame, orifice_min=None, orifice_max=None, pixel_to_micron=None, min_area=500):
#     if ENABLE_TIMING:
#         start_time = time.time()
    
#     gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#     _, binary = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)
#     contours, _ = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

#     valid = []
#     for c in contours:
#         area = cv2.contourArea(c)
#         if area >= min_area:
#             perimeter = cv2.arcLength(c, True)
#             if perimeter > 0:
#                 circ = 4 * np.pi * area / (perimeter**2)
#                 if 0.5 < circ < 1.5:
#                     valid.append(c)

#     if not valid:
#         if ENABLE_TIMING:
#             elapsed = (time.time() - start_time) * 1000
#             print(f"[measure_orifice] Time: {elapsed:.2f} ms")
#         return {"orifice_diameter_mm": 0.0, "orifice_status": "NOK"}

#     contour = sorted(valid, key=cv2.contourArea)[0]
#     M = cv2.moments(contour)
#     if M["m00"] == 0:
#         if ENABLE_TIMING:
#             elapsed = (time.time() - start_time) * 1000
#             print(f"[measure_orifice] Time: {elapsed:.2f} ms")
#         return {"orifice_diameter_mm": 0.0, "orifice_status": "NOK"}

#     cx, cy = int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"])
#     radius = int(np.sqrt(cv2.contourArea(contour) / np.pi))

#     diameters = []
#     for angle in range(0, 360, 10):
#         rad = math.radians(angle)
#         pt1 = (int(cx + radius * math.cos(rad)), int(cy + radius * math.sin(rad)))
#         pt2 = (int(cx - radius * math.cos(rad)), int(cy - radius * math.sin(rad)))
#         diameters.append(math.hypot(pt2[0] - pt1[0], pt2[1] - pt1[1]))
#     avg = sum(diameters) / len(diameters)
#     d_mm = (avg * pixel_to_micron) / 1000.0

#     if ENABLE_TIMING:
#         elapsed = (time.time() - start_time) * 1000
#         print(f"[measure_orifice] Time: {elapsed:.2f} ms")

#     return {
#         "orifice_diameter_mm": round(d_mm, 2),
#         "orifice_status": "OK" if orifice_min <= d_mm <= orifice_max else "NOK",
#         "orifice_contour": contour,
#         "center_x": cx,
#         "center_y": cy,
#         "radius": radius
#     }

# # ========= 6. Save Annotated Result Image ==========
# def save_final_result_image(image, dim_data, flash_data, concentricity_data=None, orifice_data=None, output_folder="output_images"):
#     if ENABLE_TIMING:
#         start_time = time.time()
#     try:
#         result_img = flash_data.get("flash_marked_image", image.copy())
#         os.makedirs(output_folder, exist_ok=True)
#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#         cv2.drawContours(result_img, [dim_data["od_contour"]], -1, OD_CONTOUR_COLOR, CONTOUR_THICKNESS)
#         cv2.drawContours(result_img, [dim_data["id_contour"]], -1, ID_CONTOUR_COLOR, CONTOUR_THICKNESS)
#         cv2.circle(result_img, (dim_data["center_x_od"], dim_data["center_y_od"]), CENTER_DOT_RADIUS, CENTER_COLOR, CENTER_DOT_THICKNESS)
#         cv2.circle(result_img, (dim_data["center_x_id"], dim_data["center_y_id"]), CENTER_DOT_RADIUS, CENTER_COLOR, CENTER_DOT_THICKNESS)
#         for angle in range(0, 360, 10):
#             rad = math.radians(angle)
#             pt1_od = (int(dim_data["center_x_od"] + dim_data["radius_od"] * math.cos(rad)), int(dim_data["center_y_od"] + dim_data["radius_od"] * math.sin(rad)))
#             pt2_od = (int(dim_data["center_x_od"] - dim_data["radius_od"] * math.cos(rad)), int(dim_data["center_y_od"] - dim_data["radius_od"] * math.sin(rad)))
#             cv2.line(result_img, pt1_od, pt2_od, DIAMETER_OD_COLOR, DIAMETER_LINE_THICKNESS)
#             pt1_id = (int(dim_data["center_x_id"] + dim_data["radius_id"] * math.cos(rad)), int(dim_data["center_y_id"] + dim_data["radius_id"] * math.sin(rad)))
#             pt2_id = (int(dim_data["center_x_id"] - dim_data["radius_id"] * math.cos(rad)), int(dim_data["center_y_id"] - dim_data["radius_id"] * math.sin(rad)))
#             cv2.line(result_img, pt1_id, pt2_id, DIAMETER_ID_COLOR, DIAMETER_LINE_THICKNESS)
#         if concentricity_data:
#             cv2.line(result_img,
#                      (dim_data["center_x_od"], dim_data["center_y_od"]),
#                      (dim_data["center_x_id"], dim_data["center_y_id"]),
#                      CONCENTRICITY_COLOR, 2)
#         if orifice_data and orifice_data.get("orifice_contour") is not None:
#             cx, cy = orifice_data["center_x"], orifice_data["center_y"]
#             radius = orifice_data["radius"]
#             for angle in range(0, 360, 10):
#                 rad = math.radians(angle)
#                 pt1 = (int(cx + radius * math.cos(rad)), int(cy + radius * math.sin(rad)))
#                 pt2 = (int(cx - radius * math.cos(rad)), int(cy - radius * math.sin(rad)))
#                 cv2.line(result_img, pt1, pt2, ORIFICE_DIAMETER_COLOR, DIAMETER_LINE_THICKNESS)
#         font = cv2.FONT_HERSHEY_SIMPLEX
#         y = 50
#         lh = 40
#         cv2.putText(
#             result_img,
#             f"ID: {dim_data['diameter_id_mm']}mm | {dim_data['diameter_id_px']}px ({dim_data['id_status']})",
#             (50, y), font, 1.2, ID_CONTOUR_COLOR, 2
#         ); y += lh
#         cv2.putText(
#             result_img,
#             f"OD: {dim_data['diameter_od_mm']}mm | {dim_data['diameter_od_px']}px ({dim_data['od_status']})",
#             (50, y), font, 1.2, OD_CONTOUR_COLOR, 2
#         ); y += lh
#         if concentricity_data:
#             cv2.putText(result_img, f"Concentricity: {concentricity_data['concentricity_mm']}mm ({concentricity_data['concentricity_status']})",
#                         (50, y), font, 1.2, CONCENTRICITY_COLOR, 2); y += lh
#         if orifice_data:
#             cv2.putText(result_img, f"Orifice: {orifice_data['orifice_diameter_mm']}mm ({orifice_data['orifice_status']})",
#                         (50, y), font, 1.2, ORIFICE_DIAMETER_COLOR, 2); y += lh
#         cv2.putText(result_img, f"Flash: {flash_data['Defect_Result']} ({flash_data['defect_position']})",
#                     (50, y), font, 1.2, CONCENTRICITY_COLOR, 2)
#         filename = f"cam1_bmp.bmp"
#         output_path = os.path.join(output_folder, filename)
#         cv2.imwrite(output_path, result_img)
#         if ENABLE_TIMING:
#             elapsed = (time.time() - start_time) * 1000
#             print(f"[save_final_result_image] Time: {elapsed:.2f} ms")
#         return {"output_path": output_path, "success": True}
#     except Exception as e:
#         if ENABLE_TIMING:
#             elapsed = (time.time() - start_time) * 1000
#             print(f"[save_final_result_image] Time: {elapsed:.2f} ms")
#         return {"output_path": None, "success": False, "error": str(e)}
















