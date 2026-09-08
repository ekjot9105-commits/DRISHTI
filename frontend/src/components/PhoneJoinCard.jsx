/**
 * PhoneJoinCard — shows the LAN QR code that opens the /phone page, so anyone
 * on the same network can scan it and turn their handset into a live feed.
 */
import { useEffect, useState } from 'react';
import { fetchLanUrl, qrImageUrl } from '../services/api';

export default function PhoneJoinCard() {
  const [url, setUrl] = useState('');
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    fetchLanUrl('/phone', window.location.port || 5173)
      .then((d) => setUrl(d.url))
      .catch((e) => setError(e.message));
  }, []);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      setError('Clipboard blocked — copy the link manually.');
    }
  };

  return (
    <div className="bg-surface-container-low border border-outline-variant/30 p-container-padding rounded-sm">
      <div className="font-label-caps text-on-surface-variant mb-2">JOIN AS PHONE CAMERA</div>

      {error && <div className="text-xs text-error mb-2">{error}</div>}

      {url ? (
        <div className="flex items-center gap-4">
          <img
            src={qrImageUrl(url)}
            alt="QR code linking to the phone camera page"
            className="w-32 h-32 bg-white p-1 rounded-sm"
            onError={() => setError('QR service unavailable — run: pip install "qrcode[pil]"')}
          />
          <div className="min-w-0">
            <p className="text-xs text-on-surface-variant mb-2">
              Scan with a phone on the same network. The handset streams straight
              into the detection pipeline.
            </p>
            <code className="block text-xs text-primary break-all mb-2">{url}</code>
            <button
              onClick={copy}
              className="px-3 py-1 text-xs font-semibold border border-outline-variant/40 rounded-sm hover:border-primary/50"
            >
              {copied ? 'COPIED' : 'COPY LINK'}
            </button>
          </div>
        </div>
      ) : (
        !error && <div className="text-xs text-on-surface-variant">Resolving LAN address…</div>
      )}
    </div>
  );
}
