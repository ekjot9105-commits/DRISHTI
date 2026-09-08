import React from 'react';
import {
  Shield, Eye, Database, ArrowRight, Activity, Camera, Bell,
  GraduationCap, Banknote, TrafficCone, Home, Factory, Flame, Users, Zap,
} from 'lucide-react';

/**
 * Landing — product page for DRISHTI, a universal AI safety monitoring
 * platform. Same dark command-center aesthetic as the app; the language is
 * deliberately sector-neutral so schools, shops and factories see themselves
 * in it rather than a defence installation.
 */

const FEATURES = [
  {
    icon: Zap,
    title: 'Detects What Matters',
    desc: 'Fights, fire and smoke, line crossings, loitering and crowding — recognised as they happen, not found later in the footage.',
  },
  {
    icon: Bell,
    title: 'Tells The Right People',
    desc: 'Desktop alerts, an audible alarm and an email with the evidence frame attached, all within seconds of the incident.',
  },
  {
    icon: Camera,
    title: 'Uses Your Cameras',
    desc: 'Works with the CCTV, RTSP streams and phones you already own. No proprietary hardware, no rip-and-replace.',
  },
  {
    icon: Database,
    title: 'Keeps The Proof',
    desc: 'Every incident captures a snapshot, a cryptographic hash and a one-click PDF report you can hand to anyone.',
  },
];

// 3.1 — use-case showcase. Each card names the detectors that actually apply.
const USE_CASES = [
  {
    icon: GraduationCap,
    place: 'Schools & Campuses',
    line: 'Catch a corridor fight in seconds and get staff moving before it escalates.',
    detectors: ['Fight', 'Crowd', 'Intrusion'],
    accent: 'text-violet-400',
    ring: 'group-hover:border-violet-500/40',
  },
  {
    icon: Banknote,
    place: 'ATMs & Bank Lobbies',
    line: 'Know when someone lingers at the machine after hours, or forces the door.',
    detectors: ['Loitering', 'Intrusion', 'Fight'],
    accent: 'text-emerald-400',
    ring: 'group-hover:border-emerald-500/40',
  },
  {
    icon: TrafficCone,
    place: 'Streets & Public Spaces',
    line: 'Spot a brawl or a gathering crowd on a public camera and alert patrols early.',
    detectors: ['Fight', 'Crowd', 'Fleeing'],
    accent: 'text-amber-400',
    ring: 'group-hover:border-amber-500/40',
  },
  {
    icon: Home,
    place: 'Homes & Apartments',
    line: 'A tripwire across the driveway, and a kitchen fire flagged the moment it starts.',
    detectors: ['Intrusion', 'Fire', 'Watchlist'],
    accent: 'text-cyan-400',
    ring: 'group-hover:border-cyan-500/40',
  },
  {
    icon: Factory,
    place: 'Factories & Warehouses',
    line: 'Restricted-zone entry and early fire detection on floors nobody is watching at 3am.',
    detectors: ['Fire', 'Intrusion', 'Loitering'],
    accent: 'text-rose-400',
    ring: 'group-hover:border-rose-500/40',
  },
];

const DETECTOR_ICONS = { Fight: Users, Fire: Flame, Crowd: Users, Intrusion: Shield };

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
            <span className="text-xl font-bold tracking-widest text-cyan-50 text-shadow-sm">
              DRISHTI <span className="text-cyan-500 opacity-60">//</span>{' '}
              <span className="text-sm font-normal tracking-wider text-slate-400">SAFETY MONITORING</span>
            </span>
          </div>
          <div className="flex items-center gap-6 text-sm font-mono tracking-wider text-slate-400">
            <span className="hidden sm:block">RUNS ON YOUR EXISTING CAMERAS</span>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span className="text-emerald-500">SYSTEM ONLINE</span>
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
              AI SAFETY MONITORING PLATFORM
            </div>

            <h1 className="text-5xl lg:text-7xl font-extrabold text-white tracking-tight mb-6 leading-tight">
              See everything.<br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">Miss nothing.</span>
            </h1>

            <p className="text-lg text-slate-400 mb-10 leading-relaxed max-w-xl">
              Most cameras only matter after something has gone wrong. DRISHTI watches
              them live and raises the alarm as it happens — a fight breaking out, a fire
              starting, someone crossing a line they shouldn't. Schools, shops, streets,
              homes and factories, on the cameras you already have.
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

            <div className="flex flex-wrap items-center gap-x-6 gap-y-2 mt-8 text-xs font-mono text-slate-500">
              <span className="flex items-center gap-1.5"><Users className="w-3.5 h-3.5" /> FIGHT</span>
              <span className="flex items-center gap-1.5"><Flame className="w-3.5 h-3.5" /> FIRE &amp; SMOKE</span>
              <span className="flex items-center gap-1.5"><Shield className="w-3.5 h-3.5" /> INTRUSION</span>
              <span className="flex items-center gap-1.5"><Eye className="w-3.5 h-3.5" /> LOITERING</span>
              <span className="flex items-center gap-1.5"><Activity className="w-3.5 h-3.5" /> CROWDING</span>
            </div>
          </div>

          {/* Abstract HUD Graphic */}
          <div className="relative aspect-square lg:aspect-auto lg:h-[500px] w-full rounded-2xl border border-slate-800 bg-slate-900/50 backdrop-blur-sm overflow-hidden flex items-center justify-center p-8 group">
            <div className="absolute inset-0 bg-slate-900 opacity-40 group-hover:scale-105 transition-transform duration-700" />

            <div className="relative w-full h-full border border-cyan-500/30 rounded-xl p-6 flex flex-col justify-between">
              {/* Live-watch pulse */}
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-48 h-48 border border-cyan-500/20 rounded-full flex items-center justify-center">
                <div className="w-32 h-32 border-t border-b border-cyan-400 animate-[spin_4s_linear_infinite]" />
                <Eye className="absolute w-8 h-8 text-cyan-500/50" />
              </div>

              <div className="flex justify-between items-start font-mono text-xs text-cyan-500/70">
                <div className="flex flex-col gap-1">
                  <span>UPTIME // 99.4%</span>
                  <span>LATENCY // 24ms</span>
                </div>
                <span>[ LIVE FEED ]</span>
              </div>

              <div className="flex justify-between items-end font-mono text-xs text-cyan-500/70">
                <span>4 CAMERAS // 0 INCIDENTS</span>
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

        {/* ---- 3.1 Use-case showcase ---- */}
        <section className="mt-32">
          <div className="max-w-2xl mb-10">
            <h2 className="text-3xl lg:text-4xl font-bold text-white tracking-tight mb-3">
              One system. Every kind of space.
            </h2>
            <p className="text-slate-400 leading-relaxed">
              The same detectors protect very different places — only the rules change.
              Point DRISHTI at a camera and choose what it should watch for.
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {USE_CASES.map((uc) => (
              <div
                key={uc.place}
                className={`group p-6 rounded-xl border border-slate-800 bg-slate-800/20 hover:bg-slate-800/40 transition-colors ${uc.ring}`}
              >
                <uc.icon className={`w-9 h-9 ${uc.accent} mb-4`} strokeWidth={1.5} />
                <h3 className="text-lg font-semibold text-white mb-2">{uc.place}</h3>
                <p className="text-sm text-slate-400 leading-relaxed mb-4">{uc.line}</p>
                <div className="flex flex-wrap gap-1.5">
                  {uc.detectors.map((d) => {
                    const Icon = DETECTOR_ICONS[d];
                    return (
                      <span
                        key={d}
                        className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border border-slate-700 bg-slate-900/60 text-[11px] font-mono tracking-wide text-slate-300"
                      >
                        {Icon && <Icon className="w-3 h-3" />}
                        {d.toUpperCase()}
                      </span>
                    );
                  })}
                </div>
              </div>
            ))}

            {/* Closing card — ties the grid back to the product */}
            <div className="p-6 rounded-xl border border-cyan-500/30 bg-cyan-500/5 flex flex-col justify-between">
              <div>
                <Activity className="w-9 h-9 text-cyan-400 mb-4" strokeWidth={1.5} />
                <h3 className="text-lg font-semibold text-white mb-2">Somewhere else?</h3>
                <p className="text-sm text-slate-400 leading-relaxed">
                  Every detector is independent and can be switched on per camera, so the
                  same install covers a car park, a stairwell or a server room.
                </p>
              </div>
              <button
                onClick={() => onNavigate('cameras')}
                className="mt-4 inline-flex items-center gap-2 text-sm font-semibold text-cyan-400 hover:text-cyan-300 transition-colors"
              >
                Add a camera <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </section>

        {/* Feature Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mt-24">
          {FEATURES.map((feature) => (
            <div key={feature.title} className="p-6 rounded-xl border border-slate-800 bg-slate-800/20 hover:bg-slate-800/40 transition-colors">
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
