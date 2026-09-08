/**
 * ThreatMeter — animated dial for the rolling 0-100 threat score.
 *
 * Plain inline SVG and a requestAnimationFrame tween; no charting library.
 * Polls /api/threat, which decays on its own, so the needle drifts back toward
 * green when nothing is happening.
 */
import { useEffect, useRef, useState } from 'react';
import { fetchThreat } from '../services/api';

const POLL_MS = 2000;
const SWEEP = 180;          // degrees across the dial
const CX = 100, CY = 104, R = 74, STROKE = 13;

// Fallback bands; the backend sends its own so the two never drift apart.
const FALLBACK_BANDS = [
  { from: 0, label: 'NOMINAL', color: '#16a34a' },
  { from: 25, label: 'ELEVATED', color: '#ca8a04' },
  { from: 50, label: 'HIGH', color: '#ea580c' },
  { from: 75, label: 'CRITICAL', color: '#dc2626' },
];

const scoreToDeg = (score) => 180 - (Math.max(0, Math.min(100, score)) / 100) * SWEEP;

function polar(cx, cy, r, deg) {
  const a = (deg * Math.PI) / 180;
  return { x: cx + r * Math.cos(a), y: cy - r * Math.sin(a) };
}

function arcPath(cx, cy, r, fromScore, toScore) {
  const s = polar(cx, cy, r, scoreToDeg(fromScore));
  const e = polar(cx, cy, r, scoreToDeg(toScore));
  return `M ${s.x.toFixed(2)} ${s.y.toFixed(2)} A ${r} ${r} 0 0 1 ${e.x.toFixed(2)} ${e.y.toFixed(2)}`;
}

export default function ThreatMeter() {
  const [state, setState] = useState(null);
  const [error, setError] = useState(false);
  const [display, setDisplay] = useState(0);   // tweened score for the needle
  const displayRef = useRef(0);

  // ---- poll the backend ---------------------------------------------------
  useEffect(() => {
    let alive = true;
    const tick = async () => {
      try {
        const data = await fetchThreat();
        if (!alive) return;
        setState(data);
        setError(false);
      } catch {
        if (alive) setError(true);
      }
    };
    tick();
    const id = setInterval(tick, POLL_MS);
    return () => { alive = false; clearInterval(id); };
  }, []);

  // ---- ease the needle toward the new score -------------------------------
  const target = state?.score ?? 0;
  useEffect(() => {
    const from = displayRef.current;
    const delta = target - from;
    if (Math.abs(delta) < 0.05) return;
    const t0 = performance.now();
    const DURATION = 700;
    let raf;
    const step = (now) => {
      const k = Math.min(1, (now - t0) / DURATION);
      const eased = 1 - Math.pow(1 - k, 3);       // ease-out cubic
      const value = from + delta * eased;
      displayRef.current = value;
      setDisplay(value);
      if (k < 1) raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [target]);

  const bands = state?.bands?.length ? state.bands : FALLBACK_BANDS;
  const color = state?.color || '#16a34a';
  const level = state?.level || 'NOMINAL';
  const trend = state?.trend ?? 0;
  const needle = polar(CX, CY, R - 18, scoreToDeg(display));
  const trendIcon = trend > 0.5 ? 'trending_up' : trend < -0.5 ? 'trending_down' : 'trending_flat';
  const trendColor = trend > 0.5 ? 'text-error' : trend < -0.5 ? 'text-primary' : 'text-on-surface-variant';

  return (
    <div className="bg-surface-container-low border border-outline-variant/30 p-container-padding rounded-sm">
      <div className="flex items-center justify-between mb-1">
        <span className="font-label-caps text-on-surface-variant">THREAT LEVEL</span>
        {error ? (
          <span className="font-data-display text-[9px] text-error">OFFLINE</span>
        ) : (
          <span className="font-data-display text-[9px] text-on-surface-variant">
            {state?.active_events ?? 0} ACTIVE
          </span>
        )}
      </div>

      <div className="flex items-center gap-4">
        <svg viewBox="0 0 200 120" className="w-44 shrink-0" role="img"
             aria-label={`Threat level ${level}, score ${Math.round(display)} of 100`}>
          {/* unlit track */}
          <path d={arcPath(CX, CY, R, 0, 100)} fill="none" stroke="currentColor"
                className="text-outline-variant/25" strokeWidth={STROKE} strokeLinecap="round" />

          {/* colour bands, dimmed until the needle reaches them */}
          {bands.map((band, i) => {
            const to = bands[i + 1] ? bands[i + 1].from : 100;
            return (
              <path key={band.label} d={arcPath(CX, CY, R, band.from, to)} fill="none"
                    stroke={band.color} strokeWidth={STROKE} strokeLinecap="butt"
                    opacity={display >= band.from ? 0.95 : 0.22}
                    style={{ transition: 'opacity 300ms ease' }} />
            );
          })}

          {/* scale ticks at each band edge */}
          {bands.map((band) => {
            const a = polar(CX, CY, R - STROKE / 2 - 3, scoreToDeg(band.from));
            const b = polar(CX, CY, R - STROKE / 2 - 9, scoreToDeg(band.from));
            return band.from === 0 ? null : (
              <line key={`t-${band.label}`} x1={a.x} y1={a.y} x2={b.x} y2={b.y}
                    stroke="currentColor" className="text-on-surface-variant/50" strokeWidth="1" />
            );
          })}

          {/* needle */}
          <line x1={CX} y1={CY} x2={needle.x} y2={needle.y} stroke={color}
                strokeWidth="3" strokeLinecap="round" />
          <circle cx={CX} cy={CY} r="6" fill={color} />
          <circle cx={CX} cy={CY} r="2.5" className="fill-surface" />

          <text x={CX} y={CY - 26} textAnchor="middle" fill={color}
                style={{ fontSize: 34, fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>
            {Math.round(display)}
          </text>
          <text x={CX} y={CY - 10} textAnchor="middle" fill="currentColor"
                className="text-on-surface-variant" style={{ fontSize: 9, letterSpacing: 1.5 }}>
            / 100
          </text>
        </svg>

        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="font-data-display text-lg font-bold" style={{ color }}>{level}</span>
            <span className={`material-symbols-outlined text-[16px] ${trendColor}`}>{trendIcon}</span>
            <span className={`font-data-display text-[10px] ${trendColor}`}
                  title="Change compared with 30 seconds ago">
              {trend > 0 ? '+' : ''}{trend.toFixed(1)} <span className="opacity-60">/30s</span>
            </span>
          </div>

          {state?.contributors?.length ? (
            <ul className="mt-2 space-y-1">
              {state.contributors.slice(0, 3).map((c) => (
                <li key={c.id || `${c.type}-${c.age_seconds}`}
                    className="flex items-center justify-between gap-2 text-[11px]">
                  <span className="truncate text-on-surface">
                    {c.icon} {c.title || c.type}
                    <span className="text-on-surface-variant"> · {c.camera_name || `Cam ${c.camera_id}`}</span>
                  </span>
                  <span className="font-data-display text-on-surface-variant shrink-0">
                    +{c.contribution}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-2 text-[11px] text-on-surface-variant">
              No active threats. Score decays with a {Math.round((state?.half_life ?? 120) / 60)} min half-life.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
