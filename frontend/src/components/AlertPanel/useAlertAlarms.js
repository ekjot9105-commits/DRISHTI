/**
 * useAlertAlarms — browser push notifications + alarm tone for incoming alerts.
 *
 * Both fire off the same `alerts` array the Incident Log renders, which is fed
 * by the existing /ws/alerts WebSocket in App.jsx. Nothing opens a second
 * socket; this hook only reacts to alerts appearing at the head of that list.
 *
 * Mute state lives in the shared backend settings store (settings.json via
 * /api/settings), not localStorage, so it is the same toggle everywhere and
 * survives a different browser or machine.
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import { fetchSettings, updateSettings } from '../../services/api';

const CRITICAL_SOUND = '/alarm-critical.wav';
const WARNING_SOUND = '/alarm-warning.wav';

const SEVERITY_RANK = { info: 0, warning: 1, high: 2, critical: 3 };
const rank = (s) => SEVERITY_RANK[String(s || 'info').toLowerCase()] ?? 0;

export default function useAlertAlarms(alerts) {
  const [permission, setPermission] = useState(
    typeof Notification === 'undefined' ? 'unsupported' : Notification.permission,
  );
  const [muted, setMuted] = useState(false);
  const [settingsLoaded, setSettingsLoaded] = useState(false);

  // Ids already announced, so a re-render never re-fires an alert.
  const seenIds = useRef(new Set());
  const primed = useRef(false);
  const lastPlayed = useRef(0);
  const cooldownRef = useRef(3.0);
  const pushEnabled = useRef(true);
  const audioRef = useRef({ critical: null, warning: null });
  const liveNotifications = useRef([]);

  // ---- preload the two tones once -----------------------------------------
  useEffect(() => {
    const make = (src) => {
      const a = new Audio(src);
      a.preload = 'auto';
      return a;
    };
    audioRef.current = { critical: make(CRITICAL_SOUND), warning: make(WARNING_SOUND) };
    return () => {
      Object.values(audioRef.current).forEach((a) => a && a.pause());
      liveNotifications.current.forEach((n) => n.close());
      liveNotifications.current = [];
    };
  }, []);

  // ---- mute + cooldown come from the shared settings store -----------------
  useEffect(() => {
    let cancelled = false;
    fetchSettings()
      .then((s) => {
        if (cancelled) return;
        setMuted(Boolean(s.alarm_muted));
        cooldownRef.current = Number(s.alarm_cooldown ?? 3.0);
        pushEnabled.current = s.browser_push_enabled !== false;
      })
      .catch(() => {
        /* Backend unreachable — fall back to audible, the safer default. */
      })
      .finally(() => !cancelled && setSettingsLoaded(true));
    return () => {
      cancelled = true;
    };
  }, []);

  const toggleMute = useCallback(async () => {
    const next = !muted;
    setMuted(next); // optimistic; the panel stays responsive
    try {
      await updateSettings({ alarm_muted: next });
    } catch (e) {
      setMuted(!next); // roll back if the store rejected it
      console.warn('Could not persist mute setting:', e.message);
    }
  }, [muted]);

  /**
   * Ask for notification permission. Must be called from a real user gesture —
   * browsers ignore (and Chrome permanently denies) requests made on page load.
   */
  const requestPermission = useCallback(async () => {
    if (typeof Notification === 'undefined') return 'unsupported';
    const result = await Notification.requestPermission();
    setPermission(result);
    return result;
  }, []);

  const playAlarm = useCallback((severity) => {
    if (muted) return;
    const now = Date.now() / 1000;
    // Anti-spam: one tone per cooldown window, however many alerts land.
    if (now - lastPlayed.current < cooldownRef.current) return;

    const el = rank(severity) >= SEVERITY_RANK.critical
      ? audioRef.current.critical
      : audioRef.current.warning;
    if (!el) return;

    lastPlayed.current = now;
    // Rewind rather than spawning a second element, so tones never overlap.
    try {
      el.pause();
      el.currentTime = 0;
      const p = el.play();
      if (p && p.catch) {
        p.catch(() => {
          // Autoplay blocked until the user interacts with the page — expected
          // before the first gesture, and not worth surfacing.
        });
      }
    } catch {
      /* element not ready yet */
    }
  }, [muted]);

  const showNotification = useCallback((alert) => {
    if (!pushEnabled.current) return;
    if (typeof Notification === 'undefined' || Notification.permission !== 'granted') return;
    if (typeof document !== 'undefined' && document.visibilityState === 'visible') return;

    const camera = alert.camera_name || `Camera ${alert.camera_id}`;
    const severity = String(alert.severity || 'info').toUpperCase();
    try {
      const n = new Notification(`${alert.icon || '🚨'} ${alert.title}`, {
        body: `${alert.type?.toUpperCase() || 'EVENT'} · ${camera} · ${severity}\n${alert.detail || ''}`,
        icon: '/drishti_logo.jpg',
        badge: '/favicon.svg',
        tag: alert.id,                                  // collapses duplicates
        requireInteraction: rank(alert.severity) >= SEVERITY_RANK.critical,
      });
      n.onclick = () => {
        window.focus();                                 // bring the console forward
        n.close();
      };
      liveNotifications.current.push(n);
      if (liveNotifications.current.length > 12) liveNotifications.current.shift().close();
    } catch (e) {
      console.warn('Notification failed:', e.message);
    }
  }, []);

  // ---- react to new alerts on the existing WS feed -------------------------
  useEffect(() => {
    if (!settingsLoaded || !alerts.length) return;

    // First pass after mount: adopt the backlog silently rather than firing a
    // burst of notifications for alerts that happened before the panel opened.
    if (!primed.current) {
      alerts.forEach((a) => seenIds.current.add(a.id));
      primed.current = true;
      return;
    }

    const fresh = alerts.filter((a) => a && a.id && !seenIds.current.has(a.id));
    if (!fresh.length) return;
    fresh.forEach((a) => seenIds.current.add(a.id));

    // Keep the id set bounded on a long-running console.
    if (seenIds.current.size > 500) {
      seenIds.current = new Set(alerts.map((a) => a.id));
    }

    fresh.forEach(showNotification);

    // One tone for the whole batch, at the highest severity present.
    const loudest = fresh.reduce(
      (worst, a) => (rank(a.severity) > rank(worst) ? a.severity : worst),
      'info',
    );
    if (rank(loudest) >= SEVERITY_RANK.warning) playAlarm(loudest);
  }, [alerts, settingsLoaded, showNotification, playAlarm]);

  return { permission, requestPermission, muted, toggleMute };
}
