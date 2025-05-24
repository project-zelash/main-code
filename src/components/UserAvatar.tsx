
import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { User } from 'lucide-react';
import { motion } from 'framer-motion';

type UserAvatarProps = {
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  pulseEffect?: boolean;
};

const UserAvatar = ({ 
  className,
  size = 'md',
  pulseEffect = false
}: UserAvatarProps) => {
  const [isHovered, setIsHovered] = useState(false);
  
  const sizeClasses = {
    sm: 'h-8 w-8',
    md: 'h-10 w-10',
    lg: 'h-12 w-12'
  };
  
  return (
    <motion.div 
      className={cn(
        'relative rounded-full flex items-center justify-center overflow-hidden',
        sizeClasses[size],
        className
      )}
      whileHover={{ scale: 1.08 }}
      transition={{ type: "spring", stiffness: 500, damping: 30 }}
      onHoverStart={() => setIsHovered(true)}
      onHoverEnd={() => setIsHovered(false)}
    >
      {/* Background glow effect */}
      <div className={cn(
        "absolute inset-0 bg-gradient-to-br from-violet-600 via-indigo-600 to-blue-700 opacity-80",
        isHovered && "animate-pulse-slow"
      )}></div>
      
      {/* Pulse ring effect */}
      {pulseEffect && (
        <div className="absolute inset-0 rounded-full animate-pulse-ring"></div>
      )}
      
      {/* Avatar border */}
      <div className="absolute inset-0.5 bg-gradient-to-br from-slate-800 to-slate-900 rounded-full"></div>
      
      {/* Shine effect on hover */}
      <div className={cn(
        "absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-0 transition-opacity duration-700",
        isHovered && "opacity-20 -translate-x-full",
        isHovered && "transition-transform duration-700"
      )} style={{ transform: 'translateX(100%)' }}></div>
      
      {/* User icon */}
      <User className={cn(
        'relative text-slate-300 z-10',
        size === 'sm' && 'h-4 w-4',
        size === 'md' && 'h-5 w-5',
        size === 'lg' && 'h-6 w-6',
      )} />
      
      {/* Inner highlight */}
      <div className="absolute inset-0 bg-gradient-to-b from-white/10 to-transparent opacity-30 rounded-full"></div>
    </motion.div>
  );
};

export default UserAvatar;
