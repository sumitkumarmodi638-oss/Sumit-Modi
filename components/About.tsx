import React from 'react';
import { Quote, Award, Briefcase, Clock, ArrowUpRight } from 'lucide-react';
import { Reveal } from './ui/Reveal';
import { ABOUT_TEXT, PERSONAL_INFO } from '../constants';

export const About: React.FC = () => {
  return (
    <section id="about" className="py-32 bg-[#050505] relative">
      <div className="container mx-auto px-6 md:px-12">
        
        {/* Section Label */}
        <div className="mb-16">
          <Reveal>
            <div className="flex items-center gap-4">
              <div className="h-px w-12 bg-white/20"></div>
              <span className="text-xs font-mono text-gray-400 uppercase tracking-widest">The Architect</span>
            </div>
          </Reveal>
        </div>

        {/* Bento Grid Layout */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
          
          {/* 1. HEADLINE CARD (Spans 8 cols) */}
          <div className="col-span-12 md:col-span-8">
            <Reveal width="100%">
              <div className="h-full bg-[#0A0A0A] border border-white/5 rounded-[2rem] p-10 md:p-14 relative overflow-hidden group hover:border-indigo-500/30 transition-all duration-500">
                {/* Background Gradient Hover */}
                <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700"></div>
                
                <h2 className="relative z-10 text-5xl md:text-7xl font-display font-bold text-white leading-[0.9] tracking-tight">
                  Design for the <br/>
                  <span className="text-transparent bg-clip-text bg-gradient-to-r from-gray-500 to-gray-700 group-hover:from-indigo-400 group-hover:to-purple-400 transition-all duration-700">
                    Real World.
                  </span>
                </h2>
                
                <div className="absolute top-8 right-8 p-3 rounded-full border border-white/10 text-white/20 group-hover:text-white group-hover:border-white/30 transition-all duration-500">
                  <ArrowUpRight size={24} className="group-hover:rotate-45 transition-transform duration-500" />
                </div>
              </div>
            </Reveal>
          </div>

          {/* 2. PROFILE IMAGE CARD (Spans 4 cols, Tall) */}
          <div className="col-span-12 md:col-span-4 row-span-1 md:row-span-2">
            <Reveal width="100%" delay={0.2}>
              <div className="h-[500px] md:h-full min-h-[500px] bg-gray-900 rounded-[2rem] overflow-hidden relative group border border-white/5">
                {/* 
                   IMPORTANT: 
                   I have updated the src to 'sumit-profile.jpg'.
                   Please rename your uploaded image to 'sumit-profile.jpg' and ensure it is in the public/assets folder.
                */}
                <img 
                  src="/sumit-profile.jpg" 
                  alt={PERSONAL_INFO.name} 
                  className="absolute inset-0 w-full h-full object-cover group-hover:scale-105 transition-transform duration-1000 ease-out"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black via-black/20 to-transparent opacity-80"></div>
                
                <div className="absolute bottom-0 left-0 right-0 p-8 transform translate-y-2 group-hover:translate-y-0 transition-transform duration-500">
                  <p className="text-white font-display font-bold text-2xl mb-1">{PERSONAL_INFO.name}</p>
                  <p className="text-indigo-400 font-mono text-xs uppercase tracking-widest">{PERSONAL_INFO.role}</p>
                </div>
              </div>
            </Reveal>
          </div>

          {/* 3. MANIFESTO / BIO CARD (Spans 8 cols) */}
          <div className="col-span-12 md:col-span-8">
            <Reveal width="100%" delay={0.3}>
              <div className="h-full bg-[#080808] border border-white/5 rounded-[2rem] p-10 relative flex flex-col justify-between group hover:bg-[#0c0c0c] transition-colors duration-500">
                <div className="mb-6 text-indigo-500 opacity-50">
                  <Quote size={40} />
                </div>
                <div className="space-y-6">
                   {ABOUT_TEXT.split('\n').filter(Boolean).map((paragraph, i) => (
                     <p key={i} className={`text-lg md:text-xl leading-relaxed font-light ${i === 0 ? 'text-white' : 'text-gray-400'}`}>
                       {paragraph}
                     </p>
                   ))}
                </div>
                <div className="mt-8 pt-8 border-t border-white/5 flex items-center gap-4">
                  <div className="h-1 w-12 bg-indigo-500 rounded-full"></div>
                  <span className="text-xs font-mono text-gray-500 uppercase tracking-widest">Philosophy v1.0</span>
                </div>
              </div>
            </Reveal>
          </div>

          {/* 4. STATS ROW (3 Cards) */}
          <div className="col-span-12 md:col-span-8 grid grid-cols-1 md:grid-cols-3 gap-6">
            
            <Reveal width="100%" delay={0.4}>
              <div className="bg-[#0A0A0A] border border-white/5 rounded-[2rem] p-8 hover:border-indigo-500/20 transition-colors group h-full">
                <div className="flex items-start justify-between mb-4">
                  <Clock size={20} className="text-gray-600 group-hover:text-indigo-400 transition-colors" />
                  <span className="text-[10px] font-mono text-gray-600 uppercase">Experience</span>
                </div>
                <span className="block text-4xl font-display font-bold text-white mb-1 group-hover:scale-105 origin-left transition-transform">6+</span>
                <span className="text-sm text-gray-400">Years in Field</span>
              </div>
            </Reveal>

            <Reveal width="100%" delay={0.5}>
              <div className="bg-[#0A0A0A] border border-white/5 rounded-[2rem] p-8 hover:border-indigo-500/20 transition-colors group h-full">
                <div className="flex items-start justify-between mb-4">
                  <Briefcase size={20} className="text-gray-600 group-hover:text-indigo-400 transition-colors" />
                  <span className="text-[10px] font-mono text-gray-600 uppercase">Output</span>
                </div>
                <span className="block text-4xl font-display font-bold text-white mb-1 group-hover:scale-105 origin-left transition-transform">40+</span>
                <span className="text-sm text-gray-400">Projects Shipped</span>
              </div>
            </Reveal>

            <Reveal width="100%" delay={0.6}>
              <div className="bg-[#0A0A0A] border border-white/5 rounded-[2rem] p-8 hover:border-indigo-500/20 transition-colors group h-full">
                <div className="flex items-start justify-between mb-4">
                  <Award size={20} className="text-gray-600 group-hover:text-indigo-400 transition-colors" />
                  <span className="text-[10px] font-mono text-gray-600 uppercase">Recognition</span>
                </div>
                <span className="block text-4xl font-display font-bold text-white mb-1 group-hover:scale-105 origin-left transition-transform">12</span>
                <span className="text-sm text-gray-400">Industry Awards</span>
              </div>
            </Reveal>

          </div>

        </div>
      </div>
    </section>
  );
};