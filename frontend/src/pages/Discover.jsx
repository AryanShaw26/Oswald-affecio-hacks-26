import { useState } from 'react';
import ProfileCard from '../components/ProfileCard';

const MOCK_PROFILES = [
  { name: 'Aria', age: 26, bio: 'Coffee enthusiast, yoga practitioner, and passionate reader.', interests: ['Yoga', 'Books', 'Travel'], score: 92, verified: true },
  { name: 'Jordan', age: 29, bio: 'Product designer by day, amateur chef by night.', interests: ['Design', 'Cooking', 'Music'], score: 78, verified: false },
  { name: 'Priya', age: 24, bio: 'Software engineer who loves hiking and photography.', interests: ['Hiking', 'Photography', 'Tech'], score: 88, verified: true },
  { name: 'Marcus', age: 31, bio: 'Avid traveler. 40+ countries and counting.', interests: ['Travel', 'Languages', 'Food'], score: 65, verified: false },
  { name: 'Sofia', age: 27, bio: 'Musician and visual artist living in the city.', interests: ['Music', 'Art', 'Books'], score: 95, verified: true },
  { name: 'Leo', age: 28, bio: 'Personal trainer and nutrition coach.', interests: ['Fitness', 'Cooking', 'Nature'], score: 81, verified: true },
];

const FILTER_LEVELS = ['All', 'High Trust (80+)', 'Verified Only'];

export default function Discover() {
  const [filter, setFilter] = useState('All');

  const filtered = MOCK_PROFILES.filter((p) => {
    if (filter === 'High Trust (80+)') return p.score >= 80;
    if (filter === 'Verified Only') return p.verified;
    return true;
  });

  return (
    <div className="min-h-screen bg-[#FFF1F2] pt-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="text-3xl font-bold text-[#831843]">Discover</h1>
            <p className="text-[#9F7A89] text-sm mt-1">Every profile includes a live Trust Score.</p>
          </div>
          <div className="flex gap-2 flex-wrap">
            {FILTER_LEVELS.map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-4 py-2 rounded-full text-sm font-medium border transition-all ${
                  filter === f
                    ? 'bg-[#BE185D] border-[#BE185D] text-white'
                    : 'bg-white border-pink-200 text-[#9F7A89] hover:border-[#BE185D]'
                }`}
              >
                {f}
              </button>
            ))}
          </div>
        </div>

        {filtered.length === 0 ? (
          <p className="text-center text-[#9F7A89] py-20">No profiles match this filter.</p>
        ) : (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {filtered.map((p) => (
              <ProfileCard key={p.name} {...p} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

