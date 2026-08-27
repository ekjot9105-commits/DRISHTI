/**
 * PlaceholderPage — Temporary placeholder for pages not yet built.
 * Shows a coming-soon message with the page name.
 */
export default function PlaceholderPage({ title, description, icon }) {
  return (
    <div className="page-content">
      <div className="empty-state" style={{ height: '60vh' }}>
        <div className="empty-state-icon">{icon || '🚧'}</div>
        <div className="empty-state-text">{title}</div>
        <p className="empty-state-sub">{description || 'This feature will be available in a future phase.'}</p>
        <div
          style={{
            marginTop: '24px',
            padding: '12px 20px',
            background: 'var(--bg-card)',
            border: '1px solid var(--border-primary)',
            borderRadius: '8px',
            fontSize: '12px',
            color: 'var(--text-muted)',
          }}
        >
          📋 Check the Implementation Plan for timeline details
        </div>
      </div>
    </div>
  );
}
