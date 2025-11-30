'use client'

import { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { 
  PaperAirplaneIcon,
  PlayIcon,
  PauseIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  CommandLineIcon,
  CpuChipIcon
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

interface ActionLog {
  id: string
  timestamp: Date
  tool: string
  action: string
  status: 'pending' | 'running' | 'success' | 'error'
  output?: string
}

const CLAUDE_MODELS = [
  // Claude 4.5 Family (Latest - Production IDs)
  { value: 'claude-sonnet-4-5-20250929', label: 'Claude Sonnet 4.5', badge: 'Best Coding & Agents' },
  { value: 'claude-haiku-4-5-20251001', label: 'Claude Haiku 4.5', badge: 'Fast Executor' },
  
  // Claude 4.x Family
  { value: 'claude-opus-4-1-20250805', label: 'Claude Opus 4.1', badge: 'Deep Thinker' },
  { value: 'claude-opus-4-20250514', label: 'Claude Opus 4' },
  { value: 'claude-sonnet-4-20250514', label: 'Claude Sonnet 4' },
  
  // Claude 3.x Family (Legacy)
  { value: 'claude-3-7-sonnet-20250219', label: 'Claude Sonnet 3.7' },
  { value: 'claude-3-5-sonnet-20241022', label: 'Claude Sonnet 3.5 v2' },
  { value: 'claude-3-5-haiku-20241022', label: 'Claude Haiku 3.5' },
  { value: 'claude-3-haiku-20240307', label: 'Claude Haiku 3' },
]

export default function AgentChatManus() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [selectedModel, setSelectedModel] = useState('claude-sonnet-4-5-20250929')
  const [approvalMode, setApprovalMode] = useState('normal')
  const [actionLogs, setActionLogs] = useState<ActionLog[]>([])
  const [isPaused, setIsPaused] = useState(false)
  const [showActionsPanel, setShowActionsPanel] = useState(false)
  const [panelWidth, setPanelWidth] = useState(50) // percentage
  const [isResizing, setIsResizing] = useState(false)
  const [streamingText, setStreamingText] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const actionsEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    actionsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, actionLogs])

  const addActionLog = (tool: string, action: string, status: ActionLog['status'], output?: string) => {
    const log: ActionLog = {
      id: Date.now().toString(),
      timestamp: new Date(),
      tool,
      action,
      status,
      output
    }
    setActionLogs(prev => [...prev, log])
    // Auto-show panel when action is logged
    if (!showActionsPanel) {
      setShowActionsPanel(true)
    }
  }

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsResizing(true)
    e.preventDefault()
  }

  const handleMouseMove = (e: MouseEvent) => {
    if (!isResizing) return
    const newWidth = (e.clientX / window.innerWidth) * 100
    if (newWidth > 30 && newWidth < 70) {
      setPanelWidth(100 - newWidth)
    }
  }

  const handleMouseUp = () => {
    setIsResizing(false)
  }

  useEffect(() => {
    if (isResizing) {
      window.addEventListener('mousemove', handleMouseMove)
      window.addEventListener('mouseup', handleMouseUp)
      return () => {
        window.removeEventListener('mousemove', handleMouseMove)
        window.removeEventListener('mouseup', handleMouseUp)
      }
    }
  }, [isResizing])

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

    addActionLog('System', 'Processing user request...', 'running')

    try {
      const response = await axios.post(`${API_URL}/api/agent/chat`, {
        message: input,
        conversation_id: conversationId,
        auto_approve_safe: true,
        approval_mode: approvalMode,
        claude_model: selectedModel
      })

      // Add action logs for tools used
      if (response.data.tool_uses) {
        response.data.tool_uses.forEach((tool: any) => {
          addActionLog(tool.name, JSON.stringify(tool.input), 'success')
        })
      }

      // Streaming effect
      const fullText = response.data.response
      setIsStreaming(true)
      setStreamingText('')
      
      // Add empty message that will be updated
      const assistantMessage: Message = {
        role: 'assistant',
        content: '',
        timestamp: new Date(),
        toolUses: response.data.tool_uses,
        toolResults: response.data.tool_results,
        pendingExecution: response.data.execution
      }
      setMessages(prev => [...prev, assistantMessage])

      // Stream text character by character
      let currentText = ''
      for (let i = 0; i < fullText.length; i++) {
        currentText += fullText[i]
        setStreamingText(currentText)
        setMessages(prev => {
          const newMessages = [...prev]
          newMessages[newMessages.length - 1].content = currentText
          return newMessages
        })
        await new Promise(resolve => setTimeout(resolve, 10)) // 10ms per character
      }
      
      setIsStreaming(false)
      setConversationId(response.data.conversation_id)
      
      addActionLog('System', 'Task completed', 'success')

    } catch (error) {
      console.error('Agent error:', error)
      addActionLog('System', 'Error occurred', 'error', String(error))
      
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
      addActionLog('User', approved ? 'Approved execution' : 'Rejected execution', 'running')
      
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

      addActionLog('System', approved ? 'Execution completed' : 'Execution cancelled', approved ? 'success' : 'error')

    } catch (error) {
      console.error('Approval error:', error)
      addActionLog('System', 'Approval failed', 'error')
    } finally {
      setLoading(false)
    }
  }

  const getStatusIcon = (status: ActionLog['status']) => {
    switch (status) {
      case 'pending': return <ClockIcon className="w-4 h-4 text-gray-400" />
      case 'running': return <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      case 'success': return <CheckCircleIcon className="w-4 h-4 text-green-500" />
      case 'error': return <XCircleIcon className="w-4 h-4 text-red-500" />
    }
  }

  return (
    <div className="flex h-screen bg-[#0A0A0A] text-white relative">
      {/* LEFT PANEL - Chat Interface */}
      <div 
        className="flex flex-col border-r border-zinc-800 transition-all duration-300"
        style={{ width: showActionsPanel ? `${100 - panelWidth}%` : '100%' }}
      >
        {/* Header */}
        <div className="flex-shrink-0 px-6 py-4 border-b border-zinc-800 bg-black/40 backdrop-blur-sm">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-lg font-semibold text-white">ATLAS Agent</h1>
              <p className="text-xs text-zinc-400">Autonomous DevOps Assistant</p>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-xs text-zinc-400">Active</span>
            </div>
          </div>

          {/* Controls */}
          <div className="mt-4 flex items-center gap-3">
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="px-3 py-1.5 text-xs bg-zinc-900 border border-zinc-700 rounded-lg focus:outline-none focus:ring-1 focus:ring-zinc-600"
            >
              {CLAUDE_MODELS.map((model) => (
                <option key={model.value} value={model.value}>
                  {model.label} {model.badge ? `• ${model.badge}` : ''}
                </option>
              ))}
            </select>

            <select
              value={approvalMode}
              onChange={(e) => setApprovalMode(e.target.value)}
              className="px-3 py-1.5 text-xs bg-zinc-900 border border-zinc-700 rounded-lg focus:outline-none focus:ring-1 focus:ring-zinc-600"
            >
              <option value="normal">Normal</option>
              <option value="strict">Strict</option>
              <option value="auto">Auto</option>
            </select>

            <button
              onClick={() => setIsPaused(!isPaused)}
              className="p-2 bg-zinc-900 hover:bg-zinc-800 border border-zinc-700 rounded-lg transition-colors"
              title={isPaused ? 'Resume' : 'Pause'}
            >
              {isPaused ? <PlayIcon className="w-4 h-4" /> : <PauseIcon className="w-4 h-4" />}
            </button>

            {actionLogs.length > 0 && (
              <button
                onClick={() => setShowActionsPanel(!showActionsPanel)}
                className={`px-3 py-2 text-xs font-medium rounded-lg transition-all ${
                  showActionsPanel 
                    ? 'bg-blue-600 hover:bg-blue-700 text-white' 
                    : 'bg-zinc-900 hover:bg-zinc-800 border border-zinc-700 text-zinc-300'
                }`}
              >
                {showActionsPanel ? 'Hide' : 'Show'} Actions ({actionLogs.length})
              </button>
            )}
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.length === 0 && (
            <div className="h-full flex items-center justify-center">
              <div className="text-center space-y-3 max-w-md">
                <div className="w-16 h-16 bg-gradient-to-br from-blue-600 to-purple-600 rounded-2xl mx-auto flex items-center justify-center">
                  <CpuChipIcon className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-xl font-semibold text-white">Ready to Execute</h3>
                <p className="text-sm text-zinc-400">
                  Describe your DevOps task and watch it execute in real-time
                </p>
              </div>
            </div>
          )}

          {messages.map((message, index) => (
            <div key={index} className="group py-6 px-4 hover:bg-zinc-900/30 transition-colors">
              {/* Role Label */}
              <div className="mb-2">
                <span className={`text-xs font-semibold uppercase tracking-wider ${
                  message.role === 'user' ? 'text-blue-400' : 'text-zinc-400'
                }`}>
                  {message.role === 'user' ? 'You' : 'ATLAS'}
                </span>
              </div>
              
              {/* Message Content */}
              <div className="max-w-none">
                {message.role === 'assistant' ? (
                  <div className="prose prose-invert prose-sm max-w-none prose-headings:font-semibold prose-p:text-zinc-200 prose-p:leading-7">
                    <ReactMarkdown
                      components={{
                        code({ inline, className, children, ...props }: any) {
                          const match = /language-(\w+)/.exec(className || '')
                          return !inline && match ? (
                            <SyntaxHighlighter
                              style={vscDarkPlus as any}
                              language={match[1]}
                              PreTag="div"
                              className="rounded-lg my-3"
                              {...props}
                            >
                              {String(children).replace(/\n$/, '')}
                            </SyntaxHighlighter>
                          ) : (
                            <code className="bg-zinc-800/80 px-1.5 py-0.5 rounded text-blue-400 text-sm" {...props}>
                              {children}
                            </code>
                          )
                        }
                      }}
                    >
                      {message.content}
                    </ReactMarkdown>
                    {isStreaming && index === messages.length - 1 && (
                      <span className="inline-block w-0.5 h-5 bg-blue-500 ml-1 animate-pulse"></span>
                    )}
                  </div>
                ) : message.role === 'system' ? (
                  <div className="bg-amber-900/10 border-l-2 border-amber-600 px-4 py-3 rounded">
                    <p className="text-sm text-amber-200 leading-relaxed">{message.content}</p>
                  </div>
                ) : (
                  <p className="text-sm text-zinc-200 leading-7 whitespace-pre-wrap">{message.content}</p>
                )}
              </div>
              
              {/* Timestamp */}
              <div className="text-[10px] text-zinc-600 mt-2">
                {message.timestamp.toLocaleTimeString()}
              </div>

              {/* Approval UI */}
              {message.pendingExecution && (
                <div className="mt-3 p-4 bg-orange-900/20 border border-orange-600/30 rounded-xl">
                  <div className="flex items-start gap-3">
                    <div className="flex-1">
                      <h4 className="font-semibold text-orange-400 text-sm mb-2">⚠️ Approval Required</h4>
                      <p className="text-xs text-orange-200 mb-3">
                        <strong>{message.pendingExecution.tool_name}</strong>
                      </p>
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleApproval(message.pendingExecution.execution_id, true)}
                          disabled={loading}
                          className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg text-xs font-medium transition-colors disabled:opacity-50"
                        >
                          Approve
                        </button>
                        <button
                          onClick={() => handleApproval(message.pendingExecution.execution_id, false)}
                          disabled={loading}
                          className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg text-xs font-medium transition-colors disabled:opacity-50"
                        >
                          Reject
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
              <div className="bg-zinc-800 rounded-2xl px-4 py-3">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-zinc-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-zinc-400 rounded-full animate-bounce delay-100"></div>
                  <div className="w-2 h-2 bg-zinc-400 rounded-full animate-bounce delay-200"></div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <form onSubmit={sendMessage} className="flex-shrink-0 p-4 border-t border-zinc-800 bg-black/40">
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Describe your task..."
              className="flex-1 px-4 py-3 bg-zinc-900 border border-zinc-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-600 text-sm placeholder:text-zinc-500"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={!input.trim() || loading}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-zinc-700 disabled:cursor-not-allowed rounded-xl transition-colors flex items-center gap-2 text-sm font-medium"
            >
              <span>{loading ? 'Executing...' : 'Execute'}</span>
              <PaperAirplaneIcon className="w-4 h-4" />
            </button>
          </div>
        </form>
      </div>

      {/* RESIZE HANDLE */}
      {showActionsPanel && (
        <div
          className="w-1 bg-zinc-800 hover:bg-blue-600 cursor-col-resize transition-colors relative group"
          onMouseDown={handleMouseDown}
        >
          <div className="absolute inset-y-0 -left-1 -right-1 group-hover:bg-blue-600/20" />
        </div>
      )}

      {/* RIGHT PANEL - Live Action Viewer (Collapsible) */}
      <div 
        className={`flex flex-col bg-zinc-950 transition-all duration-300 ${
          showActionsPanel ? 'opacity-100' : 'opacity-0 w-0 overflow-hidden'
        }`}
        style={{ width: showActionsPanel ? `${panelWidth}%` : '0%' }}
      >
        {/* Header */}
        <div className="flex-shrink-0 px-6 py-4 border-b border-zinc-800 bg-black/40 backdrop-blur-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CommandLineIcon className="w-5 h-5 text-zinc-400" />
              <h2 className="text-base font-semibold text-white">Live Execution</h2>
            </div>
            <div className="text-xs text-zinc-400">
              {actionLogs.length} actions logged
            </div>
          </div>
        </div>

        {/* Action Logs */}
        <div className="flex-1 overflow-y-auto p-6 space-y-2">
          {actionLogs.length === 0 && (
            <div className="h-full flex items-center justify-center">
              <div className="text-center space-y-2">
                <CommandLineIcon className="w-12 h-12 text-zinc-700 mx-auto" />
                <p className="text-sm text-zinc-500">No actions yet</p>
              </div>
            </div>
          )}

          {actionLogs.map((log) => (
            <div
              key={log.id}
              className="p-3 bg-zinc-900/50 border border-zinc-800 rounded-lg hover:border-zinc-700 transition-colors"
            >
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 mt-0.5">
                  {getStatusIcon(log.status)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-medium text-blue-400">{log.tool}</span>
                    <span className="text-[10px] text-zinc-500">
                      {log.timestamp.toLocaleTimeString()}
                    </span>
                  </div>
                  <p className="text-xs text-zinc-300 break-words">{log.action}</p>
                  {log.output && (
                    <div className="mt-2 p-2 bg-black/50 rounded text-[10px] text-zinc-400 font-mono overflow-x-auto">
                      {log.output}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}

          <div ref={actionsEndRef} />
        </div>
      </div>
    </div>
  )
}
