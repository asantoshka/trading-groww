/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#090c10',
        surface: '#0d1117',
        surface2: '#131920',
        border: '#1e2832',
        'border-hover': '#2d3f52',
        green: '#00ff88',
        'green-dim': 'rgba(0,255,136,0.12)',
        amber: '#ffb700',
        'amber-dim': 'rgba(255,183,0,0.12)',
        red: '#ff4560',
        'red-dim': 'rgba(255,69,96,0.12)',
        blue: '#00b4ff',
        'blue-dim': 'rgba(0,180,255,0.12)',
        muted: '#4a5568',
        muted2: '#2d3748',
        text: '#e2e8f0'
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', 'monospace'],
        display: ['Syne', 'sans-serif']
      }
    }
  },
  plugins: []
}
