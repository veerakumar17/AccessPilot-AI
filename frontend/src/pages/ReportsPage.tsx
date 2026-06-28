import React from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText, Eye, Calendar } from 'lucide-react';
import Card from '../components/ui/Card';
import EmptyState from '../components/ui/EmptyState';
import { CardSkeleton } from '../components/ui/LoadingSkeleton';
import { useAudits } from '../hooks/useApi';

const getGrade = (score: number | null): { letter: string; color: string } => {
  if (score === null) return { letter: '--', color: 'text-gray-500' };
  if (score >= 90) return { letter: 'A', color: 'text-green-400' };
  if (score >= 75) return { letter: 'B', color: 'text-blue-400' };
  if (score >= 60) return { letter: 'C', color: 'text-yellow-400' };
  if (score >= 40) return { letter: 'D', color: 'text-orange-400' };
  return { letter: 'F', color: 'text-red-400' };
};

const ReportsPage: React.FC = () => {
  const navigate = useNavigate();
  const { data: audits, isLoading } = useAudits();

  // Filter to only completed audits
  const completedAudits = (audits || []).filter((a) => a.status === 'completed');

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {Array.from({ length: 4 }).map((_, i) => (
          <CardSkeleton key={i} />
        ))}
      </div>
    );
  }

  if (!completedAudits || completedAudits.length === 0) {
    return (
      <EmptyState
        title="No reports available"
        description="Reports are generated after audits are completed. Start an audit from the Projects page first."
        icon={<FileText size={48} />}
      />
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {completedAudits.map((audit) => {
          const grade = getGrade(audit.accessibility_score);
          return (
            <Card key={audit.id} className="hover:border-navy-400">
              {/* Header */}
              <div className="flex items-start justify-between mb-6">
                <div>
                  <h3 className="text-lg font-semibold text-white mb-1">{audit.project_name}</h3>
                  <p className="text-xs text-gray-400 font-mono">
                    Audit: {audit.id.slice(0, 8)}...
                  </p>
                </div>
                <div className="text-right">
                  <div className={`text-3xl font-bold ${grade.color}`}>
                    {grade.letter}
                  </div>
                  <p className={`text-sm font-medium ${
                    audit.accessibility_score !== null
                      ? audit.accessibility_score >= 90 ? 'text-green-400'
                      : audit.accessibility_score >= 60 ? 'text-yellow-400'
                      : 'text-red-400'
                      : 'text-gray-500'
                  }`}>
                    {audit.accessibility_score !== null ? `${audit.accessibility_score}%` : 'No score yet'}
                  </p>
                </div>
              </div>

              {/* Completed Date */}
              <div className="mb-6 flex items-center gap-1.5 text-xs text-gray-400">
                <Calendar size={12} />
                Completed: {audit.completed_at ? new Date(audit.completed_at).toLocaleDateString() : '--'}
              </div>

              {/* Actions */}
              <div className="flex items-center justify-between pt-4 border-t border-navy-600">
                <button
                  onClick={() => navigate(`/audits/${audit.id}`)}
                  className="flex items-center gap-1.5 text-sm text-accent hover:text-accent-dark transition-colors"
                >
                  <Eye size={14} />
                  View Report
                </button>
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
};

export default ReportsPage;