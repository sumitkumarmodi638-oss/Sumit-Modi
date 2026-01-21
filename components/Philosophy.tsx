import React, { useState, useRef, useEffect } from 'react';
import { Brain, ScanEye, Grid3x3, Minimize2, Wind, TrendingUp, ArrowRight, Activity, Aperture, Circle } from 'lucide-react';
import { Reveal } from './ui/Reveal';

const MANIFESTO_POINTS = [
  {
    id: "01",
    title: "Thinking Discipline",
    subtitle: "Context First",
    description: "Design without context is just decoration. I start with the problem, not the pixel.",
    icon: Brain,
    color: "bg-blue-500",
    textAccent: "text-blue-400"
  },
  {
    id: "02",
    title: "Clarity is Craft",
    subtitle: "Radical Reduction",
    description: "Confusion is a failure. I strip away the noise until only the essential signal remains.",
    icon: ScanEye,
    color: "bg-emerald-500",
    textAccent: "text-emerald-400"
  },
  {
    id: "03",
    title: "Systems Scale",
    subtitle: "Atomic Thinking",
    description: "I build living languages, not dead pages. Patterns that evolve with the product.",
    icon: Grid3x3,
    color: "bg-orange-500",
    textAccent: "text-orange-400"
  },
  {
    id: "04",
    title: "Restraint",
    subtitle: "Minimalism",
    description: "Adding is easy. Removing is hard. Every element must fight for its existence.",
    icon: Minimize2,
    color: "bg-white",
    textAccent: "text-gray-200"
  },
  {
    id: "05",
    title: "Kinetic UI",
    subtitle: "Meaningful Motion",
    description: "Motion is the body language of software. It guides, hints, and confirms.",
    icon: Wind,
    color: "bg-purple-500",
    textAccent: "text-purple-400"
  },
  {
    id: "06",
    title: "Impact",
    subtitle: "Measurable Results",
    description: "A beautiful interface that doesn't convert is useless. Design must drive business.",
    icon: TrendingUp,
    color: "bg-pink-500",
    textAccent: "text-pink-400"
  }
];

export const Philosophy: React.FC = () => {
  const targetRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const [scrollProgress, setScrollProgress] = useState(0);
  const [translateX, setTranslateX] = useState(0);
  const [skew, setSkew] = useState(0);
  const lastScrollY = useRef(0);

  // Physics Loop for Skew & Scroll Calculation
  useEffect(() => {
    let animationFrameId: number;

    const updatePhysics = () => {
      if (!targetRef.current || !scrollContainerRef.current) return;

      // 1. Calculate Horizontal Scroll Progress
      const targetRect = targetRef.current.getBoundingClientRect();
      const targetTop = targetRect.top;
      const targetHeight = targetRect.height;
      const viewportHeight = window.innerHeight;

      // The section is 'sticky', so we measure how far we've scrolled through the container height
      // The container is usually much taller than viewport (e.g., 400vh)
      // We want progress 0 to 1
      const scrollDist = targetHeight - viewportHeight;
      // Invert top because it goes negative as we scroll down
      let rawProgress = -targetTop / scrollDist;
      
      // Clamp between 0 and 1
      const progress = Math.max(0, Math.min(1, rawProgress));
      setScrollProgress(progress);

      // 2. Calculate Exact Horizontal Translation
      const trackWidth = scrollContainerRef.current.scrollWidth;
      const winWidth = window.innerWidth;
      // Calculate how much we need to move to see the end
      // We assume the window width is the viewport width
      const maxTranslate = Math.max(0, trackWidth - winWidth);
      const currentTranslate = maxTranslate * progress;
      setTranslateX(-currentTranslate);

      // 3. Calculate Velocity Skew
      const currentScrollY = window.scrollY;
      const velocity = currentScrollY - lastScrollY.current;
      
      // Smooth decay for skew
      setSkew(velocity * 0.15); // Adjust multiplier for sensitivity

      lastScrollY.current = currentScrollY;
      animationFrameId = requestAnimationFrame(updatePhysics);
    };

    window.addEventListener('scroll', updatePhysics); 
    const loop = () => {
       updatePhysics();
       animationFrameId = requestAnimationFrame(loop);
    }
    loop();

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('scroll', updatePhysics);
    };
  }, []);

  return (
    // Height 500vh gives us plenty of scroll room to complete the animation
    <section ref={targetRef} id="philosophy" className="relative h-[500vh] bg-[#030303]">
      
      {/* Sticky Viewport */}
      <div className="sticky top-0 h-screen overflow-hidden flex flex-col justify-center perspective-[1000px]">
        
        {/* Background Elements */}
        <div className="absolute inset-0 pointer-events-none">
           <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[80vw] h-[80vh] bg-indigo-900/10 blur-[120px] rounded-full"></div>
           <div className="absolute top-0 left-0 w-full h-full bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-[0.03]"></div>
        </div>

        {/* Section Title (Fixed Position Layer) */}
        <div className="absolute top-12 left-6 md:left-12 z-20">
           <Reveal>
             <div className="flex items-center gap-3 mb-2">
                <Activity size={16} className="text-indigo-500 animate-pulse" />
                <span className="font-mono text-xs text-indigo-400 uppercase tracking-widest">Core DNA</span>
             </div>
             <h2 className="text-4xl font-display font-bold text-white">The Manifesto</h2>
           </Reveal>
        </div>

        {/* Scroll Indicator (Fades out) */}
        <div 
          className="absolute bottom-12 right-12 z-20 flex items-center gap-4 transition-opacity duration-500"
          style={{ opacity: 1 - scrollProgress * 3 }} 
        >
           <span className="font-mono text-xs text-gray-500 uppercase tracking-widest">Scroll to Explore</span>
           <div className="w-12 h-px bg-gray-700"></div>
           <ArrowRight size={16} className="text-white animate-bounce-x" />
        </div>

        {/* HORIZONTAL TRACK */}
        <div 
           ref={scrollContainerRef}
           className="relative flex items-center gap-12 md:gap-32 px-12 md:px-32 will-change-transform"
           style={{ 
             transform: `translateX(${translateX}px) skewX(${skew}deg)`,
             transition: 'transform 0.1s cubic-bezier(0.2, 0.8, 0.2, 1)' // Slight smoothing
           }}
        >
           
           {/* Intro Block in the track */}
           <div className="min-w-[400px] md:min-w-[600px] flex flex-col justify-center">
              <h3 className="text-6xl md:text-9xl font-display font-bold text-transparent bg-clip-text bg-gradient-to-br from-white via-gray-400 to-gray-800 leading-[0.9] tracking-tighter mb-8">
                 Design <br/>
                 as a <br/>
                 <span className="text-white">System.</span>
              </h3>
              <p className="text-xl text-gray-400 max-w-md leading-relaxed font-light">
                 My philosophy is built on six immutable laws. These aren't just rules; they are the physics of my design universe.
              </p>
           </div>

           {/* Cards */}
           {MANIFESTO_POINTS.map((item, index) => (
             <div 
               key={item.id}
               className="group relative min-w-[320px] md:min-w-[500px] h-[500px] md:h-[650px] bg-[#080808] border border-white/10 rounded-[2rem] p-8 md:p-12 flex flex-col justify-between overflow-hidden transition-all duration-500 hover:border-white/30 hover:-translate-y-4 hover:shadow-2xl"
             >
                {/* Hover Gradient */}
                <div className={`absolute inset-0 opacity-0 group-hover:opacity-10 bg-gradient-to-br ${item.color.replace('bg-', 'from-')} to-transparent transition-opacity duration-700`}></div>
                
                {/* Card Top */}
                <div className="relative z-10 flex justify-between items-start">
                   <span className="text-7xl md:text-9xl font-display font-bold text-white/5 group-hover:text-white/10 transition-colors select-none">
                     {item.id}
                   </span>
                   <div className={`p-4 rounded-full bg-white/5 border border-white/5 text-gray-400 group-hover:text-white group-hover:scale-110 transition-all duration-500 ${item.textAccent}`}>
                      <item.icon size={32} />
                   </div>
                </div>

                {/* Card Content (Parallax Effect Layer) */}
                <div className="relative z-10 transform translate-y-0 group-hover:-translate-y-2 transition-transform duration-500">
                   <h4 className="text-3xl md:text-5xl font-display font-bold text-white mb-2 leading-tight">
                     {item.title}
                   </h4>
                   <span className={`inline-block font-mono text-xs uppercase tracking-widest mb-6 ${item.textAccent}`}>
                     {item.subtitle}
                   </span>
                   <p className="text-lg text-gray-400 font-light leading-relaxed border-l-2 border-white/10 pl-6 group-hover:border-white/30 transition-colors">
                     {item.description}
                   </p>
                </div>

                {/* Decorative Elements */}
                <div className="absolute -bottom-12 -right-12 opacity-5 group-hover:opacity-10 transition-opacity duration-500 pointer-events-none">
                   <Aperture size={200} className="animate-spin-slow" />
                </div>
                
                {/* Tech Line */}
                <div className="absolute top-0 left-8 w-px h-full bg-gradient-to-b from-transparent via-white/5 to-transparent"></div>

             </div>
           ))}

           {/* Outro Block */}
           <div className="min-w-[300px] flex items-center justify-center">
              <div className="w-px h-32 bg-white/20"></div>
              <div className="mx-8 font-mono text-xs text-gray-600 uppercase tracking-[0.3em] rotate-90 whitespace-nowrap">
                 End of Transmission
              </div>
           </div>

        </div>

        {/* Progress Bar (Bottom) */}
        <div className="absolute bottom-0 left-0 w-full h-1 bg-white/5">
           <div 
             className="h-full bg-indigo-500 shadow-[0_0_20px_rgba(99,102,241,0.5)] transition-all duration-75 ease-out"
             style={{ width: `${scrollProgress * 100}%` }}
           ></div>
        </div>

      </div>
    </section>
  );
};