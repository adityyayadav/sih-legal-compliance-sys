import { useState } from "react";
import { Link } from "react-router-dom";
import { PageHeader } from "../components/layout/AppLayout";
import {
  Alert,
  ComplianceBadge,
  Loading,
  Pagination,
  Panel,
  ScanStatusBadge,
} from "../components/ui";
import { fmtDateTime } from "../lib/format";
import { toApiError } from "../lib/api";
import { useProducts, useScans } from "../lib/queries";

const STATUSES = ["PENDING", "PROCESSING", "COMPLETED", "FAILED"];

export function ScansPage() {
  const [page, setPage] = useState(0);
  const [status, setStatus] = useState("");
  const [productId, setProductId] = useState("");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");

  const products = useProducts();
  const scans = useScans({ page, size: 20, status, productId, from, to });

  function resetFilters() {
    setStatus("");
    setProductId("");
    setFrom("");
    setTo("");
    setPage(0);
  }

  return (
    <div className="page-inner">
      <PageHeader
        title="All Scans"
        breadcrumbs={[{ label: "Home", to: "/" }, { label: "Scans" }]}
        actions={
          <Link to="/scans/new" className="btn">
            + New Scan
          </Link>
        }
      />

      <Panel title="Filters">
        <div className="toolbar">
          <div className="field">
            <label htmlFor="f-status">Status</label>
            <select
              id="f-status"
              value={status}
              onChange={(e) => {
                setStatus(e.target.value);
                setPage(0);
              }}
            >
              <option value="">All</option>
              {STATUSES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label htmlFor="f-product">Product</label>
            <select
              id="f-product"
              value={productId}
              onChange={(e) => {
                setProductId(e.target.value);
                setPage(0);
              }}
            >
              <option value="">All</option>
              {products.data?.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label htmlFor="f-from">From</label>
            <input
              id="f-from"
              type="date"
              value={from}
              onChange={(e) => {
                setFrom(e.target.value);
                setPage(0);
              }}
            />
          </div>
          <div className="field">
            <label htmlFor="f-to">To</label>
            <input
              id="f-to"
              type="date"
              value={to}
              onChange={(e) => {
                setTo(e.target.value);
                setPage(0);
              }}
            />
          </div>
          <button className="btn secondary sm" type="button" onClick={resetFilters}>
            Clear
          </button>
        </div>
      </Panel>

      <Panel title="Results">
        {scans.isLoading && <Loading />}
        {scans.isError && <Alert kind="error">{toApiError(scans.error).message}</Alert>}
        {scans.data && scans.data.content.length === 0 && (
          <p className="muted small">No scans match the current filters.</p>
        )}
        {scans.data && scans.data.content.length > 0 && (
          <>
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
                  {scans.data.content.map((s) => (
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
                        <Link to={`/scans/${s.id}`}>Open report</Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Pagination
              page={scans.data.number}
              totalPages={scans.data.totalPages}
              totalElements={scans.data.totalElements}
              onChange={setPage}
            />
          </>
        )}
      </Panel>
    </div>
  );
}
