import { Link } from 'react-router-dom';
import { useState, useEffect } from 'react';
import api from '../services/api';
import SafetyAlert from '../components/SafetyAlert';
import TrustScoreCard from '../components/TrustScoreCard';
import ProfileCard from '../components/ProfileCard';

const FEATURE_CARDS = [
  {
    icon: '🛡️',
    title: 'Trust Score AI',
    desc: 'Every profile receives a 0-100 trust rating based on behavioral signals and verification.',
  },
  {
    icon: '🔒',
    title: 'Privacy Guardian',
    desc: "Real-time detection of sensitive information shared in conversations \u2014 before it's too late.",
  },
  {
    icon: '✅',
    title: 'Identity Verified',
    desc: "Multi-step verification gives you confidence in who you're connecting with.",
  },
  {
    icon: '🚨',
    title: 'Safety Center',
    desc: 'Report, block, and access safety resources -- always one tap away, never hidden.',
  },
];

const MOCK_PROFILES = [
  { name: 'Aria', age: 26, bio: 'Coffee enthusiast, yoga practitioner, and passionate reader.', interests: ['Yoga', 'Books', 'Travel'], score: 92, verified: true },
  { name: 'Jordan', age: 29, bio: 'Product designer by day, amateur chef by night.', interests: ['Design', 'Cooking', 'Music'], score: 78, verified: false },
  { name: 'Priya', age: 24, bio: 'Software engineer who loves hiking and photography.', interests: ['Hiking', 'Photography', 'Tech'], score: 88, verified: true },
];

export default function Home() {
  const [apiStatus, setApiStatus] = useState(null);
  const [checking, setChecking] = useState(false);

  const checkHealth = async () => {
    setChecking(true);
    try {
      const res = await api.get('/health');
      setApiStatus({ ok: true, data: res.data });
    } catch {
      setApiStatus({ ok: false });
    } finally {
      setChecking(false);
    }
  };

  return (
    <div className="min-h-screen">
      {/* ── Hero Section ─────────────────────────────────────── */}
      <section className="relative bg-gradient-to-br from-[#831843] via-[#BE185D] to-[#E11D48] min-h-screen flex items-center pt-16 overflow-hidden">
        {/* Ambient glow */}
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_rgba(252,231,243,0.15)_0%,_transparent_70%)] pointer-events-none" />

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 flex flex-col items-center text-center gap-8">
          <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm border border-white/20 rounded-full px-4 py-2 text-pink-100 text-sm font-medium">
            <span>🛡️</span> Safety-first dating -- powered by AI
          </div>

          <h1 className="text-5xl md:text-7xl font-bold text-white max-w-4xl leading-tight">
            Connect with{' '}
            <span className="text-[#FCE7F3]">confidence</span>,
            <br />not uncertainty.
          </h1>

          <p className="text-pink-100 text-lg md:text-xl max-w-2xl leading-relaxed">
            TrustMatch AI uses advanced trust scoring and privacy protection to help you build
            genuine connections -- safely, confidently, and on your terms.
          </p>

          <div className="flex flex-col sm:flex-row gap-4">
            <Link
              to="/register"
              className="px-8 py-4 rounded-full font-semibold text-lg bg-white text-[#BE185D] hover:bg-[#FCE7F3] active:scale-95 transition-all shadow-lg"
            >
              Get Started
            </Link>
            <Link
              to="/discover"
              className="px-8 py-4 rounded-full font-semibold text-lg border-2 border-white/60 text-white hover:bg-white/10 transition-all"
            >
              Explore How It Works
            </Link>
          </div>

          {/* API health check */}
          <div className="w-full max-w-sm">
            <button
              onClick={checkHealth}
              disabled={checking}
              className="w-full py-2 rounded-full text-sm font-medium bg-white/10 border border-white/20 text-pink-100 hover:bg-white/20 transition-all disabled:opacity-50"
            >
              {checking ? 'Checking backend…' : '⚡ Check API Status'}
            </button>
            {apiStatus && (
              <div className="mt-2">
                <SafetyAlert
                  level={apiStatus.ok ? 'safe' : 'risk'}
                  message={
                    apiStatus.ok
                      ? `Backend online -- ${apiStatus.data?.service}`
                      : 'Backend unreachable -- start FastAPI on :8000'
                  }
                />
              </div>
            )}
          </div>
        </div>
      </section>

      {/* ── Feature Cards ────────────────────────────────────── */}
      <section className="py-20 px-4 bg-[#FFF1F2]">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl md:text-4xl font-bold text-center text-[#831843] mb-3">
            Romance with reassurance.
          </h2>
          <p className="text-center text-[#9F7A89] mb-12 max-w-xl mx-auto">
            Every feature is designed to keep you safe while helping you find meaningful connections.
          </p>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {FEATURE_CARDS.map((card) => (
              <div key={card.title} className="bg-white rounded-2xl p-6 shadow-sm hover:shadow-md hover:-translate-y-1 transition-all">
                <div className="text-3xl mb-3">{card.icon}</div>
                <h3 className="font-semibold text-[#1F1720] mb-2">{card.title}</h3>
                <p className="text-sm text-[#9F7A89] leading-relaxed">{card.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Discovery Preview ────────────────────────────────── */}
      <section className="py-20 px-4 bg-[#FCE7F3]">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl font-bold text-center text-[#831843] mb-3">
            Discover with Trust
          </h2>
          <p className="text-center text-[#9F7A89] mb-12">
            Every profile shows a live Trust Score so you always know who you're connecting with.
          </p>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
            {MOCK_PROFILES.map((p) => (
              <ProfileCard key={p.name} {...p} />
            ))}
          </div>
          <div className="text-center">
            <Link
              to="/discover"
              className="inline-block px-8 py-3 rounded-full font-semibold bg-gradient-to-r from-[#BE185D] to-[#E11D48] text-white hover:brightness-110 transition-all shadow-md"
            >
              See All Profiles
            </Link>
          </div>
        </div>
      </section>

      {/* ── Trust Score Demo ──────────────────────────────────── */}
      <section className="py-20 px-4 bg-white">
        <div className="max-w-7xl mx-auto flex flex-col lg:flex-row items-center gap-12">
          <div className="flex-1">
            <h2 className="text-3xl font-bold text-[#831843] mb-4">
              Your Safety, Scored.
            </h2>
            <p className="text-[#9F7A89] mb-6 leading-relaxed">
              Our AI Trust Engine analyzes behavioral patterns, verifies identity signals,
              and gives every user a transparent 0-100 Trust Score. Green means go.
            </p>
            <ul className="space-y-3">
              {['Behavioral pattern analysis', 'Multi-step identity verification', 'Real-time conversation monitoring', 'Privacy leak detection'].map((f) => (
                <li key={f} className="flex items-center gap-2 text-sm text-[#1F1720]">
                  <span className="text-[#16A34A] font-bold">✓</span> {f}
                </li>
              ))}
            </ul>
          </div>
          <div className="flex gap-6 flex-wrap justify-center">
            <TrustScoreCard score={92} riskLevel="safe" factors={['Identity verified', 'Consistent behavior', 'Privacy-respecting']} />
            <TrustScoreCard score={45} riskLevel="caution" factors={['Unverified identity', 'Flagged message pattern']} />
          </div>
        </div>
      </section>

      {/* ── Footer ───────────────────────────────────────────── */}
      <footer className="bg-[#831843] text-pink-200 py-10 px-4">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 text-sm">
          <div className="flex items-center gap-2 font-bold text-white text-lg">
            <span>🛡️</span> TrustMatch AI
          </div>
          <p>© 2026 TrustMatch AI. Building safer connections.</p>
          <div className="flex gap-4">
            <Link to="/safety" className="hover:text-white transition-colors">Safety</Link>
            <Link to="/login" className="hover:text-white transition-colors">Sign In</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
