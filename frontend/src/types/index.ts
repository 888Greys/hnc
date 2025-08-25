export interface ClientBioData {
  fullName: string;
  maritalStatus: 'Single' | 'Married' | 'Divorced' | 'Widowed';
  spouseName?: string;
  spouseId?: string;
  children: string;
}

export interface Asset {
  type: 'Real Estate' | 'Bank Account' | 'Shares' | 'Other';
  description: string;
  value: number;
}

export interface FinancialData {
  assets: Asset[];
  liabilities: string;
  incomeSources: string;
}

export interface EconomicContext {
  economicStanding: 'High Net Worth' | 'Middle Income' | 'Low Income';
  distributionPrefs: string;
}

export interface ClientObjectives {
  objective: 'Create Will' | 'Create Living Will' | 'Create Share Transfer Will' | 'Create Trust' | 'Sell Asset' | 'Other';
  details: string;
}

export interface QuestionnaireData {
  bioData: ClientBioData;
  financialData: FinancialData;
  economicContext: EconomicContext;
  objectives: ClientObjectives;
  lawyerNotes: string;
  savedAt?: string;
}

export interface AIProposal {
  suggestion: string;
  legalReferences: string[];
  consequences: string[];
  nextSteps: string[];
}

export interface LoginData {
  username: string;
  password: string;
}

// Alias for consistency with API service
export type LoginRequest = LoginData;

export interface AIProposalRequest {
  questionnaireData: QuestionnaireData;
  distributionPrefs: string;
}

export interface UserSession {
  username: string;
  loginTime: string;
  isAuthenticated: boolean;
}