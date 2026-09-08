/**
 * Dashboard — Main Command Center view with camera grid, stats, and alert panel.
 */
import CameraGrid from '../components/CameraGrid/CameraGrid';
import AlertPanel from '../components/AlertPanel/AlertPanel';
import SystemMonitor from '../components/SystemMonitor';
import DemoLauncher from '../components/DemoLauncher';
import ThreatMeter from '../components/ThreatMeter';
import { useLanguage } from '../context/LanguageContext';

export default function Dashboard({ cameras, alerts, humanCount, vehicleCount, onNavigate, onCamerasChange }) {
  const { t } = useLanguage();
  const activeCameras = cameras.filter((c) => c.status === 'active').length;

  return (
    <main className="p-margin-page flex-1 bg-surface relative h-full flex flex-col">
      <div className="absolute inset-0 pointer-events-none opacity-5" style={{backgroundImage: 'radial-gradient(circle at 1px 1px, white 1px, transparent 0)', backgroundSize: '20px 20px'}}></div>
      
      <div className="flex flex-col lg:flex-row gap-gutter h-full relative z-10">
        <div className="flex-1 flex flex-col gap-gutter min-w-0 overflow-y-auto custom-scrollbar pr-2 pb-4">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-unit">
            <div className="bg-surface-container-low border border-outline-variant/30 p-container-padding flex flex-col justify-between h-20 rounded-sm relative overflow-hidden group hover:border-primary/50 transition-colors">
              <span className="font-label-caps text-on-surface-variant z-10">{t('active_cameras')}</span>
              <span className="font-data-display text-headline-lg text-primary z-10">{activeCameras}</span>
              <div className="absolute bottom-0 left-0 w-full h-1 bg-primary/20">
                <div className="h-full bg-primary" style={{width: `${(activeCameras / Math.max(cameras.length, 1)) * 100}%`}}></div>
              </div>
            </div>
            
            <div className="bg-surface-container-low border border-outline-variant/30 p-container-padding flex flex-col justify-between h-20 rounded-sm relative overflow-hidden group hover:border-primary/50 transition-colors">
              <span className="font-label-caps text-on-surface-variant z-10">{t('humans_detected')}</span>
              <span className="font-data-display text-headline-lg text-secondary z-10">{humanCount}</span>
            </div>
            
            <div className="bg-surface-container-low border border-outline-variant/30 p-container-padding flex flex-col justify-between h-20 rounded-sm relative overflow-hidden group hover:border-primary/50 transition-colors">
              <span className="font-label-caps text-on-surface-variant z-10">{t('vehicles_detected')}</span>
              <span className="font-data-display text-headline-lg text-secondary z-10">{vehicleCount}</span>
            </div>
            
            <div className="bg-surface-container-low border border-outline-variant/30 p-container-padding flex flex-col justify-between h-20 rounded-sm relative overflow-hidden group hover:border-error/50 transition-colors">
              <span className="font-label-caps text-on-surface-variant z-10">{t('alerts_today')}</span>
              <div className="flex items-center space-x-2 z-10">
                <span className="font-data-display text-headline-lg text-error">{alerts.length}</span>
                <span className="material-symbols-outlined text-error text-sm animate-bounce" data-icon="trending_up" style={{fontVariationSettings: "'FILL' 1"}}>trending_up</span>
              </div>
            </div>
            
            <div className="bg-surface-container-low border border-outline-variant/30 p-container-padding flex flex-col justify-between h-20 rounded-sm relative overflow-hidden group hover:border-primary/50 transition-colors">
              <span className="font-label-caps text-on-surface-variant z-10">{t('total_cameras')}</span>
              <span className="font-data-display text-headline-lg text-on-surface">{cameras.length}</span>
            </div>
          </div>

          <ThreatMeter />

          <DemoLauncher onCamerasChange={onCamerasChange} />

          <CameraGrid cameras={cameras} />
          
          <div className="mt-2">
            <SystemMonitor />
          </div>
        </div>

        <AlertPanel alerts={alerts} />
      </div>
    </main>
  );
}
