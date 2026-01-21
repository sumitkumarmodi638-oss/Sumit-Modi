import React, { useState } from 'react';
import { Layout, Brain, Zap, PenTool, Search, Terminal, Cpu, Command, Share2, Layers, GitBranch, Monitor } from 'lucide-react';
import { Reveal } from './ui/Reveal';
import { SKILL_CATEGORIES } from '../constants';

const THEMES = [
  { 
    id: "design",
    color: "text-rose-400", 
    border: "group-hover:border-rose-500/50", 
    bg: "group-hover:bg-rose-500/5",
    gradient: "from-rose-500",
    icon: PenTool,
    glitchColor: "#fb7185" 
  },
  { 
    id: "strategy",
    color: "text-cyan-400", 
    border: "group-hover:border-cyan-500/50", 
    bg: "group-hover:bg-cyan-500/5",
    gradient: "from-cyan-500",
    icon: Search,
    glitchColor: "#22d3ee" 
  },
  { 
    id: "execution",
    color: "text-emerald-400", 
    border: "group-hover:border-emerald-500/50", 
    bg: "group-hover:bg-emerald-500/5",
    gradient: "from-emerald-500",
    icon: Terminal,
    glitchColor: "#34d399" 
  }
];

export const Skills: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);

  const activeTheme = THEMES[activeTab];
  const activeCategory = SKILL_CATEGORIES[activeTab];

  return (
    <section id="skills" className="py-32 bg-[#050505] relative overflow-hidden min-h-screen flex flex-col justify-center">
      
      {/* Dynamic Background Mesh */}
      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] pointer-events-none"></div>
      
      {/* Active Theme Glow */}
      <div 
        className={`absolute top-0 left-1/2 -translate-x-1/2 w-full h-[500px] bg-gradient-to-b ${activeTheme.gradient} to-transparent opacity-5 blur-[120px] transition-all duration-1000 ease-in-out`}
      ></div>

      <div className="container mx-auto px-6 md:px-12 relative z-10">
        
        {/* Section Header */}
        <div className="text-center mb-20">
          <Reveal width="100%">
            <div className="inline-flex items-center gap-2 mb-4 px-3 py-1 rounded-full border border-white/10 bg-white/5 backdrop-blur-sm">
               <Cpu size={14} className={activeTheme.color} />
               <span className="text-[10px] font-mono uppercase tracking-widest text-gray-400">System Capabilities</span>
            </div>
            <h2 className="text-5xl md:text-7xl font-display font-bold text-white tracking-tight mb-6">
              Technical <span className={activeTheme.color}>Arsenal</span>
            </h2>
          </Reveal>
        </div>

        {/* Cybernetic Tabs */}
        <div className="flex justify-center mb-16">
          <div className="inline-flex p-1 bg-white/5 border border-white/10 rounded-full backdrop-blur-md">
            {SKILL_CATEGORIES.map((cat, idx) => {
              const isActive = activeTab === idx;
              const ThemeIcon = THEMES[idx].icon;
              return (
                <button
                  key={cat.id}
                  onClick={() => setActiveTab(idx)}
                  className={`
                    relative px-6 py-3 rounded-full flex items-center gap-3 transition-all duration-500
                    ${isActive ? 'text-white' : 'text-gray-500 hover:text-gray-300'}
                  `}
                >
                  {isActive && (
                    <div className="absolute inset-0 bg-white/10 rounded-full shadow-inner border border-white/10"></div>
                  )}
                  <ThemeIcon size={16} className={`relative z-10 ${isActive ? THEMES[idx].color : ''}`} />
                  <span className="relative z-10 text-sm font-mono uppercase tracking-widest font-bold">
                    {cat.title}
                  </span>
                </button>
              )
            })}
          </div>
        </div>

        {/* Dashboard Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-start">
          
          {/* Left: Category Overview (Sticky) */}
          <div className="lg:col-span-4 lg:sticky lg:top-32">
            <Reveal key={`overview-${activeTab}`} width="100%">
               <div className="p-8 md:p-10 rounded-[2rem] border border-white/10 bg-[#0A0A0A] relative overflow-hidden group">
                  {/* Decorative Scan Line */}
                  <div className={`absolute top-0 left-0 w-full h-1 bg-gradient-to-r ${activeTheme.gradient} to-transparent opacity-50`}></div>
                  
                  <div className={`w-16 h-16 rounded-2xl bg-white/5 flex items-center justify-center mb-8 border border-white/5 ${activeTheme.color}`}>
                     <activeTheme.icon size={32} />
                  </div>
                  
                  <h3 className="text-3xl font-display font-bold text-white mb-4">
                    {activeCategory.title}
                  </h3>
                  <p className="text-gray-400 text-lg leading-relaxed mb-8">
                    {activeCategory.subtitle}
                  </p>

                  <div className="space-y-4">
                    <div className="flex items-center gap-3 text-sm text-gray-500 font-mono">
                       <Command size={14} />
                       <span>Protocol: Active</span>
                    </div>
                    <div className="flex items-center gap-3 text-sm text-gray-500 font-mono">
                       <Layers size={14} />
                       <span>Depth: Level 5</span>
                    </div>
                    <div className="flex items-center gap-3 text-sm text-gray-500 font-mono">
                       <Share2 size={14} />
                       <span>Nodes: {activeCategory.skills.length}</span>
                    </div>
                  </div>

                  {/* Dynamic Background Icon */}
                  <activeTheme.icon className="absolute -bottom-8 -right-8 w-48 h-48 text-white/5 pointer-events-none rotate-12" />
               </div>
            </Reveal>
          </div>

          {/* Right: Skill Modules */}
          <div className="lg:col-span-8 grid grid-cols-1 md:grid-cols-2 gap-4">
            {activeCategory.skills.map((skill, idx) => (
              <Reveal key={`${activeCategory.id}-${idx}`} delay={idx * 0.1} width="100%">
                <div 
                  className={`
                    group relative p-6 rounded-2xl border border-white/5 bg-white/[0.02] backdrop-blur-sm
                    hover:scale-[1.02] transition-all duration-300 cursor-default overflow-hidden
                    ${activeTheme.border} ${activeTheme.bg}
                  `}
                >
                  <div className="flex justify-between items-start mb-4 relative z-10">
                    <h4 className="text-xl font-bold text-white group-hover:text-white transition-colors">
                      {skill.name}
                    </h4>
                    <span className="text-[10px] font-mono text-gray-600 border border-white/10 px-2 py-1 rounded bg-black/50">
                      0{idx + 1}
                    </span>
                  </div>
                  
                  <p className="text-sm text-gray-500 mb-6 font-light leading-relaxed group-hover:text-gray-300 transition-colors">
                    {skill.desc}
                  </p>

                  {/* Tech HUD Footer */}
                  <div className="relative pt-4 border-t border-white/5 flex items-center justify-between">
                     <div className="flex items-center gap-2">
                        <div className={`w-2 h-2 rounded-full ${activeTheme.bg.replace('group-hover:', '')} ${activeTheme.color} animate-pulse`}></div>
                        <span className={`text-[10px] font-mono uppercase tracking-widest ${activeTheme.color} opacity-60 group-hover:opacity-100 transition-opacity`}>
                          Online
                        </span>
                     </div>
                     
                     {/* Decorative Bar Code */}
                     <div className="flex gap-1 opacity-30 group-hover:opacity-60 transition-opacity">
                        <div className="w-px h-3 bg-white"></div>
                        <div className="w-px h-3 bg-white"></div>
                        <div className="w-1 h-3 bg-white"></div>
                        <div className="w-px h-3 bg-white"></div>
                        <div className="w-2 h-3 bg-white"></div>
                     </div>
                  </div>

                  {/* Hover Gradient Overlay */}
                  <div className={`absolute inset-0 bg-gradient-to-br ${activeTheme.gradient} to-transparent opacity-0 group-hover:opacity-5 transition-opacity duration-500 pointer-events-none`}></div>
                </div>
              </Reveal>
            ))}
          </div>

        </div>

      </div>
    </section>
  );
};