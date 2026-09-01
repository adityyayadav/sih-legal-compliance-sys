import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { PageHeader } from "../components/layout/AppLayout";
import {
  Alert,
  ComplianceBadge,
  Loading,
  Panel,
  RuleBadge,
  ScanStatusBadge,
} from "../components/ui";
import { fmtConfidence, fmtDateTime, titleCase } from "../lib/format";
import { toApiError } from "../lib/api";
import { downloadScanPdf, useScanDetail } from "../lib/queries";

export function ScanDetailPage() {
  const { id } = useParams<{ id: string }>();
  const detail = useScanDetail(id);

  const status = detail.data?.scan.status;
  const isProcessing = status === "PENDING" || status === "PROCESSING";

  const [dl, setDl] = useState<{ busy: boolean; error?: string }>({ busy: false });

  async function onDownload() {
    if (!id) return;
    setDl({ busy: true });
    try {
      await downloadScanPdf(id);
      setDl({ busy: false });
    } catch (err) {
      setDl({ busy: false, error: toApiError(err).message });
    }
  }

  if (detail.isLoading) {
    return (
      <div className="page-inner">
        <Loading label="Loading scan…" />
      </div>
    );
  }

  if (detail.isError) {
    const e = toApiError(detail.error);
    return (
      <div className="page-inner">
        <PageHeader title="Scan" breadcrumbs={[{ label: "Scans", to: "/scans" }, { label: "Detail" }]} />
        <Alert kind="error">
          {e.status === 403
            ? "You do not have access to this scan."
            : e.status === 404
              ? "Scan not found."
              : e.message}
        </Alert>
        <Link to="/scans">← Back to all scans</Link>
      </div>
    );
  }

  const d = detail.data!;
  const s = d.scan;

  return (
    <div className="page-inner">
      <PageHeader
        title="Compliance Report"
        breadcrumbs={[
          { label: "Home", to: "/" },
          { label: "Scans", to: "/scans" },
          { label: "Report" },
        ]}
        actions={
          s.status === "COMPLETED" && (
            <button className="btn" onClick={onDownload} disabled={dl.busy}>
              {dl.busy ? "Preparing…" : "⭳ Download PDF"}
            </button>
          )
        }
      />

      {dl.error && <Alert kind="error">{dl.error}</Alert>}

      {isProcessing && (
        <Alert kind="info">
          <span className="spinner" /> &nbsp;This scan is still being processed. The page will update
          automatically.
        </Alert>
      )}
      {s.status === "FAILED" && (
        <Alert kind="error">Processing failed: {s.errorMessage ?? "unknown error"}</Alert>
      )}

      <div className="grid cols-2">
        <Panel title="Scan details">
          <dl className="dl">
            <dt>Scan ID</dt>
            <dd>
              <code>{s.id}</code>
            </dd>
            <dt>Status</dt>
            <dd>
              <ScanStatusBadge status={s.status} />
            </dd>
            <dt>Overall compliance</dt>
            <dd>
              <ComplianceBadge status={s.overallStatus} />
            </dd>
            {s.complianceScore != null && (
              <>
                <dt>Compliance score</dt>
                <dd>{Math.round(s.complianceScore * 100)}%</dd>
              </>
            )}
            <dt>Submitted</dt>
            <dd>{fmtDateTime(s.createdAt)}</dd>
            <dt>Processed</dt>
            <dd>{fmtDateTime(s.processedAt)}</dd>
          </dl>
        </Panel>

        <Panel title="Product">
          {d.product ? (
            <dl className="dl">
              <dt>Name</dt>
              <dd>{d.product.name}</dd>
              <dt>Category</dt>
              <dd>{d.product.category.replace(/_/g, " ")}</dd>
              <dt>Brand</dt>
              <dd>{d.product.brand ?? "—"}</dd>
            </dl>
          ) : (
            <p className="muted small">No product linked.</p>
          )}
          {s.imageUrl && (
            <p style={{ marginTop: 10 }}>
              <a href={s.imageUrl} target="_blank" rel="noreferrer">
                View submitted image →
              </a>
            </p>
          )}
        </Panel>
      </div>

      <Panel title={`Declarations found (${d.declarations.length})`}>
        {d.declarations.length === 0 ? (
          <p className="muted small">No declarations extracted.</p>
        ) : (
          <div className="table-wrap">
            <table className="gov">
              <thead>
                <tr>
                  <th>Declaration</th>
                  <th>Present</th>
                  <th>Extracted value</th>
                  <th>Confidence</th>
                </tr>
              </thead>
              <tbody>
                {d.declarations.map((dec) => (
                  <tr key={dec.id}>
                    <td>{titleCase(dec.declarationType)}</td>
                    <td>
                      {dec.present ? (
                        <span className="badge ok">Yes</span>
                      ) : (
                        <span className="badge fail">No</span>
                      )}
                    </td>
                    <td>{dec.extractedValue ?? "—"}</td>
                    <td>{fmtConfidence(dec.confidenceScore)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>

      <Panel title={`Rule compliance results (${d.complianceResults.length})`}>
        {d.complianceResults.length === 0 ? (
          <p className="muted small">No compliance results.</p>
        ) : (
          <div className="table-wrap">
            <table className="gov">
              <thead>
                <tr>
                  <th>Rule code</th>
                  <th>Description</th>
                  <th>Status</th>
                  <th>Remarks</th>
                </tr>
              </thead>
              <tbody>
                {d.complianceResults.map((cr) => (
                  <tr key={cr.id}>
                    <td>
                      <code>{cr.ruleCode}</code>
                    </td>
                    <td>{cr.ruleDescription ?? "—"}</td>
                    <td>
                      <RuleBadge status={cr.status} />
                    </td>
                    <td>{cr.remarks ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>

      {s.ocrRawText && (
        <Panel title="Raw OCR text">
          <pre
            style={{
              whiteSpace: "pre-wrap",
              fontSize: "0.82rem",
              background: "#f7f8fb",
              padding: 12,
              border: "1px solid var(--border)",
              borderRadius: 3,
            }}
          >
            {s.ocrRawText}
          </pre>
        </Panel>
      )}

      <Link to="/scans">← Back to all scans</Link>
    </div>
  );
}
