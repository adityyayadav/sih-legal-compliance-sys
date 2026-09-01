import { FormEvent, useState } from "react";
import { PageHeader } from "../components/layout/AppLayout";
import { Alert, Field, Loading, Panel } from "../components/ui";
import { fmtDate } from "../lib/format";
import { toApiError } from "../lib/api";
import { useCreateProduct, useProducts } from "../lib/queries";

const CATEGORIES = [
  "EDIBLE_OIL",
  "PULSES",
  "FLOUR",
  "BEVERAGES",
  "SNACKS",
  "SAUCES",
  "DAIRY",
  "SPICES",
  "OTHER",
];

export function ProductsPage() {
  const list = useProducts();
  const create = useCreateProduct();

  const [form, setForm] = useState({ name: "", category: "EDIBLE_OIL", brand: "" });
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [banner, setBanner] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setFieldErrors({});
    setBanner(null);
    try {
      await create.mutateAsync({
        name: form.name,
        category: form.category,
        brand: form.brand || undefined,
      });
      setForm({ name: "", category: form.category, brand: "" });
      setBanner("Product added to the register.");
    } catch (err) {
      const apiErr = toApiError(err);
      if (apiErr.fieldErrors) setFieldErrors(apiErr.fieldErrors);
      else setBanner(apiErr.message);
    }
  }

  return (
    <div className="page-inner">
      <PageHeader
        title="Product Register"
        breadcrumbs={[{ label: "Home", to: "/" }, { label: "Products" }]}
      />

      <div className="grid cols-2">
        <Panel title="Register a product">
          {banner && <Alert kind={banner.includes("added") ? "success" : "error"}>{banner}</Alert>}
          <form onSubmit={onSubmit} noValidate>
            <Field label="Product name" htmlFor="p-name" required error={fieldErrors.name}>
              <input
                id="p-name"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="e.g. Refined Sunflower Oil 1L"
                required
              />
            </Field>
            <Field label="Category" htmlFor="p-cat" required error={fieldErrors.category}>
              <select
                id="p-cat"
                value={form.category}
                onChange={(e) => setForm({ ...form, category: e.target.value })}
              >
                {CATEGORIES.map((c) => (
                  <option key={c} value={c}>
                    {c.replace(/_/g, " ")}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Brand" htmlFor="p-brand" hint="Optional">
              <input
                id="p-brand"
                value={form.brand}
                onChange={(e) => setForm({ ...form, brand: e.target.value })}
              />
            </Field>
            <button className="btn" type="submit" disabled={create.isPending}>
              {create.isPending ? "Saving…" : "Add product"}
            </button>
          </form>
        </Panel>

        <Panel title={`Registered products${list.data ? ` (${list.data.length})` : ""}`}>
          {list.isLoading && <Loading />}
          {list.isError && <Alert kind="error">{toApiError(list.error).message}</Alert>}
          {list.data && list.data.length === 0 && (
            <p className="muted small">No products registered yet.</p>
          )}
          {list.data && list.data.length > 0 && (
            <div className="table-wrap">
              <table className="gov">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Category</th>
                    <th>Brand</th>
                    <th>Added by</th>
                    <th>Added on</th>
                  </tr>
                </thead>
                <tbody>
                  {list.data.map((p) => (
                    <tr key={p.id}>
                      <td>{p.name}</td>
                      <td>{p.category.replace(/_/g, " ")}</td>
                      <td>{p.brand ?? "—"}</td>
                      <td>{p.createdBy}</td>
                      <td>{fmtDate(p.createdAt)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Panel>
      </div>
    </div>
  );
}
