/**
 * Card Component
 * Professional card with theme support and micro-interactions
 */

import React from 'react';

export function Card({ children, className = '', hover = false, ...props }) {
  return (
    <div
      className={`
        relative overflow-hidden
        rounded-xl p-6
        border transition-all duration-300
        ${hover ? 'hover:shadow-lg cursor-pointer transform hover:scale-[1.01]' : ''}
        ${className}
      `}
      style={{
        backgroundColor: 'var(--bg-primary)',
        borderColor: 'var(--border-color)',
        boxShadow: 'var(--shadow-sm)',
      }}
      {...props}
    >
      {/* Subtle gradient overlay */}
      <div
        className="absolute inset-0 opacity-50 pointer-events-none"
        style={{
          background: 'linear-gradient(to bottom right, transparent, var(--bg-secondary))'
        }}
      />

      {/* Content */}
      <div className="relative z-10">
        {children}
      </div>
    </div>
  );
}

export function CardHeader({ children, className = '' }) {
  return (
    <div className={`mb-4 ${className}`}>
      {children}
    </div>
  );
}

export function CardTitle({ children, className = '' }) {
  return (
    <h3
      className={`text-xl font-semibold mb-2 ${className}`}
      style={{ color: 'var(--text-primary)' }}
    >
      {children}
    </h3>
  );
}

export function CardDescription({ children, className = '' }) {
  return (
    <p
      className={`text-sm ${className}`}
      style={{ color: 'var(--text-secondary)' }}
    >
      {children}
    </p>
  );
}

export function CardContent({ children, className = '' }) {
  return (
    <div className={className}>
      {children}
    </div>
  );
}

export function CardFooter({ children, className = '' }) {
  return (
    <div className={`mt-6 pt-4 border-t ${className}`} style={{ borderColor: 'var(--border-color)' }}>
      {children}
    </div>
  );
}
