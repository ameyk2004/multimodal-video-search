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
  search: (query, type = 'combined') => apiClient(`/search?q=${encodeURIComponent(query)}&type=${type}`),
  getStories: () => apiClient(`/stories`),
  getVideos: () => apiClient(`/videos`),
  getVideoDetails: (videoId) => apiClient(`/videos/${videoId}`),
  getBooks: () => apiClient(`/books`),
  getBookDetails: (bookId) => apiClient(`/books/${bookId}`),
  getMusic: () => apiClient(`/music`),
  getNextChunk: (bookName, chunkIndex) => apiClient(`/search?action=next_chunk&book_name=${encodeURIComponent(bookName)}&chunk_index=${chunkIndex}`),
  fetchBookPage: (bookName, pageNumber) => apiClient(`/search?action=fetch_page&book_name=${encodeURIComponent(bookName)}&page_number=${pageNumber}`),
  getConfig: fetchConfig,
  getAdminVideos: () => apiClient('/admin/videos'),
  getAdminVideoDetails: (videoId) => apiClient(`/admin/videos/${videoId}`),
  updateAdminVideo: (videoId, data) => apiClient(`/admin/videos/${videoId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  })
};
