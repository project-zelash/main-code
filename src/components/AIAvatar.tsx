
import React, { useState, useEffect } from 'react';
import { cn } from '@/lib/utils';

type AIAvatarProps = {
  emotion?: 'neutral' | 'thinking' | 'happy' | 'concerned' | 'confused';
  pulseEffect?: boolean;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
};

const AIAvatar = ({ 
  emotion = 'neutral', 
  pulseEffect = false, 
  className,
  size = 'md'
}: AIAvatarProps) => {
  const [animating, setAnimating] = useState(false);
  
  useEffect(() => {
    setAnimating(true);
    const timer = setTimeout(() => setAnimating(false), 1000);
    return () => clearTimeout(timer);
  }, [emotion]);

  // Get color based on emotion
  const getEmotionColor = () => {
    switch(emotion) {
      case 'happy': return 'from-emerald-400 to-teal-600';
      case 'thinking': return 'from-blue-400 to-indigo-600';
      case 'concerned': return 'from-amber-400 to-yellow-600';
      case 'confused': return 'from-purple-400 to-fuchsia-600';
      default: return 'from-indigo-400 to-violet-600';
    }
  };
  
  // Size classes
  const sizeClasses = {
    sm: 'h-8 w-8',
    md: 'h-10 w-10',
    lg: 'h-12 w-12'
  };

  return (
    <div 
      className={cn(
        'relative rounded-full flex items-center justify-center overflow-hidden',
        sizeClasses[size],
        pulseEffect && 'animate-pulse-slow',
        className
      )}
    >
      {/* Background gradient */}
      <div className={cn(
        'absolute inset-0 bg-gradient-to-br',
        getEmotionColor(),
        animating && 'animate-pulse'
      )}/>
      
      {/* Overlay with pattern */}
      <div className="absolute inset-0 opacity-30 ai-grid-bg" />
      
      {/* Inner circle */}
      <div className="absolute inset-1.5 bg-ai-dark rounded-full flex items-center justify-center overflow-hidden">
        <div className="flex items-center justify-center h-full w-full">
          {/* AI Icon */}
          <svg 
            width="60%" 
            height="60%" 
            viewBox="0 0 24 24" 
            fill="none" 
            xmlns="http://www.w3.org/2000/svg"
            className={cn(
              'text-white',
              animating && 'animate-float'
            )}
          >
            <path 
              d="M12 3C16.9706 3 21 7.02944 21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3Z" 
              stroke="currentColor" 
              strokeWidth="2" 
              strokeLinecap="round" 
              strokeLinejoin="round"
              fill="rgba(99, 102, 241, 0.1)"
            />
            <path 
              d="M8 14C8.5 15.5 10 17 12 17C14 17 15.5 15.5 16 14" 
              stroke="currentColor" 
              strokeWidth="2" 
              strokeLinecap="round" 
              strokeLinejoin="round" 
            />
            <path 
              d="M9 9H9.01" 
              stroke="currentColor" 
              strokeWidth="3" 
              strokeLinecap="round" 
              strokeLinejoin="round" 
            />
            <path 
              d="M15 9H15.01" 
              stroke="currentColor" 
              strokeWidth="3" 
              strokeLinecap="round" 
              strokeLinejoin="round" 
            />
          </svg>
        </div>
      </div>
      
      {/* Animated ring */}
      {pulseEffect && (
        <div className="absolute inset-0 border-2 border-white/20 rounded-full animate-ping" />
      )}
    </div>
  );
};

export default AIAvatar;
