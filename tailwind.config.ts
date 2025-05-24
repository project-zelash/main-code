
import type { Config } from "tailwindcss";

export default {
	darkMode: ["class"],
	content: [
		"./pages/**/*.{ts,tsx}",
		"./components/**/*.{ts,tsx}",
		"./app/**/*.{ts,tsx}",
		"./src/**/*.{ts,tsx}",
	],
	prefix: "",
	theme: {
		container: {
			center: true,
			padding: '2rem',
			screens: {
				'2xl': '1400px'
			}
		},
		extend: {
			colors: {
				border: 'hsl(var(--border))',
				input: 'hsl(var(--input))',
				ring: 'hsl(var(--ring))',
				background: 'hsl(var(--background))',
				foreground: 'hsl(var(--foreground))',
				primary: {
					DEFAULT: 'hsl(var(--primary))',
					foreground: 'hsl(var(--primary-foreground))'
				},
				secondary: {
					DEFAULT: 'hsl(var(--secondary))',
					foreground: 'hsl(var(--secondary-foreground))'
				},
				destructive: {
					DEFAULT: 'hsl(var(--destructive))',
					foreground: 'hsl(var(--destructive-foreground))'
				},
				muted: {
					DEFAULT: 'hsl(var(--muted))',
					foreground: 'hsl(var(--muted-foreground))'
				},
				accent: {
					DEFAULT: 'hsl(var(--accent))',
					foreground: 'hsl(var(--accent-foreground))'
				},
				popover: {
					DEFAULT: 'hsl(var(--popover))',
					foreground: 'hsl(var(--popover-foreground))'
				},
				card: {
					DEFAULT: 'hsl(var(--card))',
					foreground: 'hsl(var(--card-foreground))'
				},
				sidebar: {
					DEFAULT: 'hsl(var(--sidebar-background))',
					foreground: 'hsl(var(--sidebar-foreground))',
					primary: 'hsl(var(--sidebar-primary))',
					'primary-foreground': 'hsl(var(--sidebar-primary-foreground))',
					accent: 'hsl(var(--sidebar-accent))',
					'accent-foreground': 'hsl(var(--sidebar-accent-foreground))',
					border: 'hsl(var(--sidebar-border))',
					ring: 'hsl(var(--sidebar-ring))'
				},
				// Enhanced AI theme colors with extended palette
				ai: {
					'bg': '#0a0f1f', // Darker background
					'primary': '#6366F1',
					'secondary': '#06B6D4',
					'accent': '#8B5CF6',
					'text': '#F8FAFC',
					'muted': '#94A3B8',
					'border': '#1E293B',
					'success': '#10B981',
					'warning': '#F59E0B',
					'error': '#EF4444',
					'dark': '#020617',
					'highlight': '#9333EA', // Vibrant purple highlight
					'neon': '#F472B6', // Neon pink for glowing elements
					'deep': '#1E1B4B', // Deep indigo for layering
					'cosmic': '#3B0764', // Cosmic purple for special elements
					'space': '#0F172A', // Space blue for dark containers
					'nebula': '#7C3AED', // Vibrant nebula purple
					'star': '#E0E7FF', // Bright star white
					'ultraviolet': '#5B21B6', // Ultra-violet for deep space feel
					'fuchsia': '#C026D3', // Fuchsia for dimensional effects
					'galaxy': '#581C87', // Galaxy purple for depth
					'interstellar': '#4338CA', // Interstellar blue for cosmic effects
					'abyss': '#0F172A', // Abyss dark background
				}
			},
			borderRadius: {
				lg: 'var(--radius)',
				md: 'calc(var(--radius) - 2px)',
				sm: 'calc(var(--radius) - 4px)',
				'2xl': '1rem',
				'3xl': '1.5rem',
				'4xl': '2rem',
			},
			boxShadow: {
				'glow-sm': '0 0 10px 1px rgba(139, 92, 246, 0.3)',
				'glow-md': '0 0 15px 2px rgba(139, 92, 246, 0.4)',
				'glow-lg': '0 0 25px 3px rgba(139, 92, 246, 0.5)',
				'inner-glow': 'inset 0 0 15px 0 rgba(139, 92, 246, 0.2)',
				'cosmic': '0 4px 20px -1px rgba(0, 0, 0, 0.5), 0 0 15px 5px rgba(139, 92, 246, 0.2)',
				'neon': '0 0 5px rgba(139, 92, 246, 0.5), 0 0 10px rgba(139, 92, 246, 0.3), 0 0 15px rgba(139, 92, 246, 0.1)',
			},
			keyframes: {
				'accordion-down': {
					from: { height: '0' },
					to: { height: 'var(--radix-accordion-content-height)' }
				},
				'accordion-up': {
					from: { height: 'var(--radix-accordion-content-height)' },
					to: { height: '0' }
				},
				'pulse-slow': {
					'0%, 100%': { opacity: '1' },
					'50%': { opacity: '0.5' }
				},
				'shimmer': {
					'0%': { backgroundPosition: '-200% 0' },
					'100%': { backgroundPosition: '200% 0' }
				},
				'wave': {
					'0%': { transform: 'scale(0)' },
					'50%': { transform: 'scale(1)' },
					'100%': { transform: 'scale(0)' }
				},
				'typing': {
					'0%': { width: '0%' },
					'100%': { width: '100%' }
				},
				'float': {
					'0%, 100%': { transform: 'translateY(0)' },
					'50%': { transform: 'translateY(-10px)' }
				},
				'float-slight': {
					'0%, 100%': { transform: 'translateY(0)' },
					'50%': { transform: 'translateY(-5px)' }
				},
				'blink': {
					'0%, 100%': { opacity: '1' },
					'50%': { opacity: '0' }
				},
				'rotate-3d': {
					'0%': { transform: 'perspective(1000px) rotateY(0deg)' },
					'100%': { transform: 'perspective(1000px) rotateY(360deg)' }
				},
				'pulse-ring': {
					'0%': { boxShadow: '0 0 0 0 rgba(139, 92, 246, 0.7)' },
					'70%': { boxShadow: '0 0 0 15px rgba(139, 92, 246, 0)' },
					'100%': { boxShadow: '0 0 0 0 rgba(139, 92, 246, 0)' }
				},
				'meteor': {
					'0%': { transform: 'rotate(215deg) translateX(0)', opacity: '1' },
					'70%': { opacity: '1' },
					'100%': { transform: 'rotate(215deg) translateX(-500px)', opacity: '0' }
				},
				'bounce-slight': {
					'0%, 100%': { transform: 'translateY(0)' },
					'50%': { transform: 'translateY(-5px)' }
				},
				'cosmic-shift': {
					'0%': { transform: 'translate(0, 0)', opacity: '0.7' },
					'33%': { transform: 'translate(10px, -10px)', opacity: '0.8' },
					'66%': { transform: 'translate(-10px, 5px)', opacity: '0.6' },
					'100%': { transform: 'translate(0, 0)', opacity: '0.7' },
				},
				'orbit': {
					'0%': { transform: 'rotate(0deg) translateX(10px) rotate(0deg)' },
					'100%': { transform: 'rotate(360deg) translateX(10px) rotate(-360deg)' }
				},
				'jelly': {
					'0%': { transform: 'scale3d(1, 1, 1)' },
					'30%': { transform: 'scale3d(1.15, 0.85, 1)' },
					'40%': { transform: 'scale3d(0.85, 1.15, 1)' },
					'50%': { transform: 'scale3d(1.05, 0.95, 1)' },
					'65%': { transform: 'scale3d(0.95, 1.05, 1)' },
					'75%': { transform: 'scale3d(1.05, 0.95, 1)' },
					'100%': { transform: 'scale3d(1, 1, 1)' }
				},
				'glow-pulse': {
					'0%, 100%': { boxShadow: '0 0 15px 5px rgba(139, 92, 246, 0.4)' },
					'50%': { boxShadow: '0 0 30px 5px rgba(139, 92, 246, 0.7)' }
				}
			},
			animation: {
				'accordion-down': 'accordion-down 0.2s ease-out',
				'accordion-up': 'accordion-up 0.2s ease-out',
				'pulse-slow': 'pulse-slow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
				'shimmer': 'shimmer 2s linear infinite',
				'wave': 'wave 1.5s infinite ease-in-out',
				'typing': 'typing 1.5s steps(40, end)',
				'float': 'float 5s ease-in-out infinite',
				'float-slight': 'float-slight 3s ease-in-out infinite',
				'blink': 'blink 1s infinite',
				'rotate-3d': 'rotate-3d 20s linear infinite',
				'pulse-ring': 'pulse-ring 2s cubic-bezier(0.455, 0.03, 0.515, 0.955) infinite',
				'meteor': 'meteor 5s linear infinite',
				'bounce-slight': 'bounce-slight 2s ease infinite',
				'cosmic-shift': 'cosmic-shift 10s ease-in-out infinite',
				'orbit': 'orbit 8s linear infinite',
				'jelly': 'jelly 0.8s ease-in-out',
				'glow-pulse': 'glow-pulse 2s ease-in-out infinite',
			},
			backgroundImage: {
				'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
				'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
				'ai-grid': "url(\"data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32' width='32' height='32' fill='none' stroke='rgb(15 23 42 / 0.04)'%3e%3cpath d='M0 .5H31.5V32'/%3e%3c/svg%3e\")",
				'cosmic': "radial-gradient(circle at 25% 25%, rgba(139, 92, 246, 0.3) 0%, transparent 50%), radial-gradient(circle at 75% 75%, rgba(6, 182, 212, 0.3) 0%, transparent 50%)",
				'nebula': "radial-gradient(circle at 50% 50%, rgba(139, 92, 246, 0.3) 0%, rgba(99, 102, 241, 0.2) 35%, rgba(244, 114, 182, 0.1) 75%, transparent 100%)",
				'cosmic-rays': "linear-gradient(45deg, rgba(139, 92, 246, 0.1) 25%, transparent 25%, transparent 50%, rgba(139, 92, 246, 0.1) 50%, rgba(139, 92, 246, 0.1) 75%, transparent 75%, transparent)",
				'star-field': "radial-gradient(1px 1px at calc(random(100) * 1%) calc(random(100) * 1%), rgba(255, 255, 255, 0.3), transparent), radial-gradient(1px 1px at calc(random(100) * 1%) calc(random(100) * 1%), rgba(255, 255, 255, 0.3), transparent)",
				'holographic': "linear-gradient(135deg, rgba(139, 92, 246, 0.2) 0%, rgba(99, 102, 241, 0.1) 25%, rgba(244, 114, 182, 0.2) 50%, rgba(99, 102, 241, 0.1) 75%, rgba(139, 92, 246, 0.2) 100%)",
			},
			backdropBlur: {
				'xs': '2px',
				'4xl': '80px',
			},
			fontSize: {
				'xxs': '0.625rem',
			},
			typography: {
				DEFAULT: {
					css: {
						color: 'inherit',
						'h1, h2, h3, h4': {
							color: 'inherit',
							fontWeight: '600',
						},
						'p, li': {
							color: 'inherit',
						},
						'pre': {
							backgroundColor: '#1a1a2e',
							color: '#e2e2e2',
							borderRadius: '0.5rem',
							padding: '1rem',
						},
						'code': {
							backgroundColor: 'rgba(0, 0, 0, 0.1)',
							color: '#e2e2e2',
							borderRadius: '0.25rem',
							padding: '0.15rem 0.3rem',
							fontSize: '0.875em',
						}
					},
				},
			},
		}
	},
	plugins: [require("tailwindcss-animate")],
} satisfies Config;

