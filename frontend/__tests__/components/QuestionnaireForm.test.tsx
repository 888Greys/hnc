import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QuestionnaireForm } from '@/components/QuestionnaireForm';
import { ToastProvider } from '@/components/Toast';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import apiService from '@/services/api';

// Mock the API service
jest.mock('@/services/api');
const mockApiService = apiService as jest.Mocked<typeof apiService>;

// Mock Next.js router
jest.mock('next/router', () => ({
  useRouter: () => ({
    push: jest.fn(),
    pathname: '/',
    query: {},
    asPath: '/',
  }),
}));

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ErrorBoundary>
    <ToastProvider>
      {children}
    </ToastProvider>
  </ErrorBoundary>
);

describe('QuestionnaireForm', () => {
  const user = userEvent.setup();

  beforeEach(() => {
    jest.clearAllMocks();
    mockApiService.submitQuestionnaire.mockResolvedValue({
      message: 'Success',
      clientId: 'test-client-id',
      savedAt: '2024-01-01T00:00:00Z',
    });
    mockApiService.generateAIProposal.mockResolvedValue({
      suggestion: 'Test AI suggestion',
      legalReferences: ['Test Reference'],
      consequences: ['Test Consequence'],
      nextSteps: ['Test Step'],
    });
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('Form Rendering', () => {
    it('renders all sections of the questionnaire', () => {
      render(
        <TestWrapper>
          <QuestionnaireForm />
        </TestWrapper>
      );

      // Check section navigation
      expect(screen.getByText('Bio Data')).toBeInTheDocument();
      expect(screen.getByText('Financial')).toBeInTheDocument();
      expect(screen.getByText('Economic Context')).toBeInTheDocument();
      expect(screen.getByText('Objectives')).toBeInTheDocument();
      expect(screen.getByText('AI Proposal')).toBeInTheDocument();
      expect(screen.getByText('Lawyer Notes')).toBeInTheDocument();
    });

    it('starts with the Bio Data section active', () => {
      render(
        <TestWrapper>
          <QuestionnaireForm />
        </TestWrapper>
      );

      expect(screen.getByText('Client Bio Data')).toBeInTheDocument();
      expect(screen.getByLabelText(/full name/i)).toBeInTheDocument();
    });

    it('displays required field indicators', () => {
      render(
        <TestWrapper>
          <QuestionnaireForm />
        </TestWrapper>
      );

      expect(screen.getByText(/full name \*/i)).toBeInTheDocument();
    });
  });

  describe('Form Navigation', () => {
    it('allows navigation between sections', async () => {
      render(
        <TestWrapper>
          <QuestionnaireForm />
        </TestWrapper>
      );

      // Navigate to Financial section
      await user.click(screen.getByText('Financial'));
      expect(screen.getByText('Financial Data')).toBeInTheDocument();

      // Navigate to Economic Context
      await user.click(screen.getByText('Economic Context'));
      expect(screen.getByText('Economic Context')).toBeInTheDocument();
    });

    it('uses Next/Previous buttons for navigation', async () => {
      render(
        <TestWrapper>
          <QuestionnaireForm />
        </TestWrapper>
      );

      // Check Previous button is disabled on first section
      const prevButton = screen.getByText('Previous');
      expect(prevButton).toBeDisabled();

      // Navigate to next section
      await user.click(screen.getByText('Next'));
      expect(screen.getByText('Financial Data')).toBeInTheDocument();

      // Previous button should now be enabled
      expect(prevButton).not.toBeDisabled();
    });
  });

  describe('Bio Data Section', () => {
    it('validates required fields', async () => {
      render(
        <TestWrapper>
          <QuestionnaireForm />
        </TestWrapper>
      );

      const fullNameInput = screen.getByLabelText(/full name/i);
      
      // Try to submit without filling required fields
      await user.click(fullNameInput);
      await user.tab(); // Move focus away to trigger validation

      await waitFor(() => {
        // Should show validation error for empty required field
        expect(screen.getByText(/full name is required/i)).toBeInTheDocument();
      });
    });

    it('handles marital status changes correctly', async () => {
      render(
        <TestWrapper>
          <QuestionnaireForm />
        </TestWrapper>
      );

      const maritalStatusSelect = screen.getByLabelText(/marital status/i);
      
      // Initially, spouse fields should not be visible
      expect(screen.queryByLabelText(/spouse name/i)).not.toBeInTheDocument();

      // Select "Married"
      await user.selectOptions(maritalStatusSelect, 'Married');

      // Spouse fields should now be visible
      await waitFor(() => {
        expect(screen.getByLabelText(/spouse name/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/spouse id/i)).toBeInTheDocument();
      });
    });

    it('accepts valid input data', async () => {
      render(
        <TestWrapper>
          <QuestionnaireForm />
        </TestWrapper>
      );

      const fullNameInput = screen.getByLabelText(/full name/i);
      await user.type(fullNameInput, 'John Doe');

      expect(fullNameInput).toHaveValue('John Doe');
    });
  });

  describe('Financial Data Section', () => {
    beforeEach(async () => {
      render(
        <TestWrapper>
          <QuestionnaireForm />
        </TestWrapper>
      );
      
      // Navigate to Financial section
      await user.click(screen.getByText('Financial'));
    });

    it('displays asset management controls', () => {
      expect(screen.getByText('Assets')).toBeInTheDocument();
      expect(screen.getByText('Add Asset')).toBeInTheDocument();
    });

    it('allows adding new assets', async () => {
      const addAssetButton = screen.getByText('Add Asset');
      const initialAssetCount = screen.getAllByText(/asset description/i).length;

      await user.click(addAssetButton);

      await waitFor(() => {
        const newAssetCount = screen.getAllByText(/asset description/i).length;
        expect(newAssetCount).toBe(initialAssetCount + 1);
      });
    });

    it('allows removing assets', async () => {
      // Add an asset first
      await user.click(screen.getByText('Add Asset'));
      
      await waitFor(() => {
        const deleteButtons = screen.getAllByLabelText(/delete asset/i);
        expect(deleteButtons.length).toBeGreaterThan(0);
      });

      const deleteButtons = screen.getAllByLabelText(/delete asset/i);
      const initialCount = deleteButtons.length;

      await user.click(deleteButtons[0]);

      await waitFor(() => {
        const remainingButtons = screen.queryAllByLabelText(/delete asset/i);
        expect(remainingButtons.length).toBe(Math.max(0, initialCount - 1));
      });
    });

    it('calculates total asset value correctly', async () => {
      // Fill in asset value
      const valueInputs = screen.getAllByLabelText(/value.*kes/i);
      await user.clear(valueInputs[0]);
      await user.type(valueInputs[0], '1000000');

      await waitFor(() => {
        expect(screen.getByText(/total asset value.*kes 1,000,000/i)).toBeInTheDocument();
      });
    });
  });

  describe('AI Proposal Section', () => {
    beforeEach(async () => {
      render(
        <TestWrapper>
          <QuestionnaireForm />
        </TestWrapper>
      );
      
      // Navigate to AI Proposal section
      await user.click(screen.getByText('AI Proposal'));
    });

    it('displays AI proposal generation button', () => {
      expect(screen.getByText('Generate AI Proposal')).toBeInTheDocument();
    });

    it('generates AI proposal when button is clicked', async () => {
      const generateButton = screen.getByText('Generate AI Proposal');
      
      await user.click(generateButton);

      await waitFor(() => {
        expect(mockApiService.generateAIProposal).toHaveBeenCalled();
      });

      await waitFor(() => {
        expect(screen.getByText('Test AI suggestion')).toBeInTheDocument();
      });
    });

    it('shows loading state during AI generation', async () => {
      // Mock a delayed response
      mockApiService.generateAIProposal.mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve({
          suggestion: 'Test AI suggestion',
          legalReferences: ['Test Reference'],
          consequences: ['Test Consequence'],
          nextSteps: ['Test Step'],
        }), 100))
      );

      const generateButton = screen.getByText('Generate AI Proposal');
      
      await user.click(generateButton);

      expect(screen.getByText('Generating...')).toBeInTheDocument();

      await waitFor(() => {
        expect(screen.getByText('Test AI suggestion')).toBeInTheDocument();
      }, { timeout: 2000 });
    });

    it('handles AI generation errors gracefully', async () => {
      mockApiService.generateAIProposal.mockRejectedValue(
        new Error('AI service unavailable')
      );

      const generateButton = screen.getByText('Generate AI Proposal');
      
      await user.click(generateButton);

      await waitFor(() => {
        expect(screen.getByText(/failed to generate ai proposal/i)).toBeInTheDocument();
      });
    });
  });

  describe('Form Submission', () => {
    it('submits complete form successfully', async () => {
      render(
        <TestWrapper>
          <QuestionnaireForm />
        </TestWrapper>
      );

      // Fill required fields
      await user.type(screen.getByLabelText(/full name/i), 'John Doe');
      
      // Navigate to objectives and fill required field
      await user.click(screen.getByText('Objectives'));
      await user.selectOptions(screen.getByLabelText(/primary objective/i), 'Create Will');

      // Navigate to final section
      await user.click(screen.getByText('Lawyer Notes'));

      // Submit the form
      const submitButton = screen.getByText('Save Questionnaire');
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockApiService.submitQuestionnaire).toHaveBeenCalled();
      });
    });

    it('shows loading state during submission', async () => {
      // Mock a delayed response
      mockApiService.submitQuestionnaire.mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve({
          message: 'Success',
          clientId: 'test-client-id',
          savedAt: '2024-01-01T00:00:00Z',
        }), 100))
      );

      render(
        <TestWrapper>
          <QuestionnaireForm />
        </TestWrapper>
      );

      // Navigate to final section and submit
      await user.click(screen.getByText('Lawyer Notes'));
      const submitButton = screen.getByText('Save Questionnaire');
      
      await user.click(submitButton);

      expect(screen.getByText('Saving...')).toBeInTheDocument();

      await waitFor(() => {
        expect(mockApiService.submitQuestionnaire).toHaveBeenCalled();
      }, { timeout: 2000 });
    });

    it('handles submission errors gracefully', async () => {
      mockApiService.submitQuestionnaire.mockRejectedValue(
        new Error('Server error')
      );

      render(
        <TestWrapper>
          <QuestionnaireForm />
        </TestWrapper>
      );

      // Navigate to final section and submit
      await user.click(screen.getByText('Lawyer Notes'));
      const submitButton = screen.getByText('Save Questionnaire');
      
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/failed to submit questionnaire/i)).toBeInTheDocument();
      });
    });
  });

  describe('Data Persistence', () => {
    it('preserves form data when navigating between sections', async () => {
      render(
        <TestWrapper>
          <QuestionnaireForm />
        </TestWrapper>
      );

      // Fill data in Bio section
      const fullNameInput = screen.getByLabelText(/full name/i);
      await user.type(fullNameInput, 'John Doe');

      // Navigate away and back
      await user.click(screen.getByText('Financial'));
      await user.click(screen.getByText('Bio Data'));

      // Data should be preserved
      expect(screen.getByLabelText(/full name/i)).toHaveValue('John Doe');
    });

    it('maintains asset data across navigation', async () => {
      render(
        <TestWrapper>
          <QuestionnaireForm />
        </TestWrapper>
      );

      // Navigate to Financial section
      await user.click(screen.getByText('Financial'));

      // Add asset value
      const valueInput = screen.getAllByLabelText(/value.*kes/i)[0];
      await user.clear(valueInput);
      await user.type(valueInput, '500000');

      // Navigate away and back
      await user.click(screen.getByText('Bio Data'));
      await user.click(screen.getByText('Financial'));

      // Value should be preserved
      expect(screen.getAllByLabelText(/value.*kes/i)[0]).toHaveValue(500000);
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels and roles', () => {
      render(
        <TestWrapper>
          <QuestionnaireForm />
        </TestWrapper>
      );

      expect(screen.getByRole('navigation')).toBeInTheDocument();
      expect(screen.getByRole('form')).toBeInTheDocument();
    });

    it('supports keyboard navigation', async () => {
      render(
        <TestWrapper>
          <QuestionnaireForm />
        </TestWrapper>
      );

      const fullNameInput = screen.getByLabelText(/full name/i);
      
      // Tab to the input
      await user.tab();
      expect(fullNameInput).toHaveFocus();

      // Continue tabbing through form elements
      await user.tab();
      const maritalStatusSelect = screen.getByLabelText(/marital status/i);
      expect(maritalStatusSelect).toHaveFocus();
    });

    it('announces form validation errors to screen readers', async () => {
      render(
        <TestWrapper>
          <QuestionnaireForm />
        </TestWrapper>
      );

      const fullNameInput = screen.getByLabelText(/full name/i);
      
      // Trigger validation error
      await user.click(fullNameInput);
      await user.tab();

      await waitFor(() => {
        const errorMessage = screen.getByText(/full name is required/i);
        expect(errorMessage).toHaveAttribute('role', 'alert');
      });
    });
  });

  describe('Responsive Design', () => {
    it('adapts layout for mobile devices', () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });
      
      render(
        <TestWrapper>
          <QuestionnaireForm />
        </TestWrapper>
      );

      // Check if mobile-responsive classes are applied
      const container = screen.getByRole('form').closest('div');
      expect(container).toHaveClass('p-6'); // Mobile padding
    });
  });
});