import type { Recommendation } from '../types/api'
import ScoreBar from './ScoreBar'

interface Props {
  rec: Recommendation
  rank: number
  apiBase: string
}

export default function RecommendationCard({ rec, rank, apiBase }: Props) {
  const imgSrc = rec.image_url ? `${apiBase}${rec.image_url}` : ''

  return (
    <div className="border border-white/10 bg-[#0A0A0A] group hover:-translate-y-1 transition-transform duration-500" data-testid={`rec-card-${rank}`}>
      {/* Image */}
      <div className="aspect-[3/4] overflow-hidden border-b border-white/10 bg-surface relative">
        {imgSrc ? (
          <img
            src={imgSrc}
            alt={rec.label}
            className="w-full h-full object-cover grayscale group-hover:grayscale-0 transition-all duration-700"
            loading="lazy"
          />
        ) : (
          <div className="flex items-center justify-center h-full text-zinc-600 text-xs">No image</div>
        )}
        {/* Rank badge */}
        <div className="absolute top-3 left-3 border border-white/20 bg-black/70 backdrop-blur px-2 py-1 text-[10px] uppercase tracking-widest text-zinc-300">
          #{rank}
        </div>
      </div>

      {/* Info */}
      <div className="p-5 space-y-3">
        <div className="flex items-center justify-between">
          <span className="font-serif text-lg text-white">{rec.label.replace(/_/g, ' ')}</span>
          <span className="font-mono text-sm text-white">{rec.score.toFixed(2)}</span>
        </div>

        {/* Score breakdown */}
        <div className="space-y-1.5">
          <ScoreBar label="CLIP" value={rec.img_score} />
          <ScoreBar label="Occasion" value={rec.txt_score} />
          <ScoreBar label="Harmony" value={rec.harmony} />
          <ScoreBar label="Skin" value={rec.skin} />
        </div>
      </div>
    </div>
  )
}
