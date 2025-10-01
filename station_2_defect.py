# code 3

#station_2_defect.py
import cv2
import numpy as np
import math
from datetime import datetime
import os
import imutils

def preprocess_image(frame, output_folder=None, min_thresh=0, max_thresh=255):
    # Preprocess the image: create folder, grayscale, threshold, find and filter contours
    """Preprocessing function for image loading, thresholding, and contour detection"""
    if output_folder:
        # Ensure output directory exists for any downstream saves
        os.makedirs(output_folder, exist_ok=True)
    
    # Convert BGR image to grayscale for robust thresholding
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Ensure integer thresholds in valid range
    try:
        min_thr = int(float(min_thresh))
        min_thr = max(0, min(255, min_thr))
        max_thr = int(float(max_thresh))
        max_thr = max(0, min(255, max_thr))
    except Exception:
        min_thr = 0
        max_thr = 255
    
    # Inverse binary threshold so darker objects become white blobs (foreground)
    _, thresh_img = cv2.threshold(gray, min_thr, max_thr, cv2.THRESH_BINARY_INV)
    
    # Detect external contours on the binary image (ignore holes/children)
    contours, _ = cv2.findContours(thresh_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Define ROI rectangle; keep contours whose bounding box lies fully inside
    rect_x1, rect_y1 = 660, 600      # SUPPORT PISTON 780 SPACER 600
    rect_x2, rect_y2 = 1560, 960
    
    # Collect contours fully contained in the ROI to reject outside noise
    filtered_contours = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if x >= rect_x1 and (x + w) <= rect_x2 and y >= rect_y1 and (y + h) <= rect_y2:
            filtered_contours.append(contour)
    
    # Sort kept contours by area (largest first) for downstream use
    sorted_contours = sorted(filtered_contours, key=cv2.contourArea, reverse=True) if filtered_contours else []
    
    # Return original copy plus intermediates and filtered, sorted contours
    return {
        "image": frame.copy(),
        "sorted_contours": sorted_contours,
        "original_gray": gray,
        "thresh_img": thresh_img
    }

def measure_thickness(frame, contours, thick_min=None, thick_max=None, pixel_to_micron=None):
    # Measure thickness using only the center vertical scan line across the largest contour
    """Measure thickness using only the center vertical line segment"""
    if not contours:
        # Guard: no valid contours found in preprocessing
        raise ValueError("No contours found for thickness measurement")
    
    # Use largest contour for measurement
    largest_contour = contours[0]
    
    # Compute bounding box center x to define the center scan line
    x, y, w, h = cv2.boundingRect(largest_contour)
    center_x = x + w // 2
    
    # Vertical line spans full image height at x=center_x
    img_height = frame.shape[0]
    line_x = center_x
    
    # Intersect center vertical line with contour to get crossing points
    intersections = find_line_contour_intersections(largest_contour, line_x, img_height)
    
    # If at least two crossings, compute the distance between first two (top to bottom)
    line_segment = None
    valid_measurements = []
    if len(intersections) >= 2:
        start_pt = intersections[0]
        end_pt = intersections[1]
        # Euclidean distance in pixels between boundary points
        distance_pixels = calculate_distance(start_pt, end_pt)
        # Convert pixels → microns → millimeters using calibration factor
        distance_mm = (distance_pixels * pixel_to_micron) / 1000.0
        valid_measurements.append(distance_mm)
        # Save exact endpoints for drawing the short segment later
        line_segment = {'x': line_x, 'pt1': start_pt, 'pt2': end_pt}
    
    # If no valid segment, return NOK with zero thickness and endpoints (if any)
    if not valid_measurements:
        return {
            "thickness_mm": 0.0,
            "thickness_status": "NOK",
            "contour": largest_contour,
            "center_x": center_x,
            "valid_lines": 0,
            "center_segment": line_segment  # may be None
        }
    
    # Average thickness (only center used now) and spec check
    average_thickness_mm = sum(valid_measurements) / len(valid_measurements)
    
    status = "OK"
    if thick_min is not None and thick_max is not None:
        if not (thick_min <= average_thickness_mm <= thick_max):
            status = "NOK"
    
    # Return numeric results, contour handle, scan x, and the measured segment
    return {
        "thickness_mm": round(average_thickness_mm, 2),
        "thickness_status": status,
        "contour": largest_contour,
        "center_x": center_x,
        "valid_lines": 1,
        "center_segment": line_segment
    }

def flash_detection_thickness(frame, contours, output_folder=None):
    # Stub for flash detection; currently always returns OK placeholder
    """Flash detection for thickness measurement (simplified version)"""
    if not contours:
        # If no contours, treat as OK for this placeholder implementation
        return {
            "Defect_Result": "OK",
            "defect_position": "None",
            "defect_type": "Flash"
        }
    # Default OK; extend with actual flash logic as needed
    return {
        "Defect_Result": "OK",
        "defect_position": "None",
        "defect_type": "Flash"
    }

def find_line_contour_intersections(contour, line_x, img_height):
    # Return intersection points between vertical line x=line_x and the polygonal contour
    """Find intersection points where a vertical line crosses the contour"""
    contour_pts = contour.reshape(-1, 2)
    intersections = []
    
    # 1) Direct near-vertex check: accept points with small x-offset tolerance
    tolerance = 3
    for pt in contour_pts:
        if abs(pt[0] - line_x) <= tolerance:
            intersections.append(tuple(pt))
    
    # 2) Precise segment test: intersect each contour edge with vertical line
    line_start = (line_x, 0)
    line_end = (line_x, img_height)
    
    for i in range(len(contour_pts)):
        p1 = contour_pts[i]
        p2 = contour_pts[(i + 1) % len(contour_pts)]
        
        # Parametric intersection; keep if x is close to the scan line
        intersection = line_segment_intersection(line_start, line_end, tuple(p1), tuple(p2))
        if intersection and abs(intersection[0] - line_x) <= 2:
            intersections.append(intersection)
    
    # Deduplicate near-identical points and sort by y ascending (top→bottom)
    if intersections:
        unique_intersections = []
        for pt in intersections:
            is_duplicate = False
            for existing_pt in unique_intersections:
                if abs(pt[0] - existing_pt[0]) <= 3 and abs(pt[1] - existing_pt[1]) <= 3:
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique_intersections.append(pt)
        
        unique_intersections.sort(key=lambda p: p[1])
        return unique_intersections
    
    # No intersections found
    return []

def line_segment_intersection(line1_start, line1_end, line2_start, line2_end):
    # Compute intersection point of two line segments using parametric form
    """Calculate intersection point between two line segments"""
    x1, y1 = line1_start
    x2, y2 = line1_end
    x3, y3 = line2_start
    x4, y4 = line2_end
    
    # Denominator close to zero → parallel or colinear, no unique intersection
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < 1e-10:
        return None
    
    # Solve for parameters t and u to locate intersection along both segments
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom
    
    # If intersection lies within both segments (0..1), compute the point
    if 0 <= t <= 1 and 0 <= u <= 1:
        x = x1 + t * (x2 - x1)
        y = y1 + t * (y2 - y1)
        # Return pixel coordinates as integers (drawing-friendly)
        return (int(x), int(y))
    
    # Segments do not overlap at a point
    return None

def calculate_distance(pt1, pt2):
    # Euclidean distance between two (x, y) points in pixels
    """Calculate Euclidean distance between two points"""
    return np.sqrt((pt2[0] - pt1[0])**2 + (pt2[1] - pt1[1])**2)

def save_thickness_result_image(image, thickness_data, flash_data, output_folder="output_images"):
    # Save visualization: crop around contour center, draw only center short segment and endpoints, add thickness text
    """Save result image with thickness measurement annotations (cropped around contour center).
       CHANGE: Draw only the center short segment between the two intersection points; no full vertical lines and no contour."""
    try:
        # Work on a copy to preserve original frame
        result_img = image.copy()
        os.makedirs(output_folder, exist_ok=True)
        
        # Image dimensions for bounds checks and cropping
        img_height, img_width = result_img.shape[:2]
        
        # Compute contour centroid via moments; fallback to bbox center if degenerate
        contour_center_x, contour_center_y = None, None
        if 'contour' in thickness_data and thickness_data['contour'] is not None:
            # Moments return area and first-order sums for centroid computation
            M = cv2.moments(thickness_data['contour'])
            if M["m00"] != 0:
                contour_center_x = int(M["m10"] / M["m00"])
                contour_center_y = int(M["m01"] / M["m00"])
            else:
                # Use bounding box center when area is zero (degenerate)
                x, y, w, h = cv2.boundingRect(thickness_data['contour'])
                contour_center_x = x + w // 2
                contour_center_y = y + h // 2
        
        # If we have a center, crop a 600x600 window around it with boundary clamps
        x1 = y1 = x2 = y2 = None
        if contour_center_x is not None and contour_center_y is not None:
            crop_size = 300
            x1 = max(0, contour_center_x - crop_size)
            y1 = max(0, contour_center_y - crop_size)
            x2 = min(img_width, contour_center_x + crop_size)
            y2 = min(img_height, contour_center_y + crop_size)
            # Apply crop to the working image
            result_img = result_img[y1:y2, x1:x2]
        
        # Draw only the measured center short segment and small endpoint markers (if available)
        center_seg = thickness_data.get('center_segment', None)
        if center_seg is not None:
            pt1 = center_seg['pt1']
            pt2 = center_seg['pt2']
            # Adjust segment endpoints into cropped coordinates if a crop was applied
            if x1 is not None and y1 is not None:
                draw_pt1 = (int(pt1[0] - x1), int(pt1[1] - y1))
                draw_pt2 = (int(pt2[0] - x1), int(pt2[1] - y1))
            else:
                draw_pt1 = (int(pt1[0]), int(pt1[1]))
                draw_pt2 = (int(pt2[0]), int(pt2[1]))
            # Draw the short red line segment exactly between the two intersection points
            cv2.line(result_img, draw_pt1, draw_pt2, (0, 0, 255), 2)  # red short segment [pt1, pt2]
            # Draw small yellow filled circles to mark the exact endpoints used
            cv2.circle(result_img, draw_pt1, 3, (0, 255, 255), -1)    # endpoint 1
            cv2.circle(result_img, draw_pt2, 3, (0, 255, 255), -1)    # endpoint 2
        
        # Choose text position; adjust for crop so it stays visible in the ROI
        if x1 is not None and y1 is not None:
            thickness_text_x = max(10, 150 - x1)
            thickness_text_y = max(30, 300 - y1)
        else:
            thickness_text_x, thickness_text_y = 150, 300
        
        # Annotation font parameters (size and thickness tuned for readability)
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        text_thickness = 1
        
        # Render thickness string in blue for quick visual confirmation
        thickness_text = f"Thickness = {thickness_data['thickness_mm']:.2f}mm"
        cv2.putText(result_img, thickness_text, (thickness_text_x, thickness_text_y), font, font_scale, (255, 0, 0), text_thickness)
        
        # Persist annotated crop to a deterministic filename (will overwrite each run)
        filename = "cam2_bmp.bmp"
        output_path = os.path.join(output_folder, filename)
        write_ok = cv2.imwrite(output_path, result_img)

        # If annotated write failed, try writing the original image as fallback
        if not write_ok:
            print("Annotated write failed, attempting fallback with original image")
            write_ok = cv2.imwrite(output_path, image)
        
        # Report path and success flag for downstream consumers/logging
        return {"output_path": output_path if write_ok else None, "success": bool(write_ok)}
    except Exception as e:
        # Last-resort fallback: try to save the original image anyway
        try:
            os.makedirs(output_folder, exist_ok=True)
            output_path = os.path.join(output_folder, "cam2_bmp.bmp")
            ok = cv2.imwrite(output_path, image)
            return {"output_path": output_path if ok else None, "success": bool(ok), "error": str(e)}
        except Exception as _e:
            return {"output_path": None, "success": False, "error": f"{e} | fallback: {_e}"}





















### working 30 sep 25

# #station_2_defect.py
# import cv2
# import numpy as np
# import math
# from datetime import datetime
# import os
# import imutils

# def preprocess_image(frame, output_folder=None, min_thresh=0, max_thresh=255):
#     # Preprocess the image: create folder, grayscale, threshold, find and filter contours
#     """Preprocessing function for image loading, thresholding, and contour detection"""
#     if output_folder:
#         # Ensure output directory exists for any downstream saves
#         os.makedirs(output_folder, exist_ok=True)
    
#     # Convert BGR image to grayscale for robust thresholding
#     gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
#     # Ensure integer thresholds in valid range
#     try:
#         min_thr = int(float(min_thresh))
#         min_thr = max(0, min(255, min_thr))
#         max_thr = int(float(max_thresh))
#         max_thr = max(0, min(255, max_thr))
#     except Exception:
#         min_thr = 0
#         max_thr = 255
    
#     # Inverse binary threshold so darker objects become white blobs (foreground)
#     _, thresh_img = cv2.threshold(gray, min_thr, max_thr, cv2.THRESH_BINARY_INV)
    
#     # Detect external contours on the binary image (ignore holes/children)
#     contours, _ = cv2.findContours(thresh_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
#     # Define ROI rectangle; keep contours whose bounding box lies fully inside
#     rect_x1, rect_y1 = 660, 600      # SUPPORT PISTON 780 SPACER 600
#     rect_x2, rect_y2 = 1560, 960
    
#     # Collect contours fully contained in the ROI to reject outside noise
#     filtered_contours = []
#     for contour in contours:
#         x, y, w, h = cv2.boundingRect(contour)
#         if x >= rect_x1 and (x + w) <= rect_x2 and y >= rect_y1 and (y + h) <= rect_y2:
#             filtered_contours.append(contour)
    
#     # Sort kept contours by area (largest first) for downstream use
#     sorted_contours = sorted(filtered_contours, key=cv2.contourArea, reverse=True) if filtered_contours else []
    
#     # Return original copy plus intermediates and filtered, sorted contours
#     return {
#         "image": frame.copy(),
#         "sorted_contours": sorted_contours,
#         "original_gray": gray,
#         "thresh_img": thresh_img
#     }

# def measure_thickness(frame, contours, thick_min=None, thick_max=None, pixel_to_micron=None):
#     # Measure thickness using only the center vertical scan line across the largest contour
#     """Measure thickness using only the center vertical line segment"""
#     if not contours:
#         # Guard: no valid contours found in preprocessing
#         raise ValueError("No contours found for thickness measurement")
    
#     # Use largest contour for measurement
#     largest_contour = contours[0]
    
#     # Compute bounding box center x to define the center scan line
#     x, y, w, h = cv2.boundingRect(largest_contour)
#     center_x = x + w // 2
    
#     # Vertical line spans full image height at x=center_x
#     img_height = frame.shape[0]
#     line_x = center_x
    
#     # Intersect center vertical line with contour to get crossing points
#     intersections = find_line_contour_intersections(largest_contour, line_x, img_height)
    
#     # If at least two crossings, compute the distance between first two (top to bottom)
#     line_segment = None
#     valid_measurements = []
#     if len(intersections) >= 2:
#         start_pt = intersections[0]
#         end_pt = intersections[1]
#         # Euclidean distance in pixels between boundary points
#         distance_pixels = calculate_distance(start_pt, end_pt)
#         # Convert pixels → microns → millimeters using calibration factor
#         distance_mm = (distance_pixels * pixel_to_micron) / 1000.0
#         valid_measurements.append(distance_mm)
#         # Save exact endpoints for drawing the short segment later
#         line_segment = {'x': line_x, 'pt1': start_pt, 'pt2': end_pt}
    
#     # If no valid segment, return NOK with zero thickness and endpoints (if any)
#     if not valid_measurements:
#         return {
#             "thickness_mm": 0.0,
#             "thickness_status": "NOK",
#             "contour": largest_contour,
#             "center_x": center_x,
#             "valid_lines": 0,
#             "center_segment": line_segment  # may be None
#         }
    
#     # Average thickness (only center used now) and spec check
#     average_thickness_mm = sum(valid_measurements) / len(valid_measurements)
    
#     status = "OK"
#     if thick_min is not None and thick_max is not None:
#         if not (thick_min <= average_thickness_mm <= thick_max):
#             status = "NOK"
    
#     # Return numeric results, contour handle, scan x, and the measured segment
#     return {
#         "thickness_mm": round(average_thickness_mm, 2),
#         "thickness_status": status,
#         "contour": largest_contour,
#         "center_x": center_x,
#         "valid_lines": 1,
#         "center_segment": line_segment
#     }

# def flash_detection_thickness(frame, contours, output_folder=None):
#     # Stub for flash detection; currently always returns OK placeholder
#     """Flash detection for thickness measurement (simplified version)"""
#     if not contours:
#         # If no contours, treat as OK for this placeholder implementation
#         return {
#             "Defect_Result": "OK",
#             "defect_position": "None",
#             "defect_type": "Flash"
#         }
#     # Default OK; extend with actual flash logic as needed
#     return {
#         "Defect_Result": "OK",
#         "defect_position": "None",
#         "defect_type": "Flash"
#     }

# def find_line_contour_intersections(contour, line_x, img_height):
#     # Return intersection points between vertical line x=line_x and the polygonal contour
#     """Find intersection points where a vertical line crosses the contour"""
#     contour_pts = contour.reshape(-1, 2)
#     intersections = []
    
#     # 1) Direct near-vertex check: accept points with small x-offset tolerance
#     tolerance = 3
#     for pt in contour_pts:
#         if abs(pt[0] - line_x) <= tolerance:
#             intersections.append(tuple(pt))
    
#     # 2) Precise segment test: intersect each contour edge with vertical line
#     line_start = (line_x, 0)
#     line_end = (line_x, img_height)
    
#     for i in range(len(contour_pts)):
#         p1 = contour_pts[i]
#         p2 = contour_pts[(i + 1) % len(contour_pts)]
        
#         # Parametric intersection; keep if x is close to the scan line
#         intersection = line_segment_intersection(line_start, line_end, tuple(p1), tuple(p2))
#         if intersection and abs(intersection[0] - line_x) <= 2:
#             intersections.append(intersection)
    
#     # Deduplicate near-identical points and sort by y ascending (top→bottom)
#     if intersections:
#         unique_intersections = []
#         for pt in intersections:
#             is_duplicate = False
#             for existing_pt in unique_intersections:
#                 if abs(pt[0] - existing_pt[0]) <= 3 and abs(pt[1] - existing_pt[1]) <= 3:
#                     is_duplicate = True
#                     break
#             if not is_duplicate:
#                 unique_intersections.append(pt)
        
#         unique_intersections.sort(key=lambda p: p[1])
#         return unique_intersections
    
#     # No intersections found
#     return []

# def line_segment_intersection(line1_start, line1_end, line2_start, line2_end):
#     # Compute intersection point of two line segments using parametric form
#     """Calculate intersection point between two line segments"""
#     x1, y1 = line1_start
#     x2, y2 = line1_end
#     x3, y3 = line2_start
#     x4, y4 = line2_end
    
#     # Denominator close to zero → parallel or colinear, no unique intersection
#     denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
#     if abs(denom) < 1e-10:
#         return None
    
#     # Solve for parameters t and u to locate intersection along both segments
#     t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
#     u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom
    
#     # If intersection lies within both segments (0..1), compute the point
#     if 0 <= t <= 1 and 0 <= u <= 1:
#         x = x1 + t * (x2 - x1)
#         y = y1 + t * (y2 - y1)
#         # Return pixel coordinates as integers (drawing-friendly)
#         return (int(x), int(y))
    
#     # Segments do not overlap at a point
#     return None

# def calculate_distance(pt1, pt2):
#     # Euclidean distance between two (x, y) points in pixels
#     """Calculate Euclidean distance between two points"""
#     return np.sqrt((pt2[0] - pt1[0])**2 + (pt2[1] - pt1[1])**2)

# def save_thickness_result_image(image, thickness_data, flash_data, output_folder="output_images"):
#     # Save visualization: crop around contour center, draw only center short segment and endpoints, add thickness text
#     """Save result image with thickness measurement annotations (cropped around contour center).
#        CHANGE: Draw only the center short segment between the two intersection points; no full vertical lines and no contour."""
#     try:
#         # Work on a copy to preserve original frame
#         result_img = image.copy()
#         os.makedirs(output_folder, exist_ok=True)
        
#         # Image dimensions for bounds checks and cropping
#         img_height, img_width = result_img.shape[:2]
        
#         # Compute contour centroid via moments; fallback to bbox center if degenerate
#         contour_center_x, contour_center_y = None, None
#         if 'contour' in thickness_data and thickness_data['contour'] is not None:
#             # Moments return area and first-order sums for centroid computation
#             M = cv2.moments(thickness_data['contour'])
#             if M["m00"] != 0:
#                 contour_center_x = int(M["m10"] / M["m00"])
#                 contour_center_y = int(M["m01"] / M["m00"])
#             else:
#                 # Use bounding box center when area is zero (degenerate)
#                 x, y, w, h = cv2.boundingRect(thickness_data['contour'])
#                 contour_center_x = x + w // 2
#                 contour_center_y = y + h // 2
        
#         # If we have a center, crop a 600x600 window around it with boundary clamps
#         x1 = y1 = x2 = y2 = None
#         if contour_center_x is not None and contour_center_y is not None:
#             crop_size = 300
#             x1 = max(0, contour_center_x - crop_size)
#             y1 = max(0, contour_center_y - crop_size)
#             x2 = min(img_width, contour_center_x + crop_size)
#             y2 = min(img_height, contour_center_y + crop_size)
#             # Apply crop to the working image
#             result_img = result_img[y1:y2, x1:x2]
        
#         # Draw only the measured center short segment and small endpoint markers (if available)
#         center_seg = thickness_data.get('center_segment', None)
#         if center_seg is not None:
#             pt1 = center_seg['pt1']
#             pt2 = center_seg['pt2']
#             # Adjust segment endpoints into cropped coordinates if a crop was applied
#             if x1 is not None and y1 is not None:
#                 draw_pt1 = (int(pt1[0] - x1), int(pt1[1] - y1))
#                 draw_pt2 = (int(pt2[0] - x1), int(pt2[1] - y1))
#             else:
#                 draw_pt1 = (int(pt1[0]), int(pt1[1]))
#                 draw_pt2 = (int(pt2[0]), int(pt2[1]))
#             # Draw the short red line segment exactly between the two intersection points
#             cv2.line(result_img, draw_pt1, draw_pt2, (0, 0, 255), 2)  # red short segment [pt1, pt2]
#             # Draw small yellow filled circles to mark the exact endpoints used
#             cv2.circle(result_img, draw_pt1, 3, (0, 255, 255), -1)    # endpoint 1
#             cv2.circle(result_img, draw_pt2, 3, (0, 255, 255), -1)    # endpoint 2
        
#         # Choose text position; adjust for crop so it stays visible in the ROI
#         if x1 is not None and y1 is not None:
#             thickness_text_x = max(10, 150 - x1)
#             thickness_text_y = max(30, 300 - y1)
#         else:
#             thickness_text_x, thickness_text_y = 150, 300
        
#         # Annotation font parameters (size and thickness tuned for readability)
#         font = cv2.FONT_HERSHEY_SIMPLEX
#         font_scale = 0.5
#         text_thickness = 1
        
#         # Render thickness string in blue for quick visual confirmation
#         thickness_text = f"Thickness = {thickness_data['thickness_mm']:.2f}mm"
#         cv2.putText(result_img, thickness_text, (thickness_text_x, thickness_text_y), font, font_scale, (255, 0, 0), text_thickness)
        
#         # Persist annotated crop to a deterministic filename (will overwrite each run)
#         filename = "cam2_bmp.bmp"
#         output_path = os.path.join(output_folder, filename)
#         cv2.imwrite(output_path, result_img)
        
#         # Report path and success flag for downstream consumers/logging
#         return {"output_path": output_path, "success": True}
#     except Exception as e:
#         # Standardized error return to avoid raising from visualization path
#         return {"output_path": None, "success": False, "error": str(e)}













