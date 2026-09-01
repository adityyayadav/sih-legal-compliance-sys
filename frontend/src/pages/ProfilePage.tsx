import { PageHeader } from "../components/layout/AppLayout";
import { Panel } from "../components/ui";
import { useAuth } from "../lib/auth";
import { fmtDateTime } from "../lib/format";

export function ProfilePage() {
  const { user } = useAuth();
  if (!user) return null;

  return (
    <div className="page-inner">
      <PageHeader
        title="My Profile"
        breadcrumbs={[{ label: "Home", to: "/" }, { label: "Profile" }]}
      />
      <Panel title="Account">
        <dl className="dl">
          <dt>Username</dt>
          <dd>{user.username}</dd>
          <dt>Email</dt>
          <dd>{user.email}</dd>
          <dt>Role</dt>
          <dd>
            <span className={`badge ${user.role === "ADMIN" ? "info" : "muted"}`}>{user.role}</span>
          </dd>
          <dt>Registered</dt>
          <dd>{fmtDateTime(user.createdAt)}</dd>
          <dt>User ID</dt>
          <dd>
            <code>{user.id}</code>
          </dd>
        </dl>
      </Panel>
      <Panel title="Access">
        <p className="small muted">
          {user.role === "ADMIN"
            ? "As an administrator you can view every scan and department-wide statistics."
            : "As an inspector you can view the scans you have submitted and your own statistics."}
        </p>
      </Panel>
    </div>
  );
}
