import { Link } from "react-router-dom";
import { Emblem } from "./Emblem";

export function Masthead() {
  return (
    <header className="gov-masthead">
      <div className="container">
        <Emblem />
        <div className="masthead-titles">
          <div className="ministry">
            Ministry of Consumer Affairs, Food &amp; Public Distribution
          </div>
          <Link to="/" className="dept" style={{ display: "block" }}>
            Department of Legal Metrology
          </Link>
          <div className="portal">Automated Label Compliance Verification Portal</div>
        </div>
        <div className="masthead-badges">
          <span className="badge-chip">
            SIH&nbsp;2025
            <small>Prototype</small>
          </span>
          <span className="badge-chip">
            Digital India
            <small>Initiative</small>
          </span>
          <span className="badge-chip">
            LM Act 2009
            <small>Rules 2011</small>
          </span>
        </div>
      </div>
    </header>
  );
}
