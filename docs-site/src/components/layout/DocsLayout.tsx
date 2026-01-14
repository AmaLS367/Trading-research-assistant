import { ReactNode, useState } from 'react';
import Navbar from './Navbar';
import Sidebar from './Sidebar';
import Footer from './Footer';
import TOC from './TOC';

interface DocsLayoutProps {
  children: ReactNode;
}

export default function DocsLayout({ children }: DocsLayoutProps) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-background">
      <Navbar
        showSidebar
        onMenuClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
        isMobileMenuOpen={isMobileMenuOpen}
      />

      <div className="flex">
        <Sidebar
          isOpen={isMobileMenuOpen}
          onClose={() => setIsMobileMenuOpen(false)}
        />

        <main className="flex-1 min-w-0">
          <div className="mx-auto max-w-[1000px] px-4 py-8 md:px-8 lg:px-12">
            <div className="flex gap-12">
              <div className="flex-1 min-w-0">
                {children}
              </div>
              <div className="hidden xl:block w-64 shrink-0">
                <TOC />
              </div>
            </div>
          </div>
          <Footer />
        </main>
      </div>
    </div>
  );
}
