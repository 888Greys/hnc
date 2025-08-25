'use client';

import { useState } from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { cn } from '@/lib/utils';
import { User, DollarSign, FileText, Target, Brain, Save, Plus, Trash2, Download, Send } from 'lucide-react';
import { QuestionnaireData } from '@/types';
import apiService from '@/services/api';

const assetSchema = z.object({
  type: z.enum(['Real Estate', 'Bank Account', 'Shares', 'Other']),
  description: z.string().min(1, 'Asset description is required'),
  value: z.number().min(0, 'Asset value must be positive'),
});

const bioDataSchema = z.object({
  fullName: z.string().min(1, 'Full name is required'),
  maritalStatus: z.enum(['Single', 'Married', 'Divorced', 'Widowed']),
  spouseName: z.string().optional(),
  spouseId: z.string().optional(),
  children: z.string(),
});

const financialDataSchema = z.object({
  assets: z.array(assetSchema),
  liabilities: z.string(),
  incomeSources: z.string(),
});

const economicContextSchema = z.object({
  economicStanding: z.enum(['High Net Worth', 'Middle Income', 'Low Income']),
  distributionPrefs: z.string(),
});

const objectivesSchema = z.object({
  objective: z.enum(['Create Will', 'Create Living Will', 'Create Share Transfer Will', 'Create Trust', 'Sell Asset', 'Other']),
  details: z.string(),
});

const lawyerNotesSchema = z.object({
  notes: z.string(),
});

const formSchema = z.object({
  bioData: bioDataSchema,
  financialData: financialDataSchema,
  economicContext: economicContextSchema,
  objectives: objectivesSchema,
  lawyerNotes: lawyerNotesSchema,
});

type FormData = z.infer<typeof formSchema>;

export function QuestionnaireForm() {
  const [currentSection, setCurrentSection] = useState(0);
  const [aiProposal, setAiProposal] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      bioData: {
        fullName: '',
        maritalStatus: 'Single',
        spouseName: '',
        spouseId: '',
        children: '',
      },
      financialData: {
        assets: [{ type: 'Real Estate' as const, description: '', value: 0 }],
        liabilities: '',
        incomeSources: '',
      },
      economicContext: {
        economicStanding: 'High Net Worth' as const,
        distributionPrefs: '',
      },
      objectives: {
        objective: 'Create Will' as const,
        details: '',
      },
      lawyerNotes: {
        notes: '',
      },
    },
  });

  const { fields, append, remove } = useFieldArray({
    control: form.control,
    name: 'financialData.assets',
  });

  const sections = [
    { title: 'Bio Data', icon: User },
    { title: 'Financial', icon: DollarSign },
    { title: 'Economic Context', icon: FileText },
    { title: 'Objectives', icon: Target },
    { title: 'AI Proposal', icon: Brain },
    { title: 'Lawyer Notes', icon: Save },
  ];

  const generateProposal = async () => {
    setIsGenerating(true);
    try {
      const formData = form.getValues();
      const questionnaireData: QuestionnaireData = {
        bioData: formData.bioData,
        financialData: formData.financialData,
        economicContext: formData.economicContext,
        objectives: formData.objectives,
        lawyerNotes: formData.lawyerNotes.notes,
      };
      
      const response = await apiService.generateAIProposal({
        questionnaireData,
        distributionPrefs: formData.economicContext.distributionPrefs,
      });
      
      setAiProposal(response.suggestion);
    } catch (error: unknown) {
      setAiProposal('Failed to generate AI proposal. Please try again.');
      console.error('AI proposal generation failed:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const onSubmit = async (data: FormData) => {
    setIsSaving(true);
    try {
      const questionnaireData: QuestionnaireData = {
        bioData: data.bioData,
        financialData: data.financialData,
        economicContext: data.economicContext,
        objectives: data.objectives,
        lawyerNotes: data.lawyerNotes.notes,
      };
      
      const response = await apiService.submitQuestionnaire(questionnaireData);
      alert(`Questionnaire submitted successfully! Saved at: ${response.savedAt}`);
    } catch (error: unknown) {
      alert('Failed to submit questionnaire. Please try again.');
      console.error('Questionnaire submission failed:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const addAsset = () => {
    append({ type: 'Real Estate' as const, description: '', value: 0 });
  };

  const watchMaritalStatus = form.watch('bioData.maritalStatus');
  const watchAssets = form.watch('financialData.assets');

  const totalAssetValue = watchAssets?.reduce((sum, asset) => sum + (asset.value || 0), 0) || 0;

  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden">
      {/* Header */}
      <div className="bg-indigo-50 px-6 py-4 border-b">
        <h2 className="text-2xl font-bold text-gray-900">Digital Client Questionnaire</h2>
        <p className="text-gray-600 mt-1">Complete all sections to generate legal proposals</p>
      </div>

      {/* Section Navigation */}
      <div className="bg-gray-50 px-6 py-3 border-b">
        <nav className="flex space-x-8">
          {sections.map((section, index) => {
            const Icon = section.icon;
            const isActive = currentSection === index;
            const isCompleted = false; // You can add completion logic here
            
            return (
              <button
                key={index}
                onClick={() => setCurrentSection(index)}
                className={cn(
                  "flex items-center space-x-2 py-2 px-3 rounded-md text-sm font-medium transition-colors",
                  isActive
                    ? "bg-indigo-100 text-indigo-700"
                    : "text-gray-500 hover:text-gray-700 hover:bg-gray-100"
                )}
              >
                <Icon className="h-4 w-4" />
                <span>{section.title}</span>
                {isCompleted && (
                  <div className="h-2 w-2 bg-green-500 rounded-full" />
                )}
              </button>
            );
          })}
        </nav>
      </div>

      <form onSubmit={form.handleSubmit(onSubmit)} className="p-6">
        {/* Section 1: Client Bio Data */}
        {currentSection === 0 && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <User className="h-5 w-5 mr-2" />
              Client Bio Data
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Full Name *
                </label>
                <input
                  {...form.register('bioData.fullName')}
                  className="input-high-contrast w-full px-3 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="Enter full name"
                />
                {form.formState.errors.bioData?.fullName && (
                  <p className="text-red-600 text-sm mt-1">
                    {form.formState.errors.bioData.fullName.message}
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Marital Status
                </label>
                <select
                  {...form.register('bioData.maritalStatus')}
                  className="select-high-contrast w-full px-3 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="Single">Single</option>
                  <option value="Married">Married</option>
                  <option value="Divorced">Divorced</option>
                  <option value="Widowed">Widowed</option>
                </select>
              </div>
            </div>

            {watchMaritalStatus === 'Married' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Spouse Name
                  </label>
                  <input
                    {...form.register('bioData.spouseName')}
                    className="input-high-contrast w-full px-3 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    placeholder="Enter spouse name"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Spouse ID Number
                  </label>
                  <input
                    {...form.register('bioData.spouseId')}
                    className="input-high-contrast w-full px-3 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    placeholder="Enter spouse ID number"
                  />
                </div>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Children's Details
              </label>
              <textarea
                {...form.register('bioData.children')}
                rows={3}
                className="input-high-contrast w-full px-3 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="Name, Age, Relationship - one per line"
              />
            </div>
          </div>
        )}

        {/* Section 2: Financial Data */}
        {currentSection === 1 && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <DollarSign className="h-5 w-5 mr-2" />
              Financial Data
            </h3>

            {/* Assets */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <label className="block text-sm font-medium text-gray-700">
                  Assets
                </label>
                <button
                  type="button"
                  onClick={addAsset}
                  className="flex items-center space-x-2 px-3 py-1.5 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 text-sm"
                >
                  <Plus className="h-4 w-4" />
                  <span>Add Asset</span>
                </button>
              </div>

              <div className="space-y-4">
                {fields.map((field, index) => (
                  <div key={field.id} className="grid grid-cols-1 md:grid-cols-4 gap-4 p-4 border border-gray-200 rounded-lg">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Type
                      </label>
                      <select
                        {...form.register(`financialData.assets.${index}.type`)}
                        className="select-high-contrast w-full px-3 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                      >
                        <option value="Real Estate">Real Estate</option>
                        <option value="Bank Account">Bank Account</option>
                        <option value="Shares">Shares</option>
                        <option value="Other">Other</option>
                      </select>
                    </div>
                    
                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Description
                      </label>
                      <input
                        {...form.register(`financialData.assets.${index}.description`)}
                        className="input-high-contrast w-full px-3 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                        placeholder="Asset description"
                      />
                    </div>
                    
                    <div className="flex space-x-2">
                      <div className="flex-1">
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Value (KES)
                        </label>
                        <input
                          type="number"
                          {...form.register(`financialData.assets.${index}.value`, { valueAsNumber: true })}
                          className="input-high-contrast w-full px-3 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                          placeholder="0"
                        />
                      </div>
                      {fields.length > 1 && (
                        <button
                          type="button"
                          onClick={() => remove(index)}
                          className="mt-6 p-2 text-red-600 hover:text-red-800"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600">
                  <strong>Total Asset Value:</strong> KES {totalAssetValue.toLocaleString()}
                </p>
              </div>
            </div>

            {/* Liabilities */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Liabilities
              </label>
              <textarea
                {...form.register('financialData.liabilities')}
                rows={3}
                className="input-high-contrast w-full px-3 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="Loans, debts, mortgages - Type, Amount, Details"
              />
            </div>

            {/* Income Sources */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Income Sources
              </label>
              <textarea
                {...form.register('financialData.incomeSources')}
                rows={3}
                className="input-high-contrast w-full px-3 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="Salary, business income, investments - Source, Amount"
              />
            </div>
          </div>
        )}

        {/* Section 3: Economic Context */}
        {currentSection === 2 && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <FileText className="h-5 w-5 mr-2" />
              Economic Context
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Economic Standing
                </label>
                <select
                  {...form.register('economicContext.economicStanding')}
                  className="select-high-contrast w-full px-3 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="">Select economic standing</option>
                  <option value="Low Income">Low Income</option>
                  <option value="Middle Income">Middle Income</option>
                  <option value="High Net Worth">High Net Worth</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Distribution Preferences
                </label>
                <select
                  {...form.register('economicContext.distributionPrefs')}
                  className="select-high-contrast w-full px-3 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="">Select preference</option>
                  <option value="Equal Distribution">Equal Distribution</option>
                  <option value="Merit-based">Merit-based</option>
                  <option value="Need-based">Need-based</option>
                  <option value="Age-based">Age-based</option>
                  <option value="Custom">Custom</option>
                </select>
              </div>
            </div>
          </div>
        )}

        {/* Section 4: Objectives */}
        {currentSection === 3 && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <Target className="h-5 w-5 mr-2" />
              Client Objectives
            </h3>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Primary Objective *
              </label>
              <select
                {...form.register('objectives.objective')}
                className="select-high-contrast w-full px-3 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">Select primary objective</option>
                <option value="Create Will">Create Will</option>
                <option value="Create Living Will">Create Living Will</option>
                <option value="Create Share Transfer Will">Create Share Transfer Will</option>
                <option value="Create Trust">Create Trust</option>
                <option value="Sell Asset">Sell Asset</option>
                <option value="Other">Other</option>
              </select>
              {form.formState.errors.objectives?.objective && (
                <p className="text-red-600 text-sm mt-1">
                  {form.formState.errors.objectives.objective.message}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Objective Details
              </label>
              <textarea
                {...form.register('objectives.details')}
                rows={4}
                className="input-high-contrast w-full px-3 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="Provide specific details about your objectives, expectations, and any special requirements"
              />
            </div>
          </div>
        )}

        {/* Section 5: AI Proposal */}
        {currentSection === 4 && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                <Brain className="h-5 w-5 mr-2" />
                AI Legal Proposal
              </h3>
              <button
                type="button"
                onClick={generateProposal}
                disabled={isGenerating}
                className="flex items-center space-x-2 px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50"
              >
                <Brain className="h-4 w-4" />
                <span>{isGenerating ? 'Generating...' : 'Generate AI Proposal'}</span>
              </button>
            </div>

            {aiProposal && (
              <div className="bg-gradient-to-r from-purple-50 to-indigo-50 border border-purple-200 rounded-lg p-6">
                <h4 className="text-md font-semibold text-purple-900 mb-3">AI Generated Legal Proposal</h4>
                <div className="text-gray-700 whitespace-pre-wrap">
                  {aiProposal}
                </div>
                <div className="mt-4 flex space-x-3">
                  <button
                    type="button"
                    className="flex items-center space-x-2 px-3 py-1.5 bg-purple-600 text-white rounded-md hover:bg-purple-700 text-sm"
                  >
                    <Download className="h-4 w-4" />
                    <span>Download Proposal</span>
                  </button>
                  <button
                    type="button"
                    className="flex items-center space-x-2 px-3 py-1.5 bg-gray-600 text-white rounded-md hover:bg-gray-700 text-sm"
                  >
                    <Send className="h-4 w-4" />
                    <span>Send to Client</span>
                  </button>
                </div>
              </div>
            )}

            {!aiProposal && !isGenerating && (
              <div className="text-center py-12 text-gray-500">
                <Brain className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                <p>Click "Generate AI Proposal" to create a legal recommendation based on the questionnaire data.</p>
              </div>
            )}
          </div>
        )}

        {/* Section 6: Lawyer Notes */}
        {currentSection === 5 && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <Save className="h-5 w-5 mr-2" />
              Lawyer Notes & Final Review
            </h3>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Internal Notes & Observations
              </label>
              <textarea
                {...form.register('lawyerNotes.notes')}
                rows={6}
                className="input-high-contrast w-full px-3 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="Add internal notes, legal observations, follow-up actions, or refinements needed..."
              />
            </div>

            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <h4 className="text-md font-semibold text-yellow-800 mb-2">Review Checklist</h4>
              <ul className="text-sm text-yellow-700 space-y-1">
                <li>✓ Client bio data complete and verified</li>
                <li>✓ Financial assets and liabilities documented</li>
                <li>✓ Economic context and preferences captured</li>
                <li>✓ Objectives clearly defined</li>
                <li>✓ AI proposal generated and reviewed</li>
                <li>✓ Legal compliance verified</li>
              </ul>
            </div>
          </div>
        )}

        {/* Navigation */}
        <div className="flex justify-between items-center mt-8 pt-6 border-t">
          <button
            type="button"
            onClick={() => setCurrentSection(Math.max(0, currentSection - 1))}
            disabled={currentSection === 0}
            className="px-4 py-2 text-gray-600 bg-gray-100 rounded-md hover:bg-gray-200 disabled:opacity-50"
          >
            Previous
          </button>

          <span className="text-sm text-gray-500">
            Section {currentSection + 1} of {sections.length}
          </span>

          {currentSection < sections.length - 1 ? (
            <button
              type="button"
              onClick={() => setCurrentSection(currentSection + 1)}
              className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
            >
              Next
            </button>
          ) : (
            <button
              type="submit"
              disabled={isSaving}
              className="flex items-center space-x-2 px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
            >
              <Save className="h-4 w-4" />
              <span>{isSaving ? 'Saving...' : 'Save Questionnaire'}</span>
            </button>
          )}
        </div>
      </form>
    </div>
  );
}