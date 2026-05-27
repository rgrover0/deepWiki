/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{html,ts}'],
  theme: {
    extend: {
      colors: {
        // Penske-inspired navy blue + yellow theme
        background:  '#ffffff',
        foreground:  '#1a1a2e',
        primary:     { DEFAULT: '#003087', foreground: '#ffffff' },
        secondary:   { DEFAULT: '#f0f4f8', foreground: '#003087' },
        muted:       { DEFAULT: '#e2e8f0', foreground: '#4a5568' },
        accent:      { DEFAULT: '#e8f0fb', foreground: '#1a1a2e' },
        border:      'rgba(0,48,135,0.15)',
        destructive: { DEFAULT: '#dc2626', foreground: '#ffffff' },
        'penske-yellow': '#FFD100',
        'penske-blue':   '#0077C8',

        // D3 graph dark theme tokens (graph route only)
        'graph-bg':       '#020C18',
        'graph-panel':    '#030E1C',
        'graph-border':   '#0D3464',
        'graph-border-hi':'#1A6CC0',
        'graph-text':     '#507898',
        'graph-text-hi':  '#B0D4EE',
        'graph-yellow':   '#FFD100',
        'graph-blue':     '#2878CC',
        'graph-teal':     '#1D9E75',
        'graph-purple':   '#8870DD',
      },
      fontFamily: {
        sans:  ['Inter', 'system-ui', 'sans-serif'],
        mono:  ['"Courier New"', 'monospace'],
      },
      borderRadius: { DEFAULT: '0.625rem' },
    },
  },
  plugins: [],
};
