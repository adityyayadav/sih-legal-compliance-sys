import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { PageHeader } from "../components/layout/AppLayout";
import { Alert, Field, Loading, Panel } from "../components/ui";
import { toApiError } from "../lib/api";
import { useProducts, useSubmitScan } from "../lib/queries";

const ACCEPTED = ["image/jpeg", "image/png"];
const MAX_BYTES = 10 * 1024 * 1024;

export function NewScanPage() {
  const products = useProducts();
  const submit = useSubmitScan();
  const navigate = useNavigate();

  const [productId, setProductId] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);
  const [serverError, setServerError] = useState<string | null>(null);

  function onPick(f: File | null) {
    setLocalError(null);
    if (f && !ACCEPTED.includes(f.type)) {
      setLocalError("Only JPEG or PNG images are accepted.");
      setFile(null);
      return;
    }
    if (f && f.size > MAX_BYTES) {
      setLocalError("File exceeds the 10 MB limit.");
      setFile(null);
      return;
    }
    setFile(f);
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setServerError(null);
    if (!productId || !file) {
      setLocalError("Select a product and a label image.");
      return;
    }
    try {
      const res = await submit.mutateAsync({ file, productId });
      navigate(`/scans/${res.id}`);
    } catch (err) {
      setServerError(toApiError(err).message);
    }
  }

  const noProducts = products.data && products.data.length === 0;

  return (
    <div className="page-inner">
      <PageHeader
        title="Submit a Scan"
        breadcrumbs={[
          { label: "Home", to: "/" },
          { label: "Scans", to: "/scans" },
          { label: "New" },
        ]}
      />

      <div className="grid cols-2">
        <Panel title="Label image">
          {products.isLoading && <Loading />}
          {noProducts && (
            <Alert kind="info">
              No products registered yet. <Link to="/products">Register a product</Link> before
              submitting a scan.
            </Alert>
          )}
          {localError && <Alert kind="error">{localError}</Alert>}
          {serverError && <Alert kind="error">{serverError}</Alert>}

          <form onSubmit={onSubmit} noValidate>
            <Field label="Product" htmlFor="s-product" required>
              <select
                id="s-product"
                value={productId}
                onChange={(e) => setProductId(e.target.value)}
                required
              >
                <option value="">— Select —</option>
                {products.data?.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} {p.brand ? `(${p.brand})` : ""}
                  </option>
                ))}
              </select>
            </Field>

            <Field
              label="Principal display panel photo"
              htmlFor="s-file"
              required
              hint="JPEG or PNG, up to 10 MB. Keep the barcode in frame for print-size calibration."
            >
              <input
                id="s-file"
                type="file"
                accept="image/jpeg,image/png"
                onChange={(e) => onPick(e.target.files?.[0] ?? null)}
              />
            </Field>

            {file && (
              <div style={{ marginBottom: 14 }}>
                <img
                  src={URL.createObjectURL(file)}
                  alt="Selected label preview"
                  style={{ maxHeight: 240, border: "1px solid var(--border)", borderRadius: 3 }}
                />
              </div>
            )}

            <button className="btn" type="submit" disabled={submit.isPending || noProducts}>
              {submit.isPending ? "Processing…" : "Submit for analysis"}
            </button>
          </form>
        </Panel>

        <Panel title="Capture guidance">
          <ul className="small">
            <li>Fill the frame with the principal display panel; avoid glare and shadows.</li>
            <li>Hold the camera parallel to the label — minimise perspective distortion.</li>
            <li>Keep the product barcode fully visible — it is used as a size reference.</li>
            <li>Ensure the net-quantity and MRP text is sharp and legible.</li>
          </ul>
          <p className="small muted">
            Processing is synchronous in this prototype — you will be taken to the report as soon as
            the model service responds.
          </p>
        </Panel>
      </div>
    </div>
  );
}
