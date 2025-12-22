import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { login as apiLogin } from '../api/api';
import { useAuth } from '../context/AuthContext';
import { useDarkMode } from '../context/DarkModeContext';
import { Lock, Mail, Eye, EyeOff, AlertCircle, Loader, LogIn } from 'lucide-react';

export default function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const { darkMode } = useDarkMode();

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
      className="min-h-screen flex items-center justify-center p-4"
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
            Finance Transparency Platform
          </p>
        </div>

        {/* Login Card */}
        <div
          className="rounded-3xl p-8 border shadow-2xl"
          style={darkMode
            ? { backgroundColor: '#2D2844', borderColor: 'rgba(255, 255, 255, 0.05)' }
            : { backgroundColor: '#ffffff', borderColor: 'rgba(255, 255, 255, 0.2)' }
          }
        >
          <h2 className={`text-2xl font-bold mb-6 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
            Welcome Back
          </h2>

          {/* Error Message */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl flex items-center gap-3">
              <AlertCircle className="text-red-600" size={20} />
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Username Field */}
            <div>
              <label
                className={`block text-sm font-bold mb-2 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}
              >
                Username
              </label>
              <div className="relative">
                <div className="absolute left-4 top-1/2 -translate-y-1/2">
                  <Mail size={18} className={darkMode ? 'text-gray-400' : 'text-gray-500'} />
                </div>
                <input
                  type="text"
                  name="username"
                  value={formData.username}
                  onChange={handleChange}
                  required
                  className={`w-full pl-12 pr-4 py-3.5 rounded-xl border outline-none transition-all ${
                    darkMode
                      ? 'bg-[#1F1B31] border-gray-700 text-white placeholder-gray-500 focus:border-[#7163BA] focus:ring-1 focus:ring-[#7163BA]'
                      : 'bg-white border-gray-300 text-gray-900 placeholder-gray-400 focus:border-[#7163BA] focus:ring-1 focus:ring-[#7163BA]'
                  }`}
                  placeholder="Enter your username"
                />
              </div>
            </div>

            {/* Password Field */}
            <div>
              <label
                className={`block text-sm font-bold mb-2 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}
              >
                Password
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
                  className={`w-full pl-12 pr-12 py-3.5 rounded-xl border outline-none transition-all ${
                    darkMode
                      ? 'bg-[#1F1B31] border-gray-700 text-white placeholder-gray-500 focus:border-[#7163BA] focus:ring-1 focus:ring-[#7163BA]'
                      : 'bg-white border-gray-300 text-gray-900 placeholder-gray-400 focus:border-[#7163BA] focus:ring-1 focus:ring-[#7163BA]'
                  }`}
                  placeholder="Enter your password"
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

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-4 rounded-2xl bg-[#7163BA] hover:bg-[#5b4fa8] text-white font-bold flex items-center justify-center gap-3 transition-all shadow-lg shadow-purple-500/20 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <Loader size={20} className="animate-spin" />
                  Signing in...
                </>
              ) : (
                <>
                  <LogIn size={20} />
                  Sign In
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
                className="text-[#7163BA] font-bold hover:underline"
              >
                Create Account
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
