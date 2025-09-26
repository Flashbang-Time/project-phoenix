import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  Alert,
} from 'react-native';
import ApiService from '../services/ApiService';

const TerminalScreen = () => {
  const [command, setCommand] = useState('');
  const [output, setOutput] = useState([]);
  const [isExecuting, setIsExecuting] = useState(false);
  const scrollViewRef = useRef();

  useEffect(() => {
    fetchOutput();
    const interval = setInterval(fetchOutput, 1500);
    return () => clearInterval(interval);
  }, []);

  const fetchOutput = async () => {
    try {
      const response = await ApiService.getTerminalOutput();
      if (response.output && response.output.length > 0) {
        setOutput(prev => [...prev, ...response.output]);
        // Auto-scroll to bottom
        setTimeout(() => {
          scrollViewRef.current?.scrollToEnd({ animated: true });
        }, 100);
      }
    } catch (error) {
      console.error('Failed to fetch terminal output:', error);
    }
  };

  const executeCommand = async () => {
    if (!command.trim()) {
      Alert.alert('Error', 'Please enter a command');
      return;
    }

    setIsExecuting(true);
    try {
      await ApiService.runTerminalCommand(command);
      setCommand('');
    } catch (error) {
      Alert.alert('Error', error.message || 'Failed to execute command');
    } finally {
      setIsExecuting(false);
    }
  };

  const clearOutput = () => {
    setOutput([]);
  };

  const getLineStyle = (type) => {
    switch (type) {
      case 'command':
        return { color: '#f3f4f6', fontWeight: 'bold' };
      case 'error':
        return { color: '#f87171' };
      case 'success':
        return { color: '#4ade80' };
      case 'info':
        return { color: '#60a5fa' };
      default:
        return { color: '#cbd5e1' };
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerText}>Terminal</Text>
        <TouchableOpacity style={styles.clearButton} onPress={clearOutput}>
          <Text style={styles.clearButtonText}>Clear</Text>
        </TouchableOpacity>
      </View>

      <ScrollView
        ref={scrollViewRef}
        style={styles.outputContainer}
        showsVerticalScrollIndicator={true}
      >
        {output.length === 0 ? (
          <Text style={styles.emptyText}>No output yet. Run a command to see results.</Text>
        ) : (
          output.map((line, index) => (
            <Text
              key={index}
              style={[styles.outputLine, getLineStyle(line.type)]}
            >
              {line.message}
            </Text>
          ))
        )}
      </ScrollView>

      <View style={styles.inputContainer}>
        <TextInput
          style={styles.commandInput}
          value={command}
          onChangeText={setCommand}
          placeholder="Enter command..."
          placeholderTextColor="#9ca3af"
          multiline={false}
          onSubmitEditing={executeCommand}
          editable={!isExecuting}
        />
        <TouchableOpacity
          style={[styles.executeButton, isExecuting && styles.disabledButton]}
          onPress={executeCommand}
          disabled={isExecuting}
        >
          <Text style={styles.executeButtonText}>
            {isExecuting ? 'Running...' : 'Run'}
          </Text>
        </TouchableOpacity>
      </View>

      <View style={styles.quickCommands}>
        <Text style={styles.quickCommandsTitle}>Quick Commands:</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          {['ls -la', 'ps aux', 'df -h', 'free -h', 'uname -a'].map((cmd) => (
            <TouchableOpacity
              key={cmd}
              style={styles.quickCommandButton}
              onPress={() => setCommand(cmd)}
            >
              <Text style={styles.quickCommandText}>{cmd}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#111827',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#374151',
  },
  headerText: {
    color: '#ffffff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  clearButton: {
    backgroundColor: '#374151',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  clearButtonText: {
    color: '#ffffff',
    fontSize: 14,
  },
  outputContainer: {
    flex: 1,
    backgroundColor: '#0f172a',
    margin: 16,
    marginBottom: 0,
    borderRadius: 8,
    padding: 12,
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  emptyText: {
    color: '#6b7280',
    fontStyle: 'italic',
    textAlign: 'center',
    marginTop: 20,
  },
  outputLine: {
    fontFamily: 'monospace',
    fontSize: 12,
    lineHeight: 18,
    marginBottom: 2,
  },
  inputContainer: {
    flexDirection: 'row',
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: '#374151',
  },
  commandInput: {
    flex: 1,
    backgroundColor: '#374151',
    borderWidth: 1,
    borderColor: '#4b5563',
    borderRadius: 6,
    padding: 12,
    color: '#ffffff',
    fontSize: 14,
    fontFamily: 'monospace',
    marginRight: 12,
  },
  executeButton: {
    backgroundColor: '#3b82f6',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 6,
    justifyContent: 'center',
  },
  disabledButton: {
    backgroundColor: '#4b5563',
    opacity: 0.5,
  },
  executeButtonText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: 'bold',
  },
  quickCommands: {
    padding: 16,
    paddingTop: 0,
  },
  quickCommandsTitle: {
    color: '#d1d5db',
    fontSize: 14,
    marginBottom: 8,
  },
  quickCommandButton: {
    backgroundColor: '#374151',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    marginRight: 8,
  },
  quickCommandText: {
    color: '#ffffff',
    fontSize: 12,
    fontFamily: 'monospace',
  },
});

export default TerminalScreen;