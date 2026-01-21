import React, { useState, useRef } from 'react';
import { MousePointer2, Check, Loader2, CreditCard, X, Maximize2, Sparkles, Fingerprint, RefreshCcw, Sliders, Type, Globe, Smartphone } from 'lucide-react';
import { Reveal } from './ui/Reveal';
import { MICRO_INTERACTIONS_DATA } from '../constants';

// --- DEMO COMPONENTS ---
// Kept logic similar but refined visuals for the "Lab" aesthetic

const MagneticDemo = () => {
  const btnRef = useRef<HTMLButtonElement>(null);
  const [position, setPosition] = useState({ x: 0, y: 0 });

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!btnRef.current) return;
    const { left, top, width, height } = btnRef.current.getBoundingClientRect();
    const centerX = left + width / 2;
    const centerY = top + height / 2;
    const x = (e.clientX - centerX) * 0.5; // Stronger pull
    const y = (e.clientY - centerY) * 0.5;
    setPosition({ x, y });
  };

  const handleMouseLeave = () => {
    setPosition({ x: 0, y: 0 });
  };

  return (
    <div className="flex flex-col items-center gap-8">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-white/5 to-transparent pointer-events-none"></div>
      <button
        ref={btnRef}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        style={{ transform: `translate(${position.x}px, ${position.y}px)` }}
        className="relative group bg-white text-black font-bold py-6 px-12 rounded-full transition-all duration-100 ease-out cursor-none z-10 hover:scale-110"
      >
        <span className="relative z-10 flex items-center gap-3 text-lg font-mono uppercase tracking-tighter">
          Magnetic <MousePointer2 size={18} className="group-hover:-rotate-12 transition-transform" />
        </span>
      </button>
      <div className="text-xs font-mono text-gray-500 text-center mt-8 opacity-50">
        CURSOR PROXIMITY SENSOR ACTIVE
      </div>
    </div>
  );
};

const MorphDemo = () => {
  const [state, setState] = useState<'idle' | 'loading' | 'success'>('idle');

  const handleClick = () => {
    if (state !== 'idle') return;
    setState('loading');
    setTimeout(() => {
      setState('success');
      setTimeout(() => setState('idle'), 2500);
    }, 1500);
  };

  return (
    <div className="flex flex-col items-center gap-8">
      <button
        onClick={handleClick}
        className={`
          relative h-16 flex items-center justify-center font-bold text-white transition-all duration-500 ease-[cubic-bezier(0.23,1,0.32,1)] overflow-hidden border border-indigo-500/30
          ${state === 'idle' ? 'w-64 bg-indigo-600/20 hover:bg-indigo-600/40 rounded-lg' : ''}
          ${state === 'loading' ? 'w-16 bg-transparent border-white/20 rounded-full' : ''}
          ${state === 'success' ? 'w-16 bg-emerald-500/20 border-emerald-500 text-emerald-400 rounded-full' : ''}
        `}
      >
        <span className={`absolute transition-all duration-300 font-mono text-sm tracking-widest uppercase ${state === 'idle' ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
          Initialize
        </span>
        <span className={`absolute transition-all duration-300 ${state === 'loading' ? 'opacity-100 scale-100' : 'opacity-0 scale-50'}`}>
          <Loader2 className="animate-spin text-indigo-400" size={24} />
        </span>
        <span className={`absolute transition-all duration-500 ${state === 'success' ? 'opacity-100 scale-100 rotate-0' : 'opacity-0 scale-50 -rotate-90'}`}>
          <Check size={24} />
        </span>
      </button>
      <div className="flex gap-4 text-[10px] font-mono text-gray-600 uppercase">
        <span className={state === 'idle' ? 'text-indigo-400' : ''}>State: Idle</span>
        <span className={state === 'loading' ? 'text-white' : ''}>State: Process</span>
        <span className={state === 'success' ? 'text-emerald-400' : ''}>State: Done</span>
      </div>
    </div>
  );
};

const TiltDemo = () => {
  const cardRef = useRef<HTMLDivElement>(null);
  const [rotation, setRotation] = useState({ x: 0, y: 0 });

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!cardRef.current) return;
    const { left, top, width, height } = cardRef.current.getBoundingClientRect();
    const centerX = left + width / 2;
    const centerY = top + height / 2;
    const rotateX = ((e.clientY - centerY) / (height / 2)) * -25; 
    const rotateY = ((e.clientX - centerX) / (width / 2)) * 25;
    setRotation({ x: rotateX, y: rotateY });
  };

  const handleMouseLeave = () => {
    setRotation({ x: 0, y: 0 });
  };

  return (
    <div className="perspective-[1200px] flex flex-col items-center">
      <div
        ref={cardRef}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        style={{ transform: `rotateX(${rotation.x}deg) rotateY(${rotation.y}deg)` }}
        className="w-80 h-52 bg-[#1a1a1a] rounded-xl border border-white/10 p-6 flex flex-col justify-between shadow-2xl transition-transform duration-100 ease-linear cursor-default relative overflow-hidden group"
      >
        {/* Holographic Sheen */}
        <div 
          className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/10 to-transparent pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-300 z-20 mix-blend-overlay"
          style={{ transform: `translateX(${-rotation.y * 4}px) translateY(${-rotation.x * 4}px)` }}
        ></div>

        <div className="flex justify-between items-start relative z-10">
          <div className="w-12 h-8 bg-gradient-to-br from-yellow-500/20 to-yellow-600/10 rounded border border-yellow-500/30 backdrop-blur-md"></div>
          <CreditCard className="text-gray-500" size={20} />
        </div>
        
        <div className="relative z-10">
          <div className="text-gray-400 font-mono text-sm tracking-[0.2em] mb-4">•••• 8829</div>
          <div className="flex justify-between items-end border-t border-white/5 pt-4">
            <div className="text-[10px] text-gray-500 font-mono uppercase">Card Holder<br/><span className="text-gray-300">Sumit Modi</span></div>
            <div className="text-[10px] text-gray-500 font-mono uppercase text-right">Expires<br/><span className="text-gray-300">12/30</span></div>
          </div>
        </div>
      </div>
      <div className="mt-8 flex items-center gap-2 text-[10px] font-mono text-gray-600">
        <RefreshCcw size={10} className="animate-spin-slow" />
        GYROSCOPIC SIMULATION
      </div>
    </div>
  );
};

const PREVIEW_ICONS: Record<string, React.ElementType> = {
  "exp-01": Type,
  "exp-02": Globe,
  "exp-03": Smartphone
};

export const MicroInteractions: React.FC = () => {
  const [activeExp, setActiveExp] = useState<number | null>(null);

  const demoComponents: Record<string, React.ReactNode> = {
    "exp-01": <MagneticDemo />,
    "exp-02": <MorphDemo />,
    "exp-03": <TiltDemo />
  };

  return (
    <section id="interactions" className="py-32 bg-[#050505] text-white relative overflow-hidden border-t border-white/5">
      
      {/* Technical Background Grid */}
      <div className="absolute inset-0 bg-grid-pattern opacity-20 pointer-events-none"></div>

      <div className="container mx-auto px-6 md:px-12 relative z-10">
        
        {/* Header Section */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-12 mb-24 border-b border-white/10 pb-12">
          <Reveal>
            <div className="inline-flex items-center gap-2 mb-6 px-3 py-1 bg-indigo-500/10 border border-indigo-500/20 rounded-full text-indigo-400 font-mono text-xs tracking-widest uppercase">
              <Sparkles size={12} />
              <span>R&D Lab 04</span>
            </div>
            <h2 className="text-5xl md:text-7xl font-display font-bold text-white tracking-tight">
              Motion <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400">Experiments</span>
            </h2>
          </Reveal>
          
          <Reveal delay={0.2}>
            <div className="max-w-md">
              <p className="text-gray-400 text-lg leading-relaxed font-light mb-4">
                A collection of interactive prototypes exploring the physics of digital interfaces.
              </p>
              <div className="flex gap-4 text-xs font-mono text-gray-600 uppercase tracking-widest">
                <span>React</span>
                <span>•</span>
                <span>Framer Motion</span>
                <span>•</span>
                <span>WebGL</span>
              </div>
            </div>
          </Reveal>
        </div>

        {/* Technical Grid Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {MICRO_INTERACTIONS_DATA.map((item, index) => {
            const PreviewIcon = PREVIEW_ICONS[item.id] || Sparkles;

            return (
              <Reveal key={item.id} delay={index * 0.1} width="100%">
                <div 
                  onClick={() => setActiveExp(index)}
                  className="group relative h-[420px] bg-[#0A0A0A] border border-white/5 hover:border-indigo-500/50 transition-all duration-500 cursor-pointer overflow-hidden flex flex-col"
                >
                  {/* HUD Corners */}
                  <div className="absolute top-0 left-0 w-2 h-2 border-t border-l border-white/20 group-hover:border-indigo-500 transition-colors"></div>
                  <div className="absolute top-0 right-0 w-2 h-2 border-t border-r border-white/20 group-hover:border-indigo-500 transition-colors"></div>
                  <div className="absolute bottom-0 left-0 w-2 h-2 border-b border-l border-white/20 group-hover:border-indigo-500 transition-colors"></div>
                  <div className="absolute bottom-0 right-0 w-2 h-2 border-b border-r border-white/20 group-hover:border-indigo-500 transition-colors"></div>

                  {/* Card Header */}
                  <div className="p-6 border-b border-white/5 flex justify-between items-start">
                    <span className="font-mono text-xs text-gray-600 group-hover:text-indigo-400 transition-colors tracking-widest">
                      {item.id.toUpperCase()}
                    </span>
                    <div className="p-2 rounded-full border border-white/10 text-gray-500 group-hover:text-white group-hover:border-indigo-500 group-hover:bg-indigo-500/10 transition-all">
                      <Maximize2 size={14} />
                    </div>
                  </div>

                  {/* Visual Preview (Abstract with Icon) */}
                  <div className="flex-1 relative flex items-center justify-center bg-grid-pattern group-hover:bg-[#0f0f0f] transition-colors">
                    <div className="absolute inset-0 bg-gradient-to-t from-[#0A0A0A] to-transparent z-10"></div>
                    
                    {/* Glowing center indicator */}
                    <div className="w-32 h-32 rounded-full border border-white/5 flex items-center justify-center group-hover:scale-110 transition-transform duration-700 bg-white/[0.02]">
                       <PreviewIcon 
                         size={48} 
                         strokeWidth={1}
                         className="text-gray-600 group-hover:text-indigo-400 transition-colors duration-500 opacity-50 group-hover:opacity-100" 
                       />
                       <div className="absolute inset-0 border border-white/5 rounded-full animate-ping opacity-0 group-hover:opacity-20"></div>
                    </div>
                  </div>

                  {/* Card Footer */}
                  <div className="p-8 relative z-20 bg-[#0A0A0A]">
                    <div className="text-indigo-500 text-[10px] font-mono mb-3 opacity-0 group-hover:opacity-100 transform translate-y-2 group-hover:translate-y-0 transition-all duration-300 uppercase tracking-widest font-bold flex items-center gap-2">
                      <div className="w-1 h-1 bg-indigo-500 rounded-full"></div>
                      {item.category}
                    </div>
                    <h3 className="text-2xl font-display font-bold text-white mb-2 group-hover:text-indigo-100 transition-colors">{item.title}</h3>
                    <p className="text-sm text-gray-500 font-light line-clamp-2">
                      {item.userStory}
                    </p>
                  </div>
                </div>
              </Reveal>
            );
          })}
        </div>

        {/* Full Screen Sandbox Modal */}
        {activeExp !== null && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-0 md:p-6 animate-in fade-in duration-300">
            {/* Backdrop */}
            <div className="absolute inset-0 bg-black/95 backdrop-blur-xl" onClick={() => setActiveExp(null)}></div>
            
            <div className="relative w-full max-w-[1400px] h-full md:h-[90vh] bg-[#050505] md:border border-white/10 md:rounded-3xl overflow-hidden flex flex-col md:flex-row shadow-2xl">
              
              {/* Close Button */}
              <button 
                onClick={() => setActiveExp(null)}
                className="absolute top-6 right-6 z-50 p-3 bg-black/50 hover:bg-white/10 border border-white/10 rounded-full text-white transition-colors backdrop-blur-md"
              >
                <X size={20} />
              </button>

              {/* Left: Interaction Canvas */}
              <div className="w-full md:w-3/4 h-[60%] md:h-full bg-[#080808] relative flex flex-col items-center justify-center border-b md:border-b-0 md:border-r border-white/10 overflow-hidden">
                 {/* Grid Background */}
                 <div className="absolute inset-0 opacity-20 bg-grid-pattern"></div>
                 
                 {/* Interactive Component */}
                 <div className="relative z-20 scale-100 md:scale-125">
                   {demoComponents[MICRO_INTERACTIONS_DATA[activeExp].id]}
                 </div>

                 {/* Canvas UI Overlays */}
                 <div className="absolute top-8 left-8 flex items-center gap-3 text-gray-500 font-mono text-xs">
                   <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                   <span>LIVE ENVIRONMENT</span>
                 </div>
                 
                 <div className="absolute bottom-8 right-8 flex gap-4 text-[10px] font-mono text-gray-600 uppercase">
                    <div>X: 1920</div>
                    <div>Y: 1080</div>
                    <div>FPS: 60</div>
                 </div>
              </div>

              {/* Right: Technical Specs */}
              <div className="w-full md:w-1/4 h-[40%] md:h-full bg-[#050505] p-8 md:p-10 overflow-y-auto border-l border-white/5">
                <div className="flex flex-col h-full">
                  <div className="mb-auto">
                    <span className="inline-block px-2 py-1 bg-indigo-500/10 text-indigo-400 font-mono text-[10px] tracking-widest mb-6 uppercase border border-indigo-500/20 rounded">
                      {MICRO_INTERACTIONS_DATA[activeExp].id}
                    </span>
                    
                    <h2 className="text-3xl font-display font-bold text-white mb-2">
                      {MICRO_INTERACTIONS_DATA[activeExp].title}
                    </h2>
                    <p className="text-sm text-gray-500 font-mono mb-8 uppercase tracking-wider">
                      {MICRO_INTERACTIONS_DATA[activeExp].category}
                    </p>

                    <div className="space-y-8">
                      <div className="relative pl-4 border-l border-white/10">
                        <h4 className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-2 flex items-center gap-2">
                          <Fingerprint size={10} /> User Objective
                        </h4>
                        <p className="text-sm text-gray-300 font-light leading-relaxed">
                          {MICRO_INTERACTIONS_DATA[activeExp].userStory}
                        </p>
                      </div>
                      
                      <div className="relative pl-4 border-l border-white/10">
                        <h4 className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-2 flex items-center gap-2">
                          <Sliders size={10} /> Technical Execution
                        </h4>
                        <p className="text-sm text-gray-400 font-light leading-relaxed mb-3">
                          {MICRO_INTERACTIONS_DATA[activeExp].context}
                        </p>
                        <div className="text-xs font-mono text-indigo-400">
                          Stack: {MICRO_INTERACTIONS_DATA[activeExp].tech}
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="mt-8 pt-8 border-t border-white/10">
                    <div className="text-[10px] text-gray-600 font-mono uppercase text-center">
                      Interaction Design System v2.0
                    </div>
                  </div>
                </div>
              </div>

            </div>
          </div>
        )}
    </section>
  );
};