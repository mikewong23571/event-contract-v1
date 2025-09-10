/* Using the automatic JSX runtime; no explicit React import required. */

import { ReactNode, useState } from 'react';
import {
  ChartBarIcon,
  SignalIcon,
  CogIcon,
  PlayIcon,
  BellIcon,
  HomeIcon,
  Bars3Icon,
  XMarkIcon,
} from '@heroicons/react/24/outline';

/**
 * Dashboard
 * Main layout component providing navigation, sidebar, and content areas.
 * Responsive design with collapsible sidebar and breadcrumb navigation.
 *
 * Features:
 * - Responsive sidebar navigation
 * - Breadcrumb navigation
 * - Active page highlighting
 * - Mobile-friendly hamburger menu
 * - Content area with proper spacing
 */

export interface NavigationItem {
  name: string;
  href: string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  current?: boolean;
  badge?: string | number;
}

export interface DashboardProps {
  children: ReactNode;
  currentPage: string;
  navigation?: NavigationItem[];
  className?: string;
  sidebarOpen?: boolean;
  onSidebarToggle?: (open: boolean) => void;
}

const defaultNavigation: NavigationItem[] = [
  { name: 'Dashboard', href: '/', icon: HomeIcon },
  { name: 'Signals', href: '/signals', icon: SignalIcon },
  { name: 'Market Data', href: '/market-data', icon: ChartBarIcon },
  { name: 'Backtesting', href: '/backtesting', icon: PlayIcon },
  { name: 'Risk Management', href: '/risk', icon: CogIcon },
  { name: 'Alerts', href: '/alerts', icon: BellIcon },
];

function classNames(...classes: (string | boolean | undefined)[]): string {
  return classes.filter(Boolean).join(' ');
}

export function Dashboard({
  children,
  currentPage,
  navigation = defaultNavigation,
  className,
  sidebarOpen = false,
  onSidebarToggle
}: DashboardProps) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(sidebarOpen);

  const handleSidebarToggle = (open: boolean) => {
    setIsSidebarOpen(open);
    onSidebarToggle?.(open);
  };

  // Update navigation items with current page
  const updatedNavigation = navigation.map(item => ({
    ...item,
    current: item.name.toLowerCase() === currentPage.toLowerCase() || 
             item.href === `/${currentPage.toLowerCase()}` ||
             (currentPage === 'Home' && item.href === '/')
  }));

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile sidebar backdrop */}
      {isSidebarOpen && (
        <div 
          className="fixed inset-0 z-40 lg:hidden"
          onClick={() => handleSidebarToggle(false)}
        >
          <div className="absolute inset-0 bg-gray-600 opacity-75" />
        </div>
      )}

      {/* Mobile sidebar */}
      <div className={classNames(
        'fixed inset-y-0 left-0 z-50 w-64 transform bg-white shadow-xl transition-transform duration-300 ease-in-out lg:hidden',
        isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
      )}>
        <div className="flex h-16 items-center justify-between border-b border-gray-200 px-4">
          <div className="flex items-center">
            <div className="h-8 w-8 rounded bg-blue-600 flex items-center justify-center">
              <ChartBarIcon className="h-5 w-5 text-white" />
            </div>
            <span className="ml-2 text-lg font-semibold text-gray-900">
              Event Contract
            </span>
          </div>
          <button
            onClick={() => handleSidebarToggle(false)}
            className="rounded-md p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-500"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        <nav className="mt-8 px-4">
          <ul className="space-y-1">
            {updatedNavigation.map((item) => (
              <li key={item.name}>
                <a
                  href={item.href}
                  className={classNames(
                    'group flex items-center rounded-md px-2 py-2 text-sm font-medium',
                    item.current
                      ? 'bg-blue-100 text-blue-900'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  )}
                >
                  <item.icon
                    className={classNames(
                      'mr-3 h-5 w-5 flex-shrink-0',
                      item.current ? 'text-blue-500' : 'text-gray-400'
                    )}
                  />
                  {item.name}
                  {item.badge && (
                    <span className="ml-auto rounded-full bg-blue-100 px-2 py-1 text-xs text-blue-600">
                      {item.badge}
                    </span>
                  )}
                </a>
              </li>
            ))}
          </ul>
        </nav>
      </div>

      {/* Desktop sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col">
        <div className="flex min-h-0 flex-1 flex-col border-r border-gray-200 bg-white">
          <div className="flex h-16 items-center border-b border-gray-200 px-4">
            <div className="h-8 w-8 rounded bg-blue-600 flex items-center justify-center">
              <ChartBarIcon className="h-5 w-5 text-white" />
            </div>
            <span className="ml-2 text-lg font-semibold text-gray-900">
              Event Contract
            </span>
          </div>

          <nav className="mt-8 flex-1 px-4 pb-4">
            <ul className="space-y-1">
              {updatedNavigation.map((item) => (
                <li key={item.name}>
                  <a
                    href={item.href}
                    className={classNames(
                      'group flex items-center rounded-md px-2 py-2 text-sm font-medium',
                      item.current
                        ? 'bg-blue-100 text-blue-900'
                        : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                    )}
                  >
                    <item.icon
                      className={classNames(
                        'mr-3 h-5 w-5 flex-shrink-0',
                        item.current ? 'text-blue-500' : 'text-gray-400'
                      )}
                    />
                    {item.name}
                    {item.badge && (
                      <span className="ml-auto rounded-full bg-blue-100 px-2 py-1 text-xs text-blue-600">
                        {item.badge}
                      </span>
                    )}
                  </a>
                </li>
              ))}
            </ul>
          </nav>
        </div>
      </div>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Header */}
        <div className="sticky top-0 z-10 flex h-16 flex-shrink-0 border-b border-gray-200 bg-white shadow-sm">
          <button
            type="button"
            className="border-r border-gray-200 px-4 text-gray-500 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500 lg:hidden"
            onClick={() => handleSidebarToggle(true)}
          >
            <Bars3Icon className="h-6 w-6" />
          </button>

          <div className="flex flex-1 items-center justify-between px-4 sm:px-6 lg:px-8">
            <div className="flex items-center">
              <nav className="flex" aria-label="Breadcrumb">
                <ol className="flex items-center space-x-4">
                  <li>
                    <div>
                      <a href="/" className="text-gray-400 hover:text-gray-500">
                        <HomeIcon className="h-5 w-5 flex-shrink-0" />
                        <span className="sr-only">Home</span>
                      </a>
                    </div>
                  </li>
                  {currentPage !== 'Home' && (
                    <li>
                      <div className="flex items-center">
                        <svg
                          className="h-5 w-5 flex-shrink-0 text-gray-300"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path
                            fillRule="evenodd"
                            d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                            clipRule="evenodd"
                          />
                        </svg>
                        <span className="ml-4 text-sm font-medium text-gray-500">
                          {currentPage}
                        </span>
                      </div>
                    </li>
                  )}
                </ol>
              </nav>
            </div>

            <div className="flex items-center space-x-4">
              {/* Status indicator */}
              <div className="flex items-center space-x-2">
                <div className="h-2 w-2 rounded-full bg-green-400" />
                <span className="text-sm text-gray-500">Connected</span>
              </div>

              {/* User menu placeholder */}
              <div className="h-8 w-8 rounded-full bg-gray-300" />
            </div>
          </div>
        </div>

        {/* Page content */}
        <main className={classNames('flex-1', className)}>
          <div className="py-6">
            <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
              {children}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

export default Dashboard;