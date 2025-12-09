import React from 'react';
import { Link } from 'react-router-dom';
import { Home, Rocket } from 'lucide-react';
import { useDarkMode } from "../context/DarkModeContext";

const Star = ({ style }) => (
  <div className="absolute bg-white rounded-full" style={style} />
);

const NotFound = () => {
  const { darkMode } = useDarkMode();

  // Generate a set of random stars for the background
  const stars = React.useMemo(() => {
    return Array.from({ length: 150 }).map((_, i) => {
      const size = Math.random() * 2 + 1; // Star size between 1px and 3px
      const animationDuration = Math.random() * 3 + 2; // Twinkle duration between 2s and 5s
      const animationDelay = Math.random() * 5; // Start twinkling at different times

      return (
        <Star
          key={i}
          style={{
            width: `${size}px`,
            height: `${size}px`,
            top: `${Math.random() * 100}%`,
            left: `${Math.random() * 100}%`,
            animation: `twinkle ${animationDuration}s linear ${animationDelay}s infinite`,
            opacity: darkMode ? Math.random() * 0.8 + 0.2 : Math.random() * 0.3, // Stars are more prominent in dark mode
          }}
        />
      );
    });
  }, [darkMode]);

  return (
    <div className={`relative flex flex-col items-center justify-center min-h-screen overflow-hidden transition-colors duration-500 ${darkMode ? 'bg-[#2a2347]' : 'bg-gray-100'}`}>
      <div className="absolute inset-0 z-0">
        {stars}
      </div>
      
      <div className="relative z-10 flex flex-col items-center text-center p-8">
        <div className="relative mb-8">
          <Rocket className={`absolute -top-10 -left-16 w-24 h-24 transform -rotate-45 transition-all duration-500 ${darkMode ? 'text-purple-300/50' : 'text-purple-300/70'}`} />
          <h1 className={`font-black text-8xl sm:text-9xl transition-colors duration-500 ${darkMode ? 'text-white' : 'text-gray-800'}`} style={{ textShadow: `0 0 15px ${darkMode ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'}` }}>
            404
          </h1>
        </div>
        
        <h2 className={`text-2xl sm:text-3xl font-bold mt-4 mb-2 transition-colors duration-500 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
          Page Not Found
        </h2>
        
        <p className={`max-w-md text-base transition-colors duration-500 ${darkMode ? 'text-gray-300' : 'text-gray-500'}`}>
          It seems you've ventured into uncharted territory. The page you're looking for might have been moved, deleted, or never existed in the first place.
        </p>
        
        <Link
          to="/"
          className={`mt-10 inline-flex items-center gap-2 px-6 py-3 rounded-xl font-semibold text-white transition-all shadow-lg hover:shadow-2xl focus:outline-none focus:ring-2 focus:ring-offset-2 ${darkMode ? 'bg-purple-500 hover:bg-purple-600 focus:ring-purple-400 focus:ring-offset-gray-900' : 'bg-[#7163BA] hover:bg-[#5b509a] focus:ring-[#7163BA] focus:ring-offset-gray-100'}`}
        >
          <Home className="w-5 h-5" />
          <span>Return to Dashboard</span>
        </Link>
      </div>
      
      <style>{`
        @keyframes twinkle {
          0%, 100% { opacity: 0.2; transform: scale(0.8); }
          50% { opacity: 1; transform: scale(1.2); }
        }
      `}</style>
    </div>
  );
};

export default NotFound;
