// script.js

// Configuration
const API_CHAT_URL = "http://localhost:8001/api/advisor/query";

// Elements
const chatDisplay = document.getElementById('chatDisplay');
const userInput = document.getElementById('userInput');
const sendButton = document.getElementById('sendButton');
const departmentList = document.getElementById('departmentList');

// Language Toggle Elements
const languageToggle = document.getElementById('languageToggle');
const languageLabel = document.getElementById('languageLabel');
let currentLanguage = 'En'; // Default language is English

// Sidebar toggle elements
const sidebarToggle = document.getElementById('sidebarToggle');
const closeSidebarButton = document.getElementById('closeSidebar');
const sidebar = document.getElementById('sidebar');

// Reset button
const resetButton = document.getElementById('resetButton');

// Variables to store current advisor department
let currentDepartment = "MSFEA Advisor";
let currentDepartmentIcon = 'images/msfea_logo.png';

// Variable for the "Thinking..." animation
let thinkingInterval;

// At the top of your script, add a variable to track the return timeout
let returnToMsfeaTimeout;
let lastReturnTime = 0;

// Department data
const departments = [
    {
        id: 'msfea',
        name: 'MSFEA Advisor',
        icon: 'images/msfea_logo.png',
        description: 'General faculty information'
    },
    {
        id: 'chee', 
        name: 'Chemical Engineering',
        icon: 'images/department_icons/chemical.png',
        description: 'CHEE department'
    },
    {
        id: 'mech',
        name: 'Mechanical Engineering',
        icon: 'images/department_icons/mechanical.png',
        description: 'MECH department'
    },
    {
        id: 'cee',
        name: 'Civil Engineering',
        icon: 'images/department_icons/civil.png',
        description: 'CEE department'
    },
    {
        id: 'ece',
        name: 'Electrical & Computer',
        icon: 'images/department_icons/ece.png',
        description: 'ECE department'
    },
    {
        id: 'enmg',
        name: 'Industrial Engineering',
        icon: 'images/department_icons/industrial.png',
        description: 'ENMG department'
    }
];

// Department mapping to ensure consistent naming
const departmentMap = {
    "MSFEA Advisor": { 
        name: "MSFEA Advisor", 
        icon: 'images/msfea_logo.png',
        displayName: "MSFEA Advisor" 
    },
    "Chemical Engineering": { 
        name: "Chemical Engineering", 
        icon: 'images/department_icons/chemical.png',
        displayName: "Chemical Engineering"
    },
    "Mechanical Engineering": { 
        name: "Mechanical Engineering", 
        icon: 'images/department_icons/mechanical.png',
        displayName: "Mechanical Engineering"
    },
    "Civil Engineering": { 
        name: "Civil Engineering", 
        icon: 'images/department_icons/civil.png',
        displayName: "Civil Engineering"
    },
    "Electrical & Computer": { 
        name: "Electrical & Computer", 
        icon: 'images/department_icons/ece.png',
        displayName: "Electrical & Computer"
    },
    "Computer Science Engineering": { 
        name: "Computer Science Engineering", 
        icon: 'images/department_icons/ece.png',
        displayName: "CSE"
    },
    "Computer & Communications Engineering": { 
        name: "Computer & Communications Engineering", 
        icon: 'images/department_icons/ece.png',
        displayName: "CCE"
    },
    "Industrial Engineering": { 
        name: "Industrial Engineering", 
        icon: 'images/department_icons/industrial.png',
        displayName: "Industrial Engineering"
    }
};

// Initial Chat State
let messages = [
    { 
        role: "bot", 
        content: "Hello! How can I assist you with your academic inquiries today?", 
        department: currentDepartment, 
        departmentIcon: currentDepartmentIcon 
    }
];

// Load chat history from localStorage if available
const savedMessages = localStorage.getItem('msfeaAdvisorMessages');
if (savedMessages) {
    try {
        const parsedMessages = JSON.parse(savedMessages);
        if (Array.isArray(parsedMessages) && parsedMessages.length > 0) {
            messages = parsedMessages;
        }
    } catch (e) {
        console.error('Error parsing saved messages:', e);
    }
}

// Save messages to localStorage whenever they change
function saveMessagesToLocalStorage() {
    localStorage.setItem('msfeaAdvisorMessages', JSON.stringify(messages));
}

// Function to populate department list
function populateDepartmentList() {
    // Clear existing departments
    departmentList.innerHTML = '';
    
    // Add each department as a non-interactive element
    departments.forEach(dept => {
        const deptElement = document.createElement('div');
        
        // Apply active class if this is the current department
        const isActive = dept.name === currentDepartment;
        deptElement.className = 'department-item' + (isActive ? ' active-department' : '');
        
        console.log(`Department: ${dept.name}, Current: ${currentDepartment}, Active: ${isActive}`);
        
        // Create department content with icon and name
        deptElement.innerHTML = `
            <img src="${dept.icon}" alt="${dept.name}" class="department-icon">
            <div class="department-details">
                <div class="department-name">${dept.name}</div>
                <div class="department-desc">${dept.description}</div>
            </div>
        `;
        
        // Add to the list
        departmentList.appendChild(deptElement);
    });
}

// Function to sanitize user input to prevent XSS
function sanitize(str) {
    const temp = document.createElement('div');
    temp.textContent = str;
    return temp.innerHTML;
}

// Added function to format markdown bold text
function formatMarkdown(str) {
    return str.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');
}

// Function to render messages
function renderMessages() {
    chatDisplay.innerHTML = '';
    
    // Add welcome message with suggested questions if no messages
    if (messages.length === 1 && messages[0].role === "bot") {
        const welcomeContainer = document.createElement('div');
        welcomeContainer.className = 'welcome-suggestions';
        welcomeContainer.innerHTML = `
            <h3>Welcome to MSFEA Academic Advisor</h3>
            <p>Here are some questions you can ask:</p>
            <div class="suggestion-buttons">
                <button onclick="askSuggestedQuestion('What majors are offered at MSFEA?')">What majors are offered at MSFEA?</button>
                <button onclick="askSuggestedQuestion('How can I declare my major?')">How can I declare my major?</button>
                <button onclick="askSuggestedQuestion('What are the graduation requirements for ECE?')">What are the graduation requirements for ECE?</button>
                <button onclick="askSuggestedQuestion('What electives are available for my department?')">What electives are available for my department?</button>
            </div>
        `;
        chatDisplay.appendChild(welcomeContainer);
    }
    
    messages.forEach(message => {
        if (message.isNotification) {
            // Render a notification message
            const notificationDiv = document.createElement('div');
            notificationDiv.className = 'notification-message';
            notificationDiv.textContent = message.content;
            chatDisplay.appendChild(notificationDiv);
        } else if (message.isSystem) {
            // System Message (department change) - NEW STYLING
            const systemContainer = document.createElement('div');
            systemContainer.className = 'system-message';
            
            // Style it properly
            systemContainer.style.textAlign = 'center';
            systemContainer.style.color = '#a7c7f7';
            systemContainer.style.backgroundColor = 'rgba(30, 30, 50, 0.5)';
            systemContainer.style.padding = '8px 15px';
            systemContainer.style.margin = '12px auto';
            systemContainer.style.borderRadius = '10px';
            systemContainer.style.fontSize = '0.9em';
            systemContainer.style.maxWidth = '70%';
            systemContainer.style.boxShadow = '0 1px 2px rgba(0,0,0,0.2)';
            
            systemContainer.textContent = message.content;
            chatDisplay.appendChild(systemContainer);
        } else if (message.role === "user") {
            // User Message
            const userContainer = document.createElement('div');
            userContainer.className = 'chat-container user-chat-container';
            
            const chatContent = document.createElement('div');
            chatContent.className = 'chat-content user-bubble chat-bubble';
            chatContent.innerHTML = `<span class="sender-label">You:</span> <span class="message-text">${formatMarkdown(sanitize(message.content))}</span>`;
            
            const userIcon = document.createElement('img');
            userIcon.src = 'images/user_icon.png';
            userIcon.alt = 'User';
            userIcon.className = 'message-icon';
            
            userContainer.appendChild(chatContent);
            userContainer.appendChild(userIcon);
            chatDisplay.appendChild(userContainer);
        } else {
            // Bot/Advisor Message
            const botContainer = document.createElement('div');
            botContainer.className = 'chat-container bot-chat-container';
            
            if (message.isThinking) {
                botContainer.setAttribute('data-is-thinking', 'true');
            }
            
            const botIcon = document.createElement('img');
            botIcon.src = message.departmentIcon || currentDepartmentIcon;
            botIcon.alt = 'Advisor';
            botIcon.className = 'message-icon';
            
            const chatContent = document.createElement('div');
            chatContent.className = 'chat-content bot-bubble chat-bubble';
            
            const senderName = message.department || "MSFEA Advisor";
            
            // Create a custom label for debugging
            console.log(`Rendering message with department: ${senderName}`);
            
            // Directly add a new span for the sender label
            const senderLabel = document.createElement('span');
            senderLabel.className = 'sender-label';
            senderLabel.textContent = `${senderName}:`;
            
            const messageText = document.createElement('span');
            messageText.className = 'message-text';
            messageText.innerHTML = formatMarkdown(sanitize(message.content)).replace(/\n/g, '<br>');
            
            chatContent.appendChild(senderLabel);
            chatContent.appendChild(messageText);
            
            botContainer.appendChild(botIcon);
            botContainer.appendChild(chatContent);
            chatDisplay.appendChild(botContainer);
        }
    });
    
    // Automatically scroll to the bottom after rendering messages
    scrollToBottom();
    
    // Save messages to localStorage whenever they change
    saveMessagesToLocalStorage();
}

// Create a mapping for detecting departments from keywords
const departmentKeywords = {
    "mechanical": "Mechanical Engineering",
    "mech": "Mechanical Engineering",
    "civil": "Civil Engineering",
    "cee": "Civil Engineering",
    "electrical": "Electrical & Computer Engineering",
    "ece": "Electrical & Computer",
    "computer": "Electrical & Computer",
    "chemical": "Chemical Engineering",
    "chee": "Chemical Engineering",
    "industrial": "Industrial Engineering",
    "enmg": "Industrial Engineering",
    "cse": "Computer Science and Engineering",
    "cce": "Computer and Communications Engineering"
};

// Function to send user message using Fetch API
async function sendMessage() {
    const userText = userInput.value.trim();
    
    if (userText === "") {
        return;
    }
    
    // Append user message to chat display
    messages.push({ role: "user", content: userText });
    renderMessages();
    
    // Clear input
    userInput.value = "";
    
    // Show "Thinking..." animation
    showThinkingAnimation();
    
    try {
        // Add delay to ensure thinking animation is visible (even with quick responses)
        const delayPromise = new Promise(resolve => setTimeout(resolve, 500));
        
        const fetchPromise = fetch(API_CHAT_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                text: userText,
                language: currentLanguage.toLowerCase() === 'ar' ? 'arabic' : 'english'
            })
        });
        
        // Wait for both the delay and the fetch to complete
        await delayPromise;
        const response = await fetchPromise;
        
        if (response.ok) {
            const data = await response.json();
            console.log("API Response:", data);
            
            // Stop the "Thinking..." animation
            stopThinkingAnimation();
            messages.pop();
            
            // Initialize with default department
            let responseDepartment = "MSFEA Advisor";
            
            // IMPROVED DEPARTMENT DETECTION
            // 1. First try to get it from the API response
            if (data.department && data.department !== "MSFEA Advisor") {
                responseDepartment = data.department;
                console.log("Using department from API:", responseDepartment);
            } 
            // 2. Then try to detect it from the user's query
            else {
                const query = userText.toLowerCase();
                for (const keyword in departmentKeywords) {
                    if (query.includes(keyword)) {
                        responseDepartment = departmentKeywords[keyword];
                        console.log("Detected department from query:", responseDepartment);
                        break;
                    }
                }
            }
            
            // Set current department for sidebar highlighting
            if (responseDepartment !== "MSFEA Advisor") {
                // Update current department variable - THIS IS KEY FOR SIDEBAR
                currentDepartment = responseDepartment;
                
                // Find the matching department icon
                const deptObj = departments.find(d => d.name === responseDepartment);
                currentDepartmentIcon = deptObj ? deptObj.icon : 'images/msfea_logo.png';
                
                // Update the sidebar to highlight current department
                populateDepartmentList();
                console.log("Updated sidebar with active department:", currentDepartment);
            }
            
            // Force ALL bot messages to use the detected department
            const botMessage = {
                role: "bot",
                content: data.content || "No content available",
                department: responseDepartment,
                departmentIcon: 'images/department_icons/' + 
                               (responseDepartment === "MSFEA Advisor" ? 
                                "msfea_logo.png" : responseDepartment.toLowerCase().replace(/ /g, "_") + ".png")
            };
            
            console.log("Created message with department:", botMessage.department);
            messages.push(botMessage);
            
            // Add department switching notification if needed
            if (responseDepartment !== "MSFEA Advisor") {
                // Insert system message BEFORE the bot response
                messages.splice(messages.length-1, 0, {
                    role: "system",
                    isSystem: true,
                    content: `→ Switched to ${responseDepartment} advisor`
                });
            }
            
            // Render all messages
            renderMessages();
            
            // Return to MSFEA Advisor after delay if switched
            if (responseDepartment !== "MSFEA Advisor") {
                // Clear any existing timeout
                if (returnToMsfeaTimeout) {
                    clearTimeout(returnToMsfeaTimeout);
                    returnToMsfeaTimeout = null;
                }
                
                // Set the new timeout
                returnToMsfeaTimeout = setTimeout(() => {
                    // Prevent duplicate return messages within 5 seconds
                    const now = Date.now();
                    if (now - lastReturnTime < 5000) {
                        console.log("Skipping duplicate return message");
                        return;
                    }
                    
                    // Track when we added a return message
                    lastReturnTime = now;
                    
                    // Remove any existing return messages first
                    messages = messages.filter(msg => 
                        !(msg.isSystem && msg.content.includes("Returned to MSFEA"))
                    );
                    
                    // Add the return message
                    messages.push({
                        role: "system",
                        isSystem: true,
                        content: `← Returned to MSFEA Advisor`
                    });
                    
                    currentDepartment = "MSFEA Advisor";
                    currentDepartmentIcon = departments.find(d => d.name === "MSFEA Advisor")?.icon || 'images/msfea_logo.png';
                    
                    populateDepartmentList();
                    renderMessages();
                }, 2000);
            }
        } else {
            handleApiError("The server returned an error.");
        }
    } catch (error) {
        handleApiError("Could not connect to the advisor service.");
    }
}

// Function to handle API errors
function handleApiError(errorMsg) {
    console.error("API Error:", errorMsg);
    stopThinkingAnimation();
    messages.pop();
    
    let errorContent;
    if (errorMsg.includes("connect")) {
        errorContent = "Could not connect to the advisor service. Please check your internet connection and try again.";
    } else {
        errorContent = `The server returned an error. Please try again. If the problem persists, try a different question or contact technical support.`;
    }
    
    messages.push({
        role: "bot",
        content: errorContent,
        department: currentDepartment,
        departmentIcon: currentDepartmentIcon
    });
    renderMessages();
}

// Function to start "Thinking..." live animation
function showThinkingAnimation() {
    let dots = 0;
    const thinkingMessage = {
        role: "bot",
        content: "Thinking...",
        department: currentDepartment,
        departmentIcon: currentDepartmentIcon,
        isThinking: true
    };
    messages.push(thinkingMessage);
    renderMessages();
    
    thinkingInterval = setInterval(() => {
        dots = (dots + 1) % 4;
        thinkingMessage.content = "Thinking" + ".".repeat(dots);
        
        // Update just the thinking message content
        const thinkingElement = document.querySelector('[data-is-thinking="true"] .message-text');
        if (thinkingElement) {
            thinkingElement.innerHTML = sanitize(thinkingMessage.content).replace(/\n/g, '<br>');
        }
    }, 500);
}

// Function to stop the "Thinking..." animation
function stopThinkingAnimation() {
    if (thinkingInterval) {
        clearInterval(thinkingInterval);
        thinkingInterval = null;
    }
}

// Function to reset chatbot
function resetChatbot() {
    // Reset to initial state
    messages = [
        { 
            role: "bot", 
            content: "Hello! How can I assist you with your academic inquiries today?", 
            department: "MSFEA Advisor", 
            departmentIcon: 'images/msfea_logo.png' 
        }
    ];
    currentDepartment = "MSFEA Advisor";
    currentDepartmentIcon = 'images/msfea_logo.png';
    
    // Update UI
    renderMessages();
    populateDepartmentList();
    
    // Optionally send reset signal to backend
    fetch(API_CHAT_URL, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ reset: true })
    }).catch(err => console.error('Error resetting chat:', err));
}

// Scroll the chat to the bottom
function scrollToBottom() {
    chatDisplay.scrollTop = chatDisplay.scrollHeight;
}

// Function to toggle sidebar and button visibility
function toggleSidebar() {
    sidebar.classList.toggle('closed');
    
    // Show/hide sidebar toggle buttons based on sidebar state
    if (sidebar.classList.contains('closed')) {
        sidebarToggle.style.display = 'block';
        closeSidebarButton.style.display = 'none';
    } else {
        sidebarToggle.style.display = 'none';
        closeSidebarButton.style.display = 'block';
    }
}

// Event listeners
sendButton.addEventListener('click', sendMessage);
resetButton.addEventListener('click', resetChatbot);
sidebarToggle.addEventListener('click', toggleSidebar);
closeSidebarButton.addEventListener('click', toggleSidebar);

// Allow sending message by pressing Enter key
userInput.addEventListener('keypress', function(event) {
    if (event.key === 'Enter') {
        event.preventDefault();
        sendMessage();
    }
});

// Event listener for language toggle button
languageToggle.addEventListener('click', function() {
    if (currentLanguage === 'En') {
        currentLanguage = 'Ar';
    } else {
        currentLanguage = 'En';
    }
    languageLabel.textContent = currentLanguage;
    
    // Update the lang attribute on the body element
    document.body.setAttribute('lang', currentLanguage === 'Ar' ? 'ar' : 'en');
    
    // Update text direction based on language
    if (currentLanguage === 'Ar') {
        document.body.style.direction = 'rtl'; // Right-to-left for Arabic
    } else {
        document.body.style.direction = 'ltr'; // Left-to-right for English
    }
});

// Initialize
populateDepartmentList();
renderMessages();

// Hide the sidebar toggle initially (when sidebar is open)
sidebarToggle.style.display = 'none';

// Add this function after sendMessage
function askSuggestedQuestion(question) {
    userInput.value = question;
    sendMessage();
}

// Add to script.js
document.addEventListener('keydown', function(event) {
    // Press Ctrl+/ to focus on input
    if (event.ctrlKey && event.key === '/') {
        event.preventDefault();
        userInput.focus();
    }
});

// Add to beginning of script.js
window.addEventListener('load', function() {
    // Remove any loading indicators or splash screens if needed
    const loadingScreen = document.getElementById('loadingScreen');
    if (loadingScreen) {
        loadingScreen.style.opacity = '0';
        setTimeout(() => {
            loadingScreen.style.display = 'none';
        }, 500);
    }
});

// Handle missing images gracefully
document.addEventListener('error', function(e) {
    if (e.target.tagName.toLowerCase() === 'img') {
        // Replace broken department icons with a fallback
        if (e.target.classList.contains('department-icon')) {
            e.target.src = 'images/msfea_logo.png'; // Fallback to main logo
        }
        // Replace broken message icons with a fallback
        else if (e.target.classList.contains('message-icon')) {
            e.target.src = 'images/advisor_icon.png'; // Fallback to advisor icon
        }
        // Replace other broken images
        else {
            e.target.style.display = 'none'; // Hide broken images
        }
    }
}, true);
