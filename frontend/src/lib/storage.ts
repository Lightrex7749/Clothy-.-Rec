/**
 * ClothyRec — localStorage persistence layer.
 *
 * Stores: skin profile, analysis history, bookmarked recommendations.
 * All data stays in the browser — no server-side storage needed.
 */
import type { SkinProfile, StyleItemResponse, Recommendation } from '../types/api'

const KEYS = {
  SKIN_PROFILE: 'clothyrec_skin_profile',
  HISTORY: 'clothyrec_history',
  BOOKMARKS: 'clothyrec_bookmarks',
} as const

// ── Skin Profile ──────────────────────────────────────────────
export function saveSkinProfile(profile: SkinProfile): void {
  localStorage.setItem(KEYS.SKIN_PROFILE, JSON.stringify(profile))
}
export function loadSkinProfile(): SkinProfile | null {
  const raw = localStorage.getItem(KEYS.SKIN_PROFILE)
  return raw ? JSON.parse(raw) : null
}
export function clearSkinProfile(): void {
  localStorage.removeItem(KEYS.SKIN_PROFILE)
}

// ── Analysis History ──────────────────────────────────────────
export interface HistoryEntry {
  id: string
  timestamp: number
  mode: 'item' | 'person' | 'skin'
  occasion?: string
  previewUrl?: string       // base64 data URL of uploaded image
  predictedLabel?: string
  confidence?: number
  direction?: string
  recCount?: number
  skinTone?: string
  skinUndertone?: string
}

function generateId(): string {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 6)
}

export function addHistoryEntry(entry: Omit<HistoryEntry, 'id' | 'timestamp'>): HistoryEntry {
  const full: HistoryEntry = { ...entry, id: generateId(), timestamp: Date.now() }
  const history = loadHistory()
  history.unshift(full)
  // Keep last 50 entries
  const trimmed = history.slice(0, 50)
  localStorage.setItem(KEYS.HISTORY, JSON.stringify(trimmed))
  return full
}

export function loadHistory(): HistoryEntry[] {
  const raw = localStorage.getItem(KEYS.HISTORY)
  return raw ? JSON.parse(raw) : []
}

export function clearHistory(): void {
  localStorage.removeItem(KEYS.HISTORY)
}

export function deleteHistoryEntry(id: string): void {
  const history = loadHistory().filter(h => h.id !== id)
  localStorage.setItem(KEYS.HISTORY, JSON.stringify(history))
}

// ── Bookmarked Recommendations ────────────────────────────────
export interface BookmarkedRec {
  id: string
  timestamp: number
  label: string
  score: number
  occasion: string
  imageUrl?: string
  direction: string
}

export function saveBookmark(rec: Recommendation, occasion: string, direction: string): BookmarkedRec {
  const entry: BookmarkedRec = {
    id: generateId(),
    timestamp: Date.now(),
    label: rec.label,
    score: rec.score,
    occasion,
    imageUrl: rec.image_url,
    direction,
  }
  const bookmarks = loadBookmarks()
  bookmarks.unshift(entry)
  localStorage.setItem(KEYS.BOOKMARKS, JSON.stringify(bookmarks.slice(0, 100)))
  return entry
}

export function loadBookmarks(): BookmarkedRec[] {
  const raw = localStorage.getItem(KEYS.BOOKMARKS)
  return raw ? JSON.parse(raw) : []
}

export function removeBookmark(id: string): void {
  const bookmarks = loadBookmarks().filter(b => b.id !== id)
  localStorage.setItem(KEYS.BOOKMARKS, JSON.stringify(bookmarks))
}

export function clearBookmarks(): void {
  localStorage.removeItem(KEYS.BOOKMARKS)
}

// ── Stats (computed) ──────────────────────────────────────────
export function getStats() {
  const history = loadHistory()
  const bookmarks = loadBookmarks()
  const skin = loadSkinProfile()
  return {
    totalAnalyses: history.length,
    itemAnalyses: history.filter(h => h.mode === 'item').length,
    personAnalyses: history.filter(h => h.mode === 'person').length,
    skinAnalyses: history.filter(h => h.mode === 'skin').length,
    savedOutfits: bookmarks.length,
    hasSkinProfile: !!skin,
    skinProfile: skin,
  }
}
