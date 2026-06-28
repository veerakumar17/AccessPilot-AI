import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Search, Globe, Calendar, Trash2, Play, ArrowRight, History } from 'lucide-react';
import Card from '../components/ui/Card';
import Modal from '../components/ui/Modal';
import EmptyState from '../components/ui/EmptyState';
import { CardSkeleton } from '../components/ui/LoadingSkeleton';
import { useProjects, useCreateProject, useDeleteProject, useStartAudit } from '../hooks/useApi';
import type { ProjectResponse } from '../services/projectService';

const ProjectsPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newProject, setNewProject] = useState({ name: '', base_url: '', description: '' });

  const { data: projects, isLoading, isError } = useProjects();
  const createProject = useCreateProject();
  const deleteProject = useDeleteProject();
  const startAudit = useStartAudit();
  const [selectedProjectForAudit, setSelectedProjectForAudit] = useState<string>('');
  const [showAuditModal, setShowAuditModal] = useState(false);

  const filtered = (projects || []).filter((p) =>
    p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    p.base_url.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    createProject.mutate(newProject, {
      onSuccess: () => {
        setShowCreateModal(false);
        setNewProject({ name: '', base_url: '', description: '' });
      },
    });
  };

  const handleDelete = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm('Are you sure you want to delete this project?')) {
      deleteProject.mutate(id);
    }
  };

  const handleStartAudit = (projectId: string) => {
    setSelectedProjectForAudit(projectId);
    setShowAuditModal(true);
  };

  const handleConfirmAudit = () => {
    if (!selectedProjectForAudit) return;
    startAudit.mutate(
      { project_id: selectedProjectForAudit },
      {
        onSuccess: (data) => {
          setShowAuditModal(false);
          setSelectedProjectForAudit('');
          navigate(`/audits/${data.id}`);
        },
      }
    );
  };

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <CardSkeleton key={i} />
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <EmptyState
        title="Failed to load projects"
        description="There was an error loading your projects. Please try again."
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Search projects..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-navy-800 border border-navy-600 rounded-lg pl-9 pr-3 py-2 text-sm text-white placeholder-gray-400 focus:outline-none focus:border-accent"
          />
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 bg-accent hover:bg-accent-dark text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          <Plus size={16} />
          Create Project
        </button>
      </div>

      {/* Project Grid */}
      {filtered.length === 0 ? (
        <EmptyState
          title="No projects found"
          description={searchQuery ? 'Try a different search term' : 'Create your first project to get started'}
          action={
            !searchQuery ? (
              <button
                onClick={() => setShowCreateModal(true)}
                className="bg-accent hover:bg-accent-dark text-white px-4 py-2 rounded-lg text-sm font-medium"
              >
                Create Project
              </button>
            ) : undefined
          }
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((project: ProjectResponse) => (
            <Card
              key={project.id}
              className="hover:border-navy-400 group"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="p-2 rounded-lg bg-accent/10">
                  <Globe size={18} className="text-accent" />
                </div>
                <button
                  onClick={(e) => handleDelete(project.id, e)}
                  className="p-1.5 rounded-lg text-gray-500 hover:text-red-400 hover:bg-red-500/10 opacity-0 group-hover:opacity-100 transition-all"
                >
                  <Trash2 size={14} />
                </button>
              </div>
              <h3 className="font-semibold text-white mb-1">{project.name}</h3>
              <p className="text-xs text-gray-400 font-mono mb-3 truncate">{project.base_url}</p>
              <p className="text-sm text-gray-400 mb-4 line-clamp-2">{project.description || 'No description'}</p>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5 text-xs text-gray-500">
                  <Calendar size={12} />
                  {new Date(project.created_at).toLocaleDateString()}
                </div>
                <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-all">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleStartAudit(project.id);
                    }}
                    className="flex items-center gap-1 text-xs text-accent hover:text-accent-dark"
                  >
                    <Play size={10} />
                    Run Audit
                  </button>
                  <span
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate('/audits');
                    }}
                    className="text-xs text-gray-400 hover:text-white flex items-center gap-1 cursor-pointer"
                  >
                    <History size={10} />
                    History
                  </span>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Start Audit Modal */}
      <Modal
        isOpen={showAuditModal}
        onClose={() => {
          setShowAuditModal(false);
          setSelectedProjectForAudit('');
        }}
        title="Start New Audit"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1.5">Project</label>
            <select
              value={selectedProjectForAudit}
              onChange={(e) => setSelectedProjectForAudit(e.target.value)}
              className="w-full bg-navy-900 border border-navy-600 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-accent"
            >
              <option value="">Select a project...</option>
              {(projects || []).map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={() => {
                setShowAuditModal(false);
                setSelectedProjectForAudit('');
              }}
              className="px-4 py-2 text-sm text-gray-400 hover:text-white transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleConfirmAudit}
              disabled={!selectedProjectForAudit || startAudit.isPending}
              className="bg-accent hover:bg-accent-dark text-white px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-50"
            >
              {startAudit.isPending ? 'Starting...' : 'Start Audit'}
            </button>
          </div>
        </div>
      </Modal>

      {/* Create Project Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create New Project"
      >
        <form onSubmit={handleCreate} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1.5">Project Name</label>
            <input
              type="text"
              value={newProject.name}
              onChange={(e) => setNewProject({ ...newProject, name: e.target.value })}
              placeholder="My Project"
              className="w-full bg-navy-900 border border-navy-600 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-accent"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1.5">Base URL</label>
            <input
              type="url"
              value={newProject.base_url}
              onChange={(e) => setNewProject({ ...newProject, base_url: e.target.value })}
              placeholder="https://example.com"
              className="w-full bg-navy-900 border border-navy-600 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-accent"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1.5">Description</label>
            <textarea
              value={newProject.description}
              onChange={(e) => setNewProject({ ...newProject, description: e.target.value })}
              placeholder="Describe your project..."
              rows={3}
              className="w-full bg-navy-900 border border-navy-600 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-accent resize-none"
            />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={() => setShowCreateModal(false)}
              className="px-4 py-2 text-sm text-gray-400 hover:text-white transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createProject.isPending}
              className="bg-accent hover:bg-accent-dark text-white px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-50"
            >
              {createProject.isPending ? 'Creating...' : 'Create Project'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default ProjectsPage;