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
  // Claude 4.x Family (Latest - GA)
  { value: 'claude-opus-4-1-20250805', label: 'Claude Opus 4.1', badge: 'Most Powerful' },
  { value: 'claude-opus-4-20250514', label: 'Claude Opus 4' },
  { value: 'claude-sonnet-4-20250514', label: 'Claude Sonnet 4', badge: 'Recommended' },
  
  // Claude 3.x Family (Supported)
  { value: 'claude-3-7-sonnet-20250219', label: 'Claude Sonnet 3.7' },
  { value: 'claude-3-5-sonnet-20241022', label: 'Claude Sonnet 3.5 v2' },
  { value: 'claude-3-5-haiku-20241022', label: 'Claude Haiku 3.5', badge: 'Fast' },
  { value: 'claude-3-haiku-20240307', label: 'Claude Haiku 3', badge: 'Fastest' },
]

const APPROVAL_MODES = [
  { value: 'normal', label: 'Normal', description: 'Balanced security' },
  { value: 'strict', label: 'Strict', description: 'Maximum control' },
  { value: 'auto', label: 'Auto', description: 'Full automation' },
]

export default function AgentChat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [autoApproveSafe, setAutoApproveSafe] = useState(true)
  const [selectedModel, setSelectedModel] = useState('claude-sonnet-4-20250514')
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
    <div className="w-full max-w-[1400px] h-[calc(100vh-100px)] bg-white rounded-xl shadow-[0_0_50px_rgba(0,0,0,0.08)] border border-zinc-200/60 flex flex-col overflow-hidden">
      {/* Chat Header */}
      <div className="px-6 py-4 border-b border-zinc-100">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-zinc-900 to-zinc-700 flex items-center justify-center shadow-sm">
                <WrenchScrewdriverIcon className="w-5 h-5 text-white" />
              </div>
              <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-emerald-500 rounded-full border-2 border-white"></div>
            </div>
            <div>
              <h2 className="text-base font-semibold text-zinc-900 tracking-tight">ATLAS</h2>
              <p className="text-xs text-zinc-500 font-medium">Agentic DevOps</p>
            </div>
          </div>
          <button
            onClick={clearConversation}
            className="p-2 text-zinc-400 hover:text-zinc-600 hover:bg-zinc-50 rounded-lg transition-all duration-200"
            title="Clear conversation"
          >
            <TrashIcon className="w-4 h-4" />
          </button>
        </div>
        
        {/* Configuration Row */}
        <div className="mt-4 flex items-center gap-2 flex-wrap">
          <div className="flex items-center gap-2">
            <label className="text-xs font-medium text-zinc-500">Model</label>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="px-3 py-1.5 text-xs font-medium border border-zinc-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-zinc-900 focus:border-transparent bg-white hover:border-zinc-300 transition-all shadow-sm"
            >
              {CLAUDE_MODELS.map((model) => (
                <option key={model.value} value={model.value}>
                  {model.label} {model.badge ? `• ${model.badge}` : ''}
                </option>
              ))}
            </select>
          </div>
          
          <div className="flex items-center gap-2">
            <label className="text-xs font-medium text-zinc-500">Approval</label>
            <select
              value={approvalMode}
              onChange={(e) => setApprovalMode(e.target.value)}
              className="px-3 py-1.5 text-xs font-medium border border-zinc-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-zinc-900 focus:border-transparent bg-white hover:border-zinc-300 transition-all shadow-sm"
            >
              {APPROVAL_MODES.map((mode) => (
                <option key={mode.value} value={mode.value}>
                  {mode.label}
                </option>
              ))}
            </select>
          </div>
          
          <label className="flex items-center gap-2 text-xs font-medium text-zinc-600 cursor-pointer hover:text-zinc-900 transition-colors">
            <input
              type="checkbox"
              checked={autoApproveSafe}
              onChange={(e) => setAutoApproveSafe(e.target.checked)}
              className="rounded border-zinc-300 text-zinc-900 focus:ring-zinc-900 focus:ring-offset-0 cursor-pointer w-4 h-4"
            />
            <span>Auto-approve</span>
          </label>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-8 space-y-4 bg-gradient-to-b from-zinc-50/50 to-white">
        {messages.length === 0 && (
          <div className="h-full flex items-center justify-center">
            <div className="text-center space-y-6 max-w-lg">
              <div className="w-16 h-16 bg-gradient-to-br from-zinc-900 to-zinc-700 rounded-2xl mx-auto flex items-center justify-center shadow-lg shadow-zinc-900/10">
                <WrenchScrewdriverIcon className="w-8 h-8 text-white" />
              </div>
              <div className="space-y-2">
                <h3 className="text-2xl font-semibold text-zinc-900 tracking-tight">Ready to assist</h3>
                <p className="text-sm text-zinc-500 leading-relaxed">
                  Start a conversation to execute DevOps operations
                </p>
              </div>
              <div className="pt-2 grid grid-cols-2 gap-2 max-w-md mx-auto">
                <button
                  onClick={() => setInput("List all pods in production namespace")}
                  className="group text-left px-4 py-3.5 bg-white hover:bg-zinc-50 rounded-xl text-xs font-medium text-zinc-700 hover:text-zinc-900 transition-all border border-zinc-200 hover:border-zinc-300 hover:shadow-sm"
                >
                  <span className="block text-zinc-900 font-semibold mb-0.5">List pods</span>
                  <span className="text-[11px] text-zinc-500">View all running pods</span>
                </button>
                <button
                  onClick={() => setInput("Check logs for backend-python pod")}
                  className="group text-left px-4 py-3.5 bg-white hover:bg-zinc-50 rounded-xl text-xs font-medium text-zinc-700 hover:text-zinc-900 transition-all border border-zinc-200 hover:border-zinc-300 hover:shadow-sm"
                >
                  <span className="block text-zinc-900 font-semibold mb-0.5">Check logs</span>
                  <span className="text-[11px] text-zinc-500">View pod logs</span>
                </button>
                <button
                  onClick={() => setInput("Show me pod crashes in the last hour")}
                  className="group text-left px-4 py-3.5 bg-white hover:bg-zinc-50 rounded-xl text-xs font-medium text-zinc-700 hover:text-zinc-900 transition-all border border-zinc-200 hover:border-zinc-300 hover:shadow-sm"
                >
                  <span className="block text-zinc-900 font-semibold mb-0.5">Check crashes</span>
                  <span className="text-[11px] text-zinc-500">Find issues</span>
                </button>
                <button
                  onClick={() => setInput("Get deployment status in staging")}
                  className="group text-left px-4 py-3.5 bg-white hover:bg-zinc-50 rounded-xl text-xs font-medium text-zinc-700 hover:text-zinc-900 transition-all border border-zinc-200 hover:border-zinc-300 hover:shadow-sm"
                >
                  <span className="block text-zinc-900 font-semibold mb-0.5">Get status</span>
                  <span className="text-[11px] text-zinc-500">Deployment info</span>
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
                        code({ inline, className, children, ...props }: any) {
                          const match = /language-(\w+)/.exec(className || '')
                          return !inline && match ? (
                            <SyntaxHighlighter
                              style={vscDarkPlus as any}
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

      {/* Input Form */}
      <form onSubmit={sendMessage} className="p-6 border-t border-zinc-100 bg-white">
        <div className="flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Send a message to ATLAS..."
            className="flex-1 px-4 py-3 border border-zinc-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-zinc-900 focus:border-transparent bg-white text-sm placeholder:text-zinc-400 shadow-sm transition-all"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="px-6 py-3 bg-zinc-900 text-white rounded-xl hover:bg-zinc-800 disabled:bg-zinc-300 disabled:cursor-not-allowed transition-all duration-200 flex items-center gap-2 text-sm font-medium shadow-sm hover:shadow"
          >
            <span>{loading ? 'Sending...' : 'Send'}</span>
            <PaperAirplaneIcon className="w-4 h-4" />
          </button>
        </div>
      </form>
    </div>
  )
}
