import { Link } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { Carousel, type Slide } from "../components/Carousel";
import { Ticker } from "../components/Ticker";
import {
  IconBox,
  IconGauge,
  IconHelp,
  IconReport,
  IconRules,
  IconScan,
  IconShield,
  IconUpload,
} from "../components/Icons";

const SLIDES: Slide[] = [
  {
    image: "/images/slides/slide-1-inspection.svg",
    kicker: "Automated Label Compliance",
    title: "Verify packaged-commodity labels in seconds, not minutes",
    text: "Upload a photo of the principal display panel. The system extracts every mandatory declaration and checks it against the Legal Metrology (Packaged Commodities) Rules, 2011.",
    cta: { label: "Submit a scan", to: "/scans/new" },
  },
  {
    image: "/images/slides/slide-2-metrology.svg",
    kicker: "Legal Metrology Act, 2009",
    title: "Consistent, evidence-backed enforcement decisions",
    text: "Every declaration is graded PASS, FAIL or WARNING against a transparent rule matrix, with the extracted value and confidence recorded for the field file.",
    cta: { label: "View the rule matrix", to: "/about#rules" },
  },
  {
    image: "/images/slides/slide-3-digital.svg",
    kicker: "Digital India Initiative",
    title: "A live picture of compliance across your jurisdiction",
    text: "Track scan volume, compliant vs. non-compliant ratios and the most frequent violations from a single dashboard.",
    cta: { label: "Open dashboard", to: "/dashboard" },
  },
];

const NOTICES = [
  "Barcode-based print-size calibration is now supported for net-quantity and MRP declarations.",
  "Rule matrix updated in line with the Legal Metrology (Packaged Commodities) Amendment Rules.",
  "Inspectors can now filter their scan history by status, product and date range.",
  "Compliance reports can be downloaded as a signed-style PDF for the inspection record.",
];

const TILES = [
  { icon: <IconUpload />, label: "Submit a Scan", to: "/scans/new" },
  { icon: <IconGauge />, label: "Compliance Dashboard", to: "/dashboard" },
  { icon: <IconBox />, label: "Product Register", to: "/products" },
  { icon: <IconReport />, label: "Scan Reports", to: "/scans" },
  { icon: <IconRules />, label: "Rule Matrix", to: "/about#rules" },
  { icon: <IconHelp />, label: "Help & Contact", to: "/about#contact" },
];

export function HomePage() {
  const { isAuthenticated } = useAuth();

  return (
    <>
      <Carousel slides={SLIDES} />
      <Ticker items={NOTICES} />

      {/* stats band */}
      <div className="stats-band">
        <div className="container">
          <div className="sb-item">
            <span className="sb-value">9</span>
            <span className="sb-label">Mandatory declarations checked</span>
          </div>
          <div className="sb-item">
            <span className="sb-value">Rule 6 &amp; 7</span>
            <span className="sb-label">LM (Packaged Commodities) Rules, 2011</span>
          </div>
          <div className="sb-item">
            <span className="sb-value">&lt; 5 s</span>
            <span className="sb-label">Target turnaround per label</span>
          </div>
          <div className="sb-item">
            <span className="sb-value">PDF</span>
            <span className="sb-label">Inspection-ready compliance report</span>
          </div>
        </div>
      </div>

      <div className="page-inner">
        {/* quick access */}
        <section className="panel">
          <header>Quick access</header>
          <div className="panel-body">
            <div className="tile-grid">
              {TILES.map((t) => (
                <Link key={t.to} to={t.to} className="tile">
                  <span className="tile-icon">{t.icon}</span>
                  <span className="tile-label">{t.label}</span>
                </Link>
              ))}
            </div>
          </div>
        </section>

        {/* features */}
        <div className="grid cols-3" style={{ marginBottom: 22 }}>
          <div className="feature-card">
            <span className="feature-ic">
              <IconScan />
            </span>
            <h3>Declaration extraction</h3>
            <p className="small">
              Manufacturer name &amp; address, common name of commodity, net quantity, MRP, month and
              year of manufacture, consumer-care details and country of origin.
            </p>
          </div>
          <div className="feature-card">
            <span className="feature-ic">
              <IconGauge />
            </span>
            <h3>Print-size check</h3>
            <p className="small">
              Cap-height of the net-quantity and MRP declarations is measured in millimetres and
              compared against the Rule 7 minimum-height slab for the pack size.
            </p>
          </div>
          <div className="feature-card">
            <span className="feature-ic">
              <IconShield />
            </span>
            <h3>Rule engine &amp; report</h3>
            <p className="small">
              A configurable rule matrix grades each check, and a compliance report can be downloaded
              for the field file with the extracted evidence.
            </p>
          </div>
        </div>

        {/* how it works + authority */}
        <div className="grid cols-2">
          <section className="panel">
            <header>How it works</header>
            <div className="panel-body">
              <ol className="steps">
                <li>Register the product (name, category, brand) in the Product Register.</li>
                <li>Capture a clear photo of the principal display panel — barcode in frame.</li>
                <li>Submit the image against the product. Processing runs automatically.</li>
                <li>Review the extracted declarations and rule results on the scan report.</li>
                <li>Download the compliance report PDF for the inspection record.</li>
              </ol>
            </div>
          </section>

          <section className="panel">
            <header>About this initiative</header>
            <div className="panel-body">
              <p className="small">
                This portal is a decision-support tool for enforcement officers of the Department of
                Legal Metrology under the Ministry of Consumer Affairs, Food &amp; Public
                Distribution. It reduces the manual effort of checking pre-packaged commodity labels
                against the mandatory declarations of the Legal Metrology (Packaged Commodities)
                Rules, 2011.
              </p>
              <p className="small">
                {isAuthenticated ? (
                  <Link to="/dashboard">Go to your dashboard →</Link>
                ) : (
                  <Link to="/login">Officer login →</Link>
                )}{" "}
                &nbsp;·&nbsp; <Link to="/about">Read more about the rule matrix →</Link>
              </p>
              <p className="small muted">
                Prototype developed for the Smart India Hackathon. Not an official Government of India
                portal.
              </p>
            </div>
          </section>
        </div>
      </div>
    </>
  );
}
