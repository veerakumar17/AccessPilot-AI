import api from './api';

export interface ReportResponse {
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

export const reportService = {
  get: async (auditId: string): Promise<ReportResponse> => {
    const response = await api.get<ReportResponse>(`/reports/${auditId}`);
    return response.data;
  },

  exportPdf: async (auditId: string): Promise<Blob> => {
    const response = await api.get<Blob>(`/reports/${auditId}/pdf`, {
      responseType: 'blob',
    });
    return response.data;
  },
};
