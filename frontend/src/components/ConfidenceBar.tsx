import { useEffect, useState } from 'react'
import type { Prediction } from '../types/api'

interface Props {
  title: string
  pred: Prediction
  color?: string
}

export default function ConfidenceBar({ title, pred, color = 'bg-white' }: Props) {
  const [pct, setPct] = useState(0)
  const targetPct = Math.round(pred.confidence * 100)

  useEffect(() => {
    const timer = setTimeout(() => setPct(targetPct), 100)
    return () => clearTimeout(timer)
  }, [targetPct])

  return (
    <div className="border border-white/10 bg-[#0A0A0A] p-5 group/conf" data-testid={`pred-${title.toLowerCase()}`}>
      <div className="flex items-center justify-between mb-3">
        <span className="overline">{title}</span>
        <span className="text-white font-mono text-sm group-hover/conf:scale-110 transition-transform">{pct}%</span>
      </div>
      <div className="font-serif text-xl text-white mb-3 truncate" title={pred.label.replace(/_/g, ' ')}>
        {pred.label.replace(/_/g, ' ')}
      </div>
      <div className="h-px bg-white/10 w-full relative">
        <div
          className={`absolute top-[-1px] left-0 h-[3px] ${color} transition-all duration-1000 ease-out`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}
