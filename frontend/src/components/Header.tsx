import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { BarChart3, FileText, Home, Search, LayoutDashboard } from 'lucide-react';

const Header: React.FC = () => {
  const location = useLocation();
  
  const isActive = (path: string) => location.pathname === path;
  
  return (
    <header className="glass p-4 mb-6">
      <div className="container mx-auto">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <BarChart3 className="w-8 h-8 text-primary" />
            <h1 className="text-2xl font-bold text-gray-800">
              Competitor Analysis System
            </h1>
          </div>
          
          <nav className="flex items-center gap-6">
            <Link
              to="/"
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition ${
                isActive('/') 
                  ? 'bg-primary text-white' 
                  : 'text-gray-600 hover:text-primary hover:bg-white hover:bg-opacity-50'
              }`}
            >
              <Home className="w-5 h-5 text-white" />
              <span className="font-medium text-white">Home</span>
            </Link>
            
            <Link
              to="/home"
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition ${
                isActive('/home') 
                  ? 'bg-primary text-white' 
                  : 'text-gray-600 hover:text-primary hover:bg-white hover:bg-opacity-50'
              }`}
            >
              <LayoutDashboard className="w-5 h-5 text-white" />
              <span className="font-medium text-white">Dashboard</span>
            </Link>
            
            <Link
              to="/analysis"
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition ${
                isActive('/analysis') 
                  ? 'bg-primary text-white' 
                  : 'text-gray-600 hover:text-primary hover:bg-white hover:bg-opacity-50'
              }`}
            >
              <Search className="w-5 h-5 text-white" />
              <span className="font-medium text-white">Analysis</span>
            </Link>
            
            <Link
              to="/reports"
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition ${
                isActive('/reports') 
                  ? 'bg-primary text-white' 
                  : 'text-gray-600 hover:text-primary hover:bg-white hover:bg-opacity-50'
              }`}
            >
              <FileText className="w-5 h-5 text-white" />
              <span className="font-medium text-white">Reports</span>
            </Link>
          </nav>
        </div>
      </div>
    </header>
  );
};

export default Header;