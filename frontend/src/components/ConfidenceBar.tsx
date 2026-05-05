import type { Prediction } from '../types/api'

interface Props {
  title: string
  pred: Prediction
  color?: string
}

export default function ConfidenceBar({ title, pred, color = 'bg-white' }: Props) {
  const pct = Math.round(pred.confidence * 100)
  return (
    <div className="border border-white/10 bg-[#0A0A0A] p-5" data-testid={`pred-${title.toLowerCase()}`}>
      <div className="flex items-center justify-between mb-3">
        <span className="overline">{title}</span>
        <span className="text-white font-mono text-sm">{pct}%</span>
      </div>
      <div className="font-serif text-xl text-white mb-3">
        {pred.label.replace(/_/g, ' ')}
      </div>
      <div className="h-px bg-white/10 w-full relative">
        <div
          className={`absolute top-[-1px] left-0 h-[3px] ${color} transition-all duration-700`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}
