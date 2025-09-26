import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  Alert,
  StyleSheet,
  ActivityIndicator,
} from 'react-native';
import { Picker } from '@react-native-picker/picker';
import ApiService from '../services/ApiService';

const VMControlScreen = () => {
  const [vmStatus, setVmStatus] = useState('Checking...');
  const [isLoading, setIsLoading] = useState(false);
  const [config, setConfig] = useState({
    ram_mb: '8192',
    cores: '6',
    cpu_model: 'max',
    primary_disk_path: '',
    cdrom_path: '',
    data_disk_path: '',
    net_device: 'virtio-net-pci',
    vga_model: 'virtio',
    boot_order: 'c',
  });

  const CPU_MODELS = ['max', 'qemu64', 'host', 'Haswell-v4', 'Skylake-Client-v4'];
  const NET_DEVICES = ['virtio-net-pci', 'e1000', 'rtl8139'];
  const VGA_MODELS = ['virtio', 'std', 'qxl', 'vmware', 'cirrus'];
  const BOOT_ORDERS = ['c', 'd', 'n', 'cd', 'dc', 'ncd', 'dcn'];

  useEffect(() => {
    loadDefaults();
    updateVmStatus();
    const interval = setInterval(updateVmStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadDefaults = async () => {
    try {
      const defaults = await ApiService.getDefaults();
      setConfig({
        ram_mb: defaults.default_ram_mb.toString(),
        cores: defaults.default_cores.toString(),
        cpu_model: defaults.default_cpu_model,
        primary_disk_path: defaults.default_primary_disk_path,
        cdrom_path: defaults.default_cdrom_path,
        data_disk_path: defaults.default_data_disk_path,
        net_device: defaults.default_net_device,
        vga_model: defaults.default_vga_model,
        boot_order: defaults.default_boot_order,
      });
    } catch (error) {
      Alert.alert('Error', 'Failed to load default settings');
    }
  };

  const updateVmStatus = async () => {
    try {
      const status = await ApiService.getVmStatus();
      setVmStatus(status.running ? 'Running' : 'Stopped');
    } catch (error) {
      setVmStatus('Error (Server Down?)');
    }
  };

  const startVM = async () => {
    if (!config.primary_disk_path.trim()) {
      Alert.alert('Error', 'Primary Disk Path is required');
      return;
    }

    setIsLoading(true);
    try {
      const vmConfig = {
        ...config,
        ram_mb: parseInt(config.ram_mb),
        cores: parseInt(config.cores),
      };
      
      const response = await ApiService.startVM(vmConfig);
      Alert.alert('Success', response.message);
      setTimeout(updateVmStatus, 2000);
    } catch (error) {
      Alert.alert('Error', error.message || 'Failed to start VM');
    } finally {
      setIsLoading(false);
    }
  };

  const stopVM = async () => {
    setIsLoading(true);
    try {
      const response = await ApiService.stopVM();
      Alert.alert('Success', response.message);
      setTimeout(updateVmStatus, 1000);
    } catch (error) {
      Alert.alert('Error', error.message || 'Failed to stop VM');
    } finally {
      setIsLoading(false);
    }
  };

  const updateConfig = (key, value) => {
    setConfig(prev => ({ ...prev, [key]: value }));
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.statusCard}>
        <Text style={styles.statusLabel}>VM Status:</Text>
        <Text style={[
          styles.statusText,
          { color: vmStatus === 'Running' ? '#10b981' : vmStatus === 'Stopped' ? '#ef4444' : '#f59e0b' }
        ]}>
          {vmStatus}
        </Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Core Settings</Text>
        
        <View style={styles.row}>
          <View style={styles.inputContainer}>
            <Text style={styles.label}>RAM (MB)</Text>
            <TextInput
              style={styles.input}
              value={config.ram_mb}
              onChangeText={(value) => updateConfig('ram_mb', value)}
              keyboardType="numeric"
              placeholderTextColor="#9ca3af"
            />
          </View>
          
          <View style={styles.inputContainer}>
            <Text style={styles.label}>CPU Cores</Text>
            <TextInput
              style={styles.input}
              value={config.cores}
              onChangeText={(value) => updateConfig('cores', value)}
              keyboardType="numeric"
              placeholderTextColor="#9ca3af"
            />
          </View>
        </View>

        <View style={styles.inputContainer}>
          <Text style={styles.label}>CPU Model</Text>
          <View style={styles.pickerContainer}>
            <Picker
              selectedValue={config.cpu_model}
              onValueChange={(value) => updateConfig('cpu_model', value)}
              style={styles.picker}
              dropdownIconColor="#ffffff"
            >
              {CPU_MODELS.map(model => (
                <Picker.Item key={model} label={model} value={model} color="#ffffff" />
              ))}
            </Picker>
          </View>
        </View>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Storage</Text>
        
        <View style={styles.inputContainer}>
          <Text style={styles.label}>Primary Disk Path (.qcow2)</Text>
          <TextInput
            style={styles.input}
            value={config.primary_disk_path}
            onChangeText={(value) => updateConfig('primary_disk_path', value)}
            placeholder="Windows_100G.qcow2"
            placeholderTextColor="#9ca3af"
          />
        </View>

        <View style={styles.inputContainer}>
          <Text style={styles.label}>CD-ROM / ISO Path</Text>
          <TextInput
            style={styles.input}
            value={config.cdrom_path}
            onChangeText={(value) => updateConfig('cdrom_path', value)}
            placeholder="win10.iso"
            placeholderTextColor="#9ca3af"
          />
        </View>

        <View style={styles.inputContainer}>
          <Text style={styles.label}>Secondary Data Disk (.qcow2)</Text>
          <TextInput
            style={styles.input}
            value={config.data_disk_path}
            onChangeText={(value) => updateConfig('data_disk_path', value)}
            placeholder="data.qcow2"
            placeholderTextColor="#9ca3af"
          />
        </View>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Network & Display</Text>
        
        <View style={styles.row}>
          <View style={styles.inputContainer}>
            <Text style={styles.label}>Network Device</Text>
            <View style={styles.pickerContainer}>
              <Picker
                selectedValue={config.net_device}
                onValueChange={(value) => updateConfig('net_device', value)}
                style={styles.picker}
                dropdownIconColor="#ffffff"
              >
                {NET_DEVICES.map(device => (
                  <Picker.Item key={device} label={device} value={device} color="#ffffff" />
                ))}
              </Picker>
            </View>
          </View>

          <View style={styles.inputContainer}>
            <Text style={styles.label}>VGA Model</Text>
            <View style={styles.pickerContainer}>
              <Picker
                selectedValue={config.vga_model}
                onValueChange={(value) => updateConfig('vga_model', value)}
                style={styles.picker}
                dropdownIconColor="#ffffff"
              >
                {VGA_MODELS.map(model => (
                  <Picker.Item key={model} label={model} value={model} color="#ffffff" />
                ))}
              </Picker>
            </View>
          </View>
        </View>

        <View style={styles.inputContainer}>
          <Text style={styles.label}>Boot Order</Text>
          <View style={styles.pickerContainer}>
            <Picker
              selectedValue={config.boot_order}
              onValueChange={(value) => updateConfig('boot_order', value)}
              style={styles.picker}
              dropdownIconColor="#ffffff"
            >
              {BOOT_ORDERS.map(order => (
                <Picker.Item key={order} label={order} value={order} color="#ffffff" />
              ))}
            </Picker>
          </View>
        </View>
      </View>

      <View style={styles.buttonContainer}>
        <TouchableOpacity
          style={[styles.button, styles.startButton, isLoading && styles.disabledButton]}
          onPress={startVM}
          disabled={isLoading || vmStatus === 'Running'}
        >
          {isLoading ? (
            <ActivityIndicator color="#ffffff" />
          ) : (
            <Text style={styles.buttonText}>Start VM</Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.button, styles.stopButton, isLoading && styles.disabledButton]}
          onPress={stopVM}
          disabled={isLoading || vmStatus === 'Stopped'}
        >
          {isLoading ? (
            <ActivityIndicator color="#ffffff" />
          ) : (
            <Text style={styles.buttonText}>Stop VM</Text>
          )}
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
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  inputContainer: {
    flex: 1,
    marginBottom: 16,
    marginHorizontal: 4,
  },
  label: {
    color: '#d1d5db',
    fontSize: 14,
    marginBottom: 8,
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
  pickerContainer: {
    backgroundColor: '#374151',
    borderWidth: 1,
    borderColor: '#4b5563',
    borderRadius: 6,
  },
  picker: {
    color: '#ffffff',
    height: 50,
  },
  buttonContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 16,
    marginBottom: 32,
  },
  button: {
    flex: 1,
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginHorizontal: 8,
  },
  startButton: {
    backgroundColor: '#059669',
  },
  stopButton: {
    backgroundColor: '#dc2626',
  },
  disabledButton: {
    opacity: 0.5,
  },
  buttonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});

export default VMControlScreen;