import React from 'react';
import { useNavigate } from 'react-router-dom';
import { FolderKanban, History, Target, AlertTriangle, ArrowRight } from 'lucide-react';
import Card from '../components/ui/Card';
import { CardSkeleton } from '../components/ui/LoadingSkeleton';
import { useProjects } from '../hooks/useApi';

const StatCard: React.FC<{
  icon: React.ReactNode;
  label: string;
  value: string | number;
  color: string;
  trend?: string;
}> = ({ icon, label, value, color, trend }) => (
  <Card className="flex items-start gap-4">
    <div className={`p-3 rounded-lg ${color}`}>{icon}</div>
    <div className="flex-1">
      <p className="text-sm text-gray-400">{label}</p>
      <p className="text-2xl font-bold text-white mt-1">{value}</p>
      {trend && <p className="text-xs text-green-400 mt-1">{trend}</p>}
    </div>
  </Card>
);

const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { data: projects, isLoading: projectsLoading } = useProjects();

  // For dashboard stats, we use projects count and derive other stats
  const totalProjects = projects?.length || 0;
  const isLoading = projectsLoading;

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <CardSkeleton key={i} />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={<FolderKanban size={20} className="text-blue-400" />}
          label="Total Projects"
          value={totalProjects}
          color="bg-blue-500/10"
        />
        <StatCard
          icon={<History size={20} className="text-purple-400" />}
          label="Total Audits"
          value={0}
          color="bg-purple-500/10"
        />
        <StatCard
          icon={<Target size={20} className="text-green-400" />}
          label="Accessibility Score"
          value="--"
          color="bg-green-500/10"
        />
        <StatCard
          icon={<AlertTriangle size={20} className="text-red-400" />}
          label="Critical Violations"
          value={0}
          color="bg-red-500/10"
        />
      </div>

      {/* Recent Audits */}
      <Card>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-white">Recent Audits</h2>
          <button
            onClick={() => navigate('/audits')}
            className="flex items-center gap-1 text-sm text-accent hover:text-accent-dark"
          >
            View All <ArrowRight size={14} />
          </button>
        </div>
        <div className="space-y-3">
          <p className="text-sm text-gray-400 text-center py-8">
            Run an audit to see results here
          </p>
        </div>
      </Card>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card onClick={() => navigate('/projects')} className="hover:border-accent/50">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-accent/10">
              <FolderKanban size={20} className="text-accent" />
            </div>
            <div>
              <h3 className="font-medium text-white">Manage Projects</h3>
              <p className="text-sm text-gray-400">View and manage your accessibility projects</p>
            </div>
          </div>
        </Card>
        <Card onClick={() => navigate('/reports')} className="hover:border-accent/50">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-green-500/10">
              <Target size={20} className="text-green-400" />
            </div>
            <div>
              <h3 className="font-medium text-white">View Reports</h3>
              <p className="text-sm text-gray-400">Access detailed accessibility reports</p>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default DashboardPage;