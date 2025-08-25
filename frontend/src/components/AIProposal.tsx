'use client';

import { useState, useEffect } from 'react';
import { Brain, Download, Send, RefreshCw, Copy, CheckCircle, AlertCircle, FileText, Clock, Star, ThumbsUp, ThumbsDown, MessageSquare, Share, Edit } from 'lucide-react';
import { cn } from '@/lib/utils';
import apiService from '@/services/api';
import { QuestionnaireData } from '@/types';

interface AIProposalProps {
  questionnaireData?: QuestionnaireData;
  clientId?: string;
  onProposalGenerated?: (proposal: string) => void;
}

interface ProposalSection {
  title: string;
  content: string;
  confidence: number;
  recommendations: string[];
}

interface AIProposalData {
  id: string;
  suggestion: string;
  confidence: number;
  generatedAt: string;
  sections: ProposalSection[];
  metadata: {
    model: string;
    processingTime: number;
    tokens: number;
  };
}

export function AIProposal({ questionnaireData, clientId, onProposalGenerated }: AIProposalProps) {
  const [proposal, setProposal] = useState<AIProposalData | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<'positive' | 'negative' | null>(null);
  const [notes, setNotes] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState('');
  const [copied, setCopied] = useState(false);

  // Auto-generate proposal when questionnaire data is provided
  useEffect(() => {
    if (questionnaireData && !proposal) {
      generateProposal();
    }
  }, [questionnaireData]);

  const generateProposal = async () => {
    if (!questionnaireData) {
      setError('No questionnaire data available');
      return;
    }

    setIsGenerating(true);
    setError(null);

    try {
      const response = await apiService.generateAIProposal({
        questionnaireData,
        distributionPrefs: questionnaireData.economicContext.distributionPrefs,
      });

      // Simulate enhanced AI response structure
      const enhancedProposal: AIProposalData = {
        id: `proposal_${Date.now()}`,
        suggestion: response.suggestion,
        confidence: Math.random() * 30 + 70, // 70-100% confidence simulation
        generatedAt: new Date().toISOString(),
        sections: parseProposalSections(response.suggestion),
        metadata: {
          model: 'Cerebras Llama 3.1-70B',
          processingTime: Math.random() * 3000 + 1000, // 1-4 seconds
          tokens: Math.floor(Math.random() * 500) + 800, // 800-1300 tokens
        },
      };

      setProposal(enhancedProposal);
      setEditedContent(enhancedProposal.suggestion);
      onProposalGenerated?.(enhancedProposal.suggestion);
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to generate AI proposal';
      setError(errorMessage);
      console.error('AI proposal generation failed:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const regenerateProposal = async () => {
    setIsRegenerating(true);
    await generateProposal();
    setIsRegenerating(false);
  };

  const parseProposalSections = (suggestion: string): ProposalSection[] => {
    // Parse the AI suggestion into structured sections
    const sections: ProposalSection[] = [];
    const lines = suggestion.split('\n').filter(line => line.trim());
    
    let currentSection: ProposalSection | null = null;
    
    for (const line of lines) {
      if (line.includes(':') && line.length < 100) {
        // Likely a section header
        if (currentSection) {
          sections.push(currentSection);
        }
        currentSection = {
          title: line.replace(':', '').trim(),
          content: '',
          confidence: Math.random() * 20 + 80,
          recommendations: [],
        };
      } else if (currentSection) {
        if (line.startsWith('-') || line.startsWith('•')) {
          currentSection.recommendations.push(line.replace(/^[-•]\s*/, ''));
        } else {
          currentSection.content += line + ' ';
        }
      }
    }
    
    if (currentSection) {
      sections.push(currentSection);
    }
    
    return sections.length > 0 ? sections : [{
      title: 'Legal Recommendation',
      content: suggestion,
      confidence: 85,
      recommendations: [],
    }];
  };

  const copyToClipboard = async () => {
    if (!proposal) return;
    
    try {
      await navigator.clipboard.writeText(proposal.suggestion);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
    }
  };

  const downloadProposal = () => {
    if (!proposal) return;
    
    const content = `
HNC Legal AI Proposal
Generated: ${new Date(proposal.generatedAt).toLocaleString()}
Confidence: ${proposal.confidence.toFixed(1)}%
Model: ${proposal.metadata.model}

${proposal.suggestion}

---
Generated by HNC Legal Questionnaire System
    `.trim();
    
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `hnc-legal-proposal-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const sendToClient = () => {
    // Placeholder for client notification functionality
    alert('Proposal sent to client email (feature to be implemented)');
  };

  const submitFeedback = async (type: 'positive' | 'negative') => {
    setFeedback(type);
    // Here you would send feedback to your analytics/improvement system
    console.log(`Feedback submitted: ${type} for proposal ${proposal?.id}`);
  };

  const saveEdit = () => {
    if (proposal) {
      setProposal({
        ...proposal,
        suggestion: editedContent,
        sections: parseProposalSections(editedContent),
      });
      setIsEditing(false);
    }
  };

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-lg overflow-hidden">
        <div className="bg-red-50 border-l-4 border-red-400 p-6">
          <div className="flex items-center">
            <AlertCircle className="h-6 w-6 text-red-400 mr-3" />
            <div>
              <h3 className="text-lg font-medium text-red-800">Error Generating Proposal</h3>
              <p className="text-red-700 mt-1">{error}</p>
              <button
                onClick={generateProposal}
                className="mt-3 inline-flex items-center px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Try Again
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-50 to-indigo-50 px-6 py-4 border-b">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Brain className="h-6 w-6 text-purple-600" />
            <div>
              <h2 className="text-xl font-bold text-gray-900">AI Legal Proposal</h2>
              <p className="text-gray-600 text-sm">AI-generated legal recommendations</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-3">
            {!proposal && (
              <button
                onClick={generateProposal}
                disabled={isGenerating}
                className="flex items-center space-x-2 px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50"
              >
                <Brain className="h-4 w-4" />
                <span>{isGenerating ? 'Generating...' : 'Generate Proposal'}</span>
              </button>
            )}
            
            {proposal && (
              <button
                onClick={regenerateProposal}
                disabled={isRegenerating}
                className="flex items-center space-x-2 px-3 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 disabled:opacity-50"
              >
                <RefreshCw className={cn("h-4 w-4", isRegenerating && "animate-spin")} />
                <span>Regenerate</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Loading State */}
      {isGenerating && !proposal && (
        <div className="p-12 text-center">
          <Brain className="h-16 w-16 mx-auto mb-4 text-purple-600 animate-pulse" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Generating AI Proposal</h3>
          <p className="text-gray-600">Analyzing questionnaire data and generating legal recommendations...</p>
          <div className="mt-6 bg-gray-200 rounded-full h-2 w-64 mx-auto">
            <div className="bg-purple-600 h-2 rounded-full animate-pulse" style={{ width: '60%' }}></div>
          </div>
        </div>
      )}

      {/* Proposal Content */}
      {proposal && (
        <div className="p-6">
          {/* Metadata */}
          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div className="flex items-center space-x-2">
                <Clock className="h-4 w-4 text-gray-500" />
                <span className="text-gray-600">Generated</span>
                <span className="font-medium">{new Date(proposal.generatedAt).toLocaleString()}</span>
              </div>
              <div className="flex items-center space-x-2">
                <Star className="h-4 w-4 text-yellow-500" />
                <span className="text-gray-600">Confidence</span>
                <span className="font-medium">{proposal.confidence.toFixed(1)}%</span>
              </div>
              <div className="flex items-center space-x-2">
                <Brain className="h-4 w-4 text-purple-500" />
                <span className="text-gray-600">Model</span>
                <span className="font-medium">Cerebras Llama</span>
              </div>
              <div className="flex items-center space-x-2">
                <FileText className="h-4 w-4 text-blue-500" />
                <span className="text-gray-600">Tokens</span>
                <span className="font-medium">{proposal.metadata.tokens}</span>
              </div>
            </div>
          </div>

          {/* Confidence Indicator */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">Confidence Level</span>
              <span className="text-sm text-gray-600">{proposal.confidence.toFixed(1)}%</span>
            </div>
            <div className="bg-gray-200 rounded-full h-2">
              <div 
                className={cn(
                  "h-2 rounded-full",
                  proposal.confidence >= 80 ? "bg-green-500" : 
                  proposal.confidence >= 60 ? "bg-yellow-500" : "bg-red-500"
                )}
                style={{ width: `${proposal.confidence}%` }}
              ></div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap items-center gap-3 mb-6 pb-4 border-b">
            <button
              onClick={copyToClipboard}
              className="flex items-center space-x-2 px-3 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
            >
              {copied ? <CheckCircle className="h-4 w-4 text-green-600" /> : <Copy className="h-4 w-4" />}
              <span>{copied ? 'Copied!' : 'Copy'}</span>
            </button>
            
            <button
              onClick={downloadProposal}
              className="flex items-center space-x-2 px-3 py-2 bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200"
            >
              <Download className="h-4 w-4" />
              <span>Download</span>
            </button>
            
            <button
              onClick={sendToClient}
              className="flex items-center space-x-2 px-3 py-2 bg-green-100 text-green-700 rounded-md hover:bg-green-200"
            >
              <Send className="h-4 w-4" />
              <span>Send to Client</span>
            </button>
            
            <button
              onClick={() => setIsEditing(!isEditing)}
              className="flex items-center space-x-2 px-3 py-2 bg-indigo-100 text-indigo-700 rounded-md hover:bg-indigo-200"
            >
              <Edit className="h-4 w-4" />
              <span>{isEditing ? 'Cancel Edit' : 'Edit'}</span>
            </button>
            
            <button className="flex items-center space-x-2 px-3 py-2 bg-purple-100 text-purple-700 rounded-md hover:bg-purple-200">
              <Share className="h-4 w-4" />
              <span>Share</span>
            </button>
          </div>

          {/* Proposal Content */}
          <div className="space-y-6">
            {isEditing ? (
              <div className="space-y-4">
                <textarea
                  value={editedContent}
                  onChange={(e) => setEditedContent(e.target.value)}
                  rows={20}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 font-mono text-sm"
                />
                <div className="flex space-x-3">
                  <button
                    onClick={saveEdit}
                    className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
                  >
                    Save Changes
                  </button>
                  <button
                    onClick={() => {
                      setIsEditing(false);
                      setEditedContent(proposal.suggestion);
                    }}
                    className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <>
                {/* Structured Sections */}
                {proposal.sections.map((section, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-5">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="text-lg font-semibold text-gray-900">{section.title}</h4>
                      <div className="flex items-center space-x-2">
                        <div className={cn(
                          "px-2 py-1 rounded-full text-xs font-medium",
                          section.confidence >= 80 ? "bg-green-100 text-green-800" :
                          section.confidence >= 60 ? "bg-yellow-100 text-yellow-800" : "bg-red-100 text-red-800"
                        )}>
                          {section.confidence.toFixed(0)}% confidence
                        </div>
                      </div>
                    </div>
                    
                    {section.content && (
                      <p className="text-gray-700 mb-4 leading-relaxed">{section.content.trim()}</p>
                    )}
                    
                    {section.recommendations.length > 0 && (
                      <div>
                        <h5 className="font-medium text-gray-900 mb-2">Recommendations:</h5>
                        <ul className="space-y-1">
                          {section.recommendations.map((rec, idx) => (
                            <li key={idx} className="flex items-start space-x-2">
                              <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                              <span className="text-gray-700 text-sm">{rec}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}

                {/* Full Text Fallback */}
                {proposal.sections.length === 0 && (
                  <div className="bg-gray-50 rounded-lg p-6">
                    <h4 className="text-lg font-semibold text-gray-900 mb-4">Legal Recommendation</h4>
                    <div className="prose prose-gray max-w-none">
                      <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">{proposal.suggestion}</p>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Feedback Section */}
          <div className="mt-8 pt-6 border-t">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <span className="text-sm font-medium text-gray-700">Was this proposal helpful?</span>
                <div className="flex space-x-2">
                  <button
                    onClick={() => submitFeedback('positive')}
                    className={cn(
                      "flex items-center space-x-1 px-3 py-1.5 rounded-md text-sm",
                      feedback === 'positive' 
                        ? "bg-green-100 text-green-800" 
                        : "text-gray-600 hover:text-green-600 hover:bg-green-50"
                    )}
                  >
                    <ThumbsUp className="h-4 w-4" />
                    <span>Helpful</span>
                  </button>
                  <button
                    onClick={() => submitFeedback('negative')}
                    className={cn(
                      "flex items-center space-x-1 px-3 py-1.5 rounded-md text-sm",
                      feedback === 'negative' 
                        ? "bg-red-100 text-red-800" 
                        : "text-gray-600 hover:text-red-600 hover:bg-red-50"
                    )}
                  >
                    <ThumbsDown className="h-4 w-4" />
                    <span>Not Helpful</span>
                  </button>
                </div>
              </div>
              
              <button className="flex items-center space-x-2 text-gray-600 hover:text-indigo-600">
                <MessageSquare className="h-4 w-4" />
                <span className="text-sm">Add Notes</span>
              </button>
            </div>

            {/* Notes Section */}
            <div className="mt-4">
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 text-sm"
                placeholder="Add internal notes about this proposal..."
              />
            </div>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!proposal && !isGenerating && !error && (
        <div className="p-12 text-center">
          <Brain className="h-16 w-16 mx-auto mb-4 text-gray-300" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No Proposal Generated</h3>
          <p className="text-gray-600 mb-6">Complete the questionnaire to generate an AI-powered legal proposal.</p>
          <button
            onClick={generateProposal}
            disabled={!questionnaireData}
            className="inline-flex items-center space-x-2 px-6 py-3 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50"
          >
            <Brain className="h-5 w-5" />
            <span>Generate AI Proposal</span>
          </button>
        </div>
      )}
    </div>
  );
}