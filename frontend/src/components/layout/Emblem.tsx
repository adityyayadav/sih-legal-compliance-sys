/** Ashoka Chakra — 24-spoke wheel from the national flag. Used as a neutral
 *  Government-of-India mark (not the State Emblem). */
export function Emblem({ size = 54, color = "#0b3d91" }: { size?: number; color?: string }) {
  const spokes = Array.from({ length: 24 }, (_, i) => i * 15);
  return (
    <svg
      className="emblem"
      width={size}
      height={size}
      viewBox="0 0 100 100"
      role="img"
      aria-label="Government of India"
    >
      <circle cx="50" cy="50" r="46" fill="none" stroke={color} strokeWidth="4" />
      <circle cx="50" cy="50" r="7" fill={color} />
      {spokes.map((deg) => (
        <line
          key={deg}
          x1="50"
          y1="50"
          x2="50"
          y2="6"
          stroke={color}
          strokeWidth="2.4"
          transform={`rotate(${deg} 50 50)`}
        />
      ))}
    </svg>
  );
}
