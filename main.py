import cv2
import numpy as np
import argparse
import os
from scipy.ndimage import distance_transform_edt


# -----------------------------
# Utils
# -----------------------------


def ensure_dir(p):
    os.makedirs(p, exist_ok=True)


def load_rgb(path):
    return cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2RGB)


# -----------------------------
# Automatic foreground cutout
# -----------------------------


def extract_foreground_mask(img):
    """
    GrabCut-based foreground extraction
    """
    h, w = img.shape[:2]

    mask = np.zeros((h, w), np.uint8)

    # Center-biased rectangle (safe default)
    rect = (int(w * 0.15), int(h * 0.05), int(w * 0.7), int(h * 0.9))

    bgd = np.zeros((1, 65), np.float64)
    fgd = np.zeros((1, 65), np.float64)

    cv2.grabCut(img, mask, rect, bgd, fgd, 5, cv2.GC_INIT_WITH_RECT)

    mask = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 1.0, 0.0).astype(
        np.float32
    )

    # Clean edges
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.GaussianBlur(mask, (5, 5), 0)

    return mask


# -----------------------------
# Shadow generator
# -----------------------------


def generate_shadow(fg_rgb, mask, bg_rgb, angle, elevation):
    H, W = bg_rgb.shape[:2]

    # Resize foreground & mask
    fg_rgb = cv2.resize(fg_rgb, (W, H))
    mask = cv2.resize(mask, (W, H))

    # -----------------------------
    # Light direction
    # -----------------------------
    theta = np.deg2rad(angle)
    phi = np.deg2rad(elevation)

    light_dir = np.array([np.cos(theta), np.sin(theta)])

    shadow_len = 220 / max(0.2, np.tan(phi))

    dx = int(light_dir[0] * shadow_len)
    dy = int(light_dir[1] * shadow_len)

    # -----------------------------
    # Contact point (feet)
    # -----------------------------
    ys, xs = np.where(mask > 0.2)
    foot_y = ys.max()
    foot_x = int(xs.mean())

    # -----------------------------
    # Project silhouette
    # -----------------------------
    shadow = cv2.warpAffine(
        mask, np.float32([[1, 0, dx], [0, 1, dy]]), (W, H), flags=cv2.INTER_LINEAR
    )

    # -----------------------------
    # Distance along shadow
    # -----------------------------
    yy, xx = np.meshgrid(np.arange(H), np.arange(W), indexing="ij")

    dist = (xx - foot_x) * light_dir[0] + (yy - foot_y) * light_dir[1]
    dist = np.clip(dist, 0, None)

    # -----------------------------
    # Soft shadow falloff
    # -----------------------------
    opacity = np.exp(-dist / 160)

    # Blur passes (distance buckets)
    blurred = np.zeros_like(shadow)

    for r in [3, 7, 15, 30]:
        blurred += cv2.GaussianBlur(shadow, (0, 0), r)

    blurred /= 4.0
    shadow = blurred * opacity

    # -----------------------------
    # Contact shadow (sharp)
    # -----------------------------
    inv = 1 - mask
    contact_dist = distance_transform_edt(inv)
    contact = np.exp(-contact_dist / 4.0)
    contact[yy < foot_y - 5] = 0

    shadow = np.maximum(shadow, contact * 0.85)
    shadow = np.clip(shadow, 0, 1)

    # -----------------------------
    # Composite
    # -----------------------------
    comp = bg_rgb.copy()
    comp = comp * (1 - shadow[..., None])
    comp = comp * (1 - mask[..., None]) + fg_rgb * mask[..., None]

    return (
        comp.astype(np.uint8),
        (shadow * 255).astype(np.uint8),
        (mask * 255).astype(np.uint8),
    )


# -----------------------------
# Main
# -----------------------------


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fg", required=True)
    parser.add_argument("--bg", required=True)
    parser.add_argument("--angle", type=float, default=135)
    parser.add_argument("--elevation", type=float, default=35)
    args = parser.parse_args()

    ensure_dir("output")

    fg = load_rgb(args.fg)
    bg = load_rgb(args.bg)

    print("Extracting foreground mask...")
    mask = extract_foreground_mask(fg)

    composite, shadow_only, mask_debug = generate_shadow(
        fg, mask, bg, args.angle, args.elevation
    )

    cv2.imwrite("output/composite.png", cv2.cvtColor(composite, cv2.COLOR_RGB2BGR))
    cv2.imwrite("output/shadow_only.png", shadow_only)
    cv2.imwrite("output/mask_debug.png", mask_debug)

    print("✅ Done. Check /output folder")


if __name__ == "__main__":
    main()
