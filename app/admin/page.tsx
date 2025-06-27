'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { League } from '@/types/sports';

interface DataSource {
  id: string;
  name: string;
  type: 'api' | 'scraper';
  league: League;
  enabled: boolean;
  lastSync?: string;
  status: 'active' | 'error' | 'disabled';
  url?: string;
  apiKey?: string;
  rateLimit?: number;
}

interface ETLSchedule {
  id: string;
  name: string;
  league: League;
  type: 'full' | 'delta';
  frequency: 'daily' | 'weekly' | 'monthly';
  time: string;
  enabled: boolean;
  lastRun?: string;
  nextRun?: string;
}

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState<'sources' | 'schedules' | 'config' | 'logs'>('sources');
  
  const [dataSources, setDataSources] = useState<DataSource[]>([
    {
      id: '1',
      name: 'TheSportsDB API',
      type: 'api',
      league: League.NFL,
      enabled: true,
      status: 'active',
      lastSync: '2024-01-15T08:30:00Z',
      url: 'https://thesportsdb.com/api/v1/',
      rateLimit: 100
    },
    {
      id: '2',
      name: 'Pro Football Reference Scraper',
      type: 'scraper',
      league: League.NFL,
      enabled: true,
      status: 'active',
      lastSync: '2024-01-15T07:45:00Z',
      url: 'https://pro-football-reference.com'
    },
    {
      id: '3',
      name: 'CFL Official API',
      type: 'api',
      league: League.CFL,
      enabled: false,
      status: 'disabled',
      url: 'https://api.cfl.ca/v1/'
    }
  ]);

  const [schedules, setSchedules] = useState<ETLSchedule[]>([
    {
      id: '1',
      name: 'NFL Daily Delta Sync',
      league: League.NFL,
      type: 'delta',
      frequency: 'daily',
      time: '02:00',
      enabled: true,
      lastRun: '2024-01-15T02:00:00Z',
      nextRun: '2024-01-16T02:00:00Z'
    },
    {
      id: '2',
      name: 'CFL Weekly Full Sync',
      league: League.CFL,
      type: 'full',
      frequency: 'weekly',
      time: '03:00',
      enabled: true,
      lastRun: '2024-01-08T03:00:00Z',
      nextRun: '2024-01-15T03:00:00Z'
    }
  ]);

  const tabs = [
    { id: 'sources' as const, label: 'Data Sources', icon: '🔗' },
    { id: 'schedules' as const, label: 'ETL Schedules', icon: '⏰' },
    { id: 'config' as const, label: 'Configuration', icon: '⚙️' },
    { id: 'logs' as const, label: 'Audit Logs', icon: '📋' }
  ];

  const getStatusColor = (status: DataSource['status']) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'error': return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      case 'disabled': return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200';
    }
  };

  const toggleSource = (id: string) => {
    setDataSources(sources => 
      sources.map(source => 
        source.id === id 
          ? { ...source, enabled: !source.enabled, status: !source.enabled ? 'active' : 'disabled' }
          : source
      )
    );
  };

  const toggleSchedule = (id: string) => {
    setSchedules(schedules => 
      schedules.map(schedule => 
        schedule.id === id 
          ? { ...schedule, enabled: !schedule.enabled }
          : schedule
      )
    );
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Admin Console</h1>
        <p className="text-gray-600 dark:text-gray-400">
          Configure data sources, ETL schedules, and system settings
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

      {/* Data Sources Tab */}
      {activeTab === 'sources' && (
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Data Sources</h2>
            <Button>Add New Source</Button>
          </div>
          
          <div className="grid gap-4">
            {dataSources.map((source) => (
              <Card key={source.id}>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="text-2xl">
                        {source.type === 'api' ? '🔌' : '🕷️'}
                      </div>
                      <div>
                        <h3 className="font-semibold text-gray-900 dark:text-white">{source.name}</h3>
                        <div className="flex items-center gap-2 mt-1">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(source.status)}`}>
                            {source.status}
                          </span>
                          <span className="text-sm text-gray-500">{source.league}</span>
                          <span className="text-sm text-gray-500">•</span>
                          <span className="text-sm text-gray-500 capitalize">{source.type}</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={source.enabled}
                          onChange={() => toggleSource(source.id)}
                          className="sr-only peer"
                        />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                      </label>
                      <Button variant="outline" size="sm">Edit</Button>
                    </div>
                  </div>
                  
                  <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">URL:</span>
                      <div className="text-gray-900 dark:text-white truncate">{source.url}</div>
                    </div>
                    {source.rateLimit && (
                      <div>
                        <span className="text-gray-500 dark:text-gray-400">Rate Limit:</span>
                        <div className="text-gray-900 dark:text-white">{source.rateLimit}/hour</div>
                      </div>
                    )}
                    {source.lastSync && (
                      <div>
                        <span className="text-gray-500 dark:text-gray-400">Last Sync:</span>
                        <div className="text-gray-900 dark:text-white">
                          {new Date(source.lastSync).toLocaleString()}
                        </div>
                      </div>
                    )}
                    <div>
                      <Button variant="ghost" size="sm">Test Connection</Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* ETL Schedules Tab */}
      {activeTab === 'schedules' && (
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">ETL Schedules</h2>
            <Button>Create Schedule</Button>
          </div>
          
          <div className="grid gap-4">
            {schedules.map((schedule) => (
              <Card key={schedule.id}>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="text-2xl">⏰</div>
                      <div>
                        <h3 className="font-semibold text-gray-900 dark:text-white">{schedule.name}</h3>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-sm text-gray-500">{schedule.league}</span>
                          <span className="text-sm text-gray-500">•</span>
                          <span className="text-sm text-gray-500 capitalize">{schedule.type} sync</span>
                          <span className="text-sm text-gray-500">•</span>
                          <span className="text-sm text-gray-500">{schedule.frequency} at {schedule.time}</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={schedule.enabled}
                          onChange={() => toggleSchedule(schedule.id)}
                          className="sr-only peer"
                        />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                      </label>
                      <Button variant="outline" size="sm">Edit</Button>
                    </div>
                  </div>
                  
                  <div className="mt-4 grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                    {schedule.lastRun && (
                      <div>
                        <span className="text-gray-500 dark:text-gray-400">Last Run:</span>
                        <div className="text-gray-900 dark:text-white">
                          {new Date(schedule.lastRun).toLocaleString()}
                        </div>
                      </div>
                    )}
                    {schedule.nextRun && (
                      <div>
                        <span className="text-gray-500 dark:text-gray-400">Next Run:</span>
                        <div className="text-gray-900 dark:text-white">
                          {new Date(schedule.nextRun).toLocaleString()}
                        </div>
                      </div>
                    )}
                    <div>
                      <Button variant="ghost" size="sm">Run Now</Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Configuration Tab */}
      {activeTab === 'config' && (
        <div className="space-y-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">System Configuration</h2>
          
          <div className="grid md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Database Settings</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Connection String
                  </label>
                  <input 
                    type="text" 
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
                    value="postgresql://user:***@localhost:5432/sda"
                    readOnly
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Pool Size
                  </label>
                  <input 
                    type="number" 
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
                    defaultValue={10}
                  />
                </div>
                <Button variant="outline" size="sm">Test Connection</Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Storage Settings</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Google Cloud Storage Bucket
                  </label>
                  <input 
                    type="text" 
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
                    defaultValue="sda-data-exports"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Backup Retention (days)
                  </label>
                  <input 
                    type="number" 
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
                    defaultValue={90}
                  />
                </div>
                <Button variant="outline" size="sm">Test Access</Button>
              </CardContent>
            </Card>
          </div>
          
          <div className="flex justify-end">
            <Button>Save Configuration</Button>
          </div>
        </div>
      )}

      {/* Logs Tab */}
      {activeTab === 'logs' && (
        <div className="space-y-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Audit Logs</h2>
          
          <Card>
            <CardContent className="p-6">
              <div className="text-center py-8 text-gray-500">
                Audit logging functionality coming soon...
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}