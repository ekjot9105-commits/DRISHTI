export default function LiveTicker() {
  return (
    <div className="fixed bottom-0 left-0 w-full bg-[#030712]/90 backdrop-blur-md border-t border-cyan-900/50 z-50 overflow-hidden h-8 flex items-center pointer-events-none">
      <div className="absolute bottom-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-cyan-500/50 to-transparent"></div>
      <div className="ticker-track flex whitespace-nowrap text-[10px] sm:text-xs font-mono text-cyan-500/70 tracking-widest">
        {[1, 2].map((idx) => (
          <div key={idx} className="flex items-center gap-8 px-8">
            <span className="flex items-center gap-2"><div className="w-1.5 h-1.5 bg-cyan-500 rounded-full animate-pulse"></div> THROUGHPUT: 12,847 FPS</span>
            <span>•</span><span>ACTIVE_NODES: 247</span>
            <span>•</span><span>UPTIME: 99.98%</span>
            <span>•</span><span>LAST_SYNC: 0.4s</span>
            <span>•</span><span className="text-cyan-400">THREATS_RESOLVED_TODAY: 1,204</span>
            <span>•</span><span>ENCRYPTION: SHA-256</span>
            <span>•</span><span>BLOCK HEIGHT: 8,093</span><span>•</span>
          </div>
        ))}
      </div>
    </div>
  );
}
