import React, { useState, useEffect } from 'react';
import { Mail, Linkedin, Dribbble, MapPin, Globe, ArrowUpRight, Clock, Phone } from 'lucide-react';
import { Reveal } from './ui/Reveal';
import { PERSONAL_INFO } from '../constants';

export const Contact: React.FC = () => {
  const [time, setTime] = useState('');

  useEffect(() => {
    // Update Kolkata Time (GMT+5:30)
    const updateTime = () => {
      const now = new Date();
      const options: Intl.DateTimeFormatOptions = { 
        timeZone: 'Asia/Kolkata', 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: true 
      };
      setTime(now.toLocaleTimeString('en-US', options));
    };
    
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <footer id="contact" className="relative bg-[#030303] pt-32 pb-12 overflow-hidden border-t border-white/5">
      
      {/* Abstract Map Background */}
      <div className="absolute inset-0 opacity-10 pointer-events-none">
         <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[1000px] h-[500px] rounded-[100%] border border-white/20 blur-[100px]"></div>
         <div className="w-full h-full bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-indigo-900/20 via-[#030303] to-[#030303]"></div>
      </div>

      <div className="container mx-auto px-6 md:px-12 relative z-10">
        
        {/* Main CTA Section */}
        <div className="flex flex-col md:flex-row items-start justify-between gap-16 mb-32">
          
          <div className="md:w-2/3">
            <Reveal>
              <div className="flex items-center gap-3 mb-8">
                <div className="relative flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
                </div>
                <span className="text-sm font-mono text-emerald-400 uppercase tracking-widest">Available for new projects</span>
              </div>
              
              <h2 className="text-6xl md:text-8xl lg:text-9xl font-display font-bold text-white tracking-tighter leading-[0.9] mb-12">
                Let's build <br />
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-gray-500 via-white to-gray-500 hover:text-indigo-400 transition-colors duration-500 cursor-default">
                  something real.
                </span>
              </h2>

              <div className="flex flex-col gap-6 items-start">
                <a 
                  href={`mailto:${PERSONAL_INFO.email}`} 
                  className="inline-flex items-center gap-4 text-2xl md:text-3xl font-light text-white hover:text-indigo-400 transition-colors group"
                >
                  <Mail size={24} className="text-gray-500 group-hover:text-indigo-400 transition-colors" />
                  <span className="border-b border-white/20 group-hover:border-indigo-400 pb-1 transition-colors">
                    {PERSONAL_INFO.email}
                  </span>
                  <ArrowUpRight className="group-hover:-translate-y-1 group-hover:translate-x-1 transition-transform duration-300 opacity-50 group-hover:opacity-100" size={24} />
                </a>

                {PERSONAL_INFO.phone && (
                  <a 
                    href={`tel:${PERSONAL_INFO.phone.replace(/\s/g, '')}`} 
                    className="inline-flex items-center gap-4 text-2xl md:text-3xl font-light text-white hover:text-indigo-400 transition-colors group"
                  >
                    <Phone size={24} className="text-gray-500 group-hover:text-indigo-400 transition-colors" />
                    <span className="border-b border-white/20 group-hover:border-indigo-400 pb-1 transition-colors">
                      {PERSONAL_INFO.phone}
                    </span>
                  </a>
                )}
              </div>
            </Reveal>
          </div>

          {/* Location & Time Module */}
          <div className="md:w-1/3 flex flex-col md:items-end">
             <Reveal delay={0.2}>
               <div className="bg-[#0A0A0A] border border-white/10 rounded-2xl p-6 w-full max-w-xs backdrop-blur-sm hover:border-white/20 transition-colors">
                  <div className="flex items-start justify-between mb-8">
                     <div className="p-3 bg-indigo-500/10 rounded-full text-indigo-400">
                        <Globe size={24} />
                     </div>
                     <span className="text-[10px] font-mono text-gray-500 uppercase tracking-widest">Base of Ops</span>
                  </div>
                  
                  <div>
                    <h3 className="text-white text-lg font-bold mb-1 flex items-center gap-2">
                      Kolkata, India <MapPin size={14} className="text-red-500 fill-red-500/20" />
                    </h3>
                    <p className="text-gray-500 text-sm mb-4">West Bengal</p>
                    
                    <div className="flex items-center gap-3 pt-4 border-t border-white/5">
                       <Clock size={14} className="text-gray-400" />
                       <span className="text-xl font-mono text-white font-light tracking-widest">
                         {time} <span className="text-xs text-gray-600 font-bold ml-1">IST</span>
                       </span>
                    </div>
                  </div>
               </div>
             </Reveal>
          </div>
        </div>

        {/* Links Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12 border-t border-white/10 pt-16 pb-8">
           
           <div className="col-span-1 md:col-span-2">
             <span className="text-xl font-display font-bold text-white tracking-widest">SM.</span>
             <p className="mt-4 text-gray-500 max-w-sm text-sm leading-relaxed">
               Principal Product Designer focusing on complex systems, interaction design, and visual storytelling.
             </p>
           </div>

           <div>
              <h4 className="text-xs font-mono text-white uppercase tracking-widest mb-6">Social</h4>
              <ul className="space-y-4">
                <li>
                  <a href="#" className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors text-sm group">
                    <Linkedin size={16} /> LinkedIn 
                    <ArrowUpRight size={12} className="opacity-0 group-hover:opacity-100 transition-opacity" />
                  </a>
                </li>
                <li>
                  <a href="#" className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors text-sm group">
                    <Dribbble size={16} /> Dribbble
                    <ArrowUpRight size={12} className="opacity-0 group-hover:opacity-100 transition-opacity" />
                  </a>
                </li>
              </ul>
           </div>

           <div>
              <h4 className="text-xs font-mono text-white uppercase tracking-widest mb-6">Sitemap</h4>
              <ul className="space-y-4">
                <li><a href="#about" className="text-gray-400 hover:text-white transition-colors text-sm">Philosophy</a></li>
                <li><a href="#work" className="text-gray-400 hover:text-white transition-colors text-sm">Case Studies</a></li>
                <li><a href="#process" className="text-gray-400 hover:text-white transition-colors text-sm">Methodology</a></li>
              </ul>
           </div>

        </div>

        {/* Copyright */}
        <div className="flex flex-col md:flex-row justify-between items-center gap-4 pt-8 border-t border-white/5 text-[10px] font-mono text-gray-600 uppercase tracking-widest">
          <p>© {new Date().getFullYear()} Sumit Modi. All rights reserved.</p>
          <p className="hover:text-gray-400 transition-colors cursor-default">Designed & Engineered with Precision</p>
        </div>

      </div>
    </footer>
  );
};