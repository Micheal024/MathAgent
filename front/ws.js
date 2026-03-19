/**
 * WebSocket Client for real-time Agent communication.
 */

function resolveWsBase() {
    const override = window.__MATH_MODELING_CONFIG__?.wsBase;
    if (override) return override.replace(/\/$/, '');

    const meta = document.querySelector('meta[name="ws-base"]')?.content?.trim();
    if (meta) return meta.replace(/\/$/, '');

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.hostname || 'localhost';
    return `${protocol}//${host}:8000`;
}

const WS_BASE = resolveWsBase();

class AgentWebSocket {
    constructor() {
        this.ws = null;
        this.projectId = null;
        this.isConnected = false;
        this.callbacks = {};
        this._reconnectAttempts = 0;
        this._maxReconnect = 5;
        this._reconnectTimer = null;
    }

    /** Register a callback for a message type. */
    on(type, callback) {
        if (!this.callbacks[type]) this.callbacks[type] = [];
        this.callbacks[type].push(callback);
    }

    /** Remove all callbacks. */
    off(type) {
        if (type) {
            delete this.callbacks[type];
        } else {
            this.callbacks = {};
        }
    }

    /** Emit to registered callbacks. */
    _emit(type, data) {
        if (this.callbacks[type]) {
            this.callbacks[type].forEach(cb => cb(data));
        }
        // Also emit 'message' for catch-all listeners
        if (this.callbacks['message']) {
            this.callbacks['message'].forEach(cb => cb({ type, ...data }));
        }
    }

    /** Connect to a project's WebSocket endpoint. */
    connect(projectId) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN && this.projectId === projectId) {
            return;
        }

        this.disconnect();
        this.projectId = projectId;
        this._reconnectAttempts = 0;

        this._doConnect();
    }

    _doConnect() {
        const url = `${WS_BASE}/ws/project/${this.projectId}`;
        this.ws = new WebSocket(url);

        this.ws.onopen = () => {
            this.isConnected = true;
            this._reconnectAttempts = 0;
            this._emit('connected', {});
        };

        this.ws.onclose = () => {
            this.isConnected = false;
            this._emit('disconnected', {});
            this._tryReconnect();
        };

        this.ws.onerror = (err) => {
            console.error('WebSocket error:', err);
        };

        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this._emit(data.type, data);
            } catch (e) {
                console.error('Failed to parse WS message:', e);
            }
        };
    }

    _tryReconnect() {
        if (this._reconnectAttempts >= this._maxReconnect) return;
        this._reconnectAttempts++;
        const delay = Math.min(1000 * Math.pow(2, this._reconnectAttempts), 15000);
        this._reconnectTimer = setTimeout(() => this._doConnect(), delay);
    }

    /** Send a user message. */
    sendMessage(content) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            console.error('WebSocket not connected');
            return false;
        }
        this.ws.send(JSON.stringify({ type: 'user_message', content }));
        return true;
    }

    /** Send a response to AskHuman. */
    sendHumanResponse(content) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            console.error('WebSocket not connected');
            return false;
        }
        this.ws.send(JSON.stringify({ type: 'human_response', content }));
        return true;
    }

    /** Send stop signal to cancel the running agent. */
    sendStop() {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            console.error('WebSocket not connected');
            return false;
        }
        this.ws.send(JSON.stringify({ type: 'stop' }));
        return true;
    }

    /** Send phase confirmation to proceed to next phase. */
    sendPhaseConfirm() {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return false;
        this.ws.send(JSON.stringify({ type: 'phase_confirm' }));
        return true;
    }

    /** Disconnect from WebSocket. */
    disconnect() {
        if (this._reconnectTimer) {
            clearTimeout(this._reconnectTimer);
            this._reconnectTimer = null;
        }
        if (this.ws) {
            this.ws.onclose = null; // Prevent reconnect on intentional close
            this.ws.close();
            this.ws = null;
        }
        this.isConnected = false;
        this.projectId = null;
    }
}

// Singleton instance
const agentWS = new AgentWebSocket();
