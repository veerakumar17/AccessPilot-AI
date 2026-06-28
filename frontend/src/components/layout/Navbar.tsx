import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { LogOut, User } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const Navbar: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const getPageTitle = () => {
    switch (location.pathname) {
      case '/dashboard': return 'Dashboard';
      case '/projects': return 'Projects';
      case '/audits': return 'Audit History';
      case '/reports': return 'Reports';
      default: return 'AccessPilot AI';
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <header className="h-16 bg-navy-900/80 backdrop-blur-sm border-b border-navy-700 flex items-center justify-between px-6 sticky top-0 z-30">
      <div className="flex items-center gap-4">
        <h1 className="text-xl font-semibold text-white">{getPageTitle()}</h1>
      </div>

      <div className="flex items-center gap-3">
        {/* User */}
        <div className="flex items-center gap-2 pl-3 border-l border-navy-600">
          <div className="w-8 h-8 rounded-full bg-accent/20 flex items-center justify-center">
            <User size={16} className="text-accent" />
          </div>
          <div className="hidden md:block">
            <p className="text-sm font-medium text-white">{user?.full_name || 'User'}</p>
            <p className="text-xs text-gray-400">{user?.email || ''}</p>
          </div>
          <button
            onClick={handleLogout}
            className="ml-2 p-1.5 rounded-lg text-gray-400 hover:text-red-400 hover:bg-navy-800 transition-all"
            title="Logout"
          >
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </header>
  );
};

export default Navbar;