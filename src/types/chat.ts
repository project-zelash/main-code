
export type Message = {
  id: string;
  content: string;
  role: 'user' | 'assistant' | 'system';
  timestamp: string;
  isLoading?: boolean;
  emotion?: 'neutral' | 'thinking' | 'happy' | 'concerned' | 'confused';
  images?: string[];
};
