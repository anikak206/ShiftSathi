import { Component } from 'react';

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  componentDidCatch(error, info) {
    console.error('ShiftSathi error:', error, info);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center p-6">
          <div className="glass rounded-xl p-6 max-w-md text-center">
            <h1 className="text-xl font-bold mb-2">Something went wrong</h1>
            <p className="text-sm text-slate-400 mb-4">{String(this.state.error)}</p>
            <button onClick={() => window.location.reload()} className="bg-amber-500 text-slate-900 px-4 py-2 rounded-lg font-semibold">
              Reload
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
