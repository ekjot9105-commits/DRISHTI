/**
 * Sidebar Navigation — Command Center left panel
 */
import { useState } from 'react';

const navItems = [
  { id: 'dashboard', label: 'Command Center', icon: 'dashboard', section: 'MONITORING' },
  { id: 'cameras', label: 'Camera Management', icon: 'videocam', section: 'MONITORING' },
  { id: 'alerts', label: 'Alert Center', icon: 'notifications', section: 'MONITORING' },
  { id: 'analytics', label: 'Analytics', icon: 'monitoring', section: 'INTELLIGENCE' },
  { id: 'watchlist', label: 'Watchlist', icon: 'person', section: 'INTELLIGENCE' },
  { id: 'map', label: 'Map View', icon: 'map', section: 'INTELLIGENCE' },
  { id: 'evidence', label: 'Evidence Vault', icon: 'lock', section: 'SECURITY' },
  { id: 'settings', label: 'Settings', icon: 'settings', section: 'SYSTEM' },
];

export default function Sidebar({ activePage, onNavigate }) {
  return (
    <nav className="bg-surface-container-low dark:bg-surface-container-low text-primary dark:text-primary font-label-caps text-label-caps font-data-display text-data-display text-primary docked left-0 h-full w-20 hover:w-64 transition-all duration-300 border-r border-outline-variant flat no shadows fixed left-0 top-16 bottom-0 z-40 flex flex-col py-stack-md group overflow-hidden">
      
      {/* Brand Profile Section */}
      <div className="px-4 mb-6 whitespace-nowrap overflow-hidden flex items-center space-x-3">
        <div className="w-8 h-8 rounded bg-primary/20 flex items-center justify-center shrink-0 border border-primary/50">
          <span className="font-bold text-primary text-sm" style={{fontFamily: 'Inter'}}>IV</span>
        </div>
        <div className="flex flex-col opacity-0 group-hover:opacity-100 transition-opacity duration-300">
          <span className="font-headline-sm text-sm truncate text-on-surface tracking-widest uppercase">IBVAP</span>
          <span className="font-label-md text-primary truncate text-[9px] uppercase tracking-widest">Platform Admin</span>
        </div>
      </div>
      
      <div className="flex flex-col space-y-2 px-2 flex-grow">
        {navItems.map((item) => {
          const isActive = activePage === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`${isActive ? 'bg-primary-container text-on-primary-container' : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-container-highest'} transition-all duration-200 ease-in-out flex items-center px-3 py-3 rounded-lg w-full`}
              title={item.label}
            >
              <span className="material-symbols-outlined shrink-0" data-icon={item.icon}>{item.icon}</span>
              <span className="ml-4 whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity duration-300 tracking-wider text-xs">{item.label}</span>
            </button>
          )
        })}
      </div>
    </nav>
  );
}
