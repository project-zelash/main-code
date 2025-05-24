export type Message = {
  id: string;
  content: string;
  role: 'user' | 'assistant' | 'system';
  timestamp: string;
  isLoading?: boolean;
  emotion?: 'neutral' | 'thinking' | 'happy' | 'concerned' | 'confused';
  images?: string[];
  isQuestion?: boolean; // Added to identify question messages
  questionId?: string; // Unique ID for the question itself
  answered?: 'yes' | 'no'; // Store the answer if it's a question message that has been answered
  planText?: string; // For assistant messages containing the plan text
  planJson?: object; // For assistant messages containing the plan JSON
};
