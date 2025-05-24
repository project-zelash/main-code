import React, { useEffect, useState, useCallback, useMemo, useRef } from 'react';
import { motion } from 'framer-motion';

const TRAIL_UPDATE_THROTTLE_MS = 75; // Increased from 50ms

const QuantumCursor = () => {
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [isHovering, setIsHovering] = useState(false);
  const [isClicking, setIsClicking] = useState(false);
  const [trails, setTrails] = useState<Array<{ x: number; y: number; id: number }>>([]);

  // Refs for optimization
  const animationFrameId = useRef<number | null>(null);
  const lastTrailUpdateTime = useRef(0);
  const latestMousePosition = useRef({ x: 0, y: 0 }); // Stores the most recent mouse position

  // Define the mouse move logic separately
  const mouseMoveCallback = (e: MouseEvent): void => {
    latestMousePosition.current = { x: e.clientX, y: e.clientY };

    if (animationFrameId.current === null) {
      animationFrameId.current = requestAnimationFrame(() => {
        setMousePosition(latestMousePosition.current);
        animationFrameId.current = null;
      });
    }

    const now = Date.now();
    if (now - lastTrailUpdateTime.current > TRAIL_UPDATE_THROTTLE_MS) {
      setTrails(prevTrails => {
        const newTrail = { ...latestMousePosition.current, id: now };
        const currentTrails = Array.isArray(prevTrails) ? prevTrails : [];
        const updatedTrails = [...currentTrails, newTrail];
        return updatedTrails.slice(-3); // Reduced from -4 to -3 trail points
      });
      lastTrailUpdateTime.current = now;
    }
  };
  // Optimized mouse move handler using the defined callback
  const handleMouseMove = useCallback(mouseMoveCallback, []); // Empty dependency array is correct here

  const handleMouseOver = useCallback((e: MouseEvent) => {
    const target = e.target as HTMLElement;
    setIsHovering(target.matches('button, a, [role="button"], input, textarea, .interactive'));
  }, []);

  const handleMouseDown = useCallback(() => setIsClicking(true), []);
  const handleMouseUp = useCallback(() => setIsClicking(false), []);

  useEffect(() => {
    // Use passive listeners for better performance
    document.addEventListener('mousemove', handleMouseMove, { passive: true });
    document.addEventListener('mouseover', handleMouseOver, { passive: true });
    document.addEventListener('mousedown', handleMouseDown, { passive: true });
    document.addEventListener('mouseup', handleMouseUp, { passive: true });

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseover', handleMouseOver);
      document.removeEventListener('mousedown', handleMouseDown);
      document.removeEventListener('mouseup', handleMouseUp);

      // Important: Cleanup any pending animation frame when the component unmounts or effect re-runs
      if (animationFrameId.current) {
        cancelAnimationFrame(animationFrameId.current);
        animationFrameId.current = null;
      }
    };
  }, [handleMouseMove, handleMouseOver, handleMouseDown, handleMouseUp]);

  // Memoized styles for better performance
  const outerRingStyle = useMemo(() => ({
    left: mousePosition.x - 20,
    top: mousePosition.y - 20,
    width: 40,
    height: 40,
    background: 'radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%)',
    boxShadow: '0 0 20px rgba(255,255,255,0.3), inset 0 0 20px rgba(255,255,255,0.1)',
    willChange: 'transform, opacity', // Added will-change
  }), [mousePosition.x, mousePosition.y]);

  const middleRingStyle = useMemo(() => ({
    left: mousePosition.x - 12,
    top: mousePosition.y - 12,
    width: 24,
    height: 24,
    background: 'radial-gradient(circle, rgba(255,255,255,0.2) 0%, transparent 70%)',
    boxShadow: '0 0 15px rgba(255,255,255,0.4)',
    willChange: 'transform, opacity', // Added will-change
  }), [mousePosition.x, mousePosition.y]);

  const coreStyle = useMemo(() => ({
    left: mousePosition.x - 6,
    top: mousePosition.y - 6,
    width: 12,
    height: 12,
    background: 'radial-gradient(circle, #ffffff 0%, rgba(255,255,255,0.9) 50%, rgba(255,255,255,0.7) 100%)',
    boxShadow: `
      0 0 10px rgba(255,255,255,0.8),
      0 0 20px rgba(255,255,255,0.6),
      0 0 30px rgba(255,255,255,0.4),
      inset 0 0 8px rgba(255,255,255,0.3)
    `,
    willChange: 'transform, opacity', // Added will-change
  }), [mousePosition.x, mousePosition.y]);

  return (
    <div className="fixed inset-0 pointer-events-none z-50">
      {/* Optimized Trail Effect */}
      {trails.map((trail) => (
        <motion.div
          key={trail.id}
          className="absolute w-2 h-2 bg-white/20 rounded-full"
          style={{
            left: trail.x - 4,
            top: trail.y - 4,
            willChange: 'transform, opacity', // Added will-change
          }}
          initial={{ scale: 1, opacity: 0.6 }}
          animate={{ 
            scale: 0,
            opacity: 0,
          }}
          transition={{ 
            duration: 0.5, // Slightly reduced duration
            ease: "easeOut"
          }}
        />
      ))}

      {/* Outer Glow Ring */}
      <motion.div
        className="absolute rounded-full border border-white/30"
        style={outerRingStyle}
        animate={{
          scale: isHovering ? 1.3 : isClicking ? 0.8 : 1,
          opacity: isHovering ? 0.8 : 0.4,
        }}
        transition={{ type: 'spring', stiffness: 300, damping: 25 }}
      />

      {/* Middle Ring */}
      <motion.div
        className="absolute rounded-full border-2 border-white/60"
        style={middleRingStyle}
        animate={{
          scale: isHovering ? 1.2 : isClicking ? 0.9 : 1,
          borderColor: isHovering ? 'rgba(255,255,255,0.9)' : 'rgba(255,255,255,0.6)',
        }}
        transition={{ type: 'spring', stiffness: 400, damping: 30 }}
      />

      {/* Core Cursor */}
      <motion.div
        className="absolute rounded-full"
        style={coreStyle}
        animate={{
          scale: isHovering ? 1.3 : isClicking ? 0.8 : 1,
        }}
        transition={{ type: 'spring', stiffness: 500, damping: 35 }}
      />

      {/* Click Ripple Effect - style can also have will-change if deemed necessary, but it's a short animation */}
      {isClicking && (
        <motion.div
          className="absolute rounded-full border border-white/50"
          style={{
            left: mousePosition.x - 25,
            top: mousePosition.y - 25,
            width: 50,
            height: 50,
            willChange: 'transform, opacity', // Added will-change
          }}
          initial={{ scale: 0, opacity: 0.8 }}
          animate={{ scale: 2, opacity: 0 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
        />
      )}

      {/* Hover Pulse Rings - Optimized */}
      {isHovering && (
        <>
          <motion.div
            className="absolute rounded-full border border-white/40"
            style={{
              left: mousePosition.x - 30,
              top: mousePosition.y - 30,
              width: 60,
              height: 60,
              willChange: 'transform, opacity', // Added will-change
            }}
            animate={{
              scale: [1, 1.5],
              opacity: [0.6, 0],
            }}
            transition={{
              duration: 1.0, // Reduced duration from 1.2
              repeat: Infinity,
              ease: "easeOut"
            }}
          />
          <motion.div
            className="absolute rounded-full border border-white/30"
            style={{
              left: mousePosition.x - 35,
              top: mousePosition.y - 35,
              width: 70,
              height: 70,
              willChange: 'transform, opacity', // Added will-change
            }}
            animate={{
              scale: [1, 1.8],
              opacity: [0.4, 0],
            }}
            transition={{
              duration: 1.2, // Reduced duration from 1.5
              repeat: Infinity,
              ease: "easeOut",
              delay: 0.25 // Adjusted delay
            }}
          />
        </>
      )}

      {/* Reduced Floating Particles - now 2 */}
      {[...Array(2)].map((_, i) => (
        <motion.div
          key={i}
          className="absolute w-1 h-1 bg-white/60 rounded-full"
          style={{
            left: mousePosition.x - 2,
            top: mousePosition.y - 2,
            willChange: 'transform, opacity', // Added will-change
          }}
          animate={{
            x: [0, (Math.random() - 0.5) * 25], // Slightly reduced range
            y: [0, (Math.random() - 0.5) * 25], // Slightly reduced range
            opacity: [0.8, 0],
            scale: [1, 0],
          }}
          transition={{
            duration: 1.2, // Reduced duration from 1.5
            delay: i * 0.2,
            repeat: Infinity,
            ease: "easeOut"
          }}
        />
      ))}

      {/* Energy Field - style can also have will-change */}
      <motion.div
        className="absolute rounded-full"
        style={{
          left: mousePosition.x - 50,
          top: mousePosition.y - 50,
          width: 100,
          height: 100,
          background: 'radial-gradient(circle, rgba(255,255,255,0.05) 0%, transparent 70%)',
          filter: 'blur(20px)',
          willChange: 'transform, opacity', // Added will-change
        }}
        animate={{
          scale: isHovering ? 1.5 : 1,
          opacity: isHovering ? 0.6 : 0.2,
        }}
        transition={{ duration: 0.6, ease: "easeOut" }} // Reduced duration
      />

      {/* Crosshair - style can also have will-change */}
      <motion.div
        className="absolute"
        style={{
          left: mousePosition.x - 8,
          top: mousePosition.y - 1,
          width: 16,
          height: 2,
          background: 'linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.8) 50%, transparent 100%)',
          willChange: 'transform, opacity', // Added will-change
        }}
        animate={{
          opacity: isHovering ? 1 : 0,
          scaleX: isHovering ? 1 : 0.5,
        }}
        transition={{ duration: 0.3 }}
      />
      <motion.div
        className="absolute"
        style={{
          left: mousePosition.x - 1,
          top: mousePosition.y - 8,
          width: 2,
          height: 16,
          background: 'linear-gradient(180deg, transparent 0%, rgba(255,255,255,0.8) 50%, transparent 100%)',
          willChange: 'transform, opacity', // Added will-change
        }}
        animate={{
          opacity: isHovering ? 1 : 0,
          scaleY: isHovering ? 1 : 0.5,
        }}
        transition={{ duration: 0.3 }}
      />
    </div>
  );
};

export default QuantumCursor;
