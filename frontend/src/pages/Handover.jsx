import { useEffect, useState } from 'react';
import { api } from '../api';

export default function Handover() {
  const [summary, setSummary] = useState('');
  const [loading, setLoading] = useState(false);
  async function gen() {
    setLoading(true);
    try {
      const r = await api('/handover');
      setSummary(r.summary);
    } catch (e) {
      setSummary('Error: ' + e.message);
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => { gen(); }, []);
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Shift Handover</h1>
      <button onClick={gen} disabled={loading} className="bg-amber-500 text-slate-900 px-4 py-2 rounded-lg font-semibold disabled:opacity-50">
        {loading ? 'Generating...' : 'Regenerate'}
      </button>
      <div className="glass rounded-xl p-6">
        <pre className="whitespace-pre-wrap text-sm">{summary || 'No data yet.'}</pre>
      </div>
    </div>
  );
}
