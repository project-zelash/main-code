
import React from 'react';
import { motion } from 'framer-motion';

const HolographicInterface = ({ children }: { children: React.ReactNode }) => {
  return (
    <div className="relative">
      {/* Main holographic container */}
      <motion.div
        className="relative backdrop-blur-xl bg-gradient-to-br from-gray-900/20 via-black/20 to-gray-800/20 border border-gray-500/30 rounded-2xl overflow-hidden"
        style={{
          boxShadow: `
            0 0 50px rgba(0, 0, 0, 0.5),
            inset 0 0 50px rgba(64, 64, 64, 0.1),
            0 8px 32px rgba(0, 0, 0, 0.5)
          `,
        }}
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.8, ease: 'easeOut' }}
      >
        {/* Holographic scan lines */}
        <div className="absolute inset-0 pointer-events-none">
          <motion.div
            className="absolute inset-0 bg-gradient-to-b from-transparent via-gray-500/10 to-transparent"
            animate={{
              y: ['-100%', '100%'],
            }}
            transition={{
              duration: 3,
              repeat: Infinity,
              ease: 'linear',
            }}
            style={{ height: '200%' }}
          />
        </div>

        {/* Corner brackets */}
        <div className="absolute top-4 left-4 w-8 h-8 border-l-2 border-t-2 border-gray-400/60" />
        <div className="absolute top-4 right-4 w-8 h-8 border-r-2 border-t-2 border-gray-400/60" />
        <div className="absolute bottom-4 left-4 w-8 h-8 border-l-2 border-b-2 border-gray-400/60" />
        <div className="absolute bottom-4 right-4 w-8 h-8 border-r-2 border-b-2 border-gray-400/60" />

        {/* Glowing edge effect */}
        <div className="absolute inset-0 rounded-2xl border border-gray-500/50 animate-pulse-slow" />
        
        {/* Inner glow */}
        <div className="absolute inset-2 rounded-xl bg-gradient-to-br from-gray-500/5 via-transparent to-black/5" />

        {/* Content */}
        <div className="relative z-10">
          {children}
        </div>

        {/* Floating data points */}
        {[...Array(8)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute w-2 h-2 bg-gray-400/60 rounded-full"
            style={{
              left: `${10 + Math.random() * 80}%`,
              top: `${10 + Math.random() * 80}%`,
              boxShadow: '0 0 10px rgba(128, 128, 128, 0.6)',
            }}
            animate={{
              scale: [0.5, 1.5, 0.5],
              opacity: [0.3, 1, 0.3],
            }}
            transition={{
              duration: 2 + Math.random() * 3,
              repeat: Infinity,
              delay: i * 0.5,
            }}
          />
        ))}
      </motion.div>

      {/* External glow effect */}
      <div className="absolute inset-0 -z-10">
        <div className="absolute inset-0 bg-gradient-to-br from-gray-600/20 via-black/20 to-gray-700/20 rounded-2xl blur-2xl" />
      </div>
    </div>
  );
};

export default HolographicInterface;
