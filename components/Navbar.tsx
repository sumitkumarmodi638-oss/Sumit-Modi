import React, { useState, useEffect } from 'react';
import { Menu, X } from 'lucide-react';

export const Navbar: React.FC = () => {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navLinks = [
    { name: 'Philosophy', href: '#philosophy' },
    { name: 'Profile', href: '#about' },
    { name: 'Expertise', href: '#skills' },
    { name: 'Work', href: '#work' },
  ];

  return (
    <>
      <nav 
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-700 ease-premium ${
          isScrolled ? 'bg-[#050505]/90 backdrop-blur-md border-b border-white/5 py-4' : 'bg-transparent py-8'
        }`}
      >
        <div className="container mx-auto px-6 md:px-12 flex justify-between items-center">
          
          {/* Logo - Minimalist */}
          <a href="#" className="text-sm font-display font-bold tracking-wider text-white hover:opacity-80 transition-opacity">
            SM
          </a>

          {/* Desktop Menu - Nearly Invisible until hover */}
          <div className="hidden md:flex items-center gap-12">
            {navLinks.map((link) => (
              <a 
                key={link.name} 
                href={link.href} 
                className="text-[11px] font-mono font-medium text-gray-500 hover:text-white transition-colors tracking-[0.1em] uppercase"
              >
                {link.name}
              </a>
            ))}
            <a 
               href="#contact" 
               className="text-[11px] font-mono font-medium text-white hover:text-gray-300 transition-colors tracking-[0.1em] uppercase"
             >
               Contact
             </a>
          </div>

          {/* Mobile Toggle */}
          <button 
            className="md:hidden text-white p-2 -mr-2 opacity-80 hover:opacity-100"
            onClick={() => setIsMenuOpen(!isMenuOpen)}
          >
            {isMenuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>

        </div>
      </nav>

      {/* Mobile Menu Overlay */}
      <div 
        className={`fixed inset-0 z-40 bg-[#050505] transform transition-transform duration-500 ease-premium ${isMenuOpen ? 'translate-y-0' : '-translate-y-full'}`}
      >
        <div className="flex flex-col items-center justify-center h-full space-y-10">
          {navLinks.map((link) => (
            <a 
              key={link.name} 
              href={link.href}
              className="text-2xl font-display font-medium text-white tracking-tight"
              onClick={() => setIsMenuOpen(false)}
            >
              {link.name}
            </a>
          ))}
          <a 
             href="#contact"
             className="text-sm font-mono text-gray-400 uppercase tracking-widest mt-8"
             onClick={() => setIsMenuOpen(false)}
          >
            Get in Touch
          </a>
        </div>
      </div>
    </>
  );
};