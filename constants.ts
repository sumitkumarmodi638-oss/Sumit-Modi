import { Project, Skill, Testimonial } from './types';

export const PERSONAL_INFO = {
  name: "Sumit Modi",
  role: "Principal Product Designer",
  tagline: "Shaping the future of digital interaction.",
  email: "sumitkumarmodi638@gmail.com",
  phone: "+91 73659 77561",
  socials: {
    linkedin: "#",
    dribbble: "#",
    twitter: "#"
  }
};

export const ABOUT_TEXT = `
I build digital products that feel inevitable. 
My approach is rooted in structural clarity—removing the non-essential to reveal the core utility.
I believe that great software should be as intuitive as a physical tool and as inspiring as a work of art.
Currently obsessing over micro-interactions, typography, and the space between elements.
`;

export const SKILL_CATEGORIES = [
  {
    id: "design",
    title: "Core Discipline",
    subtitle: "The craft of making",
    icon: "Layout",
    skills: [
      { name: "UI Architecture", desc: "Structuring complex interfaces for maximum clarity." },
      { name: "Product Strategy", desc: "Defining the 'what' and 'why' before the 'how'." },
      { name: "Design Systems", desc: "Building scalable languages for product teams." },
      { name: "Visual Identity", desc: "Creating distinct visual languages." },
      { name: "Motion Design", desc: "Using time as a dimension of usability." }
    ]
  },
  {
    id: "strategy",
    title: "Strategic Foundation",
    subtitle: "The logic behind the pixels",
    icon: "Brain",
    skills: [
      { name: "User Research", desc: "Uncovering latent needs through observation." },
      { name: "Information Arch", desc: "Organizing chaos into structure." },
      { name: "Workshop Facilitation", desc: "Aligning stakeholders through co-creation." },
      { name: "Data Analysis", desc: "Informing decisions with behavioral metrics." },
      { name: "Accessibility", desc: "Designing for the full spectrum of human ability." }
    ]
  },
  {
    id: "execution",
    title: "Technical Translation",
    subtitle: "Bridging design and code",
    icon: "Zap",
    skills: [
      { name: "Rapid Prototyping", desc: "Validating ideas at the speed of thought." },
      { name: "Front-End Logic", desc: "Understanding the constraints of the medium." },
      { name: "Design Ops", desc: "Optimizing the workflow of design teams." },
      { name: "Design QA", desc: "Ensuring implementation matches intent." },
      { name: "Documentation", desc: "Writing clear specs for engineering partners." }
    ]
  }
];

export const SKILLS: Skill[] = [
  { name: "Product Strategy", icon: "Zap", level: 95 },
  { name: "Visual Design", icon: "Grid", level: 98 },
  { name: "Prototyping", icon: "Smartphone", level: 92 },
  { name: "Systems Thinking", icon: "Users", level: 90 },
  { name: "User Research", icon: "Zap", level: 85 },
  { name: "Motion", icon: "Code", level: 88 },
];

export const MICRO_INTERACTIONS_DATA = [
  {
    id: "exp-01",
    title: "Kinetic Typography",
    category: "Visual Tension",
    userStory: "As a viewer, I want type to feel alive and responsive.",
    context: "Static text fails to convey emotion. Variable fonts allow for expressive transitions.",
    outcome: "Higher engagement and brand recall through dynamic storytelling.",
    tech: "Variable Fonts / JS"
  },
  {
    id: "exp-02",
    title: "Spatial Navigation",
    category: "Information Architecture",
    userStory: "As a user, I want to explore content without losing my place.",
    context: "Traditional pagination disrupts flow. Z-axis navigation creates continuity.",
    outcome: "Seamless exploration of deep content hierarchies.",
    tech: "WebGL / React Three Fiber"
  },
  {
    id: "exp-03",
    title: "Haptic Feedback",
    category: "Sensory Design",
    userStory: "As a user, I want confirmation that feels physical.",
    context: "Visual cues aren't always enough. Haptics provide a tactile confirmation layer.",
    outcome: "Increased confidence in user actions on mobile devices.",
    tech: "Vibration API / Framer Motion"
  }
];

export const PROJECTS: Project[] = [
  {
    id: "1",
    title: "Lumina Finance",
    category: "Fintech Platform",
    description: "A complete redesign of an institutional trading platform, reducing cognitive load for high-frequency traders.",
    image: "https://picsum.photos/800/600?random=10",
    tags: ["Product Design", "React", "Data Visualization"],
    details: {
      role: "Lead Designer",
      timeline: "6 Months",
      challenge: "Traders were missing critical signals due to visual clutter.",
      solution: "Implemented a 'progressive disclosure' system that highlights anomalies."
    }
  },
  {
    id: "2",
    title: "Aether Wellness",
    category: "iOS Application",
    description: "A mindfulness app that uses generative audio and biofeedback to personalize meditation sessions.",
    image: "https://picsum.photos/800/600?random=11",
    tags: ["Mobile", "Sound Design", "Prototyping"],
    details: {
      role: "Product Designer",
      timeline: "4 Months",
      challenge: "Most meditation apps feel generic and static.",
      solution: "Created a generative visual engine that responds to user breath patterns."
    }
  },
  {
    id: "3",
    title: "Structura Design System",
    category: "Design Operations",
    description: "A multi-brand design system serving 4 distinct products with a shared underlying logic.",
    image: "https://picsum.photos/800/600?random=12",
    tags: ["Systems", "Documentation", "Tokens"],
    details: {
      role: "Systems Architect",
      timeline: "8 Months",
      challenge: "Fragmentation across products led to slow development cycles.",
      solution: "Unified the visual language with a token-based theming engine."
    }
  }
];

export const PROCESS_STEPS = [
  { 
    id: "01",
    title: "Inquiry", 
    phase: "Understanding",
    description: "We start by asking the right questions. I immerse myself in the problem space, interviewing users and auditing existing systems to find the root cause.",
    inputs: ["Stakeholder Interviews", "Heuristic Audit", "Market Research"],
    outputs: ["Research Report", "Opportunity Map", "Success Metrics"]
  },
  { 
    id: "02",
    title: "Structure", 
    phase: "Definition",
    description: "Before pixels, we need a plan. I map out user flows and information architecture to ensure the foundation is solid and scalable.",
    inputs: ["User Journeys", "Card Sorting", "Flow Diagrams"],
    outputs: ["Site Map", "User Flows", "Wireframes"]
  },
  { 
    id: "03",
    title: "Exploration", 
    phase: "Ideation",
    description: "This is where divergent thinking happens. I sketch, prototype, and explore multiple directions to find the most elegant solution.",
    inputs: ["Sketching", "Moodboarding", "Crazy 8s"],
    outputs: ["Concept Prototypes", "Visual Direction", "Feasibility Check"]
  },
  { 
    id: "04",
    title: "Refinement", 
    phase: "Design",
    description: "Turning concepts into reality. I apply the visual language, refine interactions, and ensure every detail serves a purpose.",
    inputs: ["UI Design", "Motion Study", "Accessibility Check"],
    outputs: ["High-Fidelity Mocks", "Interactive Prototype", "Design Specs"]
  },
  { 
    id: "05",
    title: "Validation", 
    phase: "Testing",
    description: "We don't guess; we test. I put prototypes in front of real users to validate our assumptions and refine the experience.",
    inputs: ["Usability Testing", "A/B Testing", "Feedback Loops"],
    outputs: ["Validation Report", "Iterated Designs", "Confidence"]
  },
  { 
    id: "06",
    title: "Handoff", 
    phase: "Delivery",
    description: "Execution is everything. I work closely with engineering to ensure the final build matches the design intent pixel for pixel.",
    inputs: ["Redlines", "Asset Export", "Dev Collaboration"],
    outputs: ["Production Code", "Design QA", "Launch"]
  }
];