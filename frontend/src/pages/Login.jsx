import { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import useAuth from '../hooks/useAuth';

export default function Login() {
  const [form, setForm] = useState({ email: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(form.email, form.password);
      // Redirect to the page the user was trying to reach, or /chat
      const from = location.state?.from?.pathname || '/chat';
      navigate(from, { replace: true });
    } catch (err) {
      const status = err.response?.status;
      if (status === 401) {
        setError('Invalid email or password.');
      } else if (status === 422) {
        setError('Please enter a valid email and password.');
      } else {
        setError('Unable to sign in. Please check your connection and try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#831843] flex items-center justify-center px-4 pt-16">
      <div className="w-full max-w-md bg-[#FFF1F2] rounded-3xl shadow-2xl p-8">
        <div className="text-center mb-8">
          <span className="text-4xl">🛡️</span>
          <h1 className="text-2xl font-bold text-[#831843] mt-2">Welcome back</h1>
          <p className="text-[#9F7A89] text-sm mt-1">Sign in to your TrustMatch account</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5" noValidate>
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-[#1F1720] mb-1">
              Email address
            </label>
            <input
              id="email"
              type="email"
              name="email"
              value={form.email}
              onChange={handleChange}
              required
              autoComplete="email"
              placeholder="you@example.com"
              className="w-full border border-pink-200 rounded-xl px-4 py-3 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-[#BE185D] transition"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-[#1F1720] mb-1">
              Password
            </label>
            <input
              id="password"
              type="password"
              name="password"
              value={form.password}
              onChange={handleChange}
              required
              autoComplete="current-password"
              placeholder="••••••••"
              className="w-full border border-pink-200 rounded-xl px-4 py-3 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-[#BE185D] transition"
            />
          </div>

          {error && (
            <p role="alert" className="text-sm text-[#DC2626] bg-red-50 rounded-xl px-4 py-2 border border-red-200">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-full font-semibold text-white bg-gradient-to-r from-[#BE185D] to-[#E11D48] hover:brightness-110 active:scale-95 transition-all disabled:opacity-60"
          >
            {loading ? 'Signing in…' : 'Sign In'}
          </button>
        </form>

        <p className="text-center text-sm text-[#9F7A89] mt-6">
          Don't have an account?{' '}
          <Link to="/register" className="text-[#BE185D] font-semibold hover:underline">
            Create one
          </Link>
        </p>
      </div>
    </div>
  );
}
