# VESTIRE — Personal Fashion Stylist

A multimodal fashion stylist app

> **Architecture in this build:** all heavy ML (PyTorch / FAISS / YOLOv8 / CLIP / MTCNN) was deliberately replaced with a single Gemini 2.5 Flash multimodal pipeline (per user choice). All persistent state (wardrobe, saved outfits, profile, preferences) lives **in the browser via `localStorage`** — the FastAPI backend is a thin proxy.

## Stack
- **Backend:** FastAPI + Google Gemini SDK calling Gemini 2.5 Flash
- **Frontend:** React (CRA) + Tailwind + shadcn primitives, `Cormorant Garamond` + `Outfit` typography, dark Swiss-brutalist editorial theme
- **Storage:** Browser `localStorage` (no DB)

## Run
Backend (already supervisor-managed at `:8001`):
```bash
cd /app/backend && uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```
Frontend:
```bash
cd /app/frontend && yarn install && yarn start
```

## Environment
`/app/backend/.env`:
```
GEMINI_API_KEY=AIza...   # user supplied
GEMINI_MODEL=gemini-2.5-flash
```

## API
| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | health + gemini status |
| GET | `/api/labels` | clothing label vocabulary |
| POST | `/api/style/item` | classify + recommend from a single item photo |
| POST | `/api/style/person` | analyze full-body photo + recommend top/bottom |
| POST | `/api/skin/analyze` | advisory skin tone + palette |
| POST | `/api/explain` | Gemini natural-language outfit reasoning |

All image-bearing requests use base64 (`image_b64`, `mime`) — see `/app/frontend/src/lib/api.js`.

### Example
```bash
curl -X POST $REACT_APP_BACKEND_URL/api/style/item \
  -H 'Content-Type: application/json' \
  -d '{"image_b64":"<base64>","mime":"image/jpeg","occasion_text":"art opening","use_skin":false,"mode":"catalog"}'
```

Response shape includes `prediction_resnet`, `prediction_effnet`, `prediction_ensemble`, `dominant_colors`, `recommendations[]` with per-rec `scores={img_score,txt_score,color_score,skin_score,final_score}` and `reasons[]`, plus `explanation_text`.

## Plugging in your own ML checkpoints
The current build uses Gemini for classification/embeddings. To restore the original PyTorch + FAISS pipeline:
1. Drop your files into `/app/backend/models/` and `/app/backend/index/`:
   - `models/resnet18_best.pt`
   - `models/effb0_best.pt`
   - `index/clip_faiss.index`
   - `index/clip_emb.npy`
   - `index/meta.csv` (with `label` column + relative paths)
2. Add a `MODEL_BACKEND=local` env var and branch in `server.py` between local model paths and Gemini.
3. Implement `path-repair`: read `DATA_ROOT` from env, join with relative paths from `meta.csv`.

## Frontend tabs
`Item Photo`, `Person Photo`, `Wardrobe`, `Saved Outfits`, `Profile`. The Profile tab handles skin-tone analysis + palette + manual undertone override.

## Notes
- Color harmony, skin-undertone scoring and explainability are produced by Gemini in a single structured-JSON response.
- The "ensemble" of two classifier predictions is emulated by Gemini for UI fidelity.
- The app is fully usable offline for wardrobe/outfit browsing once items are stored in `localStorage`.
