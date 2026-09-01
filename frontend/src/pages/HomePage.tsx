import { Link } from "react-router-dom";
import { useAuth } from "../lib/auth";

export function HomePage() {
  const { isAuthenticated } = useAuth();

  return (
    <>
      <section className="hero">
        <div className="container">
          <h1>Automated verification of Legal Metrology declarations on packaged commodities</h1>
          <p>
            Upload a photograph of a pre-packaged commodity label. The system extracts the mandatory
            declarations, measures the print size, checks them against the Legal Metrology (Packaged
            Commodities) Rules, 2011, and produces an inspection-ready compliance report.
          </p>
          <div className="btn-row" style={{ marginTop: 18 }}>
            {isAuthenticated ? (
              <>
                <Link to="/scans/new" className="btn secondary">
                  Submit a new scan
                </Link>
                <Link to="/dashboard" className="btn" style={{ borderColor: "#fff" }}>
                  Open dashboard
                </Link>
              </>
            ) : (
              <>
                <Link to="/login" className="btn secondary">
                  Officer login
                </Link>
                <Link to="/register" className="btn" style={{ borderColor: "#fff" }}>
                  Register as inspector
                </Link>
              </>
            )}
          </div>
        </div>
      </section>

      <div className="page-inner">
        <div className="grid cols-3" style={{ marginBottom: 26 }}>
          <div className="feature-card">
            <h3>Declaration extraction</h3>
            <p className="small">
              Manufacturer name &amp; address, common name of commodity, net quantity, MRP, month and
              year of manufacture, consumer-care details, country of origin.
            </p>
          </div>
          <div className="feature-card">
            <h3>Print-size check</h3>
            <p className="small">
              Cap-height of the net-quantity and MRP declarations measured in millimetres and
              compared against the Rule 7 minimum height slab for the pack size.
            </p>
          </div>
          <div className="feature-card">
            <h3>Rule engine &amp; report</h3>
            <p className="small">
              Each declaration is evaluated as PASS / FAIL / WARNING against a configurable rule
              matrix. A signed-style PDF report can be downloaded for the field file.
            </p>
          </div>
        </div>

        <section className="panel">
          <header>How it works</header>
          <div className="panel-body">
            <ol className="steps">
              <li>Register the product in the Product Register (name, category, brand).</li>
              <li>Capture a clear photo of the principal display panel — barcode in frame.</li>
              <li>Submit the image against the product. Processing runs automatically.</li>
              <li>Review the extracted declarations and rule results on the scan page.</li>
              <li>Download the compliance report PDF for the inspection record.</li>
            </ol>
          </div>
        </section>

        <div className="grid cols-2">
          <section className="panel">
            <header>Mandatory declarations (Rule 6)</header>
            <div className="panel-body small">
              <ul>
                <li>Name and address of the manufacturer / packer / importer</li>
                <li>Common or generic name of the commodity</li>
                <li>Net quantity in standard units</li>
                <li>Retail sale price — “Maximum Retail Price ₹ … inclusive of all taxes”</li>
                <li>Month and year of manufacture / pre-packing / import</li>
                <li>Consumer-care contact details</li>
                <li>Country of origin (for imported packages)</li>
              </ul>
            </div>
          </section>
          <section className="panel">
            <header>Quick links</header>
            <div className="panel-body">
              <ul className="small">
                <li>
                  <Link to="/about">About this portal &amp; the rule matrix</Link>
                </li>
                <li>
                  <Link to="/about#contact">Report an issue / grievance</Link>
                </li>
                <li>
                  <a href="https://consumeraffairs.nic.in" target="_blank" rel="noreferrer">
                    Department of Consumer Affairs
                  </a>
                </li>
              </ul>
            </div>
          </section>
        </div>
      </div>
    </>
  );
}
