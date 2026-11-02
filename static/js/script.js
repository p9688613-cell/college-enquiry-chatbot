/**
 * script.js - Client-Side Chatbot Controller
 * ==========================================
 * Manages:
 * - Real-time asynchronous communication with Flask backend (/api/chat)
 * - Message rendering with timestamps and formatted lists
 * - Clickable suggested follow-up questions
 * - Typing indicator during AI inference
 * - Speech-to-Text (voice recognition) & Text-to-Speech (audio read-out)
 * - Session chat clearing
 */

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const chatForm = document.getElementById('chatForm');
    const userInput = document.getElementById('userInput');
    const chatMessages = document.getElementById('chatMessages');
    const typingIndicator = document.getElementById('typingIndicator');
    const clearChatBtn = document.getElementById('clearChatBtn');
    const ttsToggleBtn = document.getElementById('ttsToggleBtn');
    const voiceInputBtn = document.getElementById('voiceInputBtn');
    const quickTopics = document.getElementById('quickTopics');

    // State Variables
    let isTtsEnabled = false;
    let isRecognitionActive = false;

    // Set initial timestamp
    const initialTimestamp = document.getElementById('initialTimestamp');
    if (initialTimestamp) {
        initialTimestamp.textContent = getCurrentTime();
    }

    // =========================================================================
    // EVENT LISTENERS
    // =========================================================================

    // Form submit / Enter key
    chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        sendMessage();
    });

    // Enter key inside input
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            sendMessage();
        }
    });

    // Quick Topic chips click delegation
    quickTopics.addEventListener('click', (e) => {
        const chip = e.target.closest('.topic-chip');
        if (chip) {
            const query = chip.getAttribute('data-query');
            if (query) {
                userInput.value = query;
                sendMessage();
            }
        }
    });

    // Interactive suggestion buttons click delegation
    chatMessages.addEventListener('click', (e) => {
        const btn = e.target.closest('.suggestion-btn');
        if (btn) {
            const query = btn.getAttribute('data-query');
            if (query) {
                userInput.value = query;
                sendMessage();
            }
        }
    });

    // Clear chat session
    clearChatBtn.addEventListener('click', () => {
        if (confirm('Are you sure you want to clear your current chat history?')) {
            clearChatSession();
        }
    });

    // Toggle Text-to-Speech
    ttsToggleBtn.addEventListener('click', () => {
        isTtsEnabled = !isTtsEnabled;
        ttsToggleBtn.classList.toggle('active', isTtsEnabled);
        if (isTtsEnabled) {
            ttsToggleBtn.title = 'Voice Output: ON (Click to mute)';
            speakText('Voice output enabled');
        } else {
            ttsToggleBtn.title = 'Voice Output: OFF (Click to unmute)';
            window.speechSynthesis?.cancel();
        }
    });

    // Voice recognition (Speech to text)
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';

        voiceInputBtn.addEventListener('click', () => {
            if (isRecognitionActive) {
                recognition.stop();
                return;
            }
            try {
                recognition.start();
                voiceInputBtn.classList.add('listening');
                isRecognitionActive = true;
            } catch (err) {
                console.warn('Speech recognition start failed:', err);
            }
        });

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            userInput.value = transcript;
            voiceInputBtn.classList.remove('listening');
            isRecognitionActive = false;
            sendMessage();
        };

        recognition.onerror = () => {
            voiceInputBtn.classList.remove('listening');
            isRecognitionActive = false;
        };

        recognition.onend = () => {
            voiceInputBtn.classList.remove('listening');
            isRecognitionActive = false;
        };
    } else {
        voiceInputBtn.style.display = 'none'; // Browser does not support speech recognition
    }

    // =========================================================================
    // CORE CHAT FUNCTIONS
    // =========================================================================

    /**
     * Send student query to Flask server and render response.
     */
    async function sendMessage() {
        const rawText = userInput.value;
        const cleanText = rawText.trim();

        if (!cleanText) {
            userInput.focus();
            return;
        }

        // 1. Append User Message
        appendUserMessage(cleanText);
        userInput.value = '';
        userInput.focus();

        // 2. Show Typing Indicator & Scroll
        showTypingIndicator();
        scrollToBottom();

        try {
            // 3. Request AI response from Flask backend
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: cleanText })
            });

            const data = await response.json();

            // 4. Hide typing indicator
            hideTypingIndicator();

            if (data.success || data.response) {
                appendBotMessage(data.response, data.suggestions || []);
                if (isTtsEnabled) {
                    speakText(data.response);
                }
            } else {
                appendBotMessage('Sorry, I encountered an issue. Please try again.', [
                    'Admission Process', 'Courses Offered', 'Contact Us'
                ]);
            }
        } catch (error) {
            console.error('Fetch error:', error);
            hideTypingIndicator();
            appendBotMessage(
                'Unable to connect to the college chatbot server. Please ensure the local server is running at http://127.0.0.1:5000.',
                ['Admission Process', 'Contact Us']
            );
        }

        scrollToBottom();
    }

    /**
     * Append user message bubble to chat window.
     */
    function appendUserMessage(text) {
        const row = document.createElement('div');
        row.className = 'message-row user-row';

        row.innerHTML = `
            <div class="avatar user-avatar">
                <i class="fa-solid fa-user"></i>
            </div>
            <div class="message-content">
                <div class="message-bubble user-bubble">
                    ${escapeHtml(text)}
                </div>
                <span class="timestamp">${getCurrentTime()}</span>
            </div>
        `;

        // Insert before typing indicator
        chatMessages.insertBefore(row, typingIndicator);
    }

    /**
     * Append chatbot message bubble with optional suggestions.
     */
    function appendBotMessage(text, suggestions = []) {
        const row = document.createElement('div');
        row.className = 'message-row bot-row';

        const formattedHtml = formatBotResponse(text);

        let suggestionsHtml = '';
        if (suggestions && suggestions.length > 0) {
            const buttons = suggestions.map(s => 
                `<button type="button" class="suggestion-btn" data-query="${escapeHtml(s)}">${escapeHtml(s)}</button>`
            ).join('');
            suggestionsHtml = `<div class="interactive-suggestions">${buttons}</div>`;
        }

        row.innerHTML = `
            <div class="avatar bot-avatar">
                <i class="fa-solid fa-robot"></i>
            </div>
            <div class="message-content">
                <div class="message-bubble bot-bubble">
                    ${formattedHtml}
                </div>
                ${suggestionsHtml}
                <span class="timestamp">${getCurrentTime()}</span>
            </div>
        `;

        // Insert before typing indicator
        chatMessages.insertBefore(row, typingIndicator);
    }

    /**
     * Format response string with line breaks and lists into HTML.
     */
    function formatBotResponse(text) {
        if (!text) return '';

        // Escape HTML
        let safe = escapeHtml(text);

        // Convert double newlines to paragraph tags, single newlines to <br>
        const lines = safe.split('\n');
        let formatted = '';
        let inList = false;

        lines.forEach(line => {
            const trimmed = line.trim();
            if (trimmed.startsWith('- ') || trimmed.startsWith('• ') || /^\d+\.\s/.test(trimmed)) {
                if (!inList) {
                    formatted += '<ul style="margin: 6px 0 6px 18px;">';
                    inList = true;
                }
                const cleanItem = trimmed.replace(/^[-•]\s*/, '').replace(/^\d+\.\s*/, '');
                formatted += `<li>${cleanItem}</li>`;
            } else {
                if (inList) {
                    formatted += '</ul>';
                    inList = false;
                }
                if (trimmed) {
                    formatted += `<p>${trimmed}</p>`;
                }
            }
        });

        if (inList) {
            formatted += '</ul>';
        }

        return formatted;
    }

    /**
     * Clear chat session and reset to initial welcome message.
     */
    function clearChatSession() {
        chatMessages.innerHTML = `
            <div class="message-row bot-row">
                <div class="avatar bot-avatar">
                    <i class="fa-solid fa-robot"></i>
                </div>
                <div class="message-content">
                    <div class="message-bubble bot-bubble">
                        <p><strong>Hello! 👋 Welcome back to Apex Institute Virtual Help Desk.</strong></p>
                        <p>How can I assist you with college admissions, courses, fees, or hostel facilities?</p>
                    </div>
                    <div class="interactive-suggestions">
                        <button type="button" class="suggestion-btn" data-query="What courses are offered?">Courses Offered</button>
                        <button type="button" class="suggestion-btn" data-query="What is the admission procedure?">Admission Process</button>
                        <button type="button" class="suggestion-btn" data-query="What is the fee for BCA?">Fee Structure</button>
                        <button type="button" class="suggestion-btn" data-query="What is the college helpline number?">Contact Us</button>
                    </div>
                    <span class="timestamp">${getCurrentTime()}</span>
                </div>
            </div>
            <div class="message-row bot-row typing-row" id="typingIndicator" style="display: none;">
                <div class="avatar bot-avatar">
                    <i class="fa-solid fa-robot"></i>
                </div>
                <div class="message-content">
                    <div class="message-bubble bot-bubble typing-bubble">
                        <span class="dot"></span>
                        <span class="dot"></span>
                        <span class="dot"></span>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Show loading typing indicator.
     */
    function showTypingIndicator() {
        const ind = document.getElementById('typingIndicator');
        if (ind) ind.style.display = 'flex';
    }

    /**
     * Hide loading typing indicator.
     */
    function hideTypingIndicator() {
        const ind = document.getElementById('typingIndicator');
        if (ind) ind.style.display = 'none';
    }

    /**
     * Smoothly scroll chat view to bottom.
     */
    function scrollToBottom() {
        chatMessages.scrollTo({
            top: chatMessages.scrollHeight,
            behavior: 'smooth'
        });
    }

    /**
     * Get current formatted time string (e.g. 10:45 AM).
     */
    function getCurrentTime() {
        const now = new Date();
        return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    /**
     * Convert text to spoken speech via Web Speech API.
     */
    function speakText(text) {
        if (!('speechSynthesis' in window)) return;
        window.speechSynthesis.cancel();
        // Remove markdown or bullet formatting for speech
        const cleanForSpeech = text.replace(/[*_#•-]/g, ' ');
        const utterance = new SpeechSynthesisUtterance(cleanForSpeech);
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        window.speechSynthesis.speak(utterance);
    }

    /**
     * Escape special HTML characters to prevent XSS.
     */
    function escapeHtml(string) {
        const div = document.createElement('div');
        div.textContent = string;
        return div.innerHTML;
    }
});

