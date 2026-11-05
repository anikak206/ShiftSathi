import { useEffect, useState } from 'react';
import { api } from '../api';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { AlertTriangle, CheckCircle, Clock, List } from 'lucide-react';
import Spinner from '../components/Spinner';

const COLORS = ['#ef4444','#f97316','#eab308','#22c55e'];

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [err, setErr] = useState(null);
  useEffect(() => {
    api('/dashboard/stats').then(setStats).catch(e => setErr(e.message));
  }, []);
  if (err) return <div className="text-red-400">{err}</div>;
  if (!stats) return <Spinner label="Loading dashboard..." />;
  const pieData = Object.entries(stats.priority_distribution || {}).map(([k,v]) => ({ name: k, value: v }));
  const catData = Object.entries(stats.category_distribution || {}).map(([k,v]) => ({ name: k, value: v }));
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card icon={<List />} label="Total Incidents" value={stats.total} />
        <Card icon={<Clock />} label="Open" value={stats.open} />
        <Card icon={<AlertTriangle />} label="Critical/High" value={stats.critical} />
        <Card icon={<CheckCircle />} label="Resolved" value={stats.resolved} />
      </div>
      <div className="grid md:grid-cols-2 gap-4">
        <div className="glass rounded-xl p-4">
          <h2 className="font-semibold mb-2">Priority Distribution</h2>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={pieData} dataKey="value" nameKey="name" outerRadius={80} label>
                {pieData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="glass rounded-xl p-4">
          <h2 className="font-semibold mb-2">By Category</h2>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={catData}>
              <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <YAxis tick={{ fill: '#94a3b8' }} />
              <Tooltip />
              <Bar dataKey="value" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div className="glass rounded-xl p-4">
        <h2 className="font-semibold mb-3">Recent Incidents</h2>
        <div className="space-y-2">
          {(stats.recent || []).map(i => (
            <div key={i.id} className="flex items-center justify-between border-b border-slate-800 pb-2">
              <div>
                <div className="text-sm font-medium">{i.machine_id || 'Unknown'} — {i.category}</div>
                <div className="text-xs text-slate-400">{i.description?.slice(0,80)}</div>
              </div>
              <span className={`text-xs px-2 py-1 rounded ${sevColor(i.severity)}`}>{i.severity}</span>
            </div>
          ))}
          {(!stats.recent || stats.recent.length === 0) && <div className="text-slate-400 text-sm">No incidents yet.</div>}
        </div>
      </div>
    </div>
  );
}

function Card({ icon, label, value }) {
  return (
    <div className="glass rounded-xl p-4 flex items-center gap-3">
      <div className="text-amber-400">{icon}</div>
      <div>
        <div className="text-2xl font-bold">{value}</div>
        <div className="text-xs text-slate-400">{label}</div>
      </div>
    </div>
  );
}

function sevColor(s) {
  if (s === 'critical') return 'bg-red-600 text-white';
  if (s === 'high') return 'bg-orange-500 text-white';
  if (s === 'medium') return 'bg-yellow-500 text-slate-900';
  return 'bg-green-600 text-white';
}
