/** Tiny dependency-free charts (SVG / CSS). */

export interface Segment {
  label: string;
  value: number;
  color: string;
}

export function Donut({
  segments,
  size = 160,
  thickness = 26,
  centerLabel,
  centerValue,
}: {
  segments: Segment[];
  size?: number;
  thickness?: number;
  centerLabel?: string;
  centerValue?: string | number;
}) {
  const total = segments.reduce((s, x) => s + x.value, 0);
  const r = (size - thickness) / 2;
  const c = 2 * Math.PI * r;
  let offset = 0;

  return (
    <div className="donut-wrap">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} role="img">
        <g transform={`translate(${size / 2} ${size / 2}) rotate(-90)`}>
          <circle r={r} fill="none" stroke="var(--bg-alt)" strokeWidth={thickness} />
          {total > 0 &&
            segments.map((seg, i) => {
              const len = (seg.value / total) * c;
              const el = (
                <circle
                  key={i}
                  r={r}
                  fill="none"
                  stroke={seg.color}
                  strokeWidth={thickness}
                  strokeDasharray={`${len} ${c - len}`}
                  strokeDashoffset={-offset}
                />
              );
              offset += len;
              return el;
            })}
        </g>
        <text x="50%" y="47%" textAnchor="middle" className="donut-value">
          {centerValue ?? total}
        </text>
        {centerLabel && (
          <text x="50%" y="60%" textAnchor="middle" className="donut-label">
            {centerLabel}
          </text>
        )}
      </svg>
      <ul className="donut-legend">
        {segments.map((s, i) => (
          <li key={i}>
            <span className="swatch" style={{ background: s.color }} />
            {s.label}
            <strong>{s.value}</strong>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function BarList({
  items,
  color = "var(--navy)",
}: {
  items: { label: string; value: number }[];
  color?: string;
}) {
  const max = Math.max(1, ...items.map((i) => i.value));
  return (
    <div className="barlist">
      {items.map((it, i) => (
        <div className="barlist-row" key={i}>
          <span className="barlist-label" title={it.label}>
            {it.label}
          </span>
          <span className="barlist-track">
            <span
              className="barlist-fill"
              style={{ width: `${(it.value / max) * 100}%`, background: color }}
            />
          </span>
          <span className="barlist-value">{it.value}</span>
        </div>
      ))}
    </div>
  );
}

/** A semicircular compliance meter (0–100). */
export function Meter({ value, label }: { value: number; label?: string }) {
  const pct = Math.max(0, Math.min(100, value));
  const color = pct >= 80 ? "var(--india-green)" : pct >= 50 ? "#d68a00" : "#b32020";
  const r = 60;
  const c = Math.PI * r;
  return (
    <div className="meter">
      <svg width="150" height="90" viewBox="0 0 150 90" role="img" aria-label={`${pct}%`}>
        <path
          d={`M 15 80 A ${r} ${r} 0 0 1 135 80`}
          fill="none"
          stroke="var(--bg-alt)"
          strokeWidth="14"
          strokeLinecap="round"
        />
        <path
          d={`M 15 80 A ${r} ${r} 0 0 1 135 80`}
          fill="none"
          stroke={color}
          strokeWidth="14"
          strokeLinecap="round"
          strokeDasharray={`${(pct / 100) * c} ${c}`}
        />
        <text x="75" y="72" textAnchor="middle" className="meter-value">
          {Math.round(pct)}%
        </text>
      </svg>
      {label && <div className="meter-label">{label}</div>}
    </div>
  );
}
