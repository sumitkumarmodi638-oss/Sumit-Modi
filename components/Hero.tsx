import React, { useEffect, useState, useRef } from 'react';
import { ArrowRight } from 'lucide-react';

export const Hero: React.FC = () => {
  const [loaded, setLoaded] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const buttonRef = useRef<HTMLAnchorElement>(null);

  useEffect(() => {
    const timer = setTimeout(() => setLoaded(true), 200);
    return () => clearTimeout(timer);
  }, []);

  // Universe Animation Effect
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let width = canvas.width = window.innerWidth;
    let height = canvas.height = window.innerHeight;

    const stars: { x: number; y: number; z: number; o: number }[] = [];
    const numStars = 1500;
    const centerX = width / 2;
    const centerY = height / 2;
    const focalLength = width * 0.5; // Adjust field of view

    // Initialize stars
    for (let i = 0; i < numStars; i++) {
      stars.push({
        x: Math.random() * width - centerX,
        y: Math.random() * height - centerY,
        z: Math.random() * width,
        o: Math.random(),
      });
    }

    let animationFrameId: number;

    const animate = () => {
      ctx.fillStyle = "#030303";
      ctx.fillRect(0, 0, width, height);

      stars.forEach((star) => {
        // Move star closer
        star.z -= 0.5; // Speed of the universe flow

        // Reset star if it passes the camera
        if (star.z <= 0) {
          star.z = width;
          star.x = Math.random() * width - centerX;
          star.y = Math.random() * height - centerY;
        }

        // Projection
        const scale = focalLength / star.z;
        const x = centerX + star.x * scale;
        const y = centerY + star.y * scale;
        const size = Math.max(0.1, scale * 1.5); // Star size based on depth

        const opacity = (1 - star.z / width) * star.o;

        if (x > 0 && x < width && y > 0 && y < height) {
          ctx.beginPath();
          ctx.fillStyle = `rgba(255, 255, 255, ${opacity})`;
          ctx.arc(x, y, size, 0, Math.PI * 2);
          ctx.fill();
        }
      });

      animationFrameId = requestAnimationFrame(animate);
    };

    animate();

    const handleResize = () => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };

    window.addEventListener('resize', handleResize);
    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  const handleMouseMove = (e: React.MouseEvent) => {
    // Magnetic button logic
    if (buttonRef.current) {
      const { left, top, width, height } = buttonRef.current.getBoundingClientRect();
      const centerX = left + width / 2;
      const centerY = top + height / 2;
      
      const dist = Math.sqrt(Math.pow(e.clientX - centerX, 2) + Math.pow(e.clientY - centerY, 2));
      
      if (dist < 100) {
        const x = e.clientX - centerX;
        const y = e.clientY - centerY;
        buttonRef.current.style.transform = `translate(${x * 0.2}px, ${y * 0.2}px)`;
      } else {
        buttonRef.current.style.transform = 'translate(0px, 0px)';
      }
    }
  };

  return (
    <section 
      onMouseMove={handleMouseMove}
      className="relative h-screen w-full bg-[#030303] flex flex-col justify-center items-center overflow-hidden selection:bg-indigo-500/30"
    >
      
      {/* --- 1. UNIVERSE BACKGROUND LAYER --- */}
      <canvas
        ref={canvasRef}
        className="absolute inset-0 z-0 opacity-60"
      />
      
      {/* Vignette Overlay for Depth */}
      <div className="absolute inset-0 z-0 bg-[radial-gradient(circle_at_center,transparent_0%,#030303_90%)] pointer-events-none"></div>

      {/* --- 2. CONTENT LAYER --- */}
      <div className="container mx-auto px-6 md:px-12 relative z-10 flex flex-col items-center text-center max-w-5xl">
        
        {/* Badge */}
        <div 
          className={`mb-10 transition-all duration-1000 ease-premium ${
            loaded ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
          }`}
        >
          <div className="inline-flex items-center gap-3 px-4 py-1.5 rounded-full border border-white/10 bg-white/[0.03] backdrop-blur-md shadow-[0_0_20px_rgba(0,0,0,0.5)]">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
            </span>
            <span className="text-[10px] font-mono tracking-[0.2em] text-gray-300 uppercase">
              Sumit Modi • Principal Designer
            </span>
          </div>
        </div>

        {/* Headline */}
        <h1 className="font-display font-semibold text-white tracking-tighter leading-[1.0] mb-10 mix-blend-lighten">
          <div className="overflow-hidden">
            <span className={`block text-6xl md:text-8xl lg:text-9xl transition-transform duration-[1.5s] ease-[cubic-bezier(0.2,1,0.2,1)] ${loaded ? 'translate-y-0' : 'translate-y-[110%]'}`}>
              Crafting digital
            </span>
          </div>
          
          <div className="overflow-hidden flex justify-center gap-4 md:gap-6 flex-wrap mt-2">
             <span className={`block text-6xl md:text-8xl lg:text-9xl text-gray-500 transition-transform duration-[1.5s] delay-100 ease-[cubic-bezier(0.2,1,0.2,1)] ${loaded ? 'translate-y-0' : 'translate-y-[110%]'}`}>
              experiences
            </span>
             <div className={`transition-all duration-[1.5s] delay-300 ease-[cubic-bezier(0.2,1,0.2,1)] ${loaded ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-12'}`}>
                <span className="font-serif italic font-thin text-5xl md:text-7xl lg:text-8xl text-indigo-400">
                  with soul.
                </span>
             </div>
          </div>
        </h1>

        {/* Subtext */}
        <p 
          className={`text-lg md:text-xl text-gray-400 leading-relaxed max-w-2xl mx-auto mb-16 font-light transition-all duration-1000 delay-500 ease-premium ${
            loaded ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
          }`}
        >
          I design systems that feel <span className="text-white font-medium">inevitable</span>. 
          Merging structural clarity with emotional resonance to build products that last.
        </p>

        {/* CTA */}
        <div 
          className={`transition-all duration-1000 delay-700 ease-premium ${
            loaded ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
          }`}
        >
          <a 
            ref={buttonRef}
            href="#work" 
            className="group relative inline-flex items-center justify-center px-10 py-5 bg-white text-black font-bold rounded-full overflow-hidden transition-all duration-200 ease-out hover:scale-105 active:scale-95 z-20"
          >
            <div className="absolute inset-0 bg-gradient-to-tr from-indigo-100 to-white opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
            <span className="relative flex items-center gap-3 text-sm tracking-widest uppercase font-mono">
              Explore Work 
              <ArrowRight size={14} className="transition-transform duration-300 group-hover:translate-x-1" />
            </span>
          </a>
        </div>

      </div>

      {/* Scroll Indicator */}
      <div 
        className={`absolute bottom-12 left-0 right-0 flex flex-col items-center gap-4 transition-opacity duration-1000 delay-[1.2s] ${
          loaded ? 'opacity-100' : 'opacity-0'
        }`}
      >
        <div className="w-[1px] h-16 bg-gradient-to-b from-transparent via-gray-700 to-transparent"></div>
      </div>

    </section>
  );
};