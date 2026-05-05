# 🏛️ ClothyRec — AI Personal Fashion Stylist

**ClothyRec** is a premium, high-performance AI fashion assistant designed with a sophisticated Swiss-Brutalist editorial aesthetic. It combines state-of-the-art computer vision models with the conversational intelligence of Gemini AI to provide precise, context-aware styling advice.

---

## 🚀 The Hybrid AI Architecture

ClothyRec utilizes a powerful hybrid approach, blending local machine learning inference with cloud-based generative AI:

### 1. The Computer Vision Core (Local PyTorch)
- **Classification Ensemble:** Combines **ResNet-18** and **EfficientNet-B0** for highly accurate garment identification.
- **Deep Embeddings:** Uses **OpenCLIP (ViT-B/32)** to generate 512-dimensional visual feature vectors.
- **Similarity Search:** Powered by **FAISS**, performing sub-millisecond retrieval across thousands of catalog items.
- **Human Geometry:** **YOLOv8 Pose** for body segment detection and **MTCNN** for precise facial analysis (skin-tone extraction).

### 2. The Conversational Stylist (Gemini AI)
- **Contextual Reasoning:** An integrated Gemini-powered chatbot that acts as "Atelier," your personal stylist.
- **Data Exchange:** The chatbot is context-aware—it "sees" your latest wardrobe analysis, skin profile, and saved outfits to generate intelligent, personalized styling reasoning.
- **Explanation Engine:** Translates raw ML scores (harmony, skin-match, occasion fit) into natural language advice.

---

## 🎨 Design Philosophy
Inspired by high-fashion magazines and Swiss minimalism:
- **Aesthetic:** Dark Zinc-950 palette, high-contrast white/black UI, and grain overlays.
- **Experience:** Micro-animations, intersection-reveal hooks, and interactive "scroll-progress" indicators.
- **Agnostic Persistence:** All user data (history, skin profile, bookmarks) is stored via `localStorage` for privacy and speed.

---

## 🛠️ Tech Stack

### Backend
- **Framework:** FastAPI
- **ML Libraries:** PyTorch, Torchvision, Ultralytics (YOLOv8), FaceNet-PyTorch, Timm, Open-CLIP, FAISS.
- **AI Integration:** Google GenAI SDK (Gemini).
- **Server:** Uvicorn.

### Frontend
- **Framework:** React 19 + Vite
- **Styling:** Tailwind CSS + Vanilla CSS (Swiss-Brutalist theme).
- **Icons:** Lucide-React.
- **API:** Fetch API with Vite Proxying.

---

## ⚡ Setup & Run

### 1. Prerequisites
- Python 3.10+
- Node.js 18+
- [Optional] CUDA-enabled GPU (Models will fallback to CPU automatically).

### 2. Backend Setup
```bash
cd backend
# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "GEMINI_API_KEY=your_key_here" > .env
echo "GEMINI_MODEL=gemini-2.5-flash" >> .env
echo "DATA_ROOT=D:/path/to/your/dataset" >> .env

# Run server (default port 8002)
python -m uvicorn app.main:app --port 8002 --reload
```

### 3. Frontend Setup
```bash
cd frontend
# Install dependencies
npm install

# Run dev server (default port 5173)
npm run dev
```

---

## 🛰️ API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/health` | `GET` | System health and ML model status. |
| `/api/style/item` | `POST` | Analyze a single garment and get pairings. |
| `/api/style/person` | `POST` | Analyze a full-body photo for top/bottom style. |
| `/api/skin/analyze` | `POST` | Extract undertones and generate color palettes. |
| `/api/chat` | `POST` | Talk to the AI Stylist (Gemini) with ML context. |

---

## 📦 Project Structure

```text
Atelier/
├── backend/
│   ├── app/
│   │   ├── ml/        # Neural network definitions & Registry
│   │   ├── routes/    # FastAPI Endpoints (style, skin, chat)
│   │   ├── services/  # Business logic & scoring engines
│   │   └── config.py  # Global settings & thresholds
│   └── main.py        # Entry point
├── frontend/
│   ├── src/
│   │   ├── components/ # Atomic UI & Floating Chat Widget
│   │   ├── pages/      # Stylist, Skin, Profile, & Chat views
│   │   ├── lib/        # API client, Hooks, & LocalStorage
│   │   └── App.tsx     # Layout & Navigation
└── README.md
```

---

## 📝 License
This project is for educational and stylistic exploration. All models and code are open-source.
