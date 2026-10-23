import SafetyAlert from './SafetyAlert';

/**
 * SafetyAnalysisDisplay -- visualises the result of the V4 Conversation
 * Safety analysis endpoint (`/safety/analyze`).
 *
 * Props:
 *   result  { risk_level, categories, flagged, summary, recommendation } | null
 */
const riskLevelMap = {
  low: 'safe',
  moderate: 'caution',
  high: 'risk',
};

export default function SafetyAnalysisDisplay({ result }) {
  if (!result) return null;

  const level = riskLevelMap[result.risk_level] || 'safe';

  return (
    <div className="mb-4">
      <SafetyAlert
        level={level}
        message={
          result.flagged
            ? `Potential safety concern detected (${result.risk_level})`
            : 'Message cleared by safety analysis'
        }
        detectedTypes={result.categories}
        recommendation={result.recommendation}
      />

      {result.summary && (
        <p className="text-xs text-[#9F7A89] mt-2 italic">“{result.summary}”</p>
      )}
    </div>
  );
}
