import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { register as apiRegister } from '../api/api';
import { useAuth } from '../context/AuthContext';
import { useDarkMode } from '../context/DarkModeContext';
import { Lock, Mail, User, Eye, EyeOff, AlertCircle, Loader, UserPlus, CheckCircle } from 'lucide-react';

export default function Register() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const { darkMode } = useDarkMode();

  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    passwordConfirm: '',
    firstName: '',
    lastName: '',
  });

  const [showPassword, setShowPassword] = useState(false);
  const [showPasswordConfirm, setShowPasswordConfirm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

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

    // Basic validation
    if (formData.password !== formData.passwordConfirm) {
      setError("Passwords don't match");
      setLoading(false);
      return;
    }

    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters long');
      setLoading(false);
      return;
    }

    try {
      const response = await apiRegister(
        formData.username,
        formData.email,
        formData.password,
        formData.passwordConfirm,
        formData.firstName,
        formData.lastName
      );

      setSuccess(true);

      // Auto-login after successful registration
      setTimeout(() => {
        login(response.user, response.tokens);
        navigate('/');
      }, 1500);
    } catch (err) {
      const errorMessage = err.response?.data?.username?.[0] ||
                          err.response?.data?.email?.[0] ||
                          err.response?.data?.password?.[0] ||
                          err.response?.data?.error ||
                          'Registration failed. Please try again.';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="min-h-screen flex items-center justify-center p-4 py-12"
      style={darkMode
        ? { background: '#1A1625' }
        : { background: 'linear-gradient(to bottom, #685994, #4c3e7c)' }
      }
    >
      <div className="w-full max-w-md">
        {/* Logo and Title */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <img
              src="/Arizona_logo.png"
              alt="Arizona Sunshine"
              className="w-16 h-16 object-contain opacity-95"
            />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">
            Arizona Sunshine
          </h1>
          <p className="text-white/70 text-sm">
            Create Your Admin Account
          </p>
        </div>

        {/* Register Card */}
        <div
          className="rounded-3xl p-8 border shadow-2xl"
          style={darkMode
            ? { backgroundColor: '#2D2844', borderColor: 'rgba(255, 255, 255, 0.05)' }
            : { backgroundColor: '#ffffff', borderColor: 'rgba(255, 255, 255, 0.2)' }
          }
        >
          <h2 className={`text-2xl font-bold mb-2 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
            Create Account
          </h2>
          <p className={`text-sm mb-6 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
            You'll be registered as an administrator with full access
          </p>

          {/* Success Message */}
          {success && (
            <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-xl flex items-center gap-3">
              <CheckCircle className="text-green-600" size={20} />
              <div>
                <p className="text-sm font-bold text-green-800">Account created successfully!</p>
                <p className="text-xs text-green-700">Redirecting to dashboard...</p>
              </div>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl flex items-center gap-3">
              <AlertCircle className="text-red-600" size={20} />
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Username Field */}
            <div>
              <label
                className={`block text-sm font-bold mb-2 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}
              >
                Username *
              </label>
              <div className="relative">
                <div className="absolute left-4 top-1/2 -translate-y-1/2">
                  <User size={18} className={darkMode ? 'text-gray-400' : 'text-gray-500'} />
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
                      : 'bg-white border-gray-300 text-gray-900 placeholder-gray-400 focus:border-[#7163BA] focus:ring-1 focus:ring-[#7163BA]'
                  }`}
                  placeholder="Choose a username"
                />
              </div>
            </div>

            {/* Email Field */}
            <div>
              <label
                className={`block text-sm font-bold mb-2 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}
              >
                Email *
              </label>
              <div className="relative">
                <div className="absolute left-4 top-1/2 -translate-y-1/2">
                  <Mail size={18} className={darkMode ? 'text-gray-400' : 'text-gray-500'} />
                </div>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  required
                  className={`w-full pl-12 pr-4 py-3 rounded-xl border outline-none transition-all ${
                    darkMode
                      ? 'bg-[#1F1B31] border-gray-700 text-white placeholder-gray-500 focus:border-[#7163BA] focus:ring-1 focus:ring-[#7163BA]'
                      : 'bg-white border-gray-300 text-gray-900 placeholder-gray-400 focus:border-[#7163BA] focus:ring-1 focus:ring-[#7163BA]'
                  }`}
                  placeholder="your.email@example.com"
                />
              </div>
            </div>

            {/* Name Fields (Optional) */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label
                  className={`block text-sm font-bold mb-2 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}
                >
                  First Name
                </label>
                <input
                  type="text"
                  name="firstName"
                  value={formData.firstName}
                  onChange={handleChange}
                  className={`w-full px-4 py-3 rounded-xl border outline-none transition-all ${
                    darkMode
                      ? 'bg-[#1F1B31] border-gray-700 text-white placeholder-gray-500 focus:border-[#7163BA] focus:ring-1 focus:ring-[#7163BA]'
                      : 'bg-white border-gray-300 text-gray-900 placeholder-gray-400 focus:border-[#7163BA] focus:ring-1 focus:ring-[#7163BA]'
                  }`}
                  placeholder="Optional"
                />
              </div>
              <div>
                <label
                  className={`block text-sm font-bold mb-2 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}
                >
                  Last Name
                </label>
                <input
                  type="text"
                  name="lastName"
                  value={formData.lastName}
                  onChange={handleChange}
                  className={`w-full px-4 py-3 rounded-xl border outline-none transition-all ${
                    darkMode
                      ? 'bg-[#1F1B31] border-gray-700 text-white placeholder-gray-500 focus:border-[#7163BA] focus:ring-1 focus:ring-[#7163BA]'
                      : 'bg-white border-gray-300 text-gray-900 placeholder-gray-400 focus:border-[#7163BA] focus:ring-1 focus:ring-[#7163BA]'
                  }`}
                  placeholder="Optional"
                />
              </div>
            </div>

            {/* Password Field */}
            <div>
              <label
                className={`block text-sm font-bold mb-2 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}
              >
                Password *
              </label>
              <div className="relative">
                <div className="absolute left-4 top-1/2 -translate-y-1/2">
                  <Lock size={18} className={darkMode ? 'text-gray-400' : 'text-gray-500'} />
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
                      : 'bg-white border-gray-300 text-gray-900 placeholder-gray-400 focus:border-[#7163BA] focus:ring-1 focus:ring-[#7163BA]'
                  }`}
                  placeholder="Min. 8 characters"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2"
                >
                  {showPassword ? (
                    <EyeOff size={18} className={darkMode ? 'text-gray-400' : 'text-gray-500'} />
                  ) : (
                    <Eye size={18} className={darkMode ? 'text-gray-400' : 'text-gray-500'} />
                  )}
                </button>
              </div>
            </div>

            {/* Confirm Password Field */}
            <div>
              <label
                className={`block text-sm font-bold mb-2 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}
              >
                Confirm Password *
              </label>
              <div className="relative">
                <div className="absolute left-4 top-1/2 -translate-y-1/2">
                  <Lock size={18} className={darkMode ? 'text-gray-400' : 'text-gray-500'} />
                </div>
                <input
                  type={showPasswordConfirm ? 'text' : 'password'}
                  name="passwordConfirm"
                  value={formData.passwordConfirm}
                  onChange={handleChange}
                  required
                  className={`w-full pl-12 pr-12 py-3 rounded-xl border outline-none transition-all ${
                    darkMode
                      ? 'bg-[#1F1B31] border-gray-700 text-white placeholder-gray-500 focus:border-[#7163BA] focus:ring-1 focus:ring-[#7163BA]'
                      : 'bg-white border-gray-300 text-gray-900 placeholder-gray-400 focus:border-[#7163BA] focus:ring-1 focus:ring-[#7163BA]'
                  }`}
                  placeholder="Re-enter password"
                />
                <button
                  type="button"
                  onClick={() => setShowPasswordConfirm(!showPasswordConfirm)}
                  className="absolute right-4 top-1/2 -translate-y-1/2"
                >
                  {showPasswordConfirm ? (
                    <EyeOff size={18} className={darkMode ? 'text-gray-400' : 'text-gray-500'} />
                  ) : (
                    <Eye size={18} className={darkMode ? 'text-gray-400' : 'text-gray-500'} />
                  )}
                </button>
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading || success}
              className="w-full py-4 rounded-2xl bg-[#7163BA] hover:bg-[#5b4fa8] text-white font-bold flex items-center justify-center gap-3 transition-all shadow-lg shadow-purple-500/20 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed mt-6"
            >
              {loading ? (
                <>
                  <Loader size={20} className="animate-spin" />
                  Creating account...
                </>
              ) : success ? (
                <>
                  <CheckCircle size={20} />
                  Account created!
                </>
              ) : (
                <>
                  <UserPlus size={20} />
                  Create Admin Account
                </>
              )}
            </button>
          </form>

          {/* Login Link */}
          <div className="mt-6 text-center">
            <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
              Already have an account?{' '}
              <Link
                to="/login"
                className="text-[#7163BA] font-bold hover:underline"
              >
                Sign In
              </Link>
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center">
          <p className="text-white/50 text-xs">
            &copy; 2025 Arizona Sunshine. Political Accountability Tracker.
          </p>
        </div>
      </div>
    </div>
  );
}
