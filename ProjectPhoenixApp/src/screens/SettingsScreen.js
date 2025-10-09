import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  Alert,
  Switch,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

const SettingsScreen = () => {
  const [serverUrl, setServerUrl] = useState('https://localhost:5000');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState('5');
  const [keepScreenOn, setKeepScreenOn] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const savedServerUrl = await AsyncStorage.getItem('serverUrl');
      const savedAutoRefresh = await AsyncStorage.getItem('autoRefresh');
      const savedRefreshInterval = await AsyncStorage.getItem('refreshInterval');
      const savedKeepScreenOn = await AsyncStorage.getItem('keepScreenOn');

      if (savedServerUrl) setServerUrl(savedServerUrl);
      if (savedAutoRefresh !== null) setAutoRefresh(JSON.parse(savedAutoRefresh));
      if (savedRefreshInterval) setRefreshInterval(savedRefreshInterval);
      if (savedKeepScreenOn !== null) setKeepScreenOn(JSON.parse(savedKeepScreenOn));
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
  };

  const saveSettings = async () => {
    try {
      await AsyncStorage.setItem('serverUrl', serverUrl);
      await AsyncStorage.setItem('autoRefresh', JSON.stringify(autoRefresh));
      await AsyncStorage.setItem('refreshInterval', refreshInterval);
      await AsyncStorage.setItem('keepScreenOn', JSON.stringify(keepScreenOn));
      
      Alert.alert('Success', 'Settings saved successfully');
    } catch (error) {
      Alert.alert('Error', 'Failed to save settings');
    }
  };

  const resetSettings = () => {
    Alert.alert(
      'Reset Settings',
      'Are you sure you want to reset all settings to default?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Reset',
          style: 'destructive',
          onPress: () => {
            setServerUrl('http://192.168.1.100:5000');
            setAutoRefresh(true);
            setRefreshInterval('5');
            setKeepScreenOn(false);
          },
        },
      ]
    );
  };

  const testConnection = async () => {
    try {
      const response = await fetch(`${serverUrl}/vm_status`);
      if (response.ok) {
        Alert.alert('Success', 'Connection to server successful!');
      } else {
        Alert.alert('Error', 'Server responded with an error');
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to connect to server. Check the URL and make sure the server is running.');
    }
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Server Configuration</Text>
        
        <View style={styles.inputContainer}>
          <Text style={styles.label}>Server URL</Text>
          <TextInput
            style={styles.input}
            value={serverUrl}
            onChangeText={setServerUrl}
            placeholder="http://192.168.x.x:5000"
            placeholderTextColor="#9ca3af"
            autoCapitalize="none"
            autoCorrect={false}
          />
          <Text style={styles.helpText}>
            Enter your device's local network IP address. In Termux, run: ifconfig or ip addr
          </Text>
        </View>

        <TouchableOpacity style={styles.testButton} onPress={testConnection}>
          <Text style={styles.testButtonText}>Test Connection</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>App Behavior</Text>
        
        <View style={styles.switchContainer}>
          <View style={styles.switchLabelContainer}>
            <Text style={styles.label}>Auto Refresh</Text>
            <Text style={styles.helpText}>Automatically refresh VM status and logs</Text>
          </View>
          <Switch
            value={autoRefresh}
            onValueChange={setAutoRefresh}
            trackColor={{ false: '#374151', true: '#3b82f6' }}
            thumbColor={autoRefresh ? '#ffffff' : '#9ca3af'}
          />
        </View>

        <View style={styles.inputContainer}>
          <Text style={styles.label}>Refresh Interval (seconds)</Text>
          <TextInput
            style={styles.input}
            value={refreshInterval}
            onChangeText={setRefreshInterval}
            keyboardType="numeric"
            placeholder="5"
            placeholderTextColor="#9ca3af"
            editable={autoRefresh}
          />
          <Text style={styles.helpText}>
            How often to refresh data when auto refresh is enabled
          </Text>
        </View>

        <View style={styles.switchContainer}>
          <View style={styles.switchLabelContainer}>
            <Text style={styles.label}>Keep Screen On</Text>
            <Text style={styles.helpText}>Prevent screen from turning off while using the app</Text>
          </View>
          <Switch
            value={keepScreenOn}
            onValueChange={setKeepScreenOn}
            trackColor={{ false: '#374151', true: '#3b82f6' }}
            thumbColor={keepScreenOn ? '#ffffff' : '#9ca3af'}
          />
        </View>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>About</Text>
        
        <View style={styles.aboutContainer}>
          <Text style={styles.aboutTitle}>Project Phoenix Mobile</Text>
          <Text style={styles.aboutVersion}>Version 1.0.0</Text>
          <Text style={styles.aboutDescription}>
            Mobile control interface for Project Phoenix QEMU VM management system.
          </Text>
          
          <View style={styles.aboutSection}>
            <Text style={styles.aboutSectionTitle}>Features:</Text>
            <Text style={styles.aboutFeature}>• VM Control & Configuration</Text>
            <Text style={styles.aboutFeature}>• VNC Remote Desktop Access</Text>
            <Text style={styles.aboutFeature}>• Terminal Command Execution</Text>
            <Text style={styles.aboutFeature}>• Real-time Status Monitoring</Text>
          </View>
        </View>
      </View>

      <View style={styles.buttonContainer}>
        <TouchableOpacity style={styles.saveButton} onPress={saveSettings}>
          <Text style={styles.buttonText}>Save Settings</Text>
        </TouchableOpacity>
        
        <TouchableOpacity style={styles.resetButton} onPress={resetSettings}>
          <Text style={styles.buttonText}>Reset to Defaults</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#111827',
    padding: 16,
  },
  card: {
    backgroundColor: '#1f2937',
    borderRadius: 8,
    padding: 16,
    marginBottom: 16,
  },
  cardTitle: {
    color: '#ffffff',
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#374151',
    paddingBottom: 8,
  },
  inputContainer: {
    marginBottom: 16,
  },
  label: {
    color: '#d1d5db',
    fontSize: 14,
    marginBottom: 8,
    fontWeight: '500',
  },
  input: {
    backgroundColor: '#374151',
    borderWidth: 1,
    borderColor: '#4b5563',
    borderRadius: 6,
    padding: 12,
    color: '#ffffff',
    fontSize: 16,
  },
  helpText: {
    color: '#9ca3af',
    fontSize: 12,
    marginTop: 4,
    lineHeight: 16,
  },
  switchContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  switchLabelContainer: {
    flex: 1,
    marginRight: 16,
  },
  testButton: {
    backgroundColor: '#3b82f6',
    padding: 12,
    borderRadius: 6,
    alignItems: 'center',
  },
  testButtonText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: 'bold',
  },
  aboutContainer: {
    alignItems: 'center',
  },
  aboutTitle: {
    color: '#ffffff',
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  aboutVersion: {
    color: '#9ca3af',
    fontSize: 14,
    marginBottom: 12,
  },
  aboutDescription: {
    color: '#d1d5db',
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 20,
    marginBottom: 16,
  },
  aboutSection: {
    width: '100%',
  },
  aboutSectionTitle: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  aboutFeature: {
    color: '#d1d5db',
    fontSize: 14,
    marginBottom: 4,
    lineHeight: 20,
  },
  buttonContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 16,
    marginBottom: 32,
  },
  saveButton: {
    flex: 1,
    backgroundColor: '#059669',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginRight: 8,
  },
  resetButton: {
    flex: 1,
    backgroundColor: '#dc2626',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginLeft: 8,
  },
  buttonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});

export default SettingsScreen;