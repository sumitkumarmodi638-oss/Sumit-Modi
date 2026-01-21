import React, { useState } from 'react';
import { Search, Map, Lightbulb, PenTool, FlaskConical, Rocket, ArrowRight, Activity, FileText, Settings, ChevronRight } from 'lucide-react';
import { Reveal } from './ui/Reveal';
import { PROCESS_STEPS } from '../constants';

const icons = [Search, Map, Lightbulb, PenTool, FlaskConical, Rocket];

export const Process: React.FC = () => {
  const [hoveredStep, setHoveredStep] = useState<number | null>(null);

  return (
    <section id="process" className="py-32 bg-[#030303] text-white relative overflow-hidden">
      
      {/* Background Tech Mesh */}
      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] pointer-events-none"></div>
      
      <div className="container mx-auto px-6 md:px-12 relative z-10">
        
        {/* Section Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-8 mb-20">
          <Reveal>
             <div className="flex items-center gap-3 mb-4">
                <div className="h-px w-8 bg-indigo-500"></div>
                <span className="text-indigo-400 font-mono text-xs uppercase tracking-widest">Workflow Engine</span>
             </div>
             <h2 className="text-5xl md:text-6xl font-display font-bold text-white tracking-tight">
               Operational <br/>
               <span className="text-gray-500">Framework.</span>
             </h2>
          </Reveal>
          
          <Reveal delay={0.2}>
            <p className="text-gray-400 max-w-md text-lg font-light leading-relaxed mb-2">
              My design process is a predictable, scalable system. 
              It transforms ambiguity into shippable value through rigorous iteration.
            </p>
          </Reveal>
        </div>

        {/* The Grid System */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 relative">
          
          {PROCESS_STEPS.map((step, index) => {
            const Icon = icons[index % icons.length];
            const isHovered = hoveredStep === index;

            return (
              <Reveal key={step.id} delay={index * 0.1} width="100%">
                <div 
                  onMouseEnter={() => setHoveredStep(index)}
                  onMouseLeave={() => setHoveredStep(null)}
                  className={`
                    group relative h-full min-h-[380px] bg-[#080808] border rounded-2xl p-8 flex flex-col justify-between overflow-hidden transition-all duration-500
                    ${isHovered ? 'border-indigo-500/50 bg-[#0A0A0A] shadow-[0_0_40px_-10px_rgba(99,102,241,0.15)]' : 'border-white/5 hover:border-white/10'}
                  `}
                >
                  
                  {/* Active Indicator Bar */}
                  <div className={`absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-indigo-500 via-purple-500 to-indigo-500 transform origin-left transition-transform duration-700 ease-out ${isHovered ? 'scale-x-100' : 'scale-x-0'}`}></div>

                  {/* Header Area */}
                  <div className="relative z-10">
                    <div className="flex justify-between items-start mb-6">
                      <div className={`
                        p-3 rounded-xl border transition-all duration-500
                        ${isHovered ? 'bg-indigo-500/10 border-indigo-500/20 text-indigo-400' : 'bg-white/5 border-white/5 text-gray-500'}
                      `}>
                        <Icon size={24} />
                      </div>
                      <span className="font-display font-bold text-6xl text-white/5 group-hover:text-white/10 transition-colors duration-500">
                        {step.id}
                      </span>
                    </div>

                    <h3 className="text-2xl font-bold font-display text-white mb-2 group-hover:translate-x-2 transition-transform duration-300">
                      {step.title}
                    </h3>
                    <div className="flex items-center gap-2 mb-6">
                       <span className={`text-[10px] uppercase tracking-widest font-mono py-1 px-2 rounded border ${isHovered ? 'bg-indigo-500/10 border-indigo-500/20 text-indigo-300' : 'bg-white/5 border-white/5 text-gray-600'}`}>
                         {step.phase}
                       </span>
                    </div>
                    
                    <p className="text-gray-400 font-light leading-relaxed text-sm mb-8 border-l-2 border-white/5 pl-4 group-hover:border-indigo-500/30 transition-colors duration-500">
                      {step.description}
                    </p>
                  </div>

                  {/* Input/Output System Visualization */}
                  <div className="relative z-10 bg-[#050505] rounded-xl p-4 border border-white/5 group-hover:border-white/10 transition-colors">
                     
                     {/* Connector Line Animation */}
                     <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-px h-8 bg-gray-800 hidden md:block group-hover:bg-indigo-500/50 transition-colors"></div>

                     <div className="flex flex-col gap-3">
                        {/* Input */}
                        <div className="flex items-center justify-between text-xs">
                           <div className="flex items-center gap-2 text-gray-500">
                              <FileText size={12} />
                              <span className="font-mono uppercase tracking-wide">Input</span>
                           </div>
                           <span className="text-gray-300 text-right truncate max-w-[120px]">{step.inputs[0]}</span>
                        </div>
                        
                        {/* Divider with animated arrow */}
                        <div className="h-px w-full bg-white/5 relative flex items-center justify-center">
                           <div className={`p-1 rounded-full bg-[#080808] border border-white/10 text-gray-600 transition-all duration-500 ${isHovered ? 'text-indigo-400 border-indigo-500/30 rotate-90 md:rotate-0' : ''}`}>
                              <ChevronRight size={10} />
                           </div>
                        </div>

                        {/* Output */}
                        <div className="flex items-center justify-between text-xs">
                           <div className="flex items-center gap-2 text-gray-500">
                              <Activity size={12} />
                              <span className="font-mono uppercase tracking-wide">Output</span>
                           </div>
                           <span className={`text-right truncate max-w-[120px] transition-colors duration-300 ${isHovered ? 'text-emerald-400' : 'text-gray-300'}`}>
                             {step.outputs[0]}
                           </span>
                        </div>
                     </div>
                  </div>

                  {/* Tech Overlay Details */}
                  <div className="absolute bottom-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none">
                     <Settings size={80} className="text-white/[0.02] animate-spin-slow" />
                  </div>

                </div>
              </Reveal>
            );
          })}
        </div>

        {/* Bottom Connection Line */}
        <Reveal>
           <div className="mt-16 flex items-center justify-center gap-4 opacity-30">
              <div className="h-px w-full max-w-xs bg-gradient-to-r from-transparent via-white to-transparent"></div>
              <div className="text-[10px] font-mono uppercase tracking-widest text-white whitespace-nowrap">End of Protocol</div>
              <div className="h-px w-full max-w-xs bg-gradient-to-r from-transparent via-white to-transparent"></div>
           </div>
        </Reveal>

      </div>
    </section>
  );
};
