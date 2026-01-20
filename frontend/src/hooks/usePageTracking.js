/**
 * Page View Tracking Hook
 * Tracks page views, session duration, and user engagement for analytics
 */

import { useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1/';

// Generate or retrieve visitor ID
const getVisitorId = () => {
  let visitorId = localStorage.getItem('_az_visitor_id');
  if (!visitorId) {
    visitorId = 'v_' + Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
    localStorage.setItem('_az_visitor_id', visitorId);
  }
  return visitorId;
};

// Generate session ID (refreshes after 30 minutes of inactivity)
const getSessionId = () => {
  const SESSION_TIMEOUT = 30 * 60 * 1000; // 30 minutes
  let sessionData = JSON.parse(sessionStorage.getItem('_az_session') || '{}');
  const now = Date.now();

  if (!sessionData.id || (now - sessionData.lastActivity) > SESSION_TIMEOUT) {
    sessionData = {
      id: 's_' + Math.random().toString(36).substring(2, 15),
      startTime: now,
      pageCount: 0,
    };
  }

  sessionData.lastActivity = now;
  sessionData.pageCount = (sessionData.pageCount || 0) + 1;
  sessionStorage.setItem('_az_session', JSON.stringify(sessionData));

  return sessionData;
};

// Track page view
const trackPageView = async (path, referrer, candidateId = null) => {
  try {
    const visitorId = getVisitorId();
    const sessionData = getSessionId();

    const payload = {
      path,
      referrer: referrer || document.referrer || '',
      visitor_id: visitorId,
      session_id: sessionData.id,
      page_count: sessionData.pageCount,
      title: document.title,
      screen_width: window.innerWidth,
      screen_height: window.innerHeight,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      language: navigator.language,
      utm_source: new URLSearchParams(window.location.search).get('utm_source') || '',
      utm_medium: new URLSearchParams(window.location.search).get('utm_medium') || '',
      utm_campaign: new URLSearchParams(window.location.search).get('utm_campaign') || '',
    };

    // Add candidate info if on candidate page
    if (candidateId) {
      payload.candidate_id = candidateId;
    }

    // Send tracking request (fire and forget)
    await fetch(`${API_BASE_URL}analytics/track-pageview/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
      keepalive: true, // Ensures the request completes even if page navigates away
    });
  } catch (error) {
    // Silent fail - don't interrupt user experience
    console.debug('Analytics tracking failed:', error);
  }
};

// Track time on page
const trackTimeOnPage = async (path, duration) => {
  try {
    const visitorId = getVisitorId();
    const sessionData = JSON.parse(sessionStorage.getItem('_az_session') || '{}');

    await fetch(`${API_BASE_URL}analytics/track-engagement/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        path,
        visitor_id: visitorId,
        session_id: sessionData.id,
        time_on_page: Math.round(duration / 1000), // Convert to seconds
      }),
      keepalive: true,
    });
  } catch (error) {
    console.debug('Engagement tracking failed:', error);
  }
};

export const usePageTracking = () => {
  const location = useLocation();
  const startTimeRef = useRef(Date.now());
  const lastPathRef = useRef('');

  useEffect(() => {
    const currentPath = location.pathname;

    // Track time on previous page before navigating
    if (lastPathRef.current && lastPathRef.current !== currentPath) {
      const duration = Date.now() - startTimeRef.current;
      if (duration > 1000) { // Only track if > 1 second
        trackTimeOnPage(lastPathRef.current, duration);
      }
    }

    // Reset timer for new page
    startTimeRef.current = Date.now();
    lastPathRef.current = currentPath;

    // Extract candidate ID if on candidate detail page
    let candidateId = null;
    const candidateMatch = currentPath.match(/\/candidate\/(\d+)/);
    if (candidateMatch) {
      candidateId = parseInt(candidateMatch[1]);
    }

    // Track the page view
    trackPageView(currentPath, document.referrer, candidateId);

    // Track time on page when user leaves
    const handleBeforeUnload = () => {
      const duration = Date.now() - startTimeRef.current;
      if (duration > 1000) {
        trackTimeOnPage(currentPath, duration);
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [location.pathname]);
};

// Export tracking function for manual use (e.g., search tracking)
export const trackSearch = async (query, resultsCount, clickedResult = false) => {
  try {
    const visitorId = getVisitorId();
    const sessionData = JSON.parse(sessionStorage.getItem('_az_session') || '{}');

    await fetch(`${API_BASE_URL}analytics/track-search/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query,
        results_count: resultsCount,
        clicked_result: clickedResult,
        visitor_id: visitorId,
        session_id: sessionData.id,
        search_type: 'general',
      }),
    });
  } catch (error) {
    console.debug('Search tracking failed:', error);
  }
};

// Track candidate view with additional details
export const trackCandidateView = async (candidateId, candidateName, viewedIESpending = false) => {
  try {
    const visitorId = getVisitorId();
    const sessionData = JSON.parse(sessionStorage.getItem('_az_session') || '{}');

    await fetch(`${API_BASE_URL}analytics/track-candidate-view/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        candidate_id: candidateId,
        candidate_name: candidateName,
        visitor_id: visitorId,
        session_id: sessionData.id,
        viewed_ie_spending: viewedIESpending,
      }),
    });
  } catch (error) {
    console.debug('Candidate view tracking failed:', error);
  }
};

export default usePageTracking;
