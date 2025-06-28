'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { SimpleChart } from '@/components/charts/SimpleChart';
import { TeamRankings } from '@/components/charts/TeamRankings';

interface ETLJobStatus {
  id: string;
  name: string;
  status: 'running' | 'completed' | 'failed' | 'pending';
  startTime?: string;
  endTime?: string;
  recordsProcessed?: number;
  errorMessage?: string;
}

interface SystemMetrics {
  totalTeams: number;
  totalGames: number;
  totalPlayers: number;
  lastUpdate: string;
  dataQualityScore: number;
  apiHealth: 'healthy' | 'degraded' | 'down';
}

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<SystemMetrics>({
    totalTeams: 120,
    totalGames: 52847,
    totalPlayers: 25103,
    lastUpdate: '2024-01-15T08:30:00Z',
    dataQualityScore: 96.5,
    apiHealth: 'healthy'
  });

  const [jobs, setJobs] = useState<ETLJobStatus[]>([
    {
      id: '1',
      name: 'NFL Teams Sync',
      status: 'completed',
      startTime: '2024-01-15T08:00:00Z',
      endTime: '2024-01-15T08:15:00Z',
      recordsProcessed: 32
    },
    {
      id: '2', 
      name: 'NFL Games Delta Update',
      status: 'running',
      startTime: '2024-01-15T08:30:00Z',
      recordsProcessed: 156
    },
    {
      id: '3',
      name: 'CFL Player Stats',
      status: 'failed',
      startTime: '2024-01-15T07:45:00Z',
      endTime: '2024-01-15T07:47:00Z',
      errorMessage: 'API rate limit exceeded'
    },
    {
      id: '4',
      name: 'NCAA Weekly Sync',
      status: 'pending',
    }
  ]);

  const getStatusColor = (status: ETLJobStatus['status']) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'running': return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      case 'failed': return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      case 'pending': return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200';
    }
  };

  const getStatusIcon = (status: ETLJobStatus['status']) => {
    switch (status) {
      case 'completed': return '✅';
      case 'running': return '⏳';
      case 'failed': return '❌';
      case 'pending': return '⏸️';
    }
  };

  const formatDuration = (start: string, end?: string) => {
    const startTime = new Date(start);
    const endTime = end ? new Date(end) : new Date();
    const diffMs = endTime.getTime() - startTime.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffSecs = Math.floor((diffMs % (1000 * 60)) / 1000);
    return `${diffMins}m ${diffSecs}s`;
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-10 text-center">
        <div className="inline-flex items-center gap-3 bg-gradient-to-r from-primary/20 to-secondary/20 rounded-full px-6 py-2 mb-4 border border-primary/30">
          <span className="text-2xl">👑</span>
          <span className="text-sm font-semibold text-primary">Elite Dashboard</span>
        </div>
        <h1 className="text-5xl font-bold mb-4">
          <span className="bg-gradient-to-r from-white via-primary to-secondary bg-clip-text text-transparent">
            Performance Command Center
          </span>
        </h1>
        <p className="text-xl text-gray-300 max-w-3xl mx-auto leading-relaxed">
          Real-time analytics, model performance tracking, and elite talent insights at your fingertips.
        </p>
      </div>

      {/* Elite Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-10">
        <Card className="bg-gradient-to-br from-yellow-400/10 to-orange-500/10 border-yellow-400/30 group hover:border-yellow-400/50 transition-all duration-300">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-yellow-400 font-semibold mb-1">Elite Teams</p>
                <p className="text-3xl font-bold text-white mb-1">
                  {metrics.totalTeams}
                </p>
                <p className="text-xs text-gray-400">Franchises Analyzed</p>
              </div>
              <div className="text-4xl group-hover:scale-110 transition-transform">🏆</div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-green-400/10 to-emerald-500/10 border-green-400/30 group hover:border-green-400/50 transition-all duration-300">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-green-400 font-semibold mb-1">Performance Data</p>
                <p className="text-3xl font-bold text-white mb-1">
                  {(metrics.totalGames / 1000).toFixed(1)}K
                </p>
                <p className="text-xs text-gray-400">Games Analyzed</p>
              </div>
              <div className="text-4xl group-hover:scale-110 transition-transform">📈</div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-blue-400/10 to-purple-500/10 border-blue-400/30 group hover:border-blue-400/50 transition-all duration-300">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-blue-400 font-semibold mb-1">Talent Pool</p>
                <p className="text-3xl font-bold text-white mb-1">
                  {(metrics.totalPlayers / 1000).toFixed(1)}K
                </p>
                <p className="text-xs text-gray-400">Players Tracked</p>
              </div>
              <div className="text-4xl group-hover:scale-110 transition-transform">⭐</div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-400/10 to-pink-500/10 border-purple-400/30 group hover:border-purple-400/50 transition-all duration-300">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-purple-400 font-semibold mb-1">Model Accuracy</p>
                <p className="text-3xl font-bold text-white mb-1">
                  {metrics.dataQualityScore}%
                </p>
                <p className="text-xs text-gray-400">Prediction Rate</p>
              </div>
              <div className="text-4xl group-hover:scale-110 transition-transform">🎯</div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid lg:grid-cols-4 gap-8 mb-10">
        {/* Main Content Area */}
        <div className="lg:col-span-3 space-y-8">
          {/* System Status */}
          <div className="grid md:grid-cols-3 gap-6">
            <Card className="bg-gradient-to-br from-gray-900/80 to-purple-900/40 border-purple-500/30">
              <CardHeader>
                <CardTitle className="flex items-center gap-3">
                  <span className="text-2xl">🟢</span>
                  System Status
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-3 mb-3">
                  <div className={`w-4 h-4 rounded-full animate-pulse ${
                    metrics.apiHealth === 'healthy' ? 'bg-green-400' :
                    metrics.apiHealth === 'degraded' ? 'bg-yellow-400' : 'bg-red-400'
                  }`}></div>
                  <span className="capitalize font-semibold text-white">
                    {metrics.apiHealth === 'healthy' ? 'All Systems Operational' : metrics.apiHealth}
                  </span>
                </div>
                <p className="text-sm text-gray-400">
                  Elite performance tracking active
                </p>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-gray-900/80 to-purple-900/40 border-purple-500/30">
              <CardHeader>
                <CardTitle className="flex items-center gap-3">
                  <span className="text-2xl">🔄</span>
                  Last Analysis
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-lg font-semibold text-white">
                  {new Date(metrics.lastUpdate).toLocaleString()}
                </p>
                <p className="text-sm text-gray-400 mt-2">
                  Next update: Real-time
                </p>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-gray-900/80 to-purple-900/40 border-purple-500/30">
              <CardHeader>
                <CardTitle className="flex items-center gap-3">
                  <span className="text-2xl">⚡</span>
                  Quick Actions
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button className="w-full bg-gradient-to-r from-primary to-secondary hover:from-primary/80 hover:to-secondary/80 font-semibold transition-all duration-300">
                  🚀 Analyze Performance
                </Button>
                <Button variant="outline" className="w-full border-purple-500/30 text-purple-400 hover:bg-purple-500/10">
                  📊 Export Insights
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Performance Analytics */}
          <div className="grid md:grid-cols-2 gap-6">
            <Card className="bg-gradient-to-br from-gray-900/80 to-purple-900/40 border-purple-500/30">
              <CardHeader>
                <CardTitle className="flex items-center gap-3">
                  <span className="text-2xl">🏈</span>
                  League Distribution
                </CardTitle>
              </CardHeader>
              <CardContent>
                <SimpleChart 
                  type="pie"
                  data={[
                    { label: 'NFL', value: 32, color: '#A855F7' },
                    { label: 'CFL', value: 9, color: '#EC4899' },
                    { label: 'NCAA', value: 130, color: '#10B981' }
                  ]}
                  width={350}
                  height={250}
                />
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-gray-900/80 to-purple-900/40 border-purple-500/30">
              <CardHeader>
                <CardTitle className="flex items-center gap-3">
                  <span className="text-2xl">📈</span>
                  Model Performance Trend
                </CardTitle>
              </CardHeader>
              <CardContent>
                <SimpleChart 
                  type="line"
                  data={[
                    { label: 'Mon', value: 91.2 },
                    { label: 'Tue', value: 93.5 },
                    { label: 'Wed', value: 92.8 },
                    { label: 'Thu', value: 94.1 },
                    { label: 'Fri', value: 93.9 },
                    { label: 'Sat', value: 95.2 },
                    { label: 'Sun', value: 94.2 }
                  ]}
                  width={350}
                  height={250}
                />
              </CardContent>
            </Card>
          </div>

          {/* Analysis Pipeline Status */}
          <Card className="bg-gradient-to-br from-gray-900/80 to-purple-900/40 border-purple-500/30">
            <CardHeader>
              <CardTitle className="flex items-center justify-between text-2xl">
                <span className="flex items-center gap-3">
                  <span className="text-3xl">🔧</span>
                  Elite Analysis Pipeline
                </span>
                <Button className="bg-gradient-to-r from-primary to-secondary hover:from-primary/80 hover:to-secondary/80 font-semibold transition-all duration-300">
                  🔄 Refresh
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {jobs.map((job) => {
                  const statusColors = {
                    completed: 'from-green-400/20 to-emerald-500/20 border-green-400/40',
                    running: 'from-blue-400/20 to-purple-500/20 border-blue-400/40',
                    failed: 'from-red-400/20 to-pink-500/20 border-red-400/40',
                    pending: 'from-gray-400/20 to-gray-500/20 border-gray-400/40'
                  };
                  
                  return (
                    <div key={job.id} className={`bg-gradient-to-r ${statusColors[job.status]} border rounded-xl p-6 group hover:scale-[1.02] transition-all duration-300`}>
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-4">
                          <div className="text-3xl group-hover:scale-110 transition-transform">{getStatusIcon(job.status)}</div>
                          <div>
                            <h4 className="font-bold text-white text-lg">{job.name}</h4>
                            <span className={`inline-flex px-3 py-1 text-xs font-bold rounded-full mt-1 ${
                              job.status === 'completed' ? 'bg-green-400/20 text-green-400 border border-green-400/40' :
                              job.status === 'running' ? 'bg-blue-400/20 text-blue-400 border border-blue-400/40' :
                              job.status === 'failed' ? 'bg-red-400/20 text-red-400 border border-red-400/40' :
                              'bg-gray-400/20 text-gray-400 border border-gray-400/40'
                            }`}>
                              {job.status.toUpperCase()}
                            </span>
                          </div>
                        </div>
                        <div className="text-right">
                          {job.startTime && (
                            <div className="text-sm text-gray-300 font-semibold">Duration: {formatDuration(job.startTime, job.endTime)}</div>
                          )}
                          {job.recordsProcessed && (
                            <div className="text-sm text-gray-400">Records: {job.recordsProcessed.toLocaleString()}</div>
                          )}
                        </div>
                      </div>
                      
                      {job.errorMessage && (
                        <div className="bg-red-400/10 border border-red-400/30 text-red-400 p-3 rounded-lg mt-3">
                          <strong>Error:</strong> {job.errorMessage}
                        </div>
                      )}
                      
                      {job.status === 'running' && (
                        <div className="mt-3">
                          <div className="bg-gray-700 rounded-full h-3 overflow-hidden">
                            <div className="bg-gradient-to-r from-primary to-secondary h-3 rounded-full animate-pulse" style={{width: '60%'}}></div>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </div>
        
        {/* Sidebar */}
        <div className="space-y-6">
          <TeamRankings title="Top Performers" showTrend={true} />
        </div>
      </div>
    </div>
  );
}