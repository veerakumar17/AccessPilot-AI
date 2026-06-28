import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { projectService, type ProjectResponse, type CreateProjectRequest } from '../services/projectService';
import { auditService, type AuditListResponse, type AuditSummaryResponse, type ViolationResponse, type PageResponse } from '../services/auditService';
import { reportService, type ReportResponse } from '../services/reportService';
import { useToast } from '../context/ToastContext';
import { getErrorMessage } from '../services/api';

// ====== Project Hooks ======

export const useProjects = () => {
  return useQuery<ProjectResponse[]>({
    queryKey: ['projects'],
    queryFn: projectService.list,
  });
};

export const useCreateProject = () => {
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  return useMutation({
    mutationFn: (data: CreateProjectRequest) => projectService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      showToast('success', 'Project created successfully');
    },
    onError: (error) => {
      showToast('error', getErrorMessage(error));
    },
  });
};

export const useDeleteProject = () => {
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  return useMutation({
    mutationFn: (id: string) => projectService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      showToast('success', 'Project deleted successfully');
    },
    onError: (error) => {
      showToast('error', getErrorMessage(error));
    },
  });
};

// ====== Audit Hooks ======

export const useAudits = () => {
  return useQuery<AuditListResponse[]>({
    queryKey: ['audits'],
    queryFn: auditService.list,
  });
};

export const useStartAudit = () => {
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  return useMutation({
    mutationFn: (data: { project_id: string; target_url?: string }) =>
      auditService.start(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['audits'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      showToast('info', 'Audit started successfully');
    },
    onError: (error) => {
      showToast('error', getErrorMessage(error));
    },
  });
};

export const useAuditSummary = (auditId: string | undefined) => {
  return useQuery<AuditSummaryResponse>({
    queryKey: ['auditSummary', auditId],
    queryFn: () => auditService.getSummary(auditId!),
    enabled: !!auditId,
    // Poll every 5 seconds while running/pending
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data && (data.status === 'running' || data.status === 'pending')) {
        return 5000;
      }
      return false;
    },
  });
};

export const useAuditViolations = (auditId: string | undefined, shouldPoll: boolean = false) => {
  return useQuery<ViolationResponse[]>({
    queryKey: ['auditViolations', auditId],
    queryFn: () => auditService.getViolations(auditId!),
    enabled: !!auditId,
    // Poll every 5 seconds while audit is running/pending so violations
    // appear as soon as the backend has them
    refetchInterval: shouldPoll ? 5000 : false,
  });
};

export const useAuditPages = (auditId: string | undefined) => {
  return useQuery<PageResponse[]>({
    queryKey: ['auditPages', auditId],
    queryFn: () => auditService.getPages(auditId!),
    enabled: !!auditId,
  });
};

// ====== Report Hooks ======

export const useReportDownload = () => {
  const { showToast } = useToast();

  return useMutation({
    mutationFn: async (auditId: string) => {
      const blob = await reportService.exportPdf(auditId);
      // Create download link and trigger download
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `audit_${auditId}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    },
    onSuccess: () => {
      showToast('success', 'PDF report exported successfully');
    },
    onError: (error) => {
      showToast('error', getErrorMessage(error));
    },
  });
};

export const useReport = (auditId: string | undefined) => {
  return useQuery<ReportResponse>({
    queryKey: ['report', auditId],
    queryFn: () => reportService.get(auditId!),
    enabled: !!auditId,
  });
};
