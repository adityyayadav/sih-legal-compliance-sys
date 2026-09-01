import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../../lib/auth";

export function MainNav() {
  const { isAuthenticated, isAdmin, user, logout } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate("/login");
  }

  return (
    <nav className="gov-nav" aria-label="Primary">
      <div className="container">
        <NavLink to="/" end>
          Home
        </NavLink>

        {isAuthenticated && (
          <>
            <NavLink to="/dashboard">Dashboard</NavLink>

            <div className="navitem">
              <button type="button" aria-haspopup="true">
                Scans ▾
              </button>
              <div className="dropdown">
                <NavLink to="/scans">All Scans</NavLink>
                <NavLink to="/scans/new">New Scan</NavLink>
              </div>
            </div>

            <NavLink to="/products">Products</NavLink>
          </>
        )}

        <div className="navitem">
          <button type="button" aria-haspopup="true">
            About ▾
          </button>
          <div className="dropdown">
            <NavLink to="/about">About the Portal</NavLink>
            <NavLink to="/about#rules">Legal Metrology Rules</NavLink>
            <NavLink to="/about#contact">Contact</NavLink>
          </div>
        </div>

        <span className="nav-spacer" />

        {isAuthenticated ? (
          <div className="navitem">
            <button type="button" className="nav-user" aria-haspopup="true">
              {user?.username} ({isAdmin ? "Admin" : "Inspector"}) ▾
            </button>
            <div className="dropdown">
              <NavLink to="/profile">My Profile</NavLink>
              <a
                href="#logout"
                onClick={(e) => {
                  e.preventDefault();
                  void handleLogout();
                }}
              >
                Sign out
              </a>
            </div>
          </div>
        ) : (
          <>
            <NavLink to="/login">Login</NavLink>
            <NavLink to="/register">Register</NavLink>
          </>
        )}
      </div>
    </nav>
  );
}
