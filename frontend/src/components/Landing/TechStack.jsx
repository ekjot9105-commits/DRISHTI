export default function TechStack() {
  const techs = [
    { name: "YOLOv8", type: "Computer Vision" },
    { name: "ByteTrack", type: "Object Tracking" },
    { name: "FastAPI", type: "Backend Engine" },
    { name: "React", type: "Frontend UI" },
    { name: "Three.js", type: "WebGL Rendering" },
    { name: "Blockchain", type: "Evidence Ledger" }
  ];

  return (
    <section className="py-16 relative z-10 px-6 bg-[#02050a]">
      <div className="max-w-7xl mx-auto border-t border-b border-cyan-900/30 py-12">
        <div className="text-center mb-8">
          <p className="text-slate-500 font-mono text-[10px] tracking-[0.3em] uppercase">Built with bleeding-edge technology</p>
        </div>
        <div className="flex flex-wrap justify-center gap-4 sm:gap-8 lg:gap-16">
          {techs.map((tech, idx) => (
            <div key={idx} className="group flex flex-col items-center grayscale opacity-50 hover:grayscale-0 hover:opacity-100 transition-all duration-300 cursor-default">
              <div className="text-lg lg:text-2xl font-black text-transparent bg-clip-text bg-gradient-to-br from-slate-300 to-slate-600 group-hover:from-cyan-400 group-hover:to-blue-500 transition-all">{tech.name}</div>
              <div className="text-[9px] font-mono text-cyan-500/0 group-hover:text-cyan-500/80 tracking-widest mt-1 transition-all">{tech.type}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
