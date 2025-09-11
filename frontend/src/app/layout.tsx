import type { Metadata } from 'next';
import { Inter, JetBrains_Mono } from 'next/font/google';
import { ThemeProvider } from 'next-themes';
import { Suspense } from 'react';
import { Providers } from './providers';
import './globals.css';

const inter = Inter({ 
  subsets: ['latin'],
  variable: '--font-sans',
  display: 'swap',
  preload: true,
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-mono',
  display: 'swap',
  preload: false,
});

export const metadata: Metadata = {
  title: 'Event Contract Trading System',
  description: 'Probability-based trading signals for Binance event contracts',
};

export const viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
};



export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} ${jetbrainsMono.variable} font-sans antialiased`}>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <Providers>
            <div className="min-h-screen bg-background text-foreground transition-colors">
              <Suspense fallback={
                <div className="flex items-center justify-center min-h-screen">
                  <div className="loading-spinner" />
                </div>
              }>
                {children}
              </Suspense>
            </div>
          </Providers>
        </ThemeProvider>
      </body>
    </html>
  );
}