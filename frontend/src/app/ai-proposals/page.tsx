'use client';

import { useState, useEffect } from 'react';
import { Brain, FileText, Clock, CheckCircle, AlertTriangle, Eye, Download, RefreshCw } from 'lucide-react';

interface AIProposal {
  id: string;
  clientId: string;
  clientName: string;
  type: 'will' | 'trust' | 'succession' | 'asset_transfer';
  status: 'generating' | 'completed' | 'reviewed' | 'approved';
  confidence: number;
  createdAt: string;
  lastUpdated: string;
  suggestion: string;
  legalReferences: string[];
  consequences: string[];
  nextSteps: string[];
}

export default function AIProposalsPage() {
  const [proposals, setProposals] = useState<AIProposal[]>([]);
  const [selectedProposal, setSelectedProposal] = useState<AIProposal | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchProposals = async () => {
      try {
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        const mockProposals: AIProposal[] = [
          {
            id: 'proposal_001',
            clientId: 'client_58a83757',
            clientName: 'Test Client E2E',
            type: 'will',
            status: 'completed',
            confidence: 92,
            createdAt: '2025-08-25T13:40:00.000Z',
            lastUpdated: '2025-08-25T13:40:00.000Z',
            suggestion: 'Based on the client\'s profile as a single individual with significant real estate assets, I recommend creating a comprehensive will with specific provisions for property succession under Kenyan law.',
            legalReferences: [
              'Law of Succession Act (Cap 160) - Section 5: Requirements for Valid Will',
              'Law of Succession Act - Section 32: Intestate Succession Rules',
              'Income Tax Act (Cap 470) - Section 3(2)(a): Inheritance Tax Exemption'
            ],
            consequences: [
              'Clear succession pathway for real estate assets',
              'Reduced family disputes over inheritance',
              'Tax optimization for beneficiaries'
            ],
            nextSteps: [
              'Draft formal will document',
              'Arrange proper witnessing with two independent witnesses',
              'Register will with relevant authorities'
            ]
          },
          {
            id: 'proposal_002',
            clientId: 'client_sample_001',
            clientName: 'Jane Smith',
            type: 'trust',
            status: 'generating',
            confidence: 0,
            createdAt: '2025-08-25T14:00:00.000Z',
            lastUpdated: '2025-08-25T14:00:00.000Z',
            suggestion: '',
            legalReferences: [],
            consequences: [],
            nextSteps: []
          }
        ];
        
        setProposals(mockProposals);
      } catch (error) {
        console.error('Failed to fetch AI proposals:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchProposals();
  }, []);

  const getStatusBadge = (status: string) => {
    const configs = {
      generating: { color: 'bg-yellow-100 text-yellow-800', icon: RefreshCw },
      completed: { color: 'bg-green-100 text-green-800', icon: CheckCircle },
      reviewed: { color: 'bg-blue-100 text-blue-800', icon: Eye },
      approved: { color: 'bg-purple-100 text-purple-800', icon: CheckCircle }
    };
    return configs[status as keyof typeof configs] || configs.generating;
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'will': return FileText;
      case 'trust': return Brain;
      default: return FileText;
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 90) return 'text-green-600';
    if (confidence >= 70) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">AI Legal Proposals</h1>
        <p className="text-gray-600">
          AI-generated legal recommendations based on client questionnaires and Kenyan law
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Proposals List */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Generated Proposals</h2>
            <button className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 flex items-center gap-2">
              <Brain className="h-4 w-4" />
              Generate New
            </button>
          </div>

          {isLoading ? (
            <div className="bg-white rounded-lg shadow p-6">
              <div className="animate-pulse space-y-4">
                <div className="h-4 bg-gray-300 rounded w-3/4"></div>
                <div className="h-4 bg-gray-300 rounded w-1/2"></div>
                <div className="h-4 bg-gray-300 rounded w-5/6"></div>
              </div>
            </div>
          ) : (
            proposals.map((proposal) => {
              const statusConfig = getStatusBadge(proposal.status);
              const TypeIcon = getTypeIcon(proposal.type);
              const StatusIcon = statusConfig.icon;

              return (
                <div
                  key={proposal.id}
                  className={`bg-white rounded-lg shadow p-6 cursor-pointer border-2 transition-colors ${
                    selectedProposal?.id === proposal.id ? 'border-indigo-500' : 'border-transparent hover:border-gray-300'
                  }`}
                  onClick={() => setSelectedProposal(proposal)}
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <div className="p-2 bg-indigo-100 rounded-lg">
                        <TypeIcon className="h-5 w-5 text-indigo-600" />
                      </div>
                      <div>
                        <h3 className="text-lg font-medium text-gray-900">
                          {proposal.clientName}
                        </h3>
                        <p className="text-sm text-gray-500">
                          {proposal.type.charAt(0).toUpperCase() + proposal.type.slice(1)} Planning
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex flex-col items-end space-y-2">
                      <span className={`inline-flex items-center px-2 py-1 text-xs font-medium rounded-full ${statusConfig.color}`}>
                        <StatusIcon className="h-3 w-3 mr-1" />
                        {proposal.status}
                      </span>
                      {proposal.confidence > 0 && (
                        <span className={`text-sm font-medium ${getConfidenceColor(proposal.confidence)}`}>
                          {proposal.confidence}% confidence
                        </span>
                      )}
                    </div>
                  </div>

                  {proposal.status === 'generating' ? (
                    <div className="flex items-center text-sm text-gray-500">
                      <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                      Analyzing client data and generating recommendations...
                    </div>
                  ) : (
                    <p className="text-sm text-gray-600 line-clamp-3">
                      {proposal.suggestion}
                    </p>
                  )}

                  <div className="mt-4 flex items-center justify-between text-xs text-gray-400">
                    <span>Created {new Date(proposal.createdAt).toLocaleDateString()}</span>
                    <span>ID: {proposal.id}</span>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Proposal Details */}
        <div className="bg-white rounded-lg shadow">
          {selectedProposal ? (
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold text-gray-900">Proposal Details</h3>
                <div className="flex space-x-2">
                  <button className="p-2 text-gray-400 hover:text-gray-600">
                    <Eye className="h-4 w-4" />
                  </button>
                  <button className="p-2 text-gray-400 hover:text-gray-600">
                    <Download className="h-4 w-4" />
                  </button>
                </div>
              </div>

              {selectedProposal.status === 'generating' ? (
                <div className="text-center py-12">
                  <RefreshCw className="h-8 w-8 mx-auto text-indigo-600 animate-spin mb-4" />
                  <p className="text-gray-600">Generating AI proposal...</p>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Recommendation */}
                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">AI Recommendation</h4>
                    <p className="text-gray-700 bg-gray-50 p-4 rounded-lg">
                      {selectedProposal.suggestion}
                    </p>
                  </div>

                  {/* Legal References */}
                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">Legal References</h4>
                    <ul className="space-y-2">
                      {selectedProposal.legalReferences.map((ref, index) => (
                        <li key={index} className="text-sm text-gray-600 flex items-start">
                          <span className="text-indigo-600 mr-2">•</span>
                          {ref}
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Consequences */}
                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">Potential Consequences</h4>
                    <ul className="space-y-2">
                      {selectedProposal.consequences.map((consequence, index) => (
                        <li key={index} className="text-sm text-gray-600 flex items-start">
                          <CheckCircle className="h-4 w-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                          {consequence}
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Next Steps */}
                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">Recommended Next Steps</h4>
                    <ol className="space-y-2">
                      {selectedProposal.nextSteps.map((step, index) => (
                        <li key={index} className="text-sm text-gray-600 flex items-start">
                          <span className="bg-indigo-100 text-indigo-600 rounded-full w-5 h-5 flex items-center justify-center text-xs font-medium mr-3 mt-0.5 flex-shrink-0">
                            {index + 1}
                          </span>
                          {step}
                        </li>
                      ))}
                    </ol>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="p-12 text-center text-gray-500">
              <Brain className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p>Select a proposal to view details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}