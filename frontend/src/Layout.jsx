import { NavLink, Outlet } from 'react-router-dom';
import { Mic, LayoutDashboard, History, FileText, ClipboardList, Activity, Brain } from 'lucide-react';

const nav = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/report', label: 'Voice Report', icon: Mic },
  { to: '/history', label: 'Incident History', icon: History },
  { to: '/insights', label: 'Shift Intelligence', icon: Brain },
  { to: '/handover', label: 'Shift Handover', icon: ClipboardList },
  { to: '/eval', label: 'Evaluation', icon: Activity },
];

export default function Layout() {
  return (
    <div className="min-h-screen flex">
      <aside className="w-64 bg-slate-900 border-r border-slate-800 p-4 hidden md:block">
        <div className="flex items-center gap-2 mb-8">
          <div className="w-9 h-9 rounded-lg bg-amber-500 flex items-center justify-center font-bold text-slate-900">S</div>
          <div>
            <div className="font-semibold">ShiftSathi</div>
            <div className="text-xs text-slate-400">Industrial Intelligence</div>
          </div>
        </div>
        <nav className="space-y-1">
          {nav.map(n => {
            const Icon = n.icon;
            return (
              <NavLink key={n.to} to={n.to} end={n.to === '/'}
                className={({ isActive }) => `flex items-center gap-3 px-3 py-2 rounded-lg text-sm ${isActive ? 'bg-amber-500/20 text-amber-400' : 'text-slate-300 hover:bg-slate-800'}`}>
                <Icon size={18} /> {n.label}
              </NavLink>
            );
          })}
        </nav>
      </aside>
      <main className="flex-1 p-6 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
