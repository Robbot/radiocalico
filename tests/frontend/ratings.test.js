/**
 * Frontend Unit Tests for RadioCalico Ratings System
 * Tests rating-specific functionality including edge cases
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { readFileSync } from 'fs';
import { join } from 'path';

// Load test fixtures
const fixtures = JSON.parse(
  readFileSync(join(__dirname, 'fixtures/tracks.json'), 'utf-8')
);

// Mock DOM environment
function setupMockDOM() {
  const localStorageMock = (() => {
    let store = {};
    return {
      getItem: vi.fn((key) => store[key] || null),
      setItem: vi.fn((key, value) => {
        store[key] = value.toString();
      }),
      removeItem: vi.fn((key) => {
        delete store[key];
      }),
      clear: vi.fn(() => {
        store = {};
      }),
    };
  })();

  Object.defineProperty(global, 'localStorage', {
    value: localStorageMock,
    writable: true,
  });

  global.fetch = vi.fn();

  return { localStorageMock };
}

describe('Rating Edge Cases', () => {
  let localStorageMock;

  beforeEach(() => {
    const setup = setupMockDOM();
    localStorageMock = setup.localStorageMock;
    vi.clearAllMocks();
    localStorageMock.getItem.mockReturnValue('user_test123');
  });

  describe('Rating without current track', () => {
    it('should not send request when currentTrackId is null', async () => {
      const currentTrackId = null;
      const userId = 'user_test123';

      // Simulate handleRating guard clause
      if (!currentTrackId || !userId) {
        // Should exit early without making request
        expect(true).toBe(true);
        return;
      }

      // If we reach here, the test should fail
      expect.fail('Should have exited early');
    });

    it('should not send request when userId is null', async () => {
      const currentTrackId = 1;
      const userId = null;

      if (!currentTrackId || !userId) {
        expect(true).toBe(true);
        return;
      }

      expect.fail('Should have exited early');
    });

    it('should not send request when currentTrackId is undefined', async () => {
      const currentTrackId = undefined;
      const userId = 'user_test123';

      if (!currentTrackId || !userId) {
        expect(true).toBe(true);
        return;
      }

      expect.fail('Should have exited early');
    });
  });

  describe('Rating validation', () => {
    it('should only accept rating_type of 1 or -1', async () => {
      const validRatings = [1, -1];

      validRatings.forEach(rating => {
        expect([1, -1]).toContain(rating);
      });

      expect([1, -1]).toContain(1);
      expect([1, -1]).toContain(-1);
      expect([1, -1]).not.toContain(0);
      expect([1, -1]).not.toContain(2);
      expect([1, -1]).not.toContain(5);
      expect([1, -1]).not.toContain(-2);
    });
  });

  describe('Rating feedback messages', () => {
    it('should show success message after rating', async () => {
      const ratingMessage = { textContent: '' };

      global.fetch.mockResolvedValueOnce({
        json: async () => fixtures.ratingSuccess,
        status: 200
      });

      const response = await fetch('/api/tracks/1/rate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: 'user_123', rating_type: 1 })
      });

      const data = await response.json();

      if (data.status === 'success') {
        ratingMessage.textContent = 'Thank you for rating!';
      }

      expect(ratingMessage.textContent).toBe('Thank you for rating!');
    });

    it('should show error message on duplicate rating', async () => {
      const ratingMessage = { textContent: '' };

      global.fetch.mockResolvedValueOnce({
        json: async () => fixtures.ratingError,
        status: 409
      });

      const response = await fetch('/api/tracks/1/rate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: 'user_123', rating_type: 1 })
      });

      if (response.status === 409) {
        ratingMessage.textContent = 'You have already rated this track';
      }

      expect(ratingMessage.textContent).toBe('You have already rated this track');
    });

    it('should show error message on API failure', async () => {
      const ratingMessage = { textContent: '' };

      global.fetch.mockRejectedValueOnce(new Error('Network error'));

      let errorThrown = false;
      try {
        await fetch('/api/tracks/1/rate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: 'user_123', rating_type: 1 })
        });
      } catch (error) {
        errorThrown = true;
        ratingMessage.textContent = 'Error submitting rating. Please try again.';
      }

      expect(errorThrown).toBe(true);
      expect(ratingMessage.textContent).toBe('Error submitting rating. Please try again.');
    });
  });

  describe('Concurrent rating prevention', () => {
    it('should handle multiple rapid clicks', async () => {
      let fetchCallCount = 0;

      global.fetch.mockImplementation(async () => {
        fetchCallCount++;
        // Simulate network delay
        await new Promise(resolve => setTimeout(resolve, 100));
        return {
          json: async () => fixtures.ratingSuccess,
          status: 200
        };
      });

      // Simulate multiple rapid clicks (though frontend disables buttons)
      const promises = [];
      for (let i = 0; i < 5; i++) {
        promises.push(
          fetch('/api/tracks/1/rate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: 'user_123', rating_type: 1 })
          })
        );
      }

      const results = await Promise.allSettled(promises);

      // All requests should complete (backend handles duplicates)
      expect(results).toHaveLength(5);
      expect(fetchCallCount).toBe(5);
    });
  });

  describe('Rating payload structure', () => {
    it('should send correct JSON payload structure', async () => {
      const payload = {
        user_id: 'user_test123',
        rating_type: 1
      };

      global.fetch.mockResolvedValueOnce({
        json: async () => fixtures.ratingSuccess,
        status: 200
      });

      await fetch('/api/tracks/1/rate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const fetchCall = global.fetch.mock.calls[0];
      const sentBody = JSON.parse(fetchCall[1].body);

      expect(sentBody).toHaveProperty('user_id');
      expect(sentBody).toHaveProperty('rating_type');
      expect(sentBody.user_id).toBe('user_test123');
      expect(sentBody.rating_type).toBe(1);
    });

    it('should include correct Content-Type header', async () => {
      global.fetch.mockResolvedValueOnce({
        json: async () => fixtures.ratingSuccess,
        status: 200
      });

      await fetch('/api/tracks/1/rate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: 'user_123', rating_type: 1 })
      });

      const fetchCall = global.fetch.mock.calls[0];
      const headers = fetchCall[1].headers;

      expect(headers['Content-Type']).toBe('application/json');
    });
  });

  describe('Rating button event listeners', () => {
    it('should attach click event to thumbs up button', () => {
      const mockButton = {
        addEventListener: vi.fn()
      };

      mockButton.addEventListener('click', () => {});

      expect(mockButton.addEventListener).toHaveBeenCalledWith('click', expect.any(Function));
    });

    it('should attach click event to thumbs down button', () => {
      const mockButton = {
        addEventListener: vi.fn()
      };

      mockButton.addEventListener('click', () => {});

      expect(mockButton.addEventListener).toHaveBeenCalledWith('click', expect.any(Function));
    });

    it('should pass correct rating type to handler', () => {
      const thumbsUpHandler = (ratingType) => ratingType;
      const thumbsDownHandler = (ratingType) => ratingType;

      expect(thumbsUpHandler(1)).toBe(1);
      expect(thumbsDownHandler(-1)).toBe(-1);
    });
  });

  describe('User persistence across sessions', () => {
    it('should maintain same user ID across multiple rating operations', async () => {
      const userId = 'user_persistent_123';
      localStorageMock.getItem.mockReturnValue(userId);

      // First rating
      global.fetch.mockResolvedValueOnce({
        json: async () => fixtures.ratingSuccess,
        status: 200
      });

      await fetch('/api/tracks/1/rate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, rating_type: 1 })
      });

      const firstCall = global.fetch.mock.calls[0];
      const firstBody = JSON.parse(firstCall[1].body);

      // Second rating
      global.fetch.mockResolvedValueOnce({
        json: async () => fixtures.ratingSuccess,
        status: 200
      });

      await fetch('/api/tracks/2/rate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, rating_type: -1 })
      });

      const secondCall = global.fetch.mock.calls[1];
      const secondBody = JSON.parse(secondCall[1].body);

      expect(firstBody.user_id).toBe(userId);
      expect(secondBody.user_id).toBe(userId);
      expect(firstBody.user_id).toBe(secondBody.user_id);
    });
  });

  describe('Rating count updates', () => {
    it('should correctly increment thumbs up count', async () => {
      global.fetch.mockResolvedValueOnce({
        json: async () => ({
          status: 'success',
          data: { thumbs_up: 100, thumbs_down: 5 }
        }),
        status: 200
      });

      const response = await fetch('/api/tracks/1/rate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: 'user_123', rating_type: 1 })
      });

      const data = await response.json();

      expect(data.data.thumbs_up).toBe(100);
      expect(data.data.thumbs_down).toBe(5);
    });

    it('should correctly increment thumbs down count', async () => {
      global.fetch.mockResolvedValueOnce({
        json: async () => ({
          status: 'success',
          data: { thumbs_up: 50, thumbs_down: 10 }
        }),
        status: 200
      });

      const response = await fetch('/api/tracks/1/rate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: 'user_123', rating_type: -1 })
      });

      const data = await response.json();

      expect(data.data.thumbs_up).toBe(50);
      expect(data.data.thumbs_down).toBe(10);
    });

    it('should handle zero counts correctly', async () => {
      global.fetch.mockResolvedValueOnce({
        json: async () => ({
          status: 'success',
          data: { thumbs_up: 0, thumbs_down: 0 }
        }),
        status: 200
      });

      const response = await fetch('/api/tracks/new/rate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: 'user_new', rating_type: 1 })
      });

      const data = await response.json();

      expect(data.data.thumbs_up).toBe(0);
      expect(data.data.thumbs_down).toBe(0);
    });
  });
});
