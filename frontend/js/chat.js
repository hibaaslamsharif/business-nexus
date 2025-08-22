// Chat functionality with Socket.io
class ChatApp {
    constructor() {
        this.socket = null;
        this.currentUserId = this.getCurrentUserId();
        this.currentUsername = localStorage.getItem('username') || 'User';
        this.currentRole = localStorage.getItem('role') || 'user';
        this.otherUserId = this.getOtherUserIdFromUrl();
        this.otherUsername = null;
        this.roomName = null;
        
        this.initializeElements();
        this.connectSocket();
        this.loadChatHistory();
        this.setupEventListeners();
        this.setupBackButton();
    }
    
    getCurrentUserId() {
        // Extract user ID from token or use a default method
        const token = localStorage.getItem('token');
        if (token) {
            try {
                const payload = JSON.parse(atob(token.split('.')[1]));
                return payload.user_id;
            } catch (e) {
                console.error('Error parsing token:', e);
            }
        }
        return 1; // fallback
    }
    
    getOtherUserIdFromUrl() {
        const pathParts = window.location.pathname.split('/');
        return parseInt(pathParts[pathParts.length - 2]); // Get user ID from /chat/:userId/
    }
    
    initializeElements() {
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.chatTitle = document.getElementById('chatTitle');
        this.onlineStatus = document.getElementById('onlineStatus');
        this.typingIndicator = document.getElementById('typingIndicator');
        
        // Will update title after loading user info
        this.loadOtherUserInfo();
    }
    
    async loadOtherUserInfo() {
        try {
            console.log('Loading user info for ID:', this.otherUserId);
            const response = await fetch('/api/users/list/');
            const data = await response.json();
            
            console.log('Users data:', data);
            
            if (data.success) {
                const otherUser = data.users.find(user => user.id == this.otherUserId);
                console.log('Found user:', otherUser);
                
                if (otherUser) {
                    this.otherUsername = otherUser.username;
                    this.chatTitle.textContent = `Chat with ${otherUser.username}`;
                    console.log('Updated title to:', this.chatTitle.textContent);
                } else {
                    console.log('User not found, using fallback');
                    this.chatTitle.textContent = `Chat with User ${this.otherUserId}`;
                }
            } else {
                console.log('API call failed');
                this.chatTitle.textContent = `Chat with User ${this.otherUserId}`;
            }
        } catch (error) {
            console.error('Error loading user info:', error);
            this.chatTitle.textContent = `Chat with User ${this.otherUserId}`;
        }
    }
    
    setupBackButton() {
        const backButton = document.getElementById('backToDashboard');
        if (backButton) {
            backButton.addEventListener('click', (e) => {
                e.preventDefault();
                console.log('Back button clicked, role:', this.currentRole);
                
                const role = this.currentRole;
                if (role === 'investor') {
                    console.log('Redirecting to investor dashboard');
                    window.location.href = '/dashboard_investor/';
                } else if (role === 'entrepreneur') {
                    console.log('Redirecting to entrepreneur dashboard');
                    window.location.href = '/dashboard_entrepreneur/';
                } else {
                    console.log('Redirecting to home');
                    window.location.href = '/';
                }
            });
        } else {
            console.error('Back button not found');
        }
    }
    
    connectSocket() {
        try {
            this.socket = io('http://localhost:5000', {
                transports: ['websocket', 'polling'],
                timeout: 5000,
                forceNew: true
            });
            
            this.socket.on('connect', () => {
                console.log('Connected to chat server');
                this.onlineStatus.textContent = 'Online';
                this.onlineStatus.style.color = '#28a745';
                this.joinRoom();
            });
            
            this.socket.on('connected', (data) => {
                console.log('Server confirmation:', data.message);
            });
            
            this.socket.on('joined_room', (data) => {
                console.log('Joined room:', data.room);
                this.roomName = data.room;
            });
            
            this.socket.on('receive_message', (message) => {
                this.displayMessage(message);
                this.scrollToBottom();
            });
            
            this.socket.on('disconnect', () => {
                console.log('Disconnected from chat server');
                this.onlineStatus.textContent = 'Offline';
                this.onlineStatus.style.color = '#dc3545';
            });
            
            this.socket.on('connect_error', (error) => {
                console.error('Connection error:', error);
                this.onlineStatus.textContent = 'Connection Failed';
                this.onlineStatus.style.color = '#dc3545';
                // Fallback to basic messaging without real-time
                this.enableBasicMessaging();
            });
            
            this.socket.on('error', (error) => {
                console.error('Socket error:', error);
            });
        } catch (error) {
            console.error('Socket initialization error:', error);
            this.enableBasicMessaging();
        }
    }
    
    enableBasicMessaging() {
        // Fallback messaging without Socket.io
        console.log('Using basic messaging mode');
        this.onlineStatus.textContent = 'Basic Mode';
        this.onlineStatus.style.color = '#ffc107';
    }
    
    joinRoom() {
        this.socket.emit('join_room', {
            user_id: this.currentUserId,
            other_user_id: this.otherUserId
        });
    }
    
    async loadChatHistory() {
        try {
            const response = await fetch(`/api/chat/${this.otherUserId}/?current_user=${this.currentUserId}`);
            const data = await response.json();
            
            if (data.success) {
                this.chatMessages.innerHTML = '';
                data.messages.forEach(message => {
                    this.displayMessage(message, false); // false = don't scroll for each message
                });
                this.scrollToBottom();
            } else {
                console.error('Failed to load chat history:', data.error);
            }
        } catch (error) {
            console.error('Error loading chat history:', error);
        }
    }
    
    displayMessage(message, shouldScroll = true) {
        const messageDiv = document.createElement('div');
        const isSent = message.sender_id == this.currentUserId;
        
        messageDiv.className = `message ${isSent ? 'sent' : 'received'}`;
        
        const timestamp = new Date(message.timestamp).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit'
        });
        
        messageDiv.innerHTML = `
            <div class="message-bubble">
                <div class="message-text">${this.escapeHtml(message.message)}</div>
                <div class="message-info">
                    ${isSent ? 'You' : message.sender_name} • ${timestamp}
                </div>
            </div>
        `;
        
        this.chatMessages.appendChild(messageDiv);
        
        if (shouldScroll) {
            this.scrollToBottom();
        }
    }
    
    sendMessage() {
        const messageText = this.messageInput.value.trim();
        console.log('Send message called with text:', messageText);
        
        if (!messageText) {
            console.log('No message text, returning');
            return;
        }
        
        const messageData = {
            sender_id: this.currentUserId,
            receiver_id: this.otherUserId,
            message: messageText,
            sender_name: this.currentUsername
        };
        
        console.log('Message data:', messageData);
        console.log('Socket connected?', this.socket && this.socket.connected);
        
        // Always use API for now to ensure messages work
        this.sendMessageViaAPI(messageData);
        
        // Clear input immediately
        this.messageInput.value = '';
        console.log('Input cleared');
    }
    
    async sendMessageViaAPI(messageData) {
        try {
            console.log('Sending message via API:', messageData);
            const response = await fetch('/api/send-message/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(messageData)
            });
            
            console.log('API response status:', response.status);
            
            if (response.ok) {
                const result = await response.json();
                console.log('Message sent successfully:', result);
                
                // Display message immediately
                this.displayMessage({
                    ...messageData,
                    timestamp: new Date().toISOString()
                });
                this.scrollToBottom();
            } else {
                console.error('Failed to send message, status:', response.status);
                const errorText = await response.text();
                console.error('Error response:', errorText);
            }
        } catch (error) {
            console.error('Error sending message via API:', error);
        }
    }
    
    setupEventListeners() {
        this.sendButton.addEventListener('click', (e) => {
            e.preventDefault();
            console.log('Send button clicked');
            this.sendMessage();
        });
        
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                console.log('Enter key pressed');
                this.sendMessage();
            }
        });
        
        // Auto-focus on message input
        this.messageInput.focus();
    }
    
    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize chat when page loads
document.addEventListener('DOMContentLoaded', () => {
    new ChatApp();
});
