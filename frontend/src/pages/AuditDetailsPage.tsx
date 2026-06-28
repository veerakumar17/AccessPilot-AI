import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Target,
  FileText,
  AlertTriangle,
  ChevronDown,
  ChevronRight,
  Brain,
  Wrench,
  Eye,
  EyeOff,
  Lightbulb,
  Code,
  ListChecks,
  AlertCircle,
  Users,
  Mouse,
  BrainCircuit,
  ExternalLink,
  Loader2,
  Download,
} from 'lucide-react';
import Card from '../components/ui/Card';
import { CardSkeleton } from '../components/ui/LoadingSkeleton';
import { useAuditSummary, useAuditViolations, useReportDownload } from '../hooks/useApi';
import { getSeverityColor, getPriorityColor } from '../data/mockData';
import type { ViolationResponse } from '../services/auditService';

// ====== Parsed types from backend JSON strings ======

interface AiExplanationParsed {
  plain_english?: string;
  business_impact?: string;
  recommendation?: string;
}

interface AiFixParsed {
  problem?: string;
  recommended_fix?: string;
  code_example?: string;
  implementation_steps?: string[];
  priority?: string;
}

interface SimulationGroup {
  disability: string;
  impact: string;
}

interface AiSimulationParsed {
  affected_groups?: SimulationGroup[];
  severity_explanation?: string;
  user_experience?: string;
  general_user_impact?: string;
}

// ====== Helper to parse JSON fields ======

const safeJsonParse = <T,>(json: string | null | undefined, fallback: T): T => {
  if (!json) return fallback;
  try {
    return JSON.parse(json) as T;
  } catch {
    return fallback;
  }
};

// ====== UI Components ======

const SeverityBadge: React.FC<{ severity: string }> = ({ severity }) => (
  <span className={`px-2 py-0.5 rounded text-xs font-medium border ${getSeverityColor(severity)}`}>
    {severity}
  </span>
);

const ExpandableSection: React.FC<{
  title: string;
  icon: React.ReactNode;
  color: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
}> = ({ title, icon, color, children, defaultOpen = false }) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  return (
    <div className="border border-navy-600 rounded-lg overflow-hidden">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`w-full flex items-center justify-between p-4 ${color} hover:opacity-90 transition-all`}
      >
        <div className="flex items-center gap-2">
          {icon}
          <span className="font-medium text-sm">{title}</span>
        </div>
        {isOpen ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
      </button>
      {isOpen && <div className="p-4 bg-navy-900/50 border-t border-navy-600">{children}</div>}
    </div>
  );
};

const ViolationCard: React.FC<{ violation: ViolationResponse }> = ({ violation }) => {
  // Parse all three JSON fields safely
  const aiExplanation = safeJsonParse<AiExplanationParsed | null>(violation.ai_explanation, null);
  const aiFix = safeJsonParse<AiFixParsed>(violation.ai_fix, {});
  const aiSimulation = safeJsonParse<AiSimulationParsed>(violation.ai_simulation, {});

  // Derive display strings with fallbacks
  const plainEnglish = aiExplanation?.plain_english || violation.ai_explanation || 'No explanation available.';
  const businessImpact = aiExplanation?.business_impact || '';
  const recommendation = aiExplanation?.recommendation || '';

  const getPriorityLevel = (priority?: string): 'high' | 'medium' | 'low' => {
    switch (priority?.toLowerCase()) {
      case 'critical':
      case 'high':
        return 'high';
      case 'medium':
        return 'medium';
      default:
        return 'low';
    }
  };

  const getDisabilityIcon = (disability: string) => {
    switch (disability) {
      case 'blind': return <EyeOff size={14} className="text-gray-400" />;
      case 'low_vision': return <Eye size={14} className="text-gray-400" />;
      case 'motor': return <Mouse size={14} className="text-gray-400" />;
      case 'cognitive': return <BrainCircuit size={14} className="text-gray-400" />;
      default: return <AlertTriangle size={14} className="text-gray-400" />;
    }
  };

  const getDisabilitySeverity = (disability: string): string => {
    const group = aiSimulation.affected_groups?.find(g => g.disability === disability);
    if (!group) return 'none';
    const impact = group.impact.toLowerCase();
    if (impact.includes('cannot') || impact.includes('completely') || impact.includes('impossible')) return 'severe';
    if (impact.includes('difficult') || impact.includes('struggle') || impact.includes('hard')) return 'moderate';
    if (impact.includes('minor') || impact.includes('slight')) return 'mild';
    return 'none';
  };

  return (
    <Card className="border-l-4 border-l-red-500/50">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-mono text-accent bg-accent/10 px-2 py-0.5 rounded">
              {violation.rule_id}
            </span>
            <SeverityBadge severity={violation.severity} />
          </div>
          <h3 className="text-white font-medium mb-1">{violation.rule_id} Violation</h3>
          <p className="text-sm text-gray-400">{plainEnglish}</p>
        </div>
      </div>

      {/* HTML Snippet */}
      {violation.html_snippet && (
        <div className="mb-4">
          <div className="flex items-center gap-1.5 text-xs text-gray-400 mb-1.5">
            <Code size={12} />
            HTML Snippet
          </div>
          <pre className="bg-black/50 border border-navy-600 rounded-lg p-3 text-xs text-gray-300 font-mono overflow-x-auto">
            <code>{violation.html_snippet}</code>
          </pre>
        </div>
      )}

      {/* WCAG Criterion */}
      {violation.wcag_criteria && (
        <div className="flex items-center gap-1.5 text-xs text-gray-400 mb-4">
          <ExternalLink size={12} />
          <span>WCAG Criterion: <span className="text-accent">{violation.wcag_criteria}</span></span>
        </div>
      )}

      {/* Expandable Sections */}
      <div className="space-y-2">
        {/* AI Explanation */}
        <ExpandableSection
          title="AI Explanation"
          icon={<Brain size={16} className="text-purple-400" />}
          color="bg-purple-500/10"
        >
          <div className="space-y-3">
            <div>
              <div className="flex items-center gap-1.5 text-xs text-gray-400 mb-1">
                <Lightbulb size={12} />
                Plain English
              </div>
              <p className="text-sm text-gray-200">{plainEnglish}</p>
            </div>
            {businessImpact && (
              <div>
                <div className="flex items-center gap-1.5 text-xs text-gray-400 mb-1">
                  <AlertCircle size={12} />
                  Business Impact
                </div>
                <p className="text-sm text-gray-200">{businessImpact}</p>
              </div>
            )}
            {recommendation && (
              <div>
                <div className="flex items-center gap-1.5 text-xs text-gray-400 mb-1">
                  <Target size={12} />
                  Recommendation
                </div>
                <p className="text-sm text-accent">{recommendation}</p>
              </div>
            )}
          </div>
        </ExpandableSection>

        {/* AI Fix */}
        <ExpandableSection
          title="AI Fix"
          icon={<Wrench size={16} className="text-green-400" />}
          color="bg-green-500/10"
        >
          <div className="space-y-3">
            {aiFix.problem && (
              <div>
                <div className="flex items-center gap-1.5 text-xs text-gray-400 mb-1">
                  <AlertTriangle size={12} />
                  Problem
                </div>
                <p className="text-sm text-gray-200">{aiFix.problem}</p>
              </div>
            )}
            {aiFix.recommended_fix && (
              <div>
                <div className="flex items-center gap-1.5 text-xs text-gray-400 mb-1">
                  <Target size={12} />
                  Recommended Fix
                </div>
                <p className="text-sm text-green-400">{aiFix.recommended_fix}</p>
              </div>
            )}
            {aiFix.code_example && (
              <div>
                <div className="flex items-center gap-1.5 text-xs text-gray-400 mb-1">
                  <Code size={12} />
                  Code Example
                </div>
                <pre className="bg-black/50 border border-navy-600 rounded-lg p-3 text-xs text-gray-300 font-mono overflow-x-auto">
                  <code>{aiFix.code_example}</code>
                </pre>
              </div>
            )}
            {aiFix.implementation_steps && aiFix.implementation_steps.length > 0 && (
              <div>
                <div className="flex items-center gap-1.5 text-xs text-gray-400 mb-1">
                  <ListChecks size={12} />
                  Implementation Steps
                </div>
                <ol className="list-decimal list-inside space-y-1">
                  {aiFix.implementation_steps.map((step, i) => (
                    <li key={i} className="text-sm text-gray-300">{step}</li>
                  ))}
                </ol>
              </div>
            )}
            {aiFix.priority && (
              <div className="flex items-center gap-2 pt-1">
                <span className="text-xs text-gray-400">Priority:</span>
                <span className={`text-xs font-medium ${getPriorityColor(getPriorityLevel(aiFix.priority))}`}>
                  {aiFix.priority.toUpperCase()}
                </span>
              </div>
            )}
          </div>
        </ExpandableSection>

        {/* General User Impact */}
        {aiSimulation.general_user_impact && (
          <ExpandableSection
            title="General User Impact"
            icon={<Users size={16} className="text-yellow-400" />}
            color="bg-yellow-500/10"
          >
            <div className="bg-navy-800/50 rounded-lg p-3 border border-navy-600/50">
              <p className="text-sm text-gray-200">{aiSimulation.general_user_impact}</p>
            </div>
          </ExpandableSection>
        )}

        {/* Accessibility Impact by User Group */}
        <ExpandableSection
          title="Accessibility Impact by User Group"
          icon={<Users size={16} className="text-blue-400" />}
          color="bg-blue-500/10"
        >
          <div className="space-y-4">
            {aiSimulation.affected_groups && aiSimulation.affected_groups.length > 0 ? (
              aiSimulation.affected_groups.map((group, i) => (
                <div key={i} className="bg-navy-800/50 rounded-lg p-3 border border-navy-600/50">
                  <div className="flex items-center gap-2 mb-2">
                    {getDisabilityIcon(group.disability)}
                    <span className="text-sm font-medium text-white capitalize">
                      {group.disability.replace('_', ' ')}
                    </span>
                    <SeverityBadge severity={getDisabilitySeverity(group.disability)} />
                  </div>
                  <p className="text-xs text-gray-400">{group.impact}</p>
                </div>
              ))
            ) : (
              <p className="text-sm text-gray-400">No simulation data available.</p>
            )}
            {aiSimulation.user_experience && (
              <div className="bg-navy-800/50 rounded-lg p-3 border border-navy-600/50">
                <p className="text-xs text-gray-500 italic">"{aiSimulation.user_experience}"</p>
              </div>
            )}
          </div>
        </ExpandableSection>
      </div>
    </Card>
  );
};

// ====== Main Page Component ======

const AuditDetailsPage: React.FC = () => {
  const { auditId } = useParams<{ auditId: string }>();
  const navigate = useNavigate();

  const {
    data: summary,
    isLoading: summaryLoading,
    isError: summaryError,
  } = useAuditSummary(auditId);

  const isRunning = summary?.status === 'running' || summary?.status === 'pending';

  const {
    data: violations,
    isLoading: violationsLoading,
  } = useAuditViolations(auditId, isRunning);

  const exportPdf = useReportDownload();
  const isLoading = summaryLoading;
  const isPolling = isRunning;

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <CardSkeleton key={i} />
          ))}
        </div>
      </div>
    );
  }

  if (summaryError || !summary) {
    return (
      <div className="text-center py-16">
        <AlertTriangle size={48} className="mx-auto text-gray-500 mb-4" />
        <h2 className="text-xl font-semibold text-white mb-2">Audit Not Found</h2>
        <p className="text-gray-400 mb-6">The audit you're looking for doesn't exist.</p>
        <button
          onClick={() => navigate(-1)}
          className="text-accent hover:text-accent-dark font-medium"
        >
          Back to Audits
        </button>
      </div>
    );
  }

  const severityCounts = summary.severity_breakdown || {
    critical: 0,
    serious: 0,
    moderate: 0,
    minor: 0,
  };

  return (
    <div className="space-y-6">
      {/* Header with Back Button and Export PDF */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-1.5 text-sm text-gray-400 hover:text-white transition-colors"
        >
          <ArrowLeft size={16} />
          Back to Audits
        </button>

        {summary.status === 'completed' && (
          <button
            onClick={() => exportPdf.mutate(auditId!)}
            disabled={exportPdf.isPending}
            className="flex items-center gap-2 bg-accent hover:bg-accent-dark text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
          >
            {exportPdf.isPending ? (
              <Loader2 size={14} className="animate-spin" />
            ) : (
              <Download size={14} />
            )}
            {exportPdf.isPending ? 'Exporting...' : 'Export PDF'}
          </button>
        )}
      </div>

      {/* Polling Indicator */}
      {isPolling && (
        <div className="flex items-center gap-2 text-sm text-blue-400 bg-blue-500/10 border border-blue-500/30 rounded-lg p-3">
          <Loader2 size={16} className="animate-spin" />
          Audit is {summary.status}... Polling for updates every 5 seconds
        </div>
      )}

      {/* Error State */}
      {summary.status === 'failed' && (
        <div className="flex items-center gap-2 text-sm text-red-400 bg-red-500/10 border border-red-500/30 rounded-lg p-3">
          <AlertTriangle size={16} />
          Audit failed: {summary.error_message || 'Unknown error'}
        </div>
      )}

      {/* Top Section - Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 rounded-lg bg-green-500/10">
              <Target size={18} className="text-green-400" />
            </div>
            <span className="text-sm text-gray-400">Accessibility Score</span>
          </div>
          <p className="text-3xl font-bold text-white">
            {summary.accessibility_score !== null ? `${summary.accessibility_score}%` : '--'}
          </p>
        </Card>
        <Card>
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 rounded-lg bg-blue-500/10">
              <FileText size={18} className="text-blue-400" />
            </div>
            <span className="text-sm text-gray-400">Pages Scanned</span>
          </div>
          <p className="text-3xl font-bold text-white">
            {summary.pages_scanned !== null ? summary.pages_scanned : '--'}
          </p>
        </Card>
        <Card>
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 rounded-lg bg-red-500/10">
              <AlertTriangle size={18} className="text-red-400" />
            </div>
            <span className="text-sm text-gray-400">Total Violations</span>
          </div>
          <p className="text-3xl font-bold text-white">
            {summary.total_violations !== null ? summary.total_violations : '--'}
          </p>
        </Card>
        <Card>
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 rounded-lg bg-orange-500/10">
              <AlertCircle size={18} className="text-orange-400" />
            </div>
            <span className="text-sm text-gray-400">Severity Breakdown</span>
          </div>
          <div className="flex items-center gap-3 text-sm">
            <span className="text-red-400">{severityCounts.critical} Critical</span>
            <span className="text-orange-400">{severityCounts.serious} Serious</span>
            <span className="text-yellow-400">{severityCounts.moderate} Moderate</span>
            <span className="text-blue-400">{severityCounts.minor} Minor</span>
          </div>
        </Card>
      </div>

      {/* Audit Info */}
      <Card>
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-white">Audit Details</h2>
            <p className="text-sm text-gray-400">Audit ID: <span className="text-accent font-mono">{summary.audit_id}</span></p>
          </div>
          <div className="text-right text-sm text-gray-400">
            <p>Started: {new Date(summary.started_at).toLocaleDateString()}</p>
            {summary.completed_at && <p>Completed: {new Date(summary.completed_at).toLocaleDateString()}</p>}
          </div>
        </div>
      </Card>

      {/* Summary Text */}
      {summary.summary_text && (
        <Card>
          <h3 className="text-sm font-medium text-gray-300 mb-2">Summary</h3>
          <p className="text-sm text-gray-400 leading-relaxed">{summary.summary_text}</p>
        </Card>
      )}

      {/* Violation Cards */}
      {violations && violations.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-white mb-4">
            Violations ({violations.length})
          </h2>
          <div className="space-y-4">
            {violations.map((violation) => (
              <ViolationCard key={violation.id} violation={violation} />
            ))}
          </div>
        </div>
      )}

      {violationsLoading && (
        <div className="text-center py-8">
          <Loader2 size={24} className="animate-spin mx-auto text-accent" />
          <p className="text-sm text-gray-400 mt-2">Loading violations...</p>
        </div>
      )}

      {violations && violations.length === 0 && !violationsLoading && summary.status === 'completed' && (
        <Card>
          <p className="text-sm text-gray-400 text-center py-4">No violations found.</p>
        </Card>
      )}
    </div>
  );
};

export default AuditDetailsPage;