import React from 'react';

export interface AIPersona {
  id: string;
  name: string;
  description: string;
  icon?: React.ReactNode; // Or string if it's a URL
  color?: string; // For UI elements, e.g., 'bg-blue-500'
  avatarUrl?: string; // Optional: URL for a more detailed avatar image
  systemInstruction?: string; // Added systemInstruction field
}
