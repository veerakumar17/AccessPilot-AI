import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Eye, Loader2, CheckCircle, XCircle, Clock } from 'lucide-react';
import Card from '../components/ui/Card';
import EmptyState from '../components/ui/EmptyState';
import { TableSkeleton } from '../components/ui/LoadingSkeleton';
import { useAudits } from '../hooks/useApi';
import type { AuditListResponse } from '../services/auditService';

const statusConfig: Record<string, { icon: React.ReactNode; color: string; label: string }> = {
  completed: {
    icon: <CheckCircle size={14} />,
    color: 'text-green-400',
    label: 'Completed',
  },
  failed: {
    icon: <XCircle size={14} />,
    color: 'text-red-400',
    label: 'Failed',
  },
  running: {
    icon: <Loader2 size={14} className="animate-spin" />,
    color: 'text-blue-400',
    label: 'Running',
  },
  pending: {
    icon: <Clock size={14} />,
    color: 'text-yellow-400',
    label: 'Pending',
  },
};

const AuditHistoryPage: React.FC = () => {
  const navigate = useNavigate();
  const [search, setSearch] = React.useState('');

  const { data: audits, isLoading } = useAudits();

  const filtered = (audits || []).filter((a) =>
    a.project_name.toLowerCase().includes(search.toLowerCase()) ||
    a.id.toLowerCase().includes(search.toLowerCase())
  );

  if (isLoading) {
    return (
      <Card className="p-0 overflow-hidden">
        <div className="p-6">
          <TableSkeleton rows={5} />
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between gap-3">
        <div className="relative flex-1 max-w-md">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Search audits by project name or ID..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-navy-800 border border-navy-600 rounded-lg pl-9 pr-3 py-2 text-sm text-white placeholder-gray-400 focus:outline-none focus:border-accent"
          />
        </div>
      </div>

      {/* Audit Table */}
      <Card className="p-0 overflow-hidden">
        {!audits || audits.length === 0 ? (
          <EmptyState
            title="No audit history"
            description="Start an audit from the Projects page to see history here."
          />
        ) : filtered.length === 0 ? (
          <EmptyState title="No matching audits" description="Try a different search term." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-navy-600">
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-400 uppercase tracking-wider">Audit ID</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-400 uppercase tracking-wider">Project</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-400 uppercase tracking-wider">Status</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-400 uppercase tracking-wider">Score</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-400 uppercase tracking-wider">Started</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-400 uppercase tracking-wider">Completed</th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-gray-400 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((audit: AuditListResponse) => {
                  const status = statusConfig[audit.status] || statusConfig.pending;
                  return (
                    <tr
                      key={audit.id}
                      className="border-b border-navy-700/50 hover:bg-navy-700/30 transition-colors"
                    >
                      <td className="px-4 py-3">
                        <span className="text-xs font-mono text-accent">{audit.id.slice(0, 8)}...</span>
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-white font-medium">{audit.project_name}</span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`flex items-center gap-1.5 text-xs ${status.color}`}>
                          {status.icon}
                          {status.label}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`text-sm font-semibold ${
                          audit.accessibility_score !== null
                            ? audit.accessibility_score >= 90 ? 'text-green-400'
                            : audit.accessibility_score >= 60 ? 'text-yellow-400'
                            : 'text-red-400'
                            : 'text-gray-500'
                        }`}>
                          {audit.accessibility_score !== null ? `${audit.accessibility_score}%` : '--'}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-xs text-gray-400">
                          {new Date(audit.started_at).toLocaleDateString()}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-xs text-gray-400">
                          {audit.completed_at ? new Date(audit.completed_at).toLocaleDateString() : '--'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/audits/${audit.id}`);
                          }}
                          className="inline-flex items-center gap-1.5 bg-accent/10 hover:bg-accent/20 text-accent text-xs font-medium px-3 py-1.5 rounded-lg transition-colors"
                        >
                          <Eye size={12} />
                          View Details
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Note about starting new audits */}
      {audits && audits.length > 0 && (
        <p className="text-xs text-gray-500 text-center">
          To start a new audit, go to the{' '}
          <button onClick={() => navigate('/projects')} className="text-accent hover:underline">
            Projects
          </button>{' '}
          page.
        </p>
      )}
    </div>
  );
};

export default AuditHistoryPage;