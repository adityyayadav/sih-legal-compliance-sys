import { Link } from "react-router-dom";
import { PageHeader } from "../components/layout/AppLayout";

export function NotFoundPage() {
  return (
    <div className="page-inner">
      <PageHeader title="Page not found" breadcrumbs={[{ label: "Home", to: "/" }]} />
      <p>The page you requested does not exist or has been moved.</p>
      <Link to="/" className="btn secondary">
        Return to home
      </Link>
    </div>
  );
}
