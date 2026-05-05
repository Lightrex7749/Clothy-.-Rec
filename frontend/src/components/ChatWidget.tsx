import React, { useState } from 'react'
import { MessageSquare, X } from 'lucide-react'
import ChatInterface from './ChatInterface'

export default function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end">
      {isOpen && (
        <div className="mb-4 w-[350px] shadow-2xl rounded-2xl overflow-hidden border border-zinc-800 animate-in slide-in-from-bottom-5 fade-in duration-300">
          <div className="bg-zinc-950 border-b border-zinc-900 p-4 flex justify-between items-center">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-white animate-pulse" />
              <h3 className="text-white font-medium text-sm tracking-wide">AI Stylist</h3>
            </div>
            <button 
              onClick={() => setIsOpen(false)}
              className="text-zinc-500 hover:text-white transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          <ChatInterface />
        </div>
      )}

      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`w-14 h-14 rounded-full flex items-center justify-center shadow-xl transition-all duration-300 hover:scale-105 ${
          isOpen ? 'bg-zinc-800 text-white' : 'bg-white text-black hover:bg-zinc-200'
        }`}
      >
        {isOpen ? <X className="w-6 h-6" /> : <MessageSquare className="w-6 h-6" />}
      </button>
    </div>
  )
}
