import { Link } from "react-router-dom";
import { PageHeader } from "../components/layout/AppLayout";
import { Alert, ComplianceBadge, Loading, Panel, ScanStatusBadge } from "../components/ui";
import { useAuth } from "../lib/auth";
import { fmtDateTime } from "../lib/format";
import { useDashboardStats, useScans } from "../lib/queries";
import { toApiError } from "../lib/api";

export function DashboardPage() {
  const { isAdmin, user } = useAuth();
  const stats = useDashboardStats();
  const recent = useScans({ page: 0, size: 8 });

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

      {stats.data && (
        <>
          <div className="grid cols-4" style={{ marginBottom: 6 }}>
            <div className="stat">
              <div className="value">{stats.data.totalScans}</div>
              <div className="label">Total scans</div>
            </div>
            <div className="stat ok">
              <div className="value">{stats.data.compliant}</div>
              <div className="label">Compliant</div>
            </div>
            <div className="stat fail">
              <div className="value">{stats.data.nonCompliant}</div>
              <div className="label">Non-compliant</div>
            </div>
            <div className="stat warn">
              <div className="value">{stats.data.partial}</div>
              <div className="label">Partial</div>
            </div>
          </div>

          <div className="grid cols-2">
            <Panel title="Scan volume">
              <dl className="dl">
                <dt>Last 7 days</dt>
                <dd>{stats.data.scansLast7Days}</dd>
                <dt>Last 30 days</dt>
                <dd>{stats.data.scansLast30Days}</dd>
                <dt>Compliance rate</dt>
                <dd>
                  {stats.data.totalScans
                    ? `${Math.round((stats.data.compliant / stats.data.totalScans) * 100)}%`
                    : "—"}
                </dd>
              </dl>
            </Panel>

            <Panel title="Top violations">
              {stats.data.topViolations.length === 0 ? (
                <p className="muted small">No failed rules recorded yet.</p>
              ) : (
                <table className="gov">
                  <thead>
                    <tr>
                      <th>Rule</th>
                      <th className="num">Failures</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stats.data.topViolations.map((v) => (
                      <tr key={v.ruleCode}>
                        <td>
                          <code className="small">{v.ruleCode}</code>
                        </td>
                        <td className="num">{v.count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </Panel>
          </div>
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
