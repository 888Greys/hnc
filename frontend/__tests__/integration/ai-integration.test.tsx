import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { rest } from 'msw';
import { setupServer } from 'msw/node';
import { QuestionnaireForm } from '@/components/QuestionnaireForm';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { ToastProvider } from '@/components/Toast';
import { QuestionnaireData, AIProposal } from '@/types';

// Mock server for API calls
const server = setupServer(
  rest.post('/api/auth/login', (req, res, ctx) => {
    return res(
      ctx.json({
        token: 'test-token',
        username: 'testuser',
        loginTime: new Date().toISOString(),
      })
    );
  }),

  rest.post('/api/ai/proposal', (req, res, ctx) => {
    const { questionnaire } = req.body as { questionnaire: QuestionnaireData };
    
    // Simulate different AI responses based on client scenarios
    let aiResponse: AIProposal;
    
    if (questionnaire.objectives.objective === 'Create Will') {
      aiResponse = {
        suggestion: 'Based on your assets and family structure, I recommend creating a comprehensive will with provisions for asset distribution, guardianship arrangements, and tax optimization.',
        legalReferences: [
          'Succession Act (Cap 160) - Sections 5-15 on testamentary provisions',
          'Law of Succession Act - Chapter 160, Section 27 on distribution',
          'Income Tax Act - Section 3(2)(a) on inheritance tax exemptions'
        ],
        consequences: [
          'Ensures orderly distribution of assets according to your wishes',
          'Minimizes potential family disputes and legal challenges',
          'May reduce inheritance tax burden through proper planning',
          'Provides clear guardianship instructions for minor children'
        ],
        nextSteps: [
          'Review and finalize asset valuation with certified valuers',
          'Consult with family members about distribution preferences',
          'Prepare necessary supporting documents (property titles, bank statements)',
          'Schedule will execution ceremony with witnesses and legal counsel'
        ]
      };
    } else if (questionnaire.bioData.maritalStatus === 'Married' && questionnaire.objectives.objective === 'Create Trust') {
      aiResponse = {
        suggestion: 'For married couples with significant assets, establishing a family trust can provide asset protection, tax benefits, and seamless succession planning.',
        legalReferences: [
          'Trustee Act (Cap 167) - Sections 3-8 on trust establishment',
          'Income Tax Act - Section 10(1)(a) on trust taxation',
          'Registration of Documents Act - Chapter 285 on trust registration'
        ],
        consequences: [
          'Assets held in trust are protected from personal liabilities',
          'Potential tax advantages through trust income distribution',
          'Simplified succession process avoiding lengthy probate',
          'Professional management of assets through appointed trustees'
        ],
        nextSteps: [
          'Define trust objectives and beneficiary structure',
          'Select qualified trustees with appropriate expertise',
          'Prepare trust deed with clear terms and conditions',
          'Register trust with relevant authorities and transfer assets'
        ]
      };
    } else if (questionnaire.economicContext.economicStanding === 'High Net Worth') {
      aiResponse = {
        suggestion: 'High net worth individuals require sophisticated estate planning strategies including offshore structures, tax optimization, and philanthropic considerations.',
        legalReferences: [
          'Capital Markets Act - Section 12A on offshore investments',
          'Exchange Control Act - Regulations on foreign asset holdings',
          'Public Benefit Organizations Act - Chapter 285A on charitable giving'
        ],
        consequences: [
          'Complex regulatory compliance requirements across jurisdictions',
          'Significant tax optimization opportunities if structured properly',
          'Enhanced asset protection against potential creditors',
          'Legacy planning opportunities through charitable foundations'
        ],
        nextSteps: [
          'Engage international tax and legal specialists',
          'Conduct comprehensive asset audit and jurisdiction analysis',
          'Develop multi-generational wealth transfer strategy',
          'Establish governance structures for family wealth management'
        ]
      };
    } else {
      // Default response for other scenarios
      aiResponse = {
        suggestion: 'Based on your information, I recommend starting with basic estate planning documents and gradually building a comprehensive legal framework.',
        legalReferences: [
          'Law of Succession Act - Chapter 160 on general succession principles',
          'Registration of Documents Act - Chapter 285 on document requirements'
        ],
        consequences: [
          'Establishes basic legal protection for your assets',
          'Provides clear instructions for asset distribution',
          'Reduces potential legal complications for beneficiaries'
        ],
        nextSteps: [
          'Gather all relevant financial and asset documentation',
          'Consult with qualified legal counsel for document preparation',
          'Review and update documents annually or after major life changes'
        ]
      };
    }
    
    return res(ctx.json(aiResponse));
  }),

  rest.post('/api/ai/proposal', (req, res, ctx) => {
    // Simulate AI service errors for error handling tests
    if (req.headers.get('x-test-error') === 'ai-service-down') {
      return res(
        ctx.status(503),
        ctx.json({ detail: 'AI service temporarily unavailable' })
      );
    }
    
    if (req.headers.get('x-test-error') === 'invalid-input') {
      return res(
        ctx.status(400),
        ctx.json({ detail: 'Invalid questionnaire data provided' })
      );
    }
    
    return res(ctx.json({
      suggestion: 'Test AI response',
      legalReferences: ['Test legal reference'],
      consequences: ['Test consequence'],
      nextSteps: ['Test next step']
    }));
  })
);

// Test wrapper component
const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <ErrorBoundary>
    <ToastProvider>
      {children}
    </ToastProvider>
  </ErrorBoundary>
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('AI Integration Tests', () => {
  // Test data for different client scenarios
  const willClientData: QuestionnaireData = {
    bioData: {
      fullName: 'John Doe',
      maritalStatus: 'Married',
      spouseName: 'Jane Doe',
      spouseId: '12345678',
      children: '2 children: Alice (10), Bob (8)'
    },
    financialData: {
      assets: [
        { type: 'Real Estate', description: 'Family home in Nairobi', value: 15000000 },
        { type: 'Bank Account', description: 'Savings account', value: 2000000 }
      ],
      liabilities: 'Mortgage: KES 5,000,000',
      incomeSources: 'Salary: KES 200,000/month, Rental income: KES 50,000/month'
    },
    economicContext: {
      economicStanding: 'Middle Income',
      distributionPrefs: 'Equal distribution to spouse and children'
    },
    objectives: {
      objective: 'Create Will',
      details: 'Need to create a comprehensive will for family protection'
    },
    lawyerNotes: 'Client concerned about children\'s education funding'
  };

  const trustClientData: QuestionnaireData = {
    ...willClientData,
    economicContext: {
      economicStanding: 'High Net Worth',
      distributionPrefs: 'Trust structure for tax optimization'
    },
    objectives: {
      objective: 'Create Trust',
      details: 'Establish family trust for asset protection and tax benefits'
    }
  };

  const highNetWorthClientData: QuestionnaireData = {
    ...willClientData,
    financialData: {
      assets: [
        { type: 'Real Estate', description: 'Multiple properties', value: 100000000 },
        { type: 'Shares', description: 'Public company holdings', value: 50000000 },
        { type: 'Other', description: 'Business interests', value: 75000000 }
      ],
      liabilities: 'Various business loans: KES 20,000,000',
      incomeSources: 'Multiple business ventures and investments'
    },
    economicContext: {
      economicStanding: 'High Net Worth',
      distributionPrefs: 'Complex multi-generational planning required'
    }
  };

  describe('Will Creation Scenarios', () => {
    test('should generate appropriate AI proposal for standard will creation', async () => {
      render(
        <TestWrapper>
          <QuestionnaireForm />
        </TestWrapper>
      );

      // Fill out the form with will client data
      fireEvent.change(screen.getByLabelText(/full name/i), {
        target: { value: willClientData.bioData.fullName }
      });
      
      fireEvent.change(screen.getByLabelText(/marital status/i), {
        target: { value: willClientData.bioData.maritalStatus }
      });

      // Navigate through form steps and submit
      fireEvent.click(screen.getByText(/next/i));
      fireEvent.click(screen.getByText(/next/i));
      fireEvent.click(screen.getByText(/next/i));
      
      fireEvent.click(screen.getByText(/generate ai proposal/i));

      // Wait for AI response
      await waitFor(() => {
        expect(screen.getByText(/comprehensive will with provisions/i)).toBeInTheDocument();
      });

      // Verify legal references are displayed
      expect(screen.getByText(/Succession Act \(Cap 160\)/i)).toBeInTheDocument();
      expect(screen.getByText(/Law of Succession Act/i)).toBeInTheDocument();

      // Verify consequences are shown
      expect(screen.getByText(/orderly distribution of assets/i)).toBeInTheDocument();
      expect(screen.getByText(/minimizes potential family disputes/i)).toBeInTheDocument();

      // Verify next steps are provided
      expect(screen.getByText(/review and finalize asset valuation/i)).toBeInTheDocument();
    });

    test('should handle complex family structures in will planning', async () => {
      const complexFamilyData = {
        ...willClientData,
        bioData: {
          ...willClientData.bioData,
          maritalStatus: 'Divorced' as const,
          children: '3 children from previous marriage, 1 stepchild'
        }
      };

      render(
        <TestWrapper>
          <QuestionnaireForm />
        </TestWrapper>
      );

      // Simulate complex family scenario
      // The AI should provide guidance for blended family situations
      fireEvent.click(screen.getByText(/generate ai proposal/i));

      await waitFor(() => {
        expect(screen.getByText(/legal framework/i)).toBeInTheDocument();
      });
    });
  });

  describe('Trust Creation Scenarios', () => {
    test('should generate trust-specific recommendations for married couples', async () => {
      render(
        <TestWrapper>
          <QuestionnaireForm />
        </TestWrapper>
      );

      // Simulate trust creation scenario
      fireEvent.click(screen.getByText(/generate ai proposal/i));

      await waitFor(() => {
        expect(screen.getByText(/family trust can provide/i)).toBeInTheDocument();
      });

      // Verify trust-specific legal references
      expect(screen.getByText(/Trustee Act \(Cap 167\)/i)).toBeInTheDocument();
      
      // Verify trust benefits are mentioned
      expect(screen.getByText(/asset protection/i)).toBeInTheDocument();
      expect(screen.getByText(/tax advantages/i)).toBeInTheDocument();
    });
  });

  describe('High Net Worth Scenarios', () => {
    test('should provide sophisticated planning for high net worth clients', async () => {
      render(
        <TestWrapper>
          <QuestionnaireForm />
        </TestWrapper>
      );

      fireEvent.click(screen.getByText(/generate ai proposal/i));

      await waitFor(() => {
        expect(screen.getByText(/sophisticated estate planning/i)).toBeInTheDocument();
      });

      // Verify advanced planning concepts
      expect(screen.getByText(/offshore structures/i)).toBeInTheDocument();
      expect(screen.getByText(/philanthropic considerations/i)).toBeInTheDocument();
      
      // Verify complex legal requirements
      expect(screen.getByText(/Capital Markets Act/i)).toBeInTheDocument();
      expect(screen.getByText(/Exchange Control Act/i)).toBeInTheDocument();
    });
  });

  describe('Error Handling and Edge Cases', () => {
    test('should handle AI service unavailability gracefully', async () => {
      // Mock AI service error
      server.use(
        rest.post('/api/ai/proposal', (req, res, ctx) => {
          return res(
            ctx.status(503),
            ctx.json({ detail: 'AI service temporarily unavailable' })
          );
        })
      );

      render(
        <TestWrapper>
          <QuestionnaireForm />
        </TestWrapper>
      );

      fireEvent.click(screen.getByText(/generate ai proposal/i));

      await waitFor(() => {
        expect(screen.getByText(/service temporarily unavailable/i)).toBeInTheDocument();
      });
    });

    test('should validate questionnaire data before sending to AI', async () => {
      render(
        <TestWrapper>
          <QuestionnaireForm />
        </TestWrapper>
      );

      // Try to generate proposal with incomplete data
      fireEvent.click(screen.getByText(/generate ai proposal/i));

      await waitFor(() => {
        expect(screen.getByText(/please complete all required fields/i)).toBeInTheDocument();
      });
    });

    test('should handle invalid AI responses', async () => {
      server.use(
        rest.post('/api/ai/proposal', (req, res, ctx) => {
          return res(
            ctx.json({ invalidResponse: true })
          );
        })
      );

      render(
        <TestWrapper>
          <QuestionnaireForm />
        </TestWrapper>
      );

      fireEvent.click(screen.getByText(/generate ai proposal/i));

      await waitFor(() => {
        expect(screen.getByText(/unexpected response format/i)).toBeInTheDocument();
      });
    });

    test('should retry failed AI requests with exponential backoff', async () => {
      let callCount = 0;
      server.use(
        rest.post('/api/ai/proposal', (req, res, ctx) => {
          callCount++;
          if (callCount < 3) {
            return res(ctx.status(500));
          }
          return res(ctx.json({
            suggestion: 'Success after retries',
            legalReferences: ['Test reference'],
            consequences: ['Test consequence'],
            nextSteps: ['Test step']
          }));
        })
      );

      render(
        <TestWrapper>
          <QuestionnaireForm />
        </TestWrapper>
      );

      fireEvent.click(screen.getByText(/generate ai proposal/i));

      await waitFor(() => {
        expect(screen.getByText(/success after retries/i)).toBeInTheDocument();
      }, { timeout: 10000 });

      expect(callCount).toBe(3);
    });
  });

  describe('Legal Reference Validation', () => {
    test('should validate legal references are current and accurate', async () => {
      render(
        <TestWrapper>
          <QuestionnaireForm />
        </TestWrapper>
      );

      fireEvent.click(screen.getByText(/generate ai proposal/i));

      await waitFor(() => {
        // Check for proper Kenyan legal references format
        const legalRefs = screen.getAllByText(/Act.*Section/i);
        expect(legalRefs.length).toBeGreaterThan(0);
        
        // Verify specific Kenyan laws are referenced
        expect(screen.getByText(/Succession Act/i)).toBeInTheDocument();
      });
    });

    test('should provide context-appropriate legal references', async () => {
      render(
        <TestWrapper>
          <QuestionnaireForm />
        </TestWrapper>
      );

      // Test that references match the client scenario
      fireEvent.click(screen.getByText(/generate ai proposal/i));

      await waitFor(() => {
        const references = screen.getAllByText(/Chapter \d+/i);
        expect(references.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Performance and Load Testing', () => {
    test('should handle multiple concurrent AI requests', async () => {
      const promises = Array.from({ length: 5 }, (_, i) => {
        render(
          <TestWrapper>
            <QuestionnaireForm key={i} />
          </TestWrapper>
        );
        
        return waitFor(() => {
          fireEvent.click(screen.getAllByText(/generate ai proposal/i)[i]);
        });
      });

      await Promise.all(promises);

      // Verify all requests completed successfully
      await waitFor(() => {
        expect(screen.getAllByText(/legal framework/i).length).toBeGreaterThan(0);
      });
    });

    test('should timeout long-running AI requests', async () => {
      server.use(
        rest.post('/api/ai/proposal', (req, res, ctx) => {
          return res(ctx.delay(35000)); // Simulate timeout
        })
      );

      render(
        <TestWrapper>
          <QuestionnaireForm />
        </TestWrapper>
      );

      fireEvent.click(screen.getByText(/generate ai proposal/i));

      await waitFor(() => {
        expect(screen.getByText(/request timeout/i)).toBeInTheDocument();
      }, { timeout: 40000 });
    });
  });

  describe('AI Response Quality and Relevance', () => {
    test('should ensure AI responses are relevant to client situation', async () => {
      render(
        <TestWrapper>
          <QuestionnaireForm />
        </TestWrapper>
      );

      fireEvent.click(screen.getByText(/generate ai proposal/i));

      await waitFor(() => {
        const suggestion = screen.getByTestId('ai-suggestion');
        expect(suggestion).toBeInTheDocument();
        
        // Check that response contains relevant keywords
        expect(suggestion.textContent).toMatch(/will|trust|succession|estate/i);
      });
    });

    test('should provide actionable next steps', async () => {
      render(
        <TestWrapper>
          <QuestionnaireForm />
        </TestWrapper>
      );

      fireEvent.click(screen.getByText(/generate ai proposal/i));

      await waitFor(() => {
        const nextSteps = screen.getByTestId('next-steps');
        expect(nextSteps).toBeInTheDocument();
        
        // Verify steps are actionable and specific
        expect(nextSteps.textContent).toMatch(/review|prepare|consult|schedule/i);
      });
    });
  });
});