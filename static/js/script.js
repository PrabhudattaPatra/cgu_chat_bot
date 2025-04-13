document.addEventListener('DOMContentLoaded', function() {
    const chatContainer = document.getElementById('chat-container');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-btn');
    const resetButton = document.getElementById('reset-btn');
    
    // Auto-resize textarea as user types
    userInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight > 120 ? 120 : this.scrollHeight) + 'px';
    });
    
    // Send message when Enter key is pressed (without Shift)
    userInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Send message when send button is clicked
    sendButton.addEventListener('click', sendMessage);
    
    // Reset conversation
    resetButton.addEventListener('click', resetConversation);
    
    function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;
        
        // Add user message to chat
        addMessageToChat('user', message);
        
        // Clear input
        userInput.value = '';
        userInput.style.height = 'auto';
        
        // Show typing indicator
        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'typing-indicator';
        typingIndicator.innerHTML = `
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        `;
        chatContainer.appendChild(typingIndicator);
        scrollToBottom();
        
        // Send message to server
        fetch('/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message }),
        })
        .then(response => response.json())
        .then(data => {
            // Remove typing indicator
            typingIndicator.remove();
            
            // Add assistant response to chat
            addMessageToChat('assistant', data.response);
        })
        .catch(error => {
            console.error('Error:', error);
            typingIndicator.remove();
            addMessageToChat('assistant', 'Sorry, there was an error processing your request. Please try again.');
        });
    }
    
    function addMessageToChat(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = role === 'user' ? 'user-message' : 'assistant-message';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        // For assistant messages, we want to render the HTML content
        // For user messages, we want to escape it
        if (role === 'assistant') {
            // Convert markdown-like formatting to HTML
            content = parseMarkdown(content);
            messageContent.innerHTML = `<p>${content}</p>`;
        } else {
            const p = document.createElement('p');
            p.textContent = content;
            messageContent.appendChild(p);
        }
        
        messageDiv.appendChild(messageContent);
        chatContainer.appendChild(messageDiv);
        
        scrollToBottom();
    }
    
    function parseMarkdown(text) {
        // Convert markdown to HTML
        // Bold
        text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

        // Headings
        text = text.replace(/^### (.*?)$/gm, '<h3>$1</h3>');
        text = text.replace(/^## (.*?)$/gm, '<h2>$1</h2>');
        text = text.replace(/^# (.*?)$/gm, '<h1>$1</h1>');

        // URLs to clickable links
        text = text.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');

        // Add table parsing
        if (text.includes('|')) {
            const lines = text.split('\n');
            let tableContent = '';
            let inTable = false;
            let tableRows = [];

            lines.forEach(line => {
                if (line.includes('|')) {
                    inTable = true;
                    tableRows.push(line);
                } else {
                    if (inTable && tableRows.length > 0) {
                        tableContent += createHtmlTable(tableRows);
                        tableRows = [];
                        inTable = false;
                    }
                    tableContent += line + '<br>';
                }
            });

            if (inTable && tableRows.length > 0) {
                tableContent += createHtmlTable(tableRows);
            }
            return tableContent;
        }

        // Lists
        text = text.replace(/^\* (.*?)$/gm, '<li>$1</li>');
        text = text.replace(/(<li>.*?<\/li>)\n(<li>.*?<\/li>)/gs, '$1$2');
        text = text.replace(/(<li>.*?<\/li>)+/g, '<ul>$&</ul>');

        // Line breaks
        text = text.replace(/\n/g, '<br>');

        return text;
    }
    
    function createHtmlTable(rows) {
        let tableHtml = '<table class="markdown-table">';
        
        rows.forEach((row, rowIndex) => {
            // Clean the row
            row = row.trim();
            if (row.startsWith('|')) row = row.substring(1);
            if (row.endsWith('|')) row = row.substring(0, row.length - 1);
            
            // Skip separator rows (consisting mainly of dashes)
            if (row.replace(/[\|\-\s]/g, '').length === 0) return;
            
            const cells = row.split('|').map(cell => cell.trim());
            
            tableHtml += '<tr>';
            cells.forEach(cell => {
                // Determine if this is a header row
                const cellTag = rowIndex === 0 ? 'th' : 'td';
                tableHtml += `<${cellTag}>${cell}</${cellTag}>`;
            });
            tableHtml += '</tr>';
        });
        
        tableHtml += '</table>';
        return tableHtml;
    }
    
    function scrollToBottom() {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
    
    function resetConversation() {
        if (confirm('Are you sure you want to reset this conversation?')) {
            fetch('/reset', {
                method: 'POST',
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Clear chat container except for welcome message
                    chatContainer.innerHTML = `
                        <div class="welcome-message">
                            <div class="assistant-message">
                                <div class="message-content">
                                    <p>Welcome to CGU AI Assistant! I can help you with information about C.V. Raman Global University, Odisha. Ask me about admissions, programs, fees, facilities, or anything else about the university.</p>
                                </div>
                            </div>
                        </div>
                    `;
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        }
    }
    
    // Initial scroll to bottom
    scrollToBottom();
});