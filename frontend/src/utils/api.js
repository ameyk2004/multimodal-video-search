let configPromise = null;
let apiBaseUrl = '';

// Fetch configuration from public/config.json
// Appending a timestamp to avoid stale cache entries as requested
export const fetchConfig = async () => {
  if (configPromise) return configPromise;

  configPromise = fetch(`/config.json?t=${new Date().getTime()}`)
    .then(res => {
      if (!res.ok) throw new Error("Failed to fetch config");
      return res.json();
    })
    .then(data => {
      if (data.API_BASE_URL) {
        apiBaseUrl = data.API_BASE_URL;
      } else {
        console.warn('API_BASE_URL not found in config.json');
      }
      return data;
    })
    .catch(err => {
      console.error('Error loading config:', err);
      configPromise = null;
      throw err;
    });

  return configPromise;
};

// Generic API caller to ensure config is loaded before making requests
export const apiClient = async (endpoint, options = {}) => {
  await fetchConfig();
  
  if (!apiBaseUrl) {
    throw new Error("API base URL is not configured. Please check config.json.");
  }
  
  const url = `${apiBaseUrl}${endpoint}`;
  const response = await fetch(url, options);
  
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || `HTTP error! status: ${response.status}`);
  }
  
  return data;
};

// Exported API methods
export const api = {
  search: (query) => apiClient(`/search?q=${encodeURIComponent(query)}`),
  getStories: () => apiClient(`/stories`),
  getVideos: () => apiClient(`/videos`),
  getVideoDetails: (videoId) => apiClient(`/videos/${videoId}`),
  getVideoTopics: (videoId) => apiClient(`/videos/${videoId}/topics`),
  getVideoQuestions: (videoId) => apiClient(`/videos/${videoId}/questions`),
  getConfig: fetchConfig
};
