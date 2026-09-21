import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  metadataBase: new URL('https://nyc-building-compliance-360-portfolio.hsieh203.chatgpt.site'),
  title: 'NYC Building Compliance 360',
  description: 'A governed analytics product for NYC building permits, complaints, and violations.',
  openGraph: {
    title: 'NYC Building Compliance 360',
    description: 'Permits, complaints, and violations—one governed decision layer.',
    images: ['/og.png'],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'NYC Building Compliance 360',
    description: 'Permits, complaints, and violations—one governed decision layer.',
    images: ['/og.png'],
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
