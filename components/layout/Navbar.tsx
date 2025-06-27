'use client';

import Link from 'next/link';
import { useState } from 'react';

export function Navbar() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <nav className="bg-transparent fixed top-0 left-0 right-0 z-50 backdrop-blur-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-20 items-center">
          <div className="flex items-center">
            <Link href="/" className="flex items-center space-x-3">
              <img src="/next_top_model_logo.png" alt="Sports Data Aggregator Logo" className="h-10 w-auto" />
              <span className="text-2xl font-bold text-white tracking-wider">
                SDA
              </span>
            </Link>
          </div>

          <div className="hidden md:flex items-center space-x-10">
            <Link 
              href="/dashboard" 
              className="text-gray-300 hover:text-accent font-medium transition-colors duration-300 text-shadow-glow"
            >
              Dashboard
            </Link>
            <Link 
              href="/explore" 
              className="text-gray-300 hover:text-accent font-medium transition-colors duration-300 text-shadow-glow"
            >
              Data Explorer
            </Link>
            <Link 
              href="/admin" 
              className="text-gray-300 hover:text-accent font-medium transition-colors duration-300 text-shadow-glow"
            >
              Admin
            </Link>
          </div>

          <button
            className="md:hidden p-2 rounded-md text-gray-300"
            onClick={() => setIsMenuOpen(!isMenuOpen)}
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
        </div>
      </div>

      {isMenuOpen && (
        <div className="md:hidden bg-background/90 backdrop-blur-sm border-t border-primary/20">
          <div className="px-2 pt-2 pb-3 space-y-1">
            <Link 
              href="/dashboard" 
              className="block px-3 py-2 text-gray-300 hover:text-accent"
            >
              Dashboard
            </Link>
            <Link 
              href="/explore" 
              className="block px-3 py-2 text-gray-300 hover:text-accent"
            >
              Data Explorer
            </Link>
            <Link 
              href="/admin" 
              className="block px-3 py-2 text-gray-300 hover:text-accent"
            >
              Admin
            </Link>
          </div>
        </div>
      )}
    </nav>
  );
}