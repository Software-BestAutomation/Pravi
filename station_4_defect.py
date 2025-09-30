# updated 20_9_2025 (adds circularity/aspect ratio filters into contour selection)
# updated 23_9_2025 (adds detect_burr_both and union-cropped combined overlay for cam3_bmp)
import cv2
import numpy as np
import math
from datetime import datetime
import os

import time

def _circularity(contour):
    """4*pi*A/P^2 — returns None if perimeter is zero."""
    area = cv2.contourArea(contour)
    perim = cv2.arcLength(contour, True)
    if perim <= 0:
        return None, area, perim
    c = 4.0 * math.pi * area / (perim * perim)
    return c, area, perim

def _aspect_ratio(contour):
    """w/h from boundingRect — returns None if h==0."""
    x, y, w, h = cv2.boundingRect(contour)
    if h == 0:
        return None, (w, h)
    return float(w) / float(h), (w, h)

def _passes_shape_filters(contour, min_circularity, max_circularity, min_aspect_ratio, max_aspect_ratio):
    """Check optional shape constraints; any None disables that constraint."""
    if min_circularity is not None or max_circularity is not None:
        c, _, _ = _circularity(contour)
        if c is None:
            return False
        if min_circularity is not None and c < min_circularity:
            return False
        if max_circularity is not None and c > max_circularity:
            return False
    if min_aspect_ratio is not None or max_aspect_ratio is not None:
        ar, _ = _aspect_ratio(contour)
        if ar is None:
            return False
        if min_aspect_ratio is not None and ar < min_aspect_ratio:
            return False
        if max_aspect_ratio is not None and ar > max_aspect_ratio:
            return False
    return True

def preprocess_image(frame, min_id_area=None, max_id_area=None,
                     min_od_area=None, max_od_area=None,
                     min_circularity=None, max_circularity=None,
                     min_aspect_ratio=None, max_aspect_ratio=None,
                     output_folder=None):
    """Preprocessing with area + shape filters to select ID/OD contours."""
    if output_folder:
        os.makedirs(output_folder, exist_ok=True)

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)
    binary_inv = cv2.bitwise_not(binary)

    contours, _ = cv2.findContours(binary_inv, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    sorted_contours = sorted(contours, key=cv2.contourArea, reverse=True)

    # Select ID contour
    id_contour = None
    if min_id_area is not None and max_id_area is not None:
        for contour in sorted_contours:
            area = cv2.contourArea(contour)
            if min_id_area <= area <= max_id_area:
                if _passes_shape_filters(contour, min_circularity, max_circularity, min_aspect_ratio, max_aspect_ratio):
                    id_contour = contour
                    break

    # Select OD contour
    od_contour = None
    if min_od_area is not None and max_od_area is not None:
        for contour in sorted_contours:
            area = cv2.contourArea(contour)
            if min_od_area <= area <= max_od_area:
                if _passes_shape_filters(contour, min_circularity, max_circularity, min_aspect_ratio, max_aspect_ratio):
                    od_contour = contour
                    break

    contour_img = frame.copy()
    if id_contour is not None:
        cv2.drawContours(contour_img, [id_contour], -1, (0, 255, 0), 3)
    if od_contour is not None:
        cv2.drawContours(contour_img, [od_contour], -1, (0, 255, 0), 3)

    return {
        "image": frame.copy(),
        "sorted_contours": sorted_contours,
        "original_gray": gray,
        "id_contour": id_contour,
        "od_contour": od_contour,
        "contour_image": contour_img
    }

def crop_around_contour(image, contour, crop_size=400):
    """Square crop around a contour centroid with clamped bounds."""
    h, w = image.shape[:2]
    m = cv2.moments(contour)
    if m['m00'] == 0:
        center = tuple(contour[0][0])
    else:
        cx = int(m['m10'] / m['m00'])
        cy = int(m['m01'] / m['m00'])
        center = (cx, cy)
    x_start = max(center[0] - crop_size, 0)
    y_start = max(center[1] - crop_size, 0)
    x_end = min(center[0] + crop_size, w)
    y_end = min(center[1] + crop_size, h)
    return image[y_start:y_end, x_start:x_end]

def _union_crop(image, contours, pad=30):
    """Tight union crop around multiple contours with padding."""
    pts_list = []
    for c in contours:
        if c is not None and len(c) > 0:
            pts_list.append(c.reshape(-1, 2))
    if not pts_list:
        return image
    pts = np.vstack(pts_list)
    x, y, w0, h0 = cv2.boundingRect(pts)
    x0 = max(x - pad, 0)
    y0 = max(y - pad, 0)
    x1 = min(x + w0 + pad, image.shape[1])
    y1 = min(y + h0 + pad, image.shape[0])
    return image[y0:y1, x0:x1]

def _filled_mask_from_contour(gray, contour):
    mask = np.zeros_like(gray, dtype=np.uint8)
    cv2.drawContours(mask, [contour], -1, 255, cv2.FILLED)
    return mask

def _analyze_zone(image, gray, edges, inner_mask, outer_mask,
                  HIGHLIGHT_SIZE, burr_area_min, burr_area_max, burr_perim_min, burr_perim_max,
                  draw_id=None, draw_od=None, crop_contour=None):
    """Edge-in-ring analysis with area/perimeter burr filtering and visualization."""
    analysis_zone = cv2.subtract(outer_mask, inner_mask)
    zone_edges = cv2.bitwise_and(edges, edges, mask=analysis_zone)
    edge_contours, _ = cv2.findContours(zone_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    burrs = []
    for e in edge_contours:
        ea = cv2.contourArea(e)
        ep = cv2.arcLength(e, True)
        if (burr_area_min <= ea <= burr_area_max) and (burr_perim_min <= ep <= burr_perim_max):
            burrs.append(e)

    out = image.copy()
    if draw_id is not None:
        cv2.drawContours(out, [draw_id], -1, (0, 255, 0), 4)
    if draw_od is not None:
        cv2.drawContours(out, [draw_od], -1, (0, 255, 0), 4)

    for b in burrs:
        x, y, w, h = cv2.boundingRect(b)
        cx2, cy2 = x + w // 2, y + h // 2
        cv2.rectangle(out,
                      (cx2 - HIGHLIGHT_SIZE // 2, cy2 - HIGHLIGHT_SIZE // 2),
                      (cx2 + HIGHLIGHT_SIZE // 2, cy2 + HIGHLIGHT_SIZE // 2),
                      (255, 0, 0), 3)

    status_text = "NOK - BURR DETECTED" if burrs else "OK - NO BURR"
    status_color = (0, 0, 255) if burrs else (0, 255, 0)
    tsize = cv2.getTextSize(status_text, cv2.FONT_HERSHEY_SIMPLEX, 2, 5)[0]
    tx = (out.shape[1] - tsize[0]) // 2
    cv2.putText(out, status_text, (tx, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, status_color, 5)

    if crop_contour is not None:
        out = crop_around_contour(out, crop_contour, crop_size=300)

    return burrs, out

def detect_burr(frame, sorted_contours, ID2_OFFSET=None, HIGHLIGHT_SIZE=None,
                id_BURR_MIN_AREA=None, id_BURR_MAX_AREA=None,
                id_BURR_MIN_PERIMETER=None, id_BURR_MAX_PERIMETER=None,
                min_id_area=None, max_id_area=None,
                min_od_area=None, max_od_area=None,
                min_circularity=None, max_circularity=None,
                min_aspect_ratio=None, max_aspect_ratio=None,
                output_folder="output_images", id_contour=None, od_contour=None):
    """Legacy ID-only detection kept for compatibility."""
    if any(param is None for param in [ID2_OFFSET, HIGHLIGHT_SIZE, id_BURR_MIN_AREA,
                                      id_BURR_MAX_AREA, id_BURR_MIN_PERIMETER, id_BURR_MAX_PERIMETER,
                                      min_id_area, max_id_area, min_od_area, max_od_area]):
        return {
            "burr_count": 0,
            "burr_status": "NOK",
            "time_ms": 0.0,
            "error": "Missing required parameters from software",
            "burr_output_image": None,
            "burr_contours": []
        }

    def get_props(contour):
        if contour is None or len(contour) < 5:
            return None
        area = cv2.contourArea(contour)
        m = cv2.moments(contour)
        if m['m00'] != 0:
            cx = int(m['m10'] / m['m00'])
            cy = int(m['m01'] / m['m00'])
            r = int(np.sqrt(area / np.pi))
        else:
            cx, cy, r = contour[0][0][0], contour[0][0][1], 0
        return {'center': (cx, cy), 'radius': r}

    start = time.time()
    if id_contour is None:
        for c in sorted_contours:
            a = cv2.contourArea(c)
            if min_id_area <= a <= max_id_area and _passes_shape_filters(c, min_circularity, max_circularity, min_aspect_ratio, max_aspect_ratio):
                id_contour = c
                break

    if id_contour is None:
        return {
            "burr_count": 0, "burr_status": "NOK", "time_ms": 0.0,
            "error": "ID contour not found", "burr_output_image": None, "burr_contours": []
        }

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 90, 100)

    props = get_props(id_contour)
    cx, cy = props['center']
    r = props['radius']
    r2 = max(r + ID2_OFFSET, 0)

    id_mask = _filled_mask_from_contour(gray, id_contour)
    id2_mask = np.zeros_like(gray, dtype=np.uint8)
    cv2.circle(id2_mask, (cx, cy), r2, 255, cv2.FILLED)

    burrs, id_img = _analyze_zone(frame, gray, edges,
                                  inner_mask=id_mask, outer_mask=id2_mask,
                                  HIGHLIGHT_SIZE=HIGHLIGHT_SIZE,
                                  burr_area_min=id_BURR_MIN_AREA, burr_area_max=id_BURR_MAX_AREA,
                                  burr_perim_min=id_BURR_MIN_PERIMETER, burr_perim_max=id_BURR_MAX_PERIMETER,
                                  draw_id=id_contour, crop_contour=id_contour)

    elapsed = (time.time() - start) * 1000.0
    return {
        "burr_count": len(burrs),
        "burr_status": "NOK" if burrs else "OK",
        "time_ms": elapsed,
        "burr_output_image": id_img,
        "burr_contours": burrs
    }

def detect_burr_both(frame, sorted_contours,
                     id_offset, id_highlight,
                     id_burr_area_min, id_burr_area_max, id_burr_perim_min, id_burr_perim_max,
                     od_offset, od_highlight,
                     od_burr_area_min, od_burr_area_max, od_burr_perim_min, od_burr_perim_max,
                     min_id_area=None, max_id_area=None,
                     min_od_area=None, max_od_area=None,
                     min_circularity=None, max_circularity=None,
                     min_aspect_ratio=None, max_aspect_ratio=None,
                     output_folder="output_images", id_contour=None, od_contour=None):
    """ID+OD burr detection with combined overlays and union crop."""
    required = [id_offset, id_highlight, id_burr_area_min, id_burr_area_max, id_burr_perim_min, id_burr_perim_max,
                od_offset, od_highlight, od_burr_area_min, od_burr_area_max, od_burr_perim_min, od_burr_perim_max,
                min_id_area, max_id_area, min_od_area, max_od_area]
    if any(v is None for v in required):
        return {
            "id": {"burr_count": 0, "burr_status": "NOK", "time_ms": 0.0, "error": "Missing parameters",
                   "burr_output_image": None, "burr_contours": []},
            "od": {"burr_count": 0, "burr_status": "NOK", "time_ms": 0.0, "error": "Missing parameters",
                   "burr_output_image": None, "burr_contours": []},
            "combined_output_image": None,
            "combined_output_image_id_crop": None,
            "combined_output_image_od_crop": None,
            "combined_output_image_both_crop": None
        }

    start = time.time()
    if id_contour is None:
        for c in sorted_contours:
            a = cv2.contourArea(c)
            if min_id_area <= a <= max_id_area and _passes_shape_filters(c, min_circularity, max_circularity, min_aspect_ratio, max_aspect_ratio):
                id_contour = c
                break
    if od_contour is None:
        for c in sorted_contours:
            a = cv2.contourArea(c)
            if min_od_area <= a <= max_od_area and _passes_shape_filters(c, min_circularity, max_circularity, min_aspect_ratio, max_aspect_ratio):
                od_contour = c
                break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 90, 100)

    # ID outward ring
    id_burrs = []
    id_img = None
    if id_contour is not None:
        m = cv2.moments(id_contour)
        cx = int(m['m10'] / m['m00']) if m['m00'] != 0 else id_contour[0][0][0]
        cy = int(m['m01'] / m['m00']) if m['m00'] != 0 else id_contour[0][0][1]
        r_id = int(np.sqrt(cv2.contourArea(id_contour) / np.pi))
        r_id2 = max(r_id + id_offset, 0)
        id_mask = _filled_mask_from_contour(gray, id_contour)
        id2_mask = np.zeros_like(gray, dtype=np.uint8)
        cv2.circle(id2_mask, (cx, cy), r_id2, 255, cv2.FILLED)
        id_burrs, id_img = _analyze_zone(frame, gray, edges,
                                         inner_mask=id_mask, outer_mask=id2_mask,
                                         HIGHLIGHT_SIZE=id_highlight,
                                         burr_area_min=id_burr_area_min, burr_area_max=id_burr_area_max,
                                         burr_perim_min=id_burr_perim_min, burr_perim_max=id_burr_perim_max,
                                         draw_id=id_contour, draw_od=od_contour, crop_contour=id_contour)

    # OD inward ring
    od_burrs = []
    od_img = None
    if od_contour is not None:
        m = cv2.moments(od_contour)
        cx = int(m['m10'] / m['m00']) if m['m00'] != 0 else od_contour[0][0][0]
        cy = int(m['m01'] / m['m00']) if m['m00'] != 0 else od_contour[0][0][1]
        r_od = int(np.sqrt(cv2.contourArea(od_contour) / np.pi))
        r_od2 = max(r_od - od_offset, 0)
        od_mask = _filled_mask_from_contour(gray, od_contour)
        od2_mask = np.zeros_like(gray, dtype=np.uint8)
        cv2.circle(od2_mask, (cx, cy), r_od2, 255, cv2.FILLED)
        od_burrs, od_img = _analyze_zone(frame, gray, edges,
                                         inner_mask=od2_mask, outer_mask=od_mask,
                                         HIGHLIGHT_SIZE=od_highlight,
                                         burr_area_min=od_burr_area_min, burr_area_max=od_burr_area_max,
                                         burr_perim_min=od_burr_perim_min, burr_perim_max=od_burr_perim_max,
                                         draw_id=id_contour, draw_od=od_contour, crop_contour=od_contour)

    # Combined full-frame overlay with both contours and burr boxes
    combined_full = frame.copy()
    if id_contour is not None:
        cv2.drawContours(combined_full, [id_contour], -1, (0, 255, 0), 4)
    if od_contour is not None:
        cv2.drawContours(combined_full, [od_contour], -1, (0, 255, 0), 4)
    for b in id_burrs:
        x, y, w, h = cv2.boundingRect(b)
        cx2, cy2 = x + w // 2, y + h // 2
        cv2.rectangle(combined_full, (cx2 - id_highlight // 2, cy2 - id_highlight // 2),
                      (cx2 + id_highlight // 2, cy2 + id_highlight // 2), (255, 0, 0), 3)
    for b in od_burrs:
        x, y, w, h = cv2.boundingRect(b)
        cx2, cy2 = x + w // 2, y + h // 2
        cv2.rectangle(combined_full, (cx2 - od_highlight // 2, cy2 - od_highlight // 2),
                      (cx2 + od_highlight // 2, cy2 + od_highlight // 2), (255, 0, 0), 3)
    id_txt = f"ID: {'NOK' if id_burrs else 'OK'} ({len(id_burrs)})"
    od_txt = f"OD: {'NOK' if od_burrs else 'OK'} ({len(od_burrs)})"
    id_color = (0, 0, 255) if id_burrs else (0, 255, 0)
    od_color = (0, 0, 255) if od_burrs else (0, 255, 0)
    cv2.putText(combined_full, id_txt, (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.6, id_color, 4)
    cv2.putText(combined_full, od_txt, (30, 110), cv2.FONT_HERSHEY_SIMPLEX, 1.6, od_color, 4)

    # Build per-target crops and a union crop around both contours
    combined_id_crop = crop_around_contour(combined_full, id_contour, crop_size=300) if id_contour is not None else None
    combined_od_crop = crop_around_contour(combined_full, od_contour, crop_size=300) if od_contour is not None else None
    combined_both_crop = _union_crop(combined_full, [id_contour, od_contour], pad=30)

    elapsed_ms = (time.time() - start) * 1000.0

    return {
        "id": {"burr_count": len(id_burrs), "burr_status": "NOK" if id_burrs else "OK",
               "time_ms": elapsed_ms, "burr_output_image": id_img, "burr_contours": id_burrs},
        "od": {"burr_count": len(od_burrs), "burr_status": "NOK" if od_burrs else "OK",
               "time_ms": elapsed_ms, "burr_output_image": od_img, "burr_contours": od_burrs},
        "combined_output_image": combined_full,
        "combined_output_image_id_crop": combined_id_crop,
        "combined_output_image_od_crop": combined_od_crop,
        "combined_output_image_both_crop": combined_both_crop
    }























# # updated 20_9_2025 (adds circularity/aspect ratio filters into contour selection)
# import cv2
# import numpy as np
# import math
# from datetime import datetime
# import os
# import time

# def _circularity(contour):
#     """4*pi*A/P^2 — returns None if perimeter is zero."""
#     area = cv2.contourArea(contour)
#     perim = cv2.arcLength(contour, True)
#     if perim <= 0:
#         return None, area, perim
#     c = 4.0 * math.pi * area / (perim * perim)
#     return c, area, perim

# def _aspect_ratio(contour):
#     """w/h from boundingRect — returns None if h==0."""
#     x, y, w, h = cv2.boundingRect(contour)
#     if h == 0:
#         return None, (w, h)
#     return float(w) / float(h), (w, h)

# def _passes_shape_filters(contour, min_circularity, max_circularity, min_aspect_ratio, max_aspect_ratio):
#     """Check optional shape constraints; any None disables that constraint."""
#     # Circularity check
#     if min_circularity is not None or max_circularity is not None:
#         c, _, _ = _circularity(contour)
#         if c is None:
#             return False
#         if min_circularity is not None and c < min_circularity:
#             return False
#         if max_circularity is not None and c > max_circularity:
#             return False
#     # Aspect ratio check
#     if min_aspect_ratio is not None or max_aspect_ratio is not None:
#         ar, _ = _aspect_ratio(contour)
#         if ar is None:
#             return False
#         if min_aspect_ratio is not None and ar < min_aspect_ratio:
#             return False
#         if max_aspect_ratio is not None and ar > max_aspect_ratio:
#             return False
#     return True

# def preprocess_image(frame, min_id_area=None, max_id_area=None,
#                      min_od_area=None, max_od_area=None,
#                      min_circularity=None, max_circularity=None,
#                      min_aspect_ratio=None, max_aspect_ratio=None,
#                      output_folder=None):
#     """Preprocessing for burr detection with configurable area and shape filters"""
#     print("DEBUG: Starting preprocessing of image...")
#     if output_folder:
#         os.makedirs(output_folder, exist_ok=True)

#     gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#     _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)
#     binary_inv = cv2.bitwise_not(binary)

#     contours, _ = cv2.findContours(binary_inv, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
#     print(f"DEBUG: Found {len(contours)} contours in image.")

#     sorted_contours = sorted(contours, key=cv2.contourArea, reverse=True)

#     # Select ID contour by area and shape constraints
#     id_contour = None
#     if min_id_area is not None and max_id_area is not None:
#         for i, contour in enumerate(sorted_contours):
#             area = cv2.contourArea(contour)
#             if min_id_area <= area <= max_id_area:
#                 if _passes_shape_filters(contour, min_circularity, max_circularity, min_aspect_ratio, max_aspect_ratio):
#                     id_contour = contour
#                     print(f"DEBUG: ID contour idx={i} area={area} passed shape filters")
#                     break
#         if id_contour is None:
#             print(f"DEBUG: No ID contour matched area+shape: area({min_id_area}-{max_id_area}), "
#                   f"circ({min_circularity}-{max_circularity}), ar({min_aspect_ratio}-{max_aspect_ratio})")

#     # Select OD contour by area and shape constraints
#     od_contour = None
#     if min_od_area is not None and max_od_area is not None:
#         for i, contour in enumerate(sorted_contours):
#             area = cv2.contourArea(contour)
#             if min_od_area <= area <= max_od_area:
#                 if _passes_shape_filters(contour, min_circularity, max_circularity, min_aspect_ratio, max_aspect_ratio):
#                     od_contour = contour
#                     print(f"DEBUG: OD contour idx={i} area={area} passed shape filters")
#                     break
#         if od_contour is None:
#             print(f"DEBUG: No OD contour matched area+shape: area({min_od_area}-{max_od_area}), "
#                   f"circ({min_circularity}-{max_circularity}), ar({min_aspect_ratio}-{max_aspect_ratio})")

#     contour_img = frame.copy()
#     if id_contour is not None:
#         cv2.drawContours(contour_img, [id_contour], -1, (0, 255, 0), 3)
#     if od_contour is not None:
#         cv2.drawContours(contour_img, [od_contour], -1, (0, 255, 0), 3)

#     return {
#         "image": frame.copy(),
#         "sorted_contours": sorted_contours,
#         "original_gray": gray,
#         "id_contour": id_contour,
#         "od_contour": od_contour,
#         "contour_image": contour_img
#     }

# def crop_around_contour(image, contour, crop_size=400):
#     h, w = image.shape[:2]
#     moments = cv2.moments(contour)
#     if moments['m00'] == 0:
#         center = tuple(contour[0][0])
#     else:
#         cx = int(moments['m10'] / moments['m00'])
#         cy = int(moments['m01'] / moments['m00'])
#         center = (cx, cy)
#     x_start = max(center[0] - crop_size, 0)
#     y_start = max(center[1] - crop_size, 0)
#     x_end = min(center[0] + crop_size, w)
#     y_end = min(center[1] + crop_size, h)
#     return image[y_start:y_end, x_start:x_end]

# def detect_burr(frame, sorted_contours, ID2_OFFSET=None, HIGHLIGHT_SIZE=None,
#                 id_BURR_MIN_AREA=None, id_BURR_MAX_AREA=None,
#                 id_BURR_MIN_PERIMETER=None, id_BURR_MAX_PERIMETER=None,
#                 min_id_area=None, max_id_area=None,
#                 min_od_area=None, max_od_area=None,
#                 min_circularity=None, max_circularity=None,
#                 min_aspect_ratio=None, max_aspect_ratio=None,
#                 output_folder="output_images", id_contour=None, od_contour=None):
#     """Burr detection with configurable area + shape filters"""

#     if any(param is None for param in [ID2_OFFSET, HIGHLIGHT_SIZE, id_BURR_MIN_AREA,
#                                       id_BURR_MAX_AREA, id_BURR_MIN_PERIMETER, id_BURR_MAX_PERIMETER,
#                                       min_id_area, max_id_area, min_od_area, max_od_area]):
#         return {
#             "burr_count": 0,
#             "burr_status": "NOK",
#             "time_ms": 0.0,
#             "error": "Missing required parameters from software",
#             "burr_output_image": None,
#             "burr_contours": []
#         }

#     def get_contour_properties(contour):
#         if contour is None or len(contour) < 5:
#             return None
#         props = {
#             'area': cv2.contourArea(contour),
#             'moments': cv2.moments(contour)
#         }
#         if props['moments']['m00'] != 0:
#             props['center'] = (
#                 int(props['moments']['m10'] / props['moments']['m00']),
#                 int(props['moments']['m01'] / props['moments']['m00'])
#             )
#             props['radius'] = int(np.sqrt(props['area'] / np.pi))
#         else:
#             props['center'] = tuple(contour[0][0])
#             props['radius'] = 0
#         return props

#     def analyze_id_zone(image, gray, edges, id_contour, od_contour=None):
#         results = {'burrs': [], 'id_props': None, 'burr_output_image': None}
#         try:
#             results['id_props'] = get_contour_properties(id_contour)
#             if results['id_props'] is None:
#                 return results

#             cx, cy = results['id_props']['center']
#             id_radius = results['id_props']['radius']
#             id2_radius = id_radius + ID2_OFFSET

#             id_mask = np.zeros_like(gray, dtype=np.uint8)
#             cv2.drawContours(id_mask, [id_contour], -1, 255, cv2.FILLED)

#             id2_mask = np.zeros_like(gray, dtype=np.uint8)
#             cv2.circle(id2_mask, (cx, cy), id2_radius, 255, cv2.FILLED)

#             analysis_zone = cv2.subtract(id2_mask, id_mask)
#             zone_edges = cv2.bitwise_and(edges, edges, mask=analysis_zone)
#             edge_contours, _ = cv2.findContours(zone_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

#             for edge in edge_contours:
#                 edge_area = cv2.contourArea(edge)
#                 edge_perim = cv2.arcLength(edge, True)
#                 is_burr = (id_BURR_MIN_AREA <= edge_area <= id_BURR_MAX_AREA and
#                            id_BURR_MIN_PERIMETER <= edge_perim <= id_BURR_MAX_PERIMETER)
#                 if is_burr:
#                     results['burrs'].append(edge)

#             burr_output = image.copy()
#             if id_contour is not None:
#                 cv2.drawContours(burr_output, [id_contour], -1, (0, 255, 0), 4)
#             if od_contour is not None:
#                 cv2.drawContours(burr_output, [od_contour], -1, (0, 255, 0), 4)

#             has_burrs = len(results['burrs']) > 0
#             status_text = "NOK - BURR DETECTED" if has_burrs else "OK - NO BURR"
#             status_color = (0, 0, 255) if has_burrs else (0, 255, 0)

#             if has_burrs:
#                 for burr in results['burrs']:
#                     x, y, w, h = cv2.boundingRect(burr)
#                     cxr = x + w // 2
#                     cyr = y + h // 2
#                     cv2.rectangle(
#                         burr_output,
#                         (cxr - HIGHLIGHT_SIZE // 2, cyr - HIGHLIGHT_SIZE // 2),
#                         (cxr + HIGHLIGHT_SIZE // 2, cyr + HIGHLIGHT_SIZE // 2),
#                         (255, 0, 0), 3
#                     )

#             text_size = cv2.getTextSize(status_text, cv2.FONT_HERSHEY_SIMPLEX, 2, 5)[0]
#             text_x = (burr_output.shape[1] - text_size[0]) // 2
#             cv2.putText(burr_output, status_text, (text_x, 50),
#                         cv2.FONT_HERSHEY_SIMPLEX, 2, status_color, 5)

#             cropped_output = crop_around_contour(burr_output, id_contour, crop_size=300)
#             results['burr_output_image'] = cropped_output

#         except Exception as e:
#             print(f"DEBUG: Exception in analyze_id_zone: {e}")
#             burr_output = image.copy()
#             if id_contour is not None:
#                 cv2.drawContours(burr_output, [id_contour], -1, (0, 255, 0), 4)
#                 burr_output = crop_around_contour(burr_output, id_contour, crop_size=400)
#             if od_contour is not None:
#                 cv2.drawContours(burr_output, [od_contour], -1, (0, 255, 0), 4)
#             results['burr_output_image'] = burr_output

#         return results

#     start_time = time.time()

#     # If preprocessing did not supply contours, select here with area+shape filters
#     if id_contour is None:
#         for i, contour in enumerate(sorted_contours):
#             area = cv2.contourArea(contour)
#             if min_id_area <= area <= max_id_area:
#                 if _passes_shape_filters(contour, min_circularity, max_circularity, min_aspect_ratio, max_aspect_ratio):
#                     id_contour = contour
#                     print(f"DEBUG: (fallback) ID idx={i} area={area} passed shape filters")
#                     break

#     if od_contour is None:
#         for i, contour in enumerate(sorted_contours):
#             area = cv2.contourArea(contour)
#             if min_od_area <= area <= max_od_area:
#                 if _passes_shape_filters(contour, min_circularity, max_circularity, min_aspect_ratio, max_aspect_ratio):
#                     od_contour = contour
#                     print(f"DEBUG: (fallback) OD idx={i} area={area} passed shape filters")
#                     break

#     if id_contour is None:
#         return {
#             "burr_count": 0,
#             "burr_status": "NOK",
#             "time_ms": 0.0,
#             "error": f"ID contour not found (area {min_id_area}-{max_id_area}, "
#                      f"circ {min_circularity}-{max_circularity}, ar {min_aspect_ratio}-{max_aspect_ratio})",
#             "burr_output_image": None,
#             "burr_contours": []
#         }

#     gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#     edges = cv2.Canny(gray, 90, 100)

#     id_results = analyze_id_zone(frame, gray, edges, id_contour, od_contour)
#     execution_time_ms = (time.time() - start_time) * 1000

#     final_results = {
#         "burr_count": len(id_results['burrs']),
#         "burr_status": "NOK" if id_results['burrs'] else "OK",
#         "time_ms": execution_time_ms,
#         "burr_output_image": id_results['burr_output_image'],
#         "burr_contours": id_results['burrs']
#     }

#     return final_results

# def save_burr_result_image(image, burr_data, output_folder="output_images"):
#     try:
#         os.makedirs(output_folder, exist_ok=True)
#         if burr_data.get('burr_output_image') is not None:
#             result_img = burr_data['burr_output_image']
#         else:
#             result_img = image.copy()
#             status_text = f"Burr Status: {burr_data['burr_status']}"
#             status_color = (0, 0, 255) if burr_data['burr_status'] == "NOK" else (0, 255, 0)
#             font = cv2.FONT_HERSHEY_SIMPLEX
#             cv2.putText(result_img, status_text, (50, 50), font, 1.2, status_color, 2)

#         filename = "cam4_bmp.bmp"
#         output_path = os.path.join(output_folder, filename)
#         cv2.imwrite(output_path, result_img)
#         return {"output_path": output_path, "success": True}
#     except Exception as e:
#         return {"output_path": None, "success": False, "error": str(e)}

# def main(part, subpart, frame, ID2_OFFSET, HIGHLIGHT_SIZE, id_BURR_MIN_AREA,
#          id_BURR_MAX_AREA, id_BURR_MIN_PERIMETER, id_BURR_MAX_PERIMETER,
#          min_id_area, max_id_area, min_od_area, max_od_area,
#          min_circularity, max_circularity, min_aspect_ratio, max_aspect_ratio,
#          output_folder):
#     """Optional standalone main with area + shape filters"""
#     try:
#         ID2_OFFSET = int(ID2_OFFSET)
#         HIGHLIGHT_SIZE = int(HIGHLIGHT_SIZE)
#         id_BURR_MIN_AREA = int(id_BURR_MIN_AREA)
#         id_BURR_MAX_AREA = int(id_BURR_MAX_AREA)
#         id_BURR_MIN_PERIMETER = int(id_BURR_MIN_PERIMETER)
#         id_BURR_MAX_PERIMETER = int(id_BURR_MAX_PERIMETER)
#         min_id_area = int(min_id_area)
#         max_id_area = int(max_id_area)
#         min_od_area = int(min_od_area)
#         max_od_area = int(max_od_area)
#         min_circularity = float(min_circularity) if min_circularity != "NA" else None
#         max_circularity = float(max_circularity) if max_circularity != "NA" else None
#         min_aspect_ratio = float(min_aspect_ratio) if min_aspect_ratio != "NA" else None
#         max_aspect_ratio = float(max_aspect_ratio) if max_aspect_ratio != "NA" else None
#     except ValueError as e:
#         return {"error": f"Invalid parameter conversion: {e}"}

#     preprocessing_result = preprocess_image(
#         frame,
#         min_id_area=min_id_area, max_id_area=max_id_area,
#         min_od_area=min_od_area, max_od_area=max_od_area,
#         min_circularity=min_circularity, max_circularity=max_circularity,
#         min_aspect_ratio=min_aspect_ratio, max_aspect_ratio=max_aspect_ratio,
#         output_folder=output_folder
#     )

#     burr_result = detect_burr(
#         frame=frame,
#         sorted_contours=preprocessing_result["sorted_contours"],
#         ID2_OFFSET=ID2_OFFSET,
#         HIGHLIGHT_SIZE=HIGHLIGHT_SIZE,
#         id_BURR_MIN_AREA=id_BURR_MIN_AREA,
#         id_BURR_MAX_AREA=id_BURR_MAX_AREA,
#         id_BURR_MIN_PERIMETER=id_BURR_MIN_PERIMETER,
#         id_BURR_MAX_PERIMETER=id_BURR_MAX_PERIMETER,
#         min_id_area=min_id_area, max_id_area=max_id_area,
#         min_od_area=min_od_area, max_od_area=max_od_area,
#         min_circularity=min_circularity, max_circularity=max_circularity,
#         min_aspect_ratio=min_aspect_ratio, max_aspect_ratio=max_aspect_ratio,
#         output_folder=output_folder,
#         id_contour=preprocessing_result["id_contour"],
#         od_contour=preprocessing_result["od_contour"]
#     )

#     save_result = save_burr_result_image(frame, burr_result, output_folder)

#     return {
#         "part": part,
#         "subpart": subpart,
#         "burr_count": burr_result["burr_count"],
#         "burr_status": burr_result["burr_status"],
#         "processing_time_ms": burr_result["time_ms"],
#         "output_image_path": save_result.get("output_path"),
#         "save_success": save_result["success"]
#     }









# # updated 14_9_2025
# import cv2
# import numpy as np
# import math
# from datetime import datetime
# import os
# import time

# def preprocess_image(frame, min_id_area=None, max_id_area=None, 
#                     min_od_area=None, max_od_area=None, output_folder=None):
#     """Preprocessing function for burr detection with configurable ID/OD contour area parameters"""
#     print("DEBUG: Starting preprocessing of image...")
#     if output_folder:
#         os.makedirs(output_folder, exist_ok=True)
    
#     # Convert BGR image to grayscale for processing
#     gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
#     # Apply binary thresholding - threshold value 80 specifically tuned for burr detection
#     _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)
    
#     # Invert binary image so object pixels become white (255)
#     binary_inv = cv2.bitwise_not(binary)
    
#     # Find contours using RETR_TREE hierarchy and CHAIN_APPROX_SIMPLE compression
#     contours, _ = cv2.findContours(binary_inv, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
#     print(f"DEBUG: Found {len(contours)} contours in image.")
    
#     # Sort contours by area in descending order to prioritize larger objects
#     sorted_contours = sorted(contours, key=cv2.contourArea, reverse=True)
    
#     # Find ID contour based on configurable area range
#     id_contour = None
#     if min_id_area is not None and max_id_area is not None:
#         for i, contour in enumerate(sorted_contours):
#             area = cv2.contourArea(contour)
#             if min_id_area <= area <= max_id_area:
#                 id_contour = contour
#                 print(f"DEBUG: Found ID contour at index {i} with area: {area} pixels")
#                 break
    
#     if id_contour is None:
#         print(f"DEBUG: No ID contour found within specified area range ({min_id_area}-{max_id_area})")
    
#     # Find OD contour based on configurable area range
#     od_contour = None
#     if min_od_area is not None and max_od_area is not None:
#         for i, contour in enumerate(sorted_contours):
#             area = cv2.contourArea(contour)
#             if min_od_area <= area <= max_od_area:
#                 od_contour = contour
#                 print(f"DEBUG: Found OD contour at index {i} with area: {area} pixels")
#                 break
    
#     if od_contour is None:
#         print(f"DEBUG: No OD contour found within specified area range ({min_od_area}-{max_od_area})")
    
#     # Create visualization image with green contours for debugging purposes
#     contour_img = frame.copy()
#     if id_contour is not None:
#         cv2.drawContours(contour_img, [id_contour], -1, (0, 255, 0), 3)  # Green color for ID
#     if od_contour is not None:
#         cv2.drawContours(contour_img, [od_contour], -1, (0, 255, 0), 3)  # Green color for OD
    
#     return {
#         "image": frame.copy(),
#         "sorted_contours": sorted_contours,
#         "original_gray": gray,
#         "id_contour": id_contour,
#         "od_contour": od_contour,
#         "contour_image": contour_img
#     }

# def crop_around_contour(image, contour, crop_size=400):
#     """
#     Crop the image around contour center with specified radius
#     Args:
#         image: Input image to crop
#         contour: Contour to find center of
#         crop_size: Radius in pixels from center (final image will be 2*crop_size x 2*crop_size)
#     Returns:
#         Cropped image
#     """
#     # Get image dimensions
#     h, w = image.shape[:2]
    
#     # Calculate contour center using moments
#     moments = cv2.moments(contour)
#     if moments['m00'] == 0:
#         # Fallback if moments calculation fails
#         center = tuple(contour[0][0])
#     else:
#         cx = int(moments['m10'] / moments['m00'])
#         cy = int(moments['m01'] / moments['m00'])
#         center = (cx, cy)
    
#     # Calculate crop boundaries with safety checks for image edges
#     x_start = max(center[0] - crop_size, 0)
#     y_start = max(center[1] - crop_size, 0)
#     x_end = min(center[0] + crop_size, w)
#     y_end = min(center[1] + crop_size, h)
    
#     # Perform the crop operation
#     cropped_img = image[y_start:y_end, x_start:x_end]
    
#     return cropped_img

# def detect_burr(frame, sorted_contours, ID2_OFFSET=None, HIGHLIGHT_SIZE=None, 
#                 id_BURR_MIN_AREA=None, id_BURR_MAX_AREA=None, 
#                 id_BURR_MIN_PERIMETER=None, id_BURR_MAX_PERIMETER=None,
#                 min_id_area=None, max_id_area=None,
#                 min_od_area=None, max_od_area=None,
#                 output_folder="output_images", id_contour=None, od_contour=None):
#     """Main burr detection function with configurable ID/OD area parameters"""
    
#     # Validate that all required parameters are provided by software
#     if any(param is None for param in [ID2_OFFSET, HIGHLIGHT_SIZE, id_BURR_MIN_AREA, 
#                                       id_BURR_MAX_AREA, id_BURR_MIN_PERIMETER, id_BURR_MAX_PERIMETER,
#                                       min_id_area, max_id_area, min_od_area, max_od_area]):
#         return {
#             "burr_count": 0,
#             "burr_status": "NOK",
#             "time_ms": 0.0,
#             "error": "Missing required parameters from software",
#             "burr_output_image": None,
#             "burr_contours": []
#         }
    
#     def get_contour_properties(contour):
#         """Calculate essential contour properties for burr detection"""
#         if contour is None or len(contour) < 5:
#             return None
        
#         # Calculate area and moments for geometric analysis
#         properties = {
#             'area': cv2.contourArea(contour),
#             'moments': cv2.moments(contour)
#         }
        
#         # Calculate center using image moments (centroid calculation)
#         if properties['moments']['m00'] != 0:
#             properties['center'] = (
#                 int(properties['moments']['m10'] / properties['moments']['m00']),
#                 int(properties['moments']['m01'] / properties['moments']['m00'])
#             )
#             # Calculate radius assuming circular approximation: area = π * r²
#             properties['radius'] = int(np.sqrt(properties['area'] / np.pi))
#         else:
#             # Fallback for zero moment - use first contour point
#             properties['center'] = tuple(contour[0][0])
#             properties['radius'] = 0
        
#         return properties

#     def analyze_id_zone(image, gray, edges, id_contour, od_contour=None):
#         """ID analysis with ID2 ring and burr detection"""
#         results = {
#             'burrs': [],
#             'id_props': None,
#             'burr_output_image': None
#         }
        
#         try:
#             # Get geometric properties of ID contour
#             results['id_props'] = get_contour_properties(id_contour)
#             if results['id_props'] is None:
#                 return results
            
#             cx, cy = results['id_props']['center']
#             id_radius = results['id_props']['radius']
            
#             # Create ID2 ring using software-configurable offset - creates annular analysis zone
#             id2_radius = id_radius + ID2_OFFSET
            
#             # Create analysis masks for geometric region isolation
#             id_mask = np.zeros_like(gray, dtype=np.uint8)
#             cv2.drawContours(id_mask, [id_contour], -1, 255, cv2.FILLED)  # Fill ID contour area
            
#             id2_mask = np.zeros_like(gray, dtype=np.uint8)
#             cv2.circle(id2_mask, (cx, cy), id2_radius, 255, cv2.FILLED)  # Fill ID2 circular area
            
#             # Create annular analysis zone by subtracting ID from ID2
#             analysis_zone = cv2.subtract(id2_mask, id_mask)
            
#             # Edge detection in analysis zone using Canny algorithm
#             zone_edges = cv2.bitwise_and(edges, edges, mask=analysis_zone)
#             edge_contours, _ = cv2.findContours(zone_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            
#             # Analyze each edge contour for burr classification using dual criteria
#             for i, edge in enumerate(edge_contours):
#                 edge_area = cv2.contourArea(edge)
#                 edge_perim = cv2.arcLength(edge, True)
#                 # Dual-parameter filtering: area AND perimeter constraints
#                 is_burr = (id_BURR_MIN_AREA <= edge_area <= id_BURR_MAX_AREA and 
#                           id_BURR_MIN_PERIMETER <= edge_perim <= id_BURR_MAX_PERIMETER)
                
#                 if is_burr:
#                     results['burrs'].append(edge)
            
#             # Create output image with visual overlays
#             burr_output = image.copy()
            
#             # Draw green ID/OD contours on the final output image
#             if id_contour is not None:
#                 cv2.drawContours(burr_output, [id_contour], -1, (0, 255, 0), 4)  # Thick green ID contour
#             if od_contour is not None:
#                 cv2.drawContours(burr_output, [od_contour], -1, (0, 255, 0), 4)  # Thick green OD contour
            
#             has_burrs = len(results['burrs']) > 0
#             status_text = "NOK - BURR DETECTED" if has_burrs else "OK - NO BURR"
#             status_color = (0, 0, 255) if has_burrs else (0, 255, 0)  # Red for NOK, Green for OK
            
#             # Draw blue highlight rectangles around detected burrs
#             if has_burrs:
#                 for burr in results['burrs']:
#                     x, y, w, h = cv2.boundingRect(burr)
#                     center_x = x + w//2
#                     center_y = y + h//2
#                     # Draw blue rectangle centered on burr using software-configurable size
#                     cv2.rectangle(burr_output, 
#                                  (center_x - HIGHLIGHT_SIZE//2, center_y - HIGHLIGHT_SIZE//2),
#                                  (center_x + HIGHLIGHT_SIZE//2, center_y + HIGHLIGHT_SIZE//2),
#                                  (255, 0, 0), 3)  # Blue rectangle
            
#             # Draw status text with centered positioning
#             text_size = cv2.getTextSize(status_text, cv2.FONT_HERSHEY_SIMPLEX, 2, 5)[0]
#             text_x = (burr_output.shape[1] - text_size[0]) // 2
#             cv2.putText(burr_output, status_text, (text_x, 50), 
#                        cv2.FONT_HERSHEY_SIMPLEX, 2, status_color, 5)
            
#             # Crop the output image around ID contour center
#             cropped_output = crop_around_contour(burr_output, id_contour, crop_size=300)
            
#             results['burr_output_image'] = cropped_output
            
#         except Exception as e:
#             print(f"DEBUG: Exception in analyze_id_zone: {e}")
#             # Fallback: Create basic output image with green contours only
#             burr_output = image.copy()
#             if id_contour is not None:
#                 cv2.drawContours(burr_output, [id_contour], -1, (0, 255, 0), 4)
#                 # Apply cropping even in fallback
#                 burr_output = crop_around_contour(burr_output, id_contour, crop_size=400)
#             if od_contour is not None:
#                 cv2.drawContours(burr_output, [od_contour], -1, (0, 255, 0), 4)
#             results['burr_output_image'] = burr_output
        
#         return results

#     # Start performance timing
#     start_time = time.time()
    
#     # Find ID contour based on configurable area criteria if not provided from preprocessing
#     if id_contour is None:
#         for i, contour in enumerate(sorted_contours):
#             area = cv2.contourArea(contour)
#             if min_id_area <= area <= max_id_area:
#                 id_contour = contour
#                 print(f"DEBUG: Found ID contour at index {i} with area: {area}")
#                 break
    
#     # Find OD contour based on configurable area criteria if not provided from preprocessing
#     if od_contour is None:
#         for i, contour in enumerate(sorted_contours):
#             area = cv2.contourArea(contour)
#             if min_od_area <= area <= max_od_area:
#                 od_contour = contour
#                 print(f"DEBUG: Found OD contour at index {i} with area: {area}")
#                 break
    
#     # Abort if no ID contour found - ID is mandatory for burr detection
#     if id_contour is None:
#         return {
#             "burr_count": 0,
#             "burr_status": "NOK",
#             "time_ms": 0.0,
#             "error": f"ID contour not found within specified area range ({min_id_area}-{max_id_area})",
#             "burr_output_image": None,
#             "burr_contours": []
#         }
    
#     # Initial processing for edge detection
#     gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
#     # Canny edge detection with low/high thresholds optimized for burr detection
#     edges = cv2.Canny(gray, 90, 100)
    
#     # Analyze ID zone with both ID and OD contours for comprehensive analysis
#     id_results = analyze_id_zone(frame, gray, edges, id_contour, od_contour)
    
#     # Calculate execution time in milliseconds for performance monitoring
#     execution_time_ms = (time.time() - start_time) * 1000
    
#     # Prepare final results dictionary
#     final_results = {
#         "burr_count": len(id_results['burrs']),
#         "burr_status": "NOK" if id_results['burrs'] else "OK",
#         "time_ms": execution_time_ms,
#         "burr_output_image": id_results['burr_output_image'],
#         "burr_contours": id_results['burrs']
#     }
    
#     return final_results

# def save_burr_result_image(image, burr_data, output_folder="output_images"):
#     """Save burr detection result image with software-compatible format"""
#     try:
#         os.makedirs(output_folder, exist_ok=True)
        
#         # Use the burr output image if available, otherwise create basic output
#         if burr_data.get('burr_output_image') is not None:
#             result_img = burr_data['burr_output_image']
#         else:
#             result_img = image.copy()
#             # Add basic status text if no burr output image available
#             status_text = f"Burr Status: {burr_data['burr_status']}"
#             status_color = (0, 0, 255) if burr_data['burr_status'] == "NOK" else (0, 255, 0)
            
#             font = cv2.FONT_HERSHEY_SIMPLEX
#             cv2.putText(result_img, status_text, (50, 50), font, 1.2, status_color, 2)
        
#         # Save result image with software-compatible filename
#         filename = "cam4_bmp.bmp"
#         output_path = os.path.join(output_folder, filename)
#         cv2.imwrite(output_path, result_img)
        
#         return {"output_path": output_path, "success": True}
#     except Exception as e:
#         return {"output_path": None, "success": False, "error": str(e)}

# def main(part, subpart, frame, ID2_OFFSET, HIGHLIGHT_SIZE, id_BURR_MIN_AREA,
#          id_BURR_MAX_AREA, id_BURR_MIN_PERIMETER, id_BURR_MAX_PERIMETER, 
#          min_id_area, max_id_area, min_od_area, max_od_area, output_folder):
#     """Main function with configurable ID/OD area parameters"""
    
#     # Convert string parameters to integers (as received from production environment)
#     try:
#         ID2_OFFSET = int(ID2_OFFSET)
#         HIGHLIGHT_SIZE = int(HIGHLIGHT_SIZE)
#         id_BURR_MIN_AREA = int(id_BURR_MIN_AREA)
#         id_BURR_MAX_AREA = int(id_BURR_MAX_AREA)
#         id_BURR_MIN_PERIMETER = int(id_BURR_MIN_PERIMETER)
#         id_BURR_MAX_PERIMETER = int(id_BURR_MAX_PERIMETER)
#         min_id_area = int(min_id_area)
#         max_id_area = int(max_id_area)
#         min_od_area = int(min_od_area)
#         max_od_area = int(max_od_area)
#     except ValueError as e:
#         return {"error": f"Invalid parameter conversion: {e}"}
    
#     # Preprocessing with configurable area parameters
#     preprocessing_result = preprocess_image(
#         frame, 
#         min_id_area=min_id_area, 
#         max_id_area=max_id_area,
#         min_od_area=min_od_area, 
#         max_od_area=max_od_area,
#         output_folder=output_folder
#     )
    
#     # Burr detection with all parameters
#     burr_result = detect_burr(
#         frame=frame,
#         sorted_contours=preprocessing_result["sorted_contours"],
#         ID2_OFFSET=ID2_OFFSET,
#         HIGHLIGHT_SIZE=HIGHLIGHT_SIZE,
#         id_BURR_MIN_AREA=id_BURR_MIN_AREA,
#         id_BURR_MAX_AREA=id_BURR_MAX_AREA,
#         id_BURR_MIN_PERIMETER=id_BURR_MIN_PERIMETER,
#         id_BURR_MAX_PERIMETER=id_BURR_MAX_PERIMETER,
#         min_id_area=min_id_area,
#         max_id_area=max_id_area,
#         min_od_area=min_od_area,
#         max_od_area=max_od_area,
#         output_folder=output_folder,
#         id_contour=preprocessing_result["id_contour"],
#         od_contour=preprocessing_result["od_contour"]
#     )
    
#     # Save result image
#     save_result = save_burr_result_image(frame, burr_result, output_folder)
    
#     return {
#         "part": part,
#         "subpart": subpart,
#         "burr_count": burr_result["burr_count"],
#         "burr_status": burr_result["burr_status"],
#         "processing_time_ms": burr_result["time_ms"],
#         "output_image_path": save_result.get("output_path"),
#         "save_success": save_result["success"]
#     }
























# old 13_9_2025

# # python station_4_defect.py



# import cv2
# import numpy as np
# import math
# from datetime import datetime
# import os
# import time

# def preprocess_image(frame, output_folder=None):
#     """Preprocessing function for burr detection with enhanced contour detection"""
#     print("DEBUG: Starting preprocessing of image...")  # Debug: Function entry
#     if output_folder:
#         # print(f"DEBUG: Creating output folder: {output_folder}")  # Debug: Folder creation
#         os.makedirs(output_folder, exist_ok=True)
    
#     # Convert BGR image to grayscale for processing
#     gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#     # print("DEBUG: Converted image to grayscale.")  # Debug: Grayscale conversion
    
#     # Apply binary thresholding - threshold value 80 specifically tuned for burr detection
#     _, binary = cv2.threshold(gray, 80, 255, cv2.THRESH_BINARY)
#     # print("DEBUG: Applied binary thresholding with threshold=80.")  # Debug: Thresholding
    
#     # Invert binary image so object pixels become white (255)
#     binary_inv = cv2.bitwise_not(binary)
#     # print("DEBUG: Inverted binary image.")  # Debug: Image inversion
    
#     # Find contours using RETR_TREE hierarchy and CHAIN_APPROX_SIMPLE compression
#     contours, _ = cv2.findContours(binary_inv, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
#     # print(f"DEBUG: Found {len(contours)} contours in image.")  # Debug: Contour detection
    
#     # Sort contours by area in descending order to prioritize larger objects
#     sorted_contours = sorted(contours, key=cv2.contourArea, reverse=True)
#     # print("DEBUG: Sorted contours by area in descending order.")  # Debug: Contour sorting
    
#     # Find ID contour based on area range (10000-25000 pixels) - area-based geometric selection
#     id_contour = None
#     for i, contour in enumerate(sorted_contours):
#         area = cv2.contourArea(contour)
#         if 12500 <= area <= 16500:
#             id_contour = contour
#             print(f"DEBUG: Found ID contour at index {i} with area: {area} pixels")  # Debug: ID contour found
#             break
    
#     if id_contour is None:
#         print("DEBUG: No ID contour found within specified area range (10000-25000)")  # Debug: ID contour not found
    
#     # Find OD contour based on area range (85000-140000 pixels) - area-based geometric selection
#     od_contour = None
#     for i, contour in enumerate(sorted_contours):
#         area = cv2.contourArea(contour)
#         if 108000 <= area <= 120000:
#             od_contour = contour
#             print(f"DEBUG: Found OD contour at index {i} with area: {area} pixels")  # Debug: OD contour found
#             break
    
#     if od_contour is None:
#         print("DEBUG: No OD contour found within specified area range (85000-140000)")  # Debug: OD contour not found
    
#     # Create visualization image with green contours for debugging purposes
#     contour_img = frame.copy()
#     if id_contour is not None:
#         cv2.drawContours(contour_img, [id_contour], -1, (0, 255, 0), 3)  # Green color for ID
#         # print("DEBUG: ID contour drawn on contour image in green.")  # Debug: ID contour visualization
#     if od_contour is not None:
#         cv2.drawContours(contour_img, [od_contour], -1, (0, 255, 0), 3)  # Green color for OD
#         # print("DEBUG: OD contour drawn on contour image in green.")  # Debug: OD contour visualization
    
#     # print("DEBUG: Preprocessing completed successfully.")  # Debug: Function completion
#     return {
#         "image": frame.copy(),
#         "sorted_contours": sorted_contours,
#         "original_gray": gray,
#         "id_contour": id_contour,
#         "od_contour": od_contour,
#         "contour_image": contour_img
#     }

# def crop_around_contour(image, contour, crop_size=400):
#     """
#     Crop the image around contour center with specified radius
#     Args:
#         image: Input image to crop
#         contour: Contour to find center of
#         crop_size: Radius in pixels from center (final image will be 2*crop_size x 2*crop_size)
#     Returns:
#         Cropped image
#     """
#     # print(f"DEBUG: Starting crop operation with crop_size={crop_size}")  # Debug: Crop start
    
#     # Get image dimensions
#     h, w = image.shape[:2]
#     # print(f"DEBUG: Original image dimensions: {w}x{h}")  # Debug: Original dimensions
    
#     # Calculate contour center using moments
#     moments = cv2.moments(contour)
#     if moments['m00'] == 0:
#         # Fallback if moments calculation fails
#         center = tuple(contour[0][0])
#         # print("DEBUG: Using fallback center calculation (first contour point)")  # Debug: Fallback center
#     else:
#         cx = int(moments['m10'] / moments['m00'])
#         cy = int(moments['m01'] / moments['m00'])
#         center = (cx, cy)
#         # print(f"DEBUG: Calculated contour center using moments: ({cx}, {cy})")  # Debug: Center calculation
    
#     # Calculate crop boundaries with safety checks for image edges
#     x_start = max(center[0] - crop_size, 0)
#     y_start = max(center[1] - crop_size, 0)
#     x_end = min(center[0] + crop_size, w)
#     y_end = min(center[1] + crop_size, h)
    
#     # print(f"DEBUG: Crop boundaries - x: {x_start}-{x_end}, y: {y_start}-{y_end}")  # Debug: Crop boundaries
    
#     # Perform the crop operation
#     cropped_img = image[y_start:y_end, x_start:x_end]
    
#     # Get cropped dimensions
#     crop_h, crop_w = cropped_img.shape[:2]
#     # print(f"DEBUG: Cropped image dimensions: {crop_w}x{crop_h}")  # Debug: Cropped dimensions
    
#     return cropped_img

# def detect_burr(frame, sorted_contours, ID2_OFFSET=None, HIGHLIGHT_SIZE=None, 
#                 id_BURR_MIN_AREA=None, id_BURR_MAX_AREA=None, 
#                 id_BURR_MIN_PERIMETER=None, id_BURR_MAX_PERIMETER=None,
#                 output_folder="output_images", id_contour=None, od_contour=None):
#     """Main burr detection function using ID contour analysis with software-configurable parameters"""
    
#     # print("DEBUG: Starting burr detection algorithm...")  # Debug: Function entry
#     # print(f"DEBUG: Parameters - ID2_OFFSET: {ID2_OFFSET}, HIGHLIGHT_SIZE: {HIGHLIGHT_SIZE}")  # Debug: Parameter values
#     # print(f"DEBUG: Burr criteria - Area: {id_BURR_MIN_AREA}-{id_BURR_MAX_AREA}, Perimeter: {id_BURR_MIN_PERIMETER}-{id_BURR_MAX_PERIMETER}")  # Debug: Detection criteria
    
#     # Validate that all required parameters are provided by software
#     if any(param is None for param in [ID2_OFFSET, HIGHLIGHT_SIZE, id_BURR_MIN_AREA, 
#                                       id_BURR_MAX_AREA, id_BURR_MIN_PERIMETER, id_BURR_MAX_PERIMETER]):
#         # print("DEBUG: Missing parameters for burr detection. Exiting with error.")  # Debug: Parameter validation failure
#         return {
#             "burr_count": 0,
#             "burr_status": "NOK",
#             "time_ms": 0.0,
#             "error": "Missing required parameters from software",
#             "burr_output_image": None,
#             "burr_contours": []
#         }
    
#     def get_contour_properties(contour):
#         """Calculate essential contour properties for burr detection"""
#         # print("DEBUG: Calculating contour properties...")  # Debug: Property calculation start
#         if contour is None or len(contour) < 5:
#             # print("DEBUG: Contour is None or has insufficient points (<5).")  # Debug: Invalid contour
#             return None
        
#         # Calculate area and moments for geometric analysis
#         properties = {
#             'area': cv2.contourArea(contour),
#             'moments': cv2.moments(contour)
#         }
        
#         # Calculate center using image moments (centroid calculation)
#         if properties['moments']['m00'] != 0:
#             properties['center'] = (
#                 int(properties['moments']['m10'] / properties['moments']['m00']),
#                 int(properties['moments']['m01'] / properties['moments']['m00'])
#             )
#             # Calculate radius assuming circular approximation: area = π * r²
#             properties['radius'] = int(np.sqrt(properties['area'] / np.pi))
#         else:
#             # Fallback for zero moment - use first contour point
#             properties['center'] = tuple(contour[0][0])
#             properties['radius'] = 0
        
#         # print(f"DEBUG: Contour properties - Area: {properties['area']}, Center: {properties['center']}, Radius: {properties['radius']}")  # Debug: Property values
#         return properties

#     def analyze_id_zone(image, gray, edges, id_contour, od_contour=None):
#         """ID analysis with ID2 ring and burr detection"""
#         # print("DEBUG: Analyzing ID zone for burr detection...")  # Debug: Zone analysis start
#         results = {
#             'burrs': [],
#             'id_props': None,
#             'burr_output_image': None
#         }
        
#         try:
#             # Get geometric properties of ID contour
#             results['id_props'] = get_contour_properties(id_contour)
#             if results['id_props'] is None:
#                 # print("DEBUG: ID contour properties could not be calculated.")  # Debug: Property calculation failure
#                 return results
            
#             cx, cy = results['id_props']['center']
#             id_radius = results['id_props']['radius']
#             # print(f"DEBUG: ID contour center: ({cx}, {cy}), radius: {id_radius}")  # Debug: ID geometry
            
#             # Create ID2 ring using software-configurable offset - creates annular analysis zone
#             id2_radius = id_radius + ID2_OFFSET
#             # print(f"DEBUG: ID2 ring radius: {id2_radius} (ID radius + offset {ID2_OFFSET})")  # Debug: ID2 geometry
            
#             # Create analysis masks for geometric region isolation
#             id_mask = np.zeros_like(gray, dtype=np.uint8)
#             cv2.drawContours(id_mask, [id_contour], -1, 255, cv2.FILLED)  # Fill ID contour area
            
#             id2_mask = np.zeros_like(gray, dtype=np.uint8)
#             cv2.circle(id2_mask, (cx, cy), id2_radius, 255, cv2.FILLED)  # Fill ID2 circular area
            
#             # Create annular analysis zone by subtracting ID from ID2
#             analysis_zone = cv2.subtract(id2_mask, id_mask)
#             # print("DEBUG: Created annular analysis zone between ID and ID2 rings.")  # Debug: Zone creation
            
#             # Edge detection in analysis zone using Canny algorithm
#             zone_edges = cv2.bitwise_and(edges, edges, mask=analysis_zone)
#             edge_contours, _ = cv2.findContours(zone_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
#             # print(f"DEBUG: Found {len(edge_contours)} edge contours in analysis zone.")  # Debug: Edge detection results
            
#             # Analyze each edge contour for burr classification using dual criteria
#             for i, edge in enumerate(edge_contours):
#                 edge_area = cv2.contourArea(edge)
#                 edge_perim = cv2.arcLength(edge, True)
#                 # Dual-parameter filtering: area AND perimeter constraints
#                 is_burr = (id_BURR_MIN_AREA <= edge_area <= id_BURR_MAX_AREA and 
#                           id_BURR_MIN_PERIMETER <= edge_perim <= id_BURR_MAX_PERIMETER)
#                 # print(f"DEBUG: Contour {i}: area={edge_area}, perimeter={edge_perim:.1f}, is_burr={is_burr}")  # Debug: Contour analysis
                
#                 if is_burr:
#                     results['burrs'].append(edge)
#                     # print(f"DEBUG: Contour {i} classified as BURR")  # Debug: Burr classification
            
#             # Create output image with visual overlays
#             burr_output = image.copy()
            
#             # *** CRITICAL: Draw green ID/OD contours on the final output image ***
#             if id_contour is not None:
#                 cv2.drawContours(burr_output, [id_contour], -1, (0, 255, 0), 4)  # Thick green ID contour
#                 # print("DEBUG: Drawn green ID contour on output image (thickness=4).")  # Debug: ID contour visualization
#             if od_contour is not None:
#                 cv2.drawContours(burr_output, [od_contour], -1, (0, 255, 0), 4)  # Thick green OD contour
#                 # print("DEBUG: Drawn green OD contour on output image (thickness=4).")  # Debug: OD contour visualization
            
#             has_burrs = len(results['burrs']) > 0
#             status_text = "NOK - BURR DETECTED" if has_burrs else "OK - NO BURR"
#             status_color = (0, 0, 255) if has_burrs else (0, 255, 0)  # Red for NOK, Green for OK
#             # print(f"DEBUG: Burr detection status: {status_text}")  # Debug: Detection status
            
#             # Draw blue highlight rectangles around detected burrs
#             if has_burrs:
#                 for burr in results['burrs']:
#                     x, y, w, h = cv2.boundingRect(burr)
#                     center_x = x + w//2
#                     center_y = y + h//2
#                     # Draw blue rectangle centered on burr using software-configurable size
#                     cv2.rectangle(burr_output, 
#                                  (center_x - HIGHLIGHT_SIZE//2, center_y - HIGHLIGHT_SIZE//2),
#                                  (center_x + HIGHLIGHT_SIZE//2, center_y + HIGHLIGHT_SIZE//2),
#                                  (255, 0, 0), 3)  # Blue rectangle
#                     # print(f"DEBUG: Drawn blue highlight rectangle for burr at center ({center_x}, {center_y}).")  # Debug: Burr highlighting
            
#             # Draw status text with centered positioning
#             text_size = cv2.getTextSize(status_text, cv2.FONT_HERSHEY_SIMPLEX, 2, 5)[0]
#             text_x = (burr_output.shape[1] - text_size[0]) // 2
#             cv2.putText(burr_output, status_text, (text_x, 50), 
#                        cv2.FONT_HERSHEY_SIMPLEX, 2, status_color, 5)
#             # print(f"DEBUG: Drawn status text: '{status_text}' at position ({text_x}, 50)")  # Debug: Text overlay
            
#             # *** NEW: Crop the output image around ID contour center ***
#             cropped_output = crop_around_contour(burr_output, id_contour, crop_size=300)
#             # print("DEBUG: Applied cropping to output image around ID contour center (400px radius)")  # Debug: Cropping applied
            
#             results['burr_output_image'] = cropped_output
#             # print("DEBUG: Created cropped burr output image with all overlays.")  # Debug: Output image creation
            
#         except Exception as e:
#             print(f"DEBUG: Exception in analyze_id_zone: {e}")  # Debug: Exception handling
#             # Fallback: Create basic output image with green contours only
#             burr_output = image.copy()
#             if id_contour is not None:
#                 cv2.drawContours(burr_output, [id_contour], -1, (0, 255, 0), 4)
#                 # Apply cropping even in fallback
#                 burr_output = crop_around_contour(burr_output, id_contour, crop_size=400)
#             if od_contour is not None:
#                 cv2.drawContours(burr_output, [od_contour], -1, (0, 255, 0), 4)
#             results['burr_output_image'] = burr_output
#             # print("DEBUG: Created fallback cropped output image with green contours only.")  # Debug: Fallback creation
        
#         return results

#     # Start performance timing
#     start_time = time.time()
    
#     # Find ID contour based on area criteria if not provided from preprocessing
#     if id_contour is None:
#         # print("DEBUG: ID contour not provided, searching in contours based on area range (3000-25000).")  # Debug: ID search
#         for i, contour in enumerate(sorted_contours):
#             area = cv2.contourArea(contour)
#             if 12500 <= area <= 16500:
#                 id_contour = contour
#                 print(f"DEBUG: Found ID contour at index {i} with area: {area}")  # Debug: ID found
#                 break
    
#     # Find OD contour based on area criteria if not provided from preprocessing
#     if od_contour is None:
#         # print("DEBUG: OD contour not provided, searching in contours based on area range (85000-100000).")  # Debug: OD search
#         for i, contour in enumerate(sorted_contours):
#             area = cv2.contourArea(contour)
#             if 108000 <= area <= 120000:
#                 od_contour = contour
#                 print(f"DEBUG: Found OD contour at index {i} with area: {area}")  # Debug: OD found
#                 break
    
#     # Abort if no ID contour found - ID is mandatory for burr detection
#     if id_contour is None:
#         # print("DEBUG: ID contour not found in contour list - aborting burr detection.")  # Debug: ID not found error
#         return {
#             "burr_count": 0,
#             "burr_status": "NOK",
#             "time_ms": 0.0,
#             "error": "ID contour not found within specified area range",
#             "burr_output_image": None,
#             "burr_contours": []
#         }
    
#     # Initial processing for edge detection
#     gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#     # print("DEBUG: Converted frame to grayscale for edge detection.")  # Debug: Grayscale conversion
    
#     # Canny edge detection with low/high thresholds optimized for burr detection
#     edges = cv2.Canny(gray, 90, 100)
#     # print("DEBUG: Performed Canny edge detection (thresholds: 90, 100).")  # Debug: Edge detection
    
#     # Analyze ID zone with both ID and OD contours for comprehensive analysis
#     id_results = analyze_id_zone(frame, gray, edges, id_contour, od_contour)
    
#     # Calculate execution time in milliseconds for performance monitoring
#     execution_time_ms = (time.time() - start_time) * 1000
#     # print(f"DEBUG: Burr detection completed in {execution_time_ms:.2f} ms.")  # Debug: Performance metric
    
#     # Prepare final results dictionary
#     final_results = {
#         "burr_count": len(id_results['burrs']),
#         "burr_status": "NOK" if id_results['burrs'] else "OK",
#         "time_ms": execution_time_ms,
#         "burr_output_image": id_results['burr_output_image'],
#         "burr_contours": id_results['burrs']
#     }
    
#     # print(f"DEBUG: Final results - Burr count: {final_results['burr_count']}, Status: {final_results['burr_status']}")  # Debug: Final results
#     return final_results

# def save_burr_result_image(image, burr_data, output_folder="output_images"):
#     """Save burr detection result image with software-compatible format"""
#     try:
#         # print(f"DEBUG: Saving result image to folder: {output_folder}")  # Debug: Save operation start
#         os.makedirs(output_folder, exist_ok=True)
        
#         # Use the burr output image if available, otherwise create basic output
#         if burr_data.get('burr_output_image') is not None:
#             result_img = burr_data['burr_output_image']
#             # print("DEBUG: Using cropped burr output image for saving.")  # Debug: Using processed image
#         else:
#             result_img = image.copy()
#             # Add basic status text if no burr output image available
#             status_text = f"Burr Status: {burr_data['burr_status']}"
#             status_color = (0, 0, 255) if burr_data['burr_status'] == "NOK" else (0, 255, 0)
            
#             font = cv2.FONT_HERSHEY_SIMPLEX
#             cv2.putText(result_img, status_text, (50, 50), font, 1.2, status_color, 2)
#             # print("DEBUG: Created basic output image with status text.")  # Debug: Basic image creation
        
#         # Save result image with software-compatible filename
#         filename = "cam4_bmp.bmp"
#         output_path = os.path.join(output_folder, filename)
#         cv2.imwrite(output_path, result_img)
#         # print(f"DEBUG: Successfully saved cropped result image to: {output_path}")  # Debug: Save success
        
#         return {"output_path": output_path, "success": True}
#     except Exception as e:
#         # print(f"DEBUG: Error saving result image: {e}")  # Debug: Save error
#         return {"output_path": None, "success": False, "error": str(e)}
