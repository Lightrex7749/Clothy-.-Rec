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
    <div className="relative p-px rounded-sm overflow-hidden group/outer hover:-translate-y-1 transition-transform duration-500" data-testid={`rec-card-${rank}`}>
      {/* Animated gradient border */}
      <div className="absolute inset-0 bg-gradient-to-b from-white/10 to-transparent opacity-0 group-hover/outer:opacity-100 transition-opacity duration-500" />
      
      <div className="border border-white/10 bg-[#0A0A0A] relative z-10 h-full flex flex-col group">
        {/* Image */}
        <div className="aspect-[3/4] overflow-hidden border-b border-white/10 bg-surface relative">
          {imgSrc ? (
            <img
              src={imgSrc}
              alt={rec.label}
              className="w-full h-full object-cover grayscale group-hover:grayscale-0 group-hover:scale-105 transition-all duration-700"
              loading="lazy"
            />
          ) : (
            <div className="flex items-center justify-center h-full text-zinc-600 text-xs">No image</div>
          )}
          {/* Rank badge */}
          <div className="absolute top-3 left-3 border border-white/20 bg-black/70 backdrop-blur px-2 py-1 text-[10px] uppercase tracking-widest text-zinc-300">
            #{rank}
          </div>
          {/* Source badge */}
          {rec.source && (
            <div className="absolute top-3 right-3 border border-white/20 bg-black/70 backdrop-blur px-2 py-1 text-[10px] uppercase tracking-widest text-zinc-300 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
              {rec.source === 'deepfashion' ? 'DF' : 'Ecom'}
            </div>
          )}
        </div>

        {/* Info */}
        <div className="p-5 space-y-3 flex-1 flex flex-col justify-end">
          <div className="flex items-center justify-between">
            <span className="font-serif text-lg text-white truncate mr-2" title={rec.label.replace(/_/g, ' ')}>{rec.label.replace(/_/g, ' ')}</span>
            <span className="font-mono text-sm text-white shrink-0">{rec.score.toFixed(2)}</span>
          </div>

          {/* Score breakdown */}
          <div className="space-y-1.5 pt-2 border-t border-white/5">
            {rec.similarity_score !== undefined ? (
              <ScoreBar label="Sim" value={rec.similarity_score} max={1} />
            ) : (
              <ScoreBar label="CLIP" value={rec.img_score} />
            )}
            <ScoreBar label="Occasion" value={rec.txt_score} />
            <ScoreBar label="Harmony" value={rec.harmony} />
            <ScoreBar label="Skin" value={rec.skin} />
          </div>
        </div>
      </div>
    </div>
  )
}
