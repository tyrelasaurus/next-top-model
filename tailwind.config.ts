import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0F0F17',
        sidebar: '#0A0A10',
        foreground: '#E5E7EB',
        primary: '#A855F7', // Vibrant Purple
        secondary: '#EC4899', // Hot Pink
        accent: '#10B981', // Emerald
        gold: '#F59E0B', // Gold for top performers
        silver: '#6B7280', // Silver for rankings
        bronze: '#D97706', // Bronze accent
        danger: '#EF4444', // Red for alerts
        warning: '#F59E0B', // Amber for warnings
        success: '#10B981', // Green for success
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
export default config;