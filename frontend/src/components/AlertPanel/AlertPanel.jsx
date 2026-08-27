/**
 * AlertPanel — Live alerts sidebar showing real-time detection notifications.
 */
import { useState } from 'react';

export default function AlertPanel({ alerts = [] }) {
  const displayAlerts = alerts;

  return (
    <div className="w-full lg:w-80 flex flex-col bg-surface-container-low border border-outline-variant/50 rounded-sm h-full max-h-full">
      <div className="p-3 border-b border-outline-variant/30 bg-surface/50 flex justify-between items-center">
        <h2 className="font-label-caps text-on-surface tracking-widest">INCIDENT LOG</h2>
        <span className="font-data-display text-[10px] text-on-surface-variant bg-surface-container-high px-1.5 py-0.5 rounded-sm border border-outline-variant">LIVE FEED</span>
      </div>
      
      <div className="flex-1 overflow-y-auto p-2 space-y-2 custom-scrollbar">
        {displayAlerts.map((alert, idx) => {
          const isHigh = alert.severity === 'high' || alert.severity === 'danger' || idx === 0;
          return (
            <div key={alert.id} className={`bg-surface-container border-l-2 ${isHigh ? 'border-secondary' : 'border-outline opacity-70'} p-3 rounded-r-sm hover:bg-surface-container-high transition-colors cursor-pointer group relative overflow-hidden`}>
              {isHigh && <div className="absolute inset-0 bg-secondary/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>}
              
              <div className="flex justify-between items-start mb-1 relative z-10">
                <span className={`font-label-caps ${isHigh ? 'text-secondary' : 'text-outline'} text-[10px] flex items-center`}>
                  {isHigh && <span className="w-1.5 h-1.5 rounded-full bg-secondary mr-1 animate-pulse"></span>}
                  {alert.level || (isHigh ? 'PRIORITY ALPHA' : 'ROUTINE')}
                </span>
                <span className="font-data-display text-[9px] text-on-surface-variant">{alert.time}</span>
              </div>
              
              <h3 className="font-body-md text-on-surface font-semibold text-sm leading-tight mb-1 relative z-10">{alert.title}</h3>
              <p className="font-body-md text-[11px] text-on-surface-variant leading-tight relative z-10">{alert.detail}</p>
              
              {isHigh && (
                <div className="mt-2 flex space-x-2 relative z-10">
                  <button className="font-label-caps text-[9px] text-primary border border-primary/30 px-2 py-0.5 rounded-sm hover:bg-primary/10 transition-colors">VIEW CAM</button>
                  <button className="font-label-caps text-[9px] text-on-surface-variant border border-outline-variant/50 px-2 py-0.5 rounded-sm hover:bg-surface-variant transition-colors">DISMISS</button>
                </div>
              )}
            </div>
          );
        })}

        {displayAlerts.length === 0 && (
          <div className="flex flex-col items-center justify-center p-8 opacity-50">
            <span className="material-symbols-outlined text-3xl mb-2" style={{fontVariationSettings: "'FILL' 1"}}>check_circle</span>
            <span className="font-label-caps text-on-surface-variant">No active incidents</span>
          </div>
        )}
      </div>
    </div>
  );
}
