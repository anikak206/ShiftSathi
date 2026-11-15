import { useEffect, useState } from 'react';
import { api } from '../api';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { AlertTriangle, CheckCircle, Clock, List, Cpu, RefreshCw } from 'lucide-react';
import Spinner from '../components/Spinner';

const COLORS = ['#ef4444','#f97316','#eab308','#22c55e'];

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [insights, setInsights] = useState(null);
  const [incidents, setIncidents] = useState([]);
  const [err, setErr] = useState(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setErr(null);
    try {
      const [s, ins, inc] = await Promise.all([
        api('/dashboard/stats'),
        api('/insights').catch(() => null),
        api('/incidents').catch(() => []),
      ]);
      setStats(s);
      setInsights(ins);
      setIncidents(Array.isArray(inc) ? inc : []);
    } catch (e) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  if (err) return <div className="text-red-400">{err}</div>;
  if (loading || !stats) return <Spinner label="Loading dashboard..." />;

  const pieData = Object.entries(stats.priority_distribution || {}).map(([k,v]) => ({ name: k, value: v }));
  const catData = Object.entries(stats.category_distribution || {}).map(([k,v]) => ({ name: k, value: v }));

  // machine-wise counts from actual incidents
  const machineCounts = {};
  incidents.forEach(i => {
    const m = i.machine_id || 'Unknown';
    machineCounts[m] = (machineCounts[m] || 0) + 1;
  });
  const machineRows = Object.entries(machineCounts)
    .map(([m, c]) => ({ machine: m, count: c }))
    .sort((a, b) => b.count - a.count);

  const pending = stats.open || 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Operations Dashboard</h1>
        <button onClick={load} className="flex items-center gap-1 bg-slate-700 hover:bg-slate-600 px-3 py-1.5 rounded text-sm">
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {/* Overview cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card icon={<List />} label="Total Incidents" value={stats.total} />
        <Card icon={<AlertTriangle />} label="Critical Incidents" value={stats.critical} />
        <Card icon={<CheckCircle />} label="Resolved Incidents" value={stats.resolved} />
        <Card icon={<Clock />} label="Pending Incidents" value={pending} />
      </div>

      {/* Charts */}
      <div className="grid md:grid-cols-2 gap-4">
        <div className="glass rounded-xl p-4">
          <h2 className="font-semibold mb-2">Priority Distribution</h2>
          {pieData.length === 0 ? (
            <div className="text-slate-400 text-sm py-8 text-center">No incident data yet.</div>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={pieData} dataKey="value" nameKey="name" outerRadius={80} label>
                  {pieData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
        <div className="glass rounded-xl p-4">
          <h2 className="font-semibold mb-2">Incident Category Distribution</h2>
          {catData.length === 0 ? (
            <div className="text-slate-400 text-sm py-8 text-center">No category data yet.</div>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={catData}>
                <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                <YAxis tick={{ fill: '#94a3b8' }} />
                <Tooltip />
                <Bar dataKey="value" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Recent incidents table */}
      <div className="glass rounded-xl p-4">
        <h2 className="font-semibold mb-3">Recent Incidents</h2>
        {(!stats.recent || stats.recent.length === 0) ? (
          <div className="text-slate-400 text-sm py-4 text-center">
            No incidents yet. <a href="/report" className="text-amber-400 hover:underline">Report your first incident</a>.
          </div>
        ) : (
          <div className="overflow-auto">
            <table className="w-full text-sm">
              <thead className="text-slate-400 text-xs uppercase">
                <tr>
                  <th className="text-left p-2">Machine ID</th>
                  <th className="text-left p-2">Issue</th>
                  <th className="text-left p-2">Severity</th>
                  <th className="text-left p-2">Status</th>
                  <th className="text-left p-2">Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {stats.recent.map(i => (
                  <tr key={i.id} className="border-t border-slate-800">
                    <td className="p-2 font-mono text-xs">{i.machine_id || '—'}</td>
                    <td className="p-2 max-w-xs truncate">{i.description?.slice(0, 60) || i.category}</td>
                    <td className="p-2"><span className={`text-xs px-2 py-0.5 rounded ${sevColor(i.severity)}`}>{i.severity}</span></td>
                    <td className="p-2 text-xs">{i.status}</td>
                    <td className="p-2 text-xs text-slate-400">{i.created_at ? new Date(i.created_at).toLocaleString() : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Machine-wise overview */}
      <div className="glass rounded-xl p-4">
        <h2 className="font-semibold mb-3">Machine-wise Incident Overview</h2>
        {machineRows.length === 0 ? (
          <div className="text-slate-400 text-sm py-4 text-center">No machine data available.</div>
        ) : (
          <div className="space-y-1">
            {machineRows.map(r => (
              <div key={r.machine} className="flex items-center justify-between border-b border-slate-800 pb-1 text-sm">
                <span className="font-mono text-xs">{r.machine}</span>
                <span className="text-amber-400">{r.count} incident{r.count > 1 ? 's' : ''}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Operational insights */}
      <div className="glass rounded-xl p-4">
        <h2 className="font-semibold mb-3">Operational Insights</h2>
        {(!insights || (insights.recurring_machines?.length === 0 && insights.top_pending_actions?.length === 0)) ? (
          <div className="text-slate-400 text-sm py-4 text-center">No recurring issues or pending actions yet.</div>
        ) : (
          <div className="space-y-3 text-sm">
            {insights.recurring_machines?.length > 0 && (
              <div>
                <div className="text-xs text-slate-400 mb-1">Recurring machine issues:</div>
                <ul className="list-disc pl-5 space-y-0.5">
                  {insights.recurring_machines.map(r => (
                    <li key={r.machine_id}>{r.machine_id} — {r.count} incidents</li>
                  ))}
                </ul>
              </div>
            )}
            {insights.top_pending_actions?.length > 0 && (
              <div>
                <div className="text-xs text-slate-400 mb-1">Pending critical actions:</div>
                <ul className="list-disc pl-5 space-y-0.5">
                  {insights.top_pending_actions.map((a, i) => (
                    <li key={i}>{a.action} ({a.count})</li>
                  ))}
                </ul>
              </div>
            )}
            {insights.open_critical > 0 && (
              <div className="text-red-400 text-xs">Open critical/high incidents: {insights.open_critical}</div>
            )}
          </div>
        )}
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
