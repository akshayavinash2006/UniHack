import React, { useState, useEffect } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { 
  Database, 
  Search, 
  List, 
  BarChart2, 
  Download, 
  AlertTriangle,
  Menu,
  X,
  Cpu,
  Activity,
  Globe
} from 'lucide-react';
import { api } from '../../api/client';
import type { SystemStatus } from '../../api/client';

export const Layout: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [status, setStatus] = useState<SystemStatus | null>(null);

  useEffect(() => {
    api.getStatus().then(setStatus).catch(console.error);
  }, []);

  const navItems = [
    { to: '/', icon: Activity, label: 'Dashboard' },
    { to: '/enrich/single', icon: Search, label: 'Single Product' },
    { to: '/enrich/batch', icon: Database, label: 'Batch Processing' },
    { to: '/results/latest', icon: List, label: 'Results' },
    { to: '/review', icon: AlertTriangle, label: 'Review Queue' },
    { to: '/analytics', icon: BarChart2, label: 'Analytics' },
    { to: '/exports', icon: Download, label: 'Exports' },
  ];

  return (
    <div className="min-h-screen flex bg-slate-50">
      {/* Mobile sidebar toggle */}
      <div className="lg:hidden fixed top-4 left-4 z-50">
        <button 
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-2 bg-white rounded-md shadow-sm border border-slate-200 text-slate-600"
        >
          {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      {/* Sidebar */}
      <aside className={`
        fixed inset-y-0 left-0 z-40 w-64 bg-slate-900 text-slate-300 transition-transform duration-300 ease-in-out
        lg:translate-x-0 lg:static lg:flex-shrink-0
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="h-full flex flex-col">
          <div className="h-16 flex items-center px-6 bg-slate-950/50">
            <Cpu className="w-6 h-6 text-blue-500 mr-3" />
            <span className="text-lg font-bold text-white tracking-tight">UNILOG INTEL</span>
          </div>
          
          <nav className="flex-1 py-6 px-3 space-y-1 overflow-y-auto">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={() => setSidebarOpen(false)}
                className={({ isActive }) => `
                  flex items-center px-3 py-2.5 rounded-md text-sm font-medium transition-colors
                  ${isActive 
                    ? 'bg-blue-600/10 text-blue-400' 
                    : 'hover:bg-slate-800 hover:text-white'}
                `}
              >
                <item.icon className="w-5 h-5 mr-3 flex-shrink-0" />
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-6 lg:px-10 sticky top-0 z-30">
          <div className="pl-12 lg:pl-0">
            <h1 className="text-xl font-semibold text-slate-800 tracking-tight">
              Product Enrichment Intelligence
            </h1>
            <p className="text-xs text-slate-500">Manufacturer Source Discovery</p>
          </div>
          
          <div className="hidden sm:flex items-center space-x-4">
            <div className="flex items-center text-sm">
              <span className="relative flex h-3 w-3 mr-2">
                <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${status?.search_engine_connected ? 'bg-green-400' : 'bg-red-400'}`}></span>
                <span className={`relative inline-flex rounded-full h-3 w-3 ${status?.search_engine_connected ? 'bg-green-500' : 'bg-red-500'}`}></span>
              </span>
              <span className="text-slate-600">Search Connected</span>
            </div>
            
            <div className="flex items-center text-sm">
              <span className="relative flex h-3 w-3 mr-2">
                {status?.gemini_connected && (
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 bg-blue-400"></span>
                )}
                <span className={`relative inline-flex rounded-full h-3 w-3 ${status?.gemini_connected ? 'bg-blue-500' : 'bg-slate-300'}`}></span>
              </span>
              <span className="text-slate-600">{status?.gemini_connected ? 'Gemini Active' : 'Gemini Offline'}</span>
            </div>
          </div>
        </header>

        <main className="flex-1 p-6 lg:p-10 overflow-auto">
          <div className="max-w-7xl mx-auto">
            <Outlet />
          </div>
        </main>
      </div>
      
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-slate-900/50 z-30 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  );
};
