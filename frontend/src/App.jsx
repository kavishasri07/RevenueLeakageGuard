import { useState, useEffect } from 'react'
import heroImg from './assets/hero.png'
import reactLogo from './assets/react.svg'
import viteLogo from './assets/vite.svg'
import './App.css'
import {
  getOverviewKPIs,
  getLeakageByCategory,
  getTopLeaks,
  listCustomers,
  listReconciliationEvents,
  approveReconciliationEvent,
  rejectReconciliationEvent,
} from './api/client'



/* =========================================================
   HELPERS
========================================================= */

function formatCurrency(value) {
  if (value === null || value === undefined) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

const ISSUE_LABELS = {
  usage_exceeds_entitlement: "Usage overage",
  provisioned_not_billed: "Provisioned, not billed",
  expired_discount_still_applied: "Expired discount",
  entitlement_contract_mismatch: "Entitlement drift",
};

const STATUS_LABELS = {
  open: "Open",
  proposed: "Proposed",
  finance_approved: "Approved",
  rejected: "Rejected",
  resolved: "Resolved",
};

function getInitials(name) {
  if (!name) return "FA";
  return name
    .trim()
    .split(/\s+/)
    .map((w) => w[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

function nameFromEmail(email) {
  const local = email.split("@")[0] || "";
  return local
    .split(/[._-]+/)
    .filter(Boolean)
    .map((w) => w[0].toUpperCase() + w.slice(1))
    .join(" ") || "Finance Admin";
}


/* =========================================================
   ICONS
========================================================= */

function Icon({ name, size = 18 }) {
  const common = {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.8,
    strokeLinecap: "round",
    strokeLinejoin: "round",
  };

  switch (name) {
    case "dollar":
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="9" />
          <path d="M12 7v10" />
          <path d="M9.5 9.7c0-1.3 1.2-2.2 2.5-2.2s2.5.8 2.5 2c0 3-5 1.5-5 4.5 0 1.2 1.2 2 2.5 2s2.5-.9 2.5-2.2" />
        </svg>
      );

    case "gauge":
      return (
        <svg {...common}>
          <path d="M4 15a8 8 0 1 1 16 0" />
          <path d="M12 15l4-5" />
          <circle cx="12" cy="15" r="1.3" />
        </svg>
      );

    case "spark":
      return (
        <svg {...common}>
          <path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z" />
        </svg>
      );

    case "shield":
      return (
        <svg {...common}>
          <path d="M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6z" />
          <path d="M9 12l2 2 4-4" />
        </svg>
      );

    case "check":
      return (
        <svg {...common}>
          <path d="M20 6L9 17l-5-5" />
        </svg>
      );

    case "x":
      return (
        <svg {...common}>
          <path d="M6 6l12 12M18 6L6 18" />
        </svg>
      );

    case "home":
      return (
        <svg {...common}>
          <path d="M3 11l9-8 9 8" />
          <path d="M5 10v10h14V10" />
          <path d="M9 20v-6h6v6" />
        </svg>
      );

    case "users":
      return (
        <svg {...common}>
          <circle cx="9" cy="8" r="3" />
          <path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6" />
          <path d="M16 5.5a3 3 0 0 1 0 5.8" />
          <path d="M18 14c1.8.8 3 2.6 3 4.7" />
        </svg>
      );

    case "alert":
      return (
        <svg {...common}>
          <path d="M10.3 4.2L2.8 17a2 2 0 0 0 1.7 3h15a2 2 0 0 0 1.7-3L13.7 4.2a2 2 0 0 0-3.4 0z" />
          <path d="M12 9v4" />
          <circle cx="12" cy="16.5" r=".7" fill="currentColor" />
        </svg>
      );

    case "recovery":
      return (
        <svg {...common}>
          <path d="M4 19V9" />
          <path d="M10 19V5" />
          <path d="M16 19v-7" />
          <path d="M22 19H2" />
        </svg>
      );

    case "upload":
      return (
        <svg {...common}>
          <path d="M12 15V3" />
          <path d="M8 7l4-4 4 4" />
          <path d="M5 13v6h14v-6" />
        </svg>
      );

    case "menu":
      return (
        <svg {...common}>
          <path d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      );

    case "logout":
      return (
        <svg {...common}>
          <path d="M10 17l5-5-5-5" />
          <path d="M15 12H3" />
          <path d="M14 4h5v16h-5" />
        </svg>
      );

    case "arrow":
      return (
        <svg {...common}>
          <path d="M5 12h14" />
          <path d="M13 6l6 6-6 6" />
        </svg>
      );

    case "refresh":
      return (
        <svg {...common}>
          <path d="M20 11a8 8 0 0 0-14.8-4L3 9" />
          <path d="M3 4v5h5" />
          <path d="M4 13a8 8 0 0 0 14.8 4L21 15" />
          <path d="M21 20v-5h-5" />
        </svg>
      );

    case "file":
      return (
        <svg {...common}>
          <path d="M6 3h8l4 4v14H6z" />
          <path d="M14 3v5h5" />
          <path d="M9 13h6M9 17h6" />
        </svg>
      );

    default:
      return null;
  }
}


/* =========================================================
   HUMAN CHECK
========================================================= */

function HumanCheck({ checked, onChange }) {
  return (
    <div className="human-check">
      <button
        type="button"
        role="checkbox"
        aria-checked={checked}
        className={"human-box" + (checked ? " checked" : "")}
        onClick={() => onChange(!checked)}
      >
        {checked && <Icon name="check" size={14} />}
      </button>

      <span>I'm not a robot</span>

      <div className="human-badge">
        <Icon name="shield" size={22} />
        <span>reCAPTCHA</span>
      </div>
    </div>
  );
}


/* =========================================================
   AUTH SHELL
========================================================= */

function AuthShell({ children }) {
  return (
    <div className="auth-shell">
      <div className="auth-brand">

        <div className="brand-mark">
          <Icon name="shield" />
          <span>Revora</span>
        </div>

        <h1>
          Every drifted contract is money still on the table.
        </h1>

        <p>
          Revora reconciles signed contracts, billing config,
          entitlements and usage continuously — so finance only
          reviews what actually changed.
        </p>

        <ul className="brand-points">
          <li>
            <Icon name="dollar" />
            Catch-up billing proposals, raised automatically
          </li>

          <li>
            <Icon name="gauge" />
            Usage vs. entitlement drift, tracked continuously
          </li>

          <li>
            <Icon name="spark" />
            Every customer-facing adjustment needs finance approval
          </li>
        </ul>

      </div>

      <div className="auth-card">
        {children}
      </div>
    </div>
  );
}


/* =========================================================
   LOGIN
========================================================= */

function LoginPage({ onLogin, goSignup }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [verified, setVerified] = useState(false);
  const [error, setError] = useState("");

  function submit(e) {
    e.preventDefault();

    if (!email || !password) {
      setError("Enter your email and password to continue.");
      return;
    }

    if (!verified) {
      setError("Please confirm you're not a robot.");
      return;
    }

    setError("");

    onLogin({
      email,
      name: nameFromEmail(email),
    });
  }

  return (
    <AuthShell>

      <form
        className="auth-form"
        onSubmit={submit}
        noValidate
      >

        <h2>Sign in</h2>

        <p className="auth-sub">
          Welcome back. Enter your workspace credentials.
        </p>

        <label htmlFor="login-email">
          Work email
        </label>

        <input
          id="login-email"
          type="email"
          placeholder="you@company.com"
          value={email}
          onChange={(e) =>
            setEmail(e.target.value)
          }
        />

        <label htmlFor="login-password">
          Password
        </label>

        <input
          id="login-password"
          type="password"
          placeholder="••••••••"
          value={password}
          onChange={(e) =>
            setPassword(e.target.value)
          }
        />

        <HumanCheck
          checked={verified}
          onChange={setVerified}
        />

        {error && (
          <div className="auth-error">
            {error}
          </div>
        )}

        <button
          type="submit"
          className="btn-primary full"
        >
          Sign in
        </button>

        <p className="auth-switch">
          Don't have a workspace yet?{" "}
          <button
            type="button"
            className="link-btn"
            onClick={goSignup}
          >
            Create one
          </button>
        </p>

      </form>

    </AuthShell>
  );
}


/* =========================================================
   SIGNUP
========================================================= */

function SignupPage({ onSignup, goLogin }) {
  const [form, setForm] = useState({
    name: "",
    company: "",
    email: "",
    password: "",
  });

  const [verified, setVerified] = useState(false);
  const [error, setError] = useState("");

  function update(field, value) {
    setForm((f) => ({
      ...f,
      [field]: value,
    }));
  }

  function submit(e) {
    e.preventDefault();

    if (
      !form.name ||
      !form.company ||
      !form.email ||
      !form.password
    ) {
      setError(
        "Fill in every field to create your workspace."
      );
      return;
    }

    if (!verified) {
      setError("Please confirm you're not a robot.");
      return;
    }

    setError("");


    onSignup(form);
  }

  return (
    <AuthShell>

      <form
        className="auth-form"
        onSubmit={submit}
        noValidate
      >

        <h2>Create your workspace</h2>

        <p className="auth-sub">
          Set up Revora for your finance and RevOps team.
        </p>

        <label htmlFor="su-name">
          Full name
        </label>

        <input
          id="su-name"
          type="text"
          placeholder="Finance Admin"
          value={form.name}
          onChange={(e) =>
            update("name", e.target.value)
          }
        />

        <label htmlFor="su-company">
          Company
        </label>

        <input
          id="su-company"
          type="text"
          placeholder="Acme Technologies"
          value={form.company}
          onChange={(e) =>
            update("company", e.target.value)
          }
        />

        <label htmlFor="su-email">
          Work email
        </label>

        <input
          id="su-email"
          type="email"
          placeholder="you@company.com"
          value={form.email}
          onChange={(e) =>
            update("email", e.target.value)
          }
        />

        <label htmlFor="su-password">
          Password
        </label>

        <input
          id="su-password"
          type="password"
          placeholder="Create a password"
          value={form.password}
          onChange={(e) =>
            update("password", e.target.value)
          }
        />

        <HumanCheck
          checked={verified}
          onChange={setVerified}
        />

        {error && (
          <div className="auth-error">
            {error}
          </div>
        )}

        <button
          type="submit"
          className="btn-primary full"
        >
          Create workspace
        </button>

        <p className="auth-switch">
          Already have a workspace?{" "}
          <button
            type="button"
            className="link-btn"
            onClick={goLogin}
          >
            Sign in
          </button>
        </p>

      </form>

    </AuthShell>
  );
}


/* =========================================================
   STATUS BADGE
========================================================= */

function StatusBadge({ status }) {
  if (!status) return null;

  const cls = String(status)
    .toLowerCase()
    .replace(/\s+/g, "-");

  return (
    <span className={`status-badge ${cls}`}>
      <span className="status-dot" />
      {status}
    </span>
  );
}


/* =========================================================
   SIDEBAR
========================================================= */

function Sidebar({
  page,
  setPage,
  mobileOpen,
  setMobileOpen,
  onLogout,
  user,
}) {
  const navigation = [
    {
      id: "dashboard",
      label: "Dashboard",
      icon: "home",
    },
    {
      id: "customers",
      label: "Customers",
      icon: "users",
    },
    {
      id: "findings",
      label: "Findings",
    },
    {
      id: "recovery",
      label: "Recovery",
      icon: "recovery",
    },
    {
      id: "upload",
      label: "Upload",
      icon: "upload",
    },
  ];

  function navigate(id) {
    setPage(id);
    setMobileOpen(false);
  }

  return (
    <>
      {mobileOpen && (
        <div
          className="sidebar-overlay"
          onClick={() =>
            setMobileOpen(false)
          }
        />
      )}

      <aside
        className={
          "sidebar" +
          (mobileOpen ? " mobile-open" : "")
        }
      >

        <div className="sidebar-brand">
          <div className="sidebar-logo">
            <Icon name="shield" size={19} />
          </div>

          <span>Revora</span>
        </div>

        <div className="workspace-label">
          WORKSPACE
        </div>

        <nav className="sidebar-nav">

          {navigation.map((item) => (
            <button
              key={item.id}
              className={
                "sidebar-item" +
                (page === item.id
                  ? " active"
                  : "")
              }
              onClick={() =>
                navigate(item.id)
              }
            >

              <Icon name={item.icon} />

              <span>
                {item.label}
              </span>

            </button>
          ))}

        </nav>

        <div className="sidebar-bottom">

          <div className="sidebar-user">

            <div className="avatar">
              {getInitials(user?.name)}
            </div>

            <div>
              <strong>
                {user?.name || "Finance Admin"}
              </strong>

              <span>
                Administrator
              </span>
            </div>

          </div>

          <button
            className="sidebar-logout"
            onClick={onLogout}
          >
            <Icon name="logout" />
            Sign out
          </button>

        </div>

      </aside>
    </>
  );
}


/* =========================================================
   NAVBAR
========================================================= */

function Navbar({
  page,
  setMobileOpen,
  user,
}) {
  const titles = {
    dashboard: "Executive Dashboard",
    customers: "Customers",
    customerDetail: "Customer Detail",
    findings: "Leakage Findings",
    recovery: "Recovery",
    upload: "Upload Contract",
  };

  const title =
    titles[page] ||
    "Executive Dashboard";

  return (
    <header className="topbar">

      <div className="topbar-left">

        <button
          className="mobile-menu"
          onClick={() =>
            setMobileOpen(true)
          }
        >
          <Icon name="menu" />
        </button>

        <div>

          <div className="breadcrumb">
            Revora /{" "}
            <span>{title}</span>
          </div>

          <h1>{title}</h1>

        </div>

      </div>

      <div className="topbar-right">

        <div className="live-indicator">
          <span />
          Monitoring active
        </div>

        <div className="top-avatar">
          {getInitials(user?.name)}
        </div>

      </div>

    </header>
  );
}


/* =========================================================
   KPI CARD
========================================================= */

function KPICard({
  label,
  value,
  helper,
  icon,
  variant,
}) {
  return (
    <div className="kpi-card">

      <div className="kpi-top">

        <div className="kpi-label">
          {label}
        </div>

        <div
          className={`kpi-icon ${
            variant || ""
          }`}
        >
          <Icon
            name={icon}
            size={19}
          />
        </div>

      </div>

      <div className="kpi-value">
        {value ?? "—"}
      </div>

      <div className="kpi-helper">
        {helper}
      </div>

    </div>
  );
}


/* =========================================================
   DASHBOARD — connected to backend
========================================================= */

function Dashboard({ setPage }) {
  const [dashboardData, setDashboardData] = useState(null);
  const [categoryData, setCategoryData] = useState([]);
  const [topLeaks, setTopLeaks] = useState([]);
  const [loadError, setLoadError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [overview, customers, approvedEvents, byCategory, leaks] = await Promise.all([
          getOverviewKPIs(),
          listCustomers(),
          listReconciliationEvents("finance_approved"),
          getLeakageByCategory(),
          getTopLeaks(5),
        ]);

        if (cancelled) return;

        const approvedRecoveryTotal = approvedEvents.reduce(
          (sum, e) => sum + e.delta_amount,
          0
        );

        setDashboardData({
          potentialRevenueLeakage: formatCurrency(overview.potential_revenue_recovery),
          approvedRecovery: formatCurrency(approvedRecoveryTotal),
          openFindings: overview.active_revenue_leaks,
          customersMonitored: customers.length,
        });
        setCategoryData(byCategory);
        setTopLeaks(leaks);
      } catch (err) {
        if (!cancelled) setLoadError(err.message);
      }
    }

    load();
    return () => { cancelled = true; };
  }, []);

  return (
    <div className="page-content">

      <div className="page-intro">
        <div>
          <h2>Revenue overview</h2>
          <p>Monitor revenue leakage across contracts, usage and billing.</p>
        </div>

        <div className="last-sync">
          <span className="sync-dot" />
          {loadError ? "Backend unreachable" : dashboardData ? "Connected to backend" : "Loading..."}
        </div>
      </div>

      {/* KPI CARDS */}
      <div className="kpi-grid">
        <KPICard
          label="Potential Revenue Leakage"
          value={dashboardData?.potentialRevenueLeakage}
          helper="Across monitored accounts"
          icon="dollar"
          variant="blue"
        />
        <KPICard
          label="Approved Recovery"
          value={dashboardData?.approvedRecovery}
          helper="Monthly recovery approved"
          icon="check"
          variant="green"
        />
        <KPICard
          label="Open Findings"
          value={dashboardData?.openFindings}
          helper="Require finance review"
          icon="alert"
          variant="red"
        />
        <KPICard
          label="Customers Monitored"
          value={dashboardData?.customersMonitored}
          helper="Continuously reconciled"
          icon="users"
          variant="purple"
        />
      </div>

      {/* REVENUE LEAKAGE + HEALTH */}
      <div className="dashboard-grid">

        <div className="panel">
          <div className="panel-header">
            <div>
              <h3>Revenue Leakage</h3>
              <p>Potential recovery by leakage type</p>
            </div>
            <button className="period-button">This month</button>
          </div>

          {categoryData.length === 0 ? (
            <div className="empty-state compact">
              <div className="empty-icon"><Icon name="gauge" size={22} /></div>
              <h3>No leakage data yet</h3>
              <p>Leakage data will appear here once there's data to reconcile.</p>
            </div>
          ) : (
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr><th>Leakage type</th><th>Amount</th><th>% of total</th></tr>
                </thead>
                <tbody>
                  {categoryData.map((c) => (
                    <tr key={c.discrepancy_type}>
                      <td>{ISSUE_LABELS[c.discrepancy_type] || c.discrepancy_type}</td>
                      <td>{formatCurrency(c.total_amount)}</td>
                      <td>{c.pct_of_total}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="panel health-panel">
          <div className="panel-header">
            <div>
              <h3>Revenue Health</h3>
              <p>Overall workspace signal</p>
            </div>
          </div>

          {!dashboardData ? (
            <div className="empty-state compact">
              <div className="empty-icon"><Icon name="shield" size={22} /></div>
              <h3>Awaiting data</h3>
              <p>Workspace health will be calculated from backend data.</p>
            </div>
          ) : (
            <div className="empty-state compact">
              <div className="empty-icon"><Icon name="shield" size={22} /></div>
              <h3>{dashboardData.openFindings} open finding{dashboardData.openFindings === 1 ? "" : "s"}</h3>
              <p>across {dashboardData.customersMonitored} monitored customer{dashboardData.customersMonitored === 1 ? "" : "s"}.</p>
            </div>
          )}
        </div>

      </div>

      {/* CUSTOMER TABLE — showing top affected customers */}
      <div className="panel customer-panel">
        <div className="panel-header">
          <div>
            <h3>Customers</h3>
            <p>Accounts with revenue risk</p>
          </div>
          <button className="text-button" onClick={() => setPage("customers")}>
            View all
            <Icon name="arrow" size={14} />
          </button>
        </div>

        {topLeaks.length === 0 ? (
          <EmptyTable
            message="No customer data available yet."
            action="Customer records will appear once there's reconciliation data."
          />
        ) : (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr><th>Customer</th><th>Issue</th><th>Impact</th><th>Status</th></tr>
              </thead>
              <tbody>
                {topLeaks.map((leak) => (
                  <tr key={leak.reconciliation_event_id}>
                    <td><strong>{leak.customer_name}</strong></td>
                    <td>{leak.issue}</td>
                    <td>{formatCurrency(leak.monthly_impact)}</td>
                    <td><StatusBadge status={STATUS_LABELS[leak.status] || leak.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

    </div>
  );
}


/* =========================================================
   EMPTY TABLE
========================================================= */

function EmptyTable({
  message,
  action,
}) {
  return (
    <div className="empty-state table-empty">

      <div className="empty-icon">
        <Icon
          name="users"
          size={22}
        />
      </div>

      <h3>{message}</h3>

      <p>{action}</p>

    </div>
  );
}


/* =========================================================
   CUSTOMERS PAGE — connected to backend
========================================================= */

function CustomersPage({ setPage }) {
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const rawCustomers = await listCustomers();

        const enriched = await Promise.all(
          rawCustomers.map(async (c) => {
            const events = await listReconciliationEvents("open", c.id);
            const openFindings = events.length;
            const recoverySum = events.reduce((sum, e) => sum + e.delta_amount, 0);
            const initials = c.name
              .split(" ")
              .map((w) => w[0])
              .join("")
              .slice(0, 2)
              .toUpperCase();

            return {
              id: c.id,
              initials,
              name: c.name,
              health: openFindings === 0 ? "Healthy" : "At risk",
              arr: "—",
              findings: openFindings,
              recovery: formatCurrency(recoverySum),
              status: openFindings === 0 ? "Healthy" : "At Risk",
            };
          })
        );

        if (!cancelled) setCustomers(enriched);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => { cancelled = true; };
  }, []);

  const totalCustomers = customers.length;
  const atRisk = customers.filter((c) => c.status === "At Risk").length;
  const healthy = totalCustomers - atRisk;
  const totalRecovery = customers.reduce((sum, c) => {
    const numeric = Number(String(c.recovery).replace(/[^0-9.-]/g, ""));
    return sum + (Number.isFinite(numeric) ? numeric : 0);
  }, 0);

  return (
    <div className="page-content">

      <div className="page-intro">
        <div>
          <h2>Customer monitoring</h2>
          <p>Review contract, usage and billing alignment across every account.</p>
        </div>
      </div>

      <div className="customer-stats">
        <div className="mini-stat"><span>Total customers</span><strong>{totalCustomers || "—"}</strong></div>
        <div className="mini-stat"><span>At risk</span><strong>{totalCustomers ? atRisk : "—"}</strong></div>
        <div className="mini-stat"><span>Healthy</span><strong>{totalCustomers ? healthy : "—"}</strong></div>
        <div className="mini-stat"><span>Potential recovery</span><strong>{totalCustomers ? formatCurrency(totalRecovery) : "—"}</strong></div>
      </div>

      <div className="panel">
        <div className="panel-header">
          <div>
            <h3>All Customers</h3>
            <p>Customer data from your backend</p>
          </div>
        </div>

        {!loading && customers.length === 0 ? (
          <EmptyTable
            message="No customers available."
            action="Add a customer through the API to populate this table."
          />
        ) : (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Customer</th><th>ARR</th><th>Open Findings</th>
                  <th>Potential Recovery</th><th>Status</th><th />
                </tr>
              </thead>
              <tbody>
                {customers.map((customer) => (
                  <tr
                    key={customer.id}
                    className="clickable-row"
                    onClick={() => setPage(customer.id)}
                  >
                    <td>
                      <div className="customer-cell">
                        <div className="customer-avatar">{customer.initials}</div>
                        <div>
                          <strong>{customer.name}</strong>
                          <span>{customer.health}</span>
                        </div>
                      </div>
                    </td>
                    <td>{customer.arr}</td>
                    <td>{customer.findings}</td>
                    <td>{customer.recovery}</td>
                    <td><StatusBadge status={customer.status} /></td>
                    <td><Icon name="arrow" size={16} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

    </div>
  );
}


/* =========================================================
   CUSTOMER DETAIL
========================================================= */

function CustomerDetail({
  customerId,
  goBack,
}) {


  const customer = null;

  const [reconciled, setReconciled] =
    useState(false);

  async function runReconciliation() {

    setReconciled(true);
  }

  return (
    <div className="page-content">

      <button
        className="back-button"
        onClick={goBack}
      >
        ← Back to customers
      </button>


      {!customer ? (
        <div className="panel">

          <div className="empty-state">

            <div className="empty-icon">
              <Icon
                name="users"
                size={24}
              />
            </div>

            <h3>
              Customer data unavailable
            </h3>

            <p>
              Customer ID: {customerId}
              <br />
              Connect the customer API to load
              this customer's information.
            </p>

          </div>

        </div>
      ) : (
        <>
          <div className="customer-header">

            <div className="customer-header-main">

              <div className="large-customer-avatar">
                {customer.initials}
              </div>

              <div>

                <div className="customer-title-row">

                  <h2>
                    {customer.name}
                  </h2>

                  <StatusBadge
                    status={
                      customer.status
                    }
                  />

                </div>

                <p>
                  Customer account
                </p>

              </div>

            </div>

            <div className="customer-header-metrics">

              <div>
                <span>ARR</span>
                <strong>
                  {customer.arr}
                </strong>
              </div>

              <div>
                <span>Health Score</span>
                <strong>
                  {customer.health}
                </strong>
              </div>

            </div>

          </div>


          <div className="detail-grid">

            <DetailCard
              title="Contract"
              icon="file"
            >
              <DetailRow
                label="Purchased Seats"
                value={
                  customer.contract?.purchasedSeats
                }
              />

              <DetailRow
                label="Price Per Seat"
                value={
                  customer.contract?.pricePerSeat
                }
              />

              <DetailRow
                label="Contract Value"
                value={
                  customer.contract?.contractValue
                }
                strong
              />
            </DetailCard>


            <DetailCard
              title="Usage"
              icon="gauge"
            >
              <DetailRow
                label="Active Seats"
                value={
                  customer.usage?.activeSeats
                }
                strong
              />

              <DetailRow
                label="Utilization"
                value={
                  customer.usage?.utilization
                }
              />

              <DetailRow
                label="Last Activity"
                value={
                  customer.usage?.lastActivity
                }
              />
            </DetailCard>


            <DetailCard
              title="Billing"
              icon="dollar"
            >
              <DetailRow
                label="Billed Seats"
                value={
                  customer.billing?.billedSeats
                }
                strong
              />

              <DetailRow
                label="Monthly Invoice"
                value={
                  customer.billing?.monthlyInvoice
                }
              />

              <DetailRow
                label="Billing Status"
                value={
                  customer.billing?.status
                }
              />
            </DetailCard>


            <DetailCard
              title="Entitlement"
              icon="shield"
            >
              <DetailRow
                label="Provisioned Seats"
                value={
                  customer.entitlement?.provisionedSeats
                }
              />

              <DetailRow
                label="Contract Seats"
                value={
                  customer.entitlement?.contractSeats
                }
              />

              <DetailRow
                label="Seat Drift"
                value={
                  customer.entitlement?.seatDrift
                }
                strong
              />
            </DetailCard>

          </div>


          <div className="reconciliation-panel">

            <div className="reconciliation-copy">

              <div className="reconciliation-icon">
                <Icon
                  name="refresh"
                  size={22}
                />
              </div>

              <div>

                <h3>
                  Reconciliation
                </h3>

                <p>
                  Compare signed contract terms
                  against current usage, billing
                  and entitlement data.
                </p>

              </div>

            </div>

            <button
              className="btn-primary"
              onClick={
                runReconciliation
              }
            >
              <Icon
                name="refresh"
                size={16}
              />
              Run Reconciliation
            </button>

          </div>


          {reconciled && (
            <div className="reconciliation-result">

              <div className="result-icon">
                <Icon
                  name="alert"
                  size={22}
                />
              </div>

              <div className="result-content">

                <div className="result-label">
                  Reconciliation complete
                </div>

                <h3>
                  Result received from backend.
                </h3>

                <p>
                  Replace this section with
                  the reconciliation response
                  from your API.
                </p>

              </div>

            </div>
          )}
        </>
      )}

    </div>
  );
}


/* =========================================================
   DETAIL CARD
========================================================= */

function DetailCard({
  title,
  icon,
  children,
}) {
  return (
    <div className="detail-card">

      <div className="detail-card-header">

        <div className="detail-card-icon">
          <Icon name={icon} />
        </div>

        <h3>{title}</h3>

      </div>

      <div className="detail-card-body">
        {children}
      </div>

    </div>
  );
}


/* =========================================================
   DETAIL ROW
========================================================= */

function DetailRow({
  label,
  value,
  strong,
}) {
  return (
    <div className="detail-row">

      <span>{label}</span>

      <strong
        className={
          strong
            ? "highlight-value"
            : ""
        }
      >
        {value ?? "—"}
      </strong>

    </div>
  );
}


/* =========================================================
   FINDINGS PAGE — connected to backend
========================================================= */

function FindingsPage({ approved, setApproved }) {
  const [findings, setFindings] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    try {
      const events = await listReconciliationEvents("open");
      setFindings(
        events.map((e) => ({
          id: e.id,
          customer: e.customer_id,
          issue: ISSUE_LABELS[e.discrepancy_type] || e.discrepancy_type,
          recovery: formatCurrency(e.delta_amount),
          confidence: "—",
          status: "Open",
          explanation: e.explanation,
        }))
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function approveFinding(id) {
    await approveReconciliationEvent(id, "Finance Admin");
    setApproved((prev) => ({ ...prev, [id]: "Approved" }));
    setFindings((prev) => prev.filter((f) => f.id !== id));
  }

  async function rejectFinding(id) {
    await rejectReconciliationEvent(id, "Finance Admin");
    setApproved((prev) => ({ ...prev, [id]: "Rejected" }));
    setFindings((prev) => prev.filter((f) => f.id !== id));
  }

  return (
    <div className="page-content">

      <div className="page-intro">
        <div>
          <h2>Leakage findings</h2>
          <p>Review detected revenue leakage before customer-facing adjustments are made.</p>
        </div>
        <div className="findings-summary">{findings.length || "—"} open findings</div>
      </div>

      {!loading && findings.length === 0 ? (
        <div className="panel">
          <EmptyTable
            message="No findings available."
            action="Findings appear here once reconciliation detects a discrepancy."
          />
        </div>
      ) : (
        <div className="findings-layout">
          <div className="findings-list">
            {findings.map((finding) => {
              const currentStatus = approved[finding.id] || finding.status;
              return (
                <div
                  key={finding.id}
                  className={"finding-card" + (selected === finding.id ? " selected" : "")}
                  onClick={() => setSelected(finding.id)}
                >
                  <div className="finding-top">
                    <div>
                      <div className="finding-customer">{finding.customer}</div>
                      <h3>{finding.issue}</h3>
                    </div>
                    <StatusBadge status={currentStatus} />
                  </div>

                  <div className="finding-bottom">
                    <div><span>Potential Recovery</span><strong>{finding.recovery}</strong></div>
                    <div><span>Confidence</span><strong>{finding.confidence}</strong></div>
                  </div>

                  {currentStatus === "Open" && (
                    <div className="finding-actions" onClick={(e) => e.stopPropagation()}>
                      <button className="approve-button" onClick={() => approveFinding(finding.id)}>
                        <Icon name="check" size={15} /> Approve
                      </button>
                      <button className="reject-button" onClick={() => rejectFinding(finding.id)}>
                        <Icon name="x" size={15} /> Reject
                      </button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          <div className="evidence-panel">
            <div className="evidence-header">
              <div className="evidence-icon"><Icon name="file" /></div>
              <div>
                <h3>Evidence</h3>
                <p>{selected ? "Finding evidence" : "Select a finding"}</p>
              </div>
            </div>

            {!selected ? (
              <div className="evidence-empty">
                <Icon name="file" size={30} />
                <p>Click a finding to inspect its evidence.</p>
              </div>
            ) : (
              <div className="evidence-content">
                <p>{findings.find((f) => f.id === selected)?.explanation || "No explanation available."}</p>
              </div>
            )}
          </div>
        </div>
      )}

    </div>
  );
}


/* =========================================================
   RECOVERY PAGE — connected to backend
========================================================= */

function RecoveryPage({ approved }) {
  const [recoveryData, setRecoveryData] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      const [overview, approvedEvents, resolvedEvents] = await Promise.all([
        getOverviewKPIs(),
        listReconciliationEvents("finance_approved"),
        listReconciliationEvents("resolved"),
      ]);

      if (cancelled) return;

      const approvedTotal = approvedEvents.reduce((sum, e) => sum + e.delta_amount, 0);
      const resolvedTotal = resolvedEvents.reduce((sum, e) => sum + e.delta_amount, 0);

      setRecoveryData({
        potentialRecovery: formatCurrency(overview.potential_revenue_recovery),
        approvedRecovery: formatCurrency(approvedTotal),
        recoveredRevenue: formatCurrency(resolvedTotal),
        opportunities: approvedEvents.map((e) => ({
          id: e.id,
          customer: e.customer_id,
          issue: ISSUE_LABELS[e.discrepancy_type] || e.discrepancy_type,
          recovery: formatCurrency(e.delta_amount),
        })),
      });
    }

    load();
    return () => { cancelled = true; };
  }, []);

  return (
    <div className="page-content">

      <div className="page-intro">
        <div>
          <h2>Recovery dashboard</h2>
          <p>Track revenue opportunities approved by finance.</p>
        </div>
      </div>

      <div className="recovery-kpis">
        <KPICard label="Potential Recovery" value={recoveryData?.potentialRecovery} helper="Total detected opportunity" icon="dollar" variant="blue" />
        <KPICard label="Approved Recovery" value={recoveryData?.approvedRecovery} helper="Finance-approved opportunity" icon="check" variant="green" />
        <KPICard label="Recovered Revenue" value={recoveryData?.recoveredRevenue} helper="Actual collected revenue" icon="recovery" variant="purple" />
      </div>

      <div className="panel">
        <div className="panel-header">
          <div>
            <h3>Approved Opportunities</h3>
            <p>Revenue adjustments ready for execution</p>
          </div>
        </div>

        {!recoveryData || recoveryData.opportunities.length === 0 ? (
          <EmptyTable
            message="No approved opportunities yet."
            action="Approve a finding on the Findings page to see it here."
          />
        ) : (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr><th>Customer</th><th>Issue</th><th>Recovery</th><th>Status</th></tr>
              </thead>
              <tbody>
                {recoveryData.opportunities.map((opportunity) => (
                  <tr key={opportunity.id}>
                    <td><strong>{opportunity.customer}</strong></td>
                    <td>{opportunity.issue}</td>
                    <td><strong>{opportunity.recovery}</strong></td>
                    <td><StatusBadge status="Approved" /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

    </div>
  );
}


/* =========================================================
   UPLOAD PAGE
========================================================= */

function UploadPage() {
  const [file, setFile] =
    useState(null);

  const [uploading, setUploading] =
    useState(false);

  const [uploaded, setUploaded] =
    useState(false);

  async function handleFile(e) {
    const selectedFile =
      e.target.files?.[0];

    if (!selectedFile) return;

    setFile(selectedFile);
    setUploaded(false);
  }

  async function uploadContract() {
    if (!file) return;

    setUploading(true);

    setTimeout(() => {
      setUploading(false);
      setUploaded(true);
    }, 500);
  }

  return (
    <div className="page-content">

      <div className="page-intro">

        <div>
          <h2>
            Upload contract
          </h2>

          <p>
            Upload a contract for backend
            ingestion and extraction.
          </p>
        </div>

      </div>


      <div className="upload-card">

        <div className="upload-icon">
          <Icon
            name="upload"
            size={28}
          />
        </div>

        <h3>
          Upload Contract
        </h3>

        <p>
          Drop a contract here or select
          a file from your computer.
        </p>

        <label className="upload-button">

          Choose PDF or DOCX

          <input
            type="file"
            accept=".pdf,.docx"
            onChange={handleFile}
          />

        </label>

        <span className="upload-hint">
          Accepted formats: PDF, DOCX
        </span>


        {file && (
          <div className="selected-file">

            <Icon
              name="file"
              size={17}
            />

            <span>
              {file.name}
            </span>

            <button
              className="upload-submit"
              onClick={
                uploadContract
              }
              disabled={uploading}
            >
              {uploading
                ? "Uploading..."
                : "Upload"}
            </button>

          </div>
        )}

      </div>


      {uploaded && (
        <div className="extraction-result">

          <div className="extraction-header">

            <div className="result-icon success">
              <Icon name="check" />
            </div>

            <div>

              <h3>
                Upload complete
              </h3>

              <p>
                The backend can now return
                extracted contract information.
              </p>

            </div>

          </div>

          <div className="backend-placeholder">

            <Icon
              name="file"
              size={22}
            />

            <span>
              Contract extraction result
              will be displayed here.
            </span>

          </div>

        </div>
      )}

    </div>
  );
}


/* =========================================================
   DASHBOARD APP
========================================================= */

function DashboardApp({
  user,
  onLogout,
}) {
  const [page, setPage] =
    useState("dashboard");

  const [mobileOpen, setMobileOpen] =
    useState(false);

  const [approved, setApproved] =
    useState({});

  const [selectedCustomerId, setSelectedCustomerId] =
    useState(null);

  function openCustomer(id) {
    setSelectedCustomerId(id);
    setPage("customerDetail");
  }

  function renderPage() {

    if (page === "dashboard") {
      return (
        <Dashboard
          setPage={setPage}
        />
      );
    }

    if (page === "customers") {
      return (
        <CustomersPage
          setPage={openCustomer}
        />
      );
    }

    if (page === "customerDetail") {
      return (
        <CustomerDetail
          customerId={
            selectedCustomerId
          }
          goBack={() =>
            setPage("customers")
          }
        />
      );
    }

    if (page === "findings") {
      return (
        <FindingsPage
          approved={approved}
          setApproved={
            setApproved
          }
        />
      );
    }

    if (page === "recovery") {
      return (
        <RecoveryPage
          approved={approved}
        />
      );
    }

    if (page === "upload") {
      return <UploadPage />;
    }

    return (
      <Dashboard
        setPage={setPage}
      />
    );
  }

  return (
    <div className="app-layout">

      <Sidebar
        page={page}
        setPage={setPage}
        mobileOpen={mobileOpen}
        setMobileOpen={
          setMobileOpen
        }
        onLogout={onLogout}
        user={user}
      />

      <main className="main-area">

        <Navbar
          page={page}
          setMobileOpen={
            setMobileOpen
          }
          user={user}
        />

        {renderPage()}

      </main>

    </div>
  );
}


/* =========================================================
   ROOT APP
========================================================= */

export default function App() {

  const [route, setRoute] =
    useState("login");

  const [user, setUser] =
    useState(null);

  function handleLogin(userData) {
    setUser(userData);
    setRoute("dashboard");
  }

  function handleSignup(userData) {
    setUser(userData);
    setRoute("dashboard");
  }

  function handleLogout() {
    setUser(null);
    setRoute("login");
  }

  if (route === "dashboard") {
    return (
      <DashboardApp
        user={user}
        onLogout={handleLogout}
      />
    );
  }

  if (route === "signup") {
    return (
      <SignupPage
        onSignup={handleSignup}
        goLogin={() =>
          setRoute("login")
        }
      />
    );
  }

  return (
    <LoginPage
      onLogin={handleLogin}
      goSignup={() =>
        setRoute("signup")
      }
    />
  );
}