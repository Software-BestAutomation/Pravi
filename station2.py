# code 2

import station_2_defect as dt
import cv2
import numpy as np
import os 
from PIL import Image

def main(part, subpart, frame, thick_min, thick_max, pixel_to_micron, output_folder, min_thresh=50, max_thresh=255):
    # Check if part is in the excluded list
    excluded_parts = ["PISTON", "GUIDE END", "SEPARATING PISTON", "NRV SEAL"]

    print(f"Part: {part}, SubPart: {subpart}, frame: {frame}, Thick_min:{thick_min}, thick_max: {thick_max}, pixel_to_micron: {pixel_to_micron}, output_folder: {output_folder}, min_thresh: {min_thresh}, max_thresh: {max_thresh}")
    
    if part in excluded_parts:
        # For excluded parts, return NA values for all outputs without processing
        # Also ensure fallback write of original image as requested
        try:
            os.makedirs(output_folder, exist_ok=True)
            if frame is not None:
                fallback_path = os.path.join(output_folder, "cam2_bmp.bmp")
                ok = cv2.imwrite(fallback_path, frame)
                print(f"Excluded-part fallback write to {fallback_path}: {ok}")
        except Exception as _e:
            print(f"Excluded-part fallback write error: {_e}")

        print("r")
        print("Result: NA")
        print("Error: NA")
        print("Thickness: NA, Status: NA")
        print("flash_defect: NA")
        print("defect_position: NA")
        print("Output path: NA")
        return (
            "r", "Result: NA", "Error: NA",
            "Thickness: NA, Status: NA",
            "flash_defect: NA", "defect_position: NA", "Output path: NA"
        )
    else:
        # Process only for non-excluded parts
        # Convert string parameters to float
        try:
            thick_min = float(thick_min) if thick_min != "NA" else None
            thick_max = float(thick_max) if thick_max != "NA" else None
            pixel_to_micron = float(pixel_to_micron)
        except ValueError as e:
            # Fallback save on parameter conversion failure
            try:
                os.makedirs(output_folder, exist_ok=True)
                if frame is not None:
                    fallback_path = os.path.join(output_folder, "cam2_bmp.bmp")
                    ok = cv2.imwrite(fallback_path, frame)
                    print(f"Fallback write (param error) to {fallback_path}: {ok}")
            except Exception as _e:
                print(f"Fallback write error (param error): {_e}")

            print("r")
            print("Result: NOK")
            print("Error: parameter_conversion")
            print("Thickness: 0.0mm, Status: NOK")
            print("flash_defect: NOK")
            print("defect_position: None")
            return (
                "e", "NOK", "parameter_conversion",
                "Thickness: 0.0mm, Status: NOK",
                "flash_defect: NOK", "defect_position: None", "Output path: None"
            )
        
        # Parse and validate threshold parameters
        try:
            if min_thresh in (None, "NA", ""):
                print('Min thresh none passing it as 100')
                min_thr = 100
            else:
                min_thr = int(float(min_thresh))
                print('min  thresh taken from else:',min_thr)
            min_thr = max(0, min(255, min_thr))  # clamp to valid 8-bit range
            
            if max_thresh in (None, "NA", ""):
                max_thr = 255
            else:
                max_thr = int(float(max_thresh))
            max_thr = max(0, min(255, max_thr))  # clamp to valid 8-bit range
        except Exception:
            min_thr = 100  # robust defaults
            max_thr = 255

        result = {
            'resultType': 'r',
            'result': 'OK',
            'errorType': None,
            'image_path': None,
            'measurements': {
                'thickness': {'value': 0.0, 'status': 'OK'},
                'flash': {'result': 'OK', 'position': 'None'}
            }
        }
        try:
            processed = dt.preprocess_image(frame, output_folder, min_thresh=min_thr, max_thresh=max_thr)
            if len(processed["sorted_contours"]) < 1:
                raise ValueError("Not enough contours found for thickness measurement")
            contours = processed["sorted_contours"]
            
            # Thickness measurement logic for specific parts
            thickness_measure_parts = [
                "TEFLON PISTON RING", "SUPPORT PISTON RING", "SUPPORT PISTON", 
                "OIL SEAL", "SPACER", "O RING", "NRV WASHER", 
                "WASHER", "PISTON RING", "TEFLON RING"
            ]
            if part in thickness_measure_parts:
                thickness_data = dt.measure_thickness(
                    frame, contours, thick_min, thick_max, pixel_to_micron
                )
                flash = dt.flash_detection_thickness(frame, contours, output_folder)
                result['measurements'].update({
                    'thickness': {
                        'value': thickness_data['thickness_mm'],
                        'status': thickness_data['thickness_status']
                    },
                    'flash': {
                        'result': flash['Defect_Result'],
                        'position': flash['defect_position']
                    }
                })
                save_result = dt.save_thickness_result_image(
                    processed["image"], thickness_data, flash, output_folder
                )
                result['image_path'] = save_result['output_path']

                # Fallback if save failed
                if not save_result.get('success') or not save_result.get('output_path'):
                    try:
                        os.makedirs(output_folder, exist_ok=True)
                        fallback_path = os.path.join(output_folder, "cam2_bmp.bmp")
                        ok = cv2.imwrite(fallback_path, frame)
                        result['image_path'] = fallback_path if ok else None
                        print(f"Fallback write after save failure to {fallback_path}: {ok}")
                    except Exception as _e:
                        print(f"Fallback write error after save failure: {_e}")
            else:
                raise ValueError("Thickness measurement not implemented for this part.")
            
            # Defect check
            defect_lines = []
            if result['measurements']['thickness']['status'] == "NOK":
                defect_lines.append("Thickness dimension")
            if result['measurements']['flash']['result'] != "OK":
                defect_lines.append(
                    f"Flash on {result['measurements']['flash']['position']}"
                )
            
            thickness_mm = result['measurements']['thickness']['value']
            thickness_status = result['measurements']['thickness']['status']
            flash_defect = result['measurements']['flash']['result']
            defect_position = result['measurements']['flash']['position']
            output_path = result['image_path']
            
            # Print output
            print("r")
            print("Result:", "NOK" if defect_lines else "OK")
            if defect_lines:
                print("Error:", ", ".join(defect_lines))
            else:
                print("Error: None")
            print(f"Thickness: {thickness_mm}mm, Status: {thickness_status}")
            print(f"flash_defect: {flash_defect}")
            print(f"defect_position: {defect_position}")
            print(f"Output path: {output_path}")

            # Final guard: ensure cam2_bmp.bmp exists
            try:
                os.makedirs(output_folder, exist_ok=True)
                cam2_path = os.path.join(output_folder, "cam2_bmp.bmp")
                if not os.path.exists(cam2_path) and frame is not None:
                    ok = cv2.imwrite(cam2_path, frame)
                    if not result['image_path']:
                        result['image_path'] = cam2_path if ok else None
                    print(f"Final guard wrote original to {cam2_path}: {ok}")
            except Exception as _e:
                print(f"Final guard write error: {_e}")

            return (
                "r",
                f"{'NOK' if defect_lines else 'OK'}",
                f"{', '.join(defect_lines)}" if defect_lines else "Error: None",
                f"{thickness_mm}mm, Status: {thickness_status}",
                f"{flash_defect}",
                f"{defect_position}",
                f"{output_path}"
            )
        except Exception as e:
            # On any processing error, attempt fallback save
            try:
                os.makedirs(output_folder, exist_ok=True)
                if frame is not None:
                    fallback_path = os.path.join(output_folder, "cam2_bmp.bmp")
                    ok = cv2.imwrite(fallback_path, frame)
                    print(f"Fallback write (exception path) to {fallback_path}: {ok}")
            except Exception as _e:
                print(f"Fallback write error (exception path): {_e}")

            print("r")
            print("Result: NOK")
            print("Error:", str(e))
            print("Thickness: 0.0mm, Status: NOK")
            print("flash_defect: NOK")
            print("defect_position: None")
            print("Output path: None")
            return (
                "e", "NOK", str(e),
                "Thickness: 0.0mm, Status: NOK",
                "flash_defect: NOK", "defect_position: None", "Output path: None"
            )
















### working 30 sep 25

# import station_2_defect as dt
# import cv2
# import numpy as np
# import os 
# from PIL import Image

# def main(part, subpart, frame, thick_min, thick_max, pixel_to_micron, output_folder, min_thresh=None, max_thresh=None):
#     # Check if part is in the excluded list
#     excluded_parts = ["PISTON", "GUIDE END", "SEPARATING PISTON", "NRV SEAL"]
    
#     if part in excluded_parts:
#         # For excluded parts, return NA values for all outputs without processing
#         print("r")
#         print("Result: NA")
#         print("Error: NA")
#         print("Thickness: NA, Status: NA")
#         print("flash_defect: NA")
#         print("defect_position: NA")
#         print("Output path: NA")
#         return (
#             "r", "Result: NA", "Error: NA",
#             "Thickness: NA, Status: NA",
#             "flash_defect: NA", "defect_position: NA", "Output path: NA"
#         )
#     else:
#         # Process only for non-excluded parts
#         # Convert string parameters to float
#         try:
#             thick_min = float(thick_min) if thick_min != "NA" else None
#             thick_max = float(thick_max) if thick_max != "NA" else None
#             pixel_to_micron = float(pixel_to_micron)
#         except ValueError as e:
#             print("r")
#             print("Result: NOK")
#             print("Error: parameter_conversion")
#             print("Thickness: 0.0mm, Status: NOK")
#             print("flash_defect: NOK")
#             print("defect_position: None")
#             return (
#                 "e", "NOK", "parameter_conversion",
#                 "Thickness: 0.0mm, Status: NOK",
#                 "flash_defect: NOK", "defect_position: None", "Output path: None"
#             )
        
#         # Parse and validate threshold parameters
#         try:
#             if min_thresh in (None, "NA", ""):
#                 min_thr = 100
#             else:
#                 min_thr = int(float(min_thresh))
#             min_thr = max(0, min(255, min_thr))  # clamp to valid 8-bit range
            
#             if max_thresh in (None, "NA", ""):
#                 max_thr = 255
#             else:
#                 max_thr = int(float(max_thresh))
#             max_thr = max(0, min(255, max_thr))  # clamp to valid 8-bit range
#         except Exception:
#             min_thr = 100  # robust defaults
#             max_thr = 255

#         result = {
#             'resultType': 'r',
#             'result': 'OK',
#             'errorType': None,
#             'image_path': None,
#             'measurements': {
#                 'thickness': {'value': 0.0, 'status': 'OK'},
#                 'flash': {'result': 'OK', 'position': 'None'}
#             }
#         }
#         try:
#             processed = dt.preprocess_image(frame, output_folder, min_thresh=min_thr, max_thresh=max_thr)
#             if len(processed["sorted_contours"]) < 1:
#                 raise ValueError("Not enough contours found for thickness measurement")
#             contours = processed["sorted_contours"]
            
#             # Thickness measurement logic for specific parts
#             thickness_measure_parts = [
#                 "TEFLON PISTON RING", "SUPPORT PISTON RING", "SUPPORT PISTON", 
#                 "OIL SEAL", "SPACER", "O RING", "NRV WASHER", 
#                 "WASHER", "PISTON RING", "TEFLON RING"
#             ]
#             if part in thickness_measure_parts:
#                 thickness_data = dt.measure_thickness(
#                     frame, contours, thick_min, thick_max, pixel_to_micron
#                 )
#                 flash = dt.flash_detection_thickness(frame, contours, output_folder)
#                 result['measurements'].update({
#                     'thickness': {
#                         'value': thickness_data['thickness_mm'],
#                         'status': thickness_data['thickness_status']
#                     },
#                     'flash': {
#                         'result': flash['Defect_Result'],
#                         'position': flash['defect_position']
#                     }
#                 })
#                 save_result = dt.save_thickness_result_image(
#                     processed["image"], thickness_data, flash, output_folder
#                 )
#                 result['image_path'] = save_result['output_path']
#             else:
#                 raise ValueError("Thickness measurement not implemented for this part.")
            
#             # Defect check
#             defect_lines = []
#             if result['measurements']['thickness']['status'] == "NOK":
#                 defect_lines.append("Thickness dimension")
#             if result['measurements']['flash']['result'] != "OK":
#                 defect_lines.append(
#                     f"Flash on {result['measurements']['flash']['position']}"
#                 )
            
#             thickness_mm = result['measurements']['thickness']['value']
#             thickness_status = result['measurements']['thickness']['status']
#             flash_defect = result['measurements']['flash']['result']
#             defect_position = result['measurements']['flash']['position']
#             output_path = result['image_path']
            
#             # Print output
#             print("r")
#             print("Result:", "NOK" if defect_lines else "OK")
#             if defect_lines:
#                 print("Error:", ", ".join(defect_lines))
#             else:
#                 print("Error: None")
#             print(f"Thickness: {thickness_mm}mm, Status: {thickness_status}")
#             print(f"flash_defect: {flash_defect}")
#             print(f"defect_position: {defect_position}")
#             print(f"Output path: {output_path}")
#             return (
#                 "r",
#                 f"{'NOK' if defect_lines else 'OK'}",
#                 f"{', '.join(defect_lines)}" if defect_lines else "Error: None",
#                 f"{thickness_mm}mm, Status: {thickness_status}",
#                 f"{flash_defect}",
#                 f"{defect_position}",
#                 f"{output_path}"
#             )
#         except Exception as e:
#             print("r")
#             print("Result: NOK")
#             print("Error:", str(e))
#             print("Thickness: 0.0mm, Status: NOK")
#             print("flash_defect: NOK")
#             print("defect_position: None")
#             print("Output path: None")
#             return (
#                 "e", "NOK", str(e),
#                 "Thickness: 0.0mm, Status: NOK",
#                 "flash_defect: NOK", "defect_position: None", "Output path: None"
#             )







