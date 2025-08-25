'use client';

import { useState } from 'react';
import { FileText, Download, Send, Eye, Edit, Printer, Share, Save, Plus, X, Check, AlertTriangle, Clock, Settings } from 'lucide-react';
import { cn } from '@/lib/utils';
import { QuestionnaireData } from '@/types';

interface DocumentGenerationProps {
  questionnaireData?: QuestionnaireData;
  aiProposal?: string;
  clientId?: string;
}

interface DocumentTemplate {
  id: string;
  name: string;
  description: string;
  type: 'will' | 'trust' | 'power_of_attorney' | 'living_will' | 'share_transfer' | 'custom';
  icon: React.ElementType;
  requiredFields: string[];
  estimatedPages: number;
  complexity: 'simple' | 'moderate' | 'complex';
}

interface GeneratedDocument {
  id: string;
  name: string;
  template: DocumentTemplate;
  content: string;
  status: 'draft' | 'review' | 'approved' | 'signed';
  createdAt: string;
  lastModified: string;
  version: number;
  wordCount: number;
}

const documentTemplates: DocumentTemplate[] = [
  {
    id: 'last_will_testament',
    name: 'Last Will and Testament',
    description: 'Comprehensive will document with asset distribution and guardianship provisions',
    type: 'will',
    icon: FileText,
    requiredFields: ['fullName', 'assets', 'beneficiaries'],
    estimatedPages: 8,
    complexity: 'moderate',
  },
  {
    id: 'living_will',
    name: 'Living Will',
    description: 'Advance directive for medical decisions and end-of-life care',
    type: 'living_will',
    icon: FileText,
    requiredFields: ['fullName', 'medicalPreferences'],
    estimatedPages: 4,
    complexity: 'simple',
  },
  {
    id: 'revocable_trust',
    name: 'Revocable Trust Agreement',
    description: 'Living trust for asset management and estate planning',
    type: 'trust',
    icon: FileText,
    requiredFields: ['fullName', 'assets', 'trustees', 'beneficiaries'],
    estimatedPages: 12,
    complexity: 'complex',
  },
  {
    id: 'power_of_attorney',
    name: 'Power of Attorney',
    description: 'Legal authorization for financial and legal decision-making',
    type: 'power_of_attorney',
    icon: FileText,
    requiredFields: ['fullName', 'attorney', 'powers'],
    estimatedPages: 6,
    complexity: 'moderate',
  },
  {
    id: 'share_transfer_will',
    name: 'Share Transfer Will',
    description: 'Specialized will for transferring business shares and equity',
    type: 'share_transfer',
    icon: FileText,
    requiredFields: ['fullName', 'shareDetails', 'beneficiaries'],
    estimatedPages: 10,
    complexity: 'complex',
  },
];

export function DocumentGeneration({ questionnaireData, aiProposal, clientId }: DocumentGenerationProps) {
  const [selectedTemplate, setSelectedTemplate] = useState<DocumentTemplate | null>(null);
  const [generatedDocuments, setGeneratedDocuments] = useState<GeneratedDocument[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [currentPreviewDocument, setPreviewDocument] = useState<GeneratedDocument | null>(null);
  const [exportFormat, setExportFormat] = useState<'pdf' | 'docx' | 'txt'>('pdf');
  const [showSettings, setShowSettings] = useState(false);

  const generateDocument = async (template: DocumentTemplate) => {
    if (!questionnaireData) {
      alert('Questionnaire data is required to generate documents');
      return;
    }

    setIsGenerating(true);
    setSelectedTemplate(template);

    try {
      // Simulate document generation
      await new Promise(resolve => setTimeout(resolve, 2000));

      const documentContent = generateDocumentContent(template, questionnaireData, aiProposal);
      
      const newDocument: GeneratedDocument = {
        id: `doc_${Date.now()}`,
        name: `${template.name} - ${questionnaireData.bioData.fullName}`,
        template,
        content: documentContent,
        status: 'draft',
        createdAt: new Date().toISOString(),
        lastModified: new Date().toISOString(),
        version: 1,
        wordCount: documentContent.split(' ').length,
      };

      setGeneratedDocuments(prev => [...prev, newDocument]);
    } catch (error) {
      console.error('Document generation failed:', error);
      alert('Failed to generate document. Please try again.');
    } finally {
      setIsGenerating(false);
      setSelectedTemplate(null);
    }
  };

  const generateDocumentContent = (template: DocumentTemplate, data: QuestionnaireData, proposal?: string): string => {
    const { bioData, financialData, objectives } = data;
    
    switch (template.type) {
      case 'will':
        return `
LAST WILL AND TESTAMENT

I, ${bioData.fullName}, being of sound mind and memory, do hereby make, publish, and declare this to be my Last Will and Testament, revoking all previous wills and codicils.

ARTICLE I - PERSONAL INFORMATION
I am a resident of Kenya. My marital status is ${bioData.maritalStatus.toLowerCase()}.
${bioData.spouseName ? `I am married to ${bioData.spouseName}.` : ''}

ARTICLE II - DEBTS AND EXPENSES
I direct that all my just debts, funeral expenses, and the expenses of administration of my estate be paid as soon as practicable after my death.

ARTICLE III - SPECIFIC BEQUESTS
I give, devise, and bequeath the following specific gifts:

${financialData.assets.map(asset => 
  `- ${asset.description} (${asset.type}): Valued at KES ${asset.value.toLocaleString()}`
).join('\n')}

ARTICLE IV - RESIDUARY ESTATE
All the rest, residue, and remainder of my estate, both real and personal, I give, devise, and bequeath to my beneficiaries as follows:

${bioData.children ? `To my children: ${bioData.children}` : 'As specified in attached beneficiary schedule.'}

${proposal ? `\nLEGAL RECOMMENDATIONS:\n${proposal}` : ''}

IN WITNESS WHEREOF, I have hereunto set my hand this _____ day of __________, 2024.

_________________________
${bioData.fullName}

WITNESSES:
We, the undersigned, being first duly sworn, do hereby certify and attest that:
[Witness signatures and attestation clauses to be completed at signing]
        `.trim();

      case 'living_will':
        return `
LIVING WILL AND ADVANCE DIRECTIVE

I, ${bioData.fullName}, being of sound mind, willfully and voluntarily make this Living Will and Advance Directive.

PERSONAL INFORMATION
Name: ${bioData.fullName}
Marital Status: ${bioData.maritalStatus}

STATEMENT OF DESIRES
If I am in a terminal condition or persistent vegetative state, I direct that:

1. Life-sustaining procedures be withheld or withdrawn when such procedures would serve only to prolong the dying process.

2. I be permitted to die naturally with only the administration of medication or the performance of medical procedures deemed necessary to provide comfort care.

3. My family and physicians be guided by this directive in making decisions about my medical care.

APPOINTMENT OF HEALTH CARE PROXY
${bioData.spouseName ? `I appoint ${bioData.spouseName} as my health care proxy.` : 'I will designate a health care proxy separately.'}

This directive shall remain in effect until revoked by me.

Date: __________    Signature: _________________________
                   ${bioData.fullName}
        `.trim();

      case 'trust':
        return `
REVOCABLE TRUST AGREEMENT

THIS TRUST AGREEMENT is made between ${bioData.fullName} (the "Grantor") and [TRUSTEE NAME] (the "Trustee").

ARTICLE I - TRUST PROPERTY
The Grantor transfers the following property to the Trust:

${financialData.assets.map(asset => 
  `- ${asset.description}: KES ${asset.value.toLocaleString()}`
).join('\n')}

ARTICLE II - ADMINISTRATION
The Trustee shall hold, administer, and distribute the trust property according to the terms herein.

ARTICLE III - DISTRIBUTIONS
During the Grantor's lifetime, the Trustee may distribute income and principal for the Grantor's benefit.

ARTICLE IV - SUCCESSION
Upon the Grantor's death, the trust property shall be distributed to:
${bioData.children || 'Named beneficiaries as specified in Schedule A'}

${proposal ? `\nTRUST RECOMMENDATIONS:\n${proposal}` : ''}

IN WITNESS WHEREOF, the parties have executed this Trust Agreement.

Grantor: _________________________    Date: __________
         ${bioData.fullName}

Trustee: _________________________    Date: __________
         [TRUSTEE NAME]
        `.trim();

      default:
        return `
${template.name.toUpperCase()}

Client: ${bioData.fullName}
Date: ${new Date().toLocaleDateString()}

[Document content to be customized based on template type]

${proposal ? `\nRecommendations:\n${proposal}` : ''}
        `.trim();
    }
  };

  const handlePreviewDocument = (document: GeneratedDocument) => {
    setPreviewDocument(document);
    setIsPreviewOpen(true);
  };

  const downloadDocument = (document: GeneratedDocument, format: string = exportFormat) => {
    const content = `${document.name}\n\n${document.content}`;
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${document.name.replace(/\s+/g, '_')}.${format}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const updateDocumentStatus = (documentId: string, status: GeneratedDocument['status']) => {
    setGeneratedDocuments(prev => 
      prev.map(doc => 
        doc.id === documentId 
          ? { ...doc, status, lastModified: new Date().toISOString() }
          : doc
      )
    );
  };

  const deleteDocument = (documentId: string) => {
    setGeneratedDocuments(prev => prev.filter(doc => doc.id !== documentId));
  };

  const getStatusColor = (status: GeneratedDocument['status']) => {
    switch (status) {
      case 'draft': return 'bg-gray-100 text-gray-800';
      case 'review': return 'bg-yellow-100 text-yellow-800';
      case 'approved': return 'bg-green-100 text-green-800';
      case 'signed': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getComplexityColor = (complexity: DocumentTemplate['complexity']) => {
    switch (complexity) {
      case 'simple': return 'text-green-600';
      case 'moderate': return 'text-yellow-600';
      case 'complex': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 px-6 py-4 border-b">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <FileText className="h-6 w-6 text-blue-600" />
            <div>
              <h2 className="text-xl font-bold text-gray-900">Document Generation</h2>
              <p className="text-gray-600 text-sm">Generate and manage legal documents</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setShowSettings(!showSettings)}
              className="flex items-center space-x-2 px-3 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
            >
              <Settings className="h-4 w-4" />
              <span>Settings</span>
            </button>
          </div>
        </div>
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <div className="bg-gray-50 border-b px-6 py-4">
          <div className="flex items-center space-x-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Export Format</label>
              <select
                value={exportFormat}
                onChange={(e) => setExportFormat(e.target.value as 'pdf' | 'docx' | 'txt')}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="pdf">PDF</option>
                <option value="docx">Word Document</option>
                <option value="txt">Text File</option>
              </select>
            </div>
          </div>
        </div>
      )}

      <div className="p-6">
        {/* Document Templates */}
        <div className="mb-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Available Document Templates</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {documentTemplates.map((template) => {
              const Icon = template.icon;
              return (
                <div
                  key={template.id}
                  className="border border-gray-200 rounded-lg p-4 hover:border-blue-500 hover:shadow-md transition-all cursor-pointer"
                  onClick={() => generateDocument(template)}
                >
                  <div className="flex items-start space-x-3">
                    <Icon className="h-6 w-6 text-blue-600 mt-1" />
                    <div className="flex-1">
                      <h4 className="font-medium text-gray-900">{template.name}</h4>
                      <p className="text-sm text-gray-600 mt-1">{template.description}</p>
                      <div className="flex items-center justify-between mt-3">
                        <div className="flex items-center space-x-4 text-xs text-gray-500">
                          <span>{template.estimatedPages} pages</span>
                          <span className={getComplexityColor(template.complexity)}>
                            {template.complexity}
                          </span>
                        </div>
                        <Plus className="h-4 w-4 text-blue-600" />
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Loading State */}
        {isGenerating && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6">
            <div className="flex items-center space-x-3">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
              <div>
                <h4 className="font-medium text-blue-900">Generating Document</h4>
                <p className="text-blue-700 text-sm">
                  Creating {selectedTemplate?.name} for {questionnaireData?.bioData.fullName}...
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Generated Documents */}
        {generatedDocuments.length > 0 && (
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Generated Documents</h3>
            <div className="space-y-4">
              {generatedDocuments.map((document) => (
                <div key={document.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-start space-x-4">
                      <FileText className="h-6 w-6 text-gray-600 mt-1" />
                      <div>
                        <h4 className="font-medium text-gray-900">{document.name}</h4>
                        <div className="flex items-center space-x-4 mt-1 text-sm text-gray-600">
                          <span>Version {document.version}</span>
                          <span>{document.wordCount} words</span>
                          <span>Created {new Date(document.createdAt).toLocaleDateString()}</span>
                        </div>
                        <div className="flex items-center space-x-2 mt-2">
                          <span className={cn("px-2 py-1 rounded-full text-xs font-medium", getStatusColor(document.status))}>
                            {document.status.charAt(0).toUpperCase() + document.status.slice(1)}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handlePreviewDocument(document)}
                        className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-md"
                        title="Preview"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                      
                      <button
                        onClick={() => downloadDocument(document)}
                        className="p-2 text-gray-600 hover:text-green-600 hover:bg-green-50 rounded-md"
                        title="Download"
                      >
                        <Download className="h-4 w-4" />
                      </button>
                      
                      <button className="p-2 text-gray-600 hover:text-purple-600 hover:bg-purple-50 rounded-md" title="Edit">
                        <Edit className="h-4 w-4" />
                      </button>
                      
                      <button className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-md" title="Send">
                        <Send className="h-4 w-4" />
                      </button>
                      
                      <button className="p-2 text-gray-600 hover:text-indigo-600 hover:bg-indigo-50 rounded-md" title="Print">
                        <Printer className="h-4 w-4" />
                      </button>

                      {/* Status Update Dropdown */}
                      <select
                        value={document.status}
                        onChange={(e) => updateDocumentStatus(document.id, e.target.value as GeneratedDocument['status'])}
                        className="text-xs border border-gray-300 rounded px-2 py-1"
                      >
                        <option value="draft">Draft</option>
                        <option value="review">Review</option>
                        <option value="approved">Approved</option>
                        <option value="signed">Signed</option>
                      </select>
                      
                      <button
                        onClick={() => deleteDocument(document.id)}
                        className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-md"
                        title="Delete"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {generatedDocuments.length === 0 && !isGenerating && (
          <div className="text-center py-12">
            <FileText className="h-16 w-16 mx-auto mb-4 text-gray-300" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No Documents Generated</h3>
            <p className="text-gray-600 mb-6">Select a template above to generate your first legal document.</p>
            {!questionnaireData && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 inline-block">
                <div className="flex items-center space-x-2">
                  <AlertTriangle className="h-5 w-5 text-yellow-600" />
                  <span className="text-yellow-800 text-sm">Complete the questionnaire first to enable document generation</span>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Preview Modal */}
      {isPreviewOpen && currentPreviewDocument && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl max-h-[90vh] w-full flex flex-col">
            <div className="flex items-center justify-between p-6 border-b">
              <h3 className="text-lg font-semibold text-gray-900">{currentPreviewDocument.name}</h3>
              <div className="flex items-center space-x-3">
                <button
                  onClick={() => downloadDocument(currentPreviewDocument)}
                  className="flex items-center space-x-2 px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  <Download className="h-4 w-4" />
                  <span>Download</span>
                </button>
                <button
                  onClick={() => setIsPreviewOpen(false)}
                  className="p-2 text-gray-600 hover:text-gray-800"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
            </div>
            <div className="flex-1 p-6 overflow-y-auto">
              <pre className="whitespace-pre-wrap text-sm text-gray-700 font-mono leading-relaxed">
                {currentPreviewDocument.content}
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}