'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const navItems = [
  {
    name: 'Elite Dashboard',
    href: '/dashboard',
    icon: '👑',
    description: 'Performance Overview'
  },
  {
    name: 'Model Rankings',
    href: '/explore',
    icon: '⭐',
    description: 'Player Analysis'
  },
  {
    name: 'Scouting Report',
    href: '/data-sources',
    icon: '🎯',
    description: 'Data Insights'
  },
  {
    name: 'Competition Hub',
    href: '/admin',
    icon: '🏆',
    description: 'Team Management'
  },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 h-full w-72 bg-gradient-to-b from-sidebar via-sidebar to-purple-900/20 text-white p-6 flex flex-col border-r border-purple-500/20">
      <div className="mb-10">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 bg-gradient-to-br from-primary to-secondary rounded-lg flex items-center justify-center">
            <span className="text-xl">🏆</span>
          </div>
          <div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
              Next Top Model
            </h1>
            <p className="text-xs text-gray-400">Elite Sports Analytics v2.0</p>
          </div>
        </div>
      </div>
      <nav className="flex-grow">
        <ul className="space-y-3">
          {navItems.map((item) => (
            <li key={item.name}>
              <Link
                href={item.href}
                className={`group flex items-center p-4 rounded-xl transition-all duration-300 border
                  ${pathname === item.href 
                    ? 'bg-gradient-to-r from-primary/20 to-secondary/20 border-primary/50 text-white shadow-lg shadow-primary/25' 
                    : 'text-gray-300 hover:bg-purple-800/30 border-transparent hover:border-purple-500/30 hover:text-white'
                  }
                `}
              >
                <span className="mr-4 text-2xl group-hover:scale-110 transition-transform">{item.icon}</span>
                <div>
                  <span className="font-semibold block">{item.name}</span>
                  <span className="text-xs text-gray-400 group-hover:text-gray-300">{item.description}</span>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      </nav>
      
      <div className="mt-auto pt-6 border-t border-purple-500/20">
        <div className="bg-gradient-to-r from-purple-800/40 to-pink-800/40 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-white mb-1">Performance Status</h3>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            <span className="text-xs text-green-400">All Systems Operational</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
