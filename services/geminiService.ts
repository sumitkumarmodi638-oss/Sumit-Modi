import { GoogleGenAI } from "@google/genai";
import { PERSONAL_INFO, SKILLS, PROJECTS, ABOUT_TEXT } from '../constants';

const apiKey = process.env.API_KEY || '';
const ai = new GoogleGenAI({ apiKey });

const SYSTEM_INSTRUCTION = `
You are the AI portfolio assistant for ${PERSONAL_INFO.name}, a ${PERSONAL_INFO.role}.
Your goal is to answer questions about Alex's background, skills, and work in a professional, creative, and concise manner.

Here is the context about Alex:
BIO: ${ABOUT_TEXT}
SKILLS: ${SKILLS.map(s => s.name).join(', ')}
PROJECTS: ${PROJECTS.map(p => `${p.title} (${p.description})`).join('; ')}

Tone: Professional, slightly witty, helpful, and concise (under 50 words usually).
If asked about contact, provide: ${PERSONAL_INFO.email}.
If asked something irrelevant to the portfolio, politely steer back to design topics.
`;

export const generateAIResponse = async (userMessage: string): Promise<string> => {
  if (!apiKey) {
    return "I'm currently in offline mode (API Key missing). But I'd love to tell you that Alex is great!";
  }

  try {
    const response = await ai.models.generateContent({
      model: 'gemini-3-flash-preview',
      contents: [
        {
          role: 'user',
          parts: [{ text: userMessage }]
        }
      ],
      config: {
        systemInstruction: SYSTEM_INSTRUCTION,
      }
    });

    return response.text || "I'm thinking...";
  } catch (error) {
    console.error("Gemini API Error:", error);
    return "I encountered a momentary glitch in the matrix. Please try again.";
  }
};
