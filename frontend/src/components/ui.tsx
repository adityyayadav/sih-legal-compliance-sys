import type { ReactNode, InputHTMLAttributes, SelectHTMLAttributes } from "react";
import type { ComplianceStatus, RuleStatus, ScanStatus } from "../lib/types";

export function Panel({
  title,
  actions,
  children,
}: {
  title?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className="panel">
      {(title || actions) && (
        <header>
          <span>{title}</span>
          {actions}
        </header>
      )}
      <div className="panel-body">{children}</div>
    </section>
  );
}

export function Alert({
  kind = "info",
  children,
}: {
  kind?: "info" | "error" | "success";
  children: ReactNode;
}) {
  return (
    <div className={`alert ${kind}`} role={kind === "error" ? "alert" : undefined}>
      {children}
    </div>
  );
}

export function Loading({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="center-load">
      <span className="spinner" /> <span style={{ marginLeft: 8 }}>{label}</span>
    </div>
  );
}

export function Field({
  label,
  htmlFor,
  required,
  error,
  hint,
  children,
}: {
  label: string;
  htmlFor?: string;
  required?: boolean;
  error?: string;
  hint?: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className={`field${error ? " invalid" : ""}`}>
      <label htmlFor={htmlFor}>
        {label} {required && <span className="req">*</span>}
      </label>
      {children}
      {hint && !error && <div className="hint">{hint}</div>}
      {error && <div className="error">{error}</div>}
    </div>
  );
}

export function TextInput(props: InputHTMLAttributes<HTMLInputElement>) {
  return <input {...props} />;
}

export function Select(props: SelectHTMLAttributes<HTMLSelectElement>) {
  return <select {...props} />;
}

const SCAN_BADGE: Record<ScanStatus, string> = {
  PENDING: "muted",
  PROCESSING: "info",
  COMPLETED: "ok",
  FAILED: "fail",
};

export function ScanStatusBadge({ status }: { status: ScanStatus }) {
  return <span className={`badge ${SCAN_BADGE[status]}`}>{status}</span>;
}

export function ComplianceBadge({ status }: { status: ComplianceStatus }) {
  if (!status) return <span className="badge muted">N/A</span>;
  const cls = status === "COMPLIANT" ? "ok" : status === "PARTIAL" ? "warn" : "fail";
  return <span className={`badge ${cls}`}>{status.replace("_", " ")}</span>;
}

export function RuleBadge({ status }: { status: RuleStatus }) {
  const cls =
    status === "PASS" ? "ok" : status === "FAIL" ? "fail" : status === "WARNING" ? "warn" : "muted";
  return <span className={`badge ${cls}`}>{status.replace("_", " ")}</span>;
}

export function Pagination({
  page,
  totalPages,
  totalElements,
  onChange,
}: {
  page: number;
  totalPages: number;
  totalElements: number;
  onChange: (p: number) => void;
}) {
  if (totalPages <= 1) return <div className="small muted">{totalElements} record(s)</div>;
  return (
    <div className="pagination">
      <button onClick={() => onChange(0)} disabled={page === 0}>
        « First
      </button>
      <button onClick={() => onChange(page - 1)} disabled={page === 0}>
        ‹ Prev
      </button>
      <span className="muted">
        Page {page + 1} of {totalPages} · {totalElements} record(s)
      </span>
      <button onClick={() => onChange(page + 1)} disabled={page >= totalPages - 1}>
        Next ›
      </button>
      <button onClick={() => onChange(totalPages - 1)} disabled={page >= totalPages - 1}>
        Last »
      </button>
    </div>
  );
}
