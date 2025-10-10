# python 03_red_area_neglect.py --image "D:/Pravi/burr_images/new_glass/station3/dataset/9_oct_25/VCXG.2-32C/image0000389.bmp"




import cv2 as cv                 
import numpy as np              
import argparse, sys             
from pathlib import Path         


AREA_MIN = 300000
AREA_MAX = 1200000

def read_image(pth):
    # Wrap imread with path checks to avoid silent None images on invalid paths [web:189]
    p = Path(pth)
    print(f"[INFO] path={p} exists={p.exists()}")
    img = cv.imread(str(p), cv.IMREAD_COLOR)   
    if img is None:
        
        print("[ERROR] cv.imread returned None", file=sys.stderr)
        sys.exit(2)
    return img

def find_contours_safe(binary_u8):
    
   
    out = cv.findContours(binary_u8, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
   
 
    if len(out) == 2:
        contours, hierarchy = out
    else:
        _, contours, hierarchy = out
    # Hierarchy is shaped (1, N, 4) -> pick the first axis if present; may be None 
    hierarchy = hierarchy[0] if hierarchy is not None else None
    return contours, hierarchy

def build_two_inside_mask(img_bgr, thresh=80):
    # Convert to grayscale so thresholding works on luminance instead of color 
    gray = cv.cvtColor(img_bgr, cv.COLOR_BGR2GRAY)
    # Global binary threshold: >thresh => 255 else 0 (foreground/background separation)
    _, bin_img = cv.threshold(gray, thresh, 255, cv.THRESH_BINARY)
    # Invert so objects to trace are white (OpenCV finds contours on white blobs) 
    inv = cv.bitwise_not(bin_img)

    # Find all contours from the inverted binary (pass a copy because findContours may modify input) 
    contours, _ = find_contours_safe(inv.copy())

    # Build a list of (index, area) for contours whose pixel area is within limits
    filtered = [(i, cv.contourArea(c)) for i, c in enumerate(contours)
                if AREA_MIN <= cv.contourArea(c) <= AREA_MAX]
    # Sort by area descending to get the biggest two in the permitted range 
    filtered.sort(key=lambda t: t[1], reverse=True)
    top2_idx = [idx for idx, _ in filtered[:2]]  # Keep only indices of the top two

    # Initialize a single‑channel mask (uint8) filled with zeros (black) [web:181]
    mask = np.zeros(gray.shape, np.uint8)
    if top2_idx:
        # Rasterize the interiors of the two selected contours onto the mask (white=255) 
        cv.drawContours(mask, [contours[i] for i in top2_idx], contourIdx=-1,
                        color=255, thickness=cv.FILLED)  # FILLED -> solid interior
    # The returned mask is white inside the chosen contours, black elsewhere 
    return mask

def whiten_inside(img_bgr, mask):
    # Copy original to preserve input
    out = img_bgr.copy()
    # Overwrite only masked pixels with pure white; leave others unchanged 
    out[mask > 0] = (255, 255, 255)
    return out

def show_and_save(outdir, images):
    # Ensure output folder exists; parents=True creates missing directories 
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    # Save each image; imwrite returns a boolean indicating success 
    for name, im in images.items():
        ok = cv.imwrite(str(outdir / name), im)
        print(f"[SAVE] {name}: {ok}")
    # Display each result in resizable windows for inspection 
    for name, im in images.items():
        cv.namedWindow(name, cv.WINDOW_NORMAL)
        cv.imshow(name, im)
    # waitKey processes GUI events and waits for a key press before closing 
    cv.destroyAllWindows()

def main():
    # Parse CLI arguments: input path, output folder, and threshold value 
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--image", required=True, help="path to input image")
    ap.add_argument("-o", "--outdir", default="out_whiten_inside", help="output folder")
    ap.add_argument("--thresh", type=int, default=80, help="binary threshold (0-255)")
    args = ap.parse_args()

    # Load image and build the mask for the two selected interiors 
    img = read_image(args.image)
    mask_inside2 = build_two_inside_mask(img, thresh=args.thresh)

    # Apply whitening only inside the mask to produce the final result image 
    result = whiten_inside(img, mask_inside2)

    # Optional visualization: paint masked region yellow on a copy for QA 
    vis = img.copy()
    vis[mask_inside2 > 0] = (0, 255, 255)

    # Save and show outputs: the binary mask, the whitened image, and an overlay view
    show_and_save(args.outdir, {
        "selected_mask.png": mask_inside2,
        "whitened.png": result,
        "overlay.png": vis
    })

if __name__ == "__main__":
    # Entry point when invoked as a script 
    main()
