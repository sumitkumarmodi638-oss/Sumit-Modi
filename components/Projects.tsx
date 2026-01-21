import React, { useState } from 'react';
import { ArrowUpRight, X } from 'lucide-react';
import { Reveal } from './ui/Reveal';
import { PROJECTS } from '../constants';
import { Project } from '../types';

export const Projects: React.FC = () => {
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);

  return (
    <section id="work" className="py-32 bg-background border-t border-white/5">
      <div className="container mx-auto px-6 md:px-12">
        <Reveal>
          <h2 className="text-4xl md:text-7xl font-display font-bold mb-20 text-white">Selected Work</h2>
        </Reveal>

        <div className="space-y-32">
          {PROJECTS.map((project, index) => (
            <div key={project.id} className={`flex flex-col ${index % 2 === 1 ? 'md:flex-row-reverse' : 'md:flex-row'} gap-12 md:gap-20 items-center`}>
              
              <div className="w-full md:w-3/5 group cursor-pointer" onClick={() => setSelectedProject(project)}>
                <Reveal width="100%">
                  <div className="relative overflow-hidden rounded-[2rem] aspect-[4/3] shadow-2xl transition-all duration-700 bg-surface border border-white/5">
                    <img 
                      src={project.image} 
                      alt={project.title} 
                      className="object-cover w-full h-full transition-transform duration-1000 ease-[cubic-bezier(0.25,1,0.5,1)] group-hover:scale-105 opacity-80 group-hover:opacity-100"
                    />
                    <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity duration-500 flex items-center justify-center">
                      <span className="px-8 py-4 bg-white text-black rounded-full font-bold transform translate-y-8 group-hover:translate-y-0 transition-transform duration-500">
                        View Case Study
                      </span>
                    </div>
                  </div>
                </Reveal>
              </div>

              <div className="w-full md:w-2/5">
                <Reveal>
                  <span className="text-indigo-400 font-bold text-sm tracking-widest uppercase mb-4 block">{project.category}</span>
                  <h3 className="text-4xl md:text-5xl font-display font-bold mb-6 text-white">{project.title}</h3>
                  <p className="text-xl text-gray-400 mb-8 leading-relaxed font-light">{project.description}</p>
                  <div className="flex flex-wrap gap-2 mb-10">
                    {project.tags.map(tag => (
                      <span key={tag} className="px-4 py-2 bg-white/5 rounded-full text-sm text-gray-300 border border-white/10 font-medium">{tag}</span>
                    ))}
                  </div>
                  <button 
                    onClick={() => setSelectedProject(project)}
                    className="flex items-center gap-3 text-white text-lg hover:text-indigo-400 transition-colors group font-bold"
                  >
                    Read Case Study <ArrowUpRight size={20} className="group-hover:-translate-y-1 group-hover:translate-x-1 transition-transform" />
                  </button>
                </Reveal>
              </div>
            </div>
          ))}
        </div>
      </div>

      {selectedProject && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/90 backdrop-blur-xl" onClick={() => setSelectedProject(null)}></div>
          <div className="bg-[#111] w-full max-w-4xl max-h-[90vh] overflow-y-auto rounded-3xl relative z-10 shadow-2xl animate-in fade-in zoom-in duration-300 border border-white/10">
            <button 
              onClick={() => setSelectedProject(null)}
              className="absolute top-6 right-6 p-3 bg-white/10 hover:bg-white/20 rounded-full transition-colors z-20 text-white"
            >
              <X size={24} />
            </button>
            
            <div className="h-64 md:h-96 w-full relative">
               <img src={selectedProject.image} alt={selectedProject.title} className="w-full h-full object-cover opacity-80" />
               <div className="absolute inset-0 bg-gradient-to-t from-[#111] to-transparent"></div>
               <div className="absolute bottom-8 left-8 md:bottom-12 md:left-12">
                 <h2 className="text-4xl md:text-6xl font-display font-bold text-white">{selectedProject.title}</h2>
               </div>
            </div>

            <div className="p-8 md:p-12 text-gray-300">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12 border-b border-white/10 pb-12">
                <div>
                   <h4 className="text-gray-500 text-xs uppercase tracking-widest mb-2 font-bold">Role</h4>
                   <p className="font-semibold text-lg text-white">{selectedProject.details?.role}</p>
                </div>
                <div>
                   <h4 className="text-gray-500 text-xs uppercase tracking-widest mb-2 font-bold">Timeline</h4>
                   <p className="font-semibold text-lg text-white">{selectedProject.details?.timeline}</p>
                </div>
                <div>
                   <h4 className="text-gray-500 text-xs uppercase tracking-widest mb-2 font-bold">Tools</h4>
                   <p className="font-semibold text-lg text-white">{selectedProject.tags.join(', ')}</p>
                </div>
              </div>

              <div className="space-y-12 max-w-3xl">
                <div>
                  <h3 className="text-2xl font-bold mb-4 text-white">The Challenge</h3>
                  <p className="text-gray-400 leading-relaxed text-xl font-light">{selectedProject.details?.challenge}</p>
                </div>
                <div>
                  <h3 className="text-2xl font-bold mb-4 text-white">The Solution</h3>
                  <p className="text-gray-400 leading-relaxed text-xl font-light">{selectedProject.details?.solution}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </section>
  );
};
