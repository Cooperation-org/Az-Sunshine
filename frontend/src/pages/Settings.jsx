import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useDarkMode } from '../context/DarkModeContext';
import { updateProfile, changePassword } from '../api/api';
import Sidebar from '../components/Sidebar';
import {
  User, Mail, Shield, Sun, Moon, Bell, Lock, LogOut, Pencil, X, Check, Camera, Loader, AlertCircle, CheckCircle
} from 'lucide-react';

export default function Settings() {
  const { user, logout, updateUser } = useAuth();
  const { darkMode, toggleDarkMode } = useDarkMode();
  const [notifications, setNotifications] = useState(true);

  // Edit states
  const [editingField, setEditingField] = useState(null);
  const [editValues, setEditValues] = useState({
    username: user?.username || '',
    email: user?.email || '',
    firstName: user?.first_name || '',
    lastName: user?.last_name || '',
  });
  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleLogout = () => {
    logout();
    window.location.href = '/login';
  };

  const handleEdit = (field) => {
    setEditingField(field);
    setEditValues({
      ...editValues,
      [field]: user?.[field] || '',
    });
  };

  const handleSave = async (field) => {
    setSaving(true);
    setError('');
    setSuccess('');

    try {
      const data = { [field]: editValues[field] };
      const response = await updateProfile(data);

      // Update local user state
      if (updateUser && response.user) {
        updateUser(response.user);
      }

      setSuccess('Profile updated successfully');
      setEditingField(null);
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      const errorMsg = err.response?.data?.[field]?.[0] || err.response?.data?.error || 'Failed to update profile';
      setError(errorMsg);
      setTimeout(() => setError(''), 5000);
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    setEditingField(null);
    setEditValues({
      username: user?.username || '',
      email: user?.email || '',
      firstName: user?.first_name || '',
      lastName: user?.last_name || '',
    });
  };

  const handlePasswordChange = async () => {
    if (passwordData.newPassword !== passwordData.confirmPassword) {
      setError("Passwords don't match");
      return;
    }
    setSaving(true);
    setError('');
    setSuccess('');

    try {
      await changePassword(
        passwordData.currentPassword,
        passwordData.newPassword,
        passwordData.confirmPassword
      );

      setSuccess('Password changed successfully');
      setShowPasswordModal(false);
      setPasswordData({ currentPassword: '', newPassword: '', confirmPassword: '' });
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      const errorMsg = err.response?.data?.current_password?.[0] ||
                       err.response?.data?.new_password?.[0] ||
                       err.response?.data?.confirm_password?.[0] ||
                       err.response?.data?.error ||
                       'Failed to change password';
      setError(errorMsg);
    } finally {
      setSaving(false);
    }
  };

  const ProfileField = ({ icon: Icon, label, value, field, editable = true }) => (
    <div className={`flex items-center gap-3 p-4 rounded-xl ${darkMode ? 'bg-[#1F1B31]' : 'bg-gray-50'}`}>
      <Icon size={18} className={darkMode ? 'text-gray-400' : 'text-gray-500'} />
      <div className="flex-1 min-w-0">
        <p className={`text-xs ${darkMode ? 'text-gray-500' : 'text-gray-400'}`}>{label}</p>
        {editingField === field ? (
          <input
            type={field === 'email' ? 'email' : 'text'}
            value={editValues[field]}
            onChange={(e) => setEditValues({ ...editValues, [field]: e.target.value })}
            className={`w-full text-sm font-medium mt-1 px-2 py-1 rounded-lg border outline-none ${
              darkMode
                ? 'bg-[#2D2844] border-gray-600 text-white focus:border-[#7163BA]'
                : 'bg-white border-gray-300 text-gray-900 focus:border-[#7163BA]'
            }`}
            autoFocus
          />
        ) : (
          <p className={`text-sm font-medium truncate ${darkMode ? 'text-white' : 'text-gray-900'}`}>
            {value || 'N/A'}
          </p>
        )}
      </div>
      {editable && (
        editingField === field ? (
          <div className="flex items-center gap-2">
            <button
              onClick={() => handleSave(field)}
              disabled={saving}
              className="p-1.5 rounded-lg bg-green-500/20 text-green-500 hover:bg-green-500/30 transition-colors"
            >
              <Check size={16} />
            </button>
            <button
              onClick={handleCancel}
              className="p-1.5 rounded-lg bg-red-500/20 text-red-400 hover:bg-red-500/30 transition-colors"
            >
              <X size={16} />
            </button>
          </div>
        ) : (
          <button
            onClick={() => handleEdit(field)}
            className={`p-2 rounded-lg transition-colors ${
              darkMode ? 'hover:bg-white/10 text-gray-400' : 'hover:bg-gray-200 text-gray-500'
            }`}
          >
            <Pencil size={16} />
          </button>
        )
      )}
    </div>
  );

  return (
    <div className={`min-h-screen flex ${darkMode ? 'bg-[#1A1625]' : 'bg-gray-50'}`}>
      <Sidebar />

      <main className="flex-1 p-6 md:p-8 lg:p-10 overflow-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
            Settings
          </h1>
          <p className={`text-sm mt-1 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
            Manage your account and preferences
          </p>
        </div>

        {/* Success/Error Messages */}
        {success && (
          <div className={`max-w-3xl mb-6 p-4 rounded-xl flex items-center gap-3 ${
            darkMode
              ? 'bg-green-900/20 border border-green-500/20'
              : 'bg-green-50 border border-green-200'
          }`}>
            <CheckCircle className={darkMode ? 'text-green-400' : 'text-green-600'} size={20} />
            <p className={`text-sm ${darkMode ? 'text-green-300' : 'text-green-800'}`}>{success}</p>
          </div>
        )}

        {error && (
          <div className={`max-w-3xl mb-6 p-4 rounded-xl flex items-center gap-3 ${
            darkMode
              ? 'bg-red-900/20 border border-red-500/20'
              : 'bg-red-50 border border-red-200'
          }`}>
            <AlertCircle className={darkMode ? 'text-red-400' : 'text-red-600'} size={20} />
            <p className={`text-sm ${darkMode ? 'text-red-300' : 'text-red-800'}`}>{error}</p>
          </div>
        )}

        <div className="max-w-3xl space-y-6">
          {/* Profile Section */}
          <div
            className={`rounded-2xl border p-6 ${
              darkMode
                ? 'bg-[#2D2844] border-gray-700'
                : 'bg-white border-gray-200'
            }`}
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className={`text-lg font-semibold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                Profile
              </h2>
            </div>

            {/* Avatar */}
            <div className="flex items-center gap-4 mb-6">
              <div className="relative group">
                <div className="w-20 h-20 rounded-2xl bg-[#7163BA] flex items-center justify-center text-white text-2xl font-bold">
                  {user?.username?.substring(0, 2).toUpperCase() || 'US'}
                </div>
                <button className={`absolute inset-0 rounded-2xl flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity ${
                  darkMode ? 'bg-black/50' : 'bg-black/40'
                }`}>
                  <Camera size={24} className="text-white" />
                </button>
              </div>
              <div>
                <p className={`font-semibold text-lg ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                  {user?.username || 'User'}
                </p>
                <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                  Staff Account
                </p>
              </div>
            </div>

            <div className="space-y-3">
              <ProfileField icon={User} label="Username" value={user?.username} field="username" />
              <ProfileField icon={Mail} label="Email" value={user?.email} field="email" />
              <ProfileField icon={Shield} label="Role" value={user?.is_staff ? 'Administrator' : 'Staff Member'} field="role" editable={false} />
            </div>
          </div>

          {/* Preferences Section */}
          <div
            className={`rounded-2xl border p-6 ${
              darkMode
                ? 'bg-[#2D2844] border-gray-700'
                : 'bg-white border-gray-200'
            }`}
          >
            <h2 className={`text-lg font-semibold mb-4 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
              Preferences
            </h2>

            <div className="space-y-2">
              {/* Dark Mode Toggle */}
              <button
                onClick={toggleDarkMode}
                className={`w-full flex items-center justify-between p-4 rounded-xl transition-colors ${
                  darkMode ? 'hover:bg-[#1F1B31]' : 'hover:bg-gray-50'
                }`}
              >
                <div className="flex items-center gap-3">
                  {darkMode ? (
                    <Moon size={20} className="text-[#A78BFA]" />
                  ) : (
                    <Sun size={20} className="text-yellow-500" />
                  )}
                  <div className="text-left">
                    <p className={`text-sm font-medium ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                      Dark Mode
                    </p>
                    <p className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                      {darkMode ? 'Currently using dark theme' : 'Currently using light theme'}
                    </p>
                  </div>
                </div>
                <div
                  className={`w-12 h-7 rounded-full p-1 transition-colors ${
                    darkMode ? 'bg-[#7163BA]' : 'bg-gray-300'
                  }`}
                >
                  <div
                    className={`w-5 h-5 rounded-full bg-white transition-transform ${
                      darkMode ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </div>
              </button>

              {/* Notifications Toggle */}
              <button
                onClick={() => setNotifications(!notifications)}
                className={`w-full flex items-center justify-between p-4 rounded-xl transition-colors ${
                  darkMode ? 'hover:bg-[#1F1B31]' : 'hover:bg-gray-50'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Bell size={20} className={darkMode ? 'text-gray-400' : 'text-gray-500'} />
                  <div className="text-left">
                    <p className={`text-sm font-medium ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                      Notifications
                    </p>
                    <p className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                      Receive alerts for new filings
                    </p>
                  </div>
                </div>
                <div
                  className={`w-12 h-7 rounded-full p-1 transition-colors ${
                    notifications ? 'bg-[#7163BA]' : darkMode ? 'bg-gray-600' : 'bg-gray-300'
                  }`}
                >
                  <div
                    className={`w-5 h-5 rounded-full bg-white transition-transform ${
                      notifications ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </div>
              </button>
            </div>
          </div>

          {/* Security Section */}
          <div
            className={`rounded-2xl border p-6 ${
              darkMode
                ? 'bg-[#2D2844] border-gray-700'
                : 'bg-white border-gray-200'
            }`}
          >
            <h2 className={`text-lg font-semibold mb-4 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
              Security
            </h2>

            <div className="space-y-2">
              <button
                onClick={() => setShowPasswordModal(true)}
                className={`w-full flex items-center justify-between p-4 rounded-xl transition-colors ${
                  darkMode ? 'hover:bg-[#1F1B31]' : 'hover:bg-gray-50'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Lock size={20} className={darkMode ? 'text-gray-400' : 'text-gray-500'} />
                  <div className="text-left">
                    <p className={`text-sm font-medium ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                      Change Password
                    </p>
                    <p className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                      Update your password
                    </p>
                  </div>
                </div>
                <Pencil size={16} className={darkMode ? 'text-gray-500' : 'text-gray-400'} />
              </button>

              <button
                className={`w-full flex items-center justify-between p-4 rounded-xl transition-colors ${
                  darkMode ? 'hover:bg-[#1F1B31]' : 'hover:bg-gray-50'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Shield size={20} className={darkMode ? 'text-gray-400' : 'text-gray-500'} />
                  <div className="text-left">
                    <p className={`text-sm font-medium ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                      Two-Factor Authentication
                    </p>
                    <p className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                      Add an extra layer of security
                    </p>
                  </div>
                </div>
                <Pencil size={16} className={darkMode ? 'text-gray-500' : 'text-gray-400'} />
              </button>
            </div>
          </div>

          {/* Logout Section */}
          <div
            className={`rounded-2xl border p-6 ${
              darkMode
                ? 'bg-[#2D2844] border-gray-700'
                : 'bg-white border-gray-200'
            }`}
          >
            <button
              onClick={handleLogout}
              className={`w-full flex items-center justify-center gap-2 p-4 rounded-xl transition-colors ${
                darkMode
                  ? 'bg-red-500/10 text-red-400 hover:bg-red-500/20'
                  : 'bg-red-50 text-red-600 hover:bg-red-100'
              }`}
            >
              <LogOut size={18} />
              <span className="font-medium">Sign Out</span>
            </button>
          </div>

          {/* Footer */}
          <div className="text-center pt-4 pb-8">
            <p className={`text-xs ${darkMode ? 'text-gray-600' : 'text-gray-400'}`}>
              &copy; {new Date().getFullYear()} Arizona Sunshine. Political Accountability Tracker.
            </p>
          </div>
        </div>
      </main>

      {/* Password Change Modal */}
      {showPasswordModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div
            className={`w-full max-w-md rounded-2xl p-6 ${
              darkMode ? 'bg-[#2D2844]' : 'bg-white'
            }`}
          >
            <div className="flex items-center justify-between mb-6">
              <h3 className={`text-lg font-semibold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                Change Password
              </h3>
              <button
                onClick={() => { setShowPasswordModal(false); setError(''); }}
                className={`p-2 rounded-lg ${darkMode ? 'hover:bg-white/10' : 'hover:bg-gray-100'}`}
              >
                <X size={20} className={darkMode ? 'text-gray-400' : 'text-gray-500'} />
              </button>
            </div>

            {error && (
              <div className={`mb-4 p-3 rounded-xl flex items-center gap-2 ${
                darkMode
                  ? 'bg-red-900/20 border border-red-500/20'
                  : 'bg-red-50 border border-red-200'
              }`}>
                <AlertCircle className={darkMode ? 'text-red-400' : 'text-red-600'} size={18} />
                <p className={`text-sm ${darkMode ? 'text-red-300' : 'text-red-800'}`}>{error}</p>
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className={`block text-sm font-medium mb-1.5 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                  Current Password
                </label>
                <input
                  type="password"
                  value={passwordData.currentPassword}
                  onChange={(e) => setPasswordData({ ...passwordData, currentPassword: e.target.value })}
                  className={`w-full px-4 py-3 rounded-xl border outline-none transition-all ${
                    darkMode
                      ? 'bg-[#1F1B31] border-gray-700 text-white focus:border-[#7163BA]'
                      : 'bg-gray-50 border-gray-200 text-gray-900 focus:border-[#7163BA]'
                  }`}
                  placeholder="Enter current password"
                />
              </div>

              <div>
                <label className={`block text-sm font-medium mb-1.5 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                  New Password
                </label>
                <input
                  type="password"
                  value={passwordData.newPassword}
                  onChange={(e) => setPasswordData({ ...passwordData, newPassword: e.target.value })}
                  className={`w-full px-4 py-3 rounded-xl border outline-none transition-all ${
                    darkMode
                      ? 'bg-[#1F1B31] border-gray-700 text-white focus:border-[#7163BA]'
                      : 'bg-gray-50 border-gray-200 text-gray-900 focus:border-[#7163BA]'
                  }`}
                  placeholder="Enter new password"
                />
              </div>

              <div>
                <label className={`block text-sm font-medium mb-1.5 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                  Confirm New Password
                </label>
                <input
                  type="password"
                  value={passwordData.confirmPassword}
                  onChange={(e) => setPasswordData({ ...passwordData, confirmPassword: e.target.value })}
                  className={`w-full px-4 py-3 rounded-xl border outline-none transition-all ${
                    darkMode
                      ? 'bg-[#1F1B31] border-gray-700 text-white focus:border-[#7163BA]'
                      : 'bg-gray-50 border-gray-200 text-gray-900 focus:border-[#7163BA]'
                  }`}
                  placeholder="Confirm new password"
                />
              </div>

              <button
                onClick={handlePasswordChange}
                disabled={saving || !passwordData.currentPassword || !passwordData.newPassword || !passwordData.confirmPassword}
                className="w-full py-3 rounded-xl bg-[#7163BA] hover:bg-[#5b4fa8] text-white font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed mt-2"
              >
                {saving ? 'Saving...' : 'Update Password'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
