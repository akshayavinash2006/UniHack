import React from 'react';
import { Database, Search, CheckCircle2, AlertTriangle, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

export const Dashboard: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Hero Section */}
      <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-2xl p-8 lg:p-12 text-white shadow-lg overflow-hidden relative">
        <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 -translate-y-1/2 translate-x-1/2"></div>
        <div className="absolute bottom-0 left-0 w-64 h-64 bg-indigo-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 translate-y-1/2 -translate-x-1/2"></div>
        
        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center px-3 py-1 rounded-full bg-white/10 border border-white/20 text-blue-200 text-xs font-semibold tracking-wide uppercase mb-6">
            <span className="flex h-2 w-2 rounded-full bg-green-400 mr-2"></span>
            System Operational
          </div>
          <h1 className="text-4xl lg:text-5xl font-bold tracking-tight mb-4 leading-tight">
            Product Data <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-indigo-400">Intelligence</span>
          </h1>
          <p className="text-lg text-slate-300 mb-8 max-w-xl">
            Turn messy industrial catalogue data into verified, search-ready product records using AI-powered manufacturer source discovery.
          </p>
          
          <div className="flex flex-wrap gap-4">
            <Link to="/enrich/batch" className="bg-blue-600 hover:bg-blue-500 text-white font-medium py-3 px-6 rounded-lg transition-colors flex items-center shadow-lg shadow-blue-900/20">
              <Database className="w-5 h-5 mr-2" /> Start Batch Enrichment
            </Link>
            <Link to="/enrich/single" className="bg-white/10 hover:bg-white/20 border border-white/20 text-white font-medium py-3 px-6 rounded-lg transition-colors flex items-center">
              <Search className="w-5 h-5 mr-2" /> Single Product Demo
            </Link>
          </div>
        </div>
      </div>

      {/* Quick Stats Mockup for Dashboard Feel */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 hover:border-blue-300 transition-colors cursor-pointer group">
          <div className="flex justify-between items-start mb-4">
            <div className="p-3 bg-blue-50 rounded-lg text-blue-600">
              <Database className="w-6 h-6" />
            </div>
            <span className="text-sm font-medium text-slate-500">All Time</span>
          </div>
          <h3 className="text-3xl font-bold text-slate-800 mb-1">12,408</h3>
          <p className="text-sm text-slate-500 font-medium">Products Processed</p>
          <div className="mt-4 flex items-center text-xs font-medium text-green-600">
            <span>+1,200 this week</span>
          </div>
        </div>
        
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 hover:border-green-300 transition-colors cursor-pointer group">
          <div className="flex justify-between items-start mb-4">
            <div className="p-3 bg-green-50 rounded-lg text-green-600">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <span className="text-sm font-medium text-slate-500">Match Rate</span>
          </div>
          <h3 className="text-3xl font-bold text-slate-800 mb-1">82.4%</h3>
          <p className="text-sm text-slate-500 font-medium">High Confidence Source</p>
          <div className="mt-4 flex items-center text-xs font-medium text-green-600">
            <span>+2.1% from AI improvements</span>
          </div>
        </div>
        
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 hover:border-amber-300 transition-colors cursor-pointer group">
          <div className="flex justify-between items-start mb-4">
            <div className="p-3 bg-amber-50 rounded-lg text-amber-600">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <span className="text-sm font-medium text-slate-500">Action Required</span>
          </div>
          <h3 className="text-3xl font-bold text-slate-800 mb-1">142</h3>
          <p className="text-sm text-slate-500 font-medium">In Review Queue</p>
          <div className="mt-4 flex items-center text-xs font-medium text-amber-600">
            <Link to="/review" className="hover:underline flex items-center">
              Review flagged items <ArrowRight className="w-3 h-3 ml-1" />
            </Link>
          </div>
        </div>
      </div>
      
    </div>
  );
};
