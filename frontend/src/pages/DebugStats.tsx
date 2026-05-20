import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Loader2 } from 'lucide-react';

import PaperFrame from '@/design/PaperFrame';
import Masthead from '@/design/atoms/Masthead';
import RuleDouble from '@/design/atoms/RuleDouble';
import { INK, INK_SOFT, OXBLOOD, PAPER, RULE, typeScale, space } from '@/design/tokens';

import { llmStatsDebugStatsGet } from '@/client';

interface PurposeStat {
  calls: number;
  p50_ms: number;
  p90_ms: number;
  total_in_tokens: number;
  total_out_tokens: number;
  total_cost_usd: number;
}

interface StatsPayload {
  rows: number;
  today_calls: number;
  today_cost_usd: number;
  today_in_tokens: number;
  today_out_tokens: number;
  all_time_cost_usd: number;
  by_purpose: Record<string, PurposeStat>;
  error?: string;
}

const cell: React.CSSProperties = {
  fontFamily: "'EB Garamond', serif",
  fontSize: typeScale.body,
  color: INK,
  padding: '8px 12px',
  borderBottom: `1px solid ${RULE}`,
  whiteSpace: 'nowrap' as const,
};

const headerCell: React.CSSProperties = {
  ...cell,
  fontFamily: "'Cormorant Garamond', serif",
  fontSize: typeScale.label,
  letterSpacing: 2,
  textTransform: 'uppercase' as const,
  color: INK_SOFT,
  borderBottom: `1px solid ${INK}`,
};

const statBlock: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column' as const,
  gap: 4,
  padding: '16px 20px',
  border: `1px solid ${RULE}`,
};

const statLabel: React.CSSProperties = {
  fontFamily: "'Cormorant Garamond', serif",
  fontSize: typeScale.micro,
  letterSpacing: 2,
  textTransform: 'uppercase' as const,
  color: INK_SOFT,
};

const statValue: React.CSSProperties = {
  fontFamily: "'Cormorant Garamond', serif",
  fontSize: typeScale.h1,
  color: INK,
  letterSpacing: -0.5,
};

const DebugStats: React.FC = () => {
  const [stats, setStats] = useState<StatsPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    llmStatsDebugStatsGet()
      .then((res) => {
        setStats((res.data as unknown as StatsPayload) ?? null);
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Failed to load stats');
      })
      .finally(() => setLoading(false));
  }, []);

  const purposes = stats?.by_purpose ? Object.entries(stats.by_purpose) : [];

  return (
    <PaperFrame>
      <Masthead dateline="LLM call telemetry" />
      <div style={{ padding: `0 0 ${space.xs}` }}>
        <RuleDouble color={INK} opacity={0.45} />
      </div>

      <div style={{ padding: `${space.sm} 0 ${space.xl}`, maxWidth: 960, margin: '0 auto' }}>
        <div style={{ marginBottom: 20 }}>
          <Link
            to="/preferences"
            style={{
              fontFamily: "'EB Garamond', serif",
              fontStyle: 'italic',
              fontSize: typeScale.body,
              color: INK_SOFT,
              textDecoration: 'none',
            }}
          >
            ← Back to the editor's desk
          </Link>
        </div>

        {loading && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '40px 0' }}>
            <Loader2 size={20} strokeWidth={1.5} className="animate-spin" style={{ color: INK_SOFT }} />
            <span style={{ fontFamily: "'EB Garamond', serif", fontStyle: 'italic', fontSize: typeScale.body, color: INK_SOFT }}>
              Reading the ledger…
            </span>
          </div>
        )}

        {error && (
          <div style={{ fontFamily: "'EB Garamond', serif", fontSize: typeScale.body, color: OXBLOOD, padding: '6px 10px', border: `1px solid ${OXBLOOD}` }}>
            {error}
          </div>
        )}

        {stats?.error && (
          <div style={{ fontFamily: "'EB Garamond', serif", fontStyle: 'italic', fontSize: typeScale.body, color: INK_SOFT }}>
            {stats.error}
          </div>
        )}

        {stats && !stats.error && (
          <>
            {/* Summary strip */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 32 }}>
              <div style={statBlock}>
                <span style={statLabel}>Total calls (all time)</span>
                <span style={statValue}>{stats.rows.toLocaleString()}</span>
              </div>
              <div style={statBlock}>
                <span style={statLabel}>Calls today</span>
                <span style={statValue}>{stats.today_calls.toLocaleString()}</span>
              </div>
              <div style={statBlock}>
                <span style={statLabel}>All-time cost</span>
                <span style={statValue}>${stats.all_time_cost_usd.toFixed(4)}</span>
              </div>
              <div style={statBlock}>
                <span style={statLabel}>Today — input tokens</span>
                <span style={statValue}>{stats.today_in_tokens.toLocaleString()}</span>
              </div>
              <div style={statBlock}>
                <span style={statLabel}>Today — output tokens</span>
                <span style={statValue}>{stats.today_out_tokens.toLocaleString()}</span>
              </div>
              <div style={statBlock}>
                <span style={statLabel}>Today — cost</span>
                <span style={statValue}>${stats.today_cost_usd.toFixed(4)}</span>
              </div>
            </div>

            {/* Per-purpose breakdown */}
            {purposes.length > 0 && (
              <>
                <div
                  style={{
                    fontFamily: "'Cormorant Garamond', serif",
                    fontStyle: 'italic',
                    fontSize: typeScale.micro,
                    letterSpacing: 3,
                    textTransform: 'uppercase',
                    color: OXBLOOD,
                    marginBottom: 12,
                  }}
                >
                  By purpose
                </div>
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', background: PAPER }}>
                    <thead>
                      <tr>
                        {['Purpose', 'Calls', 'P50 ms', 'P90 ms', 'In tokens', 'Out tokens', 'Cost (USD)'].map((h) => (
                          <th key={h} style={{ ...headerCell, textAlign: 'left' as const }}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {purposes.map(([purpose, s]) => (
                        <tr key={purpose}>
                          <td style={cell}>{purpose}</td>
                          <td style={{ ...cell, color: INK_SOFT }}>{s.calls.toLocaleString()}</td>
                          <td style={{ ...cell, color: INK_SOFT }}>{s.p50_ms.toLocaleString()}</td>
                          <td style={{ ...cell, color: INK_SOFT }}>{s.p90_ms.toLocaleString()}</td>
                          <td style={{ ...cell, color: INK_SOFT }}>{s.total_in_tokens.toLocaleString()}</td>
                          <td style={{ ...cell, color: INK_SOFT }}>{s.total_out_tokens.toLocaleString()}</td>
                          <td style={{ ...cell, color: INK_SOFT }}>${s.total_cost_usd.toFixed(4)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}
          </>
        )}
      </div>
    </PaperFrame>
  );
};

export default DebugStats;
