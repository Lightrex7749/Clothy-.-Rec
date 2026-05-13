import React, { useMemo, useState, useEffect } from 'react'
import ChatInterface from '../components/ChatInterface'
import Dropzone from '../components/Dropzone'
import { MessageSquare, Sparkles } from 'lucide-react'
import { apiGenerateImage, apiOptimizePrompt, apiPromptLibrary } from '../lib/api'
import { useReveal } from '../lib/hooks'
import type { PromptPreset } from '../types/api'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''

const LOADING_STAGES = [
  {
    title: 'cutting the silhouette',
    detail: 'Tracing structure from your base photo and fitting the drape.',
    eta: '10-20s',
  },
  {
    title: 'weaving the palette',
    detail: 'Matching undertones, contrast, and fabric sheen for balance.',
    eta: '15-25s',
  },
  {
    title: 'styling the accents',
    detail: 'Finishing touches: accessories, layers, and textures.',
    eta: '10-20s',
  },
  {
    title: 'rendering the lookbook',
    detail: 'Polishing light, grain, and print details for the final reveal.',
    eta: '5-15s',
  },
]

export default function ChatPage() {
  const revealRef = useReveal()
  const [genFile, setGenFile] = useState<File | null>(null)
  const [genPreview, setGenPreview] = useState<string | null>(null)
  const [presets, setPresets] = useState<PromptPreset[]>([])
  const [styleId, setStyleId] = useState<string | null>(null)
  const [prompt, setPrompt] = useState('')
  const [gender, setGender] = useState<'female' | 'male'>('female')
  const [optInstructions, setOptInstructions] = useState('')
  const [finalPrompt, setFinalPrompt] = useState('')
  const [finalTouched, setFinalTouched] = useState(false)
  const [results, setResults] = useState<string[]>([])
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null)
  const [useSelectedBase, setUseSelectedBase] = useState(false)
  const [loading, setLoading] = useState(false)
  const [optimizing, setOptimizing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [loadingStage, setLoadingStage] = useState(0)

  useEffect(() => {
    let mounted = true
    apiPromptLibrary()
      .then(res => {
        if (!mounted) return
        setPresets(res.prompts)
        const first = res.prompts[0]
        if (first) {
          setStyleId(first.id)
          setPrompt(first.prompt)
          setFinalTouched(false)
        }
      })
      .catch(() => {
        if (!mounted) return
        setPresets([])
      })
    return () => { mounted = false }
  }, [])

  const activeStyle = useMemo(
    () => presets.find(s => s.id === styleId) ?? presets[0],
    [styleId, presets]
  )

  useEffect(() => {
    if (!finalTouched) {
      setFinalPrompt(prompt)
    }
  }, [prompt, finalTouched])

  useEffect(() => {
    if (!loading) {
      setLoadingStage(0)
      return
    }
    const intervalId = window.setInterval(() => {
      setLoadingStage(prev => (prev + 1) % LOADING_STAGES.length)
    }, 1800)
    return () => window.clearInterval(intervalId)
  }, [loading])

  const handleFile = (file: File, preview: string) => {
    setGenFile(file)
    setGenPreview(preview)
    setError(null)
    setResults([])
    setSelectedIndex(null)
    setUseSelectedBase(false)
  }

  const setStyle = (id: string) => {
    const preset = presets.find(s => s.id === id)
    setStyleId(id)
    if (preset) setPrompt(preset.prompt)
    setFinalTouched(false)
  }

  const labelForPreset = (preset: PromptPreset, index: number) => {
    const firstLine = preset.prompt.split(/\r?\n/)[0] || ''
    const sentence = firstLine.split(/[.!?]/)[0].trim()
    if (sentence) return sentence.slice(0, 42)
    return `Prompt ${index + 1}`
  }

  const dataUrlToFile = async (dataUrl: string, name: string) => {
    const res = await fetch(dataUrl)
    const blob = await res.blob()
    return new File([blob], name, { type: blob.type || 'image/png' })
  }

  const generate = async () => {
    setError(null)
    setLoading(true)
    try {
      let baseFile = genFile
      if (useSelectedBase && selectedIndex !== null) {
        baseFile = await dataUrlToFile(results[selectedIndex], 'selected.png')
      }
      if (!baseFile) {
        throw new Error('Please upload a photo first.')
      }
      if (!activeStyle) {
        throw new Error('Prompt presets are not available yet.')
      }
      const basePrompt = activeStyle.prompt.trim()
      const resolvedPrompt = finalPrompt.trim() || prompt.trim()
      if (!resolvedPrompt) {
        throw new Error('Please enter a prompt first.')
      }
      const stylePrompt = resolvedPrompt === basePrompt ? '' : basePrompt
      const res = await apiGenerateImage(
        baseFile,
        resolvedPrompt,
        `Prompt ${activeStyle.id}`,
        stylePrompt,
        4,
      )
      setResults(res.images)
      setSelectedIndex(0)
    } catch (e: any) {
      setError(e.message || 'Generation failed')
    } finally {
      setLoading(false)
    }
  }

  const optimize = async () => {
    setError(null)
    setOptimizing(true)
    try {
      if (!prompt.trim()) {
        throw new Error('Please enter a prompt first.')
      }
      const res = await apiOptimizePrompt(
        prompt.trim(),
        gender,
        optInstructions.trim() || undefined,
      )
      const optimized = res.optimized_prompt?.trim() || prompt.trim()
      setFinalPrompt(optimized)
      setFinalTouched(true)
    } catch (e: any) {
      setError(e.message || 'Optimization failed')
    } finally {
      setOptimizing(false)
    }
  }

  const activeStage = LOADING_STAGES[loadingStage]
  const progress = ((loadingStage + 1) / LOADING_STAGES.length) * 100

  return (
    <div className="max-w-6xl mx-auto px-6 py-12 pt-24 min-h-screen flex flex-col">
      <div className="mb-8">
        <h1 className="text-4xl md:text-5xl font-bold text-white mb-4 tracking-tight flex items-center gap-4">
          <MessageSquare className="w-10 h-10" />
          AI Stylist
        </h1>
        <p className="text-zinc-400 text-lg max-w-2xl leading-relaxed">
          Chat with Atelier. Ask for outfit recommendations, discuss your color palette, or get advice on your latest wardrobe additions.
        </p>
      </div>

      <div className="flex-1 min-h-0 bg-zinc-950 border border-zinc-800 rounded-3xl overflow-hidden shadow-2xl">
        <ChatInterface fullPage={true} />
      </div>

      <div ref={revealRef} className="reveal mt-10 border border-zinc-800 rounded-3xl bg-zinc-950 p-6 md:p-8 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <div className="overline">AI Look Generator</div>
            <h2 className="font-serif text-2xl text-white mt-2 flex items-center gap-2">
              <Sparkles size={18} /> Generate a trending look
            </h2>
          </div>
          <div className="text-zinc-500 text-xs">Powered by Gemini</div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
          <div className="lg:col-span-6">
            <Dropzone onFile={handleFile} preview={genPreview} label="Drop your photo" />
          </div>
          <div className="lg:col-span-6 space-y-6">
            <div>
              <label className="overline block mb-3">Prompt</label>
              <textarea
                value={prompt}
                onChange={e => setPrompt(e.target.value)}
                rows={4}
                placeholder="Describe the look you want..."
                className="w-full bg-transparent border border-white/10 p-4 text-sm text-white placeholder-zinc-600 focus:outline-none focus:border-white/40 transition-colors"
              />
            </div>

            <div className="rounded-2xl border border-white/10 bg-black/30 p-4 space-y-4">
              <div className="overline">Optimization</div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setGender('female')}
                  className={`px-3 py-2 text-[10px] uppercase tracking-[0.2em] border transition-colors ${
                    gender === 'female'
                      ? 'border-white/60 text-white bg-white/5'
                      : 'border-white/20 text-zinc-400 hover:text-white'
                  }`}
                >
                  Female
                </button>
                <button
                  type="button"
                  onClick={() => setGender('male')}
                  className={`px-3 py-2 text-[10px] uppercase tracking-[0.2em] border transition-colors ${
                    gender === 'male'
                      ? 'border-white/60 text-white bg-white/5'
                      : 'border-white/20 text-zinc-400 hover:text-white'
                  }`}
                >
                  Male
                </button>
              </div>

              <div>
                <label className="overline block mb-3">Extra instructions</label>
                <textarea
                  value={optInstructions}
                  onChange={e => setOptInstructions(e.target.value)}
                  rows={3}
                  placeholder="Add fit, mood, accessories, or style constraints..."
                  className="w-full bg-transparent border border-white/10 p-4 text-sm text-white placeholder-zinc-600 focus:outline-none focus:border-white/40 transition-colors"
                />
              </div>

              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={optimize}
                  disabled={optimizing || !prompt.trim()}
                  className="bg-white text-black px-5 py-2.5 text-[10px] uppercase tracking-[0.2em] font-bold hover:bg-zinc-200 transition-colors disabled:opacity-50"
                >
                  {optimizing ? 'Optimizing...' : 'AI Optimize'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setFinalPrompt(prompt)
                    setFinalTouched(false)
                  }}
                  className="text-[10px] uppercase tracking-[0.2em] px-4 py-2.5 border border-white/20 text-zinc-400 hover:text-white transition-colors"
                >
                  Use base prompt
                </button>
              </div>

              <div>
                <label className="overline block mb-3">Final prompt</label>
                <textarea
                  value={finalPrompt}
                  onChange={e => {
                    setFinalPrompt(e.target.value)
                    setFinalTouched(true)
                  }}
                  rows={4}
                  placeholder="Final prompt used for generation..."
                  className="w-full bg-transparent border border-white/10 p-4 text-sm text-white placeholder-zinc-600 focus:outline-none focus:border-white/40 transition-colors"
                />
              </div>
            </div>


            <div className="flex items-center gap-3">
              <button
                onClick={generate}
                disabled={loading}
                className="bg-white text-black px-6 py-3 text-[10px] uppercase tracking-[0.2em] font-bold hover:bg-zinc-200 transition-colors disabled:opacity-50"
              >
                {loading ? 'Generating...' : 'Generate'}
              </button>
              {selectedIndex !== null && results.length > 0 && (
                <button
                  onClick={() => setUseSelectedBase(v => !v)}
                  className={`text-[10px] uppercase tracking-[0.2em] px-4 py-3 border transition-colors ${
                    useSelectedBase
                      ? 'border-white/60 text-white bg-white/5'
                      : 'border-white/20 text-zinc-400 hover:text-white'
                  }`}
                >
                  {useSelectedBase ? 'Using selected as base' : 'Use selected as base'}
                </button>
              )}
            </div>

            {error && (
              <div className="border border-red-500/30 bg-red-950/20 p-4">
                <p className="text-red-300 text-sm">{error}</p>
              </div>
            )}
          </div>
        </div>

        {loading && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="overline">Look in progress</div>
              <div className="text-zinc-600 text-xs">Studio feed</div>
            </div>
            <div className="rounded-2xl border border-white/10 bg-black/40 p-5 space-y-4">
              <div className="flex items-center justify-between">
                <div className="text-white text-sm">Atelier is {activeStage.title}...</div>
                <div className="text-zinc-500 text-xs">ETA {activeStage.eta}</div>
              </div>
              <p className="text-zinc-400 text-sm">{activeStage.detail}</p>
              <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
                <div className="h-full bg-white/70 loading-shimmer" style={{ width: `${progress}%` }} />
              </div>
              <div className="flex items-center gap-2">
                {LOADING_STAGES.map((_, i) => (
                  <span
                    key={i}
                    className={`h-1.5 w-6 rounded-full ${i === loadingStage ? 'bg-white' : 'bg-white/20'}`}
                  />
                ))}
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {Array.from({ length: 4 }).map((_, i) => (
                  <div
                    key={i}
                    className="relative overflow-hidden border border-white/10 bg-[#0B0B0B] aspect-[3/4]"
                  >
                    <div className="absolute inset-0 loading-shimmer" />
                    <div className="absolute bottom-3 left-3 text-[9px] uppercase tracking-widest text-white/60">
                      Look {i + 1}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        <div>
          <div className="overline mb-3">Style preset</div>
          {presets.length === 0 ? (
            <div className="text-zinc-600 text-xs">No prompt presets found.</div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
              {presets.map((preset, i) => (
                <button
                  key={preset.id}
                  type="button"
                  onClick={() => setStyle(preset.id)}
                  aria-pressed={styleId === preset.id}
                  className={`relative text-left rounded-2xl overflow-hidden border transition-all duration-300 group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/60 ${
                    styleId === preset.id
                      ? 'border-white/40 ring-2 ring-white/40'
                      : 'border-white/10 hover:border-white/30'
                  }`}
                >
                  <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/10 to-transparent opacity-80" />
                  {preset.image_url ? (
                    <div className="aspect-[4/5] min-h-[240px] sm:min-h-[260px] overflow-hidden bg-black/40">
                      <img
                        src={`${API_BASE}${preset.image_url}`}
                        alt={labelForPreset(preset, i)}
                        className="w-full h-full object-contain grayscale group-hover:grayscale-0 transition-all duration-500"
                      />
                    </div>
                  ) : (
                    <div className="aspect-[4/5] min-h-[240px] sm:min-h-[260px] bg-surface" />
                  )}
                  <div className="absolute top-3 left-3 rounded-full border border-white/30 bg-black/60 px-2.5 py-1 text-[10px] uppercase tracking-widest text-white">
                    Prompt {i + 1}
                  </div>
                  {styleId === preset.id && (
                    <div className="absolute top-3 right-3 rounded-full border border-white/30 bg-black/60 px-2.5 py-1 text-[10px] uppercase tracking-widest text-white">
                      Selected
                    </div>
                  )}
                  <div className="absolute bottom-0 left-0 right-0 p-4">
                    <div className="text-sm text-white/90 font-medium leading-snug line-clamp-2">
                      {labelForPreset(preset, i)}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {results.length > 0 && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="overline">Generated looks</div>
              <div className="text-zinc-600 text-xs">{results.length} variants</div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {results.map((url, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => setSelectedIndex(i)}
                  className="bg-bg border border-white/10 relative group"
                >
                  <img src={url} alt={`generated-${i}`} className="w-full aspect-[3/4] object-cover" />
                  {selectedIndex === i && (
                    <div className="absolute top-2 left-2 border border-white/30 bg-black/70 px-2 py-1 text-[9px] uppercase tracking-widest text-white">
                      Selected
                    </div>
                  )}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
