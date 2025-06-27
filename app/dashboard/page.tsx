'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { SimpleChart } from '@/components/charts/SimpleChart';

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
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Dashboard</h1>
        <p className="text-gray-600 dark:text-gray-400">
          Monitor ETL jobs, data quality, and system health
        </p>
      </div>

      {/* System Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Total Teams</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {metrics.totalTeams.toLocaleString()}
                </p>
              </div>
              <div className="text-3xl">🏟️</div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Total Games</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {metrics.totalGames.toLocaleString()}
                </p>
              </div>
              <div className="text-3xl">🏈</div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Total Players</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {metrics.totalPlayers.toLocaleString()}
                </p>
              </div>
              <div className="text-3xl">👤</div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Data Quality</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {metrics.dataQualityScore}%
                </p>
              </div>
              <div className="text-3xl">📊</div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* System Health */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <Card>
          <CardHeader>
            <CardTitle>API Health</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-3">
              <div className={`w-3 h-3 rounded-full ${
                metrics.apiHealth === 'healthy' ? 'bg-green-500' :
                metrics.apiHealth === 'degraded' ? 'bg-yellow-500' : 'bg-red-500'
              }`}></div>
              <span className="capitalize font-medium">{metrics.apiHealth}</span>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
              All data sources responding normally
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Last Update</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-lg font-medium">
              {new Date(metrics.lastUpdate).toLocaleString()}
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
              Next scheduled: 02:00 UTC
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <Button variant="outline" size="sm" className="w-full">
              Trigger Manual Sync
            </Button>
            <Button variant="outline" size="sm" className="w-full">
              Export Data
            </Button>
            <Button variant="outline" size="sm" className="w-full">
              View Logs
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <Card>
          <CardHeader>
            <CardTitle>Data Ingestion by League</CardTitle>
          </CardHeader>
          <CardContent>
            <SimpleChart 
              type="pie"
              data={[
                { label: 'NFL', value: 32, color: '#3B82F6' },
                { label: 'CFL', value: 9, color: '#EF4444' },
                { label: 'NCAA', value: 130, color: '#10B981' }
              ]}
              width={350}
              height={250}
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Weekly ETL Performance</CardTitle>
          </CardHeader>
          <CardContent>
            <SimpleChart 
              type="line"
              data={[
                { label: 'Mon', value: 45 },
                { label: 'Tue', value: 52 },
                { label: 'Wed', value: 38 },
                { label: 'Thu', value: 61 },
                { label: 'Fri', value: 55 },
                { label: 'Sat', value: 67 },
                { label: 'Sun', value: 43 }
              ]}
              width={350}
              height={250}
            />
          </CardContent>
        </Card>
      </div>

      {/* ETL Jobs Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>ETL Jobs</span>
            <Button size="sm">
              Refresh
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {jobs.map((job) => (
              <div key={job.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-3">
                    <span className="text-lg">{getStatusIcon(job.status)}</span>
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white">{job.name}</h4>
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(job.status)}`}>
                        {job.status}
                      </span>
                    </div>
                  </div>
                  <div className="text-right text-sm text-gray-600 dark:text-gray-400">
                    {job.startTime && (
                      <div>Duration: {formatDuration(job.startTime, job.endTime)}</div>
                    )}
                    {job.recordsProcessed && (
                      <div>Records: {job.recordsProcessed.toLocaleString()}</div>
                    )}
                  </div>
                </div>
                
                {job.errorMessage && (
                  <div className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-2 rounded mt-2">
                    Error: {job.errorMessage}
                  </div>
                )}
                
                {job.status === 'running' && (
                  <div className="mt-2">
                    <div className="bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                      <div className="bg-blue-600 h-2 rounded-full animate-pulse" style={{width: '60%'}}></div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}