import { useState, useEffect, useRef } from 'react'
import { ArrowRight, ScanLine, Menu, X, User, ChevronUp, Cpu, Eye, Palette, Layers, Zap, Brain } from 'lucide-react'
import StylistPage from './pages/StylistPage'
import SkinPage from './pages/SkinPage'
import ProfilePage from './pages/ProfilePage'
import { apiHealth } from './lib/api'
import { useCounter, useReveal, useScrollProgress } from './lib/hooks'
import { getStats } from './lib/storage'

import ChatPage from './pages/ChatPage'
import ChatWidget from './components/ChatWidget'

type View = null | 'item' | 'person' | 'skin' | 'profile' | 'chat'

const TABS: { id: Exclude<View, null>; label: string }[] = [
  { id: 'item', label: 'Item Photo' },
  { id: 'person', label: 'Person Photo' },
  { id: 'skin', label: 'Skin Analysis' },
  { id: 'chat', label: 'AI Stylist' },
  { id: 'profile', label: 'Profile' },
]

/* ── Animated Stat Counter ─────────────────────────────────── */
function StatCounter({ end, label, suffix = '' }: { end: number; label: string; suffix?: string }) {
  const { ref, value } = useCounter(end, 1200)
  return (
    <div ref={ref} className="text-center p-6 bg-bg">
      <div className="stat-number text-4xl md:text-5xl text-white">
        {value.toLocaleString()}{suffix}
      </div>
      <div className="overline mt-3">{label}</div>
    </div>
  )
}

/* ── Header ────────────────────────────────────────────────── */
function Header({ onCta, onNav, current }: { onCta: () => void; onNav: (v: View) => void; current: View }) {
  const [mobileOpen, setMobileOpen] = useState(false)
  return (
    <header className="sticky top-0 z-50 border-b border-white/10 bg-black/70 backdrop-blur-2xl">
      <div className="max-w-[1400px] mx-auto px-6 lg:px-12 flex items-center justify-between h-20">
        <button onClick={() => { onNav(null); setMobileOpen(false) }} className="text-left" data-testid="nav-home">
          <div className="overline">Atelier</div>
          <div className="font-serif text-2xl tracking-tight text-white -mt-1">CLOTHYREC</div>
        </button>
        <nav className="hidden md:flex items-center gap-8">
          {TABS.map(t => (
            <button
              key={t.id}
              onClick={() => onNav(t.id)}
              className={`text-[11px] tracking-[0.22em] uppercase transition-colors ${
                current === t.id ? 'text-white' : 'text-zinc-500 hover:text-zinc-200'
              }`}
              data-testid={`nav-${t.id}`}
            >{t.label}</button>
          ))}
        </nav>
        <button onClick={onCta} className="hidden md:inline-flex items-center bg-white text-black px-5 py-3 text-[10px] uppercase tracking-[0.2em] font-bold hover:bg-zinc-200 transition-colors" data-testid="header-cta">
          Begin <ArrowRight size={12} strokeWidth={1.5} className="ml-2" />
        </button>
        {/* Mobile hamburger */}
        <button className="md:hidden p-2" onClick={() => setMobileOpen(!mobileOpen)} data-testid="mobile-menu-btn">
          {mobileOpen ? <X size={22} strokeWidth={1.5} /> : <Menu size={22} strokeWidth={1.5} />}
        </button>
      </div>
      {/* Mobile dropdown */}
      {mobileOpen && (
        <div className="md:hidden border-t border-white/10 bg-black/95 backdrop-blur-xl">
          {TABS.map(t => (
            <button
              key={t.id}
              onClick={() => { onNav(t.id); setMobileOpen(false) }}
              className={`block w-full text-left px-6 py-4 text-xs uppercase tracking-[0.2em] border-b border-white/5 transition-colors ${
                current === t.id ? 'text-white bg-white/5' : 'text-zinc-400'
              }`}
            >{t.label}</button>
          ))}
        </div>
      )}
    </header>
  )
}

/* ── Process Step Card (interactive) ───────────────────────── */
function ProcessCard({ n, title, desc, icon: Icon, delay }: { n: string; title: string; desc: string; icon: typeof Cpu; delay: number }) {
  const ref = useReveal()
  return (
    <div ref={ref} className={`reveal reveal-delay-${delay} card-glow bg-bg p-8 md:p-10 group cursor-default`}>
      <div className="flex items-start justify-between mb-6">
        <div className="font-mono text-zinc-600 text-sm">{n}</div>
        <Icon size={24} strokeWidth={1} className="text-zinc-600 group-hover:text-white transition-colors duration-500" />
      </div>
      <div className="font-serif text-4xl text-white group-hover:translate-x-1 transition-transform duration-500">{title}</div>
      <p className="text-zinc-400 mt-4 leading-relaxed text-sm">{desc}</p>
    </div>
  )
}

/* ── Tech Stack Pill ───────────────────────────────────────── */
const TECH_STACK = [
  { name: 'ResNet-18', cat: 'classifier' },
  { name: 'EfficientNet', cat: 'classifier' },
  { name: 'CLIP ViT-B/32', cat: 'embedding' },
  { name: 'FAISS', cat: 'retrieval' },
  { name: 'YOLOv8 Pose', cat: 'vision' },
  { name: 'MTCNN', cat: 'face' },
  { name: 'FastAPI', cat: 'backend' },
  { name: 'React 19', cat: 'frontend' },
  { name: 'TypeScript', cat: 'frontend' },
  { name: 'PyTorch', cat: 'ml' },
]

/* ── Landing Page ──────────────────────────────────────────── */
function Landing({ onStart, healthy }: { onStart: (v?: View) => void; healthy: boolean | null }) {
  const heroRef = useReveal()
  const quoteRef = useReveal()
  const techRef = useReveal()
  const statsRef = useReveal()

  return (
    <div className="relative gradient-bg">
      {/* ── Hero ──────────────────────────────────────────── */}
      <section className="max-w-[1400px] mx-auto px-6 lg:px-12 pt-20 lg:pt-32 pb-16">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-16 items-end">
          <div className="lg:col-span-7 space-y-8">
            <div className="reveal-initial overline">Issue №01 · AI Fashion Stylist</div>
            <h1 className="reveal-initial reveal-delay-1 h-display text-6xl md:text-8xl lg:text-[9rem] text-white">
              Style<br />
              with<br />
              <span className="italic font-light">precision.</span>
            </h1>
            <p className="reveal-initial reveal-delay-2 text-zinc-400 text-lg max-w-lg leading-relaxed">
              An AI stylist that reads your garments, your skin, the occasion — and composes
              the perfect outfit. Powered by deep learning. Zero guesswork.
            </p>
            <div className="reveal-initial reveal-delay-3 flex flex-wrap gap-4 pt-2">
              <button
                onClick={() => onStart('item')}
                className="group inline-flex items-center bg-white text-black px-8 py-5 uppercase tracking-[0.2em] text-xs font-bold hover:bg-zinc-200 transition-all hover:px-10"
                data-testid="hero-start-btn"
              >
                Start Styling <ArrowRight size={14} strokeWidth={1.5} className="ml-3 group-hover:translate-x-1 transition-transform" />
              </button>
              <button
                onClick={() => onStart('skin')}
                className="group inline-flex items-center border border-white/30 text-white px-8 py-5 uppercase tracking-[0.2em] text-xs font-bold hover:bg-white/5 hover:border-white transition-all"
                data-testid="hero-skin-btn"
              >
                <ScanLine size={14} strokeWidth={1.5} className="mr-3" /> Read My Tones
              </button>
            </div>
            {/* Health status dot */}
            {healthy !== null && (
              <div className="reveal-initial reveal-delay-3 flex items-center gap-2 text-xs text-zinc-500">
                <div className={`w-2 h-2 rounded-full ${healthy ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}`} />
                {healthy ? 'V2 Enhanced Pipeline Active · CPU Ready' : 'Backend offline'}
              </div>
            )}
          </div>
          <div className="lg:col-span-5 reveal-initial reveal-delay-2">
            <div className="border border-white/10 bg-[#0a0a0a] aspect-[3/4] overflow-hidden relative animate-float">
              <img
                src="https://images.pexels.com/photos/31167792/pexels-photo-31167792.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=900&w=720"
                alt="editorial fashion"
                className="w-full h-full object-cover grayscale hover:grayscale-0 transition-all duration-1000"
              />
              <div className="absolute bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-black/80 to-transparent">
                <div className="overline text-white/80">ClothyRec</div>
                <div className="font-serif text-2xl text-white">Spring · 2026</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Stats Bar ─────────────────────────────────────── */}
      <section ref={statsRef} className="reveal border-t border-b border-white/10">
        <div className="max-w-[1400px] mx-auto px-6 lg:px-12">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-white/10 border-x border-white/10">
            <StatCounter end={57672} label="Indexed Items" />
            <StatCounter end={8} label="Clothing Classes" />
            <StatCounter end={4} label="ML Models" />
            <StatCounter end={512} label="Embedding Dims" suffix="D" />
          </div>
        </div>
      </section>

      {/* ── Process Steps ─────────────────────────────────── */}
      <section className="border-b border-white/10 py-20 lg:py-32">
        <div className="max-w-[1400px] mx-auto px-6 lg:px-12">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-px bg-white/10 border-x border-white/10">
            <ProcessCard n="01" title="Upload" icon={Eye}
              desc="A clothing item, a full-body photo, or a selfie. Our models read silhouette, colour, and texture."
              delay={1} />
            <ProcessCard n="02" title="Analyze" icon={Brain}
              desc="ResNet-18 + EfficientNet classify. CLIP embeddings + FAISS find nearest matches. Skin tone personalizes scoring."
              delay={2} />
            <ProcessCard n="03" title="Style" icon={Layers}
              desc="Receive a curated selection scored by colour harmony, occasion fit, and skin undertone compatibility."
              delay={3} />
          </div>
        </div>
      </section>

      {/* ── Tech Stack Showcase ────────────────────────────── */}
      <section className="border-b border-white/10">
        <div ref={techRef} className="reveal max-w-[1400px] mx-auto px-6 lg:px-12 py-16 lg:py-24">
          <div className="overline mb-6">Powered By</div>
          <div className="flex flex-wrap gap-2">
            {TECH_STACK.map((t, i) => (
              <span key={i} className="tech-pill" style={{ transitionDelay: `${i * 0.04}s` }}>
                <Zap size={10} strokeWidth={2} className="text-zinc-600" />
                {t.name}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* ── Marquee ────────────────────────────────────────── */}
      <section className="border-b border-white/10 overflow-hidden py-6">
        <div className="animate-marquee whitespace-nowrap flex gap-16 text-zinc-700 text-xs uppercase tracking-[0.3em]">
          {Array(2).fill(null).map((_, j) => (
            <div key={j} className="flex gap-16 shrink-0">
              {['Classification', 'Recommendation', 'Colour Harmony', 'Skin Analysis', 'Pose Detection', 'Outfit Generation', 'CLIP Embeddings', 'FAISS Search'].map((t, i) => (
                <span key={i}>{t}</span>
              ))}
            </div>
          ))}
        </div>
      </section>

      {/* ── Quote CTA ──────────────────────────────────────── */}
      <section className="border-b border-white/10">
        <div ref={quoteRef} className="reveal max-w-[1400px] mx-auto px-6 lg:px-12 py-16 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <p className="editorial-quote max-w-2xl">"Style is not a uniform. It is a vocabulary you build, one piece at a time."</p>
          <button
            onClick={() => onStart('item')}
            className="group inline-flex items-center bg-white text-black px-8 py-5 uppercase tracking-[0.2em] text-xs font-bold hover:bg-zinc-200 transition-all shrink-0"
            data-testid="footer-cta"
          >
            Open ClothyRec <ArrowRight size={14} strokeWidth={1.5} className="ml-3 group-hover:translate-x-1 transition-transform" />
          </button>
        </div>
      </section>

      {/* ── Footer ─────────────────────────────────────────── */}
      <footer className="py-10">
        <div className="max-w-[1400px] mx-auto px-6 lg:px-12 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <div className="overline">ClothyRec · Atelier</div>
            <div className="font-serif text-xl text-white">AI Fashion Stylist</div>
          </div>
          <div className="flex items-center gap-6">
            <button onClick={() => onStart('profile')} className="text-zinc-500 hover:text-white text-xs uppercase tracking-widest transition-colors">Profile</button>
            <div className="text-xs text-zinc-500 tracking-widest uppercase">© 2026</div>
          </div>
        </div>
      </footer>
    </div>
  )
}

/* ── View Shell ────────────────────────────────────────────── */
function ViewShell({ id, children }: { id: string; children: React.ReactNode }) {
  const titles: Record<string, [string, string]> = {
    item: ['The Edit', 'Item photo · classification + recommendations'],
    person: ['Full Look', 'Full-body photo · top + bottom analysis'],
    skin: ['Skin Profile', 'Advisory skin tone analysis + colour palette'],
    chat: ['AI Stylist', 'Chat with Atelier for personalized recommendations'],
    profile: ['Your Profile', 'Saved analyses, skin profile & bookmarks'],
  }
  const [t, sub] = titles[id] || ['', '']
  const ref = useReveal()
  return (
    <section className="max-w-[1400px] mx-auto px-6 lg:px-12 pt-12 pb-24">
      <div ref={ref} className="reveal border-b border-white/10 pb-6 mb-12">
        <div className="overline">Section</div>
        <h2 className="h-display text-5xl md:text-6xl text-white mt-1">{t}</h2>
        <p className="text-zinc-500 mt-3">{sub}</p>
      </div>
      {children}
    </section>
  )
}

/* ── App ───────────────────────────────────────────────────── */
export default function App() {
  const [view, setView] = useState<View>(null)
  const [healthy, setHealthy] = useState<boolean | null>(null)
  const scrollProgress = useScrollProgress()
  const [showTop, setShowTop] = useState(false)

  useEffect(() => {
    apiHealth().then(h => setHealthy(h.models_loaded)).catch(() => setHealthy(false))
  }, [])

  useEffect(() => {
    const handler = () => setShowTop(window.scrollY > 400)
    window.addEventListener('scroll', handler, { passive: true })
    return () => window.removeEventListener('scroll', handler)
  }, [])

  const start = (tab: View = 'item') => setView(tab)

  const renderView = () => {
    switch (view) {
      case 'item': return <StylistPage mode="item" />
      case 'person': return <StylistPage mode="person" />
      case 'skin': return <SkinPage />
      case 'chat': return <ChatPage />
      case 'profile': return <ProfilePage />
      default: return null
    }
  }

  return (
    <div className="grain min-h-screen">
      {/* Scroll progress bar */}
      <div className="scroll-progress" style={{ width: `${scrollProgress}%` }} />

      <Header onCta={() => start('item')} onNav={setView} current={view} />

      {healthy === false && (
        <div className="bg-red-950/50 border-b border-red-500/30 text-red-300 text-xs tracking-widest uppercase text-center py-2" data-testid="health-banner">
          Backend not reachable or models not loaded — check the server.
        </div>
      )}

      {view === null ? (
        <Landing onStart={start} healthy={healthy} />
      ) : view === 'chat' ? (
        renderView()
      ) : (
        <ViewShell id={view}>{renderView()}</ViewShell>
      )}

      {view !== 'chat' && <ChatWidget />}

      {/* Scroll to top button */}
      {showTop && (
        <button
          onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
          className="fixed bottom-6 right-6 z-40 bg-white/10 backdrop-blur border border-white/10 p-3 hover:bg-white/20 transition-all"
          data-testid="scroll-top"
        >
          <ChevronUp size={18} strokeWidth={1.5} />
        </button>
      )}
    </div>
  )
}
