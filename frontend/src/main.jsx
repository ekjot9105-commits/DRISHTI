import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import PhoneCam from './pages/PhoneCam.jsx'

import { LanguageProvider } from './context/LanguageContext';

/**
 * Public / operator split.
 *
 * `/phone` is the public surface: anyone who scans the QR lands there. It
 * mounts PhoneCam on its own, deliberately outside <App>, so none of the
 * operator shell exists on that page — no sidebar, no nav, no camera polling
 * and no alert WebSocket. Everything else is the operator console.
 *
 * This is a layout separation, not a security boundary; the backend API is
 * unchanged and still open on the LAN.
 */
const path = typeof window !== 'undefined' ? window.location.pathname : '/';
const isPublicCameraPage = path.startsWith('/phone');

// The 3D landing is the front door, at / and /landing. The earlier use-case
// landing is still built and still reachable at /classic. Both are
// operator-side, so they mount inside <App> and navigate with the same
// setActivePage/onNavigate flow as every other page — no router involved.
const initialPage = path.startsWith('/classic') ? 'landing' : 'landing-v2';

createRoot(document.getElementById('root')).render(
  <StrictMode>
    {isPublicCameraPage ? (
      <PhoneCam />
    ) : (
      <LanguageProvider>
        <App initialPage={initialPage} />
      </LanguageProvider>
    )}
  </StrictMode>,
)
