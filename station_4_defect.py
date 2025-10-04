


### working 3 oct 25

# updated 03_10_2025 (fixes OD keyword bug; consistent guards; preserves behavior)
import cv2
import numpy as np
import math
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
    # Keep original fixed threshold for compatibility
    _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)
    binary_inv = cv2.bitwise_not(binary)

    contours, _ = cv2.findContours(binary_inv, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    sorted_contours = sorted(contours, key=cv2.contourArea, reverse=True)

    id_contour = None
    if min_id_area is not None and max_id_area is not None:
        for contour in sorted_contours:
            area = cv2.contourArea(contour)
            if min_id_area <= area <= max_id_area:
                if _passes_shape_filters(contour, min_circularity, max_circularity, min_aspect_ratio, max_aspect_ratio):
                    id_contour = contour
                    break

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
    # Do NOT require OD area params for ID-only flow
    if any(param is None for param in [
        ID2_OFFSET, HIGHLIGHT_SIZE, id_BURR_MIN_AREA, id_BURR_MAX_AREA,
        id_BURR_MIN_PERIMETER, id_BURR_MAX_PERIMETER,
        min_id_area, max_id_area
    ]):
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
        # FIXED: correct keyword name burr_area_max (was od_burr_area_max)
        od_burrs, od_img = _analyze_zone(frame, gray, edges,
                                         inner_mask=od2_mask, outer_mask=od_mask,
                                         HIGHLIGHT_SIZE=od_highlight,
                                         burr_area_min=od_burr_area_min, burr_area_max=od_burr_area_max,
                                         burr_perim_min=od_burr_perim_min, burr_perim_max=od_burr_perim_max,
                                         draw_id=id_contour, draw_od=od_contour, crop_contour=od_contour)

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
























# # ###working 3 oct 25

# # code 3

# # updated 20_9_2025 (adds circularity/aspect ratio filters into contour selection)
# # updated 23_9_2025 (adds detect_burr_both and union-cropped combined overlay for cam3_bmp)
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
#     if min_circularity is not None or max_circularity is not None:
#         c, _, _ = _circularity(contour)
#         if c is None:
#             return False
#         if min_circularity is not None and c < min_circularity:
#             return False
#         if max_circularity is not None and c > max_circularity:
#             return False
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
#     """Preprocessing with area + shape filters to select ID/OD contours."""
#     if output_folder:
#         os.makedirs(output_folder, exist_ok=True)

#     gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#     _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)
#     binary_inv = cv2.bitwise_not(binary)

#     contours, _ = cv2.findContours(binary_inv, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
#     sorted_contours = sorted(contours, key=cv2.contourArea, reverse=True)

#     # Select ID contour
#     id_contour = None
#     if min_id_area is not None and max_id_area is not None:
#         for contour in sorted_contours:
#             area = cv2.contourArea(contour)
#             if min_id_area <= area <= max_id_area:
#                 if _passes_shape_filters(contour, min_circularity, max_circularity, min_aspect_ratio, max_aspect_ratio):
#                     id_contour = contour
#                     break

#     # Select OD contour
#     od_contour = None
#     if min_od_area is not None and max_od_area is not None:
#         for contour in sorted_contours:
#             area = cv2.contourArea(contour)
#             if min_od_area <= area <= max_od_area:
#                 if _passes_shape_filters(contour, min_circularity, max_circularity, min_aspect_ratio, max_aspect_ratio):
#                     od_contour = contour
#                     break

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
#     """Square crop around a contour centroid with clamped bounds."""
#     h, w = image.shape[:2]
#     m = cv2.moments(contour)
#     if m['m00'] == 0:
#         center = tuple(contour[0][0])
#     else:
#         cx = int(m['m10'] / m['m00'])
#         cy = int(m['m01'] / m['m00'])
#         center = (cx, cy)
#     x_start = max(center[0] - crop_size, 0)
#     y_start = max(center[1] - crop_size, 0)
#     x_end = min(center[0] + crop_size, w)
#     y_end = min(center[1] + crop_size, h)
#     return image[y_start:y_end, x_start:x_end]

# def _union_crop(image, contours, pad=30):
#     """Tight union crop around multiple contours with padding."""
#     pts_list = []
#     for c in contours:
#         if c is not None and len(c) > 0:
#             pts_list.append(c.reshape(-1, 2))
#     if not pts_list:
#         return image
#     pts = np.vstack(pts_list)
#     x, y, w0, h0 = cv2.boundingRect(pts)
#     x0 = max(x - pad, 0)
#     y0 = max(y - pad, 0)
#     x1 = min(x + w0 + pad, image.shape[1])
#     y1 = min(y + h0 + pad, image.shape[0])
#     return image[y0:y1, x0:x1]

# def _filled_mask_from_contour(gray, contour):
#     mask = np.zeros_like(gray, dtype=np.uint8)
#     cv2.drawContours(mask, [contour], -1, 255, cv2.FILLED)
#     return mask

# def _analyze_zone(image, gray, edges, inner_mask, outer_mask,
#                   HIGHLIGHT_SIZE, burr_area_min, burr_area_max, burr_perim_min, burr_perim_max,
#                   draw_id=None, draw_od=None, crop_contour=None):
#     """Edge-in-ring analysis with area/perimeter burr filtering and visualization."""
#     analysis_zone = cv2.subtract(outer_mask, inner_mask)
#     zone_edges = cv2.bitwise_and(edges, edges, mask=analysis_zone)
#     edge_contours, _ = cv2.findContours(zone_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

#     burrs = []
#     for e in edge_contours:
#         ea = cv2.contourArea(e)
#         ep = cv2.arcLength(e, True)
#         if (burr_area_min <= ea <= burr_area_max) and (burr_perim_min <= ep <= burr_perim_max):
#             burrs.append(e)

#     out = image.copy()
#     if draw_id is not None:
#         cv2.drawContours(out, [draw_id], -1, (0, 255, 0), 4)
#     if draw_od is not None:
#         cv2.drawContours(out, [draw_od], -1, (0, 255, 0), 4)

#     for b in burrs:
#         x, y, w, h = cv2.boundingRect(b)
#         cx2, cy2 = x + w // 2, y + h // 2
#         cv2.rectangle(out,
#                       (cx2 - HIGHLIGHT_SIZE // 2, cy2 - HIGHLIGHT_SIZE // 2),
#                       (cx2 + HIGHLIGHT_SIZE // 2, cy2 + HIGHLIGHT_SIZE // 2),
#                       (255, 0, 0), 3)

#     status_text = "NOK - BURR DETECTED" if burrs else "OK - NO BURR"
#     status_color = (0, 0, 255) if burrs else (0, 255, 0)
#     tsize = cv2.getTextSize(status_text, cv2.FONT_HERSHEY_SIMPLEX, 2, 5)[0]
#     tx = (out.shape[1] - tsize[0]) // 2
#     cv2.putText(out, status_text, (tx, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, status_color, 5)

#     if crop_contour is not None:
#         out = crop_around_contour(out, crop_contour, crop_size=300)

#     return burrs, out

# def detect_burr(frame, sorted_contours, ID2_OFFSET=None, HIGHLIGHT_SIZE=None,
#                 id_BURR_MIN_AREA=None, id_BURR_MAX_AREA=None,
#                 id_BURR_MIN_PERIMETER=None, id_BURR_MAX_PERIMETER=None,
#                 min_id_area=None, max_id_area=None,
#                 min_od_area=None, max_od_area=None,
#                 min_circularity=None, max_circularity=None,
#                 min_aspect_ratio=None, max_aspect_ratio=None,
#                 output_folder="output_images", id_contour=None, od_contour=None):
#     """Legacy ID-only detection kept for compatibility."""
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

#     def get_props(contour):
#         if contour is None or len(contour) < 5:
#             return None
#         area = cv2.contourArea(contour)
#         m = cv2.moments(contour)
#         if m['m00'] != 0:
#             cx = int(m['m10'] / m['m00'])
#             cy = int(m['m01'] / m['m00'])
#             r = int(np.sqrt(area / np.pi))
#         else:
#             cx, cy, r = contour[0][0][0], contour[0][0][1], 0
#         return {'center': (cx, cy), 'radius': r}

#     start = time.time()
#     if id_contour is None:
#         for c in sorted_contours:
#             a = cv2.contourArea(c)
#             if min_id_area <= a <= max_id_area and _passes_shape_filters(c, min_circularity, max_circularity, min_aspect_ratio, max_aspect_ratio):
#                 id_contour = c
#                 break

#     if id_contour is None:
#         return {
#             "burr_count": 0, "burr_status": "NOK", "time_ms": 0.0,
#             "error": "ID contour not found", "burr_output_image": None, "burr_contours": []
#         }

#     gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#     edges = cv2.Canny(gray, 90, 100)

#     props = get_props(id_contour)
#     cx, cy = props['center']
#     r = props['radius']
#     r2 = max(r + ID2_OFFSET, 0)

#     id_mask = _filled_mask_from_contour(gray, id_contour)
#     id2_mask = np.zeros_like(gray, dtype=np.uint8)
#     cv2.circle(id2_mask, (cx, cy), r2, 255, cv2.FILLED)

#     burrs, id_img = _analyze_zone(frame, gray, edges,
#                                   inner_mask=id_mask, outer_mask=id2_mask,
#                                   HIGHLIGHT_SIZE=HIGHLIGHT_SIZE,
#                                   burr_area_min=id_BURR_MIN_AREA, burr_area_max=id_BURR_MAX_AREA,
#                                   burr_perim_min=id_BURR_MIN_PERIMETER, burr_perim_max=id_BURR_MAX_PERIMETER,
#                                   draw_id=id_contour, crop_contour=id_contour)

#     elapsed = (time.time() - start) * 1000.0
#     return {
#         "burr_count": len(burrs),
#         "burr_status": "NOK" if burrs else "OK",
#         "time_ms": elapsed,
#         "burr_output_image": id_img,
#         "burr_contours": burrs
#     }

# def detect_burr_both(frame, sorted_contours,
#                      id_offset, id_highlight,
#                      id_burr_area_min, id_burr_area_max, id_burr_perim_min, id_burr_perim_max,
#                      od_offset, od_highlight,
#                      od_burr_area_min, od_burr_area_max, od_burr_perim_min, od_burr_perim_max,
#                      min_id_area=None, max_id_area=None,
#                      min_od_area=None, max_od_area=None,
#                      min_circularity=None, max_circularity=None,
#                      min_aspect_ratio=None, max_aspect_ratio=None,
#                      output_folder="output_images", id_contour=None, od_contour=None):
#     """ID+OD burr detection with combined overlays and union crop."""
#     required = [id_offset, id_highlight, id_burr_area_min, id_burr_area_max, id_burr_perim_min, id_burr_perim_max,
#                 od_offset, od_highlight, od_burr_area_min, od_burr_area_max, od_burr_perim_min, od_burr_perim_max,
#                 min_id_area, max_id_area, min_od_area, max_od_area]
#     if any(v is None for v in required):
#         return {
#             "id": {"burr_count": 0, "burr_status": "NOK", "time_ms": 0.0, "error": "Missing parameters",
#                    "burr_output_image": None, "burr_contours": []},
#             "od": {"burr_count": 0, "burr_status": "NOK", "time_ms": 0.0, "error": "Missing parameters",
#                    "burr_output_image": None, "burr_contours": []},
#             "combined_output_image": None,
#             "combined_output_image_id_crop": None,
#             "combined_output_image_od_crop": None,
#             "combined_output_image_both_crop": None
#         }

#     start = time.time()
#     if id_contour is None:
#         for c in sorted_contours:
#             a = cv2.contourArea(c)
#             if min_id_area <= a <= max_id_area and _passes_shape_filters(c, min_circularity, max_circularity, min_aspect_ratio, max_aspect_ratio):
#                 id_contour = c
#                 break
#     if od_contour is None:
#         for c in sorted_contours:
#             a = cv2.contourArea(c)
#             if min_od_area <= a <= max_od_area and _passes_shape_filters(c, min_circularity, max_circularity, min_aspect_ratio, max_aspect_ratio):
#                 od_contour = c
#                 break

#     gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#     edges = cv2.Canny(gray, 90, 100)

#     # ID outward ring
#     id_burrs = []
#     id_img = None
#     if id_contour is not None:
#         m = cv2.moments(id_contour)
#         cx = int(m['m10'] / m['m00']) if m['m00'] != 0 else id_contour[0][0][0]
#         cy = int(m['m01'] / m['m00']) if m['m00'] != 0 else id_contour[0][0][1]
#         r_id = int(np.sqrt(cv2.contourArea(id_contour) / np.pi))
#         r_id2 = max(r_id + id_offset, 0)
#         id_mask = _filled_mask_from_contour(gray, id_contour)
#         id2_mask = np.zeros_like(gray, dtype=np.uint8)
#         cv2.circle(id2_mask, (cx, cy), r_id2, 255, cv2.FILLED)
#         id_burrs, id_img = _analyze_zone(frame, gray, edges,
#                                          inner_mask=id_mask, outer_mask=id2_mask,
#                                          HIGHLIGHT_SIZE=id_highlight,
#                                          burr_area_min=id_burr_area_min, burr_area_max=id_burr_area_max,
#                                          burr_perim_min=id_burr_perim_min, burr_perim_max=id_burr_perim_max,
#                                          draw_id=id_contour, draw_od=od_contour, crop_contour=id_contour)

#     # OD inward ring
#     od_burrs = []
#     od_img = None
#     if od_contour is not None:
#         m = cv2.moments(od_contour)
#         cx = int(m['m10'] / m['m00']) if m['m00'] != 0 else od_contour[0][0][0]
#         cy = int(m['m01'] / m['m00']) if m['m00'] != 0 else od_contour[0][0][1]
#         r_od = int(np.sqrt(cv2.contourArea(od_contour) / np.pi))
#         r_od2 = max(r_od - od_offset, 0)
#         od_mask = _filled_mask_from_contour(gray, od_contour)
#         od2_mask = np.zeros_like(gray, dtype=np.uint8)
#         cv2.circle(od2_mask, (cx, cy), r_od2, 255, cv2.FILLED)
#         od_burrs, od_img = _analyze_zone(frame, gray, edges,
#                                          inner_mask=od2_mask, outer_mask=od_mask,
#                                          HIGHLIGHT_SIZE=od_highlight,
#                                          burr_area_min=od_burr_area_min, od_burr_area_max=od_burr_area_max,
#                                          burr_perim_min=od_burr_perim_min, burr_perim_max=od_burr_perim_max,
#                                          draw_id=id_contour, draw_od=od_contour, crop_contour=od_contour)

#     # Combined full-frame overlay with both contours and burr boxes
#     combined_full = frame.copy()
#     if id_contour is not None:
#         cv2.drawContours(combined_full, [id_contour], -1, (0, 255, 0), 4)
#     if od_contour is not None:
#         cv2.drawContours(combined_full, [od_contour], -1, (0, 255, 0), 4)
#     for b in id_burrs:
#         x, y, w, h = cv2.boundingRect(b)
#         cx2, cy2 = x + w // 2, y + h // 2
#         cv2.rectangle(combined_full, (cx2 - id_highlight // 2, cy2 - id_highlight // 2),
#                       (cx2 + id_highlight // 2, cy2 + id_highlight // 2), (255, 0, 0), 3)
#     for b in od_burrs:
#         x, y, w, h = cv2.boundingRect(b)
#         cx2, cy2 = x + w // 2, y + h // 2
#         cv2.rectangle(combined_full, (cx2 - od_highlight // 2, cy2 - od_highlight // 2),
#                       (cx2 + od_highlight // 2, cy2 + od_highlight // 2), (255, 0, 0), 3)
#     id_txt = f"ID: {'NOK' if id_burrs else 'OK'} ({len(id_burrs)})"
#     od_txt = f"OD: {'NOK' if od_burrs else 'OK'} ({len(od_burrs)})"
#     id_color = (0, 0, 255) if id_burrs else (0, 255, 0)
#     od_color = (0, 0, 255) if od_burrs else (0, 255, 0)
#     cv2.putText(combined_full, id_txt, (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.6, id_color, 4)
#     cv2.putText(combined_full, od_txt, (30, 110), cv2.FONT_HERSHEY_SIMPLEX, 1.6, od_color, 4)

#     # Build per-target crops and a union crop around both contours
#     combined_id_crop = crop_around_contour(combined_full, id_contour, crop_size=300) if id_contour is not None else None
#     combined_od_crop = crop_around_contour(combined_full, od_contour, crop_size=300) if od_contour is not None else None
#     combined_both_crop = _union_crop(combined_full, [id_contour, od_contour], pad=30)

#     elapsed_ms = (time.time() - start) * 1000.0

#     return {
#         "id": {"burr_count": len(id_burrs), "burr_status": "NOK" if id_burrs else "OK",
#                "time_ms": elapsed_ms, "burr_output_image": id_img, "burr_contours": id_burrs},
#         "od": {"burr_count": len(od_burrs), "burr_status": "NOK" if od_burrs else "OK",
#                "time_ms": elapsed_ms, "burr_output_image": od_img, "burr_contours": od_burrs},
#         "combined_output_image": combined_full,
#         "combined_output_image_id_crop": combined_id_crop,
#         "combined_output_image_od_crop": combined_od_crop,
#         "combined_output_image_both_crop": combined_both_crop
#     }












### working
# # code 2

# # updated 20_9_2025 (adds circularity/aspect ratio plumbing)
# # updated 23_9_2025 (adds ID/OD parameter split, combined overlay, and cropped single-image save as cam3_bmp.bmp)
# import station_4_defect as dt
# import cv2
# import numpy as np
# import os

# def _parse_num(val, typ):
#     if val == "NA" or val is None:
#         return None
#     return typ(val)

# def main(part, subpart, frame,
#          # ID parameters
#          ID2_OFFSET_ID, HIGHLIGHT_SIZE_ID,
#          ID_BURR_MIN_AREA, ID_BURR_MAX_AREA, ID_BURR_MIN_PERIMETER, ID_BURR_MAX_PERIMETER,
#          # OD parameters
#          ID2_OFFSET_OD, HIGHLIGHT_SIZE_OD,
#          OD_BURR_MIN_AREA, OD_BURR_MAX_AREA, OD_BURR_MIN_PERIMETER, OD_BURR_MAX_PERIMETER,
#          # Contour selection
#          min_id_area, max_id_area, min_od_area, max_od_area,
#          min_circularity, max_circularity, min_aspect_ratio, max_aspect_ratio,
#          output_folder):

#     print(f"DEBUG: Starting main processing for part: {part}, subpart: {subpart}")
#     print(f"DEBUG: ID Area Range: {min_id_area}-{max_id_area}, OD Area Range: {min_od_area}-{max_od_area}")
#     print(f"DEBUG: Shape filters -> circularity: {min_circularity}-{max_circularity}, aspect_ratio: {min_aspect_ratio}-{max_aspect_ratio}")

#     excluded_parts = [
#         "PISTON", "TEFLON PISTON RING", "OIL SEAL", "SPACER", "O RING",
#         "PISTON RING", "TEFLON RING", "GUIDE END", "SEPARATING PISTON", "NRV SEAL"
#     ]

#     if part in excluded_parts:
#         # Fallback write of original as cam4_bmp.bmp for excluded parts
#         try:
#             os.makedirs(output_folder, exist_ok=True)
#             if frame is not None:
#                 fallback_path = os.path.join(output_folder, "cam4_bmp.bmp")
#                 ok = cv2.imwrite(fallback_path, frame)
#                 print(f"Excluded-part fallback write to {fallback_path}: {ok}")
#         except Exception as _e:
#             print(f"Excluded-part fallback write error: {_e}")

#         print(f"DEBUG: Part '{part}' is excluded from burr detection. Returning NA statuses.")
#         print("r")
#         print("Result: NA")
#         print("Error: NA")
#         print("Burr: NA")
#         print("Burr Status: NA")
#         print("burr_count: NA")
#         print("defect_position: NA")
#         print("execution_time: NA")
#         print("Output path: NA")
#         return (
#             "r", "Result: NA", "Error: NA",
#             "Burr: NA", "Burr Status: NA", "burr_count: NA", "defect_position: NA",
#             "execution_time: NA", "Output path: NA"
#         )
#     else:
#         try:
#             print("DEBUG: Converting string parameters to numbers...")
#             # ID params
#             ID2_OFFSET_ID = int(ID2_OFFSET_ID) if ID2_OFFSET_ID != "NA" else None
#             HIGHLIGHT_SIZE_ID = int(HIGHLIGHT_SIZE_ID) if HIGHLIGHT_SIZE_ID != "NA" else None
#             ID_BURR_MIN_AREA = int(ID_BURR_MIN_AREA) if ID_BURR_MIN_AREA != "NA" else None
#             ID_BURR_MAX_AREA = int(ID_BURR_MAX_AREA) if ID_BURR_MAX_AREA != "NA" else None
#             ID_BURR_MIN_PERIMETER = int(ID_BURR_MIN_PERIMETER) if ID_BURR_MIN_PERIMETER != "NA" else None
#             ID_BURR_MAX_PERIMETER = int(ID_BURR_MAX_PERIMETER) if ID_BURR_MAX_PERIMETER != "NA" else None
#             # OD params
#             ID2_OFFSET_OD = int(ID2_OFFSET_OD) if ID2_OFFSET_OD != "NA" else None
#             HIGHLIGHT_SIZE_OD = int(HIGHLIGHT_SIZE_OD) if HIGHLIGHT_SIZE_OD != "NA" else None
#             OD_BURR_MIN_AREA = int(OD_BURR_MIN_AREA) if OD_BURR_MIN_AREA != "NA" else None
#             OD_BURR_MAX_AREA = int(OD_BURR_MAX_AREA) if OD_BURR_MAX_AREA != "NA" else None
#             OD_BURR_MIN_PERIMETER = int(OD_BURR_MIN_PERIMETER) if OD_BURR_MIN_PERIMETER != "NA" else None
#             OD_BURR_MAX_PERIMETER = int(OD_BURR_MAX_PERIMETER) if OD_BURR_MAX_PERIMETER != "NA" else None

#             # Area and shape
#             min_id_area = int(min_id_area) if min_id_area != "NA" else None
#             max_id_area = int(max_id_area) if max_id_area != "NA" else None
#             min_od_area = int(min_od_area) if min_od_area != "NA" else None
#             max_od_area = int(max_od_area) if max_od_area != "NA" else None
#             min_circularity = float(min_circularity) if min_circularity != "NA" else None
#             max_circularity = float(max_circularity) if max_circularity != "NA" else None
#             min_aspect_ratio = float(min_aspect_ratio) if min_aspect_ratio != "NA" else None
#             max_aspect_ratio = float(max_aspect_ratio) if max_aspect_ratio != "NA" else None

#             print("DEBUG: Converted parameters OK.")
#             print(f"DEBUG: ID -> offset={ID2_OFFSET_ID}, highlight={HIGHLIGHT_SIZE_ID}, area={ID_BURR_MIN_AREA}-{ID_BURR_MAX_AREA}, perim={ID_BURR_MIN_PERIMETER}-{ID_BURR_MAX_PERIMETER}")
#             print(f"DEBUG: OD -> offset={ID2_OFFSET_OD}, highlight={HIGHLIGHT_SIZE_OD}, area={OD_BURR_MIN_AREA}-{OD_BURR_MAX_AREA}, perim={OD_BURR_MIN_PERIMETER}-{OD_BURR_MAX_PERIMETER}")
#         except ValueError as e:
#             # On conversion error, attempt fallback write
#             try:
#                 os.makedirs(output_folder, exist_ok=True)
#                 if frame is not None:
#                     fallback_path = os.path.join(output_folder, "cam4_bmp.bmp")
#                     ok = cv2.imwrite(fallback_path, frame)
#                     print(f"Fallback write (param error) to {fallback_path}: {ok}")
#             except Exception as _e:
#                 print(f"Fallback write error (param error): {_e}")

#             print(f"DEBUG: Parameter conversion error: {e}")
#             print("r")
#             print("Result: NOK")
#             print("Error: parameter_conversion")
#             print("Burr: NOK")
#             print("Burr Status: BURR PRESENT")
#             print("burr_count: 0")
#             print("defect_position: None")
#             print("execution_time: 0.0 ms")
#             return (
#                 "e", "NOK", "parameter_conversion",
#                 "Burr: NOK", "Burr Status: BURR PRESENT", "burr_count: 0", "defect_position: None",
#                 "execution_time: 0.0 ms", "Output path: None"
#             )

#         print("DEBUG: Preprocessing with area + shape filters...")
#         processed = dt.preprocess_image(
#             frame,
#             min_id_area=min_id_area, max_id_area=max_id_area,
#             min_od_area=min_od_area, max_od_area=max_od_area,
#             min_circularity=min_circularity, max_circularity=max_circularity,
#             min_aspect_ratio=min_aspect_ratio, max_aspect_ratio=max_aspect_ratio,
#             output_folder=output_folder
#         )
#         print(f"DEBUG: Contours found: {len(processed['sorted_contours'])}")
#         print(f"DEBUG: ID contour found: {processed.get('id_contour') is not None}")
#         print(f"DEBUG: OD contour found: {processed.get('od_contour') is not None}")

#         if len(processed["sorted_contours"]) < 1:
#             print("r"); print("Result: NOK"); print("Error: not_enough_contours")
#             return {"resultType": "e", "error": "not_enough_contours"}

#         # Run ID+OD burr detection with separate parameter sets
#         det = dt.detect_burr_both(
#             frame, processed["sorted_contours"],
#             id_offset=ID2_OFFSET_ID, id_highlight=HIGHLIGHT_SIZE_ID,
#             id_burr_area_min=ID_BURR_MIN_AREA, id_burr_area_max=ID_BURR_MAX_AREA,
#             id_burr_perim_min=ID_BURR_MIN_PERIMETER, id_burr_perim_max=ID_BURR_MAX_PERIMETER,
#             od_offset=ID2_OFFSET_OD, od_highlight=HIGHLIGHT_SIZE_OD,
#             od_burr_area_min=OD_BURR_MIN_AREA, od_burr_area_max=OD_BURR_MAX_AREA,
#             od_burr_perim_min=OD_BURR_MIN_PERIMETER, od_burr_perim_max=OD_BURR_MAX_PERIMETER,
#             min_id_area=min_id_area, max_id_area=max_id_area,
#             min_od_area=min_od_area, max_od_area=max_od_area,
#             min_circularity=min_circularity, max_circularity=max_circularity,
#             min_aspect_ratio=min_aspect_ratio, max_aspect_ratio=max_aspect_ratio,
#             output_folder=output_folder,
#             id_contour=processed.get("id_contour"),
#             od_contour=processed.get("od_contour")
#         )

#         # Prepare paths
#         id_path = os.path.join(output_folder, "cam4_id.bmp")
#         od_path = os.path.join(output_folder, "cam4_od.bmp")
#         combined_full_path = os.path.join(output_folder, "cam4_combined.bmp")
#         combined_both_crop_path = os.path.join(output_folder, "cam4_bmp.bmp")  # single image containing both, cropped
#         combined_id_crop_path = os.path.join(output_folder, "cam4_combined_id.bmp")
#         combined_od_crop_path = os.path.join(output_folder, "cam4_combined_od.bmp")

#         # Ensure folder exists
#         os.makedirs(output_folder, exist_ok=True)

#         # cv2.imwrite(id_path, det["id"]["burr_output_image"] if det["id"]["burr_output_image"] is not None else processed["image"])
#         # cv2.imwrite(od_path, det["od"]["burr_output_image"] if det["od"]["burr_output_image"] is not None else processed["image"])
#         # cv2.imwrite(combined_full_path, det.get("combined_output_image") if det.get("combined_output_image") is not None else processed["image"])

#         # Write cam4_bmp; if annotated missing or write fails, fallback to original frame
#         write_src = det.get("combined_output_image_both_crop") if det.get("combined_output_image_both_crop") is not None else det.get("combined_output_image")
#         if write_src is None:
#             write_src = processed["image"]
#         write_ok = cv2.imwrite(combined_both_crop_path, write_src)
#         if not write_ok:
#             try:
#                 write_ok = cv2.imwrite(combined_both_crop_path, frame)
#                 print(f"Fallback write of original to {combined_both_crop_path}: {write_ok}")
#             except Exception as _e:
#                 print(f"Fallback write error to {combined_both_crop_path}: {_e}")

#         # cv2.imwrite(combined_id_crop_path, det.get("combined_output_image_id_crop") if det.get("combined_output_image_id_crop") is not None else processed["image"])
#         # cv2.imwrite(combined_od_crop_path, det.get("combined_output_image_od_crop") if det.get("combined_output_image_od_crop") is not None else processed["image"])

#         print("r")
#         print(f"ID -> status: {det['id']['burr_status']}, count: {det['id']['burr_count']}, time_ms: {det['id'].get('time_ms', 0):.2f}, path: {id_path}")
#         print(f"OD -> status: {det['od']['burr_status']}, count: {det['od']['burr_count']}, time_ms: {det['od'].get('time_ms', 0):.2f}, path: {od_path}")
#         print(f"Combined (full): {combined_full_path}")
#         print(f"Combined (both crop, cam4_bmp): {combined_both_crop_path}")
#         print(f"Combined (ID crop): {combined_id_crop_path}")
#         print(f"Combined (OD crop): {combined_od_crop_path}")

#         # Final guard to ensure cam4_bmp.bmp exists
#         try:
#             if not os.path.exists(combined_both_crop_path):
#                 cv2.imwrite(combined_both_crop_path, frame)
#                 print(f"Final guard wrote original to {combined_both_crop_path}")
#         except Exception as _e:
#             print(f"Final guard write error: {_e}")

#         return {
#             "resultType": "r", "part": part, "subpart": subpart,
#             "id": {"status": det["id"]["burr_status"], "count": det["id"]["burr_count"],
#                    "time_ms": det["id"].get('time_ms', 0.0), "image_path": id_path},
#             "od": {"status": det["od"]["burr_status"], "count": det["od"]["burr_count"],
#                    "time_ms": det["od"].get('time_ms', 0.0), "image_path": od_path},
#             "combined_image_path": combined_full_path,
#             "combined_image_both_crop_path": combined_both_crop_path,
#             "combined_image_id_crop_path": combined_id_crop_path,
#             "combined_image_od_crop_path": combined_od_crop_path,
#         }







