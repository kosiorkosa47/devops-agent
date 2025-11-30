'use client'

import { useState } from 'react'
import ChatInterface from '@/components/ChatInterface'
import Header from '@/components/Header'

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col bg-gray-50">
      <Header />
      <div className="flex-1 flex items-center justify-center p-4">
        <ChatInterface />
      </div>
    </main>
  )
}
