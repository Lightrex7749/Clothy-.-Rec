import type { SkinProfile } from '../types/api'
import { useReveal } from '../lib/hooks'

interface Props {
  profile: SkinProfile
}

export default function SkinPalette({ profile }: Props) {
  const ref = useReveal()
  return (
    <div ref={ref} className="space-y-8 reveal">
      {/* Detected tone */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-px bg-white/10">
        <div className="bg-bg p-6">
          <div className="overline mb-2">Tone</div>
          <div className="font-serif text-2xl text-white capitalize">{profile.tone_detail}</div>
        </div>
        <div className="bg-bg p-6">
          <div className="overline mb-2">Undertone</div>
          <div className="font-serif text-2xl text-white capitalize">{profile.undertone}</div>
          <div className="text-zinc-500 text-xs mt-1">Strength: {Math.round(profile.undertone_strength * 100)}%</div>
        </div>
        <div className="bg-bg p-6">
          <div className="overline mb-2">Detected Color</div>
          <div className="flex items-center gap-3 mt-2">
            <div className="w-10 h-10 border border-white/10" style={{ background: profile.hex }} />
            <span className="font-mono text-sm text-zinc-300">{profile.hex}</span>
          </div>
        </div>
      </div>

      {/* Best colors */}
      <div>
        <div className="overline mb-4">Recommended Colors</div>
        <div className="grid grid-cols-3 md:grid-cols-6 gap-px bg-white/10">
          {profile.palette.best.map((c, i) => (
            <div key={i} className="bg-bg p-4 flex flex-col items-center gap-2">
              <div className="w-full aspect-square border border-white/10" style={{ background: c.hex }} />
              <span className="text-[10px] uppercase tracking-widest text-zinc-400">{c.name}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Avoid colors */}
      <div>
        <div className="overline mb-4">Colors to Avoid</div>
        <div className="grid grid-cols-3 gap-px bg-white/10">
          {profile.palette.avoid.map((c, i) => (
            <div key={i} className="bg-bg p-4 flex flex-col items-center gap-2">
              <div className="w-full aspect-square border border-white/10 relative" style={{ background: c.hex }}>
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-[140%] h-px bg-red-500 rotate-45 origin-center" />
                </div>
              </div>
              <span className="text-[10px] uppercase tracking-widest text-zinc-400">{c.name}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Advisory */}
      <p className="editorial-quote">{profile.notes}</p>
    </div>
  )
}
