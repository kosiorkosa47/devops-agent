'use client'

import { useState } from 'react'
import ChatInterface from '@/components/ChatInterface'
import AgentChat from '@/components/AgentChat'
import Header from '@/components/Header'

export default function Home() {
  const [mode, setMode] = useState<'chat' | 'agent'>('agent')

  return (
    <main className="flex min-h-screen flex-col bg-gray-50">
      <Header mode={mode} setMode={setMode} />
      <div className="flex-1 flex items-center justify-center p-4">
        {mode === 'agent' ? <AgentChat /> : <ChatInterface />}
      </div>
    </main>
  )
}
