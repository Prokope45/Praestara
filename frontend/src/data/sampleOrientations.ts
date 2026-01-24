// Sample data for orientations until backend is implemented

import { OrientationPublic } from "../types/orientations"

export const sampleOrientations: OrientationPublic[] = [
  {
    id: "1",
    title: "I want to be a great father",
    description: "Building the qualities and habits that make a loving, present, and supportive father",
    createdAt: "2026-01-01T00:00:00Z",
    updatedAt: "2026-01-15T00:00:00Z",
    notes: "Focus on being present and patient with my children",
    traits: [
      {
        id: "trait-1-1",
        name: "Patience",
        value: 65,
        description: "Ability to remain calm and understanding",
      },
      {
        id: "trait-1-2",
        name: "Presence",
        value: 70,
        description: "Being mentally and emotionally available",
      },
      {
        id: "trait-1-3",
        name: "Playfulness",
        value: 80,
        description: "Engaging in fun activities and play",
      },
      {
        id: "trait-1-4",
        name: "Guidance",
        value: 60,
        description: "Providing wisdom and direction",
      },
      {
        id: "trait-1-5",
        name: "Support",
        value: 75,
        description: "Emotional and practical support",
      },
      {
        id: "trait-1-6",
        name: "Communication",
        value: 55,
        description: "Open and honest dialogue",
      },
    ],
  },
  {
    id: "2",
    title: "I want to be a skilled neuroscientist",
    description: "Developing the knowledge and skills to excel in neuroscience research",
    createdAt: "2026-01-05T00:00:00Z",
    updatedAt: "2026-01-20T00:00:00Z",
    notes: "Currently focusing on learning epistemology and research methodology",
    traits: [
      {
        id: "trait-2-1",
        name: "Research Skills",
        value: 70,
        description: "Experimental design and methodology",
      },
      {
        id: "trait-2-2",
        name: "Epistemology",
        value: 50,
        description: "Understanding how we know what we know",
      },
      {
        id: "trait-2-3",
        name: "Psychology",
        value: 65,
        description: "Understanding human behavior and cognition",
      },
      {
        id: "trait-2-4",
        name: "Data Analysis",
        value: 75,
        description: "Statistical and computational analysis",
      },
      {
        id: "trait-2-5",
        name: "Critical Thinking",
        value: 80,
        description: "Evaluating evidence and arguments",
      },
      {
        id: "trait-2-6",
        name: "Communication",
        value: 60,
        description: "Presenting findings clearly",
      },
    ],
  },
  {
    id: "3",
    title: "I want to be a compassionate leader",
    description: "Leading with empathy while driving results and inspiring others",
    createdAt: "2026-01-10T00:00:00Z",
    updatedAt: "2026-01-22T00:00:00Z",
    notes: "Working on balancing empathy with accountability",
    traits: [
      {
        id: "trait-3-1",
        name: "Empathy",
        value: 85,
        description: "Understanding others' perspectives",
      },
      {
        id: "trait-3-2",
        name: "Vision",
        value: 70,
        description: "Setting clear direction and goals",
      },
      {
        id: "trait-3-3",
        name: "Decisiveness",
        value: 60,
        description: "Making timely, informed decisions",
      },
      {
        id: "trait-3-4",
        name: "Accountability",
        value: 65,
        description: "Holding self and others responsible",
      },
      {
        id: "trait-3-5",
        name: "Inspiration",
        value: 75,
        description: "Motivating and energizing the team",
      },
    ],
  },
]
