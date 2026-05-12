
---

## `PROJECT_DETAILS.md`

```md
# PROJECT_DETAILS — Personal Fashion Stylist (Full Technical Documentation)

This document explains **every module**, file format, scoring function, and the full pipeline end-to-end.  
It’s intended for:
- viva preparation,
- future extension (wardrobe-only, shoes/accessories, weather),
- and as a “single source of truth” for the project.

---

## 1) Project Goal (End-to-End)
Build a system that can:
1) understand fashion images,
2) classify clothing categories,
3) recommend matching items using embeddings,
4) generate outfits under constraints (occasion, preferences),
5) personalize via user info (skin tone, body context),
6) support both **item photos** and **full-body photos**.

---

## 2) System Overview (Architecture)

### Inputs
- **Item Photo Mode (A):** product/closet image (single clothing item)
- **Person Photo Mode (B):** full-body photo (standing preferred)

### Core Outputs
- predicted category + confidence (ResNet18 / EfficientNet / Ensemble)
- recommended matches (CLIP+FAISS)
- outfit suggestions (MVP: top+bottom)
- explainability signals (scores + reason tags)
- optional: Gemini explanation text

### Components
1) **Classifier module** (CNN / ResNet18 / EfficientNet)
2) **Embedding module** (CLIP)
3) **Retrieval module** (FAISS)
4) **Outfit generator** (rules + scoring)
5) **Personalization module** (skin undertone)
6) **B-mode cropping** (pose → top/bottom crops)
7) **Guardrails** (OOD + confidence threshold + weak-match threshold)
8) **Persistence** (Drive saving, index saving)

---

## 3) Dataset (Main)
### Dataset: E-Commerce Men’s Clothing Dataset (KaggleHub)
ID: `prashantsharma526/e-commerce-mens-clothing-dataset`

Folder layout:
- `dataset_clean/<class_name>/*.jpg`

Classes (8):
- `casual_shirts`, `formal_shirts`
- `printed_tshirts`, `solid_tshirts`, `printed_hoodies`
- `jeans`, `men_cargos`, `formal_pants`

Splits:
- Stratified train/val/test
- Example run: Train 6037, Val 1294, Test 1294

---

## 4) Classification Module

### Models
1) **SimpleCNN** (baseline)
- small conv stack + adaptive avg pool + linear head
- purpose: baseline comparison (shows value of transfer learning)

2) **ResNet18** (transfer learning)
- pretrained on ImageNet
- final layer replaced with `Linear(in_features, num_classes)`
- best test generalization in our run

3) **EfficientNet-B0** (transfer learning via timm)
- often high accuracy, but can overfit depending on run

### Training Setup (typical)
- image size: 224
- transforms:
  - Resize(224,224)
  - RandomHorizontalFlip
  - ColorJitter (small)
  - Normalize(ImageNet)
- optimizer: AdamW
- mixed precision: AMP
- checkpoint selection: best **val macro-F1**

### Evaluation Metrics
- Accuracy
- Macro F1 (preferred due to class balance/robustness)
- Confusion matrix

### Model Selection Rule (important for viva)
Choose final model based on **test macro-F1**:
- validation can be optimistic; test reflects generalization.

---

## 5) Embedding + Retrieval Module (Recommendation Engine)

### CLIP model
- `open_clip` ViT-B/32, pretrained `laion2b_s34b_b79k`
- image embedding dimension: 512
- we normalize embeddings:
  - `f = f / ||f||`
- for normalized vectors:
  - cosine similarity == inner product

### FAISS Index
- `faiss.IndexFlatIP(512)`
- search returns top-k nearest neighbors quickly.

### Files saved (Index Package)
- `clip_faiss.index`  (FAISS index)
- `clip_emb.npy`      (N x 512 float32 normalized embeddings)
- `meta.csv`          (row-aligned metadata: path,label,y)

#### IMPORTANT: Path Stability
If `meta.csv` contains absolute paths from one runtime, they break in a new runtime.
Recommended fix:
- store **relative paths** in meta
- reconstruct absolute path using configured `DATA_ROOT` at runtime
OR
- re-download dataset and “repair” paths by replacing prefix.

---

## 6) Occasion Free-Text Support (No fixed labels required)

Problem:
- Users type arbitrary occasion text (e.g., “farewell party”, “interview”)

Solution:
- Use CLIP text embedding for user text.
- Use templates to “ground” text in clothing terms:
  - `men's {occasion} outfit pants`
  - `men's {occasion} trousers`
  - `men's {occasion} jeans outfit`

Score:
- `txt_score = cosine(emb(candidate_image), emb(occasion_text))`

Combine with image similarity:
- `score = 0.70*img_score + 0.30*txt_score`

Where:
- `img_score` comes from FAISS similarity (image-to-image)
- `txt_score` from CLIP text (image-to-text alignment)

---

## 7) Color Harmony Re-ranking

Goal:
Improve “goes well with” beyond raw similarity.

We compute item HSV stats on non-background pixels:
- convert image to HSV
- mask likely background pixels (low saturation / very bright)
- take mean H,S,V

Harmony heuristics (example):
- if top is colorful (high S), prefer neutral bottoms (low S)
- prefer brightness contrast (V difference)
- penalize large hue difference only when bottom is also colorful

Produces `harmony_score` ∈ roughly [0..1+].

---

## 8) Skin Tone / Undertone Personalization (No Training)

### Steps
1) Face detection: **MTCNN** (`facenet-pytorch`)
2) Cheek region sampling (inside face bbox, left/right cheek rectangles)
3) Skin pixel filtering: YCrCb threshold mask (basic)
4) Convert skin pixels to Lab:
   - `L` → tone depth estimate (very light/light/medium/tan/deep)
   - `b-128` → undertone warm/cool:
     - b > 128 (positive delta): warm (yellow)
     - b < 128 (negative delta): cool (blue)

Outputs:
- `tone_detail`
- `undertone` + strength
- estimated skin RGB/HEX
- palette suggestions (best/avoid colors)
- approximate face shape (rough estimate using face bbox ratio)

**Ethics Note**
- System does NOT infer race/ethnicity.
- Output is advisory and sensitive to lighting; user can override.

Skin score:
- classify item color family (warm/cool/neutral) from HSV
- neutral colors score high for everyone
- matching undertone scores highest

---

## 9) Full-body Photo Mode (B) — Crop top/bottom via Pose (No Training)

Model:
- **YOLOv8 pose** (`yolov8n-pose.pt`), pretrained

Process:
1) detect person + keypoints
2) define crop rectangles using keypoints:
   - top crop: shoulders → hips region
   - bottom crop: hips → ankles region
3) add padding
4) save:
   - `/content/top_crop.jpg`
   - `/content/bottom_crop.jpg`

Then run the exact same pipeline as item mode on each crop:
- classify crop
- recommend matching items via CLIP+FAISS
- re-rank via occasion + color + skin

---

## 10) Guardrails / Input Validation

### 10.1 OOD (“not clothing”) check using CLIP
Compute similarity of image embedding against:
- clothing prompts vs non-clothing prompts
Reject if:
- `cloth_score <= non_score + margin`

### 10.2 Classifier confidence threshold
If ensemble confidence < threshold:
- request clearer image or manual label selection

### 10.3 Weak recommendation threshold
If top result similarity is too low:
- return “no strong match found; expand wardrobe/index”

---

## 11) Outfit Generator (MVP: 2-piece)

Because dataset lacks shoes:
- top classes: shirts/tshirts/hoodies
- bottom classes: jeans/cargos/formal pants

Flow:
- if input predicted as top → recommend bottoms
- if input predicted as bottom → recommend tops

Final scoring (example):
`final = 0.65*CLIP_hybrid + 0.20*harmony + 0.15*skin`

Where CLIP_hybrid already includes occasion text.

---

## 12) Persistence (Drive Saving)
Saved to:
- `Drive/MyDrive/PersonalFashionStylist/models/`
- `Drive/MyDrive/PersonalFashionStylist/clip_index/fashion_reco_index/`

Restore steps:
- mount Drive
- copy to `/content/stylist_runtime`
- load models + index + meta/emb

---

## 13) Optional: Gemini Integration (Text explanations)
Gemini is used only for:
- natural language explanations,
- accessories suggestions,
- “why this matches” narrative.

Rules:
- API key stored in backend env var only.
- If key missing, fallback to rule-based explanation.

Suggested prompt:
- provide structured JSON: occasion, skin_profile, predicted item, recommended candidates with score breakdown.
- ask for concise bullet suggestions + avoid tip.

---

## 14) Full-stack Deployment Plan (FastAPI + React)
Backend responsibilities:
- load models once at startup
- inference endpoints:
  - /style/item
  - /style/person
  - /skin/analyze
  - /wardrobe/upload + list
- static serving for recommended images/crops
- Gemini call in backend only

Frontend responsibilities:
- upload UI (drag-drop)
- occasion free-text
- toggles (wardrobe-only vs catalog, use skin)
- result cards + score breakdown + explanation drawer

---


## 16) Extension Ideas
- Add shoes/accessories dataset; extend to 3-piece outfit
- Train/fine-tune a fashion compatibility model (e.g., Polyvore-style datasets)
- Add weather API (Open-Meteo) and filter materials/layers
- Add wardrobe-only indexing with user upload + incremental FAISS update