import { Link } from "react-router-dom";
import { PageHeader } from "../components/layout/AppLayout";
import { Alert, ComplianceBadge, Loading, Panel, ScanStatusBadge } from "../components/ui";
import { BarList, Donut } from "../components/Charts";
import { IconBox, IconGauge, IconReport, IconShield } from "../components/Icons";
import { useAuth } from "../lib/auth";
import { fmtDateTime } from "../lib/format";
import { useDashboardStats, useScans } from "../lib/queries";
import { toApiError } from "../lib/api";

export function DashboardPage() {
  const { isAdmin, user } = useAuth();
  const stats = useDashboardStats();
  const recent = useScans({ page: 0, size: 8 });

  const d = stats.data;
  const rate = d && d.totalScans ? Math.round((d.compliant / d.totalScans) * 100) : 0;

  return (
    <div className="page-inner">
      <PageHeader
        title="Compliance Dashboard"
        breadcrumbs={[{ label: "Home", to: "/" }, { label: "Dashboard" }]}
        actions={
          <Link to="/scans/new" className="btn">
            + New Scan
          </Link>
        }
      />

      <p className="muted small">
        Showing {isAdmin ? "department-wide" : "your"} figures for{" "}
        <strong>{user?.username}</strong> ({isAdmin ? "Administrator" : "Inspector"}).
      </p>

      {stats.isLoading && <Loading label="Loading statistics…" />}
      {stats.isError && <Alert kind="error">{toApiError(stats.error).message}</Alert>}

      {d && (
        <>
          <div className="grid cols-4 stat-row">
            <div className="stat">
              <span className="stat-ic">
                <IconReport />
              </span>
              <div>
                <div className="value">{d.totalScans}</div>
                <div className="label">Total scans</div>
              </div>
            </div>
            <div className="stat ok">
              <span className="stat-ic">
                <IconShield />
              </span>
              <div>
                <div className="value">{d.compliant}</div>
                <div className="label">Compliant</div>
              </div>
            </div>
            <div className="stat fail">
              <span className="stat-ic">
                <IconBox />
              </span>
              <div>
                <div className="value">{d.nonCompliant}</div>
                <div className="label">Non-compliant</div>
              </div>
            </div>
            <div className="stat warn">
              <span className="stat-ic">
                <IconGauge />
              </span>
              <div>
                <div className="value">{d.partial}</div>
                <div className="label">Partial</div>
              </div>
            </div>
          </div>

          <div className="grid cols-2">
            <Panel title="Compliance breakdown">
              <Donut
                centerValue={`${rate}%`}
                centerLabel="compliant"
                segments={[
                  { label: "Compliant", value: d.compliant, color: "var(--india-green)" },
                  { label: "Partial", value: d.partial, color: "#d68a00" },
                  { label: "Non-compliant", value: d.nonCompliant, color: "#b32020" },
                ]}
              />
            </Panel>

            <Panel title="Scan volume">
              <div className="mini-metrics">
                <div>
                  <span className="mm-value">{d.scansLast7Days}</span>
                  <span className="mm-label">last 7 days</span>
                </div>
                <div>
                  <span className="mm-value">{d.scansLast30Days}</span>
                  <span className="mm-label">last 30 days</span>
                </div>
                <div>
                  <span className="mm-value">{rate}%</span>
                  <span className="mm-label">compliance rate</span>
                </div>
              </div>
              <p className="small muted" style={{ marginTop: 12, marginBottom: 0 }}>
                {d.totalScans === 0
                  ? "No scans recorded yet."
                  : `${d.compliant} of ${d.totalScans} scans met all mandatory declarations.`}
              </p>
            </Panel>
          </div>

          <Panel title="Most frequent violations">
            {d.topViolations.length === 0 ? (
              <p className="muted small">No failed rules recorded yet.</p>
            ) : (
              <BarList
                color="#b32020"
                items={d.topViolations.map((v) => ({
                  label: v.ruleCode.replace(/^RULE_/, "").replace(/_/g, " "),
                  value: v.count,
                }))}
              />
            )}
          </Panel>
        </>
      )}

      <Panel
        title="Recent scans"
        actions={
          <Link to="/scans" className="small">
            View all →
          </Link>
        }
      >
        {recent.isLoading && <Loading />}
        {recent.data && recent.data.content.length === 0 && (
          <p className="muted small">No scans yet. Submit your first one.</p>
        )}
        {recent.data && recent.data.content.length > 0 && (
          <div className="table-wrap">
            <table className="gov">
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Status</th>
                  <th>Compliance</th>
                  <th>Submitted</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {recent.data.content.map((s) => (
                  <tr key={s.id}>
                    <td>{s.productName ?? "—"}</td>
                    <td>
                      <ScanStatusBadge status={s.status} />
                    </td>
                    <td>
                      <ComplianceBadge status={s.overallStatus} />
                    </td>
                    <td>{fmtDateTime(s.createdAt)}</td>
                    <td>
                      <Link to={`/scans/${s.id}`}>Open</Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>
    </div>
  );
}
