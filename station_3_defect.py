

# ### working 3 oct 25 
# code 3

# station_3_defect.py      combine ID & OD
# updated on 22_9_2025 (add combined_output_image for ID+OD in one frame; keep existing behavior)
# updated on 22_9_2025 (keep ID/OD cropped outputs; add combined cropped overlays for ID and OD)
# updated on 23_9_2025 (add combined_output_image_both_crop using union bounding box of ID and OD)
import cv2
import numpy as np
import math
import os
import time

def _circularity(contour):
    area = cv2.contourArea(contour)
    perim = cv2.arcLength(contour, True)
    if perim <= 0:
        return None, area, perim
    return (4.0 * math.pi * area) / (perim * perim), area, perim

def _aspect_ratio(contour):
    x, y, w, h = cv2.boundingRect(contour)
    if h == 0:
        return None, (w, h)
    return float(w) / float(h), (w, h)

def _passes_shape_filters(contour, min_circularity, max_circularity, min_aspect_ratio, max_aspect_ratio):
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
    if output_folder:
        os.makedirs(output_folder, exist_ok=True)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
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

def _get_contour_props(contour):
    if contour is None or len(contour) < 5:
        return None
    area = cv2.contourArea(contour)
    m = cv2.moments(contour)
    if m['m00'] != 0:
        cx = int(m['m10'] / m['m00'])
        cy = int(m['m01'] / m['m00'])
        r = int(np.sqrt(area / np.pi))
        return {'area': area, 'center': (cx, cy), 'radius': r}
    return {'area': area, 'center': tuple(contour[0][0]), 'radius': 0}

def _filled_mask_from_contour(gray, contour):
    mask = np.zeros_like(gray, dtype=np.uint8)
    cv2.drawContours(mask, [contour], -1, 255, cv2.FILLED)
    return mask

def _analyze_zone(image, gray, edges, inner_mask, outer_mask,
                  HIGHLIGHT_SIZE, burr_area_min, burr_area_max, burr_perim_min, burr_perim_max,
                  draw_id=None, draw_od=None, crop_contour=None):
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

def _union_crop(image, contours, pad=30):
    h, w = image.shape[:2]
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

    results = {"id": None, "od": None}
    id_burrs = []
    od_burrs = []

    if id_contour is not None:
        id_props = _get_contour_props(id_contour)
        cx, cy = id_props['center']
        r_id = id_props['radius']
        r_id2 = max(r_id + int(id_offset), 0)
        id_mask = _filled_mask_from_contour(gray, id_contour)
        id2_mask = np.zeros_like(gray, dtype=np.uint8)
        cv2.circle(id2_mask, (cx, cy), r_id2, 255, cv2.FILLED)
        id_burrs, id_img = _analyze_zone(frame, gray, edges,
                                         inner_mask=id_mask, outer_mask=id2_mask,
                                         HIGHLIGHT_SIZE=id_highlight,
                                         burr_area_min=id_burr_area_min, burr_area_max=id_burr_area_max,
                                         burr_perim_min=id_burr_perim_min, burr_perim_max=id_burr_perim_max,
                                         draw_id=id_contour, draw_od=od_contour, crop_contour=id_contour)
        results["id"] = {"burr_count": len(id_burrs), "burr_status": "NOK" if id_burrs else "OK",
                         "burr_output_image": id_img, "burr_contours": id_burrs}
    else:
        results["id"] = {"burr_count": 0, "burr_status": "NOK", "burr_output_image": None, "burr_contours": [], "error": "ID contour not found"}

    if od_contour is not None:
        od_props = _get_contour_props(od_contour)
        cx, cy = od_props['center']
        r_od = od_props['radius']
        r_od2 = max(r_od - int(od_offset), 0)
        od_mask = _filled_mask_from_contour(gray, od_contour)
        od2_mask = np.zeros_like(gray, dtype=np.uint8)
        cv2.circle(od2_mask, (cx, cy), r_od2, 255, cv2.FILLED)
        od_burrs, od_img = _analyze_zone(frame, gray, edges,
                                         inner_mask=od2_mask, outer_mask=od_mask,
                                         HIGHLIGHT_SIZE=od_highlight,
                                         burr_area_min=od_burr_area_min, burr_area_max=od_burr_area_max,
                                         burr_perim_min=od_burr_perim_min, burr_perim_max=od_burr_perim_max,
                                         draw_id=id_contour, draw_od=od_contour, crop_contour=od_contour)
        results["od"] = {"burr_count": len(od_burrs), "burr_status": "NOK" if od_burrs else "OK",
                         "burr_output_image": od_img, "burr_contours": od_burrs}
    else:
        results["od"] = {"burr_count": 0, "burr_status": "NOK", "burr_output_image": None, "burr_contours": [], "error": "OD contour not found"}

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
    for k in ("id", "od"):
        results[k]["time_ms"] = elapsed_ms
    results["combined_output_image"] = combined_full
    results["combined_output_image_id_crop"] = combined_id_crop
    results["combined_output_image_od_crop"] = combined_od_crop
    results["combined_output_image_both_crop"] = combined_both_crop
    return results


























#### working 30sep25
# # station_3_defect.py      combine ID & OD
# # updated on 22_9_2025 (add combined_output_image for ID+OD in one frame; keep existing behavior)
# # updated on 22_9_2025 (keep ID/OD cropped outputs; add combined cropped overlays for ID and OD)
# # updated on 23_9_2025 (add combined_output_image_both_crop using union bounding box of ID and OD)
# import cv2
# import numpy as np
# import math
# import os
# import time

# def _circularity(contour):
#     area = cv2.contourArea(contour)
#     perim = cv2.arcLength(contour, True)
#     if perim <= 0:
#         return None, area, perim
#     return (4.0 * math.pi * area) / (perim * perim), area, perim

# def _aspect_ratio(contour):
#     x, y, w, h = cv2.boundingRect(contour)
#     if h == 0:
#         return None, (w, h)
#     return float(w) / float(h), (w, h)

# def _passes_shape_filters(contour, min_circularity, max_circularity, min_aspect_ratio, max_aspect_ratio):
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
#     if output_folder:
#         os.makedirs(output_folder, exist_ok=True)
#     gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#     _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)
#     binary_inv = cv2.bitwise_not(binary)
#     contours, _ = cv2.findContours(binary_inv, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
#     sorted_contours = sorted(contours, key=cv2.contourArea, reverse=True)
#     id_contour = None
#     if min_id_area is not None and max_id_area is not None:
#         for contour in sorted_contours:
#             area = cv2.contourArea(contour)
#             if min_id_area <= area <= max_id_area:
#                 if _passes_shape_filters(contour, min_circularity, max_circularity, min_aspect_ratio, max_aspect_ratio):
#                     id_contour = contour
#                     break
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

# def _get_contour_props(contour):
#     if contour is None or len(contour) < 5:
#         return None
#     area = cv2.contourArea(contour)
#     m = cv2.moments(contour)
#     if m['m00'] != 0:
#         cx = int(m['m10'] / m['m00'])
#         cy = int(m['m01'] / m['m00'])
#         r = int(np.sqrt(area / np.pi))
#         return {'area': area, 'center': (cx, cy), 'radius': r}
#     return {'area': area, 'center': tuple(contour[0][0]), 'radius': 0}

# def _filled_mask_from_contour(gray, contour):
#     mask = np.zeros_like(gray, dtype=np.uint8)
#     cv2.drawContours(mask, [contour], -1, 255, cv2.FILLED)
#     return mask

# def _analyze_zone(image, gray, edges, inner_mask, outer_mask,
#                   HIGHLIGHT_SIZE, burr_area_min, burr_area_max, burr_perim_min, burr_perim_max,
#                   draw_id=None, draw_od=None, crop_contour=None):
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

# def _union_crop(image, contours, pad=30):
#     h, w = image.shape[:2]
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

#     results = {"id": None, "od": None}
#     id_burrs = []
#     od_burrs = []

#     if id_contour is not None:
#         id_props = _get_contour_props(id_contour)
#         cx, cy = id_props['center']
#         r_id = id_props['radius']
#         r_id2 = max(r_id + int(id_offset), 0)
#         id_mask = _filled_mask_from_contour(gray, id_contour)
#         id2_mask = np.zeros_like(gray, dtype=np.uint8)
#         cv2.circle(id2_mask, (cx, cy), r_id2, 255, cv2.FILLED)
#         id_burrs, id_img = _analyze_zone(frame, gray, edges,
#                                          inner_mask=id_mask, outer_mask=id2_mask,
#                                          HIGHLIGHT_SIZE=id_highlight,
#                                          burr_area_min=id_burr_area_min, burr_area_max=id_burr_area_max,
#                                          burr_perim_min=id_burr_perim_min, burr_perim_max=id_burr_perim_max,
#                                          draw_id=id_contour, draw_od=od_contour, crop_contour=id_contour)
#         results["id"] = {"burr_count": len(id_burrs), "burr_status": "NOK" if id_burrs else "OK",
#                          "burr_output_image": id_img, "burr_contours": id_burrs}
#     else:
#         results["id"] = {"burr_count": 0, "burr_status": "NOK", "burr_output_image": None, "burr_contours": [], "error": "ID contour not found"}

#     if od_contour is not None:
#         od_props = _get_contour_props(od_contour)
#         cx, cy = od_props['center']
#         r_od = od_props['radius']
#         r_od2 = max(r_od - int(od_offset), 0)
#         od_mask = _filled_mask_from_contour(gray, od_contour)
#         od2_mask = np.zeros_like(gray, dtype=np.uint8)
#         cv2.circle(od2_mask, (cx, cy), r_od2, 255, cv2.FILLED)
#         od_burrs, od_img = _analyze_zone(frame, gray, edges,
#                                          inner_mask=od2_mask, outer_mask=od_mask,
#                                          HIGHLIGHT_SIZE=od_highlight,
#                                          burr_area_min=od_burr_area_min, burr_area_max=od_burr_area_max,
#                                          burr_perim_min=od_burr_perim_min, burr_perim_max=od_burr_perim_max,
#                                          draw_id=id_contour, draw_od=od_contour, crop_contour=od_contour)
#         results["od"] = {"burr_count": len(od_burrs), "burr_status": "NOK" if od_burrs else "OK",
#                          "burr_output_image": od_img, "burr_contours": od_burrs}
#     else:
#         results["od"] = {"burr_count": 0, "burr_status": "NOK", "burr_output_image": None, "burr_contours": [], "error": "OD contour not found"}

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

#     combined_id_crop = crop_around_contour(combined_full, id_contour, crop_size=300) if id_contour is not None else None
#     combined_od_crop = crop_around_contour(combined_full, od_contour, crop_size=300) if od_contour is not None else None
#     combined_both_crop = _union_crop(combined_full, [id_contour, od_contour], pad=30)

#     elapsed_ms = (time.time() - start) * 1000.0
#     for k in ("id", "od"):
#         results[k]["time_ms"] = elapsed_ms
#     results["combined_output_image"] = combined_full
#     results["combined_output_image_id_crop"] = combined_id_crop
#     results["combined_output_image_od_crop"] = combined_od_crop
#     results["combined_output_image_both_crop"] = combined_both_crop
#     return results


