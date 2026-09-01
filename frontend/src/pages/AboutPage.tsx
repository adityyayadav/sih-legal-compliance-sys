import { PageHeader } from "../components/layout/AppLayout";
import { Panel } from "../components/ui";

const RULES = [
  ["RULE_6_1_A_MANUFACTURER_NAME", "Name & address of manufacturer / packer / importer", "FAIL"],
  ["RULE_6_1_B_COMMODITY_NAME", "Common or generic name of the commodity", "FAIL"],
  ["RULE_6_7_NET_QUANTITY", "Net quantity in standard units + print-size slab", "FAIL"],
  ["RULE_6_1_E_MRP", "Maximum Retail Price, inclusive of all taxes", "FAIL"],
  ["RULE_6_1_D_MFG_DATE", "Month and year of manufacture (MM/YYYY)", "FAIL"],
  ["RULE_6_1_F_CONSUMER_CARE", "Consumer-care / complaint contact details", "FAIL"],
  ["RULE_6_1_C_COUNTRY_OF_ORIGIN", "Country of origin (imported packages)", "WARNING"],
  ["RULE_18_DIMENSIONS", "Number / dimensions (category dependent)", "WARNING"],
  ["RULE_6_UNIT_SALE_PRICE", "Unit sale price (multi-piece packages)", "WARNING"],
];

export function AboutPage() {
  return (
    <div className="page-inner">
      <PageHeader
        title="About this portal"
        breadcrumbs={[{ label: "Home", to: "/" }, { label: "About" }]}
      />

      <Panel title="Purpose">
        <p>
          The Legal Metrology Compliance Portal is a prototype decision-support tool for enforcement
          officers under the Department of Legal Metrology. It reduces the manual effort of checking
          pre-packaged commodity labels for the mandatory declarations required by the Legal
          Metrology (Packaged Commodities) Rules, 2011.
        </p>
        <p className="small muted">
          Image analysis and optical character recognition are performed by a separate model service.
          All persistence, authentication and reporting is handled by this application.
        </p>
      </Panel>

      <Panel title="Rule matrix">
        <div className="table-wrap">
          <table className="gov">
            <thead>
              <tr>
                <th>Rule code</th>
                <th>Check</th>
                <th>Severity</th>
              </tr>
            </thead>
            <tbody>
              {RULES.map(([code, desc, sev]) => (
                <tr key={code}>
                  <td>
                    <code>{code}</code>
                  </td>
                  <td>{desc}</td>
                  <td>
                    <span className={`badge ${sev === "FAIL" ? "fail" : "warn"}`}>{sev}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>

      <Panel title="Contact / grievance">
        <div id="contact" />
        <p className="small">
          For issues with this prototype during the Smart India Hackathon evaluation, contact the
          project team. This portal does not process statutory grievances — those must be filed
          through the Department of Consumer Affairs grievance portal.
        </p>
      </Panel>
    </div>
  );
}
