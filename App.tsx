import React from 'react';
import { Navbar } from './components/Navbar';
import { Hero } from './components/Hero';
import { Philosophy } from './components/Philosophy';
import { About } from './components/About';
import { Skills } from './components/Skills';
import { Projects } from './components/Projects';
import { MicroInteractions } from './components/MicroInteractions';
import { Process } from './components/Process';
import { Contact } from './components/Contact';
import { AIChat } from './components/AIChat';

function App() {
  return (
    <div className="bg-background text-text min-h-screen selection:bg-secondary/20 selection:text-black">
      <Navbar />
      <main className="relative z-10">
        <Hero />
        <About />
        <Skills />
        <Philosophy />
        <Projects />
        <MicroInteractions />
        <Process />
      </main>
      <Contact />
      
      {/* AI Assistant Widget */}
      <AIChat />
    </div>
  );
}

export default App;