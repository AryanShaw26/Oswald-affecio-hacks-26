import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import useAuth from '../hooks/useAuth';

const UNAUTH_LINKS = [
  { to: '/', label: 'Home' },
  { to: '/discover', label: 'Discover' },
  { to: '/login', label: 'Sign In' },
];

const AUTH_LINKS = [
  { to: '/', label: 'Home' },
  { to: '/discover', label: 'Discover' },
  { to: '/chat', label: 'Chat' },
  { to: '/privacy-alerts', label: 'Privacy Alerts' },
];

export default function Navbar() {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);
  const { user, isAuthenticated, logout } = useAuth();

  const links = isAuthenticated ? AUTH_LINKS : UNAUTH_LINKS;

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="fixed top-0 inset-x-0 z-50 bg-[#831843]/95 backdrop-blur-sm shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2">
            <span className="text-2xl">🛡️</span>
            <span className="text-white font-bold text-xl tracking-tight">
              TrustMatch<span className="text-[#FCE7F3] font-light"> AI</span>
            </span>
          </Link>

          {/* Desktop Nav */}
          <div className="hidden md:flex items-center gap-6">
            {links.map(({ to, label }) => (
              <Link
                key={to}
                to={to}
                className={`text-sm font-medium transition-colors ${
                  pathname === to
                    ? 'text-[#FCE7F3] border-b-2 border-[#E11D48] pb-0.5'
                    : 'text-pink-200 hover:text-white'
                }`}
              >
                {label}
              </Link>
            ))}
            {isAuthenticated ? (
              <button
                onClick={handleLogout}
                className="text-sm font-medium text-pink-200 hover:text-white transition-colors"
              >
                Log Out
              </button>
            ) : (
              <Link
                to="/register"
                className="ml-2 px-4 py-2 rounded-full text-sm font-semibold bg-gradient-to-r from-[#BE185D] to-[#E11D48] text-white hover:brightness-110 active:scale-95 transition-all"
              >
                Get Started
              </Link>
            )}
          </div>

          {/* Mobile hamburger */}
          <button
            className="md:hidden text-pink-200 hover:text-white p-2 rounded-lg"
            onClick={() => setMenuOpen(!menuOpen)}
            aria-label="Toggle navigation menu"
          >
            {menuOpen ? '✕' : '☰'}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div className="md:hidden bg-[#831843] border-t border-pink-800 px-4 pb-4 flex flex-col gap-3">
          {links.map(({ to, label }) => (
            <Link
              key={to}
              to={to}
              onClick={() => setMenuOpen(false)}
              className={`text-sm font-medium py-2 ${
                pathname === to ? 'text-[#FCE7F3] border-b border-pink-700 pb-1' : 'text-pink-200 hover:text-white'
              }`}
            >
              {label}
            </Link>
          ))}
          {isAuthenticated ? (
            <button
              onClick={() => { handleLogout(); setMenuOpen(false); }}
              className="text-left text-sm font-medium py-2 text-pink-200 hover:text-white"
            >
              Log Out
            </button>
          ) : (
            <Link
              to="/register"
              onClick={() => setMenuOpen(false)}
              className="px-4 py-2 rounded-full text-sm font-semibold text-center bg-gradient-to-r from-[#BE185D] to-[#E11D48] text-white"
            >
              Get Started
            </Link>
          )}
        </div>
      )}
    </nav>
  );
}

