import { useEffect, useState } from 'react'

interface Props {
  label: string
  value: number
  max?: number
}

export default function ScoreBar({ label, value, max = 1 }: Props) {
  const [width, setWidth] = useState(0)
  
  useEffect(() => {
    // Trigger animation after mount
    const timer = setTimeout(() => {
      setWidth(Math.min(100, (value / max) * 100))
    }, 100)
    return () => clearTimeout(timer)
  }, [value, max])

  // Color coding based on score (assuming higher is better)
  const isHigh = value / max > 0.7
  const isLow = value / max < 0.3
  
  const fillClass = isHigh ? 'bg-white shadow-[0_0_8px_rgba(255,255,255,0.8)]' : 
                   isLow ? 'bg-zinc-600' : 'bg-zinc-300'

  return (
    <div className="flex items-center gap-3 text-xs group/score" data-testid={`score-${label}`}>
      <span className="w-16 text-zinc-500 uppercase tracking-widest text-[10px] shrink-0">{label}</span>
      <div className="score-track flex-1 overflow-visible">
        <div 
          className={`score-fill ${fillClass}`} 
          style={{ width: `${width}%` }} 
        />
      </div>
      <span className={`font-mono w-12 text-right transition-colors duration-500 ${isHigh ? 'text-white' : 'text-zinc-400'}`}>
        {value.toFixed(2)}
      </span>
    </div>
  )
}
