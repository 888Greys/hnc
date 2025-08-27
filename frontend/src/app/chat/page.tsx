'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import api from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Send, Bot, User, Loader2, AlertCircle } from 'lucide-react';

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'ai';
  timestamp: Date;
  isLoading?: boolean;
  error?: string;
}

interface ChatResponse {
  response: string;
  isRealAI: boolean;
  debugInfo?: {
    apiKeyAvailable: boolean;
    cerebrasAvailable: boolean;
    model: string;
  };
}

export default function ChatPage() {
  const { user } = useAuth();
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: 'Hello! I\'m your legal AI assistant specializing in Kenyan law. I can help you with questions about estate planning, succession law, wills, trusts, and other legal matters. How can I assist you today?',
      sender: 'ai',
      timestamp: new Date()
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [aiStatus, setAiStatus] = useState<'unknown' | 'real' | 'mock'>('unknown');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputMessage.trim(),
      sender: 'user',
      timestamp: new Date()
    };

    const loadingMessage: Message = {
      id: (Date.now() + 1).toString(),
      content: '',
      sender: 'ai',
      timestamp: new Date(),
      isLoading: true
    };

    setMessages(prev => [...prev, userMessage, loadingMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      console.log('=== Chat Debug Info ===');
      console.log('Auth debug:', api.getAuthDebugInfo());
      console.log('Is authenticated:', api.isAuthenticated());
      console.log('Sending message:', inputMessage.trim());
      
      const response = await api.sendChatMessage(
        inputMessage.trim(),
        'legal_consultation'
      );

      // Update AI status based on response
      setAiStatus(response.isRealAI ? 'real' : 'mock');

      // Replace loading message with actual response
      setMessages(prev => 
        prev.map(msg => 
          msg.id === loadingMessage.id 
            ? {
                ...msg,
                content: response.response,
                isLoading: false
              }
            : msg
        )
      );

    } catch (error: any) {
      console.error('Chat error:', error);
      
      // Replace loading message with error
      setMessages(prev => 
        prev.map(msg => 
          msg.id === loadingMessage.id 
            ? {
                ...msg,
                content: 'I apologize, but I encountered an error while processing your message. Please try again.',
                isLoading: false,
                error: error.message || 'Unknown error'
              }
            : msg
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const getStatusBadge = () => {
    switch (aiStatus) {
      case 'real':
        return <Badge variant="default" className="bg-green-100 text-green-800 border-green-300">Real AI</Badge>;
      case 'mock':
        return <Badge variant="destructive" className="bg-yellow-100 text-yellow-800 border-yellow-300">Mock AI</Badge>;
      default:
        return <Badge variant="secondary">Status Unknown</Badge>;
    }
  };

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="w-96">
          <CardContent className="pt-6">
            <p className="text-center text-gray-600">Please log in to access the AI chat.</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-4xl mx-auto">
        <Card className="h-[80vh] flex flex-col">
          <CardHeader className="flex-shrink-0 border-b">
            <div className="flex justify-between items-center">
              <CardTitle className="flex items-center gap-2">
                <Bot className="h-6 w-6 text-blue-600" />
                Legal AI Assistant
              </CardTitle>
              {getStatusBadge()}
            </div>
            <p className="text-sm text-gray-600">
              Chat with our AI assistant for legal guidance on Kenyan law
            </p>
          </CardHeader>
          
          <CardContent className="flex-1 flex flex-col p-0">
            <ScrollArea className="flex-1 p-4">
              <div className="space-y-4">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[80%] rounded-lg p-3 ${
                        message.sender === 'user'
                          ? 'bg-blue-600 text-white'
                          : message.error
                          ? 'bg-red-50 border border-red-200'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      <div className="flex items-start gap-2">
                        {message.sender === 'ai' && (
                          <div className={`flex-shrink-0 ${message.isLoading ? 'animate-pulse' : ''}`}>
                            {message.error ? (
                              <AlertCircle className="h-4 w-4 text-red-500 mt-0.5" />
                            ) : (
                              <Bot className={`h-4 w-4 mt-0.5 ${message.isLoading ? 'text-gray-400' : 'text-blue-600'}`} />
                            )}
                          </div>
                        )}
                        {message.sender === 'user' && (
                          <User className="h-4 w-4 flex-shrink-0 mt-0.5" />
                        )}
                        <div className="flex-1">
                          {message.isLoading ? (
                            <div className="flex items-center gap-2">
                              <Loader2 className="h-4 w-4 animate-spin" />
                              <span className="text-sm text-gray-500">AI is thinking...</span>
                            </div>
                          ) : (
                            <div className="whitespace-pre-wrap">{message.content}</div>
                          )}
                          <div className={`text-xs mt-1 ${
                            message.sender === 'user' ? 'text-blue-200' : 'text-gray-500'
                          }`}>
                            {message.timestamp.toLocaleTimeString()}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>
            </ScrollArea>
            
            <div className="border-t p-4">
              <div className="flex gap-2">
                <Input
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask me about Kenyan law, estate planning, wills, trusts..."
                  disabled={isLoading}
                  className="flex-1"
                />
                <Button 
                  onClick={sendMessage} 
                  disabled={isLoading || !inputMessage.trim()}
                  size="icon"
                >
                  {isLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                </Button>
              </div>
              <p className="text-xs text-gray-500 mt-2">
                Press Enter to send • This AI provides informational guidance only, not formal legal advice
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}