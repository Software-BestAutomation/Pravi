# code 2

# working 28/9/25
#  # changes because of support pistong ring part
# ## updated 20\9\2025  11:PM   upto 22_sep_25   
import defect as dt
import cv2
import numpy as np
import os  # needed for fallback writes

def safe_color_convert(image, conversion_code):
    """Safely convert image colors with channel checking"""
    if len(image.shape) == 2 or (len(image.shape) == 3 and image.shape[2] == 1):
        print("Input is grayscale, converting to BGR first")
        if len(image.shape) == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        else:
            image = cv2.cvtColor(image.squeeze(), cv2.COLOR_GRAY2BGR)
    try:
        result = cv2.cvtColor(image, conversion_code)
        return result
    except cv2.error as e:
        print(f"Conversion error: {e}")
        return image

def main(part, subpart, frame,
         id_min, id_max, od_min, od_max,
         concentricity_max, orifice_min, orifice_max,
         threshold_id2, threshold_id3, threshold_od2, threshold_od3,
         pixel_to_micron, pixel_to_micron_id, pixel_to_micron_od,
         output_folder):
    
    # Convert string parameters to float 
    try:
        print("type of id min:",type(id_min))
        print('frame in  station 1:', frame)
        print(f"Original frame shape: {frame.shape}")
        if len(frame.shape) == 2:
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
            print("Converted grayscale frame to BGR")
        elif len(frame.shape) == 3 and frame.shape[2] == 1:
            frame = cv2.cvtColor(frame.squeeze(), cv2.COLOR_GRAY2BGR)
            print("Converted single-channel frame to BGR")
        elif len(frame.shape) == 3 and frame.shape[2] == 4:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            print("Converted BGRA frame to BGR")
        print(f"Final frame shape: {frame.shape}")
        
        id_min = float(id_min) if id_min != "NA" else None
        id_max = float(id_max) if id_max != "NA" else None
        od_min = float(od_min) if od_min != "NA" else None
        od_max = float(od_max) if od_max != "NA" else None
        concentricity_max = float(concentricity_max) if concentricity_max != "NA" else None
        orifice_min = float(orifice_min) if orifice_min != "NA" else None
        orifice_max = float(orifice_max) if orifice_max != "NA" else None
        threshold_id2 = int(threshold_id2) if threshold_id2 != "NA" else None
        threshold_id3 = int(threshold_id3) if threshold_id3 != "NA" else None
        threshold_od2 = int(threshold_od2) if threshold_od2 != "NA" else None
        threshold_od3 = int(threshold_od3) if threshold_od3 != "NA" else None
        pixel_to_micron = float(pixel_to_micron)
        pixel_to_micron_id = float(pixel_to_micron_id)
        pixel_to_micron_od = float(pixel_to_micron_od)

    except ValueError as e:
        # On parameter conversion failure, still try to save original as fallback
        try:
            os.makedirs(output_folder, exist_ok=True)
            if frame is not None:
                fallback_path = os.path.join(output_folder, "cam1_bmp.bmp")
                ok = cv2.imwrite(fallback_path, frame)
                print(f"Fallback write (param error) to {fallback_path}: {ok}")
        except Exception as _e:
            print(f"Fallback write error (param error): {_e}")

        print("r")
        print("Result: NOK")
        print("Error: parameter_conversion")
        print("ID: 0.0mm, Status: NOK")
        print("OD: 0.0mm, Status: NOK")
        print("Concentricity: NA")
        print("flash_defect: NOK")
        print("defect_position: None")
        print("Orifice: NA")
        return ("e", "NOK", "0.0", "NOK", "0.0", "NOK", "NA", "NA", "NOK", "None", "NA", "NA", "parameter_conversion")

    result = {
        'resultType': 'r',
        'result': 'OK',
        'errorType': None,
        'image_path': None,
        'measurements': {
            # Note: keys for concentricity/orifice may be removed per part behavior to avoid defaults
            'id': {'value': 0.0, 'status': 'OK'},
            'od': {'value': 0.0, 'status': 'OK'},
            'concentricity': {'value': 0.0, 'status': 'OK'},
            'flash': {'result': 'OK', 'position': 'None'},
            'orifice': {'value': 0.0, 'status': 'OK'}
        }
    }

    try:
        processed = dt.preprocess_image(frame, output_folder)
        if len(processed["sorted_contours"]) < 2:
            raise ValueError("Not enough contours found for ID/OD measurement")
        contours = processed["sorted_contours"]

        # 1) PISTON: ID/OD + concentricity + optional orifice
        if part == "PISTON":
            dims = dt.id_od_dimension(
                frame, contours, id_min, id_max, od_min, od_max, pixel_to_micron_id, pixel_to_micron_od)
            conc = dt.concentricity(dims['center_x_od'], dims['center_y_od'],
                                    dims['center_x_id'], dims['center_y_id'], concentricity_max, pixel_to_micron)
            flash = dt.flash_detection(frame, dims['id_contour'], dims['od_contour'],
                                       threshold_id2, threshold_id3, threshold_od2, threshold_od3, output_folder)

            orifice_data = None
            if orifice_min is not None and orifice_max is not None:
                orifice_data = dt.measure_orifice(frame, orifice_min, orifice_max, pixel_to_micron)

            result['measurements'].update({
                'id': {'value': dims['diameter_id_mm'], 'status': dims['id_status']},
                'od': {'value': dims['diameter_od_mm'], 'status': dims['od_status']},
                'concentricity': {'value': conc['concentricity_mm'], 'status': conc['concentricity_status']},
                'flash': {'result': flash['Defect_Result'], 'position': flash['defect_position']},
                'orifice': {'value': orifice_data['orifice_diameter_mm'] if orifice_data else 0.0,
                            'status': orifice_data['orifice_status'] if orifice_data else 'NA'}
            })
            save_result = dt.save_final_result_image(processed["image"], dims, flash, conc, orifice_data, output_folder)
            result['image_path'] = save_result.get('output_path')

            # Fallback if save failed
            if not save_result.get('success') or not save_result.get('output_path'):
                try:
                    os.makedirs(output_folder, exist_ok=True)
                    fallback_path = os.path.join(output_folder, "cam1_bmp.bmp")
                    ok = cv2.imwrite(fallback_path, frame)
                    result['image_path'] = fallback_path if ok else None
                    print(f"Fallback write after save failure to {fallback_path}: {ok}")
                except Exception as _e:
                    print(f"Fallback write error after save failure: {_e}")

        # 2) Ring-like: ID/OD + concentricity (no orifice)
        elif part in ["TEFLON PISTON RING", "SUPPORT PISTON RING", "SUPPORT PISTON", "OIL SEAL", "SPACER", "GUIDE END", "WASHER"]:
            dims = dt.id_od_dimension(
                frame, contours, id_min, id_max, od_min, od_max, pixel_to_micron_id, pixel_to_micron_od)
            conc = dt.concentricity(dims['center_x_od'], dims['center_y_od'],
                                    dims['center_x_id'], dims['center_y_id'], concentricity_max, pixel_to_micron)
            flash = dt.flash_detection(frame, dims['id_contour'], dims['od_contour'],
                                       threshold_id2, threshold_id3, threshold_od2, threshold_od3, output_folder)

            result['measurements'].update({
                'id': {'value': dims['diameter_id_mm'], 'status': dims['id_status']},
                'od': {'value': dims['diameter_od_mm'], 'status': dims['od_status']},
                'concentricity': {'value': conc['concentricity_mm'], 'status': conc['concentricity_status']},
                'flash': {'result': flash['Defect_Result'], 'position': flash['defect_position']}
            })
            result['measurements'].pop('orifice', None)
            save_result = dt.save_final_result_image(processed["image"], dims, flash, conc, None, output_folder)
            result['image_path'] = save_result.get('output_path')

            if not save_result.get('success') or not save_result.get('output_path'):
                try:
                    os.makedirs(output_folder, exist_ok=True)
                    fallback_path = os.path.join(output_folder, "cam1_bmp.bmp")
                    ok = cv2.imwrite(fallback_path, frame)
                    result['image_path'] = fallback_path if ok else None
                    print(f"Fallback write after save failure to {fallback_path}: {ok}")
                except Exception as _e:
                    print(f"Fallback write error after save failure: {_e}")

        # 3) O RING: ID only (OD NA), no concentricity/orifice
        elif part == "O RING":
            dims = dt.id_od_dimension(
                frame, contours, id_min, id_max, od_min, od_max, pixel_to_micron_id, pixel_to_micron_od)
            dims['diameter_od_mm'] = 0.0
            dims['diameter_od_px'] = 0.0
            dims['od_status'] = "NA"
            flash = dt.flash_detection(frame, dims['id_contour'], dims['od_contour'],
                                       threshold_id2, threshold_id3, threshold_od2, threshold_od3, output_folder)

            result['measurements'].update({
                'id': {'value': dims['diameter_id_mm'], 'status': dims['id_status']},
                'od': {'value': dims['diameter_od_mm'], 'status': dims['od_status']},
                'flash': {'result': flash['Defect_Result'], 'position': flash['defect_position']}
            })
            result['measurements'].pop('concentricity', None)
            result['measurements'].pop('orifice', None)
            save_result = dt.save_final_result_image(processed["image"], dims, flash, None, output_folder=output_folder)
            result['image_path'] = save_result.get('output_path')

            if not save_result.get('success') or not save_result.get('output_path'):
                try:
                    os.makedirs(output_folder, exist_ok=True)
                    fallback_path = os.path.join(output_folder, "cam1_bmp.bmp")
                    ok = cv2.imwrite(fallback_path, frame)
                    result['image_path'] = fallback_path if ok else None
                    print(f"Fallback write after save failure to {fallback_path}: {ok}")
                except Exception as _e:
                    print(f"Fallback write error after save failure: {_e}")

        # 4) NRV SEAL: OD only (ID NA), no concentricity/orifice
        elif part == "NRV SEAL":
            dims = dt.id_od_dimension(
                frame, contours, id_min, id_max, od_min, od_max, pixel_to_micron_id, pixel_to_micron_od)
            dims['diameter_id_mm'] = 0.0
            dims['diameter_id_px'] = 0.0
            dims['id_status'] = "NA"
            flash = dt.flash_detection(frame, dims['id_contour'], dims['od_contour'],
                                       threshold_id2, threshold_id3, threshold_od2, threshold_od3, output_folder)

            result['measurements'].update({
                'id': {'value': dims['diameter_id_mm'], 'status': dims['id_status']},
                'od': {'value': dims['diameter_od_mm'], 'status': dims['od_status']},
                'flash': {'result': flash['Defect_Result'], 'position': flash['defect_position']}
            })
            result['measurements'].pop('concentricity', None)
            result['measurements'].pop('orifice', None)
            save_result = dt.save_final_result_image(processed["image"], dims, flash, None, output_folder=output_folder)
            result['image_path'] = save_result.get('output_path')

            if not save_result.get('success') or not save_result.get('output_path'):
                try:
                    os.makedirs(output_folder, exist_ok=True)
                    fallback_path = os.path.join(output_folder, "cam1_bmp.bmp")
                    ok = cv2.imwrite(fallback_path, frame)
                    result['image_path'] = fallback_path if ok else None
                    print(f"Fallback write after save failure to {fallback_path}: {ok}")
                except Exception as _e:
                    print(f"Fallback write error after save failure: {_e}")

        # 5) Other simple parts: ID/OD only (no concentricity/orifice)
        elif part in ["NRV WASHER", "PISTON RING", "TEFLON RING"]:
            dims = dt.id_od_dimension(
                frame, contours, id_min, id_max, od_min, od_max, pixel_to_micron_id, pixel_to_micron_od)
            flash = dt.flash_detection(frame, dims['id_contour'], dims['od_contour'],
                                       threshold_id2, threshold_id3, threshold_od2, threshold_od3, output_folder)

            result['measurements'].update({
                'id': {'value': dims['diameter_id_mm'], 'status': dims['id_status']},
                'od': {'value': dims['diameter_od_mm'], 'status': dims['od_status']},
                'flash': {'result': flash['Defect_Result'], 'position': flash['defect_position']}
            })
            result['measurements'].pop('concentricity', None)
            result['measurements'].pop('orifice', None)
            save_result = dt.save_final_result_image(processed["image"], dims, flash, None, output_folder=output_folder)
            result['image_path'] = save_result.get('output_path')

            if not save_result.get('success') or not save_result.get('output_path'):
                try:
                    os.makedirs(output_folder, exist_ok=True)
                    fallback_path = os.path.join(output_folder, "cam1_bmp.bmp")
                    ok = cv2.imwrite(fallback_path, frame)
                    result['image_path'] = fallback_path if ok else None
                    print(f"Fallback write after save failure to {fallback_path}: {ok}")
                except Exception as _e:
                    print(f"Fallback write error after save failure: {_e}")

        # 6) SEPEARTING PISTON: OD only (ID NA), no concentricity/orifice
        elif part == "SEPEARTING PISTON":
            dims = dt.id_od_dimension(
                frame, contours, id_min, id_max, od_min, od_max, pixel_to_micron_id, pixel_to_micron_od)
            dims['diameter_id_mm'] = 0.0
            dims['diameter_id_px'] = 0.0
            dims['id_status'] = "NA"
            flash = dt.flash_detection(frame, dims['id_contour'], dims['od_contour'],
                                       threshold_id2, threshold_id3, threshold_od2, threshold_od3, output_folder)

            result['measurements'].update({
                'id': {'value': dims['diameter_id_mm'], 'status': dims['id_status']},
                'od': {'value': dims['diameter_od_mm'], 'status': dims['od_status']},
                'flash': {'result': flash['Defect_Result'], 'position': flash['defect_position']}
            })
            result['measurements'].pop('concentricity', None)
            result['measurements'].pop('orifice', None)
            save_result = dt.save_final_result_image(processed["image"], dims, flash, None, output_folder=output_folder)
            result['image_path'] = save_result.get('output_path')

            if not save_result.get('success') or not save_result.get('output_path'):
                try:
                    os.makedirs(output_folder, exist_ok=True)
                    fallback_path = os.path.join(output_folder, "cam1_bmp.bmp")
                    ok = cv2.imwrite(fallback_path, frame)
                    result['image_path'] = fallback_path if ok else None
                    print(f"Fallback write after save failure to {fallback_path}: {ok}")
                except Exception as _e:
                    print(f"Fallback write error after save failure: {_e}")

        else:
            raise ValueError(f"Unsupported part name: {part}")

        # Defect aggregation
        defect_lines = []
        if result['measurements']['id']['status'] == "NOK" or result['measurements']['od']['status'] == "NOK":
            defect_lines.append("ID/OD dimension")
        if 'concentricity' in result['measurements'] and result['measurements']['concentricity']['status'] == "NOK":
            defect_lines.append("Concentricity dimension")
        if result['measurements']['flash']['result'] != "OK":
            defect_lines.append(f"Flash on {result['measurements']['flash']['position']}")
        if 'orifice' in result['measurements'] and result['measurements']['orifice']['status'] == "NOK":
            defect_lines.append("Orifice dimension")

        # Shortcut return
        resultType = "r"
        result_status = "NOK" if defect_lines else "OK"
        ID = str(result['measurements']['id']['value'])
        IDstatus = result['measurements']['id']['status']
        OD = str(result['measurements']['od']['value'])
        ODstatus = result['measurements']['od']['status']
        Concentricity = (str(result['measurements']['concentricity']['value'])
                         if 'concentricity' in result['measurements'] else "NA")
        ConcentricityStatus = (result['measurements']['concentricity']['status']
                               if 'concentricity' in result['measurements'] else "NA")
        FlashDefect = result['measurements']['flash']['result']
        DefectPosition = result['measurements']['flash']['position']
        OrificeDiameter = (str(result['measurements']['orifice']['value'])
                           if 'orifice' in result['measurements'] else "NA")
        OrificeStatus = (result['measurements']['orifice']['status']
                         if 'orifice' in result['measurements'] else "NA")
        dim_err = ", ".join(defect_lines) if defect_lines else "None"

        print("r")
        print("Result:", result_status)
        if defect_lines:
            print("Error:", dim_err)
        print(f"ID: {ID}mm, Status: {IDstatus}")
        print(f"OD: {OD}mm, Status: {ODstatus}")
        print(f"Concentricity: {Concentricity}mm, Status: {ConcentricityStatus}" if Concentricity != "NA" else "Concentricity: NA")
        print(f"flash_defect: {FlashDefect}")
        print(f"defect_position: {DefectPosition}")
        print(f"Orifice: {OrificeDiameter}mm, Status: {OrificeStatus}" if OrificeDiameter != "NA" else "Orifice: NA")
        print(f"Output path: {result['image_path']}")

        # Final guard: ensure cam1_bmp.bmp exists
        try:
            os.makedirs(output_folder, exist_ok=True)
            cam1_path = os.path.join(output_folder, "cam1_bmp.bmp")
            if not os.path.exists(cam1_path) and frame is not None:
                ok = cv2.imwrite(cam1_path, frame)
                if not result['image_path']:
                    result['image_path'] = cam1_path if ok else None
                print(f"Final guard wrote original to {cam1_path}: {ok}")
        except Exception as _e:
            print(f"Final guard write error: {_e}")

        return (
            resultType, result_status,
            ID, IDstatus,
            OD, ODstatus,
            Concentricity, ConcentricityStatus,
            FlashDefect, DefectPosition,
            OrificeDiameter, OrificeStatus,
            dim_err
        )
      
    except Exception as e:
        # On any processing error, attempt fallback save
        try:
            os.makedirs(output_folder, exist_ok=True)
            if frame is not None:
                fallback_path = os.path.join(output_folder, "cam1_bmp.bmp")
                ok = cv2.imwrite(fallback_path, frame)
                print(f"Fallback write (exception path) to {fallback_path}: {ok}")
        except Exception as _e:
            print(f"Fallback write error (exception path): {_e}")

        print("r")
        print("Result: NOK")
        print("Error:", str(e))
        print("ID: 0.0mm, Status: NOK")
        print("OD: 0.0mm, Status: NOK")
        print("Concentricity: NA")
        print("flash_defect: NOK")
        print("defect_position: None")
        print("Orifice: NA")
        print("Output path: None")
        return ("e", "NOK", "0.0", "NOK", "0.0", "NOK", "NA", "NA", "NOK", "None", "NA", "NA", str(e))























# # # working  30/9/25 4pm

# # working 28/9/25
# #  # changes because of support pistong ring part
# # ## updated 20\9\2025  11:PM   upto 22_sep_25   
# import defect as dt
# import cv2
# import numpy as np

# def safe_color_convert(image, conversion_code):
#     """Safely convert image colors with channel checking"""
#     if len(image.shape) == 2 or (len(image.shape) == 3 and image.shape[2] == 1):
#         print("Input is grayscale, converting to BGR first")
#         if len(image.shape) == 2:
#             image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
#         else:
#             image = cv2.cvtColor(image.squeeze(), cv2.COLOR_GRAY2BGR)
#     try:
#         result = cv2.cvtColor(image, conversion_code)
#         return result
#     except cv2.error as e:
#         print(f"Conversion error: {e}")
#         return image

# def main(part, subpart, frame,
#          id_min, id_max, od_min, od_max,
#          concentricity_max, orifice_min, orifice_max,
#          threshold_id2, threshold_id3, threshold_od2, threshold_od3,
#          pixel_to_micron, pixel_to_micron_id, pixel_to_micron_od,
#          output_folder):
    
#     # Convert string parameters to float 
#     try:
#         print("type of id min:",type(id_min))
#         print('frame in  station 1:', frame)
#         print(f"Original frame shape: {frame.shape}")
#         if len(frame.shape) == 2:
#             frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
#             print("Converted grayscale frame to BGR")
#         elif len(frame.shape) == 3 and frame.shape[2] == 1:
#             frame = cv2.cvtColor(frame.squeeze(), cv2.COLOR_GRAY2BGR)
#             print("Converted single-channel frame to BGR")
#         elif len(frame.shape) == 3 and frame.shape[2] == 4:
#             frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
#             print("Converted BGRA frame to BGR")
#         print(f"Final frame shape: {frame.shape}")
        
#         id_min = float(id_min) if id_min != "NA" else None
#         id_max = float(id_max) if id_max != "NA" else None
#         od_min = float(od_min) if od_min != "NA" else None
#         od_max = float(od_max) if od_max != "NA" else None
#         concentricity_max = float(concentricity_max) if concentricity_max != "NA" else None
#         orifice_min = float(orifice_min) if orifice_min != "NA" else None
#         orifice_max = float(orifice_max) if orifice_max != "NA" else None
#         threshold_id2 = int(threshold_id2) if threshold_id2 != "NA" else None
#         threshold_id3 = int(threshold_id3) if threshold_id3 != "NA" else None
#         threshold_od2 = int(threshold_od2) if threshold_od2 != "NA" else None
#         threshold_od3 = int(threshold_od3) if threshold_od3 != "NA" else None
#         pixel_to_micron = float(pixel_to_micron)
#         pixel_to_micron_id = float(pixel_to_micron_id)
#         pixel_to_micron_od = float(pixel_to_micron_od)

#     except ValueError as e:
#         print("r")
#         print("Result: NOK")
#         print("Error: parameter_conversion")
#         print("ID: 0.0mm, Status: NOK")
#         print("OD: 0.0mm, Status: NOK")
#         print("Concentricity: NA")
#         print("flash_defect: NOK")
#         print("defect_position: None")
#         print("Orifice: NA")
#         return ("e", "NOK", "0.0", "NOK", "0.0", "NOK", "NA", "NA", "NOK", "None", "NA", "NA", "parameter_conversion")

#     result = {
#         'resultType': 'r',
#         'result': 'OK',
#         'errorType': None,
#         'image_path': None,
#         'measurements': {
#             # Note: keys for concentricity/orifice may be removed per part behavior to avoid defaults
#             'id': {'value': 0.0, 'status': 'OK'},
#             'od': {'value': 0.0, 'status': 'OK'},
#             'concentricity': {'value': 0.0, 'status': 'OK'},
#             'flash': {'result': 'OK', 'position': 'None'},
#             'orifice': {'value': 0.0, 'status': 'OK'}
#         }
#     }

#     try:
#         processed = dt.preprocess_image(frame, output_folder)
#         if len(processed["sorted_contours"]) < 2:
#             raise ValueError("Not enough contours found for ID/OD measurement")
#         contours = processed["sorted_contours"]

#         # 1) PISTON: ID/OD + concentricity + optional orifice
#         if part == "PISTON":
#             dims = dt.id_od_dimension(
#                 frame, contours, id_min, id_max, od_min, od_max, pixel_to_micron_id, pixel_to_micron_od)
#             conc = dt.concentricity(dims['center_x_od'], dims['center_y_od'],
#                                     dims['center_x_id'], dims['center_y_id'], concentricity_max, pixel_to_micron)
#             flash = dt.flash_detection(frame, dims['id_contour'], dims['od_contour'],
#                                        threshold_id2, threshold_id3, threshold_od2, threshold_od3, output_folder)

#             orifice_data = None
#             if orifice_min is not None and orifice_max is not None:
#                 orifice_data = dt.measure_orifice(frame, orifice_min, orifice_max, pixel_to_micron)

#             result['measurements'].update({
#                 'id': {'value': dims['diameter_id_mm'], 'status': dims['id_status']},
#                 'od': {'value': dims['diameter_od_mm'], 'status': dims['od_status']},
#                 'concentricity': {'value': conc['concentricity_mm'], 'status': conc['concentricity_status']},
#                 'flash': {'result': flash['Defect_Result'], 'position': flash['defect_position']},
#                 'orifice': {'value': orifice_data['orifice_diameter_mm'] if orifice_data else 0.0,
#                             'status': orifice_data['orifice_status'] if orifice_data else 'NA'}
#             })
#             save_result = dt.save_final_result_image(processed["image"], dims, flash, conc, orifice_data, output_folder)
#             result['image_path'] = save_result['output_path']

#         # 2) Ring-like: ID/OD + concentricity (no orifice)
#         elif part in ["TEFLON PISTON RING", "SUPPORT PISTON RING", "SUPPORT PISTON", "OIL SEAL", "SPACER", "GUIDE END", "WASHER"]:
#             dims = dt.id_od_dimension(
#                 frame, contours, id_min, id_max, od_min, od_max, pixel_to_micron_id, pixel_to_micron_od)
#             conc = dt.concentricity(dims['center_x_od'], dims['center_y_od'],
#                                     dims['center_x_id'], dims['center_y_id'], concentricity_max, pixel_to_micron)
#             flash = dt.flash_detection(frame, dims['id_contour'], dims['od_contour'],
#                                        threshold_id2, threshold_id3, threshold_od2, threshold_od3, output_folder)

#             result['measurements'].update({
#                 'id': {'value': dims['diameter_id_mm'], 'status': dims['id_status']},
#                 'od': {'value': dims['diameter_od_mm'], 'status': dims['od_status']},
#                 'concentricity': {'value': conc['concentricity_mm'], 'status': conc['concentricity_status']},
#                 'flash': {'result': flash['Defect_Result'], 'position': flash['defect_position']}
#             })
#             # Ensure no stray orifice key
#             result['measurements'].pop('orifice', None)
#             save_result = dt.save_final_result_image(processed["image"], dims, flash, conc, None, output_folder)
#             result['image_path'] = save_result['output_path']

#         # 3) O RING: ID only (OD NA), no concentricity/orifice
#         elif part == "O RING":
#             dims = dt.id_od_dimension(
#                 frame, contours, id_min, id_max, od_min, od_max, pixel_to_micron_id, pixel_to_micron_od)
#             # Force OD to NA
#             dims['diameter_od_mm'] = 0.0
#             dims['diameter_od_px'] = 0.0
#             dims['od_status'] = "NA"
#             flash = dt.flash_detection(frame, dims['id_contour'], dims['od_contour'],
#                                        threshold_id2, threshold_id3, threshold_od2, threshold_od3, output_folder)

#             result['measurements'].update({
#                 'id': {'value': dims['diameter_id_mm'], 'status': dims['id_status']},
#                 'od': {'value': dims['diameter_od_mm'], 'status': dims['od_status']},
#                 'flash': {'result': flash['Defect_Result'], 'position': flash['defect_position']}
#             })
#             # Remove concentricity/orifice to express true omission
#             result['measurements'].pop('concentricity', None)
#             result['measurements'].pop('orifice', None)
#             save_result = dt.save_final_result_image(processed["image"], dims, flash, None, output_folder=output_folder)
#             result['image_path'] = save_result['output_path']

#         # 4) NRV SEAL: OD only (ID NA), no concentricity/orifice
#         elif part == "NRV SEAL":
#             dims = dt.id_od_dimension(
#                 frame, contours, id_min, id_max, od_min, od_max, pixel_to_micron_id, pixel_to_micron_od)
#             # Force ID to NA
#             dims['diameter_id_mm'] = 0.0
#             dims['diameter_id_px'] = 0.0
#             dims['id_status'] = "NA"
#             flash = dt.flash_detection(frame, dims['id_contour'], dims['od_contour'],
#                                        threshold_id2, threshold_id3, threshold_od2, threshold_od3, output_folder)

#             result['measurements'].update({
#                 'id': {'value': dims['diameter_id_mm'], 'status': dims['id_status']},
#                 'od': {'value': dims['diameter_od_mm'], 'status': dims['od_status']},
#                 'flash': {'result': flash['Defect_Result'], 'position': flash['defect_position']}
#             })
#             # Remove concentricity/orifice to express true omission
#             result['measurements'].pop('concentricity', None)
#             result['measurements'].pop('orifice', None)
#             save_result = dt.save_final_result_image(processed["image"], dims, flash, None, output_folder=output_folder)
#             result['image_path'] = save_result['output_path']

#         # 5) Other simple parts: ID/OD only (no concentricity/orifice)
#         elif part in ["NRV WASHER", "PISTON RING", "TEFLON RING"]:
#             dims = dt.id_od_dimension(
#                 frame, contours, id_min, id_max, od_min, od_max, pixel_to_micron_id, pixel_to_micron_od)
#             flash = dt.flash_detection(frame, dims['id_contour'], dims['od_contour'],
#                                        threshold_id2, threshold_id3, threshold_od2, threshold_od3, output_folder)

#             result['measurements'].update({
#                 'id': {'value': dims['diameter_id_mm'], 'status': dims['id_status']},
#                 'od': {'value': dims['diameter_od_mm'], 'status': dims['od_status']},
#                 'flash': {'result': flash['Defect_Result'], 'position': flash['defect_position']}
#             })
#             # Remove concentricity/orifice to avoid default 0.0 OK
#             result['measurements'].pop('concentricity', None)
#             result['measurements'].pop('orifice', None)
#             save_result = dt.save_final_result_image(processed["image"], dims, flash, None, output_folder=output_folder)
#             result['image_path'] = save_result['output_path']

#         # 6) SEPEARTING PISTON: OD only (ID NA), no concentricity/orifice
#         elif part == "SEPEARTING PISTON":
#             dims = dt.id_od_dimension(
#                 frame, contours, id_min, id_max, od_min, od_max, pixel_to_micron_id, pixel_to_micron_od)
#             dims['diameter_id_mm'] = 0.0
#             dims['diameter_id_px'] = 0.0
#             dims['id_status'] = "NA"
#             flash = dt.flash_detection(frame, dims['id_contour'], dims['od_contour'],
#                                        threshold_id2, threshold_id3, threshold_od2, threshold_od3, output_folder)

#             result['measurements'].update({
#                 'id': {'value': dims['diameter_id_mm'], 'status': dims['id_status']},
#                 'od': {'value': dims['diameter_od_mm'], 'status': dims['od_status']},
#                 'flash': {'result': flash['Defect_Result'], 'position': flash['defect_position']}
#             })
#             result['measurements'].pop('concentricity', None)
#             result['measurements'].pop('orifice', None)
#             save_result = dt.save_final_result_image(processed["image"], dims, flash, None, output_folder=output_folder)
#             result['image_path'] = save_result['output_path']

#         else:
#             raise ValueError(f"Unsupported part name: {part}")

#         # Defect aggregation
#         defect_lines = []
#         if result['measurements']['id']['status'] == "NOK" or result['measurements']['od']['status'] == "NOK":
#             defect_lines.append("ID/OD dimension")
#         if 'concentricity' in result['measurements'] and result['measurements']['concentricity']['status'] == "NOK":
#             defect_lines.append("Concentricity dimension")
#         if result['measurements']['flash']['result'] != "OK":
#             defect_lines.append(f"Flash on {result['measurements']['flash']['position']}")
#         if 'orifice' in result['measurements'] and result['measurements']['orifice']['status'] == "NOK":
#             defect_lines.append("Orifice dimension")

#         # Shortcut return
#         resultType = "r"
#         result_status = "NOK" if defect_lines else "OK"
#         ID = str(result['measurements']['id']['value'])
#         IDstatus = result['measurements']['id']['status']
#         OD = str(result['measurements']['od']['value'])
#         ODstatus = result['measurements']['od']['status']
#         Concentricity = (str(result['measurements']['concentricity']['value'])
#                          if 'concentricity' in result['measurements'] else "NA")
#         ConcentricityStatus = (result['measurements']['concentricity']['status']
#                                if 'concentricity' in result['measurements'] else "NA")
#         FlashDefect = result['measurements']['flash']['result']
#         DefectPosition = result['measurements']['flash']['position']
#         OrificeDiameter = (str(result['measurements']['orifice']['value'])
#                            if 'orifice' in result['measurements'] else "NA")
#         OrificeStatus = (result['measurements']['orifice']['status']
#                          if 'orifice' in result['measurements'] else "NA")
#         dim_err = ", ".join(defect_lines) if defect_lines else "None"

#         print("r")
#         print("Result:", result_status)
#         if defect_lines:
#             print("Error:", dim_err)
#         print(f"ID: {ID}mm, Status: {IDstatus}")
#         print(f"OD: {OD}mm, Status: {ODstatus}")
#         print(f"Concentricity: {Concentricity}mm, Status: {ConcentricityStatus}" if Concentricity != "NA" else "Concentricity: NA")
#         print(f"flash_defect: {FlashDefect}")
#         print(f"defect_position: {DefectPosition}")
#         print(f"Orifice: {OrificeDiameter}mm, Status: {OrificeStatus}" if OrificeDiameter != "NA" else "Orifice: NA")
#         print(f"Output path: {result['image_path']}")

#         return (
#             resultType, result_status,
#             ID, IDstatus,
#             OD, ODstatus,
#             Concentricity, ConcentricityStatus,
#             FlashDefect, DefectPosition,
#             OrificeDiameter, OrificeStatus,
#             dim_err
#         )
      
#     except Exception as e:
#         print("r")
#         print("Result: NOK")
#         print("Error:", str(e))
#         print("ID: 0.0mm, Status: NOK")
#         print("OD: 0.0mm, Status: NOK")
#         print("Concentricity: NA")
#         print("flash_defect: NOK")
#         print("defect_position: None")
#         print("Orifice: NA")
#         print("Output path: None")
#         return ("e", "NOK", "0.0", "NOK", "0.0", "NOK", "NA", "NA", "NOK", "None", "NA", "NA", str(e))



















