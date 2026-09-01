export type Role = "ADMIN" | "INSPECTOR";
export type ScanStatus = "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED";
export type ComplianceStatus = "COMPLIANT" | "NON_COMPLIANT" | "PARTIAL" | null;
export type RuleStatus = "PASS" | "FAIL" | "WARNING" | "NOT_APPLICABLE";

export interface AuthResponse {
  token: string;
  refreshToken: string;
  username: string;
  email: string;
  role: Role;
}

export interface UserProfile {
  id: string;
  username: string;
  email: string;
  role: Role;
  createdAt: string;
}

export interface Product {
  id: string;
  name: string;
  category: string;
  brand: string | null;
  createdBy: string;
  createdAt: string | null;
}

export interface ScanStatusResponse {
  id: string;
  status: ScanStatus;
  overallStatus: ComplianceStatus;
  errorMessage: string | null;
}

export interface ScanSummary {
  id: string;
  productName: string | null;
  status: ScanStatus;
  overallStatus: ComplianceStatus;
  createdAt: string;
}

export interface DeclarationView {
  id: string;
  declarationType: string;
  present: boolean;
  extractedValue: string | null;
  confidenceScore: number | null;
  boundingBox: string | null;
}

export interface ComplianceResultView {
  id: string;
  ruleCode: string;
  ruleDescription: string | null;
  status: RuleStatus;
  remarks: string | null;
}

export interface DetailedScan {
  scan: {
    id: string;
    status: ScanStatus;
    overallStatus: ComplianceStatus;
    complianceScore: number | null;
    ocrRawText: string | null;
    imageUrl: string | null;
    errorMessage: string | null;
    createdAt: string;
    processedAt: string | null;
  };
  product: {
    id: string;
    name: string;
    category: string;
    brand: string | null;
  } | null;
  declarations: DeclarationView[];
  complianceResults: ComplianceResultView[];
}

export interface DashboardStats {
  totalScans: number;
  compliant: number;
  nonCompliant: number;
  partial: number;
  scansLast7Days: number;
  scansLast30Days: number;
  topViolations: { ruleCode: string; count: number }[];
}

export interface Page<T> {
  content: T[];
  number: number;
  size: number;
  totalElements: number;
  totalPages: number;
  first: boolean;
  last: boolean;
}

export interface ApiError {
  timestamp?: string;
  status: number;
  error: string;
  message: string;
  fieldErrors?: Record<string, string>;
}
