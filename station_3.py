# code 2
# station_3.py - combine ID & OD
# Changes:
# - Fix numpy array truth evaluation error by explicit checks on None and size.
# - Add backup_output_folder param to save timestamped backup copies of cam3_bmp.
# - Legacy cam3_bmp.bmp output path unchanged.

import station_3_defect as dt
import cv2
import os
from datetime import datetime

def _parse_num(val, typ):
    if val == "NA" or val is None:
        return None
    return typ(val)

def _write_backup(image, filename, backup_output_folder):
    try:
        if backup_output_folder:
            os.makedirs(backup_output_folder, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{os.path.splitext(filename)[0]}_{ts}.bmp"
            backup_path = os.path.join(backup_output_folder, backup_name)
            cv2.imwrite(backup_path, image)
            print(f"Backup copy saved to: {backup_path}")
    except Exception as e:
        print(f"Backup file error: {e}")

def main(part, subpart, frame,
         ID2_OFFSET_ID, HIGHLIGHT_SIZE_ID,
         ID_BURR_MIN_AREA, ID_BURR_MAX_AREA,
         ID_BURR_MIN_PERIMETER, ID_BURR_MAX_PERIMETER,
         ID2_OFFSET_OD, HIGHLIGHT_SIZE_OD,
         OD_BURR_MIN_AREA, OD_BURR_MAX_AREA,
         OD_BURR_MIN_PERIMETER, OD_BURR_MAX_PERIMETER,
         min_id_area, max_id_area,
         min_od_area, max_od_area,
         min_circularity, max_circularity,
         min_aspect_ratio, max_aspect_ratio,
         output_folder,
         backup_output_folder=None):  # New backup path param

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

        min_id_area = int(min_id_area) if min_id_area is not None else None
        max_id_area = int(max_id_area) if max_id_area is not None else None
        min_od_area = int(min_od_area) if min_od_area is not None else None
        max_od_area = int(max_od_area) if max_od_area is not None else None
        min_circularity = float(min_circularity) if min_circularity is not None else None
        max_circularity = float(max_circularity) if max_circularity is not None else None
        min_aspect_ratio = float(min_aspect_ratio) if min_aspect_ratio is not None else None
        max_aspect_ratio = float(max_aspect_ratio) if max_aspect_ratio is not None else None
    except Exception:
        print("r")
        print("Result: NOK")
        print("Error: parameter_conversion")
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
        print("r")
        print("Result: NOK")
        print("Error: not_enough_contours")
        return {"resultType": "e", "error": "not_enough_contours"}

    det = dt.detect_burr_both(
        frame, processed["sorted_contours"],
        id_offset, id_high, id_ba_min, id_ba_max,
        id_bp_min, id_bp_max,
        od_offset, od_high, od_ba_min, od_ba_max,
        od_bp_min, od_bp_max,
        min_id_area=min_id_area, max_id_area=max_id_area,
        min_od_area=min_od_area, max_od_area=max_od_area,
        min_circularity=min_circularity, max_circularity=max_circularity,
        min_aspect_ratio=min_aspect_ratio, max_aspect_ratio=max_aspect_ratio,
        output_folder=output_folder,
        id_contour=processed.get("id_contour"),
        od_contour=processed.get("od_contour")
    )

    combined_both_crop_path = os.path.join(output_folder, "cam3_bmp.bmp")

    # Fix: explicit None and .size checks to avoid ValueError on numpy arrays
    if det.get("combined_output_image_both_crop") is not None and det["combined_output_image_both_crop"].size > 0:
        write_src = det["combined_output_image_both_crop"]
    elif det.get("combined_output_image") is not None and det["combined_output_image"].size > 0:
        write_src = det["combined_output_image"]
    else:
        write_src = processed["image"]

    write_ok = cv2.imwrite(combined_both_crop_path, write_src)
    if not write_ok:
        try:
            write_ok = cv2.imwrite(combined_both_crop_path, frame)
            print(f"Fallback write of original to {combined_both_crop_path}: {write_ok}")
        except Exception as e:
            print(f"Fallback write error to {combined_both_crop_path}: {e}")

    if backup_output_folder:
        _write_backup(write_src, "cam3_bmp.bmp", backup_output_folder)

    print("r")
    print(f"ID -> status: {det['id']['burr_status']}, count: {det['id']['burr_count']}, time_ms: {det['id'].get('time_ms', 0):.2f}, path: {os.path.join(output_folder, 'cam3_id.bmp')}")
    print(f"OD -> status: {det['od']['burr_status']}, count: {det['od']['burr_count']}, time_ms: {det['od'].get('time_ms', 0):.2f}, path: {os.path.join(output_folder, 'cam3_od.bmp')}")
    print(f"Combined (both crop, cam3_bmp): {combined_both_crop_path}")

    return {
        "resultType": "r", "part": part, "subpart": subpart,
        "id": {"status": det["id"]["burr_status"], "count": det["id"]["burr_count"], "time_ms": det["id"].get("time_ms", 0.0), "image_path": os.path.join(output_folder, "cam3_id.bmp")},
        "od": {"status": det["od"]["burr_status"], "count": det["od"]["burr_count"], "time_ms": det["od"].get("time_ms", 0.0), "image_path": os.path.join(output_folder, "cam3_od.bmp")},
        "combined_image_both_crop_path": combined_both_crop_path,
    }





# ### working 3 oct 25 
# # code 2
# # station_3.py   combine ID & OD
# # updated on 22_9_2025 (add saving of combined ID+OD overlay as cam3_combined.bmp; keep others)
# # updated on 22_9_2025 (save combined cropped overlays; keep all prior outputs unchanged)
# # updated on 23_9_2025 (save cropped combined ID+OD overlay as cam3_bmp.bmp using cv2.imwrite)
# import station_3_defect as dt
# import cv2
# import os  # needed for join when calling cv2.imwrite paths

# def _parse_num(val, typ):
#     if val == "NA" or val is None:
#         return None
#     return typ(val)

# def main(part, subpart, frame,
#          ID2_OFFSET_ID, HIGHLIGHT_SIZE_ID,
#          ID_BURR_MIN_AREA, ID_BURR_MAX_AREA, ID_BURR_MIN_PERIMETER, ID_BURR_MAX_PERIMETER,
#          ID2_OFFSET_OD, HIGHLIGHT_SIZE_OD,
#          OD_BURR_MIN_AREA, OD_BURR_MAX_AREA, OD_BURR_MIN_PERIMETER, OD_BURR_MAX_PERIMETER,
#          min_id_area, max_id_area, min_od_area, max_od_area,
#          min_circularity, max_circularity, min_aspect_ratio, max_aspect_ratio,
#          output_folder):

#     # 🔹 Print all argument names & values
#     print("========== Arguments Passed ==========")
#     for name, val in locals().items():
#         if name != "frame":  # frame might be an image array, too large to print
#             print(f"{name}: {val}")
#         else:
#             print(f"{name}: <image/frame of shape {getattr(frame, 'shape', 'unknown')}>")
#     print("======================================")

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
#         return {"resultType": "e", "error": "parameter_conversion"}

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
#         return {"resultType": "e", "error": "not_enough_contours"}

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
#     )

#     # Prepare file paths
#     id_path = os.path.join(output_folder, "cam3_id.bmp")
#     od_path = os.path.join(output_folder, "cam3_od.bmp")
#     combined_full_path = os.path.join(output_folder, "cam3_combined.bmp")
#     combined_both_crop_path = os.path.join(output_folder, "cam3_bmp.bmp")  # single image containing both, cropped
#     combined_id_crop_path = os.path.join(output_folder, "cam3_combined_id.bmp")
#     combined_od_crop_path = os.path.join(output_folder, "cam3_combined_od.bmp")

#     # Ensure folder exists, then save each output with cv2.imwrite (comment any line to disable writing that artifact)  [cv2.imwrite]
#     os.makedirs(output_folder, exist_ok=True)
#     # cv2.imwrite(id_path, det["id"]["burr_output_image"] if det["id"]["burr_output_image"] is not None else processed["image"])  # easy to comment out [imwrite]
#     # cv2.imwrite(od_path, det["od"]["burr_output_image"] if det["od"]["burr_output_image"] is not None else processed["image"])  # easy to comment out [imwrite]
#     # cv2.imwrite(combined_full_path, det.get("combined_output_image") if det.get("combined_output_image") is not None else processed["image"])  # [imwrite]

#     # Write cam3_bmp; if annotated is missing or write fails, fallback to original frame
#     write_src = det.get("combined_output_image_both_crop") if det.get("combined_output_image_both_crop") is not None else det.get("combined_output_image")
#     if write_src is None:
#         write_src = processed["image"]
#     write_ok = cv2.imwrite(combined_both_crop_path, write_src)
#     if not write_ok:
#         try:
#             write_ok = cv2.imwrite(combined_both_crop_path, frame)
#             print(f"Fallback write of original to {combined_both_crop_path}: {write_ok}")
#         except Exception as _e:
#             print(f"Fallback write error to {combined_both_crop_path}: {_e}")

#     # cv2.imwrite(combined_id_crop_path, det.get("combined_output_image_id_crop") if det.get("combined_output_image_id_crop") is not None else processed["image"])  # [imwrite]
#     # cv2.imwrite(combined_od_crop_path, det.get("combined_output_image_od_crop") if det.get("combined_output_image_od_crop") is not None else processed["image"])  # [imwrite]

#     print("r")
#     print(f"ID -> status: {det['id']['burr_status']}, count: {det['id']['burr_count']}, time_ms: {det['id'].get('time_ms', 0):.2f}, path: {id_path}")
#     print(f"OD -> status: {det['od']['burr_status']}, count: {det['od']['burr_count']}, time_ms: {det['od'].get('time_ms', 0):.2f}, path: {od_path}")
#     print(f"Combined (full): {combined_full_path}")
#     print(f"Combined (both crop, cam3_bmp): {combined_both_crop_path}")
#     print(f"Combined (ID crop): {combined_id_crop_path}")
#     print(f"Combined (OD crop): {combined_od_crop_path}")

#     # Final guard to ensure cam3_bmp.bmp exists
#     try:
#         if not os.path.exists(combined_both_crop_path):
#             cv2.imwrite(combined_both_crop_path, frame)
#             print(f"Final guard wrote original to {combined_both_crop_path}")
#     except Exception as _e:
#         print(f"Final guard write error: {_e}")

#     return {
#         "resultType": "r", "part": part, "subpart": subpart,
#         "id": {"status": det["id"]["burr_status"], "count": det["id"]["burr_count"],
#                "time_ms": det["id"].get("time_ms", 0.0), "image_path": id_path},
#         "od": {"status": det["od"]["burr_status"], "count": det["od"]["burr_count"],
#                "time_ms": det["od"].get("time_ms", 0.0), "image_path": od_path},
#         "combined_image_path": combined_full_path,
#         "combined_image_both_crop_path": combined_both_crop_path,
#         "combined_image_id_crop_path": combined_id_crop_path,
#         "combined_image_od_crop_path": combined_od_crop_path,
#     }

























# #### working 30sep25
# # station_3.py   combine ID & OD
# # updated on 22_9_2025 (add saving of combined ID+OD overlay as cam3_combined.bmp; keep others)
# # updated on 22_9_2025 (save combined cropped overlays; keep all prior outputs unchanged)
# # updated on 23_9_2025 (save cropped combined ID+OD overlay as cam3_bmp.bmp using cv2.imwrite)
# import station_3_defect as dt
# import cv2
# import os  # needed for join when calling cv2.imwrite paths

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
#         return {"resultType": "e", "error": "parameter_conversion"}

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
#         return {"resultType": "e", "error": "not_enough_contours"}

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
#     )

#     # Prepare file paths
#     id_path = os.path.join(output_folder, "cam3_id.bmp")
#     od_path = os.path.join(output_folder, "cam3_od.bmp")
#     combined_full_path = os.path.join(output_folder, "cam3_combined.bmp")
#     combined_both_crop_path = os.path.join(output_folder, "cam3_bmp.bmp")  # single image containing both, cropped
#     combined_id_crop_path = os.path.join(output_folder, "cam3_combined_id.bmp")
#     combined_od_crop_path = os.path.join(output_folder, "cam3_combined_od.bmp")

#     # Ensure folder exists, then save each output with cv2.imwrite (comment any line to disable writing that artifact)  [cv2.imwrite]
#     os.makedirs(output_folder, exist_ok=True)
#     # cv2.imwrite(id_path, det["id"]["burr_output_image"] if det["id"]["burr_output_image"] is not None else processed["image"])  # easy to comment out [imwrite]
#     # cv2.imwrite(od_path, det["od"]["burr_output_image"] if det["od"]["burr_output_image"] is not None else processed["image"])  # easy to comment out [imwrite]
#     # cv2.imwrite(combined_full_path, det.get("combined_output_image") if det.get("combined_output_image") is not None else processed["image"])  # [imwrite]
#     cv2.imwrite(combined_both_crop_path, det.get("combined_output_image_both_crop") if det.get("combined_output_image_both_crop") is not None else det.get("combined_output_image"))  # [imwrite]
#     # cv2.imwrite(combined_id_crop_path, det.get("combined_output_image_id_crop") if det.get("combined_output_image_id_crop") is not None else processed["image"])  # [imwrite]
#     # cv2.imwrite(combined_od_crop_path, det.get("combined_output_image_od_crop") if det.get("combined_output_image_od_crop") is not None else processed["image"])  # [imwrite]

#     print("r")
#     print(f"ID -> status: {det['id']['burr_status']}, count: {det['id']['burr_count']}, time_ms: {det['id'].get('time_ms', 0):.2f}, path: {id_path}")
#     print(f"OD -> status: {det['od']['burr_status']}, count: {det['od']['burr_count']}, time_ms: {det['od'].get('time_ms', 0):.2f}, path: {od_path}")
#     print(f"Combined (full): {combined_full_path}")
#     print(f"Combined (both crop, cam3_bmp): {combined_both_crop_path}")
#     print(f"Combined (ID crop): {combined_id_crop_path}")
#     print(f"Combined (OD crop): {combined_od_crop_path}")

#     return {
#         "resultType": "r", "part": part, "subpart": subpart,
#         "id": {"status": det["id"]["burr_status"], "count": det["id"]["burr_count"],
#                "time_ms": det["id"].get("time_ms", 0.0), "image_path": id_path},
#         "od": {"status": det["od"]["burr_status"], "count": det["od"]["burr_count"],
#                "time_ms": det["od"].get("time_ms", 0.0), "image_path": od_path},
#         "combined_image_path": combined_full_path,
#         "combined_image_both_crop_path": combined_both_crop_path,
#         "combined_image_id_crop_path": combined_id_crop_path,
#         "combined_image_od_crop_path": combined_od_crop_path,
#     }







