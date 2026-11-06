import { useEffect, useState } from 'react';
import { api } from '../api';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

export default function Insights() {
  const [data, setData] = useState(null);
  useEffect(() => { api('/insights').then(setData).catch(() => {}); }, []);
  if (!data) return <div className="text-slate-400">Loading insights...</div>;
  const catData = Object.entries(data.category_counts || {}).map(([k,v]) => ({ name: k, value: v }));
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Shift Intelligence</h1>
      <div className="grid md:grid-cols-3 gap-4">
        <div className="glass rounded-xl p-4"><div className="text-2xl font-bold">{data.total_incidents}</div><div className="text-xs text-slate-400">Total Incidents</div></div>
        <div className="glass rounded-xl p-4"><div className="text-2xl font-bold">{data.open_critical}</div><div className="text-xs text-slate-400">Open Critical/High</div></div>
        <div className="glass rounded-xl p-4"><div className="text-2xl font-bold">{data.machines_affected}</div><div className="text-xs text-slate-400">Machines Affected</div></div>
      </div>
      <div className="glass rounded-xl p-4">
        <h2 className="font-semibold mb-2">Incidents by Category</h2>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={catData}><XAxis dataKey="name" tick={{fill:'#94a3b8',fontSize:11}} /><YAxis tick={{fill:'#94a3b8'}} /><Tooltip /><Bar dataKey="value" fill="#f59e0b" /></BarChart>
        </ResponsiveContainer>
      </div>
      {data.recurring_machines?.length > 0 && (
        <div className="glass rounded-xl p-4">
          <h2 className="font-semibold mb-2">Recurring Machine Issues (evidence-backed)</h2>
          <ul className="space-y-1 text-sm">
            {data.recurring_machines.map(r => (
              <li key={r.machine_id} className="flex justify-between border-b border-slate-800 pb-1">
                <span>{r.machine_id}</span><span className="text-amber-400">{r.count} incidents</span>
              </li>
            ))}
          </ul>
        </div>
      )}
      {data.top_pending_actions?.length > 0 && (
        <div className="glass rounded-xl p-4">
          <h2 className="font-semibold mb-2">Top Pending Actions</h2>
          <ul className="space-y-1 text-sm">
            {data.top_pending_actions.map((a,i) => (
              <li key={i} className="flex justify-between border-b border-slate-800 pb-1">
                <span>{a.action}</span><span className="text-slate-400">{a.count}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
