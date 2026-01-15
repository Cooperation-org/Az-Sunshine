import { useEffect } from 'react';

/**
 * Security protection hook - prevents right-click, DevTools, and copy/paste
 * This provides React-level protection in addition to the index.html script
 */
export function useSecurityProtection() {
  useEffect(() => {
    // Prevent right-click context menu
    const handleContextMenu = (e) => {
      e.preventDefault();
      e.stopPropagation();
      return false;
    };

    // Prevent keyboard shortcuts for DevTools and view source
    const handleKeyDown = (e) => {
      // F12 - DevTools
      if (e.key === 'F12' || e.keyCode === 123) {
        e.preventDefault();
        e.stopPropagation();
        return false;
      }

      // Ctrl/Cmd + Shift + I - DevTools
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && (e.key === 'I' || e.key === 'i' || e.keyCode === 73)) {
        e.preventDefault();
        e.stopPropagation();
        return false;
      }

      // Ctrl/Cmd + Shift + J - Console
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && (e.key === 'J' || e.key === 'j' || e.keyCode === 74)) {
        e.preventDefault();
        e.stopPropagation();
        return false;
      }

      // Ctrl/Cmd + Shift + C - Element Inspector
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && (e.key === 'C' || e.key === 'c' || e.keyCode === 67)) {
        e.preventDefault();
        e.stopPropagation();
        return false;
      }

      // Ctrl/Cmd + U - View Source
      if ((e.ctrlKey || e.metaKey) && (e.key === 'U' || e.key === 'u' || e.keyCode === 85)) {
        e.preventDefault();
        e.stopPropagation();
        return false;
      }

      // Ctrl/Cmd + S - Save Page
      if ((e.ctrlKey || e.metaKey) && (e.key === 'S' || e.key === 's' || e.keyCode === 83)) {
        e.preventDefault();
        e.stopPropagation();
        return false;
      }
    };

    // Prevent drag start
    const handleDragStart = (e) => {
      e.preventDefault();
      return false;
    };

    // Prevent copy (except in input fields)
    const handleCopy = (e) => {
      const tagName = e.target.tagName;
      if (tagName !== 'INPUT' && tagName !== 'TEXTAREA') {
        e.preventDefault();
        return false;
      }
    };

    // Prevent select start (text selection)
    const handleSelectStart = (e) => {
      const tagName = e.target.tagName;
      if (tagName !== 'INPUT' && tagName !== 'TEXTAREA') {
        e.preventDefault();
        return false;
      }
    };

    // Add event listeners with capture phase for maximum priority
    document.addEventListener('contextmenu', handleContextMenu, true);
    document.addEventListener('keydown', handleKeyDown, true);
    document.addEventListener('dragstart', handleDragStart, true);
    document.addEventListener('copy', handleCopy, true);
    document.addEventListener('selectstart', handleSelectStart, true);

    // Also add to window for extra coverage
    window.addEventListener('contextmenu', handleContextMenu, true);
    window.addEventListener('keydown', handleKeyDown, true);

    // Cleanup
    return () => {
      document.removeEventListener('contextmenu', handleContextMenu, true);
      document.removeEventListener('keydown', handleKeyDown, true);
      document.removeEventListener('dragstart', handleDragStart, true);
      document.removeEventListener('copy', handleCopy, true);
      document.removeEventListener('selectstart', handleSelectStart, true);
      window.removeEventListener('contextmenu', handleContextMenu, true);
      window.removeEventListener('keydown', handleKeyDown, true);
    };
  }, []);
}

export default useSecurityProtection;
