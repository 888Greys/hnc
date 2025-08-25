'use client';

import React, { createContext, useContext, useReducer, useCallback, useEffect } from 'react';
import { QuestionnaireData } from '@/types';
import apiService from '@/services/api';

// Types
interface QuestionnaireState {
  // Current questionnaire data
  currentQuestionnaire: QuestionnaireData | null;
  
  // Form state
  currentSection: number;
  isFormDirty: boolean;
  lastSaved: string | null;
  
  // AI proposal state
  aiProposal: string | null;
  isGeneratingProposal: boolean;
  proposalError: string | null;
  
  // Document state
  generatedDocuments: GeneratedDocument[];
  
  // Client management
  selectedClientId: string | null;
  clientData: ClientRecord | null;
  
  // UI state
  isLoading: boolean;
  error: string | null;
  successMessage: string | null;
  
  // Auto-save state
  autoSaveEnabled: boolean;
  lastAutoSave: string | null;
}

interface ClientRecord {
  id: string;
  name: string;
  email: string;
  phone: string;
  createdAt: string;
  lastActivity: string;
  status: 'active' | 'inactive' | 'pending';
}

interface GeneratedDocument {
  id: string;
  name: string;
  type: string;
  content: string;
  status: 'draft' | 'review' | 'approved' | 'signed';
  createdAt: string;
  lastModified: string;
}

// Actions
type QuestionnaireAction =
  | { type: 'SET_QUESTIONNAIRE_DATA'; payload: QuestionnaireData }
  | { type: 'UPDATE_SECTION_DATA'; payload: { section: keyof QuestionnaireData; data: any } }
  | { type: 'SET_CURRENT_SECTION'; payload: number }
  | { type: 'SET_FORM_DIRTY'; payload: boolean }
  | { type: 'SET_LAST_SAVED'; payload: string }
  | { type: 'SET_AI_PROPOSAL'; payload: string }
  | { type: 'SET_GENERATING_PROPOSAL'; payload: boolean }
  | { type: 'SET_PROPOSAL_ERROR'; payload: string | null }
  | { type: 'ADD_GENERATED_DOCUMENT'; payload: GeneratedDocument }
  | { type: 'UPDATE_DOCUMENT'; payload: { id: string; updates: Partial<GeneratedDocument> } }
  | { type: 'REMOVE_DOCUMENT'; payload: string }
  | { type: 'SET_SELECTED_CLIENT'; payload: { clientId: string; clientData: ClientRecord } }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_SUCCESS_MESSAGE'; payload: string | null }
  | { type: 'SET_AUTO_SAVE_ENABLED'; payload: boolean }
  | { type: 'SET_LAST_AUTO_SAVE'; payload: string }
  | { type: 'RESET_QUESTIONNAIRE' }
  | { type: 'CLEAR_MESSAGES' };

// Initial state
const initialState: QuestionnaireState = {
  currentQuestionnaire: null,
  currentSection: 0,
  isFormDirty: false,
  lastSaved: null,
  aiProposal: null,
  isGeneratingProposal: false,
  proposalError: null,
  generatedDocuments: [],
  selectedClientId: null,
  clientData: null,
  isLoading: false,
  error: null,
  successMessage: null,
  autoSaveEnabled: true,
  lastAutoSave: null,
};

// Reducer
function questionnaireReducer(state: QuestionnaireState, action: QuestionnaireAction): QuestionnaireState {
  switch (action.type) {
    case 'SET_QUESTIONNAIRE_DATA':
      return {
        ...state,
        currentQuestionnaire: action.payload,
        isFormDirty: false,
      };

    case 'UPDATE_SECTION_DATA':
      if (!state.currentQuestionnaire) return state;
      return {
        ...state,
        currentQuestionnaire: {
          ...state.currentQuestionnaire,
          [action.payload.section]: action.payload.data,
        },
        isFormDirty: true,
      };

    case 'SET_CURRENT_SECTION':
      return {
        ...state,
        currentSection: action.payload,
      };

    case 'SET_FORM_DIRTY':
      return {
        ...state,
        isFormDirty: action.payload,
      };

    case 'SET_LAST_SAVED':
      return {
        ...state,
        lastSaved: action.payload,
        isFormDirty: false,
      };

    case 'SET_AI_PROPOSAL':
      return {
        ...state,
        aiProposal: action.payload,
        proposalError: null,
      };

    case 'SET_GENERATING_PROPOSAL':
      return {
        ...state,
        isGeneratingProposal: action.payload,
        proposalError: action.payload ? null : state.proposalError,
      };

    case 'SET_PROPOSAL_ERROR':
      return {
        ...state,
        proposalError: action.payload,
        isGeneratingProposal: false,
      };

    case 'ADD_GENERATED_DOCUMENT':
      return {
        ...state,
        generatedDocuments: [...state.generatedDocuments, action.payload],
      };

    case 'UPDATE_DOCUMENT':
      return {
        ...state,
        generatedDocuments: state.generatedDocuments.map(doc =>
          doc.id === action.payload.id
            ? { ...doc, ...action.payload.updates, lastModified: new Date().toISOString() }
            : doc
        ),
      };

    case 'REMOVE_DOCUMENT':
      return {
        ...state,
        generatedDocuments: state.generatedDocuments.filter(doc => doc.id !== action.payload),
      };

    case 'SET_SELECTED_CLIENT':
      return {
        ...state,
        selectedClientId: action.payload.clientId,
        clientData: action.payload.clientData,
      };

    case 'SET_LOADING':
      return {
        ...state,
        isLoading: action.payload,
      };

    case 'SET_ERROR':
      return {
        ...state,
        error: action.payload,
      };

    case 'SET_SUCCESS_MESSAGE':
      return {
        ...state,
        successMessage: action.payload,
      };

    case 'SET_AUTO_SAVE_ENABLED':
      return {
        ...state,
        autoSaveEnabled: action.payload,
      };

    case 'SET_LAST_AUTO_SAVE':
      return {
        ...state,
        lastAutoSave: action.payload,
      };

    case 'RESET_QUESTIONNAIRE':
      return {
        ...initialState,
        autoSaveEnabled: state.autoSaveEnabled,
        selectedClientId: state.selectedClientId,
        clientData: state.clientData,
      };

    case 'CLEAR_MESSAGES':
      return {
        ...state,
        error: null,
        successMessage: null,
      };

    default:
      return state;
  }
}

// Context
const QuestionnaireContext = createContext<{
  state: QuestionnaireState;
  actions: {
    // Questionnaire actions
    setQuestionnaireData: (data: QuestionnaireData) => void;
    updateSectionData: (section: keyof QuestionnaireData, data: any) => void;
    setCurrentSection: (section: number) => void;
    
    // Save/Load actions
    saveQuestionnaire: () => Promise<void>;
    loadQuestionnaire: (clientId: string) => Promise<void>;
    autoSave: () => Promise<void>;
    
    // AI Proposal actions
    generateAIProposal: () => Promise<void>;
    
    // Document actions
    addDocument: (document: GeneratedDocument) => void;
    updateDocument: (id: string, updates: Partial<GeneratedDocument>) => void;
    removeDocument: (id: string) => void;
    
    // Client actions
    setSelectedClient: (clientId: string, clientData: ClientRecord) => void;
    
    // Utility actions
    clearMessages: () => void;
    resetQuestionnaire: () => void;
    setAutoSaveEnabled: (enabled: boolean) => void;
  };
} | null>(null);

// Provider component
export function QuestionnaireProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(questionnaireReducer, initialState);

  // Auto-save effect
  useEffect(() => {
    if (!state.autoSaveEnabled || !state.isFormDirty || !state.currentQuestionnaire) {
      return;
    }

    const autoSaveTimer = setTimeout(() => {
      autoSave();
    }, 30000); // Auto-save every 30 seconds

    return () => clearTimeout(autoSaveTimer);
  }, [state.isFormDirty, state.currentQuestionnaire, state.autoSaveEnabled]);

  // Clear messages after timeout
  useEffect(() => {
    if (state.error || state.successMessage) {
      const timer = setTimeout(() => {
        dispatch({ type: 'CLEAR_MESSAGES' });
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [state.error, state.successMessage]);

  // Actions
  const setQuestionnaireData = useCallback((data: QuestionnaireData) => {
    dispatch({ type: 'SET_QUESTIONNAIRE_DATA', payload: data });
  }, []);

  const updateSectionData = useCallback((section: keyof QuestionnaireData, data: any) => {
    dispatch({ type: 'UPDATE_SECTION_DATA', payload: { section, data } });
  }, []);

  const setCurrentSection = useCallback((section: number) => {
    dispatch({ type: 'SET_CURRENT_SECTION', payload: section });
  }, []);

  const saveQuestionnaire = useCallback(async () => {
    if (!state.currentQuestionnaire) {
      dispatch({ type: 'SET_ERROR', payload: 'No questionnaire data to save' });
      return;
    }

    dispatch({ type: 'SET_LOADING', payload: true });
    
    try {
      const response = await apiService.submitQuestionnaire(state.currentQuestionnaire);
      dispatch({ type: 'SET_LAST_SAVED', payload: new Date().toISOString() });
      dispatch({ type: 'SET_SUCCESS_MESSAGE', payload: 'Questionnaire saved successfully' });
      console.log('Questionnaire saved:', response);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to save questionnaire';
      dispatch({ type: 'SET_ERROR', payload: errorMessage });
      console.error('Save failed:', error);
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, [state.currentQuestionnaire]);

  const loadQuestionnaire = useCallback(async (clientId: string) => {
    dispatch({ type: 'SET_LOADING', payload: true });
    
    try {
      // This would be an API call to load existing questionnaire data
      // For now, we'll simulate it
      console.log('Loading questionnaire for client:', clientId);
      dispatch({ type: 'SET_SUCCESS_MESSAGE', payload: 'Questionnaire loaded successfully' });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load questionnaire';
      dispatch({ type: 'SET_ERROR', payload: errorMessage });
      console.error('Load failed:', error);
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, []);

  const autoSave = useCallback(async () => {
    if (!state.currentQuestionnaire || !state.isFormDirty) {
      return;
    }

    try {
      // Simulate auto-save API call
      console.log('Auto-saving questionnaire...');
      dispatch({ type: 'SET_LAST_AUTO_SAVE', payload: new Date().toISOString() });
      dispatch({ type: 'SET_FORM_DIRTY', payload: false });
    } catch (error) {
      console.error('Auto-save failed:', error);
    }
  }, [state.currentQuestionnaire, state.isFormDirty]);

  const generateAIProposal = useCallback(async () => {
    if (!state.currentQuestionnaire) {
      dispatch({ type: 'SET_PROPOSAL_ERROR', payload: 'No questionnaire data available' });
      return;
    }

    dispatch({ type: 'SET_GENERATING_PROPOSAL', payload: true });
    
    try {
      const response = await apiService.generateAIProposal({
        questionnaireData: state.currentQuestionnaire,
        distributionPrefs: state.currentQuestionnaire.economicContext.distributionPrefs,
      });
      
      dispatch({ type: 'SET_AI_PROPOSAL', payload: response.suggestion });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to generate AI proposal';
      dispatch({ type: 'SET_PROPOSAL_ERROR', payload: errorMessage });
      console.error('AI proposal generation failed:', error);
    } finally {
      dispatch({ type: 'SET_GENERATING_PROPOSAL', payload: false });
    }
  }, [state.currentQuestionnaire]);

  const addDocument = useCallback((document: GeneratedDocument) => {
    dispatch({ type: 'ADD_GENERATED_DOCUMENT', payload: document });
  }, []);

  const updateDocument = useCallback((id: string, updates: Partial<GeneratedDocument>) => {
    dispatch({ type: 'UPDATE_DOCUMENT', payload: { id, updates } });
  }, []);

  const removeDocument = useCallback((id: string) => {
    dispatch({ type: 'REMOVE_DOCUMENT', payload: id });
  }, []);

  const setSelectedClient = useCallback((clientId: string, clientData: ClientRecord) => {
    dispatch({ type: 'SET_SELECTED_CLIENT', payload: { clientId, clientData } });
  }, []);

  const clearMessages = useCallback(() => {
    dispatch({ type: 'CLEAR_MESSAGES' });
  }, []);

  const resetQuestionnaire = useCallback(() => {
    dispatch({ type: 'RESET_QUESTIONNAIRE' });
  }, []);

  const setAutoSaveEnabled = useCallback((enabled: boolean) => {
    dispatch({ type: 'SET_AUTO_SAVE_ENABLED', payload: enabled });
  }, []);

  const actions = {
    setQuestionnaireData,
    updateSectionData,
    setCurrentSection,
    saveQuestionnaire,
    loadQuestionnaire,
    autoSave,
    generateAIProposal,
    addDocument,
    updateDocument,
    removeDocument,
    setSelectedClient,
    clearMessages,
    resetQuestionnaire,
    setAutoSaveEnabled,
  };

  return (
    <QuestionnaireContext.Provider value={{ state, actions }}>
      {children}
    </QuestionnaireContext.Provider>
  );
}

// Hook to use the context
export function useQuestionnaire() {
  const context = useContext(QuestionnaireContext);
  if (!context) {
    throw new Error('useQuestionnaire must be used within a QuestionnaireProvider');
  }
  return context;
}

// Selectors for common state access patterns
export const useQuestionnaireSelectors = () => {
  const { state } = useQuestionnaire();
  
  return {
    // Current form state
    currentQuestionnaire: state.currentQuestionnaire,
    currentSection: state.currentSection,
    isFormDirty: state.isFormDirty,
    lastSaved: state.lastSaved,
    
    // AI proposal state
    aiProposal: state.aiProposal,
    isGeneratingProposal: state.isGeneratingProposal,
    proposalError: state.proposalError,
    
    // Document state
    generatedDocuments: state.generatedDocuments,
    
    // Client state
    selectedClientId: state.selectedClientId,
    clientData: state.clientData,
    
    // UI state
    isLoading: state.isLoading,
    error: state.error,
    successMessage: state.successMessage,
    
    // Auto-save state
    autoSaveEnabled: state.autoSaveEnabled,
    lastAutoSave: state.lastAutoSave,
    
    // Computed values
    hasUnsavedChanges: state.isFormDirty,
    canGenerateProposal: state.currentQuestionnaire !== null && !state.isGeneratingProposal,
    documentCount: state.generatedDocuments.length,
  };
};

// Higher-order component for components that need questionnaire context
export function withQuestionnaire<P extends object>(
  Component: React.ComponentType<P>
): React.ComponentType<P> {
  return function WrappedComponent(props: P) {
    return (
      <QuestionnaireProvider>
        <Component {...props} />
      </QuestionnaireProvider>
    );
  };
}