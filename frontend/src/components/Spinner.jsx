export default function Spinner({ label = 'Loading...' }) {
  return (
    <div className="flex items-center gap-2 text-slate-400 text-sm">
      <div className="w-4 h-4 border-2 border-slate-600 border-t-amber-500 rounded-full animate-spin" />
      {label}
    </div>
  );
}
