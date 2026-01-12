# Realistic Shadow Generator

A mini image compositing app that generates **realistic, silhouette-accurate shadows** for a foreground subject composited onto a background image, with **directional lighting**, **contact shadows**, and **distance-based soft falloff**.

This project was built as a technical assessment to demonstrate real-world shadow math, image compositing, and engineering judgment — not fake drop-shadows or simple blur offsets.

---

## ✨ Features

### ✅ Core Requirements
- **Directional light control**
  - Light angle (0–360°)
  - Light elevation (0–90°)
- **Silhouette-accurate shadows**
  - Shadow matches the exact subject outline
- **Contact shadow**
  - Sharp and dark near the feet / ground contact
  - Rapid falloff with distance
- **Soft shadow falloff**
  - Blur increases as the shadow moves farther away
  - Opacity decreases with distance
- **Debug outputs**
  - Shadow-only image
  - Foreground mask visualization

### ⭐ Bonus
- Automatically handles **JPG foregrounds with no alpha**
  - Uses GrabCut to extract the subject mask
- Designed to be easily extended for **depth-map-based warping**

---

## 🧠 Approach & Shadow Math

### 1. Foreground Extraction
The provided foreground image is a standard JPG with no alpha channel.  
To obtain a clean silhouette, the subject is automatically extracted using **GrabCut**, initialized with a center-biased rectangle.

This produces a soft, realistic mask suitable for compositing and shadow generation.

---

### 2. Directional Light Model
The light is defined by:
- **Angle (θ)** — direction on the ground plane
- **Elevation (φ)** — height of the light above the horizon

The 2D light direction is computed as:
```math
L = (cos θ, sin θ)
```
Shadow length increases as elevation decreases:
```math
shadow_length ∝ 1 / tan(φ)
```
This mimics how low sun angles produce long shadows.

---

### 3. Shadow Projection
The extracted silhouette mask is **projected along the light direction** using an affine transform.  
This ensures the shadow:
- Matches the subject’s shape exactly
- Moves consistently with light direction and elevation

---

### 4. Contact Shadow
To ground the subject, a **contact shadow** is generated near the feet:

- Distance transform is applied to the inverse foreground mask
- Shadow intensity decays exponentially from the contact area
- Limited to a small vertical region near the ground

This produces a sharp, dark shadow where the subject touches the surface.

---

### 5. Soft Shadow Falloff
As shadows move farther from the contact point:
- **Blur radius increases**
- **Opacity decreases**

Opacity falloff is modeled as:
```math
opacity = exp(-distance / k)
```
Multiple Gaussian blur passes are combined to simulate increasing softness with distance, avoiding artifacts from per-pixel blurring.

---

### 6. Final Compositing
The final image is composed in this order:
1. Background
2. Shadow layer (darkened background)
3. Foreground subject

All blending is done using per-pixel alpha.

---

## 🗂 Project Structure

```
shadow-generator/
│
├── main.py
├── README.md
├── requirements.txt
│
├── input/
│   ├── foreground.jpg
│   └── background.jpg
│
└── output/
    ├── composite.png
    ├── shadow_only.png
    └── mask_debug.png
```

---

## 🚀 How to Run

### Install dependencies
```bash
pip install opencv-python numpy scipy
```
### Run from CLI
```bash
python main.py \
  --fg input/foreground.jpg \
  --bg input/background.jpg \
  --angle 135 \
  --elevation 35
```

---

## 🖼 Outputs

After running, the following files are generated in `/output`:
-	**composite.png** — final composited image
-	**shadow_only.png** — shadow layer (debug)
-	**mask_debug.png** — extracted foreground mask (debug)

---

## 🧪 Tested With

-	JPG foreground images (no alpha)
-	Large background images with different resolutions
-	Multiple light angles and elevations

---

## 🔧 Possible Extensions

-	Depth-map-based shadow warping for uneven surfaces
-	Multiple light sources
-	Ground plane estimation
-	UI controls (PyQt or Web)

---

## 📌 Notes

This project prioritizes **believability and robustness** over physically perfect simulation, matching real-world production compositing pipelines.