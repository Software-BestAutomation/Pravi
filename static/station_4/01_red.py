# python 01_red.py --image "D:/Pravi/burr_images/new_glass/station3/dataset/9_oct_25/VCXG.2-32C/image0000389.bmp"
# python red_area_filter.py --image "D:/Pravi/burr_images/new_glass/station3/dataset/9_oct_25/VCXG.2-32C/image0000389.bmp"

# python area_filter_show_save.py --image "D:/Pravi/burr_images/new_glass/station3/dataset/9_oct_25/VCXG.2-32C/image0000389.bmp"
import cv2 as cv
import numpy as np
import argparse, sys
from pathlib import Path

AREA_MIN = 300_000
AREA_MAX = 1_200_000

def read_image(path_str):
    p = Path(path_str)
    print(f"[INFO] path={p} exists={p.exists()}")
    img = cv.imread(str(p), cv.IMREAD_COLOR)
    if img is None:
        print("[ERROR] cv.imread returned None. Check path and permissions.", file=sys.stderr)
        sys.exit(2)
    return img

def find_contours_version_safe(binary_u8):
    # OpenCV 4.x returns (contours, hierarchy), 3.x returns (image, contours, hierarchy)
    found = cv.findContours(binary_u8, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
    if len(found) == 2:
        contours, hierarchy = found
    else:
        _, contours, hierarchy = found
    hierarchy = hierarchy[0] if hierarchy is not None else None
    return contours, hierarchy

def build_masks(img_bgr, thresh=80):
    gray = cv.cvtColor(img_bgr, cv.COLOR_BGR2GRAY)
    _, bin_img = cv.threshold(gray, thresh, 255, cv.THRESH_BINARY)
    inv = cv.bitwise_not(bin_img)

    contours, hierarchy = find_contours_version_safe(inv.copy())

    interior_mask = np.zeros(gray.shape, np.uint8)
    between_mask  = np.zeros(gray.shape, np.uint8)

    kept = []
    for i, cnt in enumerate(contours):
        a = cv.contourArea(cnt)
        if AREA_MIN <= a <= AREA_MAX:
            kept.append((i, a))
            cv.drawContours(interior_mask, [cnt], -1, 255, thickness=cv.FILLED)

    # Build annulus (parent minus all children) for each kept contour
    if hierarchy is not None:
        for i, _ in kept:
            child = hierarchy[i][2]  # first child or -1
            if child != -1:
                parent_fill = np.zeros_like(interior_mask)
                child_fill  = np.zeros_like(interior_mask)
                cv.drawContours(parent_fill, [contours[i]], -1, 255, cv.FILLED)
                cidx = child
                while cidx != -1:
                    cv.drawContours(child_fill, [contours[cidx]], -1, 255, cv.FILLED)
                    cidx = hierarchy[cidx][0]  # next sibling
                annulus = cv.bitwise_and(parent_fill, cv.bitwise_not(child_fill))
                between_mask = cv.bitwise_or(between_mask, annulus)

    print(f"[INFO] total_contours={len(contours)} kept_in_range={len(kept)}")
    return inv, contours, interior_mask, between_mask

def apply_processing(img_bgr, mask):
    # Example: visualize edges only inside mask
    edges = cv.Canny(cv.cvtColor(img_bgr, cv.COLOR_BGR2GRAY), 100, 200)
    edges_col = cv.cvtColor(edges, cv.COLOR_GRAY2BGR)
    masked_edges = cv.bitwise_and(edges_col, edges_col, mask=mask)
    out = img_bgr.copy()
    out[mask > 0] = cv.addWeighted(out[mask > 0], 0.6, masked_edges[mask > 0], 0.4, 0)
    return out

def imwrite_checked(path, image):
    ok = cv.imwrite(str(path), image)
    print(f"[SAVE] {path.name}: {ok}")
    if not ok:
        print(f"[ERROR] Failed to write {path}", file=sys.stderr)
    return ok

def show(title, img):
    cv.namedWindow(title, cv.WINDOW_NORMAL)
    cv.imshow(title, img)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--image", required=True, help="path to input image")
    ap.add_argument("-o", "--outdir", default="out_area_filtered", help="output folder")
    ap.add_argument("--thresh", type=int, default=80, help="binary threshold (0-255)")
    ap.add_argument("--mask", choices=["interior","between"], default="between", help="region to process")
    ap.add_argument("--no-show", action="store_true", help="do not show GUI windows")
    args = ap.parse_args()

    img = read_image(args.image)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    binary_inv, contours, interior_mask, between_mask = build_masks(img, thresh=args.thresh)

    work_mask = between_mask if args.mask == "between" else interior_mask
    result = apply_processing(img, work_mask)

    # Save outputs
    imwrite_checked(outdir / "binary_inverse.png", binary_inv)
    imwrite_checked(outdir / "mask_interior.png", interior_mask)
    imwrite_checked(outdir / "mask_between.png", between_mask)
    imwrite_checked(outdir / "processed.png", result)

    vis = img.copy()
    cv.drawContours(vis, contours, -1, (0,255,255), 2)
    imwrite_checked(outdir / "contours_overlay.png", vis)

    # Show windows
    if not args.no_show:
        show("processed", result)
        show("mask_between", between_mask)
        show("mask_interior", interior_mask)
        show("binary_inverse", binary_inv)
        show("contours_overlay", vis)
        cv.waitKey(0)  # wait for any key
        cv.destroyAllWindows()

if __name__ == "__main__":
    main()
