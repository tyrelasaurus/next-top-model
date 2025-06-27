'use client';

import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Team, Game, Player, League, SearchFilters } from '@/types/sports';
import { apiClient } from '@/lib/api';

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
    { id: 'teams' as const, label: 'Teams', icon: '🏟️' },
    { id: 'games' as const, label: 'Games', icon: '🏈' }, 
    { id: 'players' as const, label: 'Players', icon: '👤' }
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Data Explorer</h1>
        <p className="text-gray-600 dark:text-gray-400">
          Search and filter sports data across all leagues and seasons
        </p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 dark:border-gray-700 mb-6">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center gap-2 ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
              }`}
            >
              <span>{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Filters */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                League
              </label>
              <select 
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                value={filters.league || ''}
                onChange={(e) => setFilters({...filters, league: e.target.value as League || undefined})}
              >
                <option value="">All Leagues</option>
                <option value={League.NFL}>NFL</option>
                <option value={League.CFL}>CFL</option>
                <option value={League.NCAA}>NCAA</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Season
              </label>
              <select 
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
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
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Search
              </label>
              <input
                type="text"
                placeholder="Team name, city, player..."
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                value={filters.search_text || ''}
                onChange={(e) => setFilters({...filters, search_text: e.target.value || undefined})}
              />
            </div>

            <div className="flex items-end">
              <Button 
                onClick={() => activeTab === 'teams' && loadTeams()}
                className="w-full"
              >
                Apply Filters
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Content */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Results</span>
            {activeTab === 'teams' && (
              <span className="text-sm font-normal text-gray-500">
                {teams.length} teams found
              </span>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading && (
            <div className="text-center py-8">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p className="mt-2 text-gray-600 dark:text-gray-400">Loading...</p>
            </div>
          )}

          {error && (
            <div className="text-center py-8">
              <div className="text-red-600 dark:text-red-400 mb-2">⚠️ Error</div>
              <p className="text-gray-600 dark:text-gray-400">{error}</p>
              <Button 
                variant="outline" 
                size="sm" 
                className="mt-4"
                onClick={() => activeTab === 'teams' && loadTeams()}
              >
                Retry
              </Button>
            </div>
          )}

          {!loading && !error && (
            <div>
              {activeTab === 'teams' && (
                <TeamsTable teams={teams} />
              )}
              
              {activeTab === 'games' && (
                <div className="text-center py-8 text-gray-500">
                  Games data coming soon...
                </div>
              )}
              
              {activeTab === 'players' && (
                <div className="text-center py-8 text-gray-500">
                  Players data coming soon...
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function TeamsTable({ teams }: { teams: Team[] }) {
  if (teams.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No teams found. Try adjusting your filters.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
        <thead className="bg-gray-50 dark:bg-gray-800">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Team
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              League
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              City
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Stadium
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Conference/Division
            </th>
          </tr>
        </thead>
        <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
          {teams.map((team) => (
            <tr key={team.team_uid} className="hover:bg-gray-50 dark:hover:bg-gray-800">
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="flex items-center">
                  <div>
                    <div className="text-sm font-medium text-gray-900 dark:text-white">
                      {team.name}
                    </div>
                    {team.abbreviation && (
                      <div className="text-sm text-gray-500 dark:text-gray-400">
                        {team.abbreviation}
                      </div>
                    )}
                  </div>
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                  {team.league}
                </span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                {team.city}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                <div>
                  {team.stadium_name || 'N/A'}
                  {team.stadium_capacity && (
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      Capacity: {team.stadium_capacity.toLocaleString()}
                    </div>
                  )}
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                <div>
                  {team.conference && (
                    <div>{team.conference}</div>
                  )}
                  {team.division && (
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      {team.division}
                    </div>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}