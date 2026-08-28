/**
 * Professional EdTech color palette
 * Based on a neutral, credible palette with a single accent color
 * Avoids generic "AI-generated" look (purple/violet-to-green gradients)
 */

export const colors = {
  // Primary accent - a professional teal
  accent: {
    50: '#f0fdfb',
    100: '#ccf7f3',
    200: '#99efe7',
    300: '#66e7db',
    400: '#33dfcf',
    500: '#0dd7c3', // Main accent color
    600: '#0ab39d',
    700: '#078f77',
    800: '#056b51',
    900: '#03472b',
  },

  // Neutral grays - for UI structure
  gray: {
    50: '#f8f9fa',
    100: '#f1f3f5',
    200: '#e9ecef',
    300: '#dee2e6',
    400: '#ced4da',
    500: '#adb5bd',
    600: '#868e96',
    700: '#495057',
    800: '#343a40',
    900: '#212529',
  },

  // Semantic colors
  success: '#22c55e',
  warning: '#f59e0b',
  error: '#ef4444',
  info: '#3b82f6',

  // Background
  background: '#ffffff',
  backgroundSecondary: '#f8f9fa',

  // Text
  text: {
    primary: '#212529',
    secondary: '#495057',
    tertiary: '#868e96',
  },

  // Border
  border: '#dee2e6',
  borderLight: '#e9ecef',
};

export const spacing = {
  xs: '0.25rem', // 4px
  sm: '0.5rem', // 8px
  md: '1rem', // 16px
  lg: '1.5rem', // 24px
  xl: '2rem', // 32px
  '2xl': '3rem', // 48px
};

export const typography = {
  fontFamily: {
    base: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    mono: '"Fira Code", "Courier New", monospace',
  },
  fontSize: {
    xs: '0.75rem', // 12px
    sm: '0.875rem', // 14px
    base: '1rem', // 16px
    lg: '1.125rem', // 18px
    xl: '1.25rem', // 20px
    '2xl': '1.5rem', // 24px
    '3xl': '1.875rem', // 30px
  },
  fontWeight: {
    regular: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },
};

export const borderRadius = {
  sm: '0.375rem', // 6px
  md: '0.5rem', // 8px
  lg: '0.75rem', // 12px
  xl: '1rem', // 16px
  full: '9999px',
};

export const shadows = {
  sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
  md: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
  lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
  xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
};
