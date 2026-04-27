'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

type NavItem = {
  name: string;
  href: string;
  icon: string;
};

const navItems: NavItem[] = [
  { name: 'Upload', href: '/upload', icon: '📤' },
  { name: 'Topics', href: '/topics', icon: '📚' },
  { name: 'Curriculum', href: '/curriculum', icon: '📋' },
  { name: 'Lessons', href: '/lessons', icon: '📖' },
  { name: 'Slides', href: '/slides', icon: '🖥️' },
];

export default function Home() {
  const [status, setStatus] = useState<string>('checking...');

  useEffect(() => {
    fetch('/health')
      .then((res) => res.json())
      .then((data) => setStatus(data.status))
      .catch(() => setStatus('offline'));
  }, []);

  return (
    <main className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900">
              Teacher Assistant
            </h1>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-500">Backend:</span>
              <span
                className={`px-2 py-1 rounded-full text-xs font-medium ${
                  status === 'ok'
                    ? 'bg-green-100 text-green-800'
                    : 'bg-red-100 text-red-800'
                }`}
              >
                {status}
              </span>
            </div>
          </div>
        </div>
      </header>

      <nav className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex gap-1 overflow-x-auto py-2">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-100 hover:text-gray-900 transition-colors"
              >
                <span>{item.icon}</span>
                <span>{item.name}</span>
              </Link>
            ))}
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Welcome to Teacher Assistant
          </h2>
          <p className="text-gray-600 mb-6">
            Transform teaching materials into structured lesson plans and slides.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl mb-2">📤</div>
              <h3 className="font-medium">Upload Materials</h3>
              <p className="text-sm text-gray-500">
                PDF, PPTX, DOCX, XLSX
              </p>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl mb-2">📚</div>
              <h3 className="font-medium">Extract Topics</h3>
              <p className="text-sm text-gray-500">
                AI-powered extraction
              </p>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl mb-2">📖</div>
              <h3 className="font-medium">Create Lessons</h3>
              <p className="text-sm text-gray-500">
                Structured plans
              </p>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}