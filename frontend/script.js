// Global variables
let isReadingAloud = false;
let currentStoryArc = null;
let originalStoryText = '';
const API_BASE_URL = 'http://localhost:8000'; // Backend API URL

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    const userInput = document.getElementById('userInput');
    
    // Allow Enter key to send message
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    // Focus on input field
    userInput.focus();
});

// Send message function - Now acts as a router
async function sendMessage() {
    const userInput = document.getElementById('userInput');
    const message = userInput.value.trim();
    if (!message) return;

    userInput.value = '';
    addMessage(message, 'user');
    showLoading();

    if (currentStoryArc && originalStoryText) {
        // If we have a story, we refine it
        await refineStory(message);
    } else {
        // Otherwise, we create a new one
        await generateNewStory(message);
    }
}

// NEW: Function to generate a new story
async function generateNewStory(message) {
    try {
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message })
        });

        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        const data = await response.json();
        hideLoading();
        addMessage(data.response, 'storyteller');

        // *** Store the state for potential refinement ***
        currentStoryArc = data.story_arc;
        originalStoryText = data.response;

        if (isReadingAloud) {
            speakText(data.response);
        }

    } catch (error) {
        console.error('Error generating new story:', error);
        hideLoading();
        addMessage("Oops! My crystal ball is a bit foggy. I couldn't create a new story. Please try again.", 'storyteller');
    }
}

// NEW: Function to refine an existing story
async function refineStory(feedback) {
    if (!currentStoryArc || !originalStoryText) {
        addMessage("There's no story to refine. Let's create one first!", 'storyteller');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/refine-with-feedback`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_feedback: feedback,
                original_story: originalStoryText,
                story_arc: currentStoryArc
            })
        });

        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

        const data = await response.json();
        hideLoading();
        addMessage(data.response, 'storyteller');
        
        // *** Update the state with the refined story ***
        originalStoryText = data.response;
        // The arc might change in future implementations, so we update it
        if (data.story_arc) {
            currentStoryArc = data.story_arc;
        }


        if (isReadingAloud) {
            speakText(data.response);
        }

    } catch (error) {
        console.error('Error refining story:', error);
        hideLoading();
        addMessage("I tried to weave your idea into the tale, but my thread broke! Let's try another change.", 'storyteller');
    }
}

// Quick story buttons
function quickStory(type) {
    const storyPrompts = {
        adventure: "Tell me an exciting adventure story!",
        animals: "I want to hear a story about animals!",
        magic: "Can you tell me a magical story?",
        space: "Tell me a story about space and rockets!"
    };
    
    const userInput = document.getElementById('userInput');
    userInput.value = storyPrompts[type];
    sendMessage();
}

// Add message to chat display
function addMessage(message, sender) {
    const storyDisplay = document.getElementById('storyDisplay');
    
    // Remove welcome message if it exists
    const welcomeMessage = storyDisplay.querySelector('.welcome-message');
    if (welcomeMessage && sender === 'user') {
        welcomeMessage.remove();
    }
    
    const messageGroup = document.createElement('div');
    messageGroup.className = 'message-group';
    
    if (sender === 'storyteller') {
        messageGroup.innerHTML = `
            <div class="storyteller-avatar">🧙‍♂️</div>
            <div class="message-bubble storyteller">
                <p>${formatMessage(message)}</p>
            </div>
        `;
    } else {
        messageGroup.innerHTML = `
            <div class="user-avatar">👦</div>
            <div class="message-bubble user">
                <p>${formatMessage(message)}</p>
            </div>
        `;
    }
    
    storyDisplay.appendChild(messageGroup);
    storyDisplay.scrollTop = storyDisplay.scrollHeight;
}

// Format message with emojis and line breaks
function formatMessage(message) {
    return message
        .replace(/\n/g, '</p><p>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>');
}

// Show loading animation
function showLoading() {
    const storyDisplay = document.getElementById('storyDisplay');
    const loadingDiv = document.createElement('div');
    loadingDiv.id = 'loadingMessage';
    loadingDiv.className = 'message-group';
    loadingDiv.innerHTML = `
        <div class="storyteller-avatar">🧙‍♂️</div>
        <div class="message-bubble storyteller">
            <div class="loading">
                <span>Creating your story</span>
                <div class="loading-dot"></div>
                <div class="loading-dot"></div>
                <div class="loading-dot"></div>
            </div>
        </div>
    `;
    
    storyDisplay.appendChild(loadingDiv);
    storyDisplay.scrollTop = storyDisplay.scrollHeight;
}

// Hide loading animation
function hideLoading() {
    const loadingMessage = document.getElementById('loadingMessage');
    if (loadingMessage) {
        loadingMessage.remove();
    }
}

// Update newStory function to clear state
function newStory() {
    const storyDisplay = document.getElementById('storyDisplay');
    storyDisplay.innerHTML = `
        <div class="welcome-message">
            <div class="storyteller-avatar">🧙‍♂️</div>
            <div class="message-bubble storyteller">
                <p>Hello there, young adventurer! 👋</p>
                <p>I'm ready for a brand new magical story! What adventure should we create together today?</p>
            </div>
        </div>
    `;

    // *** Reset the story state ***
    currentStoryArc = null;
    originalStoryText = '';
    
    if (isReadingAloud) {
        speechSynthesis.cancel();
    }
    document.getElementById('userInput').focus();
}

// Text-to-speech functionality
function toggleReadAloud() {
    const button = document.getElementById('readAloudBtn');
    
    if (isReadingAloud) {
        isReadingAloud = false;
        speechSynthesis.cancel();
        button.textContent = '🔊 Read Aloud';
        button.style.background = 'linear-gradient(135deg, #a29bfe 0%, #6c5ce7 100%)';
    } else {
        isReadingAloud = true;
        button.textContent = '🔇 Stop Reading';
        button.style.background = 'linear-gradient(135deg, #fd79a8 0%, #e84393 100%)';
    }
}

// Speak text function
function speakText(text) {
    if ('speechSynthesis' in window) {
        speechSynthesis.cancel(); // Cancel any ongoing speech
        
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 0.8; // Slower rate for children
        utterance.pitch = 1.1; // Slightly higher pitch
        utterance.volume = 0.8;
        
        // Try to use a child-friendly voice
        const voices = speechSynthesis.getVoices();
        const childFriendlyVoice = voices.find(voice => 
            voice.name.includes('female') || 
            voice.name.includes('Google UK English Female') ||
            voice.name.includes('Karen') ||
            voice.name.includes('Zira')
        );
        
        if (childFriendlyVoice) {
            utterance.voice = childFriendlyVoice;
        }
        
        speechSynthesis.speak(utterance);
    } else {
        console.log('Speech synthesis not supported');
    }
}

// Load voices when available
speechSynthesis.addEventListener('voiceschanged', function() {
    // Voices are now loaded
});

// Fun animations on click
document.addEventListener('click', function(e) {
    if (e.target.matches('button')) {
        e.target.style.transform = 'scale(0.95)';
        setTimeout(() => {
            e.target.style.transform = '';
        }, 150);
    }
});

// Add some sparkle effects for fun
function createSparkle(x, y) {
    const sparkle = document.createElement('div');
    sparkle.style.position = 'fixed';
    sparkle.style.left = x + 'px';
    sparkle.style.top = y + 'px';
    sparkle.style.pointerEvents = 'none';
    sparkle.style.fontSize = '20px';
    sparkle.style.zIndex = '1000';
    sparkle.textContent = '✨';
    sparkle.style.animation = 'sparkleAnimation 1s ease-out forwards';
    
    document.body.appendChild(sparkle);
    
    setTimeout(() => {
        sparkle.remove();
    }, 1000);
}

// Add sparkle animation CSS
const sparkleCSS = `
@keyframes sparkleAnimation {
    0% {
        opacity: 1;
        transform: scale(0) rotate(0deg);
    }
    50% {
        opacity: 1;
        transform: scale(1) rotate(180deg);
    }
    100% {
        opacity: 0;
        transform: scale(0) rotate(360deg);
    }
}
`;

const style = document.createElement('style');
style.textContent = sparkleCSS;
document.head.appendChild(style);

// Add sparkles on button clicks
document.addEventListener('click', function(e) {
    if (e.target.matches('button') || e.target.matches('.quick-btn')) {
        const rect = e.target.getBoundingClientRect();
        const x = rect.left + rect.width / 2;
        const y = rect.top + rect.height / 2;
        createSparkle(x, y);
    }
}); 