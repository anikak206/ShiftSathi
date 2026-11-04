import { useEffect, useState } from 'react';
import { api } from '../api';

export default function History() {
  const [items, setItems] = useState([]);
  const [q, setQ] = useState('');
  const [status, setStatus] = useState('');
  const [severity, setSeverity] = useState('');

  async function load() {
    const params = new URLSearchParams();
    if (status) params.set('status', status);
    if (severity) params.set('severity', severity);
    if (q) params.set('q', q);
    const data = await api('/incidents?' + params.toString());
    setItems(data);
  }
  useEffect(() => { load(); }, []);

  async function updateStatus(id, st) {
    await api(`/incidents/${id}`, { method: 'PATCH', body: JSON.stringify({ status: st }) });
    load();
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Incident History</h1>
      <div className="flex flex-wrap gap-3">
        <input value={q} onChange={e => setQ(e.target.value)} placeholder="Search..." className="bg-slate-800 rounded px-3 py-2 text-sm" />
        <select value={status} onChange={e => setStatus(e.target.value)} className="bg-slate-800 rounded px-3 py-2 text-sm">
          <option value="">All status</option>
          <option value="open">Open</option>
          <option value="resolved">Resolved</option>
        </select>
        <select value={severity} onChange={e => setSeverity(e.target.value)} className="bg-slate-800 rounded px-3 py-2 text-sm">
          <option value="">All severity</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
        <button onClick={load} className="bg-amber-500 text-slate-900 px-4 py-2 rounded-lg text-sm font-semibold">Filter</button>
      </div>
      <div className="glass rounded-xl overflow-auto">
        <table className="w-full text-sm">
          <thead className="text-slate-400 text-xs uppercase">
            <tr>
              <th className="text-left p-3">ID</th>
              <th className="text-left p-3">Machine</th>
              <th className="text-left p-3">Category</th>
              <th className="text-left p-3">Severity</th>
              <th className="text-left p-3">Status</th>
              <th className="text-left p-3">Description</th>
              <th className="text-left p-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {items.map(i => (
              <tr key={i.id} className="border-t border-slate-800">
                <td className="p-3 font-mono text-xs">{i.id}</td>
                <td className="p-3">{i.machine_id || '-'}</td>
                <td className="p-3">{i.category}</td>
                <td className="p-3">{i.severity}</td>
                <td className="p-3">{i.status}</td>
                <td className="p-3 max-w-xs truncate">{i.description}</td>
                <td className="p-3 space-x-2">
                  {i.status !== 'resolved' && (
                    <button onClick={() => updateStatus(i.id, 'resolved')} className="text-green-400 text-xs hover:underline">Resolve</button>
                  )}
                  <a href={`/api/incidents/${i.id}/export`} className="text-blue-400 text-xs hover:underline">Export</a>
                </td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr><td colSpan={7} className="p-4 text-center text-slate-400">No incidents.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
