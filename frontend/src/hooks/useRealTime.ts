import { useState, useEffect, useRef, useCallback } from 'react';
import { useToast } from '@/components/Toast';

export interface RealTimeNotification {
  id: string;
  type: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  title: string;
  message: string;
  data?: any;
  user_id?: string;
  client_id?: string;
  created_at: string;
  expires_at?: string;
  read: boolean;
}

export interface UserActivity {
  user_id: string;
  username: string;
  activity: string;
  timestamp: string;
}

export interface ActiveUser {
  user_id: string;
  username: string;
  role: string;
  connected_at: string;
  last_activity: string;
  active_client_id?: string;
  connections: number;
}

interface UseRealTimeProps {
  userId: string;
  username: string;
  role: string;
  onNotification?: (notification: RealTimeNotification) => void;
  onUserActivity?: (activity: UserActivity) => void;
  onConnectionChange?: (connected: boolean) => void;
  autoReconnect?: boolean;
}

interface RealTimeState {
  connected: boolean;
  connecting: boolean;
  notifications: RealTimeNotification[];
  activeUsers: ActiveUser[];
  lastError: string | null;
  connectionId: string | null;
}

export const useRealTime = ({
  userId,
  username,
  role,
  onNotification,
  onUserActivity,
  onConnectionChange,
  autoReconnect = true
}: UseRealTimeProps) => {
  const { addToast } = useToast();
  
  const [state, setState] = useState<RealTimeState>({
    connected: false,
    connecting: false,
    notifications: [],
    activeUsers: [],
    lastError: null,
    connectionId: null
  });

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setState(prev => ({ ...prev, connecting: true, lastError: null }));

    try {
      const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'}/ws/${userId}?username=${encodeURIComponent(username)}&role=${encodeURIComponent(role)}`;
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('WebSocket connected');
        setState(prev => ({ 
          ...prev, 
          connected: true, 
          connecting: false, 
          lastError: null 
        }));
        
        reconnectAttemptsRef.current = 0;
        onConnectionChange?.(true);

        // Start ping interval to keep connection alive
        pingIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }));
          }
        }, 30000); // Ping every 30 seconds

        // Send initial activity
        ws.send(JSON.stringify({
          type: 'user_activity',
          data: {
            activity: 'connected',
            timestamp: new Date().toISOString()
          }
        }));
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          
          switch (message.type) {
            case 'connection_established':
              setState(prev => ({ 
                ...prev, 
                connectionId: message.connection_id 
              }));
              addToast({ type: 'success', title: message.message });
              break;

            case 'notification':
              const notification = message.notification;
              setState(prev => ({
                ...prev,
                notifications: [notification, ...prev.notifications].slice(0, 50) // Keep last 50
              }));
              
              onNotification?.(notification);
              
              // Show toast based on priority
              switch (notification.priority) {
                case 'urgent':
                  addToast({ type: 'error', title: notification.message, duration: 10000 });
                  break;
                case 'high':
                  addToast({ type: 'warning', title: notification.message, duration: 6000 });
                  break;
                case 'medium':
                  addToast({ type: 'success', title: notification.message, duration: 4000 });
                  break;
                case 'low':
                  addToast({ type: 'info', title: notification.message, duration: 3000 });
                  break;
              }
              break;

            case 'user_activity':
              const activity = message.data;
              onUserActivity?.(activity);
              
              // Show subtle notification for user activities
              if (activity.activity === 'connected') {
                addToast({ type: 'info', title: `${activity.username} joined`, duration: 2000 });
              } else if (activity.activity === 'disconnected') {
                addToast({ type: 'info', title: `${activity.username} left`, duration: 2000 });
              }
              break;

            case 'auto_save_trigger':
              // Trigger auto-save in the form
              const autoSaveEvent = new CustomEvent('autoSave', { 
                detail: { clientId: message.client_id } 
              });
              window.dispatchEvent(autoSaveEvent);
              break;

            case 'collaboration_update':
              // Handle real-time collaboration updates
              const collabUpdate = message.data;
              addToast({
                type: 'info',
                title: `${collabUpdate.username} is working on ${collabUpdate.client_id}`,
                duration: 3000
              });
              break;

            case 'idle_warning':
              addToast({ type: 'error', title: message.message, duration: 8000 });
              break;

            case 'pong':
              // Handle ping response - connection is alive
              break;

            case 'error':
              console.error('WebSocket error message:', message.message);
              addToast({ type: 'error', title: message.message });
              break;

            default:
              console.log('Unknown message type:', message.type);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        setState(prev => ({ 
          ...prev, 
          connected: false, 
          connecting: false,
          connectionId: null
        }));
        
        onConnectionChange?.(false);

        // Clear ping interval
        if (pingIntervalRef.current) {
          clearInterval(pingIntervalRef.current);
          pingIntervalRef.current = null;
        }

        // Auto-reconnect if enabled and not too many attempts
        if (autoReconnect && reconnectAttemptsRef.current < maxReconnectAttempts) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
          reconnectAttemptsRef.current++;
          
          addToast({
            type: 'info',
            title: `Connection lost. Reconnecting in ${delay/1000}s...`,
            duration: delay
          });

          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, delay);
        } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
          setState(prev => ({
            ...prev,
            lastError: 'Max reconnection attempts reached'
          }));
          addToast({ type: 'error', title: 'Connection lost. Please refresh the page.' });
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setState(prev => ({ 
          ...prev, 
          lastError: 'Connection error',
          connecting: false
        }));
      };

      wsRef.current = ws;

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setState(prev => ({ 
        ...prev, 
        lastError: 'Failed to connect',
        connecting: false
      }));
    }
  }, [userId, username, role, onNotification, onUserActivity, onConnectionChange, autoReconnect, addToast]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setState(prev => ({ 
      ...prev, 
      connected: false, 
      connecting: false,
      connectionId: null
    }));
  }, []);

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
      return true;
    }
    return false;
  }, []);

  const sendUserActivity = useCallback((activity: string, data?: any) => {
    return sendMessage({
      type: 'user_activity',
      data: {
        activity,
        timestamp: new Date().toISOString(),
        ...data
      }
    });
  }, [sendMessage]);

  const startAutoSave = useCallback((clientId: string, interval: number = 30) => {
    return sendMessage({
      type: 'start_auto_save',
      client_id: clientId,
      interval
    });
  }, [sendMessage]);

  const stopAutoSave = useCallback(() => {
    return sendMessage({
      type: 'stop_auto_save'
    });
  }, [sendMessage]);

  const markNotificationRead = useCallback((notificationId: string) => {
    setState(prev => ({
      ...prev,
      notifications: prev.notifications.map(n => 
        n.id === notificationId ? { ...n, read: true } : n
      )
    }));
  }, []);

  const clearNotifications = useCallback(() => {
    setState(prev => ({ ...prev, notifications: [] }));
  }, []);

  // Initialize connection on mount
  useEffect(() => {
    if (userId && username) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [userId, username, connect, disconnect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    ...state,
    connect,
    disconnect,
    sendMessage,
    sendUserActivity,
    startAutoSave,
    stopAutoSave,
    markNotificationRead,
    clearNotifications,
    unreadCount: state.notifications.filter(n => !n.read).length
  };
};