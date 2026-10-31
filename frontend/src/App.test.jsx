import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { AppRoutes } from './App';
import { SIDEBAR_NAV_ITEMS } from './layouts/DashboardLayout';
import { extractErrorMessage } from './services/api';
import { AlertBanner } from './components/LoadingSkeleton';

describe('NagarNexus Frontend Test Suite', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('1. Protected pages redirect unauthenticated users to AuthPage', () => {
    render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/']}>
          <AppRoutes />
        </MemoryRouter>
      </AuthProvider>
    );
    expect(screen.getByText(/Turning Urban Data Into Intelligent Decisions/i)).toBeInTheDocument();
    expect(screen.getByText(/Sign In to NagarNexus/i)).toBeInTheDocument();
  });

  it('2. AuthPage forms switch between Sign In, Create Account, and Reset Password', () => {
    render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/auth']}>
          <AppRoutes />
        </MemoryRouter>
      </AuthProvider>
    );
    const registerTab = screen.getByRole('button', { name: /Create Account/i });
    fireEvent.click(registerTab);
    expect(screen.getByPlaceholderText(/Dr. Aarav Ramanathan/i)).toBeInTheDocument();

    const resetTab = screen.getByRole('button', { name: /Reset Password/i });
    fireEvent.click(resetTab);
    expect(screen.getByPlaceholderText(/Enter new password/i)).toBeInTheDocument();
  });

  it('3. Sidebar navigation configuration includes all 14 required modules', () => {
    expect(SIDEBAR_NAV_ITEMS.length).toBe(14);
    const labels = SIDEBAR_NAV_ITEMS.map((item) => item.label);
    expect(labels).toContain('Overview Dashboard');
    expect(labels).toContain('Location Intelligence');
    expect(labels).toContain('Dataset Explorer');
    expect(labels).toContain('Data Cleaning');
    expect(labels).toContain('Exploratory Data Analysis');
    expect(labels).toContain('Statistical Analysis');
    expect(labels).toContain('Machine Learning Lab');
    expect(labels).toContain('Predictive Analytics');
    expect(labels).toContain('Risk Detection');
    expect(labels).toContain('Location Comparison');
    expect(labels).toContain('AI Insights');
    expect(labels).toContain('Report Center');
    expect(labels).toContain('User Profile');
    expect(labels).toContain('Settings');
  });

  it('4. API error handling extracts FastAPI detail and renders AlertBanner', () => {
    const mockError = {
      response: {
        data: {
          detail: 'Unsupported file extension .exe. Allowed types: CSV, XLSX, XLS.',
        },
      },
    };
    const msg = extractErrorMessage(mockError);
    expect(msg).toContain('Unsupported file extension');

    render(<AlertBanner type="error" message={msg} />);
    expect(screen.getByText(/Unsupported file extension/i)).toBeInTheDocument();
  });
});

