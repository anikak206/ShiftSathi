import { useEffect, useState } from 'react';
import { api } from '../api';

export default function Eval() {
  const [res, setRes] = useState(null);
  const [loading, setLoading] = useState(false);
  async function run() {
    setLoading(true);
    try {
      const r = await api('/eval/run', { method: 'POST' });
      setRes(r);
    } catch (e) {
      setRes({ error: e.message });
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => { run(); }, []);
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Evaluation</h1>
      <button onClick={run} disabled={loading} className="bg-amber-500 text-slate-900 px-4 py-2 rounded-lg font-semibold disabled:opacity-50">
        {loading ? 'Running...' : 'Run Eval'}
      </button>
      {res?.summary && (
        <div className="glass rounded-xl p-4">
          <div className="text-sm">Samples: {res.summary.samples}</div>
          <div className="text-sm">Field accuracy: {(res.summary.field_accuracy * 100).toFixed(1)}%</div>
          <div className="text-sm">Fields checked: {res.summary.fields_checked}, correct: {res.summary.fields_correct}</div>
        </div>
      )}
      {res?.results && (
        <div className="space-y-3">
          {res.results.map(r => (
            <div key={r.id} className="glass rounded-xl p-4 text-sm">
              <div className="font-medium">{r.id}: {r.transcript}</div>
              <div className="text-slate-400 text-xs mt-1">Extracted: {JSON.stringify(r.extracted)}</div>
              <div className="text-slate-400 text-xs">Expected: {JSON.stringify(r.expected)}</div>
              <div className="text-slate-400 text-xs">Confidence: {r.confidence} | Missing: {(r.missing_fields || []).join(', ')}</div>
              <div className="text-slate-400 text-xs">Questions: {(r.questions || []).join(' | ')}</div>
            </div>
          ))}
        </div>
      )}
      {res?.error && <div className="text-red-400">{res.error}</div>}
    </div>
  );
}
