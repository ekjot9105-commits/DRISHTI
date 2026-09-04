import React from 'react';
import { Shield, Eye, Database, Crosshair, ArrowRight, Activity, Camera, Lock } from 'lucide-react';

const Landing = ({ onNavigate }) => {
  return (
    <div className="fixed inset-0 z-[100] bg-[#0b1120] text-slate-300 font-sans selection:bg-cyan-500/30 overflow-y-auto">
      {/* Dynamic Background Effects */}
      <div className="absolute inset-0 z-0 opacity-20 pointer-events-none" 
           style={{ backgroundImage: 'linear-gradient(#06b6d4 1px, transparent 1px), linear-gradient(90deg, #06b6d4 1px, transparent 1px)', backgroundSize: '40px 40px' }} />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-cyan-900/20 rounded-full blur-[120px] pointer-events-none" />

      {/* Navigation */}
      <nav className="relative z-10 border-b border-slate-800/60 bg-[#0b1120]/80 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Shield className="w-6 h-6 text-cyan-500" />
            <span className="text-xl font-bold tracking-widest text-cyan-50 text-shadow-sm">DRISHTI <span className="text-cyan-500 opacity-60">//</span> IBVAP</span>
          </div>
          <div className="flex items-center gap-6 text-sm font-mono tracking-wider text-slate-400">
            <span className="hidden sm:block">SIH PS-26187</span>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span className="text-emerald-500">SYSTEM SECURE</span>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="relative z-10 max-w-7xl mx-auto px-6 pt-24 pb-16 lg:pt-32">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-8 items-center">
          <div className="max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs font-mono tracking-wide mb-6">
              <Activity className="w-4 h-4" />
              INTELLIGENT BORDER VIDEO ANALYTICS PLATFORM
            </div>
            
            <h1 className="text-5xl lg:text-7xl font-extrabold text-white tracking-tight mb-6 leading-tight">
              Tactical Vision.<br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">Absolute Security.</span>
            </h1>
            
            <p className="text-lg text-slate-400 mb-10 leading-relaxed max-w-xl">
              Next-generation military surveillance platform powered by real-time computer vision. Protect perimeters, identify threats instantly, and maintain automated cryptographic evidence logs without human fatigue.
            </p>

            <div className="flex flex-col sm:flex-row gap-4">
              <button 
                onClick={() => onNavigate('dashboard')}
                className="group relative inline-flex items-center justify-center gap-3 px-8 py-4 bg-cyan-500 hover:bg-cyan-400 transition-all rounded-lg overflow-hidden font-bold text-slate-900 tracking-wide"
              >
                <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform" />
                <span className="relative">ENTER COMMAND CENTER</span>
                <ArrowRight className="w-5 h-5 relative group-hover:translate-x-1 transition-transform" />
              </button>
              

            </div>
          </div>

          {/* Abstract HUD Graphic */}
          <div className="relative aspect-square lg:aspect-auto lg:h-[500px] w-full rounded-2xl border border-slate-800 bg-slate-900/50 backdrop-blur-sm overflow-hidden flex items-center justify-center p-8 group">
            <div className="absolute inset-0 bg-slate-900 opacity-40 group-hover:scale-105 transition-transform duration-700" />
            
            <div className="relative w-full h-full border border-cyan-500/30 rounded-xl p-6 flex flex-col justify-between">
               {/* Targeting Crosshair */}
               <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-48 h-48 border border-cyan-500/20 rounded-full flex items-center justify-center">
                  <div className="w-32 h-32 border-t border-b border-cyan-400 animate-[spin_4s_linear_infinite]" />
                  <Crosshair className="absolute w-8 h-8 text-cyan-500/50" />
               </div>

               <div className="flex justify-between items-start font-mono text-xs text-cyan-500/70">
                  <div className="flex flex-col gap-1">
                    <span>SYS.OP // 99.4%</span>
                    <span>LAT // 24ms</span>
                  </div>
                  <span>[ LIVE FEED OVL ]</span>
               </div>
               
               <div className="flex justify-between items-end font-mono text-xs text-cyan-500/70">
                  <span>COORD // 28.6139° N, 77.2090° E</span>
                  <div className="flex gap-1">
                    <div className="w-1 h-3 bg-cyan-500" />
                    <div className="w-1 h-4 bg-cyan-500" />
                    <div className="w-1 h-2 bg-cyan-500" />
                    <div className="w-1 h-5 bg-cyan-500" />
                  </div>
               </div>
            </div>
          </div>
        </div>

        {/* Feature Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mt-32">
          {[
            { icon: Eye, title: "Watchlist Recognition", desc: "Real-time face & ALPR detection with specialized Authorized Personnel bypass rules." },
            { icon: Crosshair, title: "Tripwire Defense", desc: "Military-grade perimeter detection using macro-trajectory vectors and directional intrusion tracking." },
            { icon: Camera, title: "Multi-Cam Sync", desc: "Process concurrent RTSP video streams with GPU-accelerated asynchronous inference pipelines." },
            { icon: Database, title: "Evidence Vault", desc: "Immutable SQLite logging with automatic PDF report generation for every critical incident." },
          ].map((feature, i) => (
            <div key={i} className="p-6 rounded-xl border border-slate-800 bg-slate-800/20 hover:bg-slate-800/40 transition-colors">
              <feature.icon className="w-10 h-10 text-cyan-400 mb-4" strokeWidth={1.5} />
              <h3 className="text-lg font-semibold text-white mb-2">{feature.title}</h3>
              <p className="text-sm text-slate-400 leading-relaxed">{feature.desc}</p>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
};

export default Landing;
