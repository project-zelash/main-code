
import React, { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';

const FuturisticBackground = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    // Neural network nodes
    const nodes: Array<{x: number, y: number, vx: number, vy: number, connections: number[]}> = [];
    const nodeCount = 80;
    
    // Initialize nodes
    for (let i = 0; i < nodeCount; i++) {
      nodes.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.5,
        vy: (Math.random() - 0.5) * 0.5,
        connections: []
      });
    }

    // Energy particles
    const particles: Array<{x: number, y: number, vx: number, vy: number, life: number, maxLife: number}> = [];
    
    function createParticle() {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 2,
        vy: (Math.random() - 0.5) * 2,
        life: 100,
        maxLife: 100
      });
    }

    // Create initial particles
    for (let i = 0; i < 150; i++) {
      createParticle();
    }

    function animate() {
      ctx.fillStyle = 'rgba(4, 6, 20, 0.1)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Update and draw neural network
      nodes.forEach((node, i) => {
        node.x += node.vx;
        node.y += node.vy;

        // Bounce off edges
        if (node.x < 0 || node.x > canvas.width) node.vx *= -1;
        if (node.y < 0 || node.y > canvas.height) node.vy *= -1;

        // Draw connections
        nodes.forEach((otherNode, j) => {
          if (i !== j) {
            const dx = node.x - otherNode.x;
            const dy = node.y - otherNode.y;
            const distance = Math.sqrt(dx * dx + dy * dy);

            if (distance < 120) {
              const opacity = (120 - distance) / 120;
              ctx.strokeStyle = `rgba(124, 58, 237, ${opacity * 0.3})`;
              ctx.lineWidth = 1;
              ctx.beginPath();
              ctx.moveTo(node.x, node.y);
              ctx.lineTo(otherNode.x, otherNode.y);
              ctx.stroke();
            }
          }
        });

        // Draw node
        const gradient = ctx.createRadialGradient(node.x, node.y, 0, node.x, node.y, 8);
        gradient.addColorStop(0, 'rgba(139, 92, 246, 0.8)');
        gradient.addColorStop(1, 'rgba(139, 92, 246, 0)');
        
        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.arc(node.x, node.y, 8, 0, Math.PI * 2);
        ctx.fill();
      });

      // Update and draw particles
      particles.forEach((particle, i) => {
        particle.x += particle.vx;
        particle.y += particle.vy;
        particle.life--;

        if (particle.life <= 0 || particle.x < 0 || particle.x > canvas.width || particle.y < 0 || particle.y > canvas.height) {
          particles.splice(i, 1);
          createParticle();
          return;
        }

        const opacity = particle.life / particle.maxLife;
        const size = (particle.life / particle.maxLife) * 3;
        
        const gradient = ctx.createRadialGradient(particle.x, particle.y, 0, particle.x, particle.y, size);
        gradient.addColorStop(0, `rgba(99, 102, 241, ${opacity})`);
        gradient.addColorStop(1, `rgba(99, 102, 241, 0)`);
        
        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.arc(particle.x, particle.y, size, 0, Math.PI * 2);
        ctx.fill();
      });

      requestAnimationFrame(animate);
    }

    animate();

    const handleResize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none">
      {/* Animated Canvas Background */}
      <canvas
        ref={canvasRef}
        className="absolute inset-0 w-full h-full"
        style={{ background: 'linear-gradient(135deg, #040614 0%, #0a0f1f 25%, #1a1b3a 50%, #2d1b69 75%, #4c1d95 100%)' }}
      />
      
      {/* Holographic Grid Overlay */}
      <div className="absolute inset-0 opacity-20">
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-cyan-500/10 to-transparent animate-pulse-slow" 
             style={{ 
               backgroundImage: `
                 linear-gradient(90deg, transparent 0%, rgba(6, 182, 212, 0.1) 25%, rgba(6, 182, 212, 0.2) 50%, rgba(6, 182, 212, 0.1) 75%, transparent 100%),
                 linear-gradient(0deg, transparent 0%, rgba(124, 58, 237, 0.1) 25%, rgba(124, 58, 237, 0.2) 50%, rgba(124, 58, 237, 0.1) 75%, transparent 100%)
               `,
               backgroundSize: '200px 200px',
               animation: 'grid-flow 20s linear infinite'
             }} 
        />
      </div>

      {/* Quantum Energy Waves */}
      <div className="absolute inset-0 overflow-hidden">
        {[...Array(6)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute w-full h-1 bg-gradient-to-r from-transparent via-purple-500/30 to-transparent"
            style={{
              top: `${20 + i * 15}%`,
              filter: 'blur(2px)',
            }}
            animate={{
              x: ['-100%', '100%'],
              opacity: [0, 1, 0],
            }}
            transition={{
              duration: 8 + i * 2,
              repeat: Infinity,
              delay: i * 1.5,
              ease: 'easeInOut',
            }}
          />
        ))}
      </div>

      {/* Floating Holographic Orbs */}
      {[...Array(12)].map((_, i) => (
        <motion.div
          key={i}
          className="absolute w-4 h-4 rounded-full"
          style={{
            background: `radial-gradient(circle, rgba(${i % 2 ? '139, 92, 246' : '6, 182, 212'}, 0.6) 0%, transparent 70%)`,
            boxShadow: `0 0 20px rgba(${i % 2 ? '139, 92, 246' : '6, 182, 212'}, 0.5)`,
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
          }}
          animate={{
            y: [0, -100, 0],
            x: [0, Math.random() * 100 - 50, 0],
            scale: [1, 1.5, 1],
            opacity: [0.3, 1, 0.3],
          }}
          transition={{
            duration: 15 + Math.random() * 10,
            repeat: Infinity,
            delay: i * 2,
            ease: 'easeInOut',
          }}
        />
      ))}

      {/* Digital Rain Effect */}
      <div className="absolute inset-0 overflow-hidden opacity-40">
        {[...Array(30)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute w-px bg-gradient-to-b from-cyan-400/80 via-purple-500/60 to-transparent"
            style={{
              left: `${Math.random() * 100}%`,
              height: `${Math.random() * 200 + 100}px`,
            }}
            animate={{
              y: ['-200px', '100vh'],
              opacity: [0, 1, 0],
            }}
            transition={{
              duration: 3 + Math.random() * 4,
              repeat: Infinity,
              delay: Math.random() * 5,
              ease: 'linear',
            }}
          />
        ))}
      </div>

      {/* Nebula Clouds */}
      <div className="absolute inset-0">
        <motion.div
          className="absolute w-full h-full"
          style={{
            background: `
              radial-gradient(ellipse 800px 400px at 20% 30%, rgba(124, 58, 237, 0.15) 0%, transparent 60%),
              radial-gradient(ellipse 600px 300px at 80% 70%, rgba(6, 182, 212, 0.1) 0%, transparent 60%),
              radial-gradient(ellipse 1000px 500px at 50% 50%, rgba(99, 102, 241, 0.08) 0%, transparent 60%)
            `,
            filter: 'blur(60px)',
          }}
          animate={{
            scale: [1, 1.2, 1],
            rotate: [0, 5, 0],
          }}
          transition={{
            duration: 30,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        />
      </div>

      {/* Energy Pulse Rings */}
      <div className="absolute inset-0 flex items-center justify-center">
        {[...Array(4)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute rounded-full border border-purple-500/20"
            style={{
              width: `${200 + i * 150}px`,
              height: `${200 + i * 150}px`,
            }}
            animate={{
              scale: [1, 1.5, 1],
              opacity: [0.2, 0.5, 0.2],
              rotate: [0, 360],
            }}
            transition={{
              duration: 20 + i * 5,
              repeat: Infinity,
              delay: i * 3,
              ease: 'easeInOut',
            }}
          />
        ))}
      </div>

      {/* Laser Grid Lines */}
      <div className="absolute inset-0 opacity-20">
        <svg width="100%" height="100%" className="absolute inset-0">
          <defs>
            <pattern id="grid" width="100" height="100" patternUnits="userSpaceOnUse">
              <path d="M 100 0 L 0 0 0 100" fill="none" stroke="rgba(139, 92, 246, 0.3)" strokeWidth="1"/>
            </pattern>
            <filter id="glow">
              <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
              <feMerge> 
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" filter="url(#glow)" />
        </svg>
      </div>

      {/* Quantum Particles */}
      <div className="absolute inset-0">
        {[...Array(50)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute w-1 h-1 bg-cyan-400 rounded-full"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              boxShadow: '0 0 10px rgba(6, 182, 212, 0.8)',
            }}
            animate={{
              scale: [0, 1, 0],
              opacity: [0, 1, 0],
              x: [0, Math.random() * 200 - 100],
              y: [0, Math.random() * 200 - 100],
            }}
            transition={{
              duration: 4 + Math.random() * 6,
              repeat: Infinity,
              delay: Math.random() * 10,
              ease: 'easeInOut',
            }}
          />
        ))}
      </div>
    </div>
  );
};

export default FuturisticBackground;
