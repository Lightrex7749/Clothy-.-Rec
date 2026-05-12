import { useState, useEffect } from 'react'
import { User, History, Bookmark, Trash2, Palette, TrendingUp, Shirt, ScanLine } from 'lucide-react'
import { useReveal } from '../lib/hooks'
import {
  loadSkinProfile, clearSkinProfile,
  loadHistory, clearHistory, deleteHistoryEntry,
  loadBookmarks, clearBookmarks, removeBookmark,
  getStats,
  type HistoryEntry,
  type BookmarkedRec,
} from '../lib/storage'
import type { SkinProfile } from '../types/api'

type Tab = 'overview' | 'history' | 'bookmarks'

export default function ProfilePage() {
  const [tab, setTab] = useState<Tab>('overview')
  const [skin, setSkin] = useState<SkinProfile | null>(null)
  const [history, setHistory] = useState<HistoryEntry[]>([])
  const [bookmarks, setBookmarks] = useState<BookmarkedRec[]>([])
  const [stats, setStats] = useState(getStats())
  const r1 = useReveal()

  const reload = () => {
    setSkin(loadSkinProfile())
    setHistory(loadHistory())
    setBookmarks(loadBookmarks())
    setStats(getStats())
  }

  useEffect(() => { reload() }, [])

  const TABS: { id: Tab; label: string; icon: typeof User }[] = [
    { id: 'overview', label: 'Overview', icon: User },
    { id: 'history', label: 'History', icon: History },
    { id: 'bookmarks', label: 'Saved', icon: Bookmark },
  ]

  return (
    <div ref={r1} className="reveal space-y-10">
      {/* Tab bar */}
      <div className="flex gap-0 border border-white/10">
        {TABS.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex-1 flex items-center justify-center gap-2 px-4 py-4 text-[10px] uppercase tracking-[0.15em] font-bold transition-all ${
              tab === t.id ? 'bg-white text-black' : 'bg-transparent text-zinc-400 hover:text-white hover:bg-white/5'
            }`}
            data-testid={`profile-tab-${t.id}`}
          >
            <t.icon size={14} strokeWidth={1.5} />
            {t.label}
          </button>
        ))}
      </div>

      {/* Overview tab */}
      {tab === 'overview' && (
        <div className="space-y-8">
          {/* Stats grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-white/10">
            {[
              { label: 'Total Analyses', value: stats.totalAnalyses, icon: TrendingUp },
              { label: 'Item Analyses', value: stats.itemAnalyses, icon: Shirt },
              { label: 'Saved Outfits', value: stats.savedOutfits, icon: Bookmark },
              { label: 'Skin Scans', value: stats.skinAnalyses, icon: ScanLine },
            ].map((s, i) => (
              <div key={i} className="bg-bg p-6 text-center">
                <s.icon size={20} strokeWidth={1} className="mx-auto text-zinc-500 mb-3" />
                <div className="stat-number text-3xl text-white">{s.value}</div>
                <div className="overline mt-2">{s.label}</div>
              </div>
            ))}
          </div>

          {/* Skin profile card */}
          <div>
            <div className="overline mb-4">Skin Profile</div>
            {skin ? (
              <div className="border border-white/10 bg-[#0A0A0A] p-6 space-y-4">
                <div className="flex items-center gap-4">
                  <div className="w-14 h-14 border border-white/10" style={{ background: skin.hex }} />
                  <div>
                    <div className="font-serif text-xl text-white capitalize">{skin.tone_detail} · {skin.undertone}</div>
                    <div className="text-zinc-500 text-xs font-mono mt-1">{skin.hex} · Strength {Math.round(skin.undertone_strength * 100)}%</div>
                  </div>
                </div>
                <div className="flex gap-1">
                  {skin.palette.best.map((c, i) => (
                    <div key={i} className="flex-1 h-8 border border-white/10" style={{ background: c.hex }} title={c.name} />
                  ))}
                </div>
                <button
                  onClick={() => { clearSkinProfile(); reload() }}
                  className="flex items-center gap-2 text-red-400 text-xs uppercase tracking-widest hover:text-red-300 transition-colors"
                >
                  <Trash2 size={12} /> Clear Profile
                </button>
              </div>
            ) : (
              <div className="border border-dashed border-white/10 p-8 text-center">
                <Palette size={24} strokeWidth={1} className="mx-auto text-zinc-600 mb-3" />
                <p className="text-zinc-500 text-sm">No skin profile saved yet.</p>
                <p className="text-zinc-600 text-xs mt-1">Run a Skin Analysis to save your profile here.</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* History tab */}
      {tab === 'history' && (
        <div className="space-y-4">
          {history.length > 0 && (
            <div className="flex justify-end">
              <button
                onClick={() => { clearHistory(); reload() }}
                className="flex items-center gap-2 text-red-400 text-xs uppercase tracking-widest hover:text-red-300"
              >
                <Trash2 size={12} /> Clear All
              </button>
            </div>
          )}
          {history.length === 0 ? (
            <div className="border border-dashed border-white/10 p-8 text-center">
              <History size={24} strokeWidth={1} className="mx-auto text-zinc-600 mb-3" />
              <p className="text-zinc-500 text-sm">No analysis history yet.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-px bg-white/10">
              {history.map(h => (
                <div key={h.id} className="history-card flex items-start gap-4">
                  {/* Thumbnail */}
                  <div className="w-14 h-14 shrink-0 border border-white/10 bg-surface overflow-hidden">
                    {h.previewUrl ? (
                      <img src={h.previewUrl} alt="" className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-zinc-600">
                        <Shirt size={16} />
                      </div>
                    )}
                  </div>
                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] uppercase tracking-widest text-zinc-500 border border-white/10 px-2 py-0.5">
                        {h.mode}
                      </span>
                      {h.predictedLabel && (
                        <span className="text-white text-sm font-serif truncate">
                          {h.predictedLabel.replace(/_/g, ' ')}
                        </span>
                      )}
                    </div>
                    <div className="text-zinc-600 text-xs mt-1">
                      {new Date(h.timestamp).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })}
                      {h.occasion && <span className="ml-2 text-zinc-500">· {h.occasion}</span>}
                    </div>
                    {h.confidence != null && (
                      <div className="text-zinc-500 text-xs mt-1">Confidence: {Math.round(h.confidence * 100)}%</div>
                    )}
                  </div>
                  {/* Delete */}
                  <button
                    onClick={() => { deleteHistoryEntry(h.id); reload() }}
                    className="text-zinc-600 hover:text-red-400 transition-colors shrink-0 p-1"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Bookmarks tab */}
      {tab === 'bookmarks' && (
        <div className="space-y-4">
          {bookmarks.length > 0 && (
            <div className="flex justify-end">
              <button
                onClick={() => { clearBookmarks(); reload() }}
                className="flex items-center gap-2 text-red-400 text-xs uppercase tracking-widest hover:text-red-300"
              >
                <Trash2 size={12} /> Clear All
              </button>
            </div>
          )}
          {bookmarks.length === 0 ? (
            <div className="border border-dashed border-white/10 p-8 text-center">
              <Bookmark size={24} strokeWidth={1} className="mx-auto text-zinc-600 mb-3" />
              <p className="text-zinc-500 text-sm">No saved recommendations yet.</p>
              <p className="text-zinc-600 text-xs mt-1">Bookmark recommendations from the Stylist to save them here.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-px bg-white/10">
              {bookmarks.map(b => (
                <div key={b.id} className="history-card flex flex-col group">
                  <div className="flex items-center justify-between mb-3">
                    <span className="font-serif text-lg text-white truncate mr-2" title={b.label.replace(/_/g, ' ')}>{b.label.replace(/_/g, ' ')}</span>
                    <button onClick={() => { removeBookmark(b.id); reload() }} className="text-zinc-600 hover:text-red-400 shrink-0">
                      <Trash2 size={14} />
                    </button>
                  </div>
                  {b.imageUrl && (
                    <div className="w-full aspect-[4/5] bg-surface mb-3 border border-white/10 overflow-hidden relative">
                      <img src={`${import.meta.env.VITE_API_BASE_URL ?? ''}${b.imageUrl}`} alt="" className="w-full h-full object-cover grayscale group-hover:grayscale-0 transition-all duration-500" />
                    </div>
                  )}
                  <div className="text-zinc-500 text-xs mt-auto">
                    Score: {b.score.toFixed(2)} · {b.direction.replace('->', '→')}
                  </div>
                  {b.occasion && <div className="text-zinc-600 text-xs mt-1">Occasion: {b.occasion}</div>}
                  <div className="text-zinc-700 text-xs mt-1">
                    {new Date(b.timestamp).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' })}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
