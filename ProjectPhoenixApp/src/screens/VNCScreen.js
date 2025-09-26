import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Alert,
  TouchableOpacity,
  Dimensions,
} from 'react-native';
import { WebView } from 'react-native-webview';
import ApiService from '../services/ApiService';

const VNCScreen = () => {
  const [vmStatus, setVmStatus] = useState('Checking...');
  const [showVNC, setShowVNC] = useState(false);
  const { width, height } = Dimensions.get('window');

  useEffect(() => {
    updateVmStatus();
    const interval = setInterval(updateVmStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const updateVmStatus = async () => {
    try {
      const status = await ApiService.getVmStatus();
      setVmStatus(status.running ? 'Running' : 'Stopped');
    } catch (error) {
      setVmStatus('Error (Server Down?)');
    }
  };

  const connectToVNC = () => {
    if (vmStatus !== 'Running') {
      Alert.alert('VM Not Running', 'Please start the VM first before connecting to VNC.');
      return;
    }
    setShowVNC(true);
  };

  const disconnectVNC = () => {
    setShowVNC(false);
  };

  if (showVNC) {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.headerText}>VNC Connection</Text>
          <TouchableOpacity style={styles.disconnectButton} onPress={disconnectVNC}>
            <Text style={styles.buttonText}>Disconnect</Text>
          </TouchableOpacity>
        </View>
        <WebView
          source={{ uri: 'http://127.0.0.1:5000/noVNC/' }}
          style={styles.webview}
          javaScriptEnabled={true}
          domStorageEnabled={true}
          startInLoadingState={true}
          scalesPageToFit={true}
          onError={(syntheticEvent) => {
            const { nativeEvent } = syntheticEvent;
            Alert.alert('Connection Error', 'Failed to connect to VNC server. Make sure the VM is running and VNC is accessible.');
          }}
        />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.statusCard}>
        <Text style={styles.statusLabel}>VM Status:</Text>
        <Text style={[
          styles.statusText,
          { color: vmStatus === 'Running' ? '#10b981' : vmStatus === 'Stopped' ? '#ef4444' : '#f59e0b' }
        ]}>
          {vmStatus}
        </Text>
      </View>

      <View style={styles.infoCard}>
        <Text style={styles.infoTitle}>VNC Remote Desktop</Text>
        <Text style={styles.infoText}>
          Connect to your VM's desktop through VNC. Make sure the VM is running before attempting to connect.
        </Text>
        <Text style={styles.infoText}>
          VNC Server: 127.0.0.1:5900
        </Text>
      </View>

      <View style={styles.buttonContainer}>
        <TouchableOpacity
          style={[
            styles.connectButton,
            vmStatus !== 'Running' && styles.disabledButton
          ]}
          onPress={connectToVNC}
          disabled={vmStatus !== 'Running'}
        >
          <Text style={styles.buttonText}>Connect to VNC</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.instructionsCard}>
        <Text style={styles.instructionsTitle}>Instructions:</Text>
        <Text style={styles.instructionText}>1. Start the VM from the VM Control tab</Text>
        <Text style={styles.instructionText}>2. Wait for the VM to fully boot</Text>
        <Text style={styles.instructionText}>3. Tap "Connect to VNC" to access the desktop</Text>
        <Text style={styles.instructionText}>4. Use touch gestures to interact with the VM</Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#111827',
    padding: 16,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#374151',
  },
  headerText: {
    color: '#ffffff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  disconnectButton: {
    backgroundColor: '#dc2626',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 6,
  },
  webview: {
    flex: 1,
  },
  statusCard: {
    backgroundColor: '#1f2937',
    borderRadius: 8,
    padding: 16,
    marginBottom: 16,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  statusLabel: {
    color: '#d1d5db',
    fontSize: 16,
  },
  statusText: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  infoCard: {
    backgroundColor: '#1f2937',
    borderRadius: 8,
    padding: 16,
    marginBottom: 16,
  },
  infoTitle: {
    color: '#ffffff',
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 12,
  },
  infoText: {
    color: '#d1d5db',
    fontSize: 14,
    marginBottom: 8,
    lineHeight: 20,
  },
  buttonContainer: {
    marginBottom: 16,
  },
  connectButton: {
    backgroundColor: '#3b82f6',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  disabledButton: {
    backgroundColor: '#4b5563',
    opacity: 0.5,
  },
  buttonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  instructionsCard: {
    backgroundColor: '#1f2937',
    borderRadius: 8,
    padding: 16,
  },
  instructionsTitle: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 12,
  },
  instructionText: {
    color: '#d1d5db',
    fontSize: 14,
    marginBottom: 8,
    lineHeight: 20,
  },
});

export default VNCScreen;