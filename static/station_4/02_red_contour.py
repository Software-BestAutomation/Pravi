# python 02_red_contour.py --image "D:/Pravi/burr_images/new_glass/station3/dataset/9_oct_25/VCXG.2-32C/image0000389.bmp"

import cv2 as cv
import numpy as np
import argparse, sys
from pathlib import Path

AREA_MIN = 300_000
AREA_MAX = 1_200_000

def read_image(pth):
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
    hierarchy = hierarchy[0] if hierarchy is not None else None
    return contours, hierarchy

def build_two_inside_mask(img_bgr, thresh=80):
    gray = cv.cvtColor(img_bgr, cv.COLOR_BGR2GRAY)
    _, bin_img = cv.threshold(gray, thresh, 255, cv.THRESH_BINARY)
    inv = cv.bitwise_not(bin_img)

    contours, _ = find_contours_safe(inv.copy())

    # Filter by area range and take the two largest by area
    filtered = [(i, cv.contourArea(c)) for i, c in enumerate(contours)
                if AREA_MIN <= cv.contourArea(c) <= AREA_MAX]
    filtered.sort(key=lambda t: t[1], reverse=True)
    top2_idx = [idx for idx,_ in filtered[:2]]

    mask = np.zeros(gray.shape, np.uint8)
    if top2_idx:
        cv.drawContours(mask, [contours[i] for i in top2_idx], -1, 255, thickness=cv.FILLED)
    return mask  # white inside the 2 contours

def whiten_inside(img_bgr, mask):
    out = img_bgr.copy()
    out[mask > 0] = (255, 255, 255)  # make interior white
    return out

def show_and_save(outdir, images):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    for name, im in images.items():
        ok = cv.imwrite(str(outdir / name), im)
        print(f"[SAVE] {name}: {ok}")
    for name, im in images.items():
        cv.namedWindow(name, cv.WINDOW_NORMAL)
        cv.imshow(name, im)
    cv.waitKey(0)
    cv.destroyAllWindows()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-i","--image", required=True)
    ap.add_argument("-o","--outdir", default="out_whiten_inside")
    ap.add_argument("--thresh", type=int, default=80)
    args = ap.parse_args()

    img = read_image(args.image)
    mask_inside2 = build_two_inside_mask(img, thresh=args.thresh)
    result = whiten_inside(img, mask_inside2)

    # Optional debug view: mask overlay on original
    vis = img.copy()
    vis[mask_inside2>0] = (0,255,255)  # highlight selected interiors

    show_and_save(args.outdir, {
        "selected_mask.png": mask_inside2,
        "whitened.png": result,
        "overlay.png": vis
    })

if __name__ == "__main__":
    main()
