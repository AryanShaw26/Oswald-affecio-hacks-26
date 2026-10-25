import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import ProfileCard from '../components/ProfileCard';
import { createConnectionRequest, getDiscoverProfiles } from '../services/api';
import useAuth from '../hooks/useAuth';

const FILTER_LEVELS = ['All', 'High Trust (80+)', 'Verified Only'];

export default function Discover() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [profiles, setProfiles] = useState([]);
  const [filter, setFilter] = useState('All');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [connectingId, setConnectingId] = useState(null);

  useEffect(() => {
    const loadProfiles = async () => {
      setLoading(true);
      setError('');
      try {
        const data = await getDiscoverProfiles();
        setProfiles(data);
      } catch (err) {
        setError('Unable to load profiles right now. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    loadProfiles();
  }, []);

  const filtered = profiles.filter((profile) => {
    const score = profile.trust_score ?? 0;
    if (filter === 'High Trust (80+)') return score >= 80;
    if (filter === 'Verified Only') return score >= 80 || profile.completion_percentage >= 80;
    return true;
  });

  const handleConnect = async (targetUserId) => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    setConnectingId(targetUserId);
    try {
      const result = await createConnectionRequest(targetUserId);
      const nextProfiles = profiles.map((profile) =>
        profile.user_id === targetUserId ? { ...profile, connection_status: result.status || 'pending' } : profile
      );
      setProfiles(nextProfiles);
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to send connection request.');
    } finally {
      setConnectingId(null);
    }
  };

  return (
    <div className="min-h-screen bg-[#FFF1F2] pt-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="text-3xl font-bold text-[#831843]">Discover</h1>
            <p className="text-[#9F7A89] text-sm mt-1">Every profile includes a live Trust Score.</p>
          </div>
          <div className="flex gap-2 flex-wrap">
            {FILTER_LEVELS.map((item) => (
              <button
                key={item}
                onClick={() => setFilter(item)}
                className={`px-4 py-2 rounded-full text-sm font-medium border transition-all ${
                  filter === item
                    ? 'bg-[#BE185D] border-[#BE185D] text-white'
                    : 'bg-white border-pink-200 text-[#9F7A89] hover:border-[#BE185D]'
                }`}
              >
                {item}
              </button>
            ))}
          </div>
        </div>

        {error && (
          <div className="mb-6 rounded-2xl border border-red-200 bg-red-50 text-red-700 px-4 py-3 text-sm">{error}</div>
        )}

        {loading ? (
          <div className="text-center text-[#9F7A89] py-20">Loading profiles...</div>
        ) : filtered.length === 0 ? (
          <div className="rounded-3xl border border-dashed border-pink-200 bg-white p-10 text-center">
            <p className="text-xl font-semibold text-[#831843]">No profiles available right now.</p>
            <p className="text-[#9F7A89] mt-2">Check back soon or update your profile to get discovered.</p>
          </div>
        ) : (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {filtered.map((profile) => (
              <ProfileCard
                key={profile.id}
                name={profile.name}
                age={profile.age}
                bio={profile.bio}
                interests={(profile.interests || []).map((interest) => interest.name || interest)}
                score={profile.trust_score ?? profile.completion_percentage ?? 0}
                verified={Boolean(profile.trust_score && profile.trust_score >= 80)}
                imageUrl={profile.profile_picture}
                onConnect={() => handleConnect(profile.user_id)}
                onView={() => navigate(`/profile/${profile.id}`)}
                connectionStatus={profile.connection_status || 'not_connected'}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

