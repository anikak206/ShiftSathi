export default function NotFound() {
  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <div className="text-center">
        <div className="text-6xl font-bold text-amber-500 mb-2">404</div>
        <div className="text-slate-400 mb-4">Page not found</div>
        <a href="/" className="text-amber-400 hover:underline">Go home</a>
      </div>
    </div>
  );
}
