import { useState, useRef } from 'react';
import { api, uploadAudio } from '../api';
import { Mic, Square, Upload, Play, CheckCircle } from 'lucide-react';

export default function VoiceReport() {
  const [recording, setRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const [transcript, setTranscript] = useState('');
  const [language, setLanguage] = useState('hi-IN');
  const [session, setSession] = useState(null);
  const [answer, setAnswer] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);
  const [confirmed, setConfirmed] = useState(null);
  const mediaRef = useRef(null);
  const chunksRef = useRef([]);

  async function startRec() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream);
      chunksRef.current = [];
      mr.ondataavailable = e => { if (e.data.size > 0) chunksRef.current.push(e.data); };
      mr.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        setAudioBlob(blob);
        stream.getTracks().forEach(t => t.stop());
      };
      mr.start();
      mediaRef.current = mr;
      setRecording(true);
    } catch (e) {
      setErr('Microphone access denied: ' + e.message);
    }
  }

  function stopRec() {
    mediaRef.current?.stop();
    setRecording(false);
  }

  async function transcribeBlob(blob) {
    setBusy(true); setErr(null);
    try {
      const file = new File([blob], 'recording.webm', { type: blob.type });
      const res = await uploadAudio(file, language);
      if (!res.success) throw new Error(res.error || 'Transcription failed');
      setTranscript(res.transcript);
    } catch (e) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function handleUpload(e) {
    const f = e.target.files?.[0];
    if (!f) return;
    setBusy(true); setErr(null);
    try {
      const res = await uploadAudio(f, language);
      if (!res.success) throw new Error(res.error || 'Transcription failed');
      setTranscript(res.transcript);
    } catch (e2) {
      setErr(e2.message);
    } finally {
      setBusy(false);
    }
  }

  async function startSession() {
    if (!transcript.trim()) { setErr('Transcript empty'); return; }
    setBusy(true); setErr(null);
    try {
      const s = await api('/sessions/start', { method: 'POST', body: JSON.stringify({ transcript }) });
      setSession(s);
    } catch (e) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function sendAnswer() {
    if (!answer.trim() || !session) return;
    setBusy(true); setErr(null);
    try {
      const s = await api(`/sessions/${session.id}/answer`, { method: 'POST', body: JSON.stringify({ answer }) });
      setSession(s);
      setAnswer('');
    } catch (e) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function confirm() {
    if (!session) return;
    setBusy(true); setErr(null);
    try {
      const inc = await api(`/sessions/${session.id}/confirm`, { method: 'POST', body: JSON.stringify({ edited_fields: session.fields }) });
      setConfirmed(inc);
    } catch (e) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function readBack() {
    if (!session) return;
    const text = buildSummary(session.fields);
    try {
      const res = await api('/voice/tts', { method: 'POST', body: JSON.stringify({ text }) });
      if (!res.success) throw new Error(res.error);
      const audio = new Audio('data:' + res.mime + ';base64,' + res.audio_base64);
      audio.play();
    } catch (e) {
      // Fallback to browser speech synthesis
      if ('speechSynthesis' in window) {
        const u = new SpeechSynthesisUtterance(text);
        window.speechSynthesis.speak(u);
      } else {
        setErr('TTS: ' + e.message);
      }
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Voice Incident Report</h1>
      {err && <div className="text-red-400 text-sm bg-red-900/20 p-3 rounded">{err}</div>}

      {/* Recording controls */}
      <div className="glass rounded-xl p-6 space-y-4">
        <div className="flex flex-wrap items-center gap-3">
          <select value={language} onChange={e => setLanguage(e.target.value)} className="bg-slate-800 rounded px-3 py-2 text-sm">
            <option value="hi-IN">Hindi (hi-IN)</option>
            <option value="en-IN">English (en-IN)</option>
          </select>
          {!recording ? (
            <button onClick={startRec} className="flex items-center gap-2 bg-red-600 hover:bg-red-500 px-4 py-2 rounded-lg">
              <Mic size={18} /> Record
            </button>
          ) : (
            <button onClick={stopRec} className="flex items-center gap-2 bg-slate-700 hover:bg-slate-600 px-4 py-2 rounded-lg">
              <Square size={18} /> Stop
            </button>
          )}
          <label className="flex items-center gap-2 bg-slate-700 hover:bg-slate-600 px-4 py-2 rounded-lg cursor-pointer">
            <Upload size={18} /> Upload Audio
            <input type="file" accept="audio/*" className="hidden" onChange={handleUpload} />
          </label>
          {audioBlob && (
            <button onClick={() => transcribeBlob(audioBlob)} disabled={busy} className="bg-amber-500 text-slate-900 px-4 py-2 rounded-lg font-semibold">
              Transcribe Recording
            </button>
          )}
        </div>
        {recording && <div className="text-red-400 text-sm animate-pulse">Recording...</div>}
      </div>

      {/* Transcript */}
      <div className="glass rounded-xl p-6 space-y-3">
        <h2 className="font-semibold">Transcript</h2>
        <textarea
          value={transcript}
          onChange={e => setTranscript(e.target.value)}
          rows={4}
          placeholder="Transcript will appear here. You can also type/edit."
          className="w-full bg-slate-800 rounded p-3 text-sm"
        />
        <div className="flex gap-3">
          <button onClick={startSession} disabled={busy || !transcript.trim()} className="bg-amber-500 text-slate-900 px-4 py-2 rounded-lg font-semibold disabled:opacity-50">
            Analyze & Start Conversation
          </button>
        </div>
      </div>

      {/* Conversation */}
      {session && !confirmed && (
        <div className="glass rounded-xl p-6 space-y-4">
          <h2 className="font-semibold">AI Conversation</h2>
          <div className="text-sm text-slate-400">Confidence: {Math.round((session.confidence || 0) * 100)}% | Source: {session.source}</div>
          <div className="bg-slate-800 rounded p-3 text-sm">
            <div className="font-medium text-amber-400 mb-1">Extracted so far</div>
            <pre className="text-xs whitespace-pre-wrap">{JSON.stringify(session.fields, null, 2)}</pre>
            {session.missing_fields?.length > 0 && (
              <div className="mt-2 text-xs text-orange-400">Missing: {session.missing_fields.join(', ')}</div>
            )}
          </div>
          {session.questions?.length > 0 && session.status !== 'ready_for_confirmation' && (
            <div className="space-y-2">
              <div className="text-sm font-medium">Follow-up questions:</div>
              <ul className="list-disc pl-5 text-sm text-slate-300 space-y-1">
                {session.questions.map((q, i) => <li key={i}>{q}</li>)}
              </ul>
              <div className="flex gap-2 mt-2">
                <input value={answer} onChange={e => setAnswer(e.target.value)} placeholder="Type answer..." className="flex-1 bg-slate-800 rounded px-3 py-2 text-sm" />
                <button onClick={sendAnswer} disabled={busy || !answer.trim()} className="bg-blue-600 px-4 py-2 rounded-lg text-sm disabled:opacity-50">Send</button>
              </div>
              <button onClick={() => setSession(s => ({ ...s, status: 'ready_for_confirmation' }))} className="text-xs text-slate-400 hover:text-amber-400 underline">
                Skip remaining questions & proceed to confirmation
              </button>
            </div>
          )}
          {(session.status === 'ready_for_confirmation') && (
            <div className="space-y-3">
              <div className="text-green-400 text-sm">Ready for confirmation.</div>
              <div className="flex gap-3">
                <button onClick={readBack} className="flex items-center gap-2 bg-slate-700 px-4 py-2 rounded-lg text-sm"><Play size={16} /> Read Back (TTS)</button>
              </div>
              <ConfirmationForm session={session} setSession={setSession} confirm={confirm} busy={busy} />
            </div>
          )}
        </div>
      )}

      {confirmed && (
        <div className="glass rounded-xl p-6 space-y-2">
          <div className="flex items-center gap-2 text-green-400 font-semibold"><CheckCircle /> Incident Created: {confirmed.id}</div>
          <pre className="text-xs bg-slate-800 p-3 rounded overflow-auto">{JSON.stringify(confirmed, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

function ConfirmationForm({ session, setSession, confirm, busy }) {
  const f = session.fields;
  function upd(key, val) {
    setSession(s => ({ ...s, fields: { ...s.fields, [key]: val } }));
  }
  return (
    <div className="space-y-3">
      <div className="grid md:grid-cols-2 gap-3">
        <Field label="Machine ID" value={f.machine_id || ''} onChange={v => upd('machine_id', v)} />
        <Field label="Plant Area" value={f.plant_area || ''} onChange={v => upd('plant_area', v)} />
        <Field label="Category" value={f.category || ''} onChange={v => upd('category', v)} />
        <Field label="Severity" value={f.severity || ''} onChange={v => upd('severity', v)} />
        <Field label="Occurred At" value={f.occurred_at || ''} onChange={v => upd('occurred_at', v)} />
        <Field label="Sensor Readings (comma)" value={(f.sensor_readings || []).join(', ')} onChange={v => upd('sensor_readings', v.split(',').map(x=>x.trim()).filter(Boolean))} />
      </div>
      <div>
        <label className="text-xs text-slate-400">Description</label>
        <textarea value={f.description || ''} onChange={e => upd('description', e.target.value)} rows={3} className="w-full bg-slate-800 rounded p-2 text-sm" />
      </div>
      <div>
        <label className="text-xs text-slate-400">Actions Taken (comma)</label>
        <input value={(f.actions_taken || []).join(', ')} onChange={e => upd('actions_taken', e.target.value.split(',').map(x=>x.trim()).filter(Boolean))} className="w-full bg-slate-800 rounded p-2 text-sm" />
      </div>
      <button onClick={confirm} disabled={busy} className="bg-green-600 hover:bg-green-500 px-5 py-2 rounded-lg font-semibold disabled:opacity-50">
        Confirm & Create Incident
      </button>
    </div>
  );
}

function Field({ label, value, onChange }) {
  return (
    <div>
      <label className="text-xs text-slate-400">{label}</label>
      <input value={value} onChange={e => onChange(e.target.value)} className="w-full bg-slate-800 rounded p-2 text-sm" />
    </div>
  );
}

function buildSummary(fields) {
  return `Incident summary. Machine ${fields.machine_id || 'unknown'}. Area ${fields.plant_area || 'unknown'}. Issue: ${fields.description || ''}. Category ${fields.category}. Severity ${fields.severity}. Occurred at ${fields.occurred_at || 'unknown'}. Sensor readings: ${(fields.sensor_readings || []).join(', ') || 'none'}. Actions taken: ${(fields.actions_taken || []).join(', ') || 'none'}. Please confirm or correct.`;
}
