/**
 * Header Bar — Top bar with page title, live stats, and system clock
 */
import { useState, useEffect } from 'react';

export default function Header({ title, activeCameras, totalAlerts, onNavigate }) {
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const formatTime = (date) => {
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    });
  };

  const displayText = `DRISHTI // ${title.toUpperCase()}`;

  return (
    <header className="bg-surface-dim dark:bg-surface-dim text-primary dark:text-primary font-headline-sm text-headline-sm font-data-display text-data-display font-bold tracking-tighter text-primary dark:text-primary docked full-width top-0 border-b border-outline-variant flat no shadows flex justify-between items-center w-full px-gutter h-16 z-50 fixed left-0 right-0 top-0 pl-[calc(5rem+16px)]">
      <div className="flex items-center space-x-4">
        <h1 className="glitch-effect text-lg tracking-widest" data-text={displayText}>{displayText}</h1>
        <div className="flex space-x-2 ml-4">
          <span className="px-2 py-0.5 rounded-sm bg-primary/10 border border-primary/30 text-primary font-label-caps text-label-caps flex items-center space-x-1">
            <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse"></span>
            <span>SYSTEM NOMINAL</span>
          </span>
        </div>
      </div>
      <div className="flex items-center space-x-2">
        <div className="text-on-surface-variant font-data-display text-[12px] mr-4 flex items-center space-x-4">
            <span className="flex items-center space-x-1">
                <span>Active Cams:</span> <span className="text-primary">{activeCameras}</span>
            </span>
            <span className="flex items-center space-x-1">
                <span>Alerts:</span> <span className={totalAlerts > 0 ? "text-error" : "text-primary"}>{totalAlerts}</span>
            </span>
            <span className="ml-2 px-2 py-1 bg-surface-container border border-outline-variant rounded">{formatTime(currentTime)}</span>
        </div>
        <button 
          onClick={() => onNavigate && onNavigate('alerts')}
          className="relative w-10 h-10 rounded-full flex items-center justify-center text-on-surface-variant hover:text-cyan-400 hover:bg-surface-container-high transition-all active:scale-95 duration-100"
        >
          <span className="material-symbols-outlined" data-icon="notifications">notifications</span>
          {totalAlerts > 0 && (
            <span className="absolute top-1 right-1 w-3.5 h-3.5 bg-red-500 rounded-full text-[9px] text-white flex items-center justify-center font-bold border border-black animate-pulse">
              {totalAlerts > 99 ? '99+' : totalAlerts}
            </span>
          )}
        </button>
        <button 
          onClick={() => onNavigate && onNavigate('settings')}
          className="w-10 h-10 rounded-full flex items-center justify-center text-on-surface-variant hover:text-cyan-400 hover:bg-surface-container-high transition-all active:scale-95 duration-100"
        >
          <span className="material-symbols-outlined" data-icon="settings">settings</span>
        </button>
        <button className="w-10 h-10 rounded-full flex items-center justify-center text-on-surface-variant hover:bg-surface-container-high transition-colors active:scale-95 duration-100">
          <span className="material-symbols-outlined" data-icon="person">person</span>
        </button>
      </div>
    </header>
  );
}
