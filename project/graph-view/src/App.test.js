import { render, screen } from '@testing-library/react';
import App from './App';

test('renders the navigation with the monitor as the default tab', () => {
  render(<App />);
  expect(screen.getByText('RealStockInsight')).toBeInTheDocument();
  expect(screen.getByText('Monitor')).toHaveClass('active');
});
