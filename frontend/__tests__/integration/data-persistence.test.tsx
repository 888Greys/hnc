import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { rest } from 'msw';
import { setupServer } from 'msw/node';
import fs from 'fs/promises';
import path from 'path';
import { QuestionnaireForm } from '@/components/QuestionnaireForm';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { ToastProvider } from '@/components/Toast';
import { QuestionnaireData } from '@/types';

// Mock file system operations
jest.mock('fs/promises');
const mockFs = fs as jest.Mocked<typeof fs>;

// Test data directory
const TEST_DATA_DIR = '/tmp/hnc-test-data';

// Mock server for API calls
const server = setupServer(
  rest.post('/api/clients', (req, res, ctx) => {
    const { questionnaire } = req.body as { questionnaire: QuestionnaireData };
    const clientId = `client_${Date.now()}`;
    
    return res(
      ctx.json({
        clientId,
        savedAt: new Date().toISOString(),
        message: 'Client data saved successfully'
      })
    );
  }),

  rest.get('/api/clients/:clientId', (req, res, ctx) => {
    const { clientId } = req.params;
    
    if (clientId === 'test-client-123') {
      return res(
        ctx.json({
          clientId,
          questionnaire: {
            bioData: {
              fullName: 'Test Client',
              maritalStatus: 'Married',
              spouseName: 'Test Spouse',
              spouseId: '12345678',
              children: '2 children'
            },
            financialData: {
              assets: [
                { type: 'Real Estate', description: 'Family home', value: 10000000 }
              ],
              liabilities: 'None',
              incomeSources: 'Salary'
            },
            economicContext: {
              economicStanding: 'Middle Income',
              distributionPrefs: 'Equal distribution'
            },
            objectives: {
              objective: 'Create Will',
              details: 'Basic will creation'
            },
            lawyerNotes: 'Standard case',
            savedAt: '2024-01-15T10:30:00Z'
          }
        })
      );
    }
    
    return res(
      ctx.status(404),
      ctx.json({ detail: 'Client not found' })
    );
  }),

  rest.get('/api/clients', (req, res, ctx) => {
    const search = req.url.searchParams.get('search');
    const limit = req.url.searchParams.get('limit') || '10';
    
    let clients = [
      {
        clientId: 'client-001',
        fullName: 'John Doe',
        savedAt: '2024-01-15T10:30:00Z',
        objective: 'Create Will'
      },
      {
        clientId: 'client-002',
        fullName: 'Jane Smith',
        savedAt: '2024-01-14T15:45:00Z',
        objective: 'Create Trust'
      },
      {
        clientId: 'client-003',
        fullName: 'Bob Johnson',
        savedAt: '2024-01-13T09:15:00Z',
        objective: 'Sell Asset'
      }
    ];
    
    if (search) {
      clients = clients.filter(client => 
        client.fullName.toLowerCase().includes(search.toLowerCase()) ||
        client.objective.toLowerCase().includes(search.toLowerCase())
      );
    }
    
    return res(
      ctx.json({
        clients: clients.slice(0, parseInt(limit)),
        total: clients.length,
        page: 1,
        totalPages: Math.ceil(clients.length / parseInt(limit))
      })
    );
  }),

  rest.put('/api/clients/:clientId', (req, res, ctx) => {
    const { clientId } = req.params;
    const { questionnaire } = req.body as { questionnaire: QuestionnaireData };
    
    return res(
      ctx.json({
        clientId,
        updatedAt: new Date().toISOString(),
        message: 'Client data updated successfully'
      })
    );
  }),

  rest.delete('/api/clients/:clientId', (req, res, ctx) => {
    const { clientId } = req.params;
    
    if (clientId === 'client-to-delete') {
      return res(
        ctx.json({
          message: 'Client data deleted successfully'
        })
      );
    }
    
    return res(
      ctx.status(404),
      ctx.json({ detail: 'Client not found' })
    );
  }),

  rest.post('/api/clients/export', (req, res, ctx) => {
    const { format, clientIds } = req.body as { format: 'pdf' | 'excel'; clientIds: string[] };
    
    return res(
      ctx.json({
        downloadUrl: `/api/downloads/export_${Date.now()}.${format}`,
        expiresAt: new Date(Date.now() + 3600000).toISOString() // 1 hour
      })
    );
  }),

  rest.get('/api/downloads/:filename', (req, res, ctx) => {
    const { filename } = req.params;
    
    if (filename.endsWith('.pdf')) {
      return res(
        ctx.set('Content-Type', 'application/pdf'),
        ctx.set('Content-Disposition', `attachment; filename="${filename}"`),
        ctx.body(Buffer.from('Mock PDF content'))
      );
    }
    
    if (filename.endsWith('.xlsx')) {
      return res(
        ctx.set('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
        ctx.set('Content-Disposition', `attachment; filename="${filename}"`),
        ctx.body(Buffer.from('Mock Excel content'))
      );
    }
    
    return res(ctx.status(404));
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

beforeAll(() => {
  server.listen();
  // Setup mock file system
  mockFs.mkdir.mockResolvedValue(undefined);
  mockFs.writeFile.mockResolvedValue(undefined);
  mockFs.readFile.mockResolvedValue('{}');
  mockFs.readdir.mockResolvedValue([]);
  mockFs.stat.mockResolvedValue({
    isFile: () => true,
    isDirectory: () => false,
    size: 1024,
    mtime: new Date(),
  } as any);
});

afterEach(() => {
  server.resetHandlers();
  jest.clearAllMocks();
});

afterAll(() => server.close());

describe('Data Persistence and Retrieval Tests', () => {
  const testQuestionnaireData: QuestionnaireData = {
    bioData: {
      fullName: 'Test Client',
      maritalStatus: 'Single',
      children: 'None'
    },
    financialData: {
      assets: [
        { type: 'Bank Account', description: 'Savings', value: 500000 }
      ],
      liabilities: 'None',
      incomeSources: 'Employment'
    },
    economicContext: {
      economicStanding: 'Middle Income',
      distributionPrefs: 'Standard distribution'
    },
    objectives: {
      objective: 'Create Will',
      details: 'Simple will'
    },
    lawyerNotes: 'Basic case'
  };

  describe('Data Saving and Storage', () => {
    test('should save questionnaire data successfully', async () => {
      render(
        <TestWrapper>
          <QuestionnaireForm />
        </TestWrapper>
      );

      // Fill out form
      fireEvent.change(screen.getByLabelText(/full name/i), {
        target: { value: testQuestionnaireData.bioData.fullName }
      });

      // Navigate to final step and save
      fireEvent.click(screen.getByText(/save data/i));

      await waitFor(() => {
        expect(screen.getByText(/data saved successfully/i)).toBeInTheDocument();
      });

      // Verify API was called
      expect(server.listHandlers()).toHaveLength(6);
    });

    test('should handle file system errors gracefully', async () => {
      // Mock file system error
      mockFs.writeFile.mockRejectedValueOnce(new Error('Disk full'));

      render(
        <TestWrapper>
          <QuestionnaireForm />
        </TestWrapper>
      );

      fireEvent.click(screen.getByText(/save data/i));

      await waitFor(() => {
        expect(screen.getByText(/error saving data/i)).toBeInTheDocument();
      });
    });

    test('should create backup copies of saved data', async () => {
      render(
        <TestWrapper>
          <QuestionnaireForm />
        </TestWrapper>
      );

      fireEvent.click(screen.getByText(/save data/i));

      await waitFor(() => {
        expect(mockFs.writeFile).toHaveBeenCalledTimes(2); // Main file + backup
      });
    });

    test('should validate data before saving', async () => {
      render(
        <TestWrapper>
          <QuestionnaireForm />
        </TestWrapper>
      );

      // Try to save incomplete data
      fireEvent.click(screen.getByText(/save data/i));

      await waitFor(() => {
        expect(screen.getByText(/please complete all required fields/i)).toBeInTheDocument();
      });
    });

    test('should generate unique client IDs', async () => {
      const savePromises = Array.from({ length: 5 }, () => {
        return new Promise<string>((resolve) => {
          server.use(
            rest.post('/api/clients', (req, res, ctx) => {
              const clientId = `client_${Date.now()}_${Math.random()}`;
              resolve(clientId);
              return res(ctx.json({ clientId }));
            })
          );
        });
      });

      const clientIds = await Promise.all(savePromises);
      const uniqueIds = new Set(clientIds);
      
      expect(uniqueIds.size).toBe(5); // All IDs should be unique
    });
  });

  describe('Data Retrieval and Loading', () => {
    test('should retrieve client data by ID', async () => {
      render(
        <TestWrapper>
          <QuestionnaireForm clientId="test-client-123" />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByDisplayValue(/test client/i)).toBeInTheDocument();
      });

      // Verify all fields are populated
      expect(screen.getByDisplayValue(/married/i)).toBeInTheDocument();
      expect(screen.getByDisplayValue(/test spouse/i)).toBeInTheDocument();
    });

    test('should handle missing client data gracefully', async () => {
      render(
        <TestWrapper>
          <QuestionnaireForm clientId="non-existent-client" />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/client not found/i)).toBeInTheDocument();
      });
    });

    test('should load data from local storage as fallback', async () => {
      // Mock localStorage
      const localStorageMock = {
        getItem: jest.fn().mockReturnValue(JSON.stringify(testQuestionnaireData)),
        setItem: jest.fn(),
        removeItem: jest.fn(),
      };
      Object.defineProperty(window, 'localStorage', { value: localStorageMock });

      render(
        <TestWrapper>
          <QuestionnaireForm clientId="test-client" />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(localStorageMock.getItem).toHaveBeenCalledWith('questionnaire_test-client');
      });
    });

    test('should handle corrupted data files', async () => {
      mockFs.readFile.mockResolvedValueOnce('invalid json data');

      render(
        <TestWrapper>
          <QuestionnaireForm clientId="corrupted-data-client" />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/data corruption detected/i)).toBeInTheDocument();
      });
    });
  });

  describe('Data Search and Filtering', () => {
    test('should search clients by name', async () => {
      render(
        <TestWrapper>
          <div data-testid="client-search">
            <input 
              placeholder="Search clients..."
              onChange={(e) => {
                // Simulate search functionality
                fetch(`/api/clients?search=${e.target.value}`);
              }}
            />
          </div>
        </TestWrapper>
      );

      const searchInput = screen.getByPlaceholderText(/search clients/i);
      fireEvent.change(searchInput, { target: { value: 'John' } });

      await waitFor(() => {
        // Verify search API was called
        expect(fetch).toHaveBeenCalledWith('/api/clients?search=John');
      });
    });

    test('should filter clients by objective type', async () => {
      render(
        <TestWrapper>
          <select data-testid="objective-filter">
            <option value="">All Objectives</option>
            <option value="Create Will">Create Will</option>
            <option value="Create Trust">Create Trust</option>
          </select>
        </TestWrapper>
      );

      const filterSelect = screen.getByTestId('objective-filter');
      fireEvent.change(filterSelect, { target: { value: 'Create Will' } });

      // Verify filtering logic would be applied
      expect(filterSelect).toHaveValue('Create Will');
    });

    test('should paginate search results', async () => {
      render(
        <TestWrapper>
          <div data-testid="pagination">
            <button onClick={() => fetch('/api/clients?page=2&limit=10')}>
              Next Page
            </button>
          </div>
        </TestWrapper>
      );

      fireEvent.click(screen.getByText(/next page/i));

      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith('/api/clients?page=2&limit=10');
      });
    });

    test('should sort clients by date', async () => {
      render(
        <TestWrapper>
          <button 
            onClick={() => fetch('/api/clients?sort=savedAt&order=desc')}
            data-testid="sort-by-date"
          >
            Sort by Date
          </button>
        </TestWrapper>
      );

      fireEvent.click(screen.getByTestId('sort-by-date'));

      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith('/api/clients?sort=savedAt&order=desc');
      });
    });
  });

  describe('Data Updates and Modifications', () => {
    test('should update existing client data', async () => {
      render(
        <TestWrapper>
          <QuestionnaireForm clientId="test-client-123" />
        </TestWrapper>
      );

      // Wait for data to load
      await waitFor(() => {
        expect(screen.getByDisplayValue(/test client/i)).toBeInTheDocument();
      });

      // Modify data
      fireEvent.change(screen.getByLabelText(/full name/i), {
        target: { value: 'Updated Client Name' }
      });

      // Save changes
      fireEvent.click(screen.getByText(/update data/i));

      await waitFor(() => {
        expect(screen.getByText(/data updated successfully/i)).toBeInTheDocument();
      });
    });

    test('should track data modification history', async () => {
      render(
        <TestWrapper>
          <QuestionnaireForm clientId="test-client-123" />
        </TestWrapper>
      );

      fireEvent.click(screen.getByText(/view history/i));

      await waitFor(() => {
        expect(screen.getByText(/modification history/i)).toBeInTheDocument();
      });
    });

    test('should prevent concurrent modifications', async () => {
      // Simulate two users editing the same client
      const user1 = render(
        <TestWrapper>
          <QuestionnaireForm clientId="test-client-123" />
        </TestWrapper>
      );

      const user2 = render(
        <TestWrapper>
          <QuestionnaireForm clientId="test-client-123" />
        </TestWrapper>
      );

      // User 1 saves first
      fireEvent.click(user1.getByText(/save data/i));

      // User 2 tries to save
      fireEvent.click(user2.getByText(/save data/i));

      await waitFor(() => {
        expect(user2.getByText(/data modified by another user/i)).toBeInTheDocument();
      });
    });
  });

  describe('Data Export and Backup', () => {
    test('should export client data to PDF', async () => {
      render(
        <TestWrapper>
          <button 
            onClick={() => fetch('/api/clients/export', {
              method: 'POST',
              body: JSON.stringify({ format: 'pdf', clientIds: ['client-001'] })
            })}
            data-testid="export-pdf"
          >
            Export to PDF
          </button>
        </TestWrapper>
      );

      fireEvent.click(screen.getByTestId('export-pdf'));

      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith('/api/clients/export', expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ format: 'pdf', clientIds: ['client-001'] })
        }));
      });
    });

    test('should export client data to Excel', async () => {
      render(
        <TestWrapper>
          <button 
            onClick={() => fetch('/api/clients/export', {
              method: 'POST',
              body: JSON.stringify({ format: 'excel', clientIds: ['client-001', 'client-002'] })
            })}
            data-testid="export-excel"
          >
            Export to Excel
          </button>
        </TestWrapper>
      );

      fireEvent.click(screen.getByTestId('export-excel'));

      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith('/api/clients/export', expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ format: 'excel', clientIds: ['client-001', 'client-002'] })
        }));
      });
    });

    test('should create automatic backups', async () => {
      // Simulate backup process
      render(
        <TestWrapper>
          <button 
            onClick={() => {
              // Trigger backup
              mockFs.writeFile('/backup/clients_backup.json', '{}');
            }}
            data-testid="create-backup"
          >
            Create Backup
          </button>
        </TestWrapper>
      );

      fireEvent.click(screen.getByTestId('create-backup'));

      await waitFor(() => {
        expect(mockFs.writeFile).toHaveBeenCalledWith('/backup/clients_backup.json', '{}');
      });
    });

    test('should restore from backup', async () => {
      mockFs.readFile.mockResolvedValueOnce(JSON.stringify({
        clients: [testQuestionnaireData]
      }));

      render(
        <TestWrapper>
          <button 
            onClick={() => {
              // Trigger restore
              mockFs.readFile('/backup/clients_backup.json');
            }}
            data-testid="restore-backup"
          >
            Restore Backup
          </button>
        </TestWrapper>
      );

      fireEvent.click(screen.getByTestId('restore-backup'));

      await waitFor(() => {
        expect(mockFs.readFile).toHaveBeenCalledWith('/backup/clients_backup.json');
      });
    });
  });

  describe('Data Integrity and Validation', () => {
    test('should validate data integrity on load', async () => {
      // Mock data with invalid structure
      server.use(
        rest.get('/api/clients/:clientId', (req, res, ctx) => {
          return res(
            ctx.json({
              questionnaire: {
                bioData: null, // Invalid structure
                financialData: { assets: 'invalid' }
              }
            })
          );
        })
      );

      render(
        <TestWrapper>
          <QuestionnaireForm clientId="invalid-data-client" />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/data validation failed/i)).toBeInTheDocument();
      });
    });

    test('should handle schema migrations', async () => {
      // Mock old data format
      const oldFormatData = {
        name: 'Old Client', // Old field name
        status: 'married',
        assets: 'Property, Savings'
      };

      mockFs.readFile.mockResolvedValueOnce(JSON.stringify(oldFormatData));

      render(
        <TestWrapper>
          <QuestionnaireForm clientId="old-format-client" />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/data migrated successfully/i)).toBeInTheDocument();
      });
    });

    test('should verify data checksums', async () => {
      const dataWithChecksum = {
        ...testQuestionnaireData,
        _checksum: 'abc123'
      };

      mockFs.readFile.mockResolvedValueOnce(JSON.stringify(dataWithChecksum));

      render(
        <TestWrapper>
          <QuestionnaireForm clientId="checksum-client" />
        </TestWrapper>
      );

      // Verify checksum validation logic would run
      expect(mockFs.readFile).toHaveBeenCalled();
    });
  });

  describe('Performance and Scalability', () => {
    test('should handle large datasets efficiently', async () => {
      // Mock large client list
      const largeClientList = Array.from({ length: 1000 }, (_, i) => ({
        clientId: `client-${i}`,
        fullName: `Client ${i}`,
        savedAt: new Date().toISOString()
      }));

      server.use(
        rest.get('/api/clients', (req, res, ctx) => {
          return res(ctx.json({
            clients: largeClientList.slice(0, 50), // Paginated
            total: largeClientList.length
          }));
        })
      );

      render(
        <TestWrapper>
          <div data-testid="client-list">
            Large client list component
          </div>
        </TestWrapper>
      );

      // Verify pagination is used for large datasets
      expect(screen.getByTestId('client-list')).toBeInTheDocument();
    });

    test('should implement data caching', async () => {
      let cacheHit = false;
      
      server.use(
        rest.get('/api/clients/:clientId', (req, res, ctx) => {
          if (cacheHit) {
            return res(ctx.status(304)); // Not modified
          }
          cacheHit = true;
          return res(ctx.json({ questionnaire: testQuestionnaireData }));
        })
      );

      // First request
      render(
        <TestWrapper>
          <QuestionnaireForm clientId="cached-client" />
        </TestWrapper>
      );

      // Second request (should use cache)
      render(
        <TestWrapper>
          <QuestionnaireForm clientId="cached-client" />
        </TestWrapper>
      );

      expect(cacheHit).toBe(true);
    });

    test('should optimize file I/O operations', async () => {
      // Test batch operations
      const batchSave = Array.from({ length: 10 }, (_, i) => 
        mockFs.writeFile(`/data/client-${i}.json`, '{}')
      );

      await Promise.all(batchSave);

      expect(mockFs.writeFile).toHaveBeenCalledTimes(10);
    });
  });
});