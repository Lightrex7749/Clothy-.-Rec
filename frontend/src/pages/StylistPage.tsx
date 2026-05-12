import { useState, useCallback } from 'react'
import { Loader2, Sparkles, Bookmark, BookmarkCheck } from 'lucide-react'
import Dropzone from '../components/Dropzone'
import ConfidenceBar from '../components/ConfidenceBar'
import RecommendationCard from '../components/RecommendationCard'
import type { StyleItemResponse, StylePersonResponse, Recommendation } from '../types/api'
import { apiStyleItem, apiStylePerson } from '../lib/api'
import { addHistoryEntry, saveBookmark, loadBookmarks } from '../lib/storage'
import { useReveal } from '../lib/hooks'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''

interface Props {
  mode: 'item' | 'person'
}

export default function StylistPage({ mode }: Props) {
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [occasion, setOccasion] = useState('')
  const [useSkin, setUseSkin] = useState(false)
  const [undertone, setUndertone] = useState('neutral')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [bookmarkedIds, setBookmarkedIds] = useState<Set<string>>(new Set())

  const [itemResult, setItemResult] = useState<StyleItemResponse | null>(null)
  const [personResult, setPersonResult] = useState<StylePersonResponse | null>(null)

  const resultsRef = useReveal()

  const handleFile = (f: File, prev: string) => {
    setFile(f); setPreview(prev)
    setItemResult(null); setPersonResult(null); setError(null)
  }

  // Create a small preview data URL for history
  const createThumbnail = useCallback((f: File): Promise<string> => {
    return new Promise(resolve => {
      const reader = new FileReader()
      reader.onload = () => {
        const img = new Image()
        img.onload = () => {
          const c = document.createElement('canvas')
          const size = 80
          c.width = size; c.height = size
          const ctx = c.getContext('2d')!
          const scale = Math.max(size / img.width, size / img.height)
          const w = img.width * scale, h = img.height * scale
          ctx.drawImage(img, (size - w) / 2, (size - h) / 2, w, h)
          resolve(c.toDataURL('image/jpeg', 0.5))
        }
        img.src = reader.result as string
      }
      reader.readAsDataURL(f)
    })
  }, [])

  const generate = async () => {
    if (!file) return
    setLoading(true); setError(null)
    try {
      const thumb = await createThumbnail(file)
      if (mode === 'item') {
        const res = await apiStyleItem(file, occasion, 'catalog', useSkin, undertone)
        setItemResult(res)
        addHistoryEntry({
          mode: 'item', occasion,
          previewUrl: thumb,
          predictedLabel: res.predictions?.ensemble?.label,
          confidence: res.predictions?.ensemble?.confidence,
          direction: res.direction ?? undefined,
          recCount: res.recommendations.length,
        })
      } else {
        const res = await apiStylePerson(file, occasion, useSkin, undertone)
        setPersonResult(res)
        addHistoryEntry({
          mode: 'person', occasion,
          previewUrl: thumb,
          predictedLabel: res.top_results?.predictions?.ensemble?.label,
          confidence: res.top_results?.predictions?.ensemble?.confidence,
        })
      }
    } catch (e: any) {
      setError(e.message || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  const handleBookmark = (rec: Recommendation, direction: string) => {
    const key = `${rec.label}-${rec.score}`
    if (bookmarkedIds.has(key)) return
    saveBookmark(rec, occasion, direction)
    setBookmarkedIds(prev => new Set(prev).add(key))
  }

  const renderItemResults = (result: StyleItemResponse) => (
    <div ref={resultsRef} className="reveal space-y-10">
      {result.clothing_check && !result.clothing_check.ok && (
        <div className="border border-red-500/30 bg-red-950/20 p-6">
          <p className="text-red-300 text-sm">{result.explanation}</p>
        </div>
      )}

      {result.predictions && (
        <div>
          <div className="overline mb-4">Model Predictions</div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-px bg-white/10">
            <ConfidenceBar title="ResNet-18" pred={result.predictions.resnet} />
            <ConfidenceBar title="EfficientNet" pred={result.predictions.effnet} color="bg-zinc-400" />
            <ConfidenceBar title="Ensemble" pred={result.predictions.ensemble} color="bg-accent-red" />
          </div>
        </div>
      )}

      {result.direction && (
        <div className="flex items-center gap-3">
          <span className="overline">Direction</span>
          <span className="border border-white/20 px-4 py-2 text-[11px] uppercase tracking-[0.15em] text-white">
            {result.direction.replace('->', ' → ')}
          </span>
          {/* V2 indicator if explanation mentions 'similarity' or 'sources' */}
          {result.explanation?.includes('similarity') && (
             <span className="border border-emerald-500/30 bg-emerald-500/10 text-emerald-400 px-3 py-1.5 text-[10px] uppercase tracking-[0.15em] font-medium flex items-center gap-1">
               <Sparkles size={10} /> Enhanced Retrieval
             </span>
          )}
        </div>
      )}

      {result.explanation && <p className="editorial-quote">{result.explanation}</p>}

      {result.recommendations.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <div className="overline">Recommendations</div>
            <div className="text-zinc-600 text-xs">{result.recommendations.length} matches</div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-white/10 stagger-children">
            {result.recommendations.map((rec, i) => (
              <div key={i} className="relative group/card reveal visible" style={{ animationDelay: `${i * 100}ms` }}>
                <RecommendationCard rec={rec} rank={i + 1} apiBase={API_BASE} />
                {/* Bookmark button */}
                <button
                  onClick={() => handleBookmark(rec, result.direction ?? '')}
                  className="absolute top-3 right-3 z-10 bg-black/70 backdrop-blur border border-white/20 p-1.5 opacity-0 group-hover/card:opacity-100 transition-opacity hover:bg-white/20"
                  title="Save recommendation"
                >
                  {bookmarkedIds.has(`${rec.label}-${rec.score}`) ? (
                    <BookmarkCheck size={14} className="text-emerald-400" />
                  ) : (
                    <Bookmark size={14} className="text-white" />
                  )}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )

  const renderPersonResults = (result: StylePersonResponse) => (
    <div className="space-y-12">
      {result.error && (
        <div className="border border-red-500/30 bg-red-950/20 p-6">
          <p className="text-red-300 text-sm">{result.error}</p>
        </div>
      )}
      {(result.top_crop_url || result.bottom_crop_url) && (
        <div>
          <div className="overline mb-4">Detected Crops</div>
          <div className="grid grid-cols-2 gap-px bg-white/10">
            {result.top_crop_url && (
              <div className="bg-bg p-4">
                <div className="overline mb-2">Top Crop</div>
                <img src={`${API_BASE}${result.top_crop_url}`} alt="top crop" className="max-h-48 object-contain" />
              </div>
            )}
            {result.bottom_crop_url && (
              <div className="bg-bg p-4">
                <div className="overline mb-2">Bottom Crop</div>
                <img src={`${API_BASE}${result.bottom_crop_url}`} alt="bottom crop" className="max-h-48 object-contain" />
              </div>
            )}
          </div>
        </div>
      )}
      {result.top_results && (
        <div>
          <h3 className="font-serif text-2xl text-white mb-4">Top Garment Analysis</h3>
          {renderItemResults(result.top_results)}
        </div>
      )}
      {result.bottom_results && (
        <div>
          <h3 className="font-serif text-2xl text-white mb-4">Bottom Garment Analysis</h3>
          {renderItemResults(result.bottom_results)}
        </div>
      )}
    </div>
  )

  return (
    <div className="space-y-10">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        <div className="lg:col-span-7">
          <Dropzone
            onFile={handleFile}
            preview={preview}
            label={mode === 'item' ? 'Drop a clothing item photo' : 'Drop a full-body photo'}
          />
        </div>
        <div className="lg:col-span-5 space-y-6">
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="overline block">Occasion</label>
              {/* Quick chips */}
              <div className="hidden md:flex gap-2">
                {['office', 'casual', 'party', 'date'].map(chip => (
                  <button 
                    key={chip}
                    onClick={() => setOccasion(chip)}
                    className="text-[9px] uppercase tracking-widest border border-white/20 px-2 py-0.5 text-zinc-400 hover:text-white hover:bg-white/10 transition-colors"
                  >
                    {chip}
                  </button>
                ))}
              </div>
            </div>
            <input
              type="text"
              placeholder="e.g. office meeting, wedding, casual brunch…"
              value={occasion}
              onChange={e => setOccasion(e.target.value)}
              className="w-full bg-transparent border-b border-white/20 px-0 py-4 text-white placeholder-zinc-600 focus:outline-none focus:border-white transition-colors"
              data-testid="occasion-input"
            />
          </div>
          <div>
            <label className="overline block mb-3">Skin Personalization</label>
            <div className="flex gap-0">
              <button onClick={() => setUseSkin(false)} className={`px-6 py-3 text-[10px] uppercase tracking-[0.15em] font-bold border border-white/20 transition-all ${!useSkin ? 'bg-white text-black' : 'bg-transparent text-zinc-400 hover:text-white'}`} data-testid="skin-off">Off</button>
              <button onClick={() => setUseSkin(true)} className={`px-6 py-3 text-[10px] uppercase tracking-[0.15em] font-bold border border-white/20 border-l-0 transition-all ${useSkin ? 'bg-white text-black' : 'bg-transparent text-zinc-400 hover:text-white'}`} data-testid="skin-on">On</button>
            </div>
          </div>
          {useSkin && (
            <div className="reveal visible slide-down">
              <label className="overline block mb-3">Your Undertone</label>
              <div className="flex gap-0">
                {['warm', 'neutral', 'cool'].map(t => (
                  <button key={t} onClick={() => setUndertone(t)} className={`flex-1 px-4 py-3 text-[10px] uppercase tracking-[0.15em] font-bold border border-white/20 transition-all ${undertone === t ? 'bg-white text-black' : 'bg-transparent text-zinc-400'} ${t !== 'warm' ? 'border-l-0' : ''}`}>{t}</button>
                ))}
              </div>
            </div>
          )}
          <button
            onClick={generate}
            disabled={!file || loading}
            className="w-full flex items-center justify-center gap-3 bg-white text-black px-8 py-5 uppercase tracking-[0.2em] text-xs font-bold hover:bg-zinc-200 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
            data-testid="generate-btn"
          >
            {loading ? (
              <><Loader2 size={16} className="animate-spin" /> Analyzing…</>
            ) : (
              <><Sparkles size={16} strokeWidth={1.5} /> Generate</>
            )}
          </button>
          {error && (
            <div className="border border-red-500/30 bg-red-950/20 p-4">
              <p className="text-red-300 text-xs">{error}</p>
            </div>
          )}
        </div>
      </div>

      {loading && (
        <div className="space-y-10 reveal visible">
           <div className="overline">Analyzing Image & Retrieving Matches</div>
           <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-white/10">
              {Array.from({length: 4}).map((_, i) => (
                <div key={i} className="border border-white/10 bg-[#0A0A0A] p-4 flex flex-col h-64 loading-shimmer">
                   <div className="w-full flex-1 bg-white/5 mb-4"></div>
                   <div className="h-4 bg-white/5 w-1/2 mb-2"></div>
                   <div className="h-3 bg-white/5 w-3/4"></div>
                </div>
              ))}
           </div>
        </div>
      )}

      {!loading && itemResult && renderItemResults(itemResult)}
      {!loading && personResult && renderPersonResults(personResult)}
    </div>
  )
}
