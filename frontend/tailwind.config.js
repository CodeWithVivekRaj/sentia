/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // Sentia's organic dark palette
        void: '#050508',
        deep: '#0a0a12',
        surface: '#0f0f1a',
        panel: '#141420',
        border: '#1e1e2e',
        muted: '#2a2a3e',
        subtle: '#3a3a50',
        // Neurochemistry colors
        dopamine: '#c084fc',
        serotonin: '#34d399',
        cortisol: '#f97316',
        oxytocin: '#fb7185',
        endorphin: '#60a5fa',
        adrenaline: '#facc15',
        melatonin: '#818cf8',
        // Text
        text: '#e2e8f0',
        'text-muted': '#94a3b8',
        'text-dim': '#64748b',
        // Accent
        life: '#a78bfa',
        'life-dim': '#6d28d9',
        pulse: '#22d3ee',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'breathe': 'breathe 4s ease-in-out infinite',
        'glow': 'glow 2s ease-in-out infinite',
      },
      keyframes: {
        breathe: {
          '0%, 100%': { opacity: '0.6', transform: 'scale(1)' },
          '50%': { opacity: '1', transform: 'scale(1.03)' },
        },
        glow: {
          '0%, 100%': { boxShadow: '0 0 8px rgba(167, 139, 250, 0.3)' },
          '50%': { boxShadow: '0 0 20px rgba(167, 139, 250, 0.7)' },
        },
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
    },
  },
  plugins: [],
}
