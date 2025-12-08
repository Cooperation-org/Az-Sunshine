/**
 * Button Component
 * Theme-aware button with variants and proper states
 */

import React from 'react';

export function Button({
  children,
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  className = '',
  ...props
}) {
  const baseStyles = `
    rounded-lg font-medium
    transition-all duration-200
    transform active:scale-[0.98]
    focus:outline-none focus:ring-2 focus:ring-offset-2
    disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none
    inline-flex items-center justify-center gap-2
  `;

  const variants = {
    primary: `
      shadow-sm hover:shadow-md
    `,
    secondary: `
      border
    `,
    ghost: `
      hover:bg-opacity-10
    `,
    danger: `
      shadow-sm hover:shadow-md
    `
  };

  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base',
  };

  const variantStyles = {
    primary: {
      backgroundColor: disabled ? 'var(--bg-tertiary)' : 'var(--accent-primary)',
      color: '#ffffff',
    },
    secondary: {
      backgroundColor: 'var(--bg-secondary)',
      color: 'var(--text-primary)',
      borderColor: 'var(--border-color)',
    },
    ghost: {
      backgroundColor: 'transparent',
      color: 'var(--text-primary)',
    },
    danger: {
      backgroundColor: disabled ? 'var(--bg-tertiary)' : '#dc2626',
      color: '#ffffff',
    }
  };

  const hoverStyles = !disabled && !loading ? {
    ':hover': {
      backgroundColor: variant === 'primary' ? 'var(--accent-hover)' :
                      variant === 'secondary' ? 'var(--bg-tertiary)' :
                      variant === 'ghost' ? 'var(--bg-secondary)' :
                      '#b91c1c'
    }
  } : {};

  return (
    <button
      className={`
        ${baseStyles}
        ${variants[variant]}
        ${sizes[size]}
        ${className}
      `}
      style={variantStyles[variant]}
      disabled={disabled || loading}
      {...props}
    >
      {loading && (
        <svg
          className="animate-spin h-4 w-4"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      )}
      {children}
    </button>
  );
}
