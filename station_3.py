# station_3.py   combine ID & OD
# updated on 22_9_2025 (add saving of combined ID+OD overlay as cam3_combined.bmp; keep others)
# updated on 22_9_2025 (save combined cropped overlays; keep all prior outputs unchanged)
# updated on 23_9_2025 (save cropped combined ID+OD overlay as cam3_bmp.bmp using cv2.imwrite)
import station_3_defect as dt
import cv2
import os  # needed for join when calling cv2.imwrite paths

def _parse_num(val, typ):
    if val == "NA" or val is None:
        return None
    return typ(val)

def main(part, subpart, frame,
         # ID parameters
         ID2_OFFSET_ID, HIGHLIGHT_SIZE_ID,
         ID_BURR_MIN_AREA, ID_BURR_MAX_AREA, ID_BURR_MIN_PERIMETER, ID_BURR_MAX_PERIMETER,
         # OD parameters
         ID2_OFFSET_OD, HIGHLIGHT_SIZE_OD,
         OD_BURR_MIN_AREA, OD_BURR_MAX_AREA, OD_BURR_MIN_PERIMETER, OD_BURR_MAX_PERIMETER,
         # Contour selection
         min_id_area, max_id_area, min_od_area, max_od_area,
         min_circularity, max_circularity, min_aspect_ratio, max_aspect_ratio,
         output_folder):

    try:
        id_offset = _parse_num(ID2_OFFSET_ID, int)
        id_high = _parse_num(HIGHLIGHT_SIZE_ID, int)
        id_ba_min = _parse_num(ID_BURR_MIN_AREA, int)
        id_ba_max = _parse_num(ID_BURR_MAX_AREA, int)
        id_bp_min = _parse_num(ID_BURR_MIN_PERIMETER, int)
        id_bp_max = _parse_num(ID_BURR_MAX_PERIMETER, int)

        od_offset = _parse_num(ID2_OFFSET_OD, int)
        od_high = _parse_num(HIGHLIGHT_SIZE_OD, int)
        od_ba_min = _parse_num(OD_BURR_MIN_AREA, int)
        od_ba_max = _parse_num(OD_BURR_MAX_AREA, int)
        od_bp_min = _parse_num(OD_BURR_MIN_PERIMETER, int)
        od_bp_max = _parse_num(OD_BURR_MAX_PERIMETER, int)

        min_id_area = _parse_num(min_id_area, int)
        max_id_area = _parse_num(max_id_area, int)
        min_od_area = _parse_num(min_od_area, int)
        max_od_area = _parse_num(max_od_area, int)

        min_circularity = _parse_num(min_circularity, float)
        max_circularity = _parse_num(max_circularity, float)
        min_aspect_ratio = _parse_num(min_aspect_ratio, float)
        max_aspect_ratio = _parse_num(max_aspect_ratio, float)
    except Exception:
        print("r"); print("Result: NOK"); print("Error: parameter_conversion")
        return {"resultType": "e", "error": "parameter_conversion"}

    processed = dt.preprocess_image(
        frame,
        min_id_area=min_id_area, max_id_area=max_id_area,
        min_od_area=min_od_area, max_od_area=max_od_area,
        min_circularity=min_circularity, max_circularity=max_circularity,
        min_aspect_ratio=min_aspect_ratio, max_aspect_ratio=max_aspect_ratio,
        output_folder=output_folder
    )
    if len(processed["sorted_contours"]) < 1:
        print("r"); print("Result: NOK"); print("Error: not_enough_contours")
        return {"resultType": "e", "error": "not_enough_contours"}

    det = dt.detect_burr_both(
        frame, processed["sorted_contours"],
        id_offset, id_high, id_ba_min, id_ba_max, id_bp_min, id_bp_max,
        od_offset, od_high, od_ba_min, od_ba_max, od_bp_min, od_bp_max,
        min_id_area=min_id_area, max_id_area=max_id_area,
        min_od_area=min_od_area, max_od_area=max_od_area,
        min_circularity=min_circularity, max_circularity=max_circularity,
        min_aspect_ratio=min_aspect_ratio, max_aspect_ratio=max_aspect_ratio,
        output_folder=output_folder,
        id_contour=processed.get("id_contour"),
        od_contour=processed.get("od_contour")
    )

    # Prepare file paths
    id_path = os.path.join(output_folder, "cam3_id.bmp")
    od_path = os.path.join(output_folder, "cam3_od.bmp")
    combined_full_path = os.path.join(output_folder, "cam3_combined.bmp")
    combined_both_crop_path = os.path.join(output_folder, "cam3_bmp.bmp")  # single image containing both, cropped
    combined_id_crop_path = os.path.join(output_folder, "cam3_combined_id.bmp")
    combined_od_crop_path = os.path.join(output_folder, "cam3_combined_od.bmp")

    # Ensure folder exists, then save each output with cv2.imwrite (comment any line to disable writing that artifact)  [cv2.imwrite]
    os.makedirs(output_folder, exist_ok=True)
    # cv2.imwrite(id_path, det["id"]["burr_output_image"] if det["id"]["burr_output_image"] is not None else processed["image"])  # easy to comment out [imwrite]
    # cv2.imwrite(od_path, det["od"]["burr_output_image"] if det["od"]["burr_output_image"] is not None else processed["image"])  # easy to comment out [imwrite]
    # cv2.imwrite(combined_full_path, det.get("combined_output_image") if det.get("combined_output_image") is not None else processed["image"])  # [imwrite]
    cv2.imwrite(combined_both_crop_path, det.get("combined_output_image_both_crop") if det.get("combined_output_image_both_crop") is not None else det.get("combined_output_image"))  # [imwrite]
    # cv2.imwrite(combined_id_crop_path, det.get("combined_output_image_id_crop") if det.get("combined_output_image_id_crop") is not None else processed["image"])  # [imwrite]
    # cv2.imwrite(combined_od_crop_path, det.get("combined_output_image_od_crop") if det.get("combined_output_image_od_crop") is not None else processed["image"])  # [imwrite]

    print("r")
    print(f"ID -> status: {det['id']['burr_status']}, count: {det['id']['burr_count']}, time_ms: {det['id'].get('time_ms', 0):.2f}, path: {id_path}")
    print(f"OD -> status: {det['od']['burr_status']}, count: {det['od']['burr_count']}, time_ms: {det['od'].get('time_ms', 0):.2f}, path: {od_path}")
    print(f"Combined (full): {combined_full_path}")
    print(f"Combined (both crop, cam3_bmp): {combined_both_crop_path}")
    print(f"Combined (ID crop): {combined_id_crop_path}")
    print(f"Combined (OD crop): {combined_od_crop_path}")

    return {
        "resultType": "r", "part": part, "subpart": subpart,
        "id": {"status": det["id"]["burr_status"], "count": det["id"]["burr_count"],
               "time_ms": det["id"].get("time_ms", 0.0), "image_path": id_path},
        "od": {"status": det["od"]["burr_status"], "count": det["od"]["burr_count"],
               "time_ms": det["od"].get("time_ms", 0.0), "image_path": od_path},
        "combined_image_path": combined_full_path,
        "combined_image_both_crop_path": combined_both_crop_path,
        "combined_image_id_crop_path": combined_id_crop_path,
        "combined_image_od_crop_path": combined_od_crop_path,
    }



























# # station_3.py   combine ID & OD  [web:2]
# # updated on 22_9_2025 (add saving of combined ID+OD overlay as cam3_combined.bmp; keep others)  [web:2]
# # updated on 22_9_2025 (save combined cropped overlays; keep all prior outputs unchanged)  [web:2]
# import station_3_defect as dt
# import cv2

# def _parse_num(val, typ):
#     # Utility to parse string numbers or "NA" into typed values or None; keeps input interface flexible for GUI/JSON sources  [web:2]
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

#     try:
#         # Convert string inputs into ints/floats or None; any failure flags parameter_conversion for early, safe exit  [web:2]
#         id_offset = _parse_num(ID2_OFFSET_ID, int)
#         id_high = _parse_num(HIGHLIGHT_SIZE_ID, int)
#         id_ba_min = _parse_num(ID_BURR_MIN_AREA, int)
#         id_ba_max = _parse_num(ID_BURR_MAX_AREA, int)
#         id_bp_min = _parse_num(ID_BURR_MIN_PERIMETER, int)
#         id_bp_max = _parse_num(ID_BURR_MAX_PERIMETER, int)

#         od_offset = _parse_num(ID2_OFFSET_OD, int)
#         od_high = _parse_num(HIGHLIGHT_SIZE_OD, int)
#         od_ba_min = _parse_num(OD_BURR_MIN_AREA, int)
#         od_ba_max = _parse_num(OD_BURR_MAX_AREA, int)
#         od_bp_min = _parse_num(OD_BURR_MIN_PERIMETER, int)
#         od_bp_max = _parse_num(OD_BURR_MAX_PERIMETER, int)

#         min_id_area = _parse_num(min_id_area, int)
#         max_id_area = _parse_num(max_id_area, int)
#         min_od_area = _parse_num(min_od_area, int)
#         max_od_area = _parse_num(max_od_area, int)

#         min_circularity = _parse_num(min_circularity, float)
#         max_circularity = _parse_num(max_circularity, float)
#         min_aspect_ratio = _parse_num(min_aspect_ratio, float)
#         max_aspect_ratio = _parse_num(max_aspect_ratio, float)
#     except Exception:
#         # Uniform error reporting when parameter parsing fails; keep output contract stable for callers  [web:2]
#         print("r"); print("Result: NOK"); print("Error: parameter_conversion")
#         return {"resultType": "e", "error": "parameter_conversion"}  # [web:12]

#     # Preprocess: grayscale → threshold to binary → find contours → select ID/OD by area/shape windows; returns contours and debug image  [web:12]
#     processed = dt.preprocess_image(
#         frame,
#         min_id_area=min_id_area, max_id_area=max_id_area,
#         min_od_area=min_od_area, max_od_area=max_od_area,
#         min_circularity=min_circularity, max_circularity=max_circularity,
#         min_aspect_ratio=min_aspect_ratio, max_aspect_ratio=max_aspect_ratio,
#         output_folder=output_folder
#     )
#     if len(processed["sorted_contours"]) < 1:
#         # Ensure at least one contour found; early out with explicit not_enough_contours error for traceability  [web:2]
#         print("r"); print("Result: NOK"); print("Error: not_enough_contours")
#         return {"resultType": "e", "error": "not_enough_contours"}  # [web:12]

#     # Detect burrs in both ID outward band and OD inward band; returns per-target overlays and a combined overlay with annotations  [web:2]
#     det = dt.detect_burr_both(
#         frame, processed["sorted_contours"],
#         id_offset, id_high, id_ba_min, id_ba_max, id_bp_min, id_bp_max,
#         od_offset, od_high, od_ba_min, od_ba_max, od_bp_min, od_bp_max,
#         min_id_area=min_id_area, max_id_area=max_id_area,
#         min_od_area=min_od_area, max_od_area=max_od_area,
#         min_circularity=min_circularity, max_circularity=max_circularity,
#         min_aspect_ratio=min_aspect_ratio, max_aspect_ratio=max_aspect_ratio,
#         output_folder=output_folder,
#         id_contour=processed.get("id_contour"),
#         od_contour=processed.get("od_contour")
#     )  # [web:12]

#     # Save legacy per-target cropped overlays for ID and OD to maintain backward-compatible outputs  [web:2]
#     save_id = dt.save_burr_result_image(processed["image"], det["id"]["burr_output_image"],
#                                         output_folder=output_folder, filename="cam3_id.bmp")
#     save_od = dt.save_burr_result_image(processed["image"], det["od"]["burr_output_image"],
#                                         output_folder=output_folder, filename="cam3_od.bmp")

#     # Save the full-frame combined overlay showing ID and OD contours, burr boxes, and status text  [web:2]
#     save_combined_full = dt.save_burr_result_image(processed["image"], det.get("combined_output_image"),
#                                                    output_folder=output_folder, filename="cam3_combined.bmp")

#     # Save combined ID-crop and combined OD-crop, preserving prior cropping behavior for compatibility  [web:2]
#     save_combined_id = dt.save_burr_result_image(processed["image"], det.get("combined_output_image_id_crop"),
#                                                  output_folder=output_folder, filename="cam3_combined_id.bmp")
#     save_combined_od = dt.save_burr_result_image(processed["image"], det.get("combined_output_image_od_crop"),
#                                                  output_folder=output_folder, filename="cam3_combined_od.bmp")

#     # Print concise station summary including status, burr counts, timings, and saved paths for quick verification  [web:2]
#     print("r")
#     print(f"ID -> status: {det['id']['burr_status']}, count: {det['id']['burr_count']}, time_ms: {det['id'].get('time_ms', 0):.2f}, path: {save_id.get('output_path')}")
#     print(f"OD -> status: {det['od']['burr_status']}, count: {det['od']['burr_count']}, time_ms: {det['od'].get('time_ms', 0):.2f}, path: {save_od.get('output_path')}")
#     print(f"Combined (full): {save_combined_full.get('output_path')}")
#     print(f"Combined (ID crop): {save_combined_id.get('output_path')}")
#     print(f"Combined (OD crop): {save_combined_od.get('output_path')}")

#     # Return a structured dict containing per-target results and combined overlay paths for downstream consumers  [web:2]
#     return {
#         "resultType": "r", "part": part, "subpart": subpart,
#         "id": {"status": det["id"]["burr_status"], "count": det["id"]["burr_count"],
#                "time_ms": det["id"].get("time_ms", 0.0), "image_path": save_id.get("output_path")},
#         "od": {"status": det["od"]["burr_status"], "count": det["od"]["burr_count"],
#                "time_ms": det["od"].get("time_ms", 0.0), "image_path": save_od.get("output_path")},
#         "combined_image_path": save_combined_full.get("output_path"),
#         "combined_image_id_crop_path": save_combined_id.get("output_path"),
#         "combined_image_od_crop_path": save_combined_od.get("output_path"),
#     }  # [web:12][web:2]












# ## upto 23 sep_25  10am

# # station_3.py   combine ID & OD 
# # updated on 22_9_2025 (add saving of combined ID+OD overlay as cam3_combined.bmp; keep others)
# # updated on 22_9_2025 (save combined cropped overlays; keep all prior outputs unchanged)
# import station_3_defect as dt
# import cv2

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

#     try:
#         id_offset = _parse_num(ID2_OFFSET_ID, int)
#         id_high = _parse_num(HIGHLIGHT_SIZE_ID, int)
#         id_ba_min = _parse_num(ID_BURR_MIN_AREA, int)
#         id_ba_max = _parse_num(ID_BURR_MAX_AREA, int)
#         id_bp_min = _parse_num(ID_BURR_MIN_PERIMETER, int)
#         id_bp_max = _parse_num(ID_BURR_MAX_PERIMETER, int)

#         od_offset = _parse_num(ID2_OFFSET_OD, int)
#         od_high = _parse_num(HIGHLIGHT_SIZE_OD, int)
#         od_ba_min = _parse_num(OD_BURR_MIN_AREA, int)
#         od_ba_max = _parse_num(OD_BURR_MAX_AREA, int)
#         od_bp_min = _parse_num(OD_BURR_MIN_PERIMETER, int)
#         od_bp_max = _parse_num(OD_BURR_MAX_PERIMETER, int)

#         min_id_area = _parse_num(min_id_area, int)
#         max_id_area = _parse_num(max_id_area, int)
#         min_od_area = _parse_num(min_od_area, int)
#         max_od_area = _parse_num(max_od_area, int)

#         min_circularity = _parse_num(min_circularity, float)
#         max_circularity = _parse_num(max_circularity, float)
#         min_aspect_ratio = _parse_num(min_aspect_ratio, float)
#         max_aspect_ratio = _parse_num(max_aspect_ratio, float)
#     except Exception:
#         print("r"); print("Result: NOK"); print("Error: parameter_conversion")
#         return {"resultType": "e", "error": "parameter_conversion"}  # [web:12]

#     processed = dt.preprocess_image(
#         frame,
#         min_id_area=min_id_area, max_id_area=max_id_area,
#         min_od_area=min_od_area, max_od_area=max_od_area,
#         min_circularity=min_circularity, max_circularity=max_circularity,
#         min_aspect_ratio=min_aspect_ratio, max_aspect_ratio=max_aspect_ratio,
#         output_folder=output_folder
#     )
#     if len(processed["sorted_contours"]) < 1:
#         print("r"); print("Result: NOK"); print("Error: not_enough_contours")
#         return {"resultType": "e", "error": "not_enough_contours"}  # [web:12]

#     det = dt.detect_burr_both(
#         frame, processed["sorted_contours"],
#         id_offset, id_high, id_ba_min, id_ba_max, id_bp_min, id_bp_max,
#         od_offset, od_high, od_ba_min, od_ba_max, od_bp_min, od_bp_max,
#         min_id_area=min_id_area, max_id_area=max_id_area,
#         min_od_area=min_od_area, max_od_area=max_od_area,
#         min_circularity=min_circularity, max_circularity=max_circularity,
#         min_aspect_ratio=min_aspect_ratio, max_aspect_ratio=max_aspect_ratio,
#         output_folder=output_folder,
#         id_contour=processed.get("id_contour"),
#         od_contour=processed.get("od_contour")
#     )  # [web:12]

#     # Save legacy cropped per-target overlays
#     save_id = dt.save_burr_result_image(processed["image"], det["id"]["burr_output_image"],
#                                         output_folder=output_folder, filename="cam3_id.bmp")
#     save_od = dt.save_burr_result_image(processed["image"], det["od"]["burr_output_image"],
#                                         output_folder=output_folder, filename="cam3_od.bmp")

#     # Save full-frame combined overlay (optional)
#     save_combined_full = dt.save_burr_result_image(processed["image"], det.get("combined_output_image"),
#                                                    output_folder=output_folder, filename="cam3_combined.bmp")

#     # Save new combined cropped overlays that respect prior cropping behavior
#     save_combined_id = dt.save_burr_result_image(processed["image"], det.get("combined_output_image_id_crop"),
#                                                  output_folder=output_folder, filename="cam3_combined_id.bmp")
#     save_combined_od = dt.save_burr_result_image(processed["image"], det.get("combined_output_image_od_crop"),
#                                                  output_folder=output_folder, filename="cam3_combined_od.bmp")

#     print("r")
#     print(f"ID -> status: {det['id']['burr_status']}, count: {det['id']['burr_count']}, time_ms: {det['id'].get('time_ms', 0):.2f}, path: {save_id.get('output_path')}")
#     print(f"OD -> status: {det['od']['burr_status']}, count: {det['od']['burr_count']}, time_ms: {det['od'].get('time_ms', 0):.2f}, path: {save_od.get('output_path')}")
#     print(f"Combined (full): {save_combined_full.get('output_path')}")
#     print(f"Combined (ID crop): {save_combined_id.get('output_path')}")
#     print(f"Combined (OD crop): {save_combined_od.get('output_path')}")

#     return {
#         "resultType": "r", "part": part, "subpart": subpart,
#         "id": {"status": det["id"]["burr_status"], "count": det["id"]["burr_count"],
#                "time_ms": det["id"].get("time_ms", 0.0), "image_path": save_id.get("output_path")},
#         "od": {"status": det["od"]["burr_status"], "count": det["od"]["burr_count"],
#                "time_ms": det["od"].get("time_ms", 0.0), "image_path": save_od.get("output_path")},
#         "combined_image_path": save_combined_full.get("output_path"),
#         "combined_image_id_crop_path": save_combined_id.get("output_path"),
#         "combined_image_od_crop_path": save_combined_od.get("output_path"),
#     }  # [web:122][web:40]





































# # updated on 20_9_2025 (adds circularity/aspect ratio plumbing)
# import station_3_defect as dt
# import cv2
# import numpy as np

# def main(part, subpart, frame, ID2_OFFSET, HIGHLIGHT_SIZE, id_BURR_MIN_AREA,
#          id_BURR_MAX_AREA, id_BURR_MIN_PERIMETER, id_BURR_MAX_PERIMETER,
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

#     try:
#         print("DEBUG: Converting string parameters to integers/floats...")
#         ID2_OFFSET = int(ID2_OFFSET) if ID2_OFFSET != "NA" else None
#         HIGHLIGHT_SIZE = int(HIGHLIGHT_SIZE) if HIGHLIGHT_SIZE != "NA" else None
#         id_BURR_MIN_AREA = int(id_BURR_MIN_AREA) if id_BURR_MIN_AREA != "NA" else None
#         id_BURR_MAX_AREA = int(id_BURR_MAX_AREA) if id_BURR_MAX_AREA != "NA" else None
#         id_BURR_MIN_PERIMETER = int(id_BURR_MIN_PERIMETER) if id_BURR_MIN_PERIMETER != "NA" else None
#         id_BURR_MAX_PERIMETER = int(id_BURR_MAX_PERIMETER) if id_BURR_MAX_PERIMETER != "NA" else None

#         min_id_area = int(min_id_area) if min_id_area != "NA" else None
#         max_id_area = int(max_id_area) if max_id_area != "NA" else None
#         min_od_area = int(min_od_area) if min_od_area != "NA" else None
#         max_od_area = int(max_od_area) if max_od_area != "NA" else None

#         # NEW: shape filters
#         min_circularity = float(min_circularity) if min_circularity != "NA" else None
#         max_circularity = float(max_circularity) if max_circularity != "NA" else None
#         min_aspect_ratio = float(min_aspect_ratio) if min_aspect_ratio != "NA" else None
#         max_aspect_ratio = float(max_aspect_ratio) if max_aspect_ratio != "NA" else None

#         print("DEBUG: Parameter conversion successful.")

#     except ValueError as e:
#         print(f"DEBUG: Parameter conversion error: {e}")
#         print("r")
#         print("Result: NOK")
#         print("Error: parameter_conversion")
#         print("Burr: NOK")
#         print("Burr Status: BURR PRESENT")
#         print("burr_count: 0")
#         print("defect_position: None")
#         print("execution_time: 0.0 ms")
#         return (
#             "e", "NOK", "parameter_conversion",
#             "Burr: NOK", "Burr Status: BURR PRESENT", "burr_count: 0", "defect_position: None",
#             "execution_time: 0.0 ms", "Output path: None"
#         )

#     result = {
#         'resultType': 'r',
#         'result': 'OK',
#         'errorType': None,
#         'image_path': None,
#         'measurements': {
#             'burr': {'count': 0, 'status': 'OK', 'position': 'None'},
#             'execution_time': 0.0
#         }
#     }
#     print("DEBUG: Initialized result structure")

#     try:
#         print("DEBUG: Preprocessing with area + shape filters...")
#         processed = dt.preprocess_image(
#             frame,
#             min_id_area=min_id_area, max_id_area=max_id_area,
#             min_od_area=min_od_area, max_od_area=max_od_area,
#             # NEW: shape filters
#             min_circularity=min_circularity, max_circularity=max_circularity,
#             min_aspect_ratio=min_aspect_ratio, max_aspect_ratio=max_aspect_ratio,
#             output_folder=output_folder
#         )
#         print(f"DEBUG: Contours found during preprocessing: {len(processed['sorted_contours'])}")
#         print(f"DEBUG: ID contour found: {processed.get('id_contour') is not None}")
#         print(f"DEBUG: OD contour found: {processed.get('od_contour') is not None}")

#         if len(processed["sorted_contours"]) < 1:
#             raise ValueError("Not enough contours found for burr detection")

#         contours = processed["sorted_contours"]

#         burr_detect_parts = [
#             "SUPPORT PISTON RING", "SUPPORT PISTON", "NRV WASHER", "WASHER"
#         ]

#         if part in burr_detect_parts:
#             print(f"DEBUG: Running burr detection with area + shape filters...")
#             burr_data = dt.detect_burr(
#                 frame, contours,
#                 ID2_OFFSET=ID2_OFFSET,
#                 HIGHLIGHT_SIZE=HIGHLIGHT_SIZE,
#                 id_BURR_MIN_AREA=id_BURR_MIN_AREA,
#                 id_BURR_MAX_AREA=id_BURR_MAX_AREA,
#                 id_BURR_MIN_PERIMETER=id_BURR_MIN_PERIMETER,
#                 id_BURR_MAX_PERIMETER=id_BURR_MAX_PERIMETER,
#                 min_id_area=min_id_area, max_id_area=max_id_area,
#                 min_od_area=min_od_area, max_od_area=max_od_area,
#                 # NEW: shape filters
#                 min_circularity=min_circularity, max_circularity=max_circularity,
#                 min_aspect_ratio=min_aspect_ratio, max_aspect_ratio=max_aspect_ratio,
#                 output_folder=output_folder,
#                 id_contour=processed.get("id_contour"),
#                 od_contour=processed.get("od_contour")
#             )
#             print(f"DEBUG: Burr detection completed - Count: {burr_data['burr_count']}, Status: {burr_data['burr_status']}")
#             print(f"DEBUG: Execution time: {burr_data['time_ms']:.2f} ms")

#             result['measurements'].update({
#                 'burr': {
#                     'count': burr_data['burr_count'],
#                     'status': burr_data['burr_status'],
#                     'position': 'ID' if burr_data['burr_count'] > 0 else 'None'
#                 },
#                 'execution_time': burr_data['time_ms']
#             })
#             print("DEBUG: Saving result image...")
#             save_result = dt.save_burr_result_image(processed["image"], burr_data, output_folder)
#             result['image_path'] = save_result['output_path']
#             print(f"DEBUG: Result image saved at: {result['image_path']}")
#         else:
#             raise ValueError("Burr detection not implemented for this part.")

#         defect_lines = []
#         burr_present = result['measurements']['burr']['status'] == "NOK"
#         if burr_present:
#             defect_lines.append("Burr detected")

#         burr_count = result['measurements']['burr']['count']
#         burr_status = result['measurements']['burr']['status']
#         defect_position = result['measurements']['burr']['position']
#         execution_time = result['measurements']['execution_time']
#         output_path = result['image_path']
#         burr_written_status = "BURR PRESENT" if burr_present else "NO BURR"

#         print("DEBUG: Preparing final output...")
#         print("r")
#         print("Result:", "NOK" if defect_lines else "OK")
#         print("Error:", ", ".join(defect_lines) if defect_lines else "None")
#         print(f"Burr: {burr_status}")
#         print(f"Burr Status: {burr_written_status}")
#         print(f"burr_count: {burr_count}")
#         print(f"defect_position: {defect_position}")
#         print(f"execution_time: {execution_time:.2f} ms")
#         print(f"Output path: {output_path}")

#         return (
#             "r",
#             f"{'NOK' if defect_lines else 'OK'}",
#             f"{', '.join(defect_lines)}" if defect_lines else "None",
#             f"{burr_status}",
#             f"{burr_count}",
#         )

#     except Exception as e:
#         print(f"DEBUG: Exception occurred in main processing: {str(e)}")
#         print("r")
#         print("Result: NOK")
#         print("Error:", str(e))
#         print("Burr: NOK")
#         print("Burr Status: BURR PRESENT")
#         print("burr_count: 0")
#         print("defect_position: None")
#         print("execution_time: 0.0 ms")
#         print("Output path: None")
#         return (
#             "e", "NOK", str(e),
#             "Burr: NOK", "Burr Status: BURR PRESENT", "burr_count: 0", "defect_position: None",
#             "execution_time: 0.0 ms", "Output path: None"
#         )
























# # updated on 14_9_2025


# import station_3_defect as dt
# import cv2
# import numpy as np

# def main(part, subpart, frame, ID2_OFFSET, HIGHLIGHT_SIZE, id_BURR_MIN_AREA, 
#          id_BURR_MAX_AREA, id_BURR_MIN_PERIMETER, id_BURR_MAX_PERIMETER, 
#          min_id_area, max_id_area, min_od_area, max_od_area, output_folder):
    
#     print(f"DEBUG: Starting main processing for part: {part}, subpart: {subpart}")
#     print(f"DEBUG: ID Area Range: {min_id_area}-{max_id_area}, OD Area Range: {min_od_area}-{max_od_area}")
    
#     # Check if part is in the excluded list - parts that don't require burr detection
#     excluded_parts = [
#         "PISTON", "TEFLON PISTON RING", "OIL SEAL", "SPACER", "O RING", 
#         "PISTON RING", "TEFLON RING", "GUIDE END", "SEPARATING PISTON", "NRV SEAL"
#     ]
    
#     if part in excluded_parts:
#         print(f"DEBUG: Part '{part}' is excluded from burr detection. Returning NA statuses.")
#         # For excluded parts, return NA values for all outputs without processing
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
#         # Process only for non-excluded parts
#         # Convert string parameters to appropriate types with error handling
#         try:
#             print("DEBUG: Converting string parameters to integers...")
#             ID2_OFFSET = int(ID2_OFFSET) if ID2_OFFSET != "NA" else None
#             HIGHLIGHT_SIZE = int(HIGHLIGHT_SIZE) if HIGHLIGHT_SIZE != "NA" else None
#             id_BURR_MIN_AREA = int(id_BURR_MIN_AREA) if id_BURR_MIN_AREA != "NA" else None
#             id_BURR_MAX_AREA = int(id_BURR_MAX_AREA) if id_BURR_MAX_AREA != "NA" else None
#             id_BURR_MIN_PERIMETER = int(id_BURR_MIN_PERIMETER) if id_BURR_MIN_PERIMETER != "NA" else None
#             id_BURR_MAX_PERIMETER = int(id_BURR_MAX_PERIMETER) if id_BURR_MAX_PERIMETER != "NA" else None
            
#             # Convert new ID/OD area parameters
#             min_id_area = int(min_id_area) if min_id_area != "NA" else None
#             max_id_area = int(max_id_area) if max_id_area != "NA" else None
#             min_od_area = int(min_od_area) if min_od_area != "NA" else None
#             max_od_area = int(max_od_area) if max_od_area != "NA" else None
            
#             print("DEBUG: Converted parameters to integers successfully.")
#             print(f"DEBUG: Converted values - ID2_OFFSET: {ID2_OFFSET}, HIGHLIGHT_SIZE: {HIGHLIGHT_SIZE}")
#             print(f"DEBUG: ID Area: {min_id_area}-{max_id_area}, OD Area: {min_od_area}-{max_od_area}")
#         except ValueError as e:
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

#         # Initialize result structure for storing processing outcomes
#         result = {
#             'resultType': 'r',
#             'result': 'OK',
#             'errorType': None,
#             'image_path': None,
#             'measurements': {
#                 'burr': {'count': 0, 'status': 'OK', 'position': 'None'},
#                 'execution_time': 0.0
#             }
#         }
#         print("DEBUG: Initialized result structure")

#         try:
#             print("DEBUG: Starting preprocessing of image with configurable area parameters...")
#             # Pass configurable ID/OD area parameters to preprocessing
#             processed = dt.preprocess_image(
#                 frame, 
#                 min_id_area=min_id_area,
#                 max_id_area=max_id_area,
#                 min_od_area=min_od_area,
#                 max_od_area=max_od_area,
#                 output_folder=output_folder
#             )
#             print(f"DEBUG: Contours found during preprocessing: {len(processed['sorted_contours'])}")
#             print(f"DEBUG: ID contour found: {processed.get('id_contour') is not None}")
#             print(f"DEBUG: OD contour found: {processed.get('od_contour') is not None}")
            
#             if len(processed["sorted_contours"]) < 1:
#                 raise ValueError("Not enough contours found for burr detection")
#             contours = processed["sorted_contours"]

#             # Burr detection logic for specific parts only
#             burr_detect_parts = [
#                 "SUPPORT PISTON RING", "SUPPORT PISTON", "NRV WASHER", "WASHER"
#             ]
            
#             if part in burr_detect_parts:
#                 print(f"DEBUG: Part '{part}' is eligible for burr detection. Running detection algorithm...")
#                 # Pass all parameters including configurable ID/OD areas to detect_burr function
#                 burr_data = dt.detect_burr(
#                     frame, contours, 
#                     ID2_OFFSET=ID2_OFFSET,
#                     HIGHLIGHT_SIZE=HIGHLIGHT_SIZE,
#                     id_BURR_MIN_AREA=id_BURR_MIN_AREA,
#                     id_BURR_MAX_AREA=id_BURR_MAX_AREA,
#                     id_BURR_MIN_PERIMETER=id_BURR_MIN_PERIMETER,
#                     id_BURR_MAX_PERIMETER=id_BURR_MAX_PERIMETER,
#                     # Pass configurable ID/OD area parameters
#                     min_id_area=min_id_area,
#                     max_id_area=max_id_area,
#                     min_od_area=min_od_area,
#                     max_od_area=max_od_area,
#                     output_folder=output_folder,
#                     # Pass the pre-identified contours for green visualization
#                     id_contour=processed.get("id_contour"),
#                     od_contour=processed.get("od_contour")
#                 )
#                 print(f"DEBUG: Burr detection completed - Count: {burr_data['burr_count']}, Status: {burr_data['burr_status']}")
#                 print(f"DEBUG: Execution time: {burr_data['time_ms']:.2f} ms")
                
#                 result['measurements'].update({
#                     'burr': {
#                         'count': burr_data['burr_count'],
#                         'status': burr_data['burr_status'],
#                         'position': 'ID' if burr_data['burr_count'] > 0 else 'None'
#                     },
#                     'execution_time': burr_data['time_ms']
#                 })

#                 print("DEBUG: Saving result image...")
#                 save_result = dt.save_burr_result_image(
#                     processed["image"], burr_data, output_folder
#                 )
#                 result['image_path'] = save_result['output_path']
#                 print(f"DEBUG: Result image saved at: {result['image_path']}")
#             else:
#                 raise ValueError("Burr detection not implemented for this part.")

#             # Defect check and burr status determination
#             defect_lines = []
#             burr_present = False
            
#             if result['measurements']['burr']['status'] == "NOK":
#                 defect_lines.append("Burr detected")
#                 burr_present = True

#             burr_count = result['measurements']['burr']['count']
#             burr_status = result['measurements']['burr']['status']
#             defect_position = result['measurements']['burr']['position']
#             execution_time = result['measurements']['execution_time']
#             output_path = result['image_path']
            
#             # Written burr status - Clear indication of burr presence
#             burr_written_status = "BURR PRESENT" if burr_present else "NO BURR"

#             print("DEBUG: Preparing final output...")
#             # Print output with enhanced burr status
#             print("r")
#             print("Result:", "NOK" if defect_lines else "OK")
#             if defect_lines:
#                 print("Error:", ", ".join(defect_lines))
#             else:
#                 print("Error: None")
#             print(f"Burr: {burr_status}")
#             print(f"Burr Status: {burr_written_status}")
#             print(f"burr_count: {burr_count}")
#             print(f"defect_position: {defect_position}")
#             print(f"execution_time: {execution_time:.2f} ms")
#             print(f"Output path: {output_path}")

#             return (
#                 "r",
#                 f"{'NOK' if defect_lines else 'OK'}",
#                 f"{', '.join(defect_lines)}" if defect_lines else "None",
#                 f"{burr_status}",
#                 f"{burr_count}",
#             )

#         except Exception as e:
#             print(f"DEBUG: Exception occurred in main processing: {str(e)}")
#             print("r")
#             print("Result: NOK")
#             print("Error:", str(e))
#             print("Burr: NOK")
#             print("Burr Status: BURR PRESENT")
#             print("burr_count: 0")
#             print("defect_position: None")
#             print("execution_time: 0.0 ms")
#             print("Output path: None")
#             return (
#                 "e", "NOK", str(e),
#                 "Burr: NOK", "Burr Status: BURR PRESENT", "burr_count: 0", "defect_position: None", 
#                 "execution_time: 0.0 ms", "Output path: None"
#             )


























# #  old 13_9_2025
# # using above changes update below code also 


# import station_3_defect as dt
# import cv2
# import numpy as np

# def main(part, subpart, frame, ID2_OFFSET, HIGHLIGHT_SIZE, id_BURR_MIN_AREA, 
#          id_BURR_MAX_AREA, id_BURR_MIN_PERIMETER, id_BURR_MAX_PERIMETER, output_folder):
    
#     # print(f"DEBUG: Starting main processing for part: {part}, subpart: {subpart}")  # Debug: Function entry
    
#     # Check if part is in the excluded list - parts that don't require burr detection
#     excluded_parts = [
#         "PISTON", "TEFLON PISTON RING", "OIL SEAL", "SPACER", "O RING", 
#         "PISTON RING", "TEFLON RING", "GUIDE END", "SEPARATING PISTON", "NRV SEAL"
#     ]
    
#     if part in excluded_parts:
#         # print(f"DEBUG: Part '{part}' is excluded from burr detection. Returning NA statuses.")  # Debug: Exclusion logic
#         # For excluded parts, return NA values for all outputs without processing
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
#         # Process only for non-excluded parts
#         # Convert string parameters to appropriate types with error handling
#         try:
#             # print("DEBUG: Converting string parameters to integers...")  # Debug: Parameter conversion start
#             ID2_OFFSET = int(ID2_OFFSET) if ID2_OFFSET != "NA" else None
#             HIGHLIGHT_SIZE = int(HIGHLIGHT_SIZE) if HIGHLIGHT_SIZE != "NA" else None
#             id_BURR_MIN_AREA = int(id_BURR_MIN_AREA) if id_BURR_MIN_AREA != "NA" else None
#             id_BURR_MAX_AREA = int(id_BURR_MAX_AREA) if id_BURR_MAX_AREA != "NA" else None
#             id_BURR_MIN_PERIMETER = int(id_BURR_MIN_PERIMETER) if id_BURR_MIN_PERIMETER != "NA" else None
#             id_BURR_MAX_PERIMETER = int(id_BURR_MAX_PERIMETER) if id_BURR_MAX_PERIMETER != "NA" else None
#             # print("DEBUG: Converted parameters to integers successfully.")  # Debug: Conversion success
#             # print(f"DEBUG: Converted values - ID2_OFFSET: {ID2_OFFSET}, HIGHLIGHT_SIZE: {HIGHLIGHT_SIZE}")  # Debug: Values confirmation
#         except ValueError as e:
#             print(f"DEBUG: Parameter conversion error: {e}")  # Debug: Conversion error
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

#         # Initialize result structure for storing processing outcomes
#         result = {
#             'resultType': 'r',
#             'result': 'OK',
#             'errorType': None,
#             'image_path': None,
#             'measurements': {
#                 'burr': {'count': 0, 'status': 'OK', 'position': 'None'},
#                 'execution_time': 0.0
#             }
#         }
#         # print("DEBUG: Initialized result structure")  # Debug: Structure initialization

#         try:
#             print("DEBUG: Starting preprocessing of image...")  # Debug: Preprocessing start
#             processed = dt.preprocess_image(frame, output_folder)
#             print(f"DEBUG: Contours found during preprocessing: {len(processed['sorted_contours'])}")  # Debug: Contour count
#             print(f"DEBUG: ID contour found: {processed.get('id_contour') is not None}")  # Debug: ID contour status
#             print(f"DEBUG: OD contour found: {processed.get('od_contour') is not None}")  # Debug: OD contour status
            
#             if len(processed["sorted_contours"]) < 1:
#                 raise ValueError("Not enough contours found for burr detection")
#             contours = processed["sorted_contours"]

#             # Burr detection logic for specific parts only
#             burr_detect_parts = [
#                 "SUPPORT PISTON RING", "SUPPORT PISTON", "NRV WASHER", "WASHER"
#             ]
            
#             if part in burr_detect_parts:
#                 # print(f"DEBUG: Part '{part}' is eligible for burr detection. Running detection algorithm...")  # Debug: Eligibility check
#                 # Pass the identified contours to detect_burr function
#                 burr_data = dt.detect_burr(
#                     frame, contours, 
#                     ID2_OFFSET=ID2_OFFSET,
#                     HIGHLIGHT_SIZE=HIGHLIGHT_SIZE,
#                     id_BURR_MIN_AREA=id_BURR_MIN_AREA,
#                     id_BURR_MAX_AREA=id_BURR_MAX_AREA,
#                     id_BURR_MIN_PERIMETER=id_BURR_MIN_PERIMETER,
#                     id_BURR_MAX_PERIMETER=id_BURR_MAX_PERIMETER,
#                     output_folder=output_folder,
#                     # Pass the pre-identified contours for green visualization
#                     id_contour=processed.get("id_contour"),
#                     od_contour=processed.get("od_contour")
#                 )
#                 # print(f"DEBUG: Burr detection completed - Count: {burr_data['burr_count']}, Status: {burr_data['burr_status']}")  # Debug: Detection results
#                 # print(f"DEBUG: Execution time: {burr_data['time_ms']:.2f} ms")  # Debug: Performance metric
                
#                 result['measurements'].update({
#                     'burr': {
#                         'count': burr_data['burr_count'],
#                         'status': burr_data['burr_status'],
#                         'position': 'ID' if burr_data['burr_count'] > 0 else 'None'
#                     },
#                     'execution_time': burr_data['time_ms']
#                 })

#                 # print("DEBUG: Saving result image...")  # Debug: Image saving start
#                 save_result = dt.save_burr_result_image(
#                     processed["image"], burr_data, output_folder
#                 )
#                 result['image_path'] = save_result['output_path']
#                 # print(f"DEBUG: Result image saved at: {result['image_path']}")  # Debug: Save confirmation
#             else:
#                 raise ValueError("Burr detection not implemented for this part.")

#             # Defect check and burr status determination
#             defect_lines = []
#             burr_present = False
            
#             if result['measurements']['burr']['status'] == "NOK":
#                 defect_lines.append("Burr detected")
#                 burr_present = True

#             burr_count = result['measurements']['burr']['count']
#             burr_status = result['measurements']['burr']['status']
#             defect_position = result['measurements']['burr']['position']
#             execution_time = result['measurements']['execution_time']
#             output_path = result['image_path']
            
#             # Written burr status - Clear indication of burr presence
#             burr_written_status = "BURR PRESENT" if burr_present else "NO BURR"

#             # print("DEBUG: Preparing final output...")  # Debug: Output preparation
#             # Print output with enhanced burr status
#             print("r")
#             print("Result:", "NOK" if defect_lines else "OK")
#             if defect_lines:
#                 print("Error:", ", ".join(defect_lines))
#             else:
#                 print("Error: None")
#             print(f"Burr: {burr_status}")
#             print(f"Burr Status: {burr_written_status}")
#             print(f"burr_count: {burr_count}")
#             print(f"defect_position: {defect_position}")
#             print(f"execution_time: {execution_time:.2f} ms")
#             print(f"Output path: {output_path}")

#             return (
#                 "r",
#                 f"{'NOK' if defect_lines else 'OK'}",
#                 f"{', '.join(defect_lines)}" if defect_lines else "None",
#                 f"{burr_status}",
#                 #f"{burr_written_status}",
#                 f"{burr_count}",
#                # f"defect_position: {defect_position}",
#               #  f"execution_time: {execution_time:.2f} ms",
#               #  f"Output path: {output_path}"
#             )

#         except Exception as e:
#             # print(f"DEBUG: Exception occurred in main processing: {str(e)}")  # Debug: Exception details
#             print("r")
#             print("Result: NOK")
#             print("Error:", str(e))
#             print("Burr: NOK")
#             print("Burr Status: BURR PRESENT")
#             print("burr_count: 0")
#             print("defect_position: None")
#             print("execution_time: 0.0 ms")
#             print("Output path: None")
#             return (
#                 "e", "NOK", str(e),
#                 "Burr: NOK", "Burr Status: BURR PRESENT", "burr_count: 0", "defect_position: None", 
#                 "execution_time: 0.0 ms", "Output path: None"
#             )
