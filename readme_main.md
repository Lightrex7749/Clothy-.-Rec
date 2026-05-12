# Personal Fashion Stylist (Open-Source AI) — Colab + PyTorch + CLIP + FAISS

An AI-based Personal Fashion Stylist that:
- understands clothing images (classification),
- recommends matching items (CLIP embeddings + FAISS),
- generates outfit suggestions (rule + scoring),
- supports free-text occasion input,
- optionally personalizes using skin tone (estimated from face photo),
- supports full-body photos by cropping top/bottom using pose.

Built using **open-source models** and **free tools** (Google Colab GPU).  
Optional: Gemini API for natural-language explanations (backend-only).

---

## Demo Capabilities (What it can do)
### Input Types
- **A) Item photo** (shirt/pants product image or closet photo)
- **B) Full-body person photo** → auto-crops **Top** and **Bottom** → runs recommendations

### Outputs
- Predictions from **ResNet18**, **EfficientNet-B0**, and **Ensemble** (+ confidence)
- Recommended matching items using **CLIP + FAISS**
- Outfit suggestions (MVP: **Top + Bottom**)
- Explainable scoring breakdown:
  - `img_score` (CLIP image similarity)
  - `txt_score` (occasion free-text relevance via CLIP text)
  - `harmony` (color harmony score)
  - `skin` (skin undertone compatibility score)
  - `final score`

### Guardrails
- Rejects non-fashion/non-person images using CLIP “clothing vs non-clothing” check
- Confidence thresholds to avoid wrong predictions on unclear inputs

---

## Dataset Used (Main)
**E-Commerce Men’s Clothing Dataset (8 classes)**  
KaggleHub dataset:
`prashantsharma526/e-commerce-mens-clothing-dataset`

Classes:
- casual_shirts, formal_shirts
- printed_tshirts, solid_tshirts, printed_hoodies
- jeans, men_cargos, formal_pants

---

## Models Used
### Classification
- Baseline: Custom CNN (from scratch)
- Transfer Learning: ResNet18 (ImageNet)
- Transfer Learning: EfficientNet-B0 (timm)

### Recommendation
- CLIP: `open_clip` ViT-B/32 (`laion2b_s34b_b79k`)
- Retrieval: FAISS cosine similarity via `IndexFlatIP` on normalized embeddings

### Personalization (No training required)
- Skin tone/undertone: **MTCNN face detection** + cheek sampling + Lab color stats
- Full-body cropping: **YOLOv8 pose** (pretrained) to crop top/bottom regions

---

## Results (Example from our runs)
- **ResNet18** achieved ~0.90 test accuracy / macro-F1 (best generalization in our run)
- EfficientNet-B0 achieved high validation but slightly lower test (depends on run/seed)
- Baseline CNN significantly lower, used as comparison baseline

> Final model selection should be based on **test macro-F1** (generalization), not only validation.

---

## Repository Structure (Suggested)
```text
.
├── notebooks/
│   ├── 01_TRAIN.ipynb
│   ├── 02_INDEX.ipynb
│   └── 03_DEMO.ipynb
├── models/                    # (optional in repo; usually store in Drive)
├── index/                     # faiss + embeddings + meta
├── README.md
└── PROJECT_DETAILS.md