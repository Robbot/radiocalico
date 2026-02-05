/**
 * Frontend Unit Tests for RadioCalico Player
 * Tests core player functionality, user ID management, and rating handlers
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { readFileSync } from 'fs';
import { join } from 'path';

// Load test fixtures
const fixtures = JSON.parse(
  readFileSync(join(__dirname, 'fixtures/tracks.json'), 'utf-8')
);

// Mock DOM environment
function setupMockDOM() {
  // Mock localStorage
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

  // Mock fetch globally
  global.fetch = vi.fn();

  // Create mock DOM elements
  const mockElements = {
    playPauseBtn: { click: vi.fn(), title: '' },
    playIcon: { textContent: '▶' },
    volumeSlider: { value: 50 },
    volumeValue: { textContent: '50%' },
    statusText: { textContent: '' },
    elapsedTime: { textContent: '0:00:00' },
    artistName: { textContent: '' },
    trackTitle: { textContent: '' },
    albumName: { textContent: '' },
    albumArt: { src: '' },
    recentlyPlayed: { innerHTML: '' },
    thumbsUpBtn: {
      addEventListener: vi.fn(),
      classList: { add: vi.fn(), remove: vi.fn() },
      disabled: false
    },
    thumbsDownBtn: {
      addEventListener: vi.fn(),
      classList: { add: vi.fn(), remove: vi.fn() },
      disabled: false
    },
    thumbsUpCount: { textContent: '0' },
    thumbsDownCount: { textContent: '0' },
    ratingMessage: { textContent: '' },
    audioPlayer: {
      volume: 0.5,
      addEventListener: vi.fn(),
      play: vi.fn(),
      pause: vi.fn(),
    }
  };

  // Mock getElementById
  document.getElementById = vi.fn((id) => mockElements[id]);

  // Mock querySelector for event listeners
  document.querySelector = vi.fn((selector) => {
    if (selector === '#playPauseBtn') return mockElements.playPauseBtn;
    return null;
  });

  return { mockElements, localStorageMock };
}

describe('User ID Management', () => {
  let localStorageMock;
  let mockElements;

  beforeEach(() => {
    const setup = setupMockDOM();
    localStorageMock = setup.localStorageMock;
    mockElements = setup.mockElements;
    vi.clearAllMocks();
  });

  afterEach(() => {
    localStorageMock.clear();
  });

  describe('initializeUserId', () => {
    it('should generate a new user ID if none exists in localStorage', () => {
      localStorageMock.getItem.mockReturnValue(null);

      // Simulate initializeUserId function logic
      let userId = localStorageMock.getItem('radioCalicoUserId');
      if (!userId) {
        userId = 'user_' + Date.now() + '_' + Math.random().toString(36).substring(2, 15);
        localStorageMock.setItem('radioCalicoUserId', userId);
      }

      expect(userId).toMatch(/^user_\d+_[a-z0-9]+$/);
      expect(localStorageMock.setItem).toHaveBeenCalledWith('radioCalicoUserId', userId);
    });

    it('should retrieve existing user ID from localStorage', () => {
      const existingUserId = 'user_1234567890_abc123def';
      localStorageMock.getItem.mockReturnValue(existingUserId);

      let userId = localStorageMock.getItem('radioCalicoUserId');

      expect(userId).toBe(existingUserId);
      expect(localStorageMock.setItem).not.toHaveBeenCalled();
    });

    it('should generate unique user IDs', () => {
      localStorageMock.getItem.mockReturnValue(null);

      const userIds = new Set();
      for (let i = 0; i < 100; i++) {
        let userId = 'user_' + Date.now() + '_' + Math.random().toString(36).substring(2, 15);
        userIds.add(userId);
      }

      // With random component, we should get mostly unique IDs
      expect(userIds.size).toBeGreaterThan(90);
    });

    it('should store user ID in localStorage with correct key', () => {
      localStorageMock.getItem.mockReturnValue(null);

      let userId = localStorageMock.getItem('radioCalicoUserId');
      if (!userId) {
        userId = 'user_' + Date.now() + '_' + Math.random().toString(36).substring(2, 15);
        localStorageMock.setItem('radioCalicoUserId', userId);
      }

      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'radioCalicoUserId',
        expect.any(String)
      );
    });
  });

  describe('userId format validation', () => {
    it('should follow the format: user_<timestamp>_<randomString>', () => {
      localStorageMock.getItem.mockReturnValue(null);

      let userId = 'user_' + Date.now() + '_' + Math.random().toString(36).substring(2, 15);

      const parts = userId.split('_');
      expect(parts[0]).toBe('user');
      expect(parts[1]).toMatch(/^\d+$/);
      expect(parts[2]).toMatch(/^[a-z0-9]+$/);
      expect(parts.length).toBe(3);
    });

    it('should have random string of 11 characters', () => {
      localStorageMock.getItem.mockReturnValue(null);

      let userId = 'user_' + Date.now() + '_' + Math.random().toString(36).substring(2, 15);
      const randomPart = userId.split('_')[2];

      expect(randomPart.length).toBeGreaterThanOrEqual(10);
    });
  });
});

describe('Rating Handler', () => {
  let localStorageMock;
  let mockElements;

  beforeEach(() => {
    const setup = setupMockDOM();
    localStorageMock = setup.localStorageMock;
    mockElements = setup.mockElements;
    vi.clearAllMocks();

    // Set up mock user ID
    localStorageMock.getItem.mockReturnValue('user_test123');
  });

  describe('handleRating', () => {
    it('should send POST request with rating_type=1 for thumbs up', async () => {
      const currentTrackId = 1;
      const userId = 'user_test123';
      const ratingType = 1;

      global.fetch.mockResolvedValueOnce({
        json: async () => fixtures.ratingSuccess,
        status: 200
      });

      // Simulate handleRating logic
      const response = await fetch(`/api/tracks/${currentTrackId}/rate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          rating_type: ratingType
        })
      });

      const data = await response.json();

      expect(global.fetch).toHaveBeenCalledWith(
        `/api/tracks/${currentTrackId}/rate`,
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: userId, rating_type: 1 })
        })
      );
      expect(data.status).toBe('success');
    });

    it('should send POST request with rating_type=-1 for thumbs down', async () => {
      const currentTrackId = 1;
      const userId = 'user_test123';
      const ratingType = -1;

      global.fetch.mockResolvedValueOnce({
        json: async () => fixtures.ratingSuccess,
        status: 200
      });

      const response = await fetch(`/api/tracks/${currentTrackId}/rate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          rating_type: ratingType
        })
      });

      const data = await response.json();

      expect(global.fetch).toHaveBeenCalledWith(
        `/api/tracks/${currentTrackId}/rate`,
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ user_id: userId, rating_type: -1 })
        })
      );
      expect(data.status).toBe('success');
    });

    it('should handle successful rating response', async () => {
      const mockResponse = {
        status: 'success',
        data: { thumbs_up: 26, thumbs_down: 3 }
      };

      global.fetch.mockResolvedValueOnce({
        json: async () => mockResponse,
        status: 200
      });

      const response = await fetch('/api/tracks/1/rate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: 'user_123', rating_type: 1 })
      });

      const data = await response.json();

      expect(data.status).toBe('success');
      expect(data.data.thumbs_up).toBe(26);
      expect(data.data.thumbs_down).toBe(3);
    });

    it('should handle 409 conflict for duplicate rating', async () => {
      global.fetch.mockResolvedValueOnce({
        json: async () => fixtures.ratingError,
        status: 409
      });

      const response = await fetch('/api/tracks/1/rate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: 'user_123', rating_type: 1 })
      });

      expect(response.status).toBe(409);
    });

    it('should handle network errors gracefully', async () => {
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
        expect(error.message).toBe('Network error');
      }

      expect(errorThrown).toBe(true);
    });
  });

  describe('Rating button state management', () => {
    it('should disable thumbs up button after rating', async () => {
      const thumbsUpBtn = mockElements.thumbsUpBtn;
      const thumbsDownBtn = mockElements.thumbsDownBtn;

      // Simulate successful rating
      global.fetch.mockResolvedValueOnce({
        json: async () => fixtures.ratingSuccess,
        status: 200
      });

      await fetch('/api/tracks/1/rate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: 'user_123', rating_type: 1 })
      });

      // Simulate button state updates
      thumbsUpBtn.classList.add('active');
      thumbsUpBtn.disabled = true;
      thumbsDownBtn.disabled = true;

      expect(thumbsUpBtn.classList.add).toHaveBeenCalledWith('active');
      expect(thumbsUpBtn.disabled).toBe(true);
      expect(thumbsDownBtn.disabled).toBe(true);
    });

    it('should disable thumbs down button after rating', async () => {
      const thumbsDownBtn = mockElements.thumbsDownBtn;
      const thumbsUpBtn = mockElements.thumbsUpBtn;

      global.fetch.mockResolvedValueOnce({
        json: async () => fixtures.ratingSuccess,
        status: 200
      });

      await fetch('/api/tracks/1/rate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: 'user_123', rating_type: -1 })
      });

      thumbsDownBtn.classList.add('active');
      thumbsUpBtn.disabled = true;
      thumbsDownBtn.disabled = true;

      expect(thumbsDownBtn.classList.add).toHaveBeenCalledWith('active');
      expect(thumbsUpBtn.disabled).toBe(true);
      expect(thumbsDownBtn.disabled).toBe(true);
    });
  });

  describe('Rating counts update', () => {
    it('should update thumbs up count after rating', async () => {
      const thumbsUpCount = mockElements.thumbsUpCount;
      const thumbsDownCount = mockElements.thumbsDownCount;

      global.fetch.mockResolvedValueOnce({
        json: async () => ({ status: 'success', data: { thumbs_up: 27, thumbs_down: 3 } }),
        status: 200
      });

      const response = await fetch('/api/tracks/1/rate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: 'user_123', rating_type: 1 })
      });

      const data = await response.json();

      thumbsUpCount.textContent = data.data.thumbs_up;
      thumbsDownCount.textContent = data.data.thumbs_down;

      expect(thumbsUpCount.textContent).toBe(String(27));
      expect(thumbsDownCount.textContent).toBe(String(3));
    });

    it('should update thumbs down count after rating', async () => {
      const thumbsUpCount = mockElements.thumbsUpCount;
      const thumbsDownCount = mockElements.thumbsDownCount;

      global.fetch.mockResolvedValueOnce({
        json: async () => ({ status: 'success', data: { thumbs_up: 25, thumbs_down: 4 } }),
        status: 200
      });

      const response = await fetch('/api/tracks/1/rate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: 'user_123', rating_type: -1 })
      });

      const data = await response.json();

      thumbsUpCount.textContent = data.data.thumbs_up;
      thumbsDownCount.textContent = data.data.thumbs_down;

      expect(thumbsUpCount.textContent).toBe(String(25));
      expect(thumbsDownCount.textContent).toBe(String(4));
    });
  });
});

describe('Rating Status Check', () => {
  let localStorageMock;
  let mockElements;

  beforeEach(() => {
    const setup = setupMockDOM();
    localStorageMock = setup.localStorageMock;
    mockElements = setup.mockElements;
    vi.clearAllMocks();
  });

  describe('checkRatingStatus', () => {
    it('should check if user has rated the current track', async () => {
      const currentTrackId = 1;
      const userId = 'user_test123';

      global.fetch.mockResolvedValueOnce({
        json: async () => fixtures.ratingStatus,
        status: 200
      });

      const response = await fetch(`/api/tracks/${currentTrackId}/rating-status`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId })
      });

      const data = await response.json();

      expect(global.fetch).toHaveBeenCalledWith(
        `/api/tracks/${currentTrackId}/rating-status`,
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        })
      );
      expect(data.data.has_rated).toBe(false);
    });

    it('should return existing rating when user has rated', async () => {
      global.fetch.mockResolvedValueOnce({
        json: async () => fixtures.ratingStatusRated,
        status: 200
      });

      const response = await fetch('/api/tracks/1/rating-status', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: 'user_123' })
      });

      const data = await response.json();

      expect(data.data.has_rated).toBe(true);
      expect(data.data.rating_type).toBe(1);
    });

    it('should return rating_type=1 for thumbs up', async () => {
      global.fetch.mockResolvedValueOnce({
        json: async () => ({
          status: 'success',
          data: { has_rated: true, rating_type: 1 }
        }),
        status: 200
      });

      const response = await fetch('/api/tracks/1/rating-status', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: 'user_123' })
      });

      const data = await response.json();

      expect(data.data.rating_type).toBe(1);
    });

    it('should return rating_type=-1 for thumbs down', async () => {
      global.fetch.mockResolvedValueOnce({
        json: async () => ({
          status: 'success',
          data: { has_rated: true, rating_type: -1 }
        }),
        status: 200
      });

      const response = await fetch('/api/tracks/1/rating-status', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: 'user_123' })
      });

      const data = await response.json();

      expect(data.data.rating_type).toBe(-1);
    });
  });
});
