'use client';

import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Team, Game, Player, League, SearchFilters } from '@/types/sports';
import { apiClient } from '@/lib/api';
import { TeamRankings } from '@/components/charts/TeamRankings';

export default function ExplorePage() {
  const [activeTab, setActiveTab] = useState<'teams' | 'games' | 'players'>('teams');
  const [teams, setTeams] = useState<Team[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<SearchFilters>({});

  const loadTeams = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.getTeams({
        league: filters.league,
        city: filters.search_text,
        name: filters.search_text
      });
      setTeams(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load teams');
    } finally {
      setLoading(false);
    }
  }, [filters.league, filters.search_text]);

  useEffect(() => {
    if (activeTab === 'teams') {
      loadTeams();
    }
  }, [activeTab, filters, loadTeams]);

  const tabs = [
    { id: 'teams' as const, label: 'Team Rankings', icon: '🏆', gradient: 'from-yellow-400 to-orange-500' },
    { id: 'games' as const, label: 'Performance Analytics', icon: '📊', gradient: 'from-primary to-secondary' }, 
    { id: 'players' as const, label: 'Talent Scouting', icon: '⭐', gradient: 'from-emerald-400 to-teal-500' }
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-10 text-center">
        <div className="inline-flex items-center gap-3 bg-gradient-to-r from-primary/20 to-secondary/20 rounded-full px-6 py-2 mb-4 border border-primary/30">
          <span className="text-2xl">⭐</span>
          <span className="text-sm font-semibold text-primary">Model Rankings Hub</span>
        </div>
        <h1 className="text-5xl font-bold mb-4">
          <span className="bg-gradient-to-r from-white via-primary to-secondary bg-clip-text text-transparent">
            Elite Talent Discovery
          </span>
        </h1>
        <p className="text-xl text-gray-300 max-w-3xl mx-auto leading-relaxed">
          Explore comprehensive rankings, performance analytics, and scouting insights powered by advanced AI modeling.
        </p>
      </div>

      {/* Tabs */}
      <div className="mb-8">
        <nav className="flex flex-wrap gap-4 justify-center">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`group flex items-center gap-3 px-6 py-4 rounded-xl font-semibold transition-all duration-300 border ${
                activeTab === tab.id
                  ? 'bg-gradient-to-r from-primary/20 to-secondary/20 border-primary/50 text-white shadow-lg shadow-primary/25'
                  : 'bg-gray-800/50 border-gray-600/30 text-gray-300 hover:bg-purple-800/30 hover:border-purple-500/30 hover:text-white'
              }`}
            >
              <div className={`w-10 h-10 bg-gradient-to-br ${tab.gradient} rounded-lg flex items-center justify-center text-white text-xl group-hover:scale-110 transition-transform`}>
                {tab.icon}
              </div>
              <span>{tab.label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Filters */}
      <Card className="mb-8 bg-gradient-to-br from-gray-900/80 to-purple-900/40 border-purple-500/30">
        <CardHeader>
          <CardTitle className="flex items-center gap-3">
            <span className="text-2xl">🎯</span>
            Elite Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div>
              <label className="block text-sm font-semibold text-white mb-3">
                League
              </label>
              <select 
                className="w-full px-4 py-3 border border-purple-500/30 rounded-xl bg-gray-800/60 text-white focus:border-primary/50 focus:ring-2 focus:ring-primary/25 transition-all"
                value={filters.league || ''}
                onChange={(e) => setFilters({...filters, league: e.target.value as League || undefined})}
              >
                <option value="">All Leagues</option>
                <option value={League.NFL}>🏈 NFL</option>
                <option value={League.CFL}>🍁 CFL</option>
                <option value={League.NCAA}>🎓 NCAA</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-semibold text-white mb-3">
                Season
              </label>
              <select 
                className="w-full px-4 py-3 border border-purple-500/30 rounded-xl bg-gray-800/60 text-white focus:border-primary/50 focus:ring-2 focus:ring-primary/25 transition-all"
                value={filters.season || ''}
                onChange={(e) => setFilters({...filters, season: e.target.value ? parseInt(e.target.value) : undefined})}
              >
                <option value="">All Seasons</option>
                {Array.from({length: 10}, (_, i) => 2024 - i).map(year => (
                  <option key={year} value={year}>{year}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-semibold text-white mb-3">
                Search
              </label>
              <input
                type="text"
                placeholder="Team, player, or keyword..."
                className="w-full px-4 py-3 border border-purple-500/30 rounded-xl bg-gray-800/60 text-white placeholder-gray-400 focus:border-primary/50 focus:ring-2 focus:ring-primary/25 transition-all"
                value={filters.search_text || ''}
                onChange={(e) => setFilters({...filters, search_text: e.target.value || undefined})}
              />
            </div>

            <div className="flex items-end">
              <Button 
                onClick={() => activeTab === 'teams' && loadTeams()}
                className="w-full bg-gradient-to-r from-primary to-secondary hover:from-primary/80 hover:to-secondary/80 font-semibold py-3 rounded-xl transition-all duration-300 shadow-lg shadow-primary/25"
              >
                🔍 Analyze
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Content */}
      <div className="grid lg:grid-cols-3 gap-8">
        {/* Main Content */}
        <div className="lg:col-span-2">
          <Card className="bg-gradient-to-br from-gray-900/80 to-purple-900/40 border-purple-500/30">
            <CardHeader>
              <CardTitle className="flex items-center justify-between text-2xl">
                <span className="flex items-center gap-3">
                  <span className="text-3xl">📈</span>
                  {activeTab === 'teams' ? 'Team Performance Matrix' : 
                   activeTab === 'games' ? 'Performance Analytics' : 'Talent Scouting Results'}
                </span>
                {activeTab === 'teams' && (
                  <span className="text-sm font-normal text-gray-400 bg-purple-800/30 px-3 py-1 rounded-full">
                    {teams.length} teams analyzed
                  </span>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading && (
                <div className="text-center py-12">
                  <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-primary border-t-transparent"></div>
                  <p className="mt-4 text-lg text-gray-300">Analyzing elite performance data...</p>
                </div>
              )}

              {error && (
                <div className="text-center py-12">
                  <div className="text-6xl mb-4">⚠️</div>
                  <div className="text-red-400 mb-2 text-xl font-semibold">Analysis Error</div>
                  <p className="text-gray-400 mb-6">{error}</p>
                  <Button 
                    onClick={() => activeTab === 'teams' && loadTeams()}
                    className="bg-gradient-to-r from-red-500 to-red-600 hover:from-red-400 hover:to-red-500 font-semibold px-6 py-3 rounded-xl"
                  >
                    🔄 Retry Analysis
                  </Button>
                </div>
              )}

              {!loading && !error && (
                <div>
                  {activeTab === 'teams' && (
                    <EliteTeamsView teams={teams} />
                  )}
                  
                  {activeTab === 'games' && (
                    <div className="text-center py-12">
                      <div className="text-6xl mb-4">🔜</div>
                      <div className="text-xl font-semibold text-white mb-2">Performance Analytics Coming Soon</div>
                      <p className="text-gray-400">Advanced game-by-game performance insights and predictive modeling</p>
                    </div>
                  )}
                  
                  {activeTab === 'players' && (
                    <div className="text-center py-12">
                      <div className="text-6xl mb-4">🎯</div>
                      <div className="text-xl font-semibold text-white mb-2">Talent Scouting Portal Coming Soon</div>
                      <p className="text-gray-400">Comprehensive player analytics, draft projections, and performance metrics</p>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <TeamRankings />
          
          <Card className="bg-gradient-to-br from-gray-900/80 to-purple-900/40 border-purple-500/30">
            <CardHeader>
              <CardTitle className="flex items-center gap-3">
                <span className="text-2xl">🎯</span>
                Elite Insights
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="p-4 bg-gradient-to-r from-yellow-400/10 to-orange-500/10 rounded-lg border border-yellow-400/20">
                <h4 className="font-semibold text-yellow-400 mb-2">🏆 Top Performer</h4>
                <p className="text-sm text-gray-300">Kansas City Chiefs lead with 98.5 model score</p>
              </div>
              
              <div className="p-4 bg-gradient-to-r from-green-400/10 to-emerald-500/10 rounded-lg border border-green-400/20">
                <h4 className="font-semibold text-green-400 mb-2">📈 Rising Star</h4>
                <p className="text-sm text-gray-300">Detroit Lions showing +15% performance gain</p>
              </div>
              
              <div className="p-4 bg-gradient-to-r from-blue-400/10 to-purple-500/10 rounded-lg border border-blue-400/20">
                <h4 className="font-semibold text-blue-400 mb-2">🔍 Key Metric</h4>
                <p className="text-sm text-gray-300">94.2% prediction accuracy achieved</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

function EliteTeamsView({ teams }: { teams: Team[] }) {
  if (teams.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-6xl mb-4">🔍</div>
        <div className="text-xl font-semibold text-white mb-2">No Elite Teams Found</div>
        <p className="text-gray-400">Adjust your filters to discover top-performing teams</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {teams.map((team, index) => {
        // Generate mock performance data based on team characteristics
        const mockScore = 75 + Math.random() * 20;
        const mockRank = index + 1;
        const performance = mockScore > 90 ? 'elite' : mockScore > 80 ? 'strong' : mockScore > 70 ? 'average' : 'developing';
        const trend = Math.random() > 0.5 ? 'up' : Math.random() > 0.3 ? 'stable' : 'down';
        
        return (
          <div 
            key={team.team_uid}
            className="group p-6 rounded-xl bg-gradient-to-r from-gray-800/50 to-purple-800/30 border border-purple-500/20 hover:border-primary/50 transition-all duration-300 hover:scale-[1.02]"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                {/* Rank Badge */}
                <div className="w-12 h-12 bg-gradient-to-br from-primary to-secondary rounded-xl flex items-center justify-center text-white font-bold text-lg group-hover:scale-110 transition-transform">
                  #{mockRank}
                </div>
                
                {/* Team Info */}
                <div>
                  <h3 className="text-xl font-bold text-white mb-1">{team.name}</h3>
                  <div className="flex items-center gap-3 text-sm">
                    <span className="bg-gradient-to-r from-primary/20 to-secondary/20 text-primary px-2 py-1 rounded-full font-semibold">
                      {team.league}
                    </span>
                    <span className="text-gray-400">{team.city}</span>
                    {team.division && (
                      <span className="text-gray-400">• {team.division}</span>
                    )}
                  </div>
                </div>
              </div>
              
              {/* Performance Metrics */}
              <div className="text-right space-y-2">
                <div className="flex items-center gap-4">
                  <div>
                    <div className="text-sm text-gray-400">Model Score</div>
                    <div className={`text-2xl font-bold ${
                      performance === 'elite' ? 'text-yellow-400' :
                      performance === 'strong' ? 'text-green-400' :
                      performance === 'average' ? 'text-blue-400' : 'text-purple-400'
                    }`}>
                      {mockScore.toFixed(1)}
                    </div>
                  </div>
                  
                  <div>
                    <div className="text-sm text-gray-400">Trend</div>
                    <div className="text-xl">
                      {trend === 'up' ? '📈' : trend === 'down' ? '📉' : '➡️'}
                    </div>
                  </div>
                  
                  <div className={`px-3 py-1 rounded-full text-xs font-semibold ${
                    performance === 'elite' ? 'text-yellow-400 bg-yellow-400/10 border border-yellow-400/30' :
                    performance === 'strong' ? 'text-green-400 bg-green-400/10 border border-green-400/30' :
                    performance === 'average' ? 'text-blue-400 bg-blue-400/10 border border-blue-400/30' :
                    'text-purple-400 bg-purple-400/10 border border-purple-400/30'
                  }`}>
                    {performance.toUpperCase()}
                  </div>
                </div>
              </div>
            </div>
            
            {/* Stadium Info */}
            {team.stadium_name && (
              <div className="mt-4 pt-4 border-t border-purple-500/20">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-400">
                    🏟️ {team.stadium_name}
                    {team.stadium_capacity && (
                      <span className="ml-2">• Capacity: {team.stadium_capacity.toLocaleString()}</span>
                    )}
                  </span>
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    className="text-primary hover:text-white hover:bg-primary/20 transition-all duration-300"
                  >
                    View Details →
                  </Button>
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}