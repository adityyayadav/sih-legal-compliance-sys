import { Link } from "react-router-dom";

export function SiteFooter() {
  return (
    <footer className="gov-footer">
      <div className="container">
        <div className="cols">
          <div>
            <h4>The Portal</h4>
            <ul>
              <li>
                <Link to="/about">About</Link>
              </li>
              <li>
                <Link to="/dashboard">Dashboard</Link>
              </li>
              <li>
                <Link to="/scans/new">Submit a Scan</Link>
              </li>
              <li>
                <Link to="/products">Product Register</Link>
              </li>
            </ul>
          </div>
          <div>
            <h4>Legal Framework</h4>
            <ul>
              <li>The Legal Metrology Act, 2009</li>
              <li>LM (Packaged Commodities) Rules, 2011</li>
              <li>Rule 6 — Mandatory Declarations</li>
              <li>Rule 7 — Size of Declarations</li>
            </ul>
          </div>
          <div>
            <h4>Related</h4>
            <ul>
              <li>
                <a href="https://consumeraffairs.nic.in" target="_blank" rel="noreferrer">
                  Dept. of Consumer Affairs
                </a>
              </li>
              <li>
                <a href="https://sih.gov.in" target="_blank" rel="noreferrer">
                  Smart India Hackathon
                </a>
              </li>
              <li>
                <a href="https://www.india.gov.in" target="_blank" rel="noreferrer">
                  National Portal of India
                </a>
              </li>
            </ul>
          </div>
          <div>
            <h4>Help</h4>
            <ul>
              <li>
                <Link to="/about#contact">Contact / Grievance</Link>
              </li>
              <li>Accessibility Statement</li>
              <li>Terms &amp; Conditions</li>
              <li>Privacy Policy</li>
            </ul>
          </div>
        </div>
        <div className="strip">
          <span>
            Content managed by the Department of Legal Metrology · Developed as a Smart India
            Hackathon prototype
          </span>
          <span>Last updated: {new Date().toLocaleDateString("en-IN")}</span>
        </div>
      </div>
      <div className="disclaimer">
        This is a hackathon prototype for demonstration purposes only. It is not an official
        Government of India website and does not carry any regulatory authority.
      </div>
    </footer>
  );
}
