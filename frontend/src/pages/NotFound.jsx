import { Link } from 'react-router-dom';

export default function NotFound() {
  return (
    <div className="min-h-screen bg-[#831843] flex items-center justify-center px-4 pt-16">
      <div className="text-center">
        <div className="text-8xl mb-6">🛡️</div>
        <h1 className="text-6xl font-bold text-white mb-4">404</h1>
        <p className="text-pink-200 text-xl mb-8">This page doesn't exist -- but safe connections do.</p>
        <Link
          to="/"
          className="px-8 py-3 rounded-full font-semibold text-[#BE185D] bg-white hover:bg-[#FCE7F3] transition-all shadow-lg"
        >
          Back to Home
        </Link>
      </div>
    </div>
  );
}
