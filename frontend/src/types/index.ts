// ====== Frontend Display Types (for UI) ======

export interface User {
  id: string;
  name: string;
  email: string;
}

export interface Project {
  id: string;
  name: string;
  baseUrl: string;
  description: string;
  createdAt: string;
  updatedAt: string;
}

export interface Audit {
  id: string;
  projectId: string;
  projectName: string;
  status: 'completed' | 'in_progress' | 'failed' | 'pending';
  score: number;
  pagesScanned: number;
  totalViolations: number;
  criticalCount: number;
  seriousCount: number;
  moderateCount: number;
  minorCount: number;
  createdAt: string;
  completedAt: string | null;
}

export interface Violation {
  id: string;
  auditId: string;
  ruleId: string;
  severity: 'critical' | 'serious' | 'moderate' | 'minor';
  description: string;
  htmlSnippet: string;
  wcagCriterion: string;
  impact: string;
  aiExplanation: AiExplanation;
  aiFix: AiFix;
  disabilitySimulation: DisabilitySimulation;
}

export interface AiExplanation {
  plainEnglish: string;
  businessImpact: string;
  recommendation: string;
}

export interface AiFix {
  problem: string;
  recommendedFix: string;
  codeExample: string;
  implementationSteps: string[];
  priority: 'high' | 'medium' | 'low';
}

export interface DisabilitySimulation {
  blind: SimulationDetail;
  lowVision: SimulationDetail;
  motor: SimulationDetail;
  cognitive: SimulationDetail;
}

export interface SimulationDetail {
  severity: 'severe' | 'moderate' | 'mild' | 'none';
  explanation: string;
  userExperience: string;
}

export interface Report {
  id: string;
  auditId: string;
  projectName: string;
  score: number;
  grade: string;
  totalViolations: number;
  criticalCount: number;
  seriousCount: number;
  moderateCount: number;
  minorCount: number;
  summary: string;
  generatedAt: string;
}

export interface DashboardStats {
  totalProjects: number;
  totalAudits: number;
  accessibilityScore: number;
  criticalViolations: number;
  recentAudits: Audit[];
}

export type PageType = 'dashboard' | 'projects' | 'audit-history' | 'audit-details' | 'reports';

// ====== Backend API Types (mapped from snake_case responses) ======

export interface ApiUser {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  created_at: string;
}

export interface ApiProject {
  id: string;
  user_id: string;
  name: string;
  base_url: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface ApiAudit {
  id: string;
  project_id: string;
  status: string;
  error_message: string | null;
  started_at: string;
  completed_at: string | null;
}

export interface ApiAuditSummary {
  audit_id: string;
  project_id: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  error_message: string | null;
  accessibility_score: number | null;
  pages_scanned: number | null;
  total_violations: number | null;
  severity_breakdown: {
    critical: number;
    serious: number;
    moderate: number;
    minor: number;
  } | null;
  summary_text: string | null;
}

export interface ApiViolation {
  id: string;
  page_id: string;
  rule_id: string;
  severity: string;
  html_snippet: string | null;
  selector: string | null;
  wcag_criteria: string | null;
  ai_explanation: string | null;
  ai_fix: string | null;
  fix_type: string | null;
  ai_simulation: string | null;
  disability_types: string[];
  created_at: string;
}

export interface ApiReport {
  id: string;
  audit_id: string;
  accessibility_score: number;
  total_violations: number;
  critical_count: number;
  serious_count: number;
  moderate_count: number;
  minor_count: number;
  pages_scanned: number;
  summary_text: string;
  generated_at: string;
}