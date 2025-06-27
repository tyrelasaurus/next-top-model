'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';

interface TeamRanking {
  rank: number;
  team: string;
  logo?: string;
  division: string;
  wins: number;
  losses: number;
  winPercentage: number;
  trend: 'up' | 'down' | 'stable';
  modelScore: number;
  performance: 'elite' | 'strong' | 'average' | 'weak';
}

interface TeamRankingsProps {
  title?: string;
  teams?: TeamRanking[];
  showTrend?: boolean;
}

const mockTeams: TeamRanking[] = [
  {
    rank: 1,
    team: "Kansas City Chiefs",
    division: "AFC West",
    wins: 49,
    losses: 12,
    winPercentage: 0.803,
    trend: 'up',
    modelScore: 98.5,
    performance: 'elite'
  },
  {
    rank: 2,
    team: "Philadelphia Eagles",
    division: "NFC East",
    wins: 45,
    losses: 14,
    winPercentage: 0.763,
    trend: 'stable',
    modelScore: 94.2,
    performance: 'elite'
  },
  {
    rank: 3,
    team: "Buffalo Bills",
    division: "AFC East",
    wins: 41,
    losses: 16,
    winPercentage: 0.719,
    trend: 'up',
    modelScore: 91.8,
    performance: 'elite'
  },
  {
    rank: 4,
    team: "Detroit Lions",
    division: "NFC North",
    wins: 38,
    losses: 17,
    winPercentage: 0.691,
    trend: 'up',
    modelScore: 89.3,
    performance: 'strong'
  },
  {
    rank: 5,
    team: "Baltimore Ravens",
    division: "AFC North",
    wins: 37,
    losses: 19,
    winPercentage: 0.661,
    trend: 'down',
    modelScore: 86.7,
    performance: 'strong'
  }
];

const getRankBadge = (rank: number) => {
  if (rank === 1) return { bg: 'bg-gradient-to-r from-yellow-400 to-yellow-600', text: 'text-black', icon: '👑' };
  if (rank === 2) return { bg: 'bg-gradient-to-r from-gray-300 to-gray-500', text: 'text-black', icon: '🥈' };
  if (rank === 3) return { bg: 'bg-gradient-to-r from-orange-400 to-orange-600', text: 'text-white', icon: '🥉' };
  return { bg: 'bg-gradient-to-r from-purple-500 to-purple-700', text: 'text-white', icon: '⭐' };
};

const getPerformanceColor = (performance: string) => {
  switch (performance) {
    case 'elite': return 'text-yellow-400';
    case 'strong': return 'text-green-400';
    case 'average': return 'text-blue-400';
    case 'weak': return 'text-red-400';
    default: return 'text-gray-400';
  }
};

const getTrendIcon = (trend: string) => {
  switch (trend) {
    case 'up': return '📈';
    case 'down': return '📉';
    case 'stable': return '➡️';
    default: return '➡️';
  }
};

export function TeamRankings({ 
  title = "Elite Team Rankings", 
  teams = mockTeams, 
  showTrend = true 
}: TeamRankingsProps) {
  return (
    <Card className="bg-gradient-to-br from-gray-900/80 to-purple-900/40 border-purple-500/30">
      <CardHeader>
        <CardTitle className="text-2xl flex items-center gap-3">
          <span className="text-3xl">🏆</span>
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {teams.map((team) => {
            const rankBadge = getRankBadge(team.rank);
            return (
              <div 
                key={team.rank}
                className="group flex items-center gap-4 p-4 rounded-xl bg-gradient-to-r from-gray-800/50 to-purple-800/30 border border-purple-500/20 hover:border-primary/50 transition-all duration-300 hover:scale-[1.02]"
              >
                {/* Rank Badge */}
                <div className={`w-12 h-12 rounded-xl ${rankBadge.bg} ${rankBadge.text} flex items-center justify-center font-bold text-lg group-hover:scale-110 transition-transform`}>
                  <span className="text-xl">{rankBadge.icon}</span>
                </div>

                {/* Team Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-bold text-white text-lg truncate">{team.team}</h3>
                    {showTrend && (
                      <span className="text-sm">{getTrendIcon(team.trend)}</span>
                    )}
                  </div>
                  <p className="text-sm text-gray-400">{team.division}</p>
                </div>

                {/* Stats */}
                <div className="text-right space-y-1">
                  <div className="text-sm text-gray-300">
                    {team.wins}-{team.losses} ({(team.winPercentage * 100).toFixed(1)}%)
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-400">Model Score:</span>
                    <span className={`font-bold ${getPerformanceColor(team.performance)}`}>
                      {team.modelScore}
                    </span>
                  </div>
                </div>

                {/* Performance Badge */}
                <div className={`px-3 py-1 rounded-full text-xs font-semibold ${getPerformanceColor(team.performance)} bg-current bg-opacity-10 border border-current border-opacity-30`}>
                  {team.performance.toUpperCase()}
                </div>
              </div>
            );
          })}
        </div>

        <div className="mt-6 pt-4 border-t border-purple-500/20">
          <div className="flex items-center justify-between text-sm text-gray-400">
            <span>Updated: {new Date().toLocaleDateString()}</span>
            <span>Model Accuracy: 94.2%</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}