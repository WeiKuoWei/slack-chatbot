import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import App from './App';
import axios from 'axios';
import { rest } from 'msw';
import { setupServer } from 'msw/node';

// Mocking axios
jest.mock('axios');

// Setting up MSW to handle API requests in tests
const server = setupServer(
  rest.get('http://${window.location.hostname}:3000/api/sandbox-assets', (req, res, ctx) => {
    return res(ctx.json([{ id: 1, display_name: 'BTC Account', currency: 'BTC', balance: '1000', available: '800', hold: '200', trading_enabled: true }]));
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

test('renders Asset Price Tracker heading', () => {
  render(<App />);
  const headingElement = screen.getByText(/Asset Price Tracker/i);
  expect(headingElement).toBeInTheDocument();
});

test('initial state is set correctly', () => {
  render(<App />);
  const sandboxButton = screen.getByText(/My Sandbox Asset/i);
  expect(sandboxButton).toBeInTheDocument();
});

test('fetches and displays sandbox assets when button is clicked', async () => {
  render(<App />);
  
  // Simulate button click to fetch sandbox assets
  fireEvent.click(screen.getByText(/My Sandbox Asset/i));

  // Expect to see loading text or some indication while fetching
  expect(screen.getByText(/Fetching sandbox assets.../i)).toBeInTheDocument();

  // Wait for the API call to resolve and the data to be displayed
  await waitFor(() => {
    const accountInfo = screen.getByText(/BTC Account/i);
    expect(accountInfo).toBeInTheDocument();
    expect(screen.getByText(/800/i)).toBeInTheDocument(); // Available balance
  });
});

test('handles API error when fetching sandbox assets', async () => {
  server.use(
    rest.get('http://${window.location.hostname}:3000/api/sandbox-assets', (req, res, ctx) => {
      return res(ctx.status(500));
    })
  );

  render(<App />);
  fireEvent.click(screen.getByText(/My Sandbox Asset/i));

  // Wait for the API error to be handled and displayed
  await waitFor(() => {
    expect(screen.getByText(/Error fetching sandbox assets/i)).toBeInTheDocument();
  });
});

