import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { getCurrentUser, logout, hasRole } from '../services/authService';
import '../styles/Navigation.css';

const Navigation = ({ tenderCount }) => {
  const [user, setUser] = useState(null);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [navMenuOpen, setNavMenuOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const userMenuRef = useRef(null);
  const navMenuRef = useRef(null);

  useEffect(() => {
    loadUser();
  }, []);

  useEffect(() => {
    // Close menus when clicking outside
    const handleClickOutside = (event) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target)) {
        setUserMenuOpen(false);
      }
      if (navMenuRef.current && !navMenuRef.current.contains(event.target)) {
        setNavMenuOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const loadUser = async () => {
    try {
      const userData = await getCurrentUser();
      setUser(userData);
    } catch (error) {
      console.error('Failed to load user:', error);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const toggleUserMenu = () => {
    setUserMenuOpen(!userMenuOpen);
    setNavMenuOpen(false);
  };

  const toggleNavMenu = () => {
    setNavMenuOpen(!navMenuOpen);
    setUserMenuOpen(false);
  };

  const handleNavigation = (path) => {
    navigate(path);
    setNavMenuOpen(false);
  };

  const isAdmin = user && hasRole('admin');
  const isActive = (path) => location.pathname === path;

  return (
    <header className="app-header">
      <div className="container">
        <div className="header-content">
          <div className="header-left">
            {/* Navigation Menu - 3 lines next to brand */}
            <div className="nav-menu-wrapper" ref={navMenuRef}>
              <button className="nav-menu-trigger hamburger" onClick={toggleNavMenu}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="3" y1="6" x2="21" y2="6"></line>
                  <line x1="3" y1="12" x2="21" y2="12"></line>
                  <line x1="3" y1="18" x2="21" y2="18"></line>
                </svg>
              </button>

              {navMenuOpen && (
                <div className="nav-menu-dropdown">
                  <button
                    className={`nav-menu-item ${isActive('/') ? 'active' : ''}`}
                    onClick={() => handleNavigation('/')}
                  >
                    <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                      <path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z" />
                    </svg>
                    <span>Home</span>
                  </button>

                  {isAdmin && (
                    <button
                      className={`nav-menu-item ${isActive('/users') ? 'active' : ''}`}
                      onClick={() => handleNavigation('/users')}
                    >
                      <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                        <path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z" />
                      </svg>
                      <span>User Management</span>
                    </button>
                  )}

                  <div className="menu-divider"></div>

                  <button
                    className="nav-menu-item nav-menu-item-danger"
                    onClick={() => {
                      setNavMenuOpen(false);
                      handleLogout();
                    }}
                  >
                    <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M3 3a1 1 0 00-1 1v12a1 1 0 001 1h12a1 1 0 001-1V4a1 1 0 00-1-1H3zm11 4.414l-4.293 4.293a1 1 0 01-1.414 0L4 7.414 5.414 6l3.293 3.293L13.586 6 15 7.414l-1-1z" clipRule="evenodd" />
                      <path d="M3 3h12v12H3V3zm7.707 4.707L8 10.414 5.293 7.707 4 9l4 4 6-6-1.293-1.293z" />
                      <path fillRule="evenodd" d="M3 4a1 1 0 011-1h8a1 1 0 011 1v1H3V4zm10 8V6h2v6h-2zm-2 4H4a1 1 0 01-1-1v-1h10v1a1 1 0 01-1 1z" clipRule="evenodd" />
                    </svg>
                    <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M3 3a1 1 0 011 1v12a1 1 0 11-2 0V4a1 1 0 011-1zm7.707 3.293a1 1 0 010 1.414L9.414 9H17a1 1 0 110 2H9.414l1.293 1.293a1 1 0 01-1.414 1.414l-3-3a1 1 0 010-1.414l3-3a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                    <span>Logout</span>
                  </button>
                </div>
              )}
            </div>

            <div className="brand-wrap">
              <div className="brand-mark">
                <svg width="40" height="40" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
                  <defs>
                    <radialGradient id="mainGrad" cx="35%" cy="35%">
                      <stop offset="0%" style={{stopColor:'#b07dd8', stopOpacity:1}} />
                      <stop offset="100%" style={{stopColor:'#6b1b9a', stopOpacity:1}} />
                    </radialGradient>
                    <radialGradient id="smallGrad1" cx="30%" cy="30%">
                      <stop offset="0%" style={{stopColor:'#8b5fbf', stopOpacity:1}} />
                      <stop offset="100%" style={{stopColor:'#2c1451', stopOpacity:1}} />
                    </radialGradient>
                    <radialGradient id="smallGrad2" cx="35%" cy="35%">
                      <stop offset="0%" style={{stopColor:'#764ba2', stopOpacity:1}} />
                      <stop offset="100%" style={{stopColor:'#4a1572', stopOpacity:1}} />
                    </radialGradient>
                    <radialGradient id="smallGrad3" cx="30%" cy="30%">
                      <stop offset="0%" style={{stopColor:'#a67fcb', stopOpacity:1}} />
                      <stop offset="100%" style={{stopColor:'#5c2d91', stopOpacity:1}} />
                    </radialGradient>
                  </defs>
                  
                  <ellipse cx="35" cy="85" rx="28" ry="5" fill="rgba(0,0,0,0.2)" />
                  
                  <circle cx="35" cy="60" r="28" fill="url(#mainGrad)" />
                  <ellipse cx="27" cy="50" rx="10" ry="8" fill="rgba(255,255,255,0.3)" />
                  
                  <circle cx="60" cy="18" r="11" fill="url(#smallGrad1)" />
                  <ellipse cx="56" cy="14" rx="4" ry="3" fill="rgba(255,255,255,0.4)" />
                  
                  <circle cx="75" cy="40" r="8" fill="url(#smallGrad2)" />
                  <ellipse cx="72" cy="37" rx="3" ry="2" fill="rgba(255,255,255,0.4)" />
                  
                  <circle cx="68" cy="65" r="9" fill="url(#smallGrad3)" />
                  <ellipse cx="65" cy="62" rx="3.5" ry="2.5" fill="rgba(255,255,255,0.4)" />
                </svg>
              </div>
              <div className="brand-text">
                <h1 className="app-title">Tender Extraction Portal</h1>
                <p className="brand-slogan">Technology Infrastructure Architects</p>
              </div>
            </div>
          </div>

          <div className="header-right">
            {/* Tender Count */}
            <div className="header-count">
              {tenderCount} tender{tenderCount === 1 ? '' : 's'}
            </div>

            {/* User Menu */}
            <div className="user-menu" ref={userMenuRef}>
              <button className="user-menu-trigger" onClick={toggleUserMenu}>
                <div className="user-avatar">
                  {user?.name?.charAt(0).toUpperCase() || user?.email?.charAt(0).toUpperCase() || 'U'}
                </div>
                <span className="user-name">{user?.name || user?.email || 'User'}</span>
                <svg
                  className={`chevron ${userMenuOpen ? 'open' : ''}`}
                  width="16"
                  height="16"
                  viewBox="0 0 16 16"
                  fill="currentColor"
                >
                  <path d="M4.5 6l3.5 3.5L11.5 6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill="none" />
                </svg>
              </button>

              {userMenuOpen && (
                <div className="user-menu-dropdown">
                  <div className="menu-header">
                    <div className="menu-user-info">
                      <div className="menu-user-name">{user?.name || 'User'}</div>
                      <div className="menu-user-email">{user?.email}</div>
                      {isAdmin && <span className="menu-user-badge">Admin</span>}
                    </div>
                  </div>
                  <div className="menu-divider"></div>
                  <button className="menu-item" onClick={() => { setUserMenuOpen(false); navigate('/profile'); }}>
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                      <path d="M8 8a3 3 0 100-6 3 3 0 000 6zM12.5 14a1.5 1.5 0 01-1.5-1.5c0-1.657-1.343-3-3-3s-3 1.343-3 3A1.5 1.5 0 013.5 14h9z"/>
                    </svg>
                    Profile
                  </button>
                  <div className="menu-divider"></div>
                  <button className="menu-item menu-item-danger" onClick={handleLogout}>
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                      <path d="M6 14H3a1 1 0 01-1-1V3a1 1 0 011-1h3M11 11l3-3-3-3M14 8H6"/>
                    </svg>
                    Logout
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Navigation;
