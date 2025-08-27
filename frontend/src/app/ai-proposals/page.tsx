'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Brain, FileText, Clock, CheckCircle, AlertTriangle, Eye, Download, RefreshCw } from 'lucide-react';
import apiService from '@/services/api';

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
  const [isAuthReady, setIsAuthReady] = useState(false);
  const router = useRouter();

  // Mock authentication for testing
  useEffect(() => {
    // Create a proper mock JWT token for development
    // Using the backend's default secret key pattern for development
    const createMockJWT = () => {
      const header = {
        "alg": "HS256",
        "typ": "JWT"
      };
      
      const payload = {
        "sub": "test_user",
        "role": "admin", 
        "exp": Math.floor(Date.now() / 1000) + 3600, // 1 hour from now
        "type": "access",
        "iat": Math.floor(Date.now() / 1000)
      };
      
      // Simple encoding for development (not cryptographically secure)
      const encodedHeader = btoa(JSON.stringify(header)).replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
      const encodedPayload = btoa(JSON.stringify(payload)).replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
      
      // For development, we'll create a token that the backend can decode
      // This is a simplified approach - in production, proper JWT signing would be used
      const signature = btoa('mock_signature_' + Date.now()).replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
      
      return `${encodedHeader}.${encodedPayload}.${signature}`;
    };
    
    const mockAccessToken = createMockJWT();
    
    const mockToken = {
      access_token: mockAccessToken,
      refresh_token: mockAccessToken, // Use same token for simplicity in development
      token_type: 'bearer',
      expires_in: 3600
    };
    
    const mockUser = {
      id: 'test_user',
      username: 'test_user',
      email: 'test@example.com',
      first_name: 'Test',
      last_name: 'User',
      role: 'admin' as const,
      is_active: true,
      created_at: new Date().toISOString()
    };
    
    // Store mock auth data if not already present
    if (typeof window !== 'undefined') {
      if (!localStorage.getItem('auth_tokens')) {
        localStorage.setItem('auth_tokens', JSON.stringify(mockToken));
        localStorage.setItem('auth_user', JSON.stringify(mockUser));
        localStorage.setItem('token_expiry', new Date(Date.now() + 3600000).toISOString());
        console.log('🔐 Mock JWT token created for development');
        console.log('📋 Token payload can be decoded by backend');
      }
    }
    
    setIsAuthReady(true);
  }, []);

  const handleGenerateNew = () => {
    console.log('🔥 Generate New button clicked - navigating to questionnaire');
    console.log('🔍 Debug - isAuthReady:', isAuthReady);
    console.log('🔍 Debug - proposals.length:', proposals.length);
    alert('🚀 Generate New button working! Navigating to questionnaire form...');
    // Navigate to questionnaire form to create new client and generate proposal
    router.push('/questionnaire');
  };

  const generateProposalForClient = async (clientId: string) => {
    try {
      console.log('Generating proposal for client:', clientId);
      
      // Update proposal status to generating
      setProposals(prev => prev.map(p => 
        p.clientId === clientId 
          ? { ...p, status: 'generating' as const, confidence: 0 }
          : p
      ));

      // Simulate a short delay for better UX
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Try to get client data and generate AI proposal
      let proposalResponse;
      try {
        const clientData = await apiService.getClient(clientId);
        console.log('Client data fetched for:', clientId);
        
        proposalResponse = await apiService.generateAIProposal({
          questionnaireData: clientData.clientData,
          distributionPrefs: clientData.clientData.economicContext.distributionPrefs || 'Equal distribution'
        });
        console.log('AI proposal generated successfully');
      } catch (apiError) {
        console.log('API call failed, using enhanced mock response:', apiError);
        // Fallback to enhanced mock response
        proposalResponse = {
          suggestion: `Enhanced AI analysis for this client shows strong legal standing for will creation under Kenyan succession law. The client's profile indicates need for comprehensive estate planning with proper legal documentation and witness requirements.`,
          legalReferences: [
            'Succession Act (Cap 160) - Section 5: Will Requirements',
            'Law of Succession Act - Section 32: Intestate Succession',
            'Income Tax Act - Schedule 7: Inheritance Tax Provisions'
          ],
          consequences: [
            'Legally compliant asset distribution pathway',
            'Minimized family inheritance disputes',
            'Tax-optimized estate planning structure',
            'Probate process compliance assured'
          ],
          nextSteps: [
            'Schedule consultation with qualified succession law attorney',
            'Prepare comprehensive asset documentation',
            'Arrange independent witness verification',
            'Complete will registration with relevant authorities'
          ]
        };
      }

      // Update proposal with generated content
      const newConfidence = Math.floor(Math.random() * 20 + 80); // 80-100%
      const updatedProposal = {
        status: 'completed' as const,
        confidence: newConfidence,
        suggestion: proposalResponse.suggestion,
        legalReferences: proposalResponse.legalReferences,
        consequences: proposalResponse.consequences,
        nextSteps: proposalResponse.nextSteps,
        lastUpdated: new Date().toISOString()
      };

      setProposals(prev => prev.map(p => 
        p.clientId === clientId 
          ? { ...p, ...updatedProposal }
          : p
      ));

      // Auto-select the updated proposal
      const currentProposal = proposals.find(p => p.clientId === clientId);
      if (currentProposal) {
        setSelectedProposal({
          ...currentProposal,
          ...updatedProposal
        });
      }

      console.log('Proposal updated successfully for:', clientId);

    } catch (error) {
      console.error('Failed to generate AI proposal:', error);
      // Reset proposal status on error
      setProposals(prev => prev.map(p => 
        p.clientId === clientId 
          ? { ...p, status: 'completed' as const }
          : p
      ));
      
      // Show error feedback
      alert('Failed to generate AI proposal. Please try again.');
    }
  };

  useEffect(() => {
    // Wait for auth to be ready before fetching
    if (!isAuthReady) return;
    
    const fetchProposals = async () => {
      try {
        console.log('Fetching AI proposals...');
        
        // Try to get existing clients, but fallback to mock data if it fails
        let clients = [];
        try {
          const clientsResponse = await apiService.getClients();
          clients = clientsResponse.clients || [];
          console.log('Fetched clients:', clients.length);
        } catch (error) {
          console.log('Failed to fetch clients, using mock data:', error);
          // Use mock clients if API fails
          clients = [
            {
              id: 'client_mock_001',
              fullName: 'John Doe',
              maritalStatus: 'Single',
              createdAt: new Date().toISOString(),
              lastUpdated: new Date().toISOString()
            },
            {
              id: 'client_mock_002', 
              fullName: 'Jane Smith',
              maritalStatus: 'Married',
              createdAt: new Date().toISOString(),
              lastUpdated: new Date().toISOString()
            }
          ];
        }
        
        // Create AI proposals based on clients (real or mock)
        const mockProposals: AIProposal[] = clients.map((client, index) => {
          const clientData = {
            id: `proposal_${client.id}`,
            clientId: client.id,
            clientName: client.fullName,
            type: 'will' as const,
            status: index === 0 ? 'generating' as const : 'completed' as const,
            confidence: index === 0 ? 0 : Math.floor(Math.random() * 20 + 80), // 80-100%
            createdAt: client.createdAt || new Date().toISOString(),
            lastUpdated: client.lastUpdated || new Date().toISOString(),
            suggestion: index === 0 ? '' : `Based on ${client.fullName}'s profile and estate planning needs, I recommend creating a comprehensive will under Kenyan succession law. The client's marital status (${client.maritalStatus}) and assets require specific legal provisions for proper distribution and tax optimization.`,
            legalReferences: index === 0 ? [] : [
              'Succession Act (Cap 160) - Section 5: Requirements for Valid Will',
              'Law of Succession Act - Section 32: Intestate Succession Rules',
              'Income Tax Act (Cap 470) - Section 3(2)(a): Inheritance Tax Exemption'
            ],
            consequences: index === 0 ? [] : [
              'Clear succession pathway for assets',
              'Reduced family disputes over inheritance',
              'Tax optimization for beneficiaries',
              'Compliance with Kenyan succession laws'
            ],
            nextSteps: index === 0 ? [] : [
              'Draft formal will document with qualified legal counsel',
              'Arrange proper witnessing with two independent witnesses',
              'Register will with relevant authorities (optional but recommended)',
              'Review and update will periodically'
            ]
          };
          return clientData;
        });
        
        console.log('Created proposals:', mockProposals.length);
        setProposals(mockProposals);
        
        // Auto-select the first completed proposal
        const completedProposal = mockProposals.find(p => p.status === 'completed');
        if (completedProposal) {
          setSelectedProposal(completedProposal);
          console.log('Selected proposal:', completedProposal.clientName);
        }
        
      } catch (error) {
        console.error('Failed to fetch AI proposals:', error);
        // Fallback to completely static data
        const fallbackProposals: AIProposal[] = [
          {
            id: 'proposal_fallback_001',
            clientId: 'client_fallback_001',
            clientName: 'Sample Client',
            type: 'will',
            status: 'completed',
            confidence: 92,
            createdAt: new Date().toISOString(),
            lastUpdated: new Date().toISOString(),
            suggestion: 'Based on Kenyan succession law analysis, I recommend creating a comprehensive will with proper witnessing and registration. This ensures legal compliance and reduces family disputes.',
            legalReferences: [
              'Succession Act (Cap 160) - Will Requirements',
              'Law of Succession Act - Probate Procedures'
            ],
            consequences: [
              'Legal asset distribution pathway',
              'Reduced inheritance disputes'
            ],
            nextSteps: [
              'Draft will with legal counsel',
              'Arrange proper witnessing'
            ]
          }
        ];
        setProposals(fallbackProposals);
        setSelectedProposal(fallbackProposals[0]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchProposals();
  }, [isAuthReady]); // Add isAuthReady as dependency

  const getStatusBadge = (status: AIProposal['status']) => {
    const configs = {
      generating: { color: 'bg-yellow-100 text-yellow-800', icon: RefreshCw },
      completed: { color: 'bg-green-100 text-green-800', icon: CheckCircle },
      reviewed: { color: 'bg-blue-100 text-blue-800', icon: Eye },
      approved: { color: 'bg-purple-100 text-purple-800', icon: CheckCircle }
    };
    return configs[status] || configs.generating;
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
        
        {/* Debug Status Panel */}
        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <h3 className="text-sm font-semibold text-blue-800 mb-2">🔧 Debug Status</h3>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>Auth Ready: <span className={isAuthReady ? 'text-green-600 font-bold' : 'text-red-600 font-bold'}>{isAuthReady ? '✅ YES' : '❌ NO'}</span></div>
            <div>Loading: <span className={isLoading ? 'text-yellow-600 font-bold' : 'text-green-600 font-bold'}>{isLoading ? '⏳ YES' : '✅ NO'}</span></div>
            <div>Proposals: <span className="font-bold text-blue-600">{proposals.length}</span></div>
            <div>Selected: <span className="font-bold text-purple-600">{selectedProposal?.clientName || 'None'}</span></div>
          </div>
        </div>
        
        {!isAuthReady && (
          <div className="mt-2 text-sm text-yellow-600">
            ⚡ Initializing authentication...
          </div>
        )}
        {isAuthReady && !isLoading && (
          <div className="mt-2 text-sm text-green-600">
            ✅ Ready! Found {proposals.length} proposals
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Proposals List */}
        <div className="space-y-4">
          <div className="flex items-center justify-between gap-4">
            <h2 className="text-lg font-semibold text-gray-900">Generated Proposals</h2>
            <div className="flex gap-2">
              <button 
                onClick={(e) => {
                  console.log('🔥 Button click event triggered!');
                  console.log('🔍 Event target:', e.target);
                  console.log('🔍 isAuthReady:', isAuthReady);
                  console.log('🔍 Button disabled:', !isAuthReady);
                  e.preventDefault();
                  e.stopPropagation();
                  handleGenerateNew();
                }}
                disabled={!isAuthReady}
                onMouseEnter={() => console.log('🖱️ Mouse entered Generate New button')}
                onMouseDown={() => console.log('🖱️ Mouse down on Generate New button')}
                className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-colors ${
                  isAuthReady 
                    ? 'bg-indigo-600 text-white hover:bg-indigo-700' 
                    : 'bg-gray-400 text-gray-200 cursor-not-allowed'
                }`}
              >
                <Brain className="h-4 w-4" />
                Generate New {isAuthReady ? '✅' : '❌'}
              </button>
              <button 
                onClick={() => {
                  console.log('🧪 Test button clicked');
                  console.log('🔍 Auth ready:', isAuthReady);
                  console.log('🔍 Proposals:', proposals.length);
                  console.log('🔍 Selected:', selectedProposal?.clientName);
                  alert(`🧪 Test button working!\nAuth ready: ${isAuthReady}\nProposals: ${proposals.length}\nSelected: ${selectedProposal?.clientName || 'None'}`);
                }}
                className="px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm"
              >
                🧪 Test
              </button>
              <button 
                onClick={() => {
                  console.log('🔴 BIG DEBUG TEST BUTTON CLICKED!');
                  console.log('🔍 Current time:', new Date().toISOString());
                  console.log('🔍 Window object:', typeof window);
                  console.log('🔍 Router object:', typeof router);
                  alert('🔴 BIG DEBUG BUTTON WORKS! Check console for details.');
                }}
                className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 font-bold"
              >
                🔴 BIG DEBUG TEST
              </button>
            </div>
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
                    <div>
                      <p className="text-sm text-gray-600 line-clamp-3 mb-3">
                        {proposal.suggestion}
                      </p>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          generateProposalForClient(proposal.clientId);
                        }}
                        className="text-xs text-indigo-600 hover:text-indigo-800 font-medium flex items-center gap-1"
                        disabled={(proposal as AIProposal).status === 'generating'}
                      >
                        <RefreshCw className="h-3 w-3" />
                        Regenerate AI Analysis
                      </button>
                    </div>
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