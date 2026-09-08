import { ChevronRight } from 'lucide-react';
import { motion } from 'framer-motion';

export default function DemoPreview({ onNavigate }) {
  return (
    <section className="py-24 relative z-10 px-6 bg-[#030712]">
      <div className="max-w-6xl mx-auto text-center">
        <h2 className="text-3xl lg:text-4xl font-black text-white mb-6 tracking-tight">See It In Action</h2>
        <p className="text-lg text-slate-400 mb-12 max-w-2xl mx-auto font-light">Enter the Command Center to experience real-time threat detection, live analytics, and encrypted evidence generation.</p>
        <motion.div initial={{ opacity: 0, y: 40 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.8 }} className="relative rounded-2xl overflow-hidden border border-cyan-900/50 shadow-[0_20px_60px_rgba(34,211,238,0.15)] group">
          <div className="bg-[#0a1122] border-b border-cyan-900/50 px-4 py-3 flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500/80"></div><div className="w-3 h-3 rounded-full bg-yellow-500/80"></div><div className="w-3 h-3 rounded-full bg-green-500/80"></div>
            <div className="mx-auto text-xs font-mono text-slate-500 tracking-widest">DRISHTI_COMMAND_CENTER</div>
          </div>
          <div className="bg-[#030712] aspect-video relative flex items-center justify-center p-8">
            <div className="absolute inset-0 bg-grid opacity-50"></div>
            <div className="w-full h-full flex gap-4 relative z-10">
              <div className="w-1/4 flex flex-col gap-4"><div className="h-1/3 bg-cyan-900/20 border border-cyan-900/40 rounded"></div><div className="h-2/3 bg-cyan-900/20 border border-cyan-900/40 rounded"></div></div>
              <div className="w-1/2 bg-cyan-900/10 border border-cyan-900/40 rounded flex items-center justify-center relative overflow-hidden"><div className="w-32 h-32 rounded-full border border-cyan-500/30 flex items-center justify-center"><div className="w-16 h-16 rounded-full border border-cyan-400/50"></div></div></div>
              <div className="w-1/4 flex flex-col gap-4"><div className="h-1/2 bg-red-900/10 border border-red-900/40 rounded"></div><div className="h-1/2 bg-cyan-900/20 border border-cyan-900/40 rounded"></div></div>
            </div>
            <div className="absolute inset-0 bg-[#030712]/60 backdrop-blur-sm flex flex-col items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-500 z-20">
              <button onClick={() => onNavigate('dashboard')} className="px-8 py-4 bg-cyan-500 text-gray-900 rounded font-mono font-bold text-sm tracking-wider hover:bg-cyan-400 shadow-[0_0_30px_rgba(34,211,238,0.4)] transition-all flex items-center gap-2 transform hover:scale-105">
                LAUNCH FULL DEMO <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
