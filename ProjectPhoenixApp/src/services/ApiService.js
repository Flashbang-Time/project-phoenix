import AsyncStorage from '@react-native-async-storage/async-storage';

class ApiService {
  constructor() {
    this.baseUrl = 'http://127.0.0.1:5000';
    this.loadServerUrl();
  }

  async loadServerUrl() {
    try {
      const savedUrl = await AsyncStorage.getItem('serverUrl');
      if (savedUrl) {
        this.baseUrl = savedUrl;
      }
    } catch (error) {
      console.error('Failed to load server URL:', error);
    }
  }

  async updateServerUrl(url) {
    this.baseUrl = url;
    try {
      await AsyncStorage.setItem('serverUrl', url);
    } catch (error) {
      console.error('Failed to save server URL:', error);
    }
  }

  async makeRequest(endpoint, options = {}) {
    try {
      // Ensure we have the latest server URL
      await this.loadServerUrl();
      
      const url = `${this.baseUrl}${endpoint}`;
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API request failed for ${endpoint}:`, error);
      throw error;
    }
  }

  async getVmStatus() {
    return this.makeRequest('/vm_status');
  }

  async startVM(config) {
    return this.makeRequest('/start_vm', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async stopVM() {
    return this.makeRequest('/stop_vm', {
      method: 'POST',
    });
  }

  async getDefaults() {
    return this.makeRequest('/get_defaults');
  }

  async getQemuLogs() {
    return this.makeRequest('/qemu_logs');
  }

  async runTerminalCommand(command) {
    return this.makeRequest('/run_terminal_command', {
      method: 'POST',
      body: JSON.stringify({ command }),
    });
  }

  async getTerminalOutput() {
    return this.makeRequest('/get_terminal_output');
  }
}

export default new ApiService();