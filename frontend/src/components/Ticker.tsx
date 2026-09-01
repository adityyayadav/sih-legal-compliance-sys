export function Ticker({ items }: { items: string[] }) {
  const loop = [...items, ...items];
  return (
    <div className="ticker" role="region" aria-label="Announcements">
      <span className="ticker-label">Latest</span>
      <div className="ticker-viewport">
        <div className="ticker-track">
          {loop.map((t, i) => (
            <span className="ticker-item" key={i}>
              <span className="ticker-dot" aria-hidden="true">
                ●
              </span>
              {t}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
