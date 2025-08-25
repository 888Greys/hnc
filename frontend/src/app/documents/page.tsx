'use client';

import { useState, useEffect } from 'react';
import { Download, FileText, Eye, Edit, Trash2, Plus, Filter, Search, Calendar } from 'lucide-react';

interface Document {
  id: string;
  name: string;
  type: 'will' | 'trust' | 'power_of_attorney' | 'succession_certificate' | 'asset_declaration';
  clientId: string;
  clientName: string;
  status: 'draft' | 'review' | 'finalized' | 'signed';
  size: string;
  createdAt: string;
  lastModified: string;
  version: number;
}

const documentTemplates = [
  { id: 'will_template', name: 'Last Will and Testament', type: 'will', description: 'Standard will template for estate planning' },
  { id: 'trust_template', name: 'Family Trust Agreement', type: 'trust', description: 'Trust document for asset management' },
  { id: 'poa_template', name: 'Power of Attorney', type: 'power_of_attorney', description: 'Legal power of attorney document' },
  { id: 'succession_template', name: 'Succession Certificate', type: 'succession_certificate', description: 'Certificate of inheritance' },
  { id: 'asset_template', name: 'Asset Declaration', type: 'asset_declaration', description: 'Comprehensive asset documentation' }
];

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [isLoading, setIsLoading] = useState(true);
  const [showTemplates, setShowTemplates] = useState(false);

  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 800));
        
        const mockDocuments: Document[] = [
          {
            id: 'doc_001',
            name: 'Will - Test Client E2E',
            type: 'will',
            clientId: 'client_58a83757',
            clientName: 'Test Client E2E',
            status: 'draft',
            size: '45 KB',
            createdAt: '2025-08-25T13:45:00.000Z',
            lastModified: '2025-08-25T13:45:00.000Z',
            version: 1
          },
          {
            id: 'doc_002',
            name: 'Trust Agreement - Jane Smith',
            type: 'trust',
            clientId: 'client_sample_001',
            clientName: 'Jane Smith',
            status: 'review',
            size: '78 KB',
            createdAt: '2025-08-23T10:30:00.000Z',
            lastModified: '2025-08-24T16:20:00.000Z',
            version: 2
          },
          {
            id: 'doc_003',
            name: 'Asset Declaration - Michael Johnson',
            type: 'asset_declaration',
            clientId: 'client_003',
            clientName: 'Michael Johnson',
            status: 'finalized',
            size: '32 KB',
            createdAt: '2025-08-20T14:15:00.000Z',
            lastModified: '2025-08-22T11:30:00.000Z',
            version: 3
          }
        ];
        
        setDocuments(mockDocuments);
      } catch (error) {
        console.error('Failed to fetch documents:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchDocuments();
  }, []);

  const filteredDocuments = documents.filter(doc => {
    const matchesSearch = doc.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         doc.clientName.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = typeFilter === 'all' || doc.type === typeFilter;
    const matchesStatus = statusFilter === 'all' || doc.status === statusFilter;
    return matchesSearch && matchesType && matchesStatus;
  });

  const getStatusBadge = (status: string) => {
    const colors = {
      draft: 'bg-gray-100 text-gray-800',
      review: 'bg-yellow-100 text-yellow-800',
      finalized: 'bg-green-100 text-green-800',
      signed: 'bg-blue-100 text-blue-800'
    };
    return colors[status as keyof typeof colors] || 'bg-gray-100 text-gray-800';
  };

  const getTypeIcon = (type: string) => {
    return FileText; // Using same icon for all document types for simplicity
  };

  const formatDocumentType = (type: string) => {
    return type.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  };

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Document Management</h1>
        <p className="text-gray-600">
          Generate, manage, and export legal documents for clients
        </p>
      </div>

      {/* Action Bar */}
      <div className="mb-6 flex flex-col sm:flex-row gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
          <input
            type="text"
            placeholder="Search documents by name or client..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        
        <div className="flex gap-2">
          <select
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
          >
            <option value="all">All Types</option>
            <option value="will">Will</option>
            <option value="trust">Trust</option>
            <option value="power_of_attorney">Power of Attorney</option>
            <option value="succession_certificate">Succession Certificate</option>
            <option value="asset_declaration">Asset Declaration</option>
          </select>
          
          <select
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="all">All Status</option>
            <option value="draft">Draft</option>
            <option value="review">Review</option>
            <option value="finalized">Finalized</option>
            <option value="signed">Signed</option>
          </select>
          
          <button 
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2"
            onClick={() => setShowTemplates(!showTemplates)}
          >
            <Plus className="h-4 w-4" />
            New Document
          </button>
        </div>
      </div>

      {/* Document Templates (when creating new) */}
      {showTemplates && (
        <div className="mb-6 bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Choose Document Template</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {documentTemplates.map((template) => (
              <div
                key={template.id}
                className="border border-gray-200 rounded-lg p-4 hover:border-indigo-500 cursor-pointer transition-colors"
                onClick={() => {
                  // Handle template selection
                  console.log('Selected template:', template.name);
                  setShowTemplates(false);
                }}
              >
                <div className="flex items-center mb-2">
                  <FileText className="h-5 w-5 text-indigo-600 mr-2" />
                  <h4 className="font-medium text-gray-900">{template.name}</h4>
                </div>
                <p className="text-sm text-gray-600">{template.description}</p>
              </div>
            ))}
          </div>
          <button
            className="mt-4 text-sm text-gray-500 hover:text-gray-700"
            onClick={() => setShowTemplates(false)}
          >
            Cancel
          </button>
        </div>
      )}

      {/* Documents Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Document
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Client
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Modified
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {isLoading ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                    Loading documents...
                  </td>
                </tr>
              ) : filteredDocuments.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                    No documents found
                  </td>
                </tr>
              ) : (
                filteredDocuments.map((document) => {
                  const TypeIcon = getTypeIcon(document.type);
                  return (
                    <tr key={document.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <TypeIcon className="h-8 w-8 text-gray-400 mr-3" />
                          <div>
                            <div className="text-sm font-medium text-gray-900">
                              {document.name}
                            </div>
                            <div className="text-sm text-gray-500">
                              {formatDocumentType(document.type)} • {document.size} • v{document.version}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{document.clientName}</div>
                        <div className="text-sm text-gray-500">{document.clientId}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusBadge(document.status)}`}>
                          {document.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <div>{new Date(document.lastModified).toLocaleDateString()}</div>
                        <div className="text-xs text-gray-400">
                          {new Date(document.lastModified).toLocaleTimeString()}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <div className="flex space-x-2">
                          <button className="text-indigo-600 hover:text-indigo-900" title="View">
                            <Eye className="h-4 w-4" />
                          </button>
                          <button className="text-green-600 hover:text-green-900" title="Edit">
                            <Edit className="h-4 w-4" />
                          </button>
                          <button className="text-blue-600 hover:text-blue-900" title="Download">
                            <Download className="h-4 w-4" />
                          </button>
                          <button className="text-red-600 hover:text-red-900" title="Delete">
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Results Summary */}
      {!isLoading && (
        <div className="mt-4 flex items-center justify-between text-sm text-gray-500">
          <span>
            Showing {filteredDocuments.length} of {documents.length} documents
          </span>
          <div className="flex items-center space-x-4">
            <span>Total Size: {documents.reduce((sum, doc) => sum + parseInt(doc.size), 0)} KB</span>
          </div>
        </div>
      )}
    </div>
  );
}