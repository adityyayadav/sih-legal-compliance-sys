import type { ReactNode } from "react";
import { Outlet } from "react-router-dom";
import { TopBar } from "./TopBar";
import { Masthead } from "./Masthead";
import { MainNav } from "./MainNav";
import { SiteFooter } from "./SiteFooter";

export function AppLayout() {
  return (
    <>
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>
      <TopBar />
      <Masthead />
      <MainNav />
      <main id="main-content" className="page">
        <Outlet />
      </main>
      <SiteFooter />
    </>
  );
}

export function PageHeader({
  title,
  breadcrumbs,
  actions,
}: {
  title: string;
  breadcrumbs?: { label: string; to?: string }[];
  actions?: ReactNode;
}) {
  return (
    <>
      {breadcrumbs && breadcrumbs.length > 0 && (
        <nav className="breadcrumbs" aria-label="Breadcrumb">
          {breadcrumbs.map((b, i) => (
            <span key={i}>
              {i > 0 && " › "}
              {b.to ? <a href={b.to}>{b.label}</a> : b.label}
            </span>
          ))}
        </nav>
      )}
      <div className="page-title-row">
        <h1>{title}</h1>
        {actions}
      </div>
    </>
  );
}
