import { useState } from 'react'
import { Loader2, ScanLine, Save, CheckCircle } from 'lucide-react'
import Dropzone from '../components/Dropzone'
import SkinPalette from '../components/SkinPalette'
import type { SkinProfile } from '../types/api'
import { apiSkinAnalyze } from '../lib/api'
import { saveSkinProfile, addHistoryEntry } from '../lib/storage'

export default function SkinPage() {
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [profile, setProfile] = useState<SkinProfile | null>(null)
  const [saved, setSaved] = useState(false)

  const handleFile = (f: File, prev: string) => {
    setFile(f); setPreview(prev)
    setProfile(null); setError(null); setSaved(false)
  }

  const analyze = async () => {
    if (!file) return
    setLoading(true); setError(null)
    try {
      const res = await apiSkinAnalyze(file)
      setProfile(res)
      // Auto-save to localStorage + history
      saveSkinProfile(res)
      addHistoryEntry({
        mode: 'skin',
        skinTone: res.tone_detail,
        skinUndertone: res.undertone,
      })
      setSaved(true)
    } catch (e: any) {
      setError(e.message || 'Analysis failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-10">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        <div className="lg:col-span-5">
          <Dropzone onFile={handleFile} preview={preview} label="Drop a face / selfie photo" />
        </div>
        <div className="lg:col-span-7 flex flex-col justify-center space-y-6">
          <div>
            <p className="text-zinc-400 leading-relaxed">
              Upload a well-lit, front-facing photo. We'll estimate your skin undertone
              and suggest a personalized colour palette. This is purely advisory — no
              race or ethnicity inference is ever made.
            </p>
          </div>
          <button
            onClick={analyze}
            disabled={!file || loading}
            className="w-full md:w-auto flex items-center justify-center gap-3 bg-white text-black px-8 py-5 uppercase tracking-[0.2em] text-xs font-bold hover:bg-zinc-200 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
            data-testid="analyze-skin-btn"
          >
            {loading ? (
              <><Loader2 size={16} className="animate-spin" /> Analyzing…</>
            ) : (
              <><ScanLine size={16} strokeWidth={1.5} /> Analyze Skin Tone</>
            )}
          </button>
          {saved && (
            <div className="flex items-center gap-2 text-emerald-400 text-xs">
              <CheckCircle size={14} /> Profile saved to your local profile
            </div>
          )}
          {error && (
            <div className="border border-red-500/30 bg-red-950/20 p-4">
              <p className="text-red-300 text-xs">{error}</p>
            </div>
          )}
        </div>
      </div>

      {profile && <SkinPalette profile={profile} />}
    </div>
  )
}
