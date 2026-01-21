export interface Project {
  id: string;
  title: string;
  category: string;
  description: string;
  image: string;
  tags: string[];
  link?: string;
  details?: {
    role: string;
    timeline: string;
    challenge: string;
    solution: string;
  }
}

export interface Skill {
  name: string;
  icon: string;
  level: number; // 0-100
}

export interface Testimonial {
  name: string;
  role: string;
  company: string;
  content: string;
  avatar: string;
}

export interface ChatMessage {
  role: 'user' | 'model';
  text: string;
  timestamp: Date;
}
