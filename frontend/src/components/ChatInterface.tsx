import React, { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, Loader2 } from 'lucide-react'
import { apiChat } from '../lib/api'
import { getStats } from '../lib/storage'
import type { ChatTurn } from '../types/api'

export default function ChatInterface({ fullPage = false }: { fullPage?: boolean }) {
  const [messages, setMessages] = useState<ChatTurn[]>([{
    role: 'model',
    content: "Hello! I'm Atelier, your AI personal fashion stylist. I can see your recent wardrobe analysis and skin profile. How can I help you style today?"
  }])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const userMessage: ChatTurn = { role: 'user', content: input.trim() }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      // Gather context
      const context = getStats()
      const historyToSent = messages.slice(1) // exclude initial greeting if desired, or send all

      const res = await apiChat(userMessage.content, historyToSent, context)
      setMessages(prev => [...prev, { role: 'model', content: res.reply }])
    } catch (err: any) {
      setMessages(prev => [...prev, { role: 'model', content: `Error: ${err.message}` }])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className={`flex flex-col bg-zinc-950 text-white ${fullPage ? 'h-full' : 'h-[500px]'}`}>
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {messages.map((msg, i) => (
          <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            {msg.role === 'model' && (
              <div className="w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center shrink-0 border border-zinc-700">
                <Bot className="w-5 h-5 text-white" />
              </div>
            )}
            
            <div className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
              msg.role === 'user' 
                ? 'bg-white text-black rounded-tr-sm font-medium' 
                : 'bg-zinc-900 text-zinc-300 rounded-tl-sm border border-zinc-800'
            }`}>
              {msg.content}
            </div>

            {msg.role === 'user' && (
              <div className="w-8 h-8 rounded-full bg-white flex items-center justify-center shrink-0">
                <User className="w-5 h-5 text-black" />
              </div>
            )}
          </div>
        ))}
        {isLoading && (
          <div className="flex gap-3 justify-start">
            <div className="w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center shrink-0 border border-zinc-700">
              <Bot className="w-5 h-5 text-white" />
            </div>
            <div className="bg-zinc-900 border border-zinc-800 rounded-2xl rounded-tl-sm px-4 py-3 flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin text-zinc-500" />
              <span className="text-sm text-zinc-500">Stylist is typing...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-4 border-t border-zinc-900 bg-zinc-950">
        <form 
          onSubmit={(e) => { e.preventDefault(); handleSend(); }}
          className="flex gap-2"
        >
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="Ask your AI Stylist..."
            className="flex-1 bg-zinc-900 text-white placeholder:text-zinc-600 border border-zinc-800 rounded-full px-5 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-white transition-all"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="bg-white text-black p-3 rounded-full hover:bg-zinc-200 transition-colors disabled:opacity-50 disabled:hover:bg-white"
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
      </div>
    </div>
  )
}
