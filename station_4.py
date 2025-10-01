
# code 2

# updated 20_9_2025 (adds circularity/aspect ratio plumbing)
# updated 23_9_2025 (adds ID/OD parameter split, combined overlay, and cropped single-image save as cam3_bmp.bmp)
import station_4_defect as dt
import cv2
import numpy as np
import os

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

    print(f"DEBUG: Starting main processing for part: {part}, subpart: {subpart}")
    print(f"DEBUG: ID Area Range: {min_id_area}-{max_id_area}, OD Area Range: {min_od_area}-{max_od_area}")
    print(f"DEBUG: Shape filters -> circularity: {min_circularity}-{max_circularity}, aspect_ratio: {min_aspect_ratio}-{max_aspect_ratio}")

    excluded_parts = [
        "PISTON", "TEFLON PISTON RING", "OIL SEAL", "SPACER", "O RING",
        "PISTON RING", "TEFLON RING", "GUIDE END", "SEPARATING PISTON", "NRV SEAL"
    ]

    if part in excluded_parts:
        # Fallback write of original as cam4_bmp.bmp for excluded parts
        try:
            os.makedirs(output_folder, exist_ok=True)
            if frame is not None:
                fallback_path = os.path.join(output_folder, "cam4_bmp.bmp")
                ok = cv2.imwrite(fallback_path, frame)
                print(f"Excluded-part fallback write to {fallback_path}: {ok}")
        except Exception as _e:
            print(f"Excluded-part fallback write error: {_e}")

        print(f"DEBUG: Part '{part}' is excluded from burr detection. Returning NA statuses.")
        print("r")
        print("Result: NA")
        print("Error: NA")
        print("Burr: NA")
        print("Burr Status: NA")
        print("burr_count: NA")
        print("defect_position: NA")
        print("execution_time: NA")
        print("Output path: NA")
        return (
            "r", "Result: NA", "Error: NA",
            "Burr: NA", "Burr Status: NA", "burr_count: NA", "defect_position: NA",
            "execution_time: NA", "Output path: NA"
        )
    else:
        try:
            print("DEBUG: Converting string parameters to numbers...")
            # ID params
            ID2_OFFSET_ID = int(ID2_OFFSET_ID) if ID2_OFFSET_ID != "NA" else None
            HIGHLIGHT_SIZE_ID = int(HIGHLIGHT_SIZE_ID) if HIGHLIGHT_SIZE_ID != "NA" else None
            ID_BURR_MIN_AREA = int(ID_BURR_MIN_AREA) if ID_BURR_MIN_AREA != "NA" else None
            ID_BURR_MAX_AREA = int(ID_BURR_MAX_AREA) if ID_BURR_MAX_AREA != "NA" else None
            ID_BURR_MIN_PERIMETER = int(ID_BURR_MIN_PERIMETER) if ID_BURR_MIN_PERIMETER != "NA" else None
            ID_BURR_MAX_PERIMETER = int(ID_BURR_MAX_PERIMETER) if ID_BURR_MAX_PERIMETER != "NA" else None
            # OD params
            ID2_OFFSET_OD = int(ID2_OFFSET_OD) if ID2_OFFSET_OD != "NA" else None
            HIGHLIGHT_SIZE_OD = int(HIGHLIGHT_SIZE_OD) if HIGHLIGHT_SIZE_OD != "NA" else None
            OD_BURR_MIN_AREA = int(OD_BURR_MIN_AREA) if OD_BURR_MIN_AREA != "NA" else None
            OD_BURR_MAX_AREA = int(OD_BURR_MAX_AREA) if OD_BURR_MAX_AREA != "NA" else None
            OD_BURR_MIN_PERIMETER = int(OD_BURR_MIN_PERIMETER) if OD_BURR_MIN_PERIMETER != "NA" else None
            OD_BURR_MAX_PERIMETER = int(OD_BURR_MAX_PERIMETER) if OD_BURR_MAX_PERIMETER != "NA" else None

            # Area and shape
            min_id_area = int(min_id_area) if min_id_area != "NA" else None
            max_id_area = int(max_id_area) if max_id_area != "NA" else None
            min_od_area = int(min_od_area) if min_od_area != "NA" else None
            max_od_area = int(max_od_area) if max_od_area != "NA" else None
            min_circularity = float(min_circularity) if min_circularity != "NA" else None
            max_circularity = float(max_circularity) if max_circularity != "NA" else None
            min_aspect_ratio = float(min_aspect_ratio) if min_aspect_ratio != "NA" else None
            max_aspect_ratio = float(max_aspect_ratio) if max_aspect_ratio != "NA" else None

            print("DEBUG: Converted parameters OK.")
            print(f"DEBUG: ID -> offset={ID2_OFFSET_ID}, highlight={HIGHLIGHT_SIZE_ID}, area={ID_BURR_MIN_AREA}-{ID_BURR_MAX_AREA}, perim={ID_BURR_MIN_PERIMETER}-{ID_BURR_MAX_PERIMETER}")
            print(f"DEBUG: OD -> offset={ID2_OFFSET_OD}, highlight={HIGHLIGHT_SIZE_OD}, area={OD_BURR_MIN_AREA}-{OD_BURR_MAX_AREA}, perim={OD_BURR_MIN_PERIMETER}-{OD_BURR_MAX_PERIMETER}")
        except ValueError as e:
            # On conversion error, attempt fallback write
            try:
                os.makedirs(output_folder, exist_ok=True)
                if frame is not None:
                    fallback_path = os.path.join(output_folder, "cam4_bmp.bmp")
                    ok = cv2.imwrite(fallback_path, frame)
                    print(f"Fallback write (param error) to {fallback_path}: {ok}")
            except Exception as _e:
                print(f"Fallback write error (param error): {_e}")

            print(f"DEBUG: Parameter conversion error: {e}")
            print("r")
            print("Result: NOK")
            print("Error: parameter_conversion")
            print("Burr: NOK")
            print("Burr Status: BURR PRESENT")
            print("burr_count: 0")
            print("defect_position: None")
            print("execution_time: 0.0 ms")
            return (
                "e", "NOK", "parameter_conversion",
                "Burr: NOK", "Burr Status: BURR PRESENT", "burr_count: 0", "defect_position: None",
                "execution_time: 0.0 ms", "Output path: None"
            )

        print("DEBUG: Preprocessing with area + shape filters...")
        processed = dt.preprocess_image(
            frame,
            min_id_area=min_id_area, max_id_area=max_id_area,
            min_od_area=min_od_area, max_od_area=max_od_area,
            min_circularity=min_circularity, max_circularity=max_circularity,
            min_aspect_ratio=min_aspect_ratio, max_aspect_ratio=max_aspect_ratio,
            output_folder=output_folder
        )
        print(f"DEBUG: Contours found: {len(processed['sorted_contours'])}")
        print(f"DEBUG: ID contour found: {processed.get('id_contour') is not None}")
        print(f"DEBUG: OD contour found: {processed.get('od_contour') is not None}")

        if len(processed["sorted_contours"]) < 1:
            print("r"); print("Result: NOK"); print("Error: not_enough_contours")
            return {"resultType": "e", "error": "not_enough_contours"}

        # Run ID+OD burr detection with separate parameter sets
        det = dt.detect_burr_both(
            frame, processed["sorted_contours"],
            id_offset=ID2_OFFSET_ID, id_highlight=HIGHLIGHT_SIZE_ID,
            id_burr_area_min=ID_BURR_MIN_AREA, id_burr_area_max=ID_BURR_MAX_AREA,
            id_burr_perim_min=ID_BURR_MIN_PERIMETER, id_burr_perim_max=ID_BURR_MAX_PERIMETER,
            od_offset=ID2_OFFSET_OD, od_highlight=HIGHLIGHT_SIZE_OD,
            od_burr_area_min=OD_BURR_MIN_AREA, od_burr_area_max=OD_BURR_MAX_AREA,
            od_burr_perim_min=OD_BURR_MIN_PERIMETER, od_burr_perim_max=OD_BURR_MAX_PERIMETER,
            min_id_area=min_id_area, max_id_area=max_id_area,
            min_od_area=min_od_area, max_od_area=max_od_area,
            min_circularity=min_circularity, max_circularity=max_circularity,
            min_aspect_ratio=min_aspect_ratio, max_aspect_ratio=max_aspect_ratio,
            output_folder=output_folder,
            id_contour=processed.get("id_contour"),
            od_contour=processed.get("od_contour")
        )

        # Prepare paths
        id_path = os.path.join(output_folder, "cam4_id.bmp")
        od_path = os.path.join(output_folder, "cam4_od.bmp")
        combined_full_path = os.path.join(output_folder, "cam4_combined.bmp")
        combined_both_crop_path = os.path.join(output_folder, "cam4_bmp.bmp")  # single image containing both, cropped
        combined_id_crop_path = os.path.join(output_folder, "cam4_combined_id.bmp")
        combined_od_crop_path = os.path.join(output_folder, "cam4_combined_od.bmp")

        # Ensure folder exists
        os.makedirs(output_folder, exist_ok=True)

        # cv2.imwrite(id_path, det["id"]["burr_output_image"] if det["id"]["burr_output_image"] is not None else processed["image"])
        # cv2.imwrite(od_path, det["od"]["burr_output_image"] if det["od"]["burr_output_image"] is not None else processed["image"])
        # cv2.imwrite(combined_full_path, det.get("combined_output_image") if det.get("combined_output_image") is not None else processed["image"])

        # Write cam4_bmp; if annotated missing or write fails, fallback to original frame
        write_src = det.get("combined_output_image_both_crop") if det.get("combined_output_image_both_crop") is not None else det.get("combined_output_image")
        if write_src is None:
            write_src = processed["image"]
        write_ok = cv2.imwrite(combined_both_crop_path, write_src)
        if not write_ok:
            try:
                write_ok = cv2.imwrite(combined_both_crop_path, frame)
                print(f"Fallback write of original to {combined_both_crop_path}: {write_ok}")
            except Exception as _e:
                print(f"Fallback write error to {combined_both_crop_path}: {_e}")

        # cv2.imwrite(combined_id_crop_path, det.get("combined_output_image_id_crop") if det.get("combined_output_image_id_crop") is not None else processed["image"])
        # cv2.imwrite(combined_od_crop_path, det.get("combined_output_image_od_crop") if det.get("combined_output_image_od_crop") is not None else processed["image"])

        print("r")
        print(f"ID -> status: {det['id']['burr_status']}, count: {det['id']['burr_count']}, time_ms: {det['id'].get('time_ms', 0):.2f}, path: {id_path}")
        print(f"OD -> status: {det['od']['burr_status']}, count: {det['od']['burr_count']}, time_ms: {det['od'].get('time_ms', 0):.2f}, path: {od_path}")
        print(f"Combined (full): {combined_full_path}")
        print(f"Combined (both crop, cam4_bmp): {combined_both_crop_path}")
        print(f"Combined (ID crop): {combined_id_crop_path}")
        print(f"Combined (OD crop): {combined_od_crop_path}")

        # Final guard to ensure cam4_bmp.bmp exists
        try:
            if not os.path.exists(combined_both_crop_path):
                cv2.imwrite(combined_both_crop_path, frame)
                print(f"Final guard wrote original to {combined_both_crop_path}")
        except Exception as _e:
            print(f"Final guard write error: {_e}")

        return {
            "resultType": "r", "part": part, "subpart": subpart,
            "id": {"status": det["id"]["burr_status"], "count": det["id"]["burr_count"],
                   "time_ms": det["id"].get('time_ms', 0.0), "image_path": id_path},
            "od": {"status": det["od"]["burr_status"], "count": det["od"]["burr_count"],
                   "time_ms": det["od"].get('time_ms', 0.0), "image_path": od_path},
            "combined_image_path": combined_full_path,
            "combined_image_both_crop_path": combined_both_crop_path,
            "combined_image_id_crop_path": combined_id_crop_path,
            "combined_image_od_crop_path": combined_od_crop_path,
        }















#### working 30 sep 25


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

#         # Comment/uncomment to control which artifacts are saved (single-line cv2.imwrite for easy toggling) [imwrite]
#         # cv2.imwrite(id_path, det["id"]["burr_output_image"] if det["id"]["burr_output_image"] is not None else processed["image"])
#         # cv2.imwrite(od_path, det["od"]["burr_output_image"] if det["od"]["burr_output_image"] is not None else processed["image"])
#         # cv2.imwrite(combined_full_path, det.get("combined_output_image") if det.get("combined_output_image") is not None else processed["image"])
#         cv2.imwrite(combined_both_crop_path, det.get("combined_output_image_both_crop") if det.get("combined_output_image_both_crop") is not None else det.get("combined_output_image"))
#         # cv2.imwrite(combined_id_crop_path, det.get("combined_output_image_id_crop") if det.get("combined_output_image_id_crop") is not None else processed["image"])
#         # cv2.imwrite(combined_od_crop_path, det.get("combined_output_image_od_crop") if det.get("combined_output_image_od_crop") is not None else processed["image"])

#         print("r")
#         print(f"ID -> status: {det['id']['burr_status']}, count: {det['id']['burr_count']}, time_ms: {det['id'].get('time_ms', 0):.2f}, path: {id_path}")
#         print(f"OD -> status: {det['od']['burr_status']}, count: {det['od']['burr_count']}, time_ms: {det['od'].get('time_ms', 0):.2f}, path: {od_path}")
#         print(f"Combined (full): {combined_full_path}")
#         print(f"Combined (both crop, cam4_bmp): {combined_both_crop_path}")
#         print(f"Combined (ID crop): {combined_id_crop_path}")
#         print(f"Combined (OD crop): {combined_od_crop_path}")

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



















