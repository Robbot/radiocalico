// Radio Calico Player
// HLS Stream Player with controls

let hls;
let audioPlayer;
let isPlaying = false;
let streamUrl = '';
let startTime = null;
let elapsedInterval = null;

// DOM Elements
const playPauseBtn = document.getElementById('playPauseBtn');
const playIcon = document.getElementById('playIcon');
const volumeSlider = document.getElementById('volumeSlider');
const volumeValue = document.getElementById('volumeValue');
const statusText = document.getElementById('statusText');
const elapsedTime = document.getElementById('elapsedTime');
const artistName = document.getElementById('artistName');
const trackTitle = document.getElementById('trackTitle');
const albumName = document.getElementById('albumName');
const albumArt = document.getElementById('albumArt');
const recentlyPlayed = document.getElementById('recentlyPlayed');

// Initialize player when page loads
document.addEventListener('DOMContentLoaded', async () => {
    audioPlayer = document.getElementById('audioPlayer');

    // Set initial volume
    audioPlayer.volume = volumeSlider.value / 100;

    // Fetch stream URL from server
    await fetchStreamUrl();

    // Setup event listeners
    setupEventListeners();

    // Fetch initial track data
    await fetchNowPlaying();
    await fetchRecentlyPlayed();

    // Update track data every 30 seconds
    setInterval(fetchNowPlaying, 30000);
    setInterval(fetchRecentlyPlayed, 60000);
});

// Fetch stream URL from backend
async function fetchStreamUrl() {
    try {
        const response = await fetch('/api/stream-url');
        const data = await response.json();

        if (data.status === 'success') {
            streamUrl = data.streamUrl;
            console.log('Stream URL loaded:', streamUrl);
            updateStatus('Ready to play');
        } else {
            throw new Error('Failed to load stream URL');
        }
    } catch (error) {
        console.error('Error fetching stream URL:', error);
        updateStatus('Error loading stream');
    }
}

// Setup all event listeners
function setupEventListeners() {
    // Play/Pause button
    playPauseBtn.addEventListener('click', togglePlayPause);

    // Volume control
    volumeSlider.addEventListener('input', (e) => {
        const volume = e.target.value;
        audioPlayer.volume = volume / 100;
        volumeValue.textContent = `${volume}%`;
    });

    // Audio player events
    audioPlayer.addEventListener('playing', () => {
        isPlaying = true;
        playIcon.textContent = '⏸';
        playPauseBtn.title = 'Pause';
        updateStatus('Streaming...');
        startElapsedTimer();
    });

    audioPlayer.addEventListener('pause', () => {
        isPlaying = false;
        playIcon.textContent = '▶';
        playPauseBtn.title = 'Play';
        updateStatus('Paused');
        stopElapsedTimer();
    });

    audioPlayer.addEventListener('waiting', () => {
        updateStatus('Buffering...');
    });

    audioPlayer.addEventListener('error', (e) => {
        console.error('Audio player error:', e);
        updateStatus('Playback error');
    });
}

// Toggle play/pause
function togglePlayPause() {
    if (!streamUrl) {
        updateStatus('Stream URL not loaded');
        return;
    }

    if (isPlaying) {
        pauseStream();
    } else {
        playStream();
    }
}

// Play the stream
function playStream() {
    if (Hls.isSupported()) {
        // Use HLS.js for browsers that don't support HLS natively
        if (!hls) {
            hls = new Hls({
                enableWorker: true,
                lowLatencyMode: true,
                backBufferLength: 90
            });

            hls.loadSource(streamUrl);
            hls.attachMedia(audioPlayer);

            hls.on(Hls.Events.MANIFEST_PARSED, () => {
                console.log('HLS manifest parsed, starting playback');
                audioPlayer.play().catch(err => {
                    console.error('Error playing:', err);
                    updateStatus('Click play to start');
                });
            });

            // Listen for ALL HLS events to debug metadata
            hls.on(Hls.Events.FRAG_PARSING_METADATA, (event, data) => {
                console.log('=== HLS METADATA EVENT ===');
                console.log('Full metadata:', JSON.stringify(data, null, 2));
                if (data.samples && data.samples.length > 0) {
                    data.samples.forEach(sample => {
                        console.log('Sample:', sample);
                        processMetadata(sample);
                    });
                }
            });

            // Listen for ID3 metadata
            hls.on(Hls.Events.FRAG_PARSING_INIT_SEGMENT, (event, data) => {
                console.log('Init segment:', data);
            });

            hls.on(Hls.Events.ERROR, (event, data) => {
                console.error('HLS error:', data);
                if (data.fatal) {
                    switch(data.type) {
                        case Hls.ErrorTypes.NETWORK_ERROR:
                            updateStatus('Network error, retrying...');
                            hls.startLoad();
                            break;
                        case Hls.ErrorTypes.MEDIA_ERROR:
                            updateStatus('Media error, recovering...');
                            hls.recoverMediaError();
                            break;
                        default:
                            updateStatus('Fatal error');
                            hls.destroy();
                            hls = null;
                            break;
                    }
                }
            });
        } else {
            audioPlayer.play().catch(err => {
                console.error('Error playing:', err);
            });
        }
    } else if (audioPlayer.canPlayType('application/vnd.apple.mpegurl')) {
        // Native HLS support (Safari)
        audioPlayer.src = streamUrl;
        audioPlayer.play().catch(err => {
            console.error('Error playing:', err);
            updateStatus('Click play to start');
        });
    } else {
        updateStatus('HLS not supported in this browser');
        console.error('HLS is not supported in this browser');
    }
}

// Pause the stream
function pauseStream() {
    audioPlayer.pause();
}

// Update status text
function updateStatus(message) {
    statusText.textContent = message;
}

// Start elapsed time timer
function startElapsedTimer() {
    if (!startTime) {
        startTime = Date.now();
    }

    // Update immediately
    updateElapsedTime();

    // Update every second
    if (elapsedInterval) {
        clearInterval(elapsedInterval);
    }

    elapsedInterval = setInterval(updateElapsedTime, 1000);
}

// Stop elapsed time timer
function stopElapsedTimer() {
    if (elapsedInterval) {
        clearInterval(elapsedInterval);
        elapsedInterval = null;
    }
}

// Update elapsed time display
function updateElapsedTime() {
    if (!startTime) return;

    const elapsed = Math.floor((Date.now() - startTime) / 1000);
    const hours = Math.floor(elapsed / 3600);
    const minutes = Math.floor((elapsed % 3600) / 60);
    const seconds = elapsed % 60;

    const timeString = `${hours}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    elapsedTime.textContent = timeString;
}

// Reset elapsed time
function resetElapsedTime() {
    startTime = null;
    elapsedTime.textContent = '0:00:00';
    stopElapsedTimer();
}

// Fetch now playing track
async function fetchNowPlaying() {
    try {
        const response = await fetch('/api/now-playing');
        const data = await response.json();

        if (data.status === 'success' && data.data) {
            const track = data.data;
            artistName.textContent = track.artist;
            trackTitle.textContent = track.title;
            albumName.textContent = track.album + (track.year ? ` (${track.year})` : '');
            if (track.album_art_url) {
                albumArt.src = track.album_art_url;
            }
        }
    } catch (error) {
        console.error('Error fetching now playing:', error);
    }
}

// Fetch recently played tracks
async function fetchRecentlyPlayed() {
    try {
        const response = await fetch('/api/recently-played');
        const data = await response.json();

        if (data.status === 'success' && data.data) {
            const tracks = data.data;
            recentlyPlayed.innerHTML = '';

            if (tracks.length === 0) {
                recentlyPlayed.innerHTML = '<li>No recently played tracks</li>';
                return;
            }

            tracks.forEach(track => {
                const li = document.createElement('li');
                li.innerHTML = `
                    <span class="track-artist">${track.artist}:</span>
                    <span class="track-song">${track.title}</span>
                `;
                recentlyPlayed.appendChild(li);
            });
        }
    } catch (error) {
        console.error('Error fetching recently played:', error);
        recentlyPlayed.innerHTML = '<li>Error loading tracks</li>';
    }
}

// Process metadata from HLS stream
function processMetadata(sample) {
    try {
        console.log('=== PROCESSING SAMPLE ===');
        console.log('Sample type:', sample.type);
        console.log('Sample data:', sample.data);
        console.log('Full sample:', JSON.stringify(sample, null, 2));

        // Try to extract text from various metadata formats
        if (sample.data) {
            const metadata = sample.data;

            // Check for common ID3 tag types
            if (metadata.key === 'TXXX' || metadata.key === 'TIT2' ||
                metadata.key === 'TPE1' || metadata.key === 'TPE2') {
                console.log('ID3 tag found:', metadata.key, metadata.data || metadata.info);
                parseStreamInfo(metadata.data || metadata.info || metadata.value || '');
            }

            // Check for StreamTitle (common in ICY metadata)
            if (metadata.StreamTitle) {
                console.log('StreamTitle found:', metadata.StreamTitle);
                parseStreamInfo(metadata.StreamTitle);
            }

            // Try parsing as string
            const infoStr = metadata.info || metadata.data || metadata.value || JSON.stringify(metadata);
            if (typeof infoStr === 'string' && infoStr.includes('-')) {
                parseStreamInfo(infoStr);
            }
        }
    } catch (error) {
        console.error('Error processing metadata:', error);
    }
}

// Parse stream info and update display
function parseStreamInfo(info) {
    console.log('Parsing stream info:', info);

    // Common formats: "Artist - Title" or "Title - Artist"
    let artist = 'Unknown Artist';
    let title = 'Unknown Track';

    if (info.includes(' - ')) {
        const parts = info.split(' - ');
        artist = parts[0].trim();
        title = parts[1].trim();
    } else {
        title = info.trim();
    }

    // Update display immediately
    artistName.textContent = artist;
    trackTitle.textContent = title;

    // Send to backend to store
    updateTrackOnServer(artist, title);
}

// Send track update to server
async function updateTrackOnServer(artist, title) {
    try {
        const response = await fetch('/api/update-track', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                artist: artist,
                title: title,
                album: 'Live Stream',
                year: new Date().getFullYear()
            })
        });

        const data = await response.json();
        if (data.status === 'success') {
            console.log('Track updated on server');
            // Refresh recently played list
            fetchRecentlyPlayed();
        }
    } catch (error) {
        console.error('Error updating track on server:', error);
    }
}

// Also listen for native HTML5 audio metadata
audioPlayer.addEventListener('loadedmetadata', () => {
    console.log('Audio metadata loaded');
    if (audioPlayer.metadata) {
        console.log('Native metadata:', audioPlayer.metadata);
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    stopElapsedTimer();
    if (hls) {
        hls.destroy();
    }
});
