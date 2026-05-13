# 🏛️ ClothyRec — AI Personal Fashion Stylist

ClothyRec is a full‑stack AI fashion assistant that blends local computer vision with Gemini-powered reasoning and prompt optimization. It analyzes garments or full‑body photos, recommends matching outfits, extracts skin tone palettes, and can generate styled looks from a reference image and a refined prompt.

---

## ✨ Key Features

- **Item + Person Styling**: Classify garments and recommend matching items, or analyze a full‑body photo and recommend for top + bottom.
- **Skin Tone Analysis**: Extract undertone and palette from a selfie.
- **AI Stylist Chat**: Gemini‑powered conversational stylist that uses local ML context.
- **Prompt Presets + Optimization**: Curated prompt presets, gender‑aware prompt refinement, and a final prompt editor.
- **AI Look Generator**: Generate new looks from a photo + prompt (Gemini image model).

---

## 🧠 Architecture Overview

### 1) Local Computer Vision Core (PyTorch)
- **Classification Ensemble**: ResNet‑18 + EfficientNet‑B0
- **Embeddings**: OpenCLIP (ViT‑B/32) 512‑D vectors
- **Retrieval**: FAISS similarity search
- **Body / Face**: YOLOv8 Pose (`yolov8s-pose.pt`, cropping), MTCNN (skin analysis)

### 2) Gemini Services
- **Chat**: Gemini generates stylist responses with ML context
- **Prompt Optimization**: Gemini rewrites prompts based on gender + extra instructions
- **Image Generation**: Gemini image model generates new looks

---

## 🖥️ Tech Stack

**Backend**: FastAPI, PyTorch, OpenCLIP, FAISS, Ultralytics, FaceNet‑PyTorch, Google GenAI SDK

**Frontend**: React 19, Vite, Tailwind CSS, Lucide Icons

---

## 📦 Project Structure

```text
Atelier/
├── backend/
│   ├── app/
│   │   ├── ml/         # model registry, inference, FAISS
│   │   ├── routes/     # FastAPI endpoints
│   │   ├── services/   # business logic and helpers
│   │   └── config.py   # env + defaults
│   └── static/         # uploads + prompt images
├── frontend/
│   ├── src/
│   │   ├── components/ # UI blocks
│   │   ├── pages/      # Chat, Stylist, Skin, Profile
│   │   └── lib/        # API + storage
├── data/               # dataset (ignored by git)
├── models/             # weights (ignored by git)
└── README.md
```

---

## ⚙️ Environment Variables

Create a `backend/.env` file:

```dotenv
GEMINI_CHAT_API_KEY=your_chat_key_here
GEMINI_IMAGE_API_KEY=your_image_key_here
GEMINI_MODEL=gemini-2.5-flash
GEMINI_IMAGE_MODEL=your_image_model
GEMINI_CHAT_RPM=60
GEMINI_IMAGE_RPM=20
GEMINI_RATE_WINDOW_SEC=60
YOLO_POSE_MODEL=yolov8s-pose.pt
CORS_ORIGINS=http://localhost:5173,http://localhost:3000,*
DATA_ROOT=D:/path/to/your/dataset
```

Notes:
- `.env` is loaded from `backend/.env`.
- `GEMINI_IMAGE_MODEL` must be image-capable (see Gemini model list for your account).
- `YOLO_POSE_MODEL` can be a filename (resolved under `models/`) or an absolute path.
- Optional paths: `MODELS_DIR`, `INDEX_DIR`, `UPLOAD_DIR`, `V2_DIR`.

---

## 🚀 Setup & Run

### Backend
```bash
cd backend
pip install -r requirements.txt
cd ..
python -m uvicorn app.main:app --app-dir backend --port 8002 --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Frontend runs on http://localhost:5173 and proxies API calls to port 8002.

---

## 🧩 API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/health` | `GET` | System health + model status |
| `/labels` | `GET` | Class labels + v2 mode |
| `/api/style/item` | `POST` | Analyze a single garment |
| `/api/style/person` | `POST` | Analyze a full‑body photo |
| `/api/skin/analyze` | `POST` | Extract skin undertone + palette |
| `/api/gemini/text/chat` | `POST` | Stylist chat (Gemini) |
| `/api/gemini/text/optimize` | `POST` | Optimize prompt (gender + instructions) |
| `/api/gemini/image` | `POST` | Generate new looks from photo + prompt |
| `/api/prompts` | `GET` | Prompt presets + images |

---

## 💡 UI Highlights

- **AI Look Generator**: upload a photo, select a prompt preset, refine with gender + instructions, and generate results.
- **Chat**: real‑time stylist guidance with ML context.
- **Profile**: saved outfits, history, and skin profile.

---

## 📝 Notes

- Large datasets, models, and local files are ignored by git via `.gitignore`.
- If Gemini image generation returns no images, verify `GEMINI_IMAGE_MODEL` is correct.

---

## 🧪 Model Cache and Benchmark

Pre-download the YOLO pose model into `models/`:

```bash
python backend/scripts/download_models.py
```

Benchmark pose models on a full-body image:

```bash
python backend/scripts/benchmark_pose.py --image path/to/full_body.jpg
```

---

## ✅ Smoke Tests

These tests validate the Gemini endpoints in no-key mode:

```bash
pytest backend/tests/test_gemini_routes.py
```

---

## 📄 License

For educational and stylistic exploration.