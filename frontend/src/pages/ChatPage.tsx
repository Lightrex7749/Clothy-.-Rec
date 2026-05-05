import React from 'react'
import ChatInterface from '../components/ChatInterface'
import { MessageSquare } from 'lucide-react'

export default function ChatPage() {
  return (
    <div className="max-w-4xl mx-auto px-6 py-12 pt-24 h-screen flex flex-col">
      <div className="mb-8">
        <h1 className="text-4xl md:text-5xl font-bold text-white mb-4 tracking-tight flex items-center gap-4">
          <MessageSquare className="w-10 h-10" />
          AI Stylist
        </h1>
        <p className="text-zinc-400 text-lg max-w-2xl leading-relaxed">
          Chat with Atelier. Ask for outfit recommendations, discuss your color palette, or get advice on your latest wardrobe additions.
        </p>
      </div>

      <div className="flex-1 min-h-0 bg-zinc-950 border border-zinc-800 rounded-3xl overflow-hidden shadow-2xl">
        <ChatInterface fullPage={true} />
      </div>
    </div>
  )
}
