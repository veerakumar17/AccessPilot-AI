import api from './api';

export interface StartAuditRequest {
  project_id: string;
  target_url?: string;
}

export interface AuditResponse {
  id: string;
  project_id: string;
  status: string;
  error_message: string | null;
  started_at: string;
  completed_at: string | null;
}

export interface AuditListResponse {
  id: string;
  project_id: string;
  project_name: string;
  status: string;
  error_message: string | null;
  started_at: string;
  completed_at: string | null;
  accessibility_score: number | null;
}

export interface AuditSummaryResponse {
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

export interface PageResponse {
  id: string;
  audit_id: string;
  url: string;
  title: string;
  violation_count: number;
  crawled_at: string;
}

export interface ViolationResponse {
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

export const auditService = {
  list: async (): Promise<AuditListResponse[]> => {
    const response = await api.get<AuditListResponse[]>('/audits');
    return response.data;
  },

  start: async (data: StartAuditRequest): Promise<AuditResponse> => {
    const response = await api.post<AuditResponse>('/audits', data);
    return response.data;
  },

  get: async (id: string): Promise<AuditResponse> => {
    const response = await api.get<AuditResponse>(`/audits/${id}`);
    return response.data;
  },

  getSummary: async (id: string): Promise<AuditSummaryResponse> => {
    const response = await api.get<AuditSummaryResponse>(`/audits/${id}/summary`);
    return response.data;
  },

  getPages: async (id: string): Promise<PageResponse[]> => {
    const response = await api.get<PageResponse[]>(`/audits/${id}/pages`);
    return response.data;
  },

  getViolations: async (id: string): Promise<ViolationResponse[]> => {
    const response = await api.get<ViolationResponse[]>(`/audits/${id}/violations`);
    return response.data;
  },
};