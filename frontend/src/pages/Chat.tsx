import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, FileText, Clock } from 'lucide-react';
import { Receipt } from '../types/receipt';
import { API_URL } from '../services/api';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  sourceReceipts?: Receipt[];
}

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(() => `session_${Date.now()}`);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');

    // Add user message to chat
    const newUserMessage: ChatMessage = {
      role: 'user',
      content: userMessage,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, newUserMessage]);
    setIsLoading(true);

    try {
      const response = await fetch(`${API_URL}/api/chat/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: userMessage,
          session_id: sessionId,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to get response');
      }

      const data = await response.json();

      const botMessage: ChatMessage = {
        role: 'assistant',
        content: data.response,
        timestamp: new Date().toISOString(),
        sourceReceipts: data.source_receipts || [],
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Error sending message:', error);

      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request. Please make sure the backend is running and try again.',
        timestamp: new Date().toISOString(),
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const exampleQuestions = [
    "How much did I receive last month?",
    "Show me all receipts above 10,000 THB",
    "What was my total spending in March 2026?",
    "Who sent me money recently?",
  ];

  const handleExampleQuestion = (question: string) => {
    setInput(question);
  };

  return (
    <div className="max-w-5xl mx-auto">
      <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-4 sm:mb-6">AI Chatbot</h1>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden flex flex-col h-[calc(100vh-180px)] sm:h-[600px]">
        {/* Chat Messages */}
        <div className="flex-1 overflow-y-auto p-3 sm:p-6 space-y-3 sm:space-y-4">
          {messages.length === 0 && (
            <div className="text-center py-8 sm:py-12 px-2">
              <Bot className="mx-auto h-10 w-10 sm:h-12 sm:w-12 text-blue-600 mb-3 sm:mb-4" />
              <h2 className="text-lg sm:text-xl font-semibold text-gray-900 mb-2">
                Welcome to OCR Bank AI Assistant
              </h2>
              <p className="text-xs sm:text-sm text-gray-600 mb-4 sm:mb-6">
                Ask me anything about your receipts! I can help you find information,
                calculate totals, and analyze your spending patterns.
              </p>

              <div className="max-w-2xl mx-auto">
                <h3 className="text-xs sm:text-sm font-medium text-gray-700 mb-2 sm:mb-3">
                  Example questions:
                </h3>
                <div className="grid grid-cols-1 gap-2 sm:gap-3">
                  {exampleQuestions.map((question, index) => (
                    <button
                      key={index}
                      onClick={() => handleExampleQuestion(question)}
                      className="text-left px-3 sm:px-4 py-2 sm:py-3 bg-gray-50 hover:bg-gray-100 rounded-lg text-xs sm:text-sm text-gray-700 transition-colors"
                    >
                      {question}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`flex max-w-[85%] sm:max-w-[80%] ${
                  message.role === 'user' ? 'flex-row-reverse' : 'flex-row'
                } gap-2 sm:gap-3`}
              >
                <div
                  className={`flex-shrink-0 w-7 h-7 sm:w-8 sm:h-8 rounded-full flex items-center justify-center ${
                    message.role === 'user'
                      ? 'bg-blue-600'
                      : 'bg-green-600'
                  }`}
                >
                  {message.role === 'user' ? (
                    <User size={14} className="text-white" />
                  ) : (
                    <Bot size={14} className="text-white sm:hidden" />
                  )}
                  {message.role !== 'user' && (
                    <Bot size={18} className="text-white hidden sm:block" />
                  )}
                </div>

                <div
                  className={`rounded-lg px-3 py-2 sm:px-4 sm:py-2 ${
                    message.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-900'
                  }`}
                >
                  <p className="text-xs sm:text-sm whitespace-pre-wrap break-words">{message.content}</p>

                  {message.sourceReceipts && message.sourceReceipts.length > 0 && (
                    <div className="mt-2 sm:mt-3 pt-2 sm:pt-3 border-t border-gray-200">
                      <p className="text-[10px] sm:text-xs font-medium text-gray-600 mb-1 sm:mb-2">
                        Source Receipts:
                      </p>
                      <div className="space-y-1 sm:space-y-2">
                        {message.sourceReceipts.map((receipt) => (
                          <div
                            key={receipt.id}
                            className="text-[10px] sm:text-xs bg-white rounded p-2 border border-gray-200"
                          >
                            <div className="flex items-center gap-1 sm:gap-2 mb-1">
                              <FileText size={10} className="text-gray-400" />
                              <span className="font-medium text-gray-700 truncate">
                                {receipt.sender || 'Unknown'} → {receipt.receiver || 'Unknown'}
                              </span>
                            </div>
                            <div className="text-gray-600">
                              {receipt.extracted_date && (
                                <span>{new Date(receipt.extracted_date).toLocaleDateString()}</span>
                              )}
                              {receipt.amount && (
                                <span className="ml-1 sm:ml-2 font-semibold text-green-600">
                                  ฿{typeof receipt.amount === 'number' ? receipt.amount.toFixed(2) : receipt.amount}
                                </span>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                <div className="flex items-center gap-1 hidden sm:flex">
                  <Clock size={12} className="text-gray-400" />
                  <span className="text-xs text-gray-500">
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </span>
                </div>
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="flex gap-2 sm:gap-3">
                <div className="flex-shrink-0 w-7 h-7 sm:w-8 sm:h-8 rounded-full flex items-center justify-center bg-green-600">
                  <Bot size={14} className="text-white sm:hidden" />
                  <Bot size={18} className="text-white hidden sm:block" />
                </div>
                <div className="bg-gray-100 rounded-lg px-3 py-2 sm:px-4 sm:py-2">
                  <div className="flex space-x-1 sm:space-x-2">
                    <div className="w-1.5 h-1.5 sm:w-2 sm:h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-1.5 h-1.5 sm:w-2 sm:h-2 bg-gray-400 rounded-full animate-bounce delay-100"></div>
                    <div className="w-1.5 h-1.5 sm:w-2 sm:h-2 bg-gray-400 rounded-full animate-bounce delay-200"></div>
                  </div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Form */}
        <form onSubmit={handleSubmit} className="border-t border-gray-200 p-3 sm:p-4">
          <div className="flex gap-2 sm:gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask me anything about your receipts..."
              className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="px-3 sm:px-4 sm:px-6 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-1 sm:gap-2"
            >
              <Send size={14} />
              <span className="hidden sm:inline">Send</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
