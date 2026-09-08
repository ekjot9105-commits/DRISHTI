import { Video, Cpu, Hexagon, Bell } from 'lucide-react';
import { motion } from 'framer-motion';

export default function HowItWorks() {
  const steps = [
    { icon: <Video className="w-6 h-6 text-cyan-400" />, title: "ORDINARY CAMERA", desc: "Connect any existing CCTV or webcam feed via RTSP/HTTP." },
    { icon: <Cpu className="w-6 h-6 text-blue-400" />, title: "AI DETECTION", desc: "Edge model analyzes frames in real-time for violence or anomalies." },
    { icon: <Hexagon className="w-6 h-6 text-purple-400" />, title: "BLOCKCHAIN LOG", desc: "Evidence is cryptographically hashed and stored immutably." },
    { icon: <Bell className="w-6 h-6 text-red-400" />, title: "INSTANT ALERT", desc: "Authorities are immediately notified with location & confidence." }
  ];

  return (
    <section className="py-24 relative z-10 px-6 bg-[#030712] border-t border-cyan-900/20">
      <div className="max-w-7xl mx-auto">
        <div className="mb-16 text-center">
          <h2 className="text-3xl lg:text-4xl font-black text-white mb-4 tracking-tight">How It Works</h2>
          <p className="text-slate-400 text-lg font-light font-mono text-sm tracking-widest uppercase">The Pipeline</p>
        </div>
        <div className="flex flex-col lg:flex-row justify-between relative gap-8 lg:gap-0">
          <div className="hidden lg:block absolute top-1/2 left-0 w-full h-[2px] bg-cyan-900/30 -translate-y-1/2 z-0">
            <div className="pipeline-flow h-full bg-gradient-to-r from-transparent via-cyan-400 to-transparent w-1/3"></div>
          </div>
          {steps.map((step, idx) => (
            <motion.div key={idx} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: idx * 0.2 }} className="relative z-10 flex flex-col items-center text-center lg:w-1/4 px-4">
              {idx !== 0 && <div className="lg:hidden w-[2px] h-8 bg-cyan-900/50 my-2"></div>}
              <div className="w-20 h-20 rounded-2xl bg-[#0a1122]/80 backdrop-blur-md border border-cyan-500/20 shadow-[0_0_20px_rgba(34,211,238,0.1)] flex items-center justify-center mb-6 relative group hover:border-cyan-400/50 transition-all">
                <div className="absolute inset-0 bg-cyan-400/5 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity"></div>
                {step.icon}
                <div className="absolute -top-3 -right-3 w-6 h-6 rounded-full bg-cyan-950 border border-cyan-500 text-cyan-400 font-mono text-[10px] flex items-center justify-center font-bold">0{idx + 1}</div>
              </div>
              <h3 className="text-base font-bold text-white mb-2 font-mono tracking-wide">{step.title}</h3>
              <p className="text-slate-400 text-xs leading-relaxed max-w-[200px]">{step.desc}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
