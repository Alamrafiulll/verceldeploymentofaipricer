import { Link, useLocation } from 'react-router-dom';

const items = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/products', label: 'Products' },
  { to: '/pricing', label: 'Pricing' },
];

export default function Navbar() {
  const location = useLocation();

  return (
    <div className="mb-5 rounded-xl border border-slate-200 bg-white p-3 shadow-card">
      <div className="flex flex-wrap items-center gap-2">
        <p className="mr-3 text-sm font-semibold text-slate-700">AI Pricing System</p>
        {items.map((item) => {
          const active = location.pathname === item.to;
          return (
            <Link
              key={item.to}
              to={item.to}
              className={`rounded-lg px-3 py-1.5 text-sm ${
                active ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              {item.label}
            </Link>
          );
        })}
      </div>
    </div>
  );
}
