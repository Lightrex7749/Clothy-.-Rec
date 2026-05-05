interface Props {
  label: string
  value: number
  max?: number
}

export default function ScoreBar({ label, value, max = 1 }: Props) {
  const pct = Math.min(100, (value / max) * 100)
  return (
    <div className="flex items-center gap-3 text-xs" data-testid={`score-${label}`}>
      <span className="w-16 text-zinc-500 uppercase tracking-widest text-[10px] shrink-0">{label}</span>
      <div className="score-track flex-1">
        <div className="score-fill" style={{ width: `${pct}%` }} />
      </div>
      <span className="text-zinc-300 font-mono w-12 text-right">{value.toFixed(2)}</span>
    </div>
  )
}
