import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export default function BootSequence({ onComplete }) {
  const [lines, setLines] = useState([]);
  const [isComplete, setIsComplete] = useState(false);

  useEffect(() => {
    if (sessionStorage.getItem('drishti_booted')) {
      onComplete();
      return;
    }
    const bootProcess = [
      { text: "INITIALIZING DRISHTI_OS v3.4...", delay: 200 },
      { text: "MOUNTING SECURE VOLUMES... [OK]", delay: 600 },
      { text: "LOADING NEURAL NETWORK... [OK]", delay: 1000 },
      { text: "ESTABLISHING WEBSOCKET UPLINK... [OK]", delay: 1400 },
      { text: "CONNECTING TO GLOBAL GRID... [OK]", delay: 1800 },
      { text: "SYSTEM READY", delay: 2200 }
    ];

    bootProcess.forEach(({ text, delay }, index) => {
      setTimeout(() => {
        setLines(prev => [...prev, text]);
        if (index === bootProcess.length - 1) {
          setTimeout(() => {
            setIsComplete(true);
            sessionStorage.setItem('drishti_booted', 'true');
            setTimeout(onComplete, 800);
          }, 800);
        }
      }, delay);
    });
  }, [onComplete]);

  if (sessionStorage.getItem('drishti_booted') && !isComplete) return null;

  return (
    <AnimatePresence>
      {!isComplete && (
        <motion.div 
          initial={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.8, ease: "easeInOut" }}
          className="fixed inset-0 z-[100] bg-black flex flex-col justify-center px-12"
        >
          <div className="max-w-2xl font-mono text-sm sm:text-base space-y-2">
            {lines.map((line, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                className={line === "SYSTEM READY" ? "text-cyan-400 mt-4 font-bold" : "text-green-500/80"}
              >
                <span className="text-gray-600 mr-4">{`>`}</span>
                {line}
              </motion.div>
            ))}
            <motion.div 
              animate={{ opacity: [0, 1, 0] }}
              transition={{ repeat: Infinity, duration: 0.8 }}
              className="w-3 h-5 bg-green-500/80 inline-block align-middle ml-2 mt-2"
            />
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
