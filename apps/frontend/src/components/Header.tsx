interface HeaderProps {
  mode?: 'chat' | 'agent'
  setMode?: (mode: 'chat' | 'agent') => void
}

export default function Header({ mode = 'agent', setMode }: HeaderProps) {
  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4 shadow-sm">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-xl">🤖</span>
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900">DevOps Agent</h1>
            <p className="text-xs text-gray-500">Powered by Claude AI</p>
          </div>
        </div>
        
        <div className="flex items-center space-x-4">
          {setMode && (
            <div className="flex items-center space-x-2 bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setMode('agent')}
                className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                  mode === 'agent'
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                🔧 Agent Mode
              </button>
              <button
                onClick={() => setMode('chat')}
                className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                  mode === 'chat'
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                💬 Chat Only
              </button>
            </div>
          )}
          <div className="flex items-center space-x-2 text-sm">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-gray-600">Online</span>
          </div>
        </div>
      </div>
    </header>
  )
}
