/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  safelist: [
    { pattern: /^(bg|text|border)-(bg|accent|txt|border)-/ },
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        bg: {
          base:    '#0a0b0d',
          surface: '#111318',
          raised:  '#181c22',
          hover:   '#1e2229',
        },
        border: {
          dim:    'rgba(255,255,255,0.07)',
          base:   'rgba(255,255,255,0.12)',
          strong: 'rgba(255,255,255,0.20)',
        },
        accent: {
          green:   '#4ade80',
          green2:  'rgba(74,222,128,0.12)',
          green3:  'rgba(74,222,128,0.30)',
          blue:    '#60a5fa',
          blue2:   'rgba(96,165,250,0.12)',
          amber:   '#fbbf24',
          amber2:  'rgba(251,191,36,0.12)',
          red:     '#f87171',
          red2:    'rgba(248,113,113,0.10)',
          purple:  '#a78bfa',
          purple2: 'rgba(167,139,250,0.12)',
        },
        txt: {
          primary:   '#e8eaf0',
          secondary: '#9ca3af',
          muted:     '#6b7280',
        },
      },
    },
  },
  plugins: [],
}