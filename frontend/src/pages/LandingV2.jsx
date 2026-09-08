import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence, useMotionValue, useSpring, useTransform } from 'framer-motion';
import { Shield, Zap, Activity, Camera, AlertCircle, MapPin, Target } from 'lucide-react';
import _CountUp from 'react-countup';
const CountUp = _CountUp.default || _CountUp;
import _Globe from 'react-globe.gl';
const Globe = _Globe.default || _Globe;

import BootSequence from '../components/Landing/BootSequence';
import LiveTicker from '../components/Landing/LiveTicker';
import HowItWorks from '../components/Landing/HowItWorks';
import TechStack from '../components/Landing/TechStack';
import DemoPreview from '../components/Landing/DemoPreview';

const CITIES = [
  { name: "Mumbai, IND", lat: 19.0760, lng: 72.8777 },
  { name: "London, UK", lat: 51.5074, lng: -0.1278 },
  { name: "New York, USA", lat: 40.7128, lng: -74.0060 },
  { name: "Tokyo, JPN", lat: 35.6762, lng: 139.6503 },
  { name: "Dubai, UAE", lat: 25.2048, lng: 55.2708 }
];

const CAMERA_FEEDS = [
  { id: 'CAM-04', type: 'FIGHT DETECTED', prob: '98.2%', color: 'text-red-500', border: 'border-red-500', bg: 'bg-red-500/10' },
  { id: 'CAM-12', type: 'SUSPICIOUS LOITERING', prob: '86.4%', color: 'text-yellow-500', border: 'border-yellow-500', bg: 'bg-yellow-500/10' },
  { id: 'CAM-02', type: 'WEAPON SPOTTED', prob: '99.1%', color: 'text-red-500', border: 'border-red-500', bg: 'bg-red-500/10' }
];

const MockCameraFeed = () => {
  const [feedIdx, setFeedIdx] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setFeedIdx(prev => (prev + 1) % CAMERA_FEEDS.length);
    }, 5500);
    return () => clearInterval(interval);
  }, []);

  const feed = CAMERA_FEEDS[feedIdx];

  return (
    <motion.div initial={{ opacity: 0, x: 50 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 1, duration: 0.8 }} className="absolute bottom-10 -left-16 z-30 w-72 h-48 bg-[#030712]/80 backdrop-blur-md border border-cyan-500/30 rounded-lg overflow-hidden shadow-[0_0_30px_rgba(34,211,238,0.15)] group">
      <div className="absolute top-1/2 -right-32 w-32 h-[1px] bg-gradient-to-r from-cyan-500/80 to-transparent pointer-events-none z-0"></div>
      <div className={`absolute top-2 left-2 w-4 h-4 border-t-2 border-l-2 ${feed.border} transition-colors`}></div>
      <div className={`absolute top-2 right-2 w-4 h-4 border-t-2 border-r-2 ${feed.border} transition-colors`}></div>
      <div className={`absolute bottom-2 left-2 w-4 h-4 border-b-2 border-l-2 ${feed.border} transition-colors`}></div>
      <div className={`absolute bottom-2 right-2 w-4 h-4 border-b-2 border-r-2 ${feed.border} transition-colors`}></div>
      <div className="absolute top-0 left-0 w-full px-3 py-1.5 flex justify-between items-center bg-black/40 border-b border-cyan-500/30 z-10 backdrop-blur-sm">
        <div className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></div><span className="text-[10px] font-mono text-cyan-300 tracking-wider">{feed.id} [LIVE]</span></div>
        <span className="text-[10px] font-mono text-cyan-500/70">REC</span>
      </div>
      <div className="absolute inset-0 flex items-center justify-center opacity-70">
        <svg viewBox="0 0 100 100" className="w-24 h-24 mt-4 drop-shadow-[0_0_5px_rgba(34,211,238,0.8)]">
          <line x1="50" y1="20" x2="50" y2="50" stroke="#22d3ee" strokeWidth="2" strokeDasharray="2,2" />
          <line x1="50" y1="30" x2="30" y2="45" stroke="#22d3ee" strokeWidth="2" />
          <line x1="50" y1="30" x2="70" y2="45" stroke="#22d3ee" strokeWidth="2" />
          <line x1="30" y1="45" x2="25" y2="65" stroke="#22d3ee" strokeWidth="2" />
          <line x1="70" y1="45" x2="75" y2="65" stroke="#22d3ee" strokeWidth="2" />
          <line x1="50" y1="50" x2="40" y2="75" stroke="#22d3ee" strokeWidth="2" />
          <line x1="50" y1="50" x2="60" y2="75" stroke="#22d3ee" strokeWidth="2" />
          <line x1="40" y1="75" x2="40" y2="95" stroke="#22d3ee" strokeWidth="2" />
          <line x1="60" y1="75" x2="60" y2="95" stroke="#22d3ee" strokeWidth="2" />
          <circle cx="50" cy="15" r="6" fill="transparent" stroke="#22d3ee" strokeWidth="2" />
          <circle cx="50" cy="30" r="3" fill="#22d3ee" /><circle cx="30" cy="45" r="3" fill="#22d3ee" /><circle cx="70" cy="45" r="3" fill="#22d3ee" />
          <circle cx="25" cy="65" r="3" fill="#22d3ee" /><circle cx="75" cy="65" r="3" fill="#22d3ee" /><circle cx="50" cy="50" r="3" fill="#22d3ee" />
          <circle cx="40" cy="75" r="3" fill="#22d3ee" /><circle cx="60" cy="75" r="3" fill="#22d3ee" /><circle cx="40" cy="95" r="3" fill="#22d3ee" />
          <circle cx="60" cy="95" r="3" fill="#22d3ee" />
        </svg>
      </div>
      <AnimatePresence mode="wait">
        <motion.div key={feedIdx} initial={{ scale: 1.2, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 1.1, opacity: 0 }} transition={{ duration: 0.4 }} className={`absolute top-1/4 left-1/4 w-1/2 h-1/2 border ${feed.border} ${feed.bg} flex flex-col justify-end p-1`}>
          <span className={`text-[8px] font-mono ${feed.color} bg-black/60 px-1 w-fit border ${feed.border} backdrop-blur-sm whitespace-nowrap`}>{feed.type}: {feed.prob}</span>
        </motion.div>
      </AnimatePresence>
      <div className="scan-line absolute top-0 left-0 w-full h-full bg-gradient-to-b from-transparent via-cyan-400/20 to-transparent pointer-events-none"></div>
    </motion.div>
  );
};

export default function LandingV2({ onNavigate }) {
  const globeEl = useRef();
  
  const [nodes, setNodes] = useState([]);
  const [arcs, setArcs] = useState([]);
  const [rings, setRings] = useState([]);
  const [activeAlert, setActiveAlert] = useState(0);
  const [timeSinceAlert, setTimeSinceAlert] = useState(0);
  const [booting, setBooting] = useState(true);
  const [utcTime, setUtcTime] = useState("");

  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);
  const smoothMouseX = useSpring(mouseX, { damping: 25, stiffness: 150 });
  const smoothMouseY = useSpring(mouseY, { damping: 25, stiffness: 150 });
  const rotateX = useTransform(smoothMouseY, [0, typeof window !== 'undefined' ? window.innerHeight : 1000], [5, -5]);
  const rotateY = useTransform(smoothMouseX, [0, typeof window !== 'undefined' ? window.innerWidth : 1000], [-5, 5]);
  const bgTransform = useTransform(
    [smoothMouseX, smoothMouseY],
    ([x, y]) => `radial-gradient(800px circle at ${x}px ${y}px, rgba(34, 211, 238, 0.05), transparent 40%)`
  );

  const handleMouseMove = (e) => {
    mouseX.set(e.clientX);
    mouseY.set(e.clientY);
  };

  const mockAlerts = [
    { city: "Mumbai, IND", type: "Fight Detected", confidence: "98.2%", level: "CRITICAL" },
    { city: "London, UK", type: "Suspicious Loitering", confidence: "94.5%", level: "WARNING" },
    { city: "New York, USA", type: "Weapon Spotted", confidence: "99.1%", level: "CRITICAL" },
    { city: "Tokyo, JPN", type: "Perimeter Breach", confidence: "96.4%", level: "WARNING" }
  ];

  useEffect(() => {
    const gNodes = CITIES.map(city => ({ ...city, size: 0.5, color: Math.random() > 0.5 ? '#ef4444' : '#06b6d4' }));
    setNodes(gNodes); setRings(gNodes);

    const gArcs = [];
    for(let i=0; i<15; i++) {
      const src = CITIES[Math.floor(Math.random() * CITIES.length)];
      const dst = CITIES[Math.floor(Math.random() * CITIES.length)];
      if (src.name !== dst.name) {
        gArcs.push({ startLat: src.lat, startLng: src.lng, endLat: dst.lat, endLng: dst.lng, color: ['rgba(34, 211, 238, 0.1)', 'rgba(34, 211, 238, 0.9)'] });
      }
    }
    setArcs(gArcs);

    setTimeout(() => {
      if (globeEl.current && globeEl.current.controls()) {
        globeEl.current.controls().autoRotate = true;
        // Slow drift: a full revolution takes roughly 3 minutes, so the globe
        // reads as alive without pulling the eye off the hero copy.
        globeEl.current.controls().autoRotateSpeed = 0.35;
        globeEl.current.controls().enableZoom = false;
        globeEl.current.pointOfView({ lat: 25, lng: 60, altitude: 2.2 });
      }
    }, 1000);

    const alertInterval = setInterval(() => { setActiveAlert(prev => (prev + 1) % mockAlerts.length); setTimeSinceAlert(0); }, 4500);
    const timerInterval = setInterval(() => { setTimeSinceAlert(prev => prev + 1); }, 1000);
    const clockInterval = setInterval(() => { setUtcTime(new Date().toISOString().substring(11, 19)); }, 1000);

    return () => { clearInterval(alertInterval); clearInterval(timerInterval); clearInterval(clockInterval); };
  }, []);

  const formatTime = (seconds) => seconds === 0 ? "Just now" : `${seconds}s ago`;

  return (
    <>
      <BootSequence onComplete={() => setBooting(false)} />
      {!booting && (
        <div className="min-h-screen bg-[#030712] text-gray-200 font-sans selection:bg-cyan-500/30 overflow-x-hidden relative" onMouseMove={handleMouseMove}>
          <style dangerouslySetInnerHTML={{__html: `
            .font-mono { font-family: 'JetBrains Mono', monospace; }
            .bg-grid { background-size: 50px 50px; background-image: linear-gradient(to right, rgba(34, 211, 238, 0.05) 1px, transparent 1px), linear-gradient(to bottom, rgba(34, 211, 238, 0.05) 1px, transparent 1px); animation: gridMove 20s linear infinite; }
            @keyframes gridMove { 0% { transform: translateY(0); } 100% { transform: translateY(50px); } }
            .bg-noise { background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E"); opacity: 0.03; pointer-events: none; }
            @keyframes scan { 0% { transform: translateY(-100%); } 100% { transform: translateY(100%); } }
            .scan-line { animation: scan 2.5s infinite linear; }
            .btn-sweep { position: relative; overflow: hidden; }
            .btn-sweep::after { content: ''; position: absolute; top: 0; left: -100%; width: 50%; height: 100%; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent); transform: skewX(-20deg); transition: 0s; }
            .btn-sweep:hover::after { animation: sweep 1s ease-out forwards; }
            @keyframes sweep { 0% { left: -100%; } 100% { left: 200%; } }
            .radar-sweep { background: conic-gradient(from 0deg at 50% 50%, transparent 70%, rgba(34, 211, 238, 0.1) 100%); border-radius: 50%; animation: rotateRadar 6s linear infinite; }
            @keyframes rotateRadar { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
            .ticker-track { animation: marquee 30s linear infinite; }
            @keyframes marquee { 0% { transform: translateX(0); } 100% { transform: translateX(-50%); } }
          `}} />

          <motion.div className="pointer-events-none fixed inset-0 z-0 transition-opacity duration-300" style={{ background: bgTransform }} />
          <div className="fixed inset-0 z-0 bg-[#030712]"><div className="absolute inset-0 bg-grid"></div><div className="absolute inset-0 bg-noise mix-blend-overlay"></div><div className="absolute top-1/4 left-1/4 w-[600px] h-[600px] bg-cyan-900/10 rounded-full blur-[150px] mix-blend-screen pointer-events-none"></div></div>

          <nav className="fixed top-0 w-full z-50 bg-[#030712]/80 backdrop-blur-xl border-b border-cyan-900/40">
            <div className="absolute bottom-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-cyan-400 to-transparent opacity-50"></div>
            <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
              <div className="flex items-center gap-3 group cursor-pointer">
                <div className="relative flex items-center justify-center w-10 h-10">
                  <div className="absolute inset-0 border border-cyan-500/30 rounded-full animate-[spin_4s_linear_infinite] group-hover:border-cyan-400/80 transition-colors"></div>
                  <div className="absolute inset-1 border border-cyan-500/10 rounded-full animate-[spin_3s_linear_infinite_reverse]"></div>
                  <div className="absolute inset-0 bg-cyan-500 blur-md opacity-20 group-hover:opacity-40 transition-opacity"></div>
                  <Shield className="w-5 h-5 text-cyan-400 relative z-10" />
                </div>
                <div className="flex flex-col"><span className="text-xl font-black tracking-widest text-white leading-none">DRISHTI</span><span className="text-[8px] font-mono text-cyan-500/60 tracking-[0.2em] uppercase">Global Overwatch</span></div>
              </div>
              <div className="hidden lg:flex items-center gap-8 px-8 py-2 bg-[#0a1122]/50 border border-cyan-900/30 rounded shadow-[inset_0_0_15px_rgba(34,211,238,0.05)]">
                <div className="flex items-center gap-2 text-[10px] font-mono text-cyan-500/70"><div className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></div>LINK: <span className="text-green-400">OPTIMAL</span></div>
                <div className="w-px h-3 bg-cyan-900/50"></div>
                <div className="flex items-center gap-2 text-[10px] font-mono text-cyan-500/70"><Activity className="w-3 h-3 text-cyan-500" />LOAD: <span className="text-cyan-400">24%</span></div>
                <div className="w-px h-3 bg-cyan-900/50"></div>
                <div className="flex items-center gap-2 text-[10px] font-mono text-cyan-400 font-bold tracking-widest w-20 justify-center">{utcTime} Z</div>
              </div>

            </div>
          </nav>

          <section className="relative pt-32 pb-20 px-6 min-h-screen flex items-center z-10 max-w-7xl mx-auto">
            <div className="flex flex-col lg:flex-row items-center w-full gap-12">
              <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8 }} className="w-full lg:w-1/2 relative z-20">
                <div className="mb-8 inline-flex items-center gap-3 px-4 py-1.5 rounded-sm bg-cyan-950/40 border border-cyan-800/60 backdrop-blur-md shadow-[0_0_15px_rgba(8,145,178,0.2)]">
                  <span className="relative flex h-2 w-2"><span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span><span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500"></span></span>
                  <span className="text-cyan-400 text-xs font-mono font-bold tracking-widest">SYSTEM ONLINE • V3.4 ACTIVE</span>
                </div>
                
                <h1 className="text-5xl lg:text-6xl xl:text-7xl font-bold text-white leading-[1.1] mb-6 tracking-tight">
                  Ordinary Cameras.<br/><span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-600 drop-shadow-lg">Extraordinary Intelligence.</span>
                </h1>
                
                <p className="text-lg lg:text-xl text-slate-400 mb-10 leading-relaxed max-w-lg font-light">Transform any ordinary camera into an intelligent threat-detection node. Real-time alerts. Immutable blockchain evidence. Complete situational awareness.</p>

                <div className="flex flex-col sm:flex-row gap-5">
                  <button onClick={() => onNavigate('dashboard')} className="btn-sweep px-8 py-4 bg-cyan-500/10 border border-cyan-400 text-cyan-300 rounded font-mono font-bold text-sm tracking-wider hover:bg-cyan-500 hover:text-gray-900 shadow-[0_0_20px_rgba(34,211,238,0.2)] hover:shadow-[0_0_40px_rgba(34,211,238,0.6)] transition-all flex items-center justify-center gap-3 group"><Activity className="w-5 h-5 group-hover:animate-pulse" />OPEN COMMAND CENTER</button>
                  <button onClick={() => window.location.href='/phone'} className="px-8 py-4 bg-[#0a1122]/80 backdrop-blur-md border border-slate-700 text-slate-300 rounded font-mono font-bold text-sm tracking-wider hover:border-slate-500 hover:text-white transition-all flex items-center justify-center gap-3"><Camera className="w-5 h-5" />JOIN AS CAMERA</button>
                </div>
                
                <div className="flex gap-8 mt-16 p-6 rounded bg-[#0a1122]/60 border border-cyan-900/50 backdrop-blur-xl shadow-2xl inline-flex group hover:border-cyan-500/50 transition-all duration-500">
                  <div className="relative"><div className="absolute -inset-2 bg-cyan-500/0 group-hover:bg-cyan-500/10 blur rounded transition-all"></div><div className="flex items-center gap-2 mb-1"><Target className="w-3 h-3 text-cyan-500 animate-pulse" /><div className="text-xs font-mono font-bold text-slate-400 uppercase tracking-widest">AI Accuracy</div></div><div className="text-3xl font-mono font-black text-cyan-50"><CountUp end={99.7} decimals={1} duration={1.2} />%</div></div><div className="w-px bg-cyan-900/50"></div>
                  <div className="relative"><div className="flex items-center gap-2 mb-1"><Zap className="w-3 h-3 text-cyan-500" /><div className="text-xs font-mono font-bold text-slate-400 uppercase tracking-widest">Avg Latency</div></div><div className="text-3xl font-mono font-black text-cyan-50"><CountUp end={45} duration={1.2} />ms</div></div><div className="w-px bg-cyan-900/50"></div>
                  <div className="relative"><div className="flex items-center gap-2 mb-1"><Shield className="w-3 h-3 text-cyan-500" /><div className="text-xs font-mono font-bold text-slate-400 uppercase tracking-widest">Encryption</div></div><div className="text-3xl font-mono font-black text-cyan-50"><CountUp end={256} duration={1.2} /><span className="text-lg text-cyan-500/50 ml-1">bit</span></div></div>
                </div>
              </motion.div>

              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 1.5, delay: 0.2 }} className="w-full lg:w-1/2 flex justify-center relative h-[600px] perspective-[1000px]" style={{ rotateX, rotateY }}>
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-40"><div className="w-[500px] h-[500px] radar-sweep"></div></div>
                <MockCameraFeed />
                <AnimatePresence mode="wait">
                  <motion.div key={activeAlert} initial={{ opacity: 0, x: 50, scale: 0.95 }} animate={{ opacity: 1, x: 0, scale: 1 }} exit={{ opacity: 0, x: -20, scale: 0.95 }} transition={{ duration: 0.4 }} className="absolute top-10 right-0 z-30 bg-[#030712]/80 backdrop-blur-xl border-l-4 border-l-red-500 border-t border-r border-b border-white/10 p-4 rounded shadow-[0_10px_40px_rgba(239,68,68,0.15)] flex items-start gap-4 w-72">
                    <div className="absolute top-1/2 -left-32 w-32 h-[1px] bg-gradient-to-l from-red-500/80 to-transparent pointer-events-none z-0"></div>
                    <div className="bg-red-500/10 p-2 border border-red-500/30"><AlertCircle className="w-5 h-5 text-red-500 animate-pulse" /></div>
                    <div className="flex-1">
                      <div className="flex justify-between items-start mb-1"><div className="text-red-400 font-mono font-bold text-sm tracking-wide flex items-center gap-2">{mockAlerts[activeAlert].level === "CRITICAL" && <span className="w-1.5 h-1.5 bg-red-500 rounded-full animate-ping"></span>}{mockAlerts[activeAlert].type}</div></div>
                      <div className="flex items-center gap-1 text-slate-300 font-mono text-[11px] mb-2"><MapPin className="w-3 h-3 text-cyan-500" /> {mockAlerts[activeAlert].city}</div>
                      <div className="flex justify-between items-end mt-2 pt-2 border-t border-white/5"><div className="text-[10px] font-mono text-slate-500 uppercase">CONF: <span className="text-cyan-400">{mockAlerts[activeAlert].confidence}</span></div><div className="text-[10px] font-mono text-slate-500">{formatTime(timeSinceAlert)}</div></div>
                    </div>
                  </motion.div>
                </AnimatePresence>
                <div className="absolute inset-0 cursor-grab active:cursor-grabbing flex items-center justify-center">
                  <Globe ref={globeEl} width={700} height={700} backgroundColor="rgba(0,0,0,0)" globeImageUrl="//unpkg.com/three-globe/example/img/earth-blue-marble.jpg" bumpImageUrl="//unpkg.com/three-globe/example/img/earth-topology.png" pointsData={nodes} pointColor="color" pointAltitude="size" pointRadius={0.5} pointsMerge={true} ringsData={rings} ringColor={() => '#22d3ee'} ringMaxRadius={5} ringPropagationSpeed={2} ringRepeatPeriod={1500} arcsData={arcs} arcColor="color" arcDashLength={0.1} arcDashGap={1} arcDashAnimateTime={2000} arcAltitude={0.2} atmosphereColor="#22d3ee" atmosphereAltitude={0.15} />
                </div>
              </motion.div>
            </div>
          </section>

          <HowItWorks />
          <TechStack />
          <DemoPreview onNavigate={onNavigate} />

          <footer className="bg-[#02050a] py-8 border-t border-cyan-900/30 text-center relative z-10">
            <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between">
              <div className="flex items-center gap-2 mb-4 md:mb-0"><Shield className="w-5 h-5 text-cyan-500" /><span className="text-lg font-black tracking-widest text-white">DRISHTI</span></div>
              <div className="flex gap-6 text-xs font-mono text-cyan-500/70"><a href="#" className="hover:text-cyan-400 transition-colors">DOCUMENTATION</a><a href="#" className="hover:text-cyan-400 transition-colors">GITHUB</a><a href="#" className="hover:text-cyan-400 transition-colors">SYSTEM_STATUS</a></div>
            </div>
          </footer>
          <LiveTicker />
          <div className="h-8"></div>
        </div>
      )}
    </>
  );
}
