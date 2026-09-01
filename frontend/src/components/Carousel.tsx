import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";

export interface Slide {
  image: string;
  kicker: string;
  title: string;
  text: string;
  cta: { label: string; to: string };
}

export function Carousel({ slides, interval = 6000 }: { slides: Slide[]; interval?: number }) {
  const [i, setI] = useState(0);
  const [paused, setPaused] = useState(false);
  const timer = useRef<number>();

  useEffect(() => {
    if (paused || slides.length < 2) return;
    timer.current = window.setTimeout(() => setI((n) => (n + 1) % slides.length), interval);
    return () => window.clearTimeout(timer.current);
  }, [i, paused, slides.length, interval]);

  const s = slides[i];

  return (
    <section
      className="carousel"
      aria-roledescription="carousel"
      aria-label="Portal highlights"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
    >
      {slides.map((sl, n) => (
        <img
          key={n}
          src={sl.image}
          alt=""
          aria-hidden="true"
          className={`carousel-bg${n === i ? " active" : ""}`}
        />
      ))}

      <div className="carousel-inner container">
        <div className="carousel-copy" key={i}>
          <span className="kicker">{s.kicker}</span>
          <h1>{s.title}</h1>
          <p>{s.text}</p>
          <Link to={s.cta.to} className="btn secondary">
            {s.cta.label}
          </Link>
        </div>
      </div>

      <button
        className="carousel-arrow prev"
        aria-label="Previous slide"
        onClick={() => setI((n) => (n - 1 + slides.length) % slides.length)}
      >
        ‹
      </button>
      <button
        className="carousel-arrow next"
        aria-label="Next slide"
        onClick={() => setI((n) => (n + 1) % slides.length)}
      >
        ›
      </button>

      <div className="carousel-dots" role="tablist">
        {slides.map((_, n) => (
          <button
            key={n}
            role="tab"
            aria-selected={n === i}
            aria-label={`Slide ${n + 1}`}
            className={n === i ? "active" : ""}
            onClick={() => setI(n)}
          />
        ))}
      </div>
    </section>
  );
}
