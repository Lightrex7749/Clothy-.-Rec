/**
 * ClothyRec API client.
 * All calls go through the Vite dev proxy (same origin) or VITE_API_BASE_URL.
 */
import type {
  HealthResponse,
  LabelsResponse,
  StyleItemResponse,
  StylePersonResponse,
  SkinProfile,
  ChatTurn,
  ChatResponse,
  ImageGenResponse,
  PromptLibraryResponse,
  PromptOptimizeResponse,
} from '../types/api'

const BASE = import.meta.env.VITE_API_BASE_URL ?? ''

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, init)
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText)
    throw new Error(`API ${res.status}: ${text}`)
  }
  return res.json()
}

export async function apiHealth(): Promise<HealthResponse> {
  return request('/health')
}

export async function apiLabels(): Promise<LabelsResponse> {
  return request('/labels')
}

export async function apiStyleItem(
  file: File,
  occasionText: string,
  mode: string,
  useSkin: boolean,
  skinUndertone: string,
): Promise<StyleItemResponse> {
  const fd = new FormData()
  fd.append('image', file)
  fd.append('occasion_text', occasionText)
  fd.append('mode', mode)
  fd.append('use_skin', String(useSkin))
  fd.append('skin_undertone', skinUndertone)
  return request('/api/style/item', { method: 'POST', body: fd })
}

export async function apiStylePerson(
  file: File,
  occasionText: string,
  useSkin: boolean,
  skinUndertone: string,
): Promise<StylePersonResponse> {
  const fd = new FormData()
  fd.append('image', file)
  fd.append('occasion_text', occasionText)
  fd.append('use_skin', String(useSkin))
  fd.append('skin_undertone', skinUndertone)
  return request('/api/style/person', { method: 'POST', body: fd })
}

export async function apiSkinAnalyze(file: File): Promise<SkinProfile> {
  const fd = new FormData()
  fd.append('image', file)
  return request('/api/skin/analyze', { method: 'POST', body: fd })
}
export async function apiChat(
  message: string,
  history: ChatTurn[],
  context?: any,
): Promise<ChatResponse> {
  return request('/api/gemini/text/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, history, context }),
  })
}

export async function apiGenerateImage(
  file: File,
  prompt: string,
  style: string,
  stylePrompt: string,
  count: number,
): Promise<ImageGenResponse> {
  const fd = new FormData()
  fd.append('image', file)
  fd.append('prompt', prompt)
  fd.append('style', style)
  fd.append('style_prompt', stylePrompt)
  fd.append('count', String(count))
  return request('/api/gemini/image', { method: 'POST', body: fd })
}

export async function apiPromptLibrary(): Promise<PromptLibraryResponse> {
  return request('/api/prompts')
}

export async function apiOptimizePrompt(
  prompt: string,
  gender: 'male' | 'female',
  instructions?: string,
): Promise<PromptOptimizeResponse> {
  return request('/api/gemini/text/optimize', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt, gender, instructions }),
  })
}
