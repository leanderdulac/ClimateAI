import { Loader2 } from 'lucide-react';

export function PageLoader() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-b from-slate-950 to-slate-900">
      <div className="flex flex-col items-center gap-4">
        <Loader2 className="w-12 h-12 text-cyan-500 animate-spin" />
        <p className="text-slate-400 text-sm">Carregando página...</p>
      </div>
    </div>
  );
}
