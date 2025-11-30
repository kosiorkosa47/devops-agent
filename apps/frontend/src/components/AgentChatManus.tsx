'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
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
  CpuChipIcon,
  Bars3Icon,
  PlusIcon,
  TrashIcon,
  ChatBubbleLeftIcon
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
  const [showSidebar, setShowSidebar] = useState(false)
  const [conversations, setConversations] = useState<any[]>([])
  const [loadingConversations, setLoadingConversations] = useState(false)
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const actionsEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    actionsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, actionLogs])

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px'
    }
  }, [input])

  // Load conversations on mount
  useEffect(() => {
    if (showSidebar) {
      loadConversations()
    }
  }, [showSidebar])

  const loadConversations = async () => {
    try {
      setLoadingConversations(true)
      const response = await axios.get(`${API_URL}/api/agent/conversations`)
      setConversations(response.data.conversations || [])
    } catch (error) {
      console.error('Failed to load conversations:', error)
    } finally {
      setLoadingConversations(false)
    }
  }

  const createNewChat = () => {
    setMessages([])
    setConversationId(null)
    setActionLogs([])
    setInput('')
    setShowSidebar(false)
  }

  const loadConversation = async (convId: string) => {
    try {
      setLoading(true)
      const response = await axios.get(`${API_URL}/api/agent/conversations/${convId}`)
      
      // Convert messages to proper format with Date objects
      const loadedMessages = response.data.messages.map((msg: any) => ({
        ...msg,
        timestamp: new Date(msg.timestamp || Date.now())
      }))
      
      setMessages(loadedMessages)
      setConversationId(convId)
      setShowSidebar(false)
      setActionLogs([])
    } catch (error) {
      console.error('Failed to load conversation:', error)
    } finally {
      setLoading(false)
    }
  }

  const deleteConversation = async (convId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    
    if (!confirm('Delete this conversation?')) return
    
    try {
      await axios.delete(`${API_URL}/api/agent/conversations/${convId}`)
      
      // Reload conversations list
      await loadConversations()
      
      // If deleted current conversation, start new chat
      if (convId === conversationId) {
        createNewChat()
      }
    } catch (error) {
      console.error('Failed to delete conversation:', error)
    }
  }

  const addActionLog = (tool: string, action: string, status: ActionLog['status'], output?: string) => {
    const log: ActionLog = {
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`, // Unique ID with timestamp + random
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

  const isResizingRef = useRef(false)

  const handleMouseDown = (e: React.MouseEvent) => {
    isResizingRef.current = true
    setIsResizing(true)
    e.preventDefault()
  }

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isResizingRef.current) return
    
    const newWidth = (e.clientX / window.innerWidth) * 100
    if (newWidth > 30 && newWidth < 70) {
      setPanelWidth(100 - newWidth)
    }
  }, [])

  const handleMouseUp = useCallback(() => {
    isResizingRef.current = false
    setIsResizing(false)
  }, [])

  useEffect(() => {
    // Add listeners once on mount
    window.addEventListener('mousemove', handleMouseMove)
    window.addEventListener('mouseup', handleMouseUp)
    
    return () => {
      window.removeEventListener('mousemove', handleMouseMove)
      window.removeEventListener('mouseup', handleMouseUp)
    }
  }, [handleMouseMove, handleMouseUp])

  const formatToolAction = (toolName: string, params: any): string => {
    // Format tool actions to show readable commands
    try {
      switch (toolName) {
        case 'kubectl_get_pods':
          return `kubectl get pods ${params.namespace ? `-n ${params.namespace}` : '--all-namespaces'} ${params.label_selector ? `-l ${params.label_selector}` : ''}`
        
        case 'kubectl_get_pod_logs':
          return `kubectl logs ${params.pod_name} -n ${params.namespace} ${params.tail_lines ? `--tail=${params.tail_lines}` : ''}`
        
        case 'kubectl_describe_pod':
          return `kubectl describe pod ${params.pod_name} -n ${params.namespace}`
        
        case 'kubectl_get_deployments':
          return `kubectl get deployments ${params.namespace ? `-n ${params.namespace}` : '--all-namespaces'}`
        
        case 'kubectl_scale_deployment':
          return `kubectl scale deployment ${params.deployment_name} --replicas=${params.replicas} -n ${params.namespace}`
        
        case 'docker_list_containers':
          return `docker ps ${params.all ? '-a' : ''}`
        
        case 'docker_logs':
          return `docker logs ${params.container_id} ${params.tail ? `--tail ${params.tail}` : ''}`
        
        case 'docker_inspect':
          return `docker inspect ${params.container_id}`
        
        case 'execute_powershell_command':
          return `PowerShell: ${params.command}`
        
        case 'execute_cmd_command':
          return `CMD: ${params.command}`
        
        case 'install_minikube':
          return 'Installing Minikube...'
        
        case 'install_kubectl':
          return 'Installing kubectl...'
        
        case 'start_minikube':
          return `minikube start ${params.driver ? `--driver=${params.driver}` : ''}`
        
        case 'stop_minikube':
          return 'minikube stop'
        
        case 'get_cluster_status':
          return 'Checking cluster status...'
        
        case 'check_tool_installed':
          return `Checking if ${params.tool_name} is installed`
        
        default:
          // For unknown tools, show params in a readable way
          return Object.entries(params)
            .map(([key, value]) => `${key}: ${value}`)
            .join(', ') || 'No parameters'
      }
    } catch (error) {
      return JSON.stringify(params)
    }
  }

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
          const action = formatToolAction(tool.name, tool.input)
          addActionLog(tool.name, action, 'success')
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
        await new Promise(resolve => setTimeout(resolve, 5)) // 5ms per character (faster)
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
      {/* SIDEBAR - Conversation History */}
      <div 
        className={`fixed inset-y-0 left-0 z-50 w-64 bg-zinc-900 border-r border-zinc-800 transform transition-transform duration-300 ${
          showSidebar ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Sidebar Header */}
        <div className="flex items-center justify-between p-4 border-b border-zinc-800">
          <h2 className="text-sm font-semibold text-white">Chat History</h2>
          <button
            onClick={() => setShowSidebar(false)}
            className="p-1 hover:bg-zinc-800 rounded"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* New Chat Button */}
        <div className="p-4 border-b border-zinc-800">
          <button
            onClick={createNewChat}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium transition-colors"
          >
            <PlusIcon className="w-4 h-4" />
            <span>New Chat</span>
          </button>
        </div>

        {/* Conversations List */}
        <div className="flex-1 overflow-y-auto p-2">
          {loadingConversations ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
            </div>
          ) : conversations.length === 0 ? (
            <div className="text-center py-8 text-zinc-500 text-sm">
              No conversations yet
            </div>
          ) : (
            conversations.map((conv) => (
              <button
                key={conv.conversation_id}
                onClick={() => loadConversation(conv.conversation_id)}
                className={`w-full text-left p-3 rounded-lg mb-2 hover:bg-zinc-800 transition-colors group ${
                  conv.conversation_id === conversationId ? 'bg-zinc-800 ring-1 ring-blue-600' : ''
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <ChatBubbleLeftIcon className="w-4 h-4 text-zinc-400 flex-shrink-0" />
                      <p className="text-sm font-medium text-white truncate">
                        {conv.title}
                      </p>
                    </div>
                    <p className="text-xs text-zinc-500">
                      {conv.message_count} messages • {new Date(conv.last_updated).toLocaleDateString()}
                    </p>
                  </div>
                  <button
                    onClick={(e) => deleteConversation(conv.conversation_id, e)}
                    className="opacity-0 group-hover:opacity-100 p-1 hover:bg-zinc-700 rounded transition-opacity"
                  >
                    <TrashIcon className="w-4 h-4 text-red-400" />
                  </button>
                </div>
              </button>
            ))
          )}
        </div>

        {/* Sidebar Footer */}
        <div className="p-4 border-t border-zinc-800">
          <div className="text-xs text-zinc-500 text-center">
            {conversations.length} conversation{conversations.length !== 1 ? 's' : ''}
          </div>
        </div>
      </div>

      {/* Overlay */}
      {showSidebar && (
        <div
          className="fixed inset-0 bg-black/50 z-40"
          onClick={() => setShowSidebar(false)}
        />
      )}

      {/* LEFT PANEL - Chat Interface */}
      <div 
        className={`flex flex-col border-r border-zinc-800 ${!isResizing ? 'transition-all duration-300' : ''}`}
        style={{ width: showActionsPanel ? `${100 - panelWidth}%` : '100%' }}
      >
        {/* Header */}
        <div className="flex-shrink-0 px-6 py-4 border-b border-zinc-800 bg-black/40 backdrop-blur-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button
                onClick={() => setShowSidebar(true)}
                className="p-2 hover:bg-zinc-800 rounded-lg transition-colors"
                title="Chat History"
              >
                <Bars3Icon className="w-5 h-5 text-zinc-400" />
              </button>
              <div>
                <h1 className="text-lg font-semibold text-white">ATLAS Agent</h1>
                <p className="text-xs text-zinc-400">Autonomous DevOps Assistant</p>
              </div>
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
                  <div className="prose prose-invert max-w-none
                    prose-p:text-zinc-200 prose-p:leading-7 prose-p:my-3
                    prose-headings:text-zinc-100 prose-headings:font-semibold prose-headings:mb-3 prose-headings:mt-5
                    prose-h1:text-2xl prose-h2:text-xl prose-h3:text-lg
                    prose-a:text-blue-400 prose-a:no-underline hover:prose-a:underline
                    prose-strong:text-zinc-100 prose-strong:font-bold
                    prose-em:text-zinc-300 prose-em:italic
                    prose-ul:my-3 prose-ul:list-disc prose-ul:pl-6 prose-ul:space-y-2
                    prose-ol:my-3 prose-ol:list-decimal prose-ol:pl-6 prose-ol:space-y-2
                    prose-li:text-zinc-200 prose-li:leading-7
                    prose-blockquote:border-l-4 prose-blockquote:border-zinc-600 prose-blockquote:pl-4 prose-blockquote:italic prose-blockquote:text-zinc-300
                    prose-table:my-4 prose-table:border-collapse
                    prose-th:border prose-th:border-zinc-700 prose-th:bg-zinc-800 prose-th:px-4 prose-th:py-2 prose-th:text-left
                    prose-td:border prose-td:border-zinc-700 prose-td:px-4 prose-td:py-2
                    prose-hr:border-zinc-700 prose-hr:my-6
                  ">
                    <ReactMarkdown
                      components={{
                        code({ inline, className, children, ...props }: any) {
                          const match = /language-(\w+)/.exec(className || '')
                          return !inline && match ? (
                            <SyntaxHighlighter
                              style={vscDarkPlus as any}
                              language={match[1]}
                              PreTag="div"
                              className="!my-4 !rounded-lg !text-sm"
                              customStyle={{
                                padding: '1rem',
                                borderRadius: '0.5rem',
                                fontSize: '0.875rem'
                              }}
                              {...props}
                            >
                              {String(children).replace(/\n$/, '')}
                            </SyntaxHighlighter>
                          ) : (
                            <code className="bg-zinc-800/90 px-1.5 py-0.5 rounded text-blue-400 font-mono text-sm" {...props}>
                              {children}
                            </code>
                          )
                        },
                        p({ children }: any) {
                          return <p className="mb-3 last:mb-0">{children}</p>
                        },
                        ul({ children }: any) {
                          return <ul className="space-y-1.5 my-3">{children}</ul>
                        },
                        ol({ children }: any) {
                          return <ol className="space-y-1.5 my-3">{children}</ol>
                        },
                        li({ children }: any) {
                          return <li className="ml-4">{children}</li>
                        },
                        a({ href, children }: any) {
                          return (
                            <a 
                              href={href} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="text-blue-400 hover:text-blue-300 underline"
                            >
                              {children}
                            </a>
                          )
                        },
                        blockquote({ children }: any) {
                          return (
                            <blockquote className="border-l-4 border-zinc-600 pl-4 my-4 italic text-zinc-400">
                              {children}
                            </blockquote>
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
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                // Shift+Enter = new line, Enter = submit
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  sendMessage(e)
                }
              }}
              placeholder="Describe your task... (Shift+Enter for new line)"
              className="flex-1 px-4 py-3 bg-zinc-900 border border-zinc-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-600 text-sm placeholder:text-zinc-500 resize-none min-h-[48px] max-h-[200px] overflow-y-auto"
              disabled={loading}
              rows={1}
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
        className={`flex flex-col bg-zinc-950 ${!isResizing ? 'transition-all duration-300' : ''} ${
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
