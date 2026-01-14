import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { register as apiRegister } from '../api/api';
import { useAuth } from '../context/AuthContext';
import { useDarkMode } from '../context/DarkModeContext';
import {
  Lock, Mail, User, Eye, EyeOff, AlertCircle, Loader, UserPlus, CheckCircle,
  Sun, Moon, Sparkles, ArrowRight, Check
} from 'lucide-react';

export default function Register() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const { darkMode, toggleDarkMode } = useDarkMode();

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

  // Password strength indicator
  const getPasswordStrength = () => {
    const password = formData.password;
    if (!password) return { strength: 0, label: '', color: '' };

    let strength = 0;
    if (password.length >= 8) strength++;
    if (password.match(/[a-z]/) && password.match(/[A-Z]/)) strength++;
    if (password.match(/[0-9]/)) strength++;
    if (password.match(/[^a-zA-Z0-9]/)) strength++;

    const levels = [
      { label: 'Weak', color: 'bg-red-500' },
      { label: 'Fair', color: 'bg-orange-500' },
      { label: 'Good', color: 'bg-yellow-500' },
      { label: 'Strong', color: 'bg-green-500' },
    ];

    return { strength, ...levels[strength - 1] || { label: '', color: '' } };
  };

  const passwordStrength = getPasswordStrength();

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
        {/* Background Elements with pulse */}
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
            <span className="text-[#A78BFA] text-sm font-semibold uppercase tracking-wider">Join the Platform</span>
          </div>

          {/* Headline */}
          <h2 className="text-4xl xl:text-5xl font-bold text-white leading-tight mb-6">
            Become a <span style={{ color: '#A78BFA' }}>Transparency</span> Champion
          </h2>

          {/* Tagline */}
          <p className="text-white/60 text-base w-[90%]">
            Join our mission to bring accountability and transparency to political campaign financing.
          </p>
        </div>

        {/* Bottom - Footer */}
        <div className="relative z-10 pb-4">
          <p className="text-white/30 text-xs">
            &copy; {new Date().getFullYear()} Arizona Sunshine. Political Accountability Tracker.
          </p>
        </div>
      </div>

      {/* Right Side - Register Form */}
      <div className="flex-1 flex items-center justify-center p-6 sm:p-8 lg:p-12 overflow-y-auto">
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
              Create Your Account
            </p>
          </div>

          {/* Register Card */}
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
                  Create Account
                </h2>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase bg-[#7163BA]/20 text-[#A78BFA]">
                  Staff
                </span>
              </div>
              <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                Get full access to the transparency platform
              </p>
            </div>

            {/* Success Message */}
            {success && (
              <div className={`mb-6 p-4 rounded-xl flex items-center gap-3 ${
                darkMode
                  ? 'bg-green-900/20 border border-green-500/20'
                  : 'bg-green-50 border border-green-200'
              }`}>
                <CheckCircle className={darkMode ? 'text-green-400' : 'text-green-600'} size={20} />
                <div>
                  <p className={`text-sm font-bold ${darkMode ? 'text-green-300' : 'text-green-800'}`}>Account created successfully!</p>
                  <p className={`text-xs ${darkMode ? 'text-green-400' : 'text-green-700'}`}>Redirecting to dashboard...</p>
                </div>
              </div>
            )}

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
                  Username <span className="text-red-400">*</span>
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
                    placeholder="Choose a username"
                  />
                </div>
              </div>

              {/* Email Field */}
              <div>
                <label className={`block text-sm font-medium mb-1.5 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                  Email <span className="text-red-400">*</span>
                </label>
                <div className="relative">
                  <div className="absolute left-4 top-1/2 -translate-y-1/2">
                    <Mail size={18} className={darkMode ? 'text-gray-500' : 'text-gray-400'} />
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
                        : 'bg-gray-50 border-gray-200 text-gray-900 placeholder-gray-400 focus:border-[#7163BA] focus:ring-1 focus:ring-[#7163BA] focus:bg-white'
                    }`}
                    placeholder="your.email@example.com"
                  />
                </div>
              </div>

              {/* Name Fields (Optional) */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className={`block text-sm font-medium mb-1.5 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
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
                        : 'bg-gray-50 border-gray-200 text-gray-900 placeholder-gray-400 focus:border-[#7163BA] focus:ring-1 focus:ring-[#7163BA] focus:bg-white'
                    }`}
                    placeholder="Optional"
                  />
                </div>
                <div>
                  <label className={`block text-sm font-medium mb-1.5 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
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
                        : 'bg-gray-50 border-gray-200 text-gray-900 placeholder-gray-400 focus:border-[#7163BA] focus:ring-1 focus:ring-[#7163BA] focus:bg-white'
                    }`}
                    placeholder="Optional"
                  />
                </div>
              </div>

              {/* Password Field */}
              <div>
                <label className={`block text-sm font-medium mb-1.5 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                  Password <span className="text-red-400">*</span>
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
                    placeholder="Min. 8 characters"
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
                {/* Password Strength Indicator */}
                {formData.password && (
                  <div className="mt-2">
                    <div className="flex gap-1 mb-1">
                      {[1, 2, 3, 4].map((level) => (
                        <div
                          key={level}
                          className={`h-1 flex-1 rounded-full transition-all ${
                            level <= passwordStrength.strength
                              ? passwordStrength.color
                              : darkMode ? 'bg-gray-700' : 'bg-gray-200'
                          }`}
                        />
                      ))}
                    </div>
                    <p className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                      Password strength: <span className="font-medium">{passwordStrength.label || 'Too short'}</span>
                    </p>
                  </div>
                )}
              </div>

              {/* Confirm Password Field */}
              <div>
                <label className={`block text-sm font-medium mb-1.5 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                  Confirm Password <span className="text-red-400">*</span>
                </label>
                <div className="relative">
                  <div className="absolute left-4 top-1/2 -translate-y-1/2">
                    <Lock size={18} className={darkMode ? 'text-gray-500' : 'text-gray-400'} />
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
                        : 'bg-gray-50 border-gray-200 text-gray-900 placeholder-gray-400 focus:border-[#7163BA] focus:ring-1 focus:ring-[#7163BA] focus:bg-white'
                    }`}
                    placeholder="Re-enter password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPasswordConfirm(!showPasswordConfirm)}
                    className="absolute right-4 top-1/2 -translate-y-1/2"
                  >
                    {showPasswordConfirm ? (
                      <EyeOff size={18} className={darkMode ? 'text-gray-500' : 'text-gray-400'} />
                    ) : (
                      <Eye size={18} className={darkMode ? 'text-gray-500' : 'text-gray-400'} />
                    )}
                  </button>
                </div>
                {/* Password Match Indicator */}
                {formData.passwordConfirm && (
                  <div className="mt-2 flex items-center gap-1.5">
                    {formData.password === formData.passwordConfirm ? (
                      <>
                        <Check size={14} className="text-green-500" />
                        <span className="text-xs text-green-500">Passwords match</span>
                      </>
                    ) : (
                      <>
                        <AlertCircle size={14} className="text-red-400" />
                        <span className="text-xs text-red-400">Passwords don't match</span>
                      </>
                    )}
                  </div>
                )}
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={loading || success}
                className="w-full py-4 rounded-xl bg-[#7163BA] hover:bg-[#5b4fa8] text-white font-semibold flex items-center justify-center gap-2 transition-all shadow-lg shadow-purple-500/20 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed mt-2"
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
                    Create Account
                    <ArrowRight size={18} className="ml-1" />
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
                  className="text-[#7163BA] font-semibold hover:underline"
                >
                  Sign In
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
