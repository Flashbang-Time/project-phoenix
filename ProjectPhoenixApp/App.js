import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import { StatusBar } from 'expo-status-bar';

import VMControlScreen from './src/screens/VMControlScreen';
import VNCScreen from './src/screens/VNCScreen';
import TerminalScreen from './src/screens/TerminalScreen';
import SettingsScreen from './src/screens/SettingsScreen';

const Tab = createBottomTabNavigator();

export default function App() {
  return (
    <NavigationContainer>
      <StatusBar style="light" backgroundColor="#1f2937" />
      <Tab.Navigator
        screenOptions={({ route }) => ({
          tabBarIcon: ({ focused, color, size }) => {
            let iconName;

            if (route.name === 'VM Control') {
              iconName = focused ? 'desktop' : 'desktop-outline';
            } else if (route.name === 'VNC') {
              iconName = focused ? 'tv' : 'tv-outline';
            } else if (route.name === 'Terminal') {
              iconName = focused ? 'terminal' : 'terminal-outline';
            } else if (route.name === 'Settings') {
              iconName = focused ? 'settings' : 'settings-outline';
            }

            return <Ionicons name={iconName} size={size} color={color} />;
          },
          tabBarActiveTintColor: '#3b82f6',
          tabBarInactiveTintColor: '#9ca3af',
          tabBarStyle: {
            backgroundColor: '#1f2937',
            borderTopColor: '#374151',
          },
          headerStyle: {
            backgroundColor: '#1f2937',
          },
          headerTintColor: '#ffffff',
          headerTitleStyle: {
            fontWeight: 'bold',
          },
        })}
      >
        <Tab.Screen name="VM Control" component={VMControlScreen} />
        <Tab.Screen name="VNC" component={VNCScreen} />
        <Tab.Screen name="Terminal" component={TerminalScreen} />
        <Tab.Screen name="Settings" component={SettingsScreen} />
      </Tab.Navigator>
    </NavigationContainer>
  );
}