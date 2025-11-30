'use client'

import { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { 
  PaperAirplaneIcon, 
  TrashIcon, 
  CheckCircleIcon, 
  XCircleIcon,
  WrenchScrewdriverIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/solid'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Message {
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  toolUses?: any[]
  toolResults?: any[]
  pendingExecution?: any
}

const CLAUDE_MODELS = [
  // Claude 4.5 (Latest)
  { value: 'claude-sonnet-4-5-20250929', label: '🚀 Claude 4.5 Sonnet', description: 'Latest & Greatest', badge: 'NEW' },
  
  // Claude 3.5 Family
  { value: 'claude-3-5-sonnet-20241022', label: '⚡ Claude 3.5 Sonnet (Oct)', description: 'Fast & Intelligent', badge: 'HOT' },
  { value: 'claude-3-5-sonnet-20240620', label: '⚡ Claude 3.5 Sonnet (June)', description: 'Stable Version' },
  
  // Claude 3 Opus (Most Powerful)
  { value: 'claude-3-opus-20240229', label: '💎 Claude 3 Opus', description: 'Most Powerful', badge: 'PRO' },
  
  // Claude 3 Sonnet
  { value: 'claude-3-sonnet-20240229', label: '🎯 Claude 3 Sonnet', description: 'Balanced Performance' },
  
  // Claude 3 Haiku (Fastest)
  { value: 'claude-3-haiku-20240307', label: '⚡ Claude 3 Haiku', description: 'Lightning Fast', badge: 'FAST' },
  
  // Claude 2.1 (Legacy)
  { value: 'claude-2.1', label: '📚 Claude 2.1', description: 'Legacy Model' },
  { value: 'claude-2.0', label: '📚 Claude 2.0', description: 'Classic' },
  
  // Claude Instant (Ultra Fast)
  { value: 'claude-instant-1.2', label: '🏃 Claude Instant 1.2', description: 'Ultra Fast', badge: 'SPEED' },
]

const APPROVAL_MODES = [
  { value: 'normal', label: 'Normal', description: 'Approve dangerous ops only', icon: '🔒', color: 'primary' },
  { value: 'strict', label: 'Strict', description: 'Approve every operation', icon: '🛡️', color: 'warning' },
  { value: 'auto', label: 'Auto', description: 'Auto-approve everything', icon: '⚡', color: 'danger' },
]

export default function AgentChat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [autoApproveSafe, setAutoApproveSafe] = useState(true)
  const [selectedModel, setSelectedModel] = useState('claude-sonnet-4-5-20250929')
  const [approvalMode, setApprovalMode] = useState('normal')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!input.trim() || loading) return

    const userMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await axios.post(`${API_URL}/api/agent/chat`, {
        message: input,
        conversation_id: conversationId,
        auto_approve_safe: autoApproveSafe,
        approval_mode: approvalMode,
        claude_model: selectedModel
      })

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.data.response,
        timestamp: new Date(),
        toolUses: response.data.tool_uses,
        toolResults: response.data.tool_results,
        pendingExecution: response.data.execution
      }

      setMessages(prev => [...prev, assistantMessage])
      setConversationId(response.data.conversation_id)

    } catch (error) {
      console.error('Agent error:', error)
      const errorMessage: Message = {
        role: 'assistant',
        content: '❌ Sorry, I encountered an error. Please check if the backend is running.',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleApproval = async (executionId: string, approved: boolean) => {
    try {
      setLoading(true)
      
      const response = await axios.post(`${API_URL}/api/agent/approve`, {
        execution_id: executionId,
        approved: approved
      })

      const resultMessage: Message = {
        role: 'system',
        content: approved 
          ? `✅ Operation approved and executed:\n\`\`\`json\n${JSON.stringify(response.data, null, 2)}\n\`\`\``
          : '❌ Operation cancelled by user.',
        timestamp: new Date()
      }

      setMessages(prev => prev.map(msg => 
        msg.pendingExecution?.execution_id === executionId 
          ? { ...msg, pendingExecution: undefined }
          : msg
      ).concat(resultMessage))

    } catch (error) {
      console.error('Approval error:', error)
      const errorMessage: Message = {
        role: 'system',
        content: '❌ Failed to process approval.',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const clearConversation = () => {
    setMessages([])
    setConversationId(null)
  }

  return (
    <div className="w-full max-w-6xl h-[calc(100vh-120px)] bg-gradient-to-br from-white via-blue-50/30 to-purple-50/30 rounded-2xl shadow-2xl border border-gray-200/50 backdrop-blur-sm flex flex-col overflow-hidden">
      {/* Chat Header */}
      <div className="px-6 py-4 border-b border-gray-200/50 bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 relative overflow-hidden">
        {/* Animated Background */}
        <div className="absolute inset-0 bg-gradient-to-r from-blue-600/90 via-purple-600/90 to-pink-600/90 animate-gradient-x"></div>
        <div className="relative z-10">
        <div className="flex items-center justify-between mb-4">
          <div>
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-white/20 backdrop-blur-md rounded-xl flex items-center justify-center animate-pulse">
                <WrenchScrewdriverIcon className="w-6 h-6 text-white drop-shadow-lg" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-white drop-shadow-lg flex items-center gap-2">
                  ATLAS Agentic Assistant
                  <span className="text-2xl animate-bounce">🚀</span>
                </h2>
                <p className="text-xs text-white/90 drop-shadow">AI-Powered DevOps Automation</p>
              </div>
              <span className="px-3 py-1 bg-green-500/90 backdrop-blur-sm text-white text-xs font-bold rounded-full shadow-lg animate-pulse">✨ LIVE</span>
            </div>
          </div>
          <button
            onClick={clearConversation}
            className="p-2.5 text-white/80 hover:text-white hover:bg-white/20 rounded-xl transition-all hover:scale-110 backdrop-blur-sm"
            title="Clear conversation"
          >
            <TrashIcon className="w-5 h-5 drop-shadow" />
          </button>
        </div>
        
        {/* Configuration Row */}
        <div className="flex items-center gap-3 flex-wrap">
          {/* Model Selector */}
          <div className="flex items-center gap-2">
            <label className="text-sm font-semibold text-white drop-shadow">🤖 Model:</label>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="px-3 py-2 text-sm border-2 border-white/30 rounded-xl focus:outline-none focus:ring-2 focus:ring-white/50 bg-white/90 backdrop-blur-md font-medium shadow-lg hover:bg-white transition-all"
            >
              {CLAUDE_MODELS.map((model) => (
                <option key={model.value} value={model.value}>
                  {model.label}
                </option>
              ))}
            </select>
          </div>
          
          {/* Approval Mode Selector */}
          <div className="flex items-center gap-2">
            <label className="text-sm font-semibold text-white drop-shadow">🛡️ Mode:</label>
            <select
              value={approvalMode}
              onChange={(e) => setApprovalMode(e.target.value)}
              className="px-3 py-2 text-sm border-2 border-white/30 rounded-xl focus:outline-none focus:ring-2 focus:ring-white/50 bg-white/90 backdrop-blur-md font-medium shadow-lg hover:bg-white transition-all"
            >
              {APPROVAL_MODES.map((mode) => (
                <option key={mode.value} value={mode.value}>
                  {mode.icon} {mode.label}
                </option>
              ))}
            </select>
          </div>
          
          {/* Auto-approve Toggle */}
          <label className="flex items-center space-x-2 text-sm bg-white/10 backdrop-blur-md px-3 py-2 rounded-xl hover:bg-white/20 transition-all cursor-pointer">
            <input
              type="checkbox"
              checked={autoApproveSafe}
              onChange={(e) => setAutoApproveSafe(e.target.checked)}
              className="rounded w-4 h-4 cursor-pointer"
            />
            <span className="font-semibold text-white drop-shadow">✨ Auto-approve</span>
          </label>
        </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 && (
          <div className="h-full flex items-center justify-center">
            <div className="text-center space-y-3">
              <div className="w-20 h-20 bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 rounded-2xl mx-auto flex items-center justify-center shadow-2xl animate-pulse">
                <WrenchScrewdriverIcon className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-2xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">ATLAS Agentic Mode Activated! 🎉</h3>
              <p className="text-gray-500 max-w-md">
                I can now execute operations for you! Try asking me to check pod status, view logs, or scale deployments.
              </p>
              <div className="pt-4 grid grid-cols-2 gap-3 max-w-2xl">
                <button
                  onClick={() => setInput("List all pods in production namespace")}
                  className="text-left p-4 bg-gradient-to-r from-blue-50 to-blue-100 hover:from-blue-100 hover:to-blue-200 rounded-xl text-sm text-gray-800 transition-all hover:scale-105 hover:shadow-lg border border-blue-200/50 font-medium"
                >
                  🔍 List all pods in production
                </button>
                <button
                  onClick={() => setInput("Check logs for backend-python pod")}
                  className="text-left p-3 bg-blue-50 hover:bg-blue-100 rounded-lg text-sm text-gray-700 transition-colors"
                >
                  📜 Check backend logs
                </button>
                <button
                  onClick={() => setInput("Show me pod crashes in the last hour")}
                  className="text-left p-3 bg-blue-50 hover:bg-blue-100 rounded-lg text-sm text-gray-700 transition-colors"
                >
                  🚨 Check for pod crashes
                </button>
                <button
                  onClick={() => setInput("Get deployment status in staging")}
                  className="text-left p-3 bg-blue-50 hover:bg-blue-100 rounded-lg text-sm text-gray-700 transition-colors"
                >
                  📊 Get deployment status
                </button>
              </div>
            </div>
          </div>
        )}

        {messages.map((message, index) => (
          <div key={index}>
            <div
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-lg px-4 py-3 ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : message.role === 'system'
                    ? 'bg-yellow-50 text-gray-900 border border-yellow-200'
                    : 'bg-gray-100 text-gray-900'
                }`}
              >
                {message.role === 'assistant' ? (
                  <div className="prose prose-sm max-w-none">
                    <ReactMarkdown
                      components={{
                        code({ node, inline, className, children, ...props }) {
                          const match = /language-(\w+)/.exec(className || '')
                          return !inline && match ? (
                            <SyntaxHighlighter
                              style={vscDarkPlus}
                              language={match[1]}
                              PreTag="div"
                              {...props}
                            >
                              {String(children).replace(/\n$/, '')}
                            </SyntaxHighlighter>
                          ) : (
                            <code className={className} {...props}>
                              {children}
                            </code>
                          )
                        }
                      }}
                    >
                      {message.content}
                    </ReactMarkdown>
                  </div>
                ) : (
                  <p className="whitespace-pre-wrap">{message.content}</p>
                )}
                
                {/* Tool execution info */}
                {message.toolUses && message.toolUses.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-gray-300">
                    <p className="text-xs font-semibold mb-2">🔧 Tools Used:</p>
                    {message.toolUses.map((tool, i) => (
                      <div key={i} className="text-xs bg-white rounded p-2 mb-1">
                        <span className="font-mono">{tool.name}</span>
                      </div>
                    ))}
                  </div>
                )}

                <div className="text-xs mt-2 opacity-70">
                  {message.timestamp.toLocaleTimeString()}
                </div>
              </div>
            </div>

            {/* Approval Required UI */}
            {message.pendingExecution && (
              <div className="mt-3 p-4 bg-orange-50 border-2 border-orange-300 rounded-lg">
                <div className="flex items-start space-x-3">
                  <ExclamationTriangleIcon className="w-6 h-6 text-orange-600 flex-shrink-0 mt-1" />
                  <div className="flex-1">
                    <h4 className="font-semibold text-orange-900 mb-2">⚠️ Approval Required</h4>
                    <p className="text-sm text-orange-800 mb-3">
                      <strong>{message.pendingExecution.tool_name}</strong>
                    </p>
                    <div className="text-xs bg-white rounded p-3 mb-3 font-mono text-gray-700">
                      {JSON.stringify(message.pendingExecution.parameters, null, 2)}
                    </div>
                    <p className="text-sm text-orange-700 mb-4">
                      {message.pendingExecution.description}
                    </p>
                    <div className="flex space-x-3">
                      <button
                        onClick={() => handleApproval(message.pendingExecution.execution_id, true)}
                        disabled={loading}
                        className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 transition-colors"
                      >
                        <CheckCircleIcon className="w-5 h-5" />
                        <span>Approve & Execute</span>
                      </button>
                      <button
                        onClick={() => handleApproval(message.pendingExecution.execution_id, false)}
                        disabled={loading}
                        className="flex items-center space-x-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:bg-gray-400 transition-colors"
                      >
                        <XCircleIcon className="w-5 h-5" />
                        <span>Reject</span>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg px-4 py-3">
              <div className="flex space-x-2">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200"></div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <form onSubmit={sendMessage} className="p-4 border-t border-gray-200">
        <div className="flex space-x-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask ATLAS to execute operations for you..."
            className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="px-8 py-3 bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 text-white rounded-xl hover:from-blue-700 hover:via-purple-700 hover:to-pink-700 disabled:from-gray-300 disabled:via-gray-300 disabled:to-gray-300 disabled:cursor-not-allowed transition-all hover:scale-105 hover:shadow-xl flex items-center space-x-2 font-semibold shadow-lg"
          >
            <PaperAirplaneIcon className="w-5 h-5" />
            <span>Send</span>
          </button>
        </div>
      </form>
    </div>
  )
}
