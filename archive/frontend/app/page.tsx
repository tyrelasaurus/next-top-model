'use client';

import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

export default function Home() {
  const features = [
    {
      title: 'Elite Performance Analytics',
      description: 'Advanced statistical modeling and player performance metrics with predictive insights',
      icon: '⭐',
      href: '/dashboard',
      gradient: 'from-yellow-400 to-orange-500'
    },
    {
      title: 'Model Rankings Hub', 
      description: 'Comprehensive player rankings and scouting reports with real-time analysis',
      icon: '🏆',
      href: '/explore',
      gradient: 'from-primary to-secondary'
    },
    {
      title: 'Competition Intelligence',
      description: 'Strategic insights, team analysis, and performance benchmarking tools',
      icon: '🎯',
      href: '/data-sources',
      gradient: 'from-emerald-400 to-teal-500'
    }
  ];

  const stats = [
    { label: 'Elite Players', value: '1,247', description: 'Top tier athletes tracked', icon: '🌟' },
    { label: 'Performance Metrics', value: '50M+', description: 'Data points analyzed', icon: '📈' },
    { label: 'Team Rankings', value: '32', description: 'NFL franchises monitored', icon: '🏆' },
    { label: 'Prediction Accuracy', value: '94.2%', description: 'Model precision rate', icon: '🎯' }
  ];

  return (
    <div className="max-w-7xl mx-auto py-8">
      {/* Hero Section */}
      <div className="text-center mb-24 relative">
        <div className="absolute inset-0 bg-gradient-to-r from-primary/10 via-secondary/10 to-primary/10 rounded-3xl blur-3xl"></div>
        <div className="relative">
          <div className="inline-flex items-center gap-3 bg-gradient-to-r from-primary/20 to-secondary/20 rounded-full px-6 py-2 mb-6 border border-primary/30">
            <span className="text-2xl">🎆</span>
            <span className="text-sm font-semibold text-primary">Elite Sports Analytics Platform</span>
          </div>
          <h1 className="text-6xl font-bold mb-6">
            <span className="bg-gradient-to-r from-white via-primary to-secondary bg-clip-text text-transparent">
              Next Top Model
            </span>
          </h1>
          <p className="text-xl text-gray-300 mb-8 max-w-4xl mx-auto leading-relaxed">
            Discover tomorrow&apos;s superstars today. Our cutting-edge analytics platform identifies elite talent, 
            predicts performance trajectories, and delivers insights that transform how teams scout and develop players.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/explore">
              <Button size="lg" className="bg-gradient-to-r from-primary to-secondary hover:from-primary/80 hover:to-secondary/80 text-white font-semibold px-8 py-4 rounded-xl transition-all duration-300 shadow-lg shadow-primary/25">
                ⭐ Discover Talent
              </Button>
            </Link>
            <Link href="/dashboard">
              <Button variant="outline" size="lg" className="border-2 border-primary/50 text-primary hover:bg-primary/10 font-semibold px-8 py-4 rounded-xl transition-all duration-300">
                📈 View Analytics
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Stats Section */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-16">
        {stats.map((stat, index) => (
          <Card key={index} className="text-center bg-gradient-to-br from-purple-900/20 to-pink-900/20 border-purple-500/30 hover:border-primary/50 transition-all duration-300 group">
            <CardContent className="p-6">
              <div className="text-4xl mb-3 group-hover:scale-110 transition-transform">{stat.icon}</div>
              <div className="text-3xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent mb-2">
                {stat.value}
              </div>
              <div className="text-lg font-semibold text-white mb-1">
                {stat.label}
              </div>
              <div className="text-sm text-gray-400">
                {stat.description}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Features Section */}
      <div className="grid md:grid-cols-3 gap-8 mb-16">
        {features.map((feature, index) => (
          <Card key={index} className="bg-gradient-to-br from-gray-900/50 to-purple-900/30 border-purple-500/30 hover:border-primary/50 transition-all duration-300 group overflow-hidden relative">
            <div className={`absolute inset-0 bg-gradient-to-br ${feature.gradient} opacity-5 group-hover:opacity-10 transition-opacity`}></div>
            <CardHeader className="relative">
              <CardTitle className="flex items-center gap-4">
                <div className={`w-12 h-12 bg-gradient-to-br ${feature.gradient} rounded-xl flex items-center justify-center text-white text-2xl group-hover:scale-110 transition-transform`}>
                  {feature.icon}
                </div>
                <span className="text-xl">{feature.title}</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="relative">
              <p className="text-gray-300 mb-6 leading-relaxed">
                {feature.description}
              </p>
              <Link href={feature.href}>
                <Button variant="ghost" size="sm" className="text-primary hover:text-white hover:bg-primary/20 transition-all duration-300">
                  Explore →
                </Button>
              </Link>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Quick Start Section */}
      <Card className="bg-gradient-to-br from-gray-900/80 to-purple-900/40 border-purple-500/30">
        <CardHeader>
          <CardTitle className="text-2xl flex items-center gap-3">
            <span className="text-3xl">🚀</span>
            Get Started with Elite Analytics
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-2 gap-10">
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-gradient-to-br from-primary to-secondary rounded-lg flex items-center justify-center text-white font-bold text-sm">
                  🔍
                </div>
                <h4 className="font-semibold text-white text-lg">For Talent Scouts</h4>
              </div>
              <ul className="space-y-3 text-gray-300 ml-11">
                <li className="flex items-start gap-3">
                  <span className="text-primary font-bold">1.</span>
                  <span>Explore player rankings in the <Link href="/explore" className="text-primary hover:text-secondary transition-colors">Model Rankings Hub</Link></span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-primary font-bold">2.</span>
                  <span>Filter by position, performance metrics, and potential</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-primary font-bold">3.</span>
                  <span>Generate comprehensive scouting reports</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-primary font-bold">4.</span>
                  <span>Track performance trends and projections</span>
                </li>
              </ul>
            </div>
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-gradient-to-br from-emerald-400 to-teal-500 rounded-lg flex items-center justify-center text-white font-bold text-sm">
                  ⚙️
                </div>
                <h4 className="font-semibold text-white text-lg">For Team Managers</h4>
              </div>
              <ul className="space-y-3 text-gray-300 ml-11">
                <li className="flex items-start gap-3">
                  <span className="text-secondary font-bold">1.</span>
                  <span>Access team analytics in the <Link href="/admin" className="text-secondary hover:text-primary transition-colors">Competition Hub</Link></span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-secondary font-bold">2.</span>
                  <span>Monitor player development and team chemistry</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-secondary font-bold">3.</span>
                  <span>Optimize roster composition and strategy</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-secondary font-bold">4.</span>
                  <span>Track competitive intelligence and benchmarks</span>
                </li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}