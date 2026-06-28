import api from './api';

export interface CreateProjectRequest {
  name: string;
  base_url: string;
  description?: string;
}

export interface ProjectResponse {
  id: string;
  user_id: string;
  name: string;
  base_url: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export const projectService = {
  list: async (): Promise<ProjectResponse[]> => {
    const response = await api.get<ProjectResponse[]>('/projects');
    return response.data;
  },

  get: async (id: string): Promise<ProjectResponse> => {
    const response = await api.get<ProjectResponse>(`/projects/${id}`);
    return response.data;
  },

  create: async (data: CreateProjectRequest): Promise<ProjectResponse> => {
    const response = await api.post<ProjectResponse>('/projects', data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/projects/${id}`);
  },
};