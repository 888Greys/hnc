import { z } from 'zod';

// Kenyan-specific validation patterns
export const KENYAN_ID_PATTERN = /^\d{7,8}$/; // Kenyan ID numbers are 7-8 digits
export const KENYAN_PHONE_PATTERN = /^(?:\+254|254|0)?([17]\d{8})$/; // Kenyan phone numbers
export const KRA_PIN_PATTERN = /^[A-Z]\d{9}[A-Z]$/; // KRA PIN format
export const POSTAL_CODE_PATTERN = /^\d{5}$/; // Kenyan postal codes

// Common validation messages
export const VALIDATION_MESSAGES = {
  required: 'This field is required',
  invalidEmail: 'Please enter a valid email address',
  invalidPhone: 'Please enter a valid Kenyan phone number',
  invalidId: 'Please enter a valid Kenyan ID number (7-8 digits)',
  invalidKraPin: 'Please enter a valid KRA PIN (e.g., A123456789B)',
  invalidPostalCode: 'Please enter a valid postal code (5 digits)',
  invalidAmount: 'Please enter a valid amount',
  minimumAge: 'Must be at least 18 years old',
  maximumAge: 'Age cannot exceed 120 years',
  invalidDate: 'Please enter a valid date',
  futureDate: 'Date cannot be in the future',
  invalidAssetValue: 'Asset value must be greater than 0',
  invalidPercentage: 'Percentage must be between 0 and 100',
};

// Custom validation functions
export const validateKenyanId = (id: string): boolean => {
  if (!id || typeof id !== 'string') return false;
  return KENYAN_ID_PATTERN.test(id.replace(/\s/g, ''));
};

export const validateKenyanPhone = (phone: string): boolean => {
  if (!phone || typeof phone !== 'string') return false;
  return KENYAN_PHONE_PATTERN.test(phone.replace(/[\s\-]/g, ''));
};

export const validateKraPin = (pin: string): boolean => {
  if (!pin || typeof pin !== 'string') return false;
  return KRA_PIN_PATTERN.test(pin.toUpperCase().replace(/\s/g, ''));
};

export const validateAge = (birthDate: string | Date): { isValid: boolean; age?: number; error?: string } => {
  try {
    const birth = new Date(birthDate);
    const today = new Date();
    
    if (birth > today) {
      return { isValid: false, error: VALIDATION_MESSAGES.futureDate };
    }
    
    const age = today.getFullYear() - birth.getFullYear();
    const monthDiff = today.getMonth() - birth.getMonth();
    
    const adjustedAge = monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate()) 
      ? age - 1 
      : age;
    
    if (adjustedAge < 18) {
      return { isValid: false, age: adjustedAge, error: VALIDATION_MESSAGES.minimumAge };
    }
    
    if (adjustedAge > 120) {
      return { isValid: false, age: adjustedAge, error: VALIDATION_MESSAGES.maximumAge };
    }
    
    return { isValid: true, age: adjustedAge };
  } catch {
    return { isValid: false, error: VALIDATION_MESSAGES.invalidDate };
  }
};

// Enhanced Zod schemas with Kenyan legal requirements
export const kenyanIdSchema = z.string()
  .min(1, VALIDATION_MESSAGES.required)
  .refine(validateKenyanId, VALIDATION_MESSAGES.invalidId);

export const kenyanPhoneSchema = z.string()
  .min(1, VALIDATION_MESSAGES.required)
  .refine(validateKenyanPhone, VALIDATION_MESSAGES.invalidPhone);

export const kraPinSchema = z.string()
  .optional()
  .refine((val) => !val || validateKraPin(val), VALIDATION_MESSAGES.invalidKraPin);

export const emailSchema = z.string()
  .min(1, VALIDATION_MESSAGES.required)
  .email(VALIDATION_MESSAGES.invalidEmail);

export const currencyAmountSchema = z.number()
  .min(0, VALIDATION_MESSAGES.invalidAmount)
  .max(1000000000000, 'Amount is too large'); // 1 trillion KES limit

export const percentageSchema = z.number()
  .min(0, VALIDATION_MESSAGES.invalidPercentage)
  .max(100, VALIDATION_MESSAGES.invalidPercentage);

// Enhanced Asset schema with Kenyan legal considerations
export const assetSchema = z.object({
  type: z.enum(['Real Estate', 'Bank Account', 'Shares', 'Vehicle', 'Business', 'Livestock', 'Other']),
  description: z.string()
    .min(3, 'Description must be at least 3 characters')
    .max(500, 'Description cannot exceed 500 characters'),
  value: currencyAmountSchema.refine(val => val > 0, VALIDATION_MESSAGES.invalidAssetValue),
  location: z.string()
    .min(2, 'Location must be at least 2 characters')
    .max(200, 'Location cannot exceed 200 characters')
    .optional(),
  registrationNumber: z.string()
    .max(50, 'Registration number cannot exceed 50 characters')
    .optional(),
  encumbrances: z.string()
    .max(1000, 'Encumbrances description cannot exceed 1000 characters')
    .optional(),
});

// Enhanced Bio Data schema
export const bioDataSchema = z.object({
  fullName: z.string()
    .min(2, 'Full name must be at least 2 characters')
    .max(100, 'Full name cannot exceed 100 characters')
    .regex(/^[a-zA-Z\s\-'\.]+$/, 'Full name can only contain letters, spaces, hyphens, apostrophes, and dots'),
  
  idNumber: kenyanIdSchema,
  
  dateOfBirth: z.string()
    .min(1, VALIDATION_MESSAGES.required)
    .refine((date) => {
      const validation = validateAge(date);
      return validation.isValid;
    }, {
      message: 'Please enter a valid date of birth'
    }),
  
  maritalStatus: z.enum(['Single', 'Married', 'Divorced', 'Widowed', 'Separated']),
  
  spouseName: z.string()
    .max(100, 'Spouse name cannot exceed 100 characters')
    .optional(),
  
  spouseId: kenyanIdSchema.optional(),
  
  children: z.string()
    .max(2000, 'Children details cannot exceed 2000 characters')
    .optional(),
  
  phoneNumber: kenyanPhoneSchema,
  
  email: emailSchema.optional(),
  
  kraPin: kraPinSchema,
  
  address: z.object({
    street: z.string().max(200, 'Street address cannot exceed 200 characters').optional(),
    city: z.string().max(100, 'City cannot exceed 100 characters').optional(),
    county: z.string().max(100, 'County cannot exceed 100 characters').optional(),
    postalCode: z.string()
      .regex(POSTAL_CODE_PATTERN, VALIDATION_MESSAGES.invalidPostalCode)
      .optional(),
  }).optional(),
  
  occupation: z.string()
    .max(100, 'Occupation cannot exceed 100 characters')
    .optional(),
  
  employer: z.string()
    .max(200, 'Employer name cannot exceed 200 characters')
    .optional(),
}).refine((data) => {
  // If married, spouse name and ID should be provided
  if (data.maritalStatus === 'Married' && (!data.spouseName || !data.spouseId)) {
    return false;
  }
  return true;
}, {
  message: 'Spouse name and ID are required for married individuals',
  path: ['spouseName']
});

// Enhanced Financial Data schema
export const financialDataSchema = z.object({
  assets: z.array(assetSchema)
    .min(1, 'At least one asset must be specified')
    .max(50, 'Cannot specify more than 50 assets'),
  
  liabilities: z.string()
    .max(2000, 'Liabilities description cannot exceed 2000 characters')
    .optional(),
  
  incomeSources: z.string()
    .max(2000, 'Income sources description cannot exceed 2000 characters')
    .optional(),
  
  monthlyIncome: currencyAmountSchema.optional(),
  
  monthlyExpenses: currencyAmountSchema.optional(),
  
  bankAccounts: z.array(z.object({
    bankName: z.string().max(100, 'Bank name cannot exceed 100 characters'),
    accountNumber: z.string().max(20, 'Account number cannot exceed 20 characters'),
    accountType: z.enum(['Savings', 'Current', 'Fixed Deposit', 'Other']),
    balance: currencyAmountSchema.optional(),
  })).optional(),
}).refine((data) => {
  const totalAssetValue = data.assets.reduce((sum, asset) => sum + asset.value, 0);
  return totalAssetValue > 0;
}, {
  message: 'Total asset value must be greater than 0',
  path: ['assets']
});

// Economic Context schema
export const economicContextSchema = z.object({
  economicStanding: z.enum(['Low Income', 'Middle Income', 'High Net Worth']),
  
  distributionPrefs: z.string()
    .max(1000, 'Distribution preferences cannot exceed 1000 characters')
    .optional(),
  
  taxConsiderations: z.string()
    .max(1000, 'Tax considerations cannot exceed 1000 characters')
    .optional(),
  
  familyDependents: z.number()
    .int('Number of dependents must be a whole number')
    .min(0, 'Number of dependents cannot be negative')
    .max(20, 'Number of dependents seems unusually high')
    .optional(),
});

// Client Objectives schema
export const objectivesSchema = z.object({
  objective: z.enum([
    'Create Will',
    'Create Living Will',
    'Create Share Transfer Will',
    'Create Trust',
    'Sell Asset',
    'Succession Planning',
    'Tax Planning',
    'Other'
  ]),
  
  details: z.string()
    .min(10, 'Please provide at least 10 characters of detail about your objectives')
    .max(2000, 'Objective details cannot exceed 2000 characters'),
  
  timeline: z.enum(['Immediate', 'Within 3 months', 'Within 6 months', 'Within 1 year', 'No rush']).optional(),
  
  budget: currencyAmountSchema.optional(),
  
  specialRequirements: z.string()
    .max(1000, 'Special requirements cannot exceed 1000 characters')
    .optional(),
});

// Lawyer Notes schema
export const lawyerNotesSchema = z.object({
  notes: z.string()
    .max(5000, 'Lawyer notes cannot exceed 5000 characters')
    .optional(),
  
  riskAssessment: z.enum(['Low', 'Medium', 'High']).optional(),
  
  urgency: z.enum(['Low', 'Medium', 'High', 'Critical']).optional(),
  
  estimatedCost: currencyAmountSchema.optional(),
  
  estimatedDuration: z.string()
    .max(100, 'Estimated duration cannot exceed 100 characters')
    .optional(),
});

// Complete Questionnaire schema
export const questionnaireSchema = z.object({
  bioData: bioDataSchema,
  financialData: financialDataSchema,
  economicContext: economicContextSchema,
  objectives: objectivesSchema,
  lawyerNotes: lawyerNotesSchema.optional(),
});

// Validation utility functions
export const validateField = <T>(
  schema: z.ZodSchema<T>,
  value: unknown
): { isValid: boolean; error?: string; data?: T } => {
  try {
    const data = schema.parse(value);
    return { isValid: true, data };
  } catch (error) {
    if (error instanceof z.ZodError) {
      const firstError = error.issues[0];
      return { 
        isValid: false, 
        error: firstError.message 
      };
    }
    return { 
      isValid: false, 
      error: 'Validation failed' 
    };
  }
};

export const validatePartial = <T>(
  schema: z.ZodSchema<T>,
  value: unknown
): { isValid: boolean; errors: Record<string, string>; data?: Partial<T> } => {
  try {
    const data = schema.parse(value);
    return { isValid: true, data, errors: {} };
  } catch (error) {
    if (error instanceof z.ZodError) {
      const errors: Record<string, string> = {};
      
      error.issues.forEach((err) => {
        const path = err.path.join('.');
        errors[path] = err.message;
      });
      
      return { 
        isValid: false, 
        errors,
        data: value as Partial<T>
      };
    }
    return { 
      isValid: false, 
      errors: { general: 'Validation failed' }
    };
  }
};

// Asset value calculation utilities
export const calculateTotalAssetValue = (assets: z.infer<typeof assetSchema>[]): number => {
  return assets.reduce((total, asset) => total + asset.value, 0);
};

export const formatKenyanCurrency = (amount: number): string => {
  return new Intl.NumberFormat('en-KE', {
    style: 'currency',
    currency: 'KES',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
};

export const calculateEstimatedTax = (assetValue: number): number => {
  // Simplified Kenyan inheritance tax calculation
  // Actual calculation would be more complex and require professional advice
  const taxFreeThreshold = 5000000; // KES 5M
  
  if (assetValue <= taxFreeThreshold) {
    return 0;
  }
  
  // Simplified 5% on amount above threshold
  return (assetValue - taxFreeThreshold) * 0.05;
};

export type ValidationResult<T> = {
  isValid: boolean;
  data?: T;
  errors?: Record<string, string>;
  warnings?: string[];
};