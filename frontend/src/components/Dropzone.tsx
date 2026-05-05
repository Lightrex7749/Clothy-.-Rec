import { useState, useCallback, useRef } from 'react'
import { Upload } from 'lucide-react'

interface Props {
  onFile: (file: File, preview: string) => void
  preview: string | null
  label?: string
}

export default function Dropzone({ onFile, preview, label = 'Drop your image here' }: Props) {
  const [over, setOver] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const handle = useCallback((file: File) => {
    const url = URL.createObjectURL(file)
    onFile(file, url)
  }, [onFile])

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault(); setOver(false)
    const f = e.dataTransfer.files[0]
    if (f) handle(f)
  }, [handle])

  return (
    <div
      className={`dropzone relative flex flex-col items-center justify-center cursor-pointer min-h-[280px] ${over ? 'drag-over' : ''}`}
      onDragOver={e => { e.preventDefault(); setOver(true) }}
      onDragLeave={() => setOver(false)}
      onDrop={onDrop}
      onClick={() => inputRef.current?.click()}
      data-testid="upload-dropzone"
    >
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={e => { const f = e.target.files?.[0]; if (f) handle(f) }}
        data-testid="upload-input"
      />
      {preview ? (
        <img src={preview} alt="preview" className="max-h-[260px] object-contain" />
      ) : (
        <>
          <Upload size={28} strokeWidth={1} className="text-zinc-500 mb-4" />
          <p className="text-zinc-500 text-sm tracking-wide">{label}</p>
          <p className="text-zinc-600 text-xs mt-1">JPEG · PNG · WebP</p>
        </>
      )}
    </div>
  )
}
