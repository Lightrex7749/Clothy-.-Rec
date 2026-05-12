import { useState, useCallback, useRef, useEffect } from 'react'
import { Upload, RefreshCw } from 'lucide-react'

interface Props {
  onFile: (file: File, preview: string) => void
  preview: string | null
  label?: string
}

export default function Dropzone({ onFile, preview, label = 'Drop your image here' }: Props) {
  const [over, setOver] = useState(false)
  const [fileDetails, setFileDetails] = useState<{name: string, size: string} | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const handle = useCallback((file: File) => {
    const url = URL.createObjectURL(file)
    setFileDetails({
      name: file.name,
      size: (file.size / 1024).toFixed(1) + ' KB'
    })
    onFile(file, url)
  }, [onFile])

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault(); setOver(false)
    const f = e.dataTransfer.files[0]
    if (f) handle(f)
  }, [handle])

  return (
    <div
      className={`dropzone relative flex flex-col items-center justify-center cursor-pointer min-h-[280px] overflow-hidden group/dz ${over ? 'drag-over' : ''} ${preview ? 'border-white/30 bg-white/5' : ''}`}
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
        <>
          <div className="absolute inset-0 z-0">
             <img src={preview} alt="preview blur" className="w-full h-full object-cover blur-3xl opacity-20 scale-110" />
          </div>
          <img src={preview} alt="preview" className="max-h-[260px] object-contain relative z-10 animate-in zoom-in duration-500" />
          
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm z-20 flex flex-col items-center justify-center opacity-0 group-hover/dz:opacity-100 transition-opacity duration-300">
             <RefreshCw size={24} className="text-white mb-3" />
             <span className="overline text-white">Change Image</span>
             {fileDetails && (
               <span className="text-zinc-400 text-[10px] mt-2 font-mono">{fileDetails.name} · {fileDetails.size}</span>
             )}
          </div>
        </>
      ) : (
        <div className="flex flex-col items-center justify-center animate-in fade-in zoom-in duration-500">
          <Upload size={28} strokeWidth={1} className="text-zinc-500 mb-4 group-hover/dz:-translate-y-1 transition-transform" />
          <p className="text-zinc-500 text-sm tracking-wide">{label}</p>
          <p className="text-zinc-600 text-xs mt-1">JPEG · PNG · WebP</p>
        </div>
      )}
    </div>
  )
}
