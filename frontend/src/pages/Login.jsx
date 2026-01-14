import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { login as apiLogin } from '../api/api';
import { useAuth } from '../context/AuthContext';
import { useDarkMode } from '../context/DarkModeContext';
import {
  Lock, User, Eye, EyeOff, AlertCircle, Loader, LogIn, Sun, Moon, Sparkles, ArrowRight
} from 'lucide-react';

export default function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const { darkMode, toggleDarkMode } = useDarkMode();

  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });

  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await apiLogin(formData.username, formData.password);

      // Check if 2FA is required
      if (response.requires_2fa) {
        // Redirect to 2FA verification page with temp token
        navigate('/verify-2fa', { state: { tempToken: response.temp_token } });
        return;
      }

      // No 2FA, login successful
      login(response.user, response.tokens);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.error || 'Invalid username or password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="min-h-screen flex relative"
      style={darkMode
        ? { background: '#1A1625' }
        : { background: '#f8f9fa' }
      }
    >
      {/* Theme Toggle Button */}
      <button
        onClick={toggleDarkMode}
        className={`absolute top-6 right-6 z-50 p-3 rounded-xl transition-all ${
          darkMode
            ? 'bg-[#2D2844] text-white hover:bg-[#373052]'
            : 'bg-white text-gray-700 hover:bg-gray-100 shadow-md'
        }`}
        title={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
      >
        {darkMode ? <Sun size={20} /> : <Moon size={20} />}
      </button>

      {/* Left Side - Branding (hidden on mobile) */}
      <div
        className="hidden lg:flex lg:w-1/2 xl:w-[55%] flex-col justify-between py-16 px-12 relative overflow-hidden"
        style={darkMode
          ? { background: 'linear-gradient(135deg, #2D2844 0%, #1A1625 100%)' }
          : { background: 'linear-gradient(135deg, #685994 0%, #4c3e7c 100%)' }
        }
      >
        {/* Background Elements */}
        <div className="absolute inset-0 overflow-hidden">
          <div
            className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full opacity-15"
            style={{ background: 'radial-gradient(circle, #A78BFA 0%, transparent 70%)' }}
          />
        </div>

        {/* Top - Logo */}
        <div className="relative z-10 pt-4">
          <div className="flex items-center gap-3">
            <img
              src="/Arizona_logo.png"
              alt="Arizona Sunshine"
              className="w-12 h-12 object-contain"
            />
            <div>
              <h1 className="text-xl font-bold text-white">Arizona Sunshine</h1>
              <p className="text-white/60 text-xs">Finance Transparency</p>
            </div>
          </div>
        </div>

        {/* Center - Main Content */}
        <div className="relative z-10">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 mb-6">
            <Sparkles size={16} className="text-[#A78BFA]" />
            <span className="text-[#A78BFA] text-sm font-semibold uppercase tracking-wider">Staff Portal</span>
          </div>

          {/* Headline */}
          <h2 className="text-4xl xl:text-5xl font-bold text-white leading-tight mb-6">
            Political <span style={{ color: '#A78BFA' }}>Accountability</span> Tracker
          </h2>

          {/* Tagline */}
          <p className="text-white/60 text-base w-[90%]">
            Empowering citizens with transparent access to campaign finance data and political spending insights.
          </p>
        </div>

        {/* Bottom - Footer */}
        <div className="relative z-10 pb-4">
          <p className="text-white/30 text-xs">
            &copy; {new Date().getFullYear()} Arizona Sunshine. Political Accountability Tracker.
          </p>
        </div>
      </div>

      {/* Right Side - Login Form */}
      <div className="flex-1 flex items-center justify-center p-6 sm:p-8 lg:p-12">
        <div className="w-full max-w-md">
          {/* Mobile Logo (shown only on mobile) */}
          <div className="lg:hidden text-center mb-6">
            <div className="flex items-center justify-center mb-3">
              <img
                src="/Arizona_logo.png"
                alt="Arizona Sunshine"
                className="w-12 h-12 object-contain"
              />
            </div>
            <h1 className={`text-xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
              Arizona Sunshine
            </h1>
            <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
              Staff Portal
            </p>
          </div>

          {/* Login Card */}
          <div
            className="rounded-3xl p-6 sm:p-8 border shadow-2xl"
            style={darkMode
              ? { backgroundColor: '#2D2844', borderColor: 'rgba(255, 255, 255, 0.05)' }
              : { backgroundColor: '#ffffff', borderColor: 'rgba(0, 0, 0, 0.05)' }
            }
          >
            <div className="mb-6">
              <div className="flex items-center gap-2 mb-1">
                <h2 className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                  Welcome Back
                </h2>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase bg-[#7163BA]/20 text-[#A78BFA]">
                  Staff
                </span>
              </div>
              <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                Sign in to access the transparency platform
              </p>
            </div>

            {/* Error Message */}
            {error && (
              <div className={`mb-6 p-4 rounded-xl flex items-center gap-3 ${
                darkMode
                  ? 'bg-red-900/20 border border-red-500/20'
                  : 'bg-red-50 border border-red-200'
              }`}>
                <AlertCircle className={darkMode ? 'text-red-400' : 'text-red-600'} size={20} />
                <p className={`text-sm ${darkMode ? 'text-red-300' : 'text-red-800'}`}>{error}</p>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Username Field */}
              <div>
                <label className={`block text-sm font-medium mb-1.5 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                  Username
                </label>
                <div className="relative">
                  <div className="absolute left-4 top-1/2 -translate-y-1/2">
                    <User size={18} className={darkMode ? 'text-gray-500' : 'text-gray-400'} />
                  </div>
                  <input
                    type="text"
                    name="username"
                    value={formData.username}
                    onChange={handleChange}
                    required
                    className={`w-full pl-12 pr-4 py-3 rounded-xl border outline-none transition-all ${
                      darkMode
                        ? 'bg-[#1F1B31] border-gray-700 text-white placeholder-gray-500 focus:border-[#7163BA] focus:ring-1 focus:ring-[#7163BA]'
                        : 'bg-gray-50 border-gray-200 text-gray-900 placeholder-gray-400 focus:border-[#7163BA] focus:ring-1 focus:ring-[#7163BA] focus:bg-white'
                    }`}
                    placeholder="Enter your username"
                  />
                </div>
              </div>

              {/* Password Field */}
              <div>
                <label className={`block text-sm font-medium mb-1.5 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                  Password
                </label>
                <div className="relative">
                  <div className="absolute left-4 top-1/2 -translate-y-1/2">
                    <Lock size={18} className={darkMode ? 'text-gray-500' : 'text-gray-400'} />
                  </div>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    required
                    className={`w-full pl-12 pr-12 py-3 rounded-xl border outline-none transition-all ${
                      darkMode
                        ? 'bg-[#1F1B31] border-gray-700 text-white placeholder-gray-500 focus:border-[#7163BA] focus:ring-1 focus:ring-[#7163BA]'
                        : 'bg-gray-50 border-gray-200 text-gray-900 placeholder-gray-400 focus:border-[#7163BA] focus:ring-1 focus:ring-[#7163BA] focus:bg-white'
                    }`}
                    placeholder="Enter your password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-4 top-1/2 -translate-y-1/2"
                  >
                    {showPassword ? (
                      <EyeOff size={18} className={darkMode ? 'text-gray-500' : 'text-gray-400'} />
                    ) : (
                      <Eye size={18} className={darkMode ? 'text-gray-500' : 'text-gray-400'} />
                    )}
                  </button>
                </div>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={loading}
                className="w-full py-4 rounded-xl bg-[#7163BA] hover:bg-[#5b4fa8] text-white font-semibold flex items-center justify-center gap-2 transition-all shadow-lg shadow-purple-500/20 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed mt-2"
              >
                {loading ? (
                  <>
                    <Loader size={20} className="animate-spin" />
                    Signing in...
                  </>
                ) : (
                  <>
                    <User size={20} />
                    Sign In
                    <ArrowRight size={18} className="ml-1" />
                  </>
                )}
              </button>
            </form>

            {/* Register Link */}
            <div className="mt-6 text-center">
              <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                Don't have an account?{' '}
                <Link
                  to="/register"
                  className="text-[#7163BA] font-semibold hover:underline"
                >
                  Create Account
                </Link>
              </p>
            </div>
          </div>

          {/* Mobile Footer */}
          <div className="lg:hidden mt-6 text-center">
            <p className={`text-xs ${darkMode ? 'text-gray-500' : 'text-gray-400'}`}>
              &copy; {new Date().getFullYear()} Arizona Sunshine. Political Accountability Tracker.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
