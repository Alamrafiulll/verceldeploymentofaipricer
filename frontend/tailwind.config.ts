import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['"Space Grotesk"', 'sans-serif'],
        body: ['"Manrope"', 'sans-serif'],
      },
      colors: {
        brand: {
          navy: '#262261',
          'navy-light': '#2f2b78',
          'navy-dark': '#1b1849',
          'navy-950': '#110f36',
          red: '#E41E2B',
          blue: '#1e3a7b',
          gold: '#d4a843',
        },
        signal: {
          green: '#1A8F5B',
          yellow: '#B38600',
          red: '#B43A3A',
        },
      },
      boxShadow: {
        card: '0 10px 28px rgba(9, 28, 51, 0.12)',
        'sidebar': '4px 0 24px rgba(38, 34, 97, 0.15)',
      },
    },
  },
  plugins: [],
};

export default config;
