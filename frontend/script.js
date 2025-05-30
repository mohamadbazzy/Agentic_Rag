// script.js

// Configuration
const API_CHAT_URL = "http://localhost:8000/api/advisor/query";

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
const header = document.querySelector('.aub-header');

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

// Session ID for conversation persistence
let sessionId = localStorage.getItem('msfeaAdvisorSessionId') || null;

// Load chat history from localStorage if no session ID
if (!sessionId) {
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
}

// Save messages to localStorage whenever they change
function saveMessagesToLocalStorage() {
    // Only save to localStorage if we don't have a session ID
    if (!sessionId) {
        localStorage.setItem('msfeaAdvisorMessages', JSON.stringify(messages));
    }
}

// Save session ID to localStorage
function saveSessionId(id) {
    if (id) {
        sessionId = id;
        localStorage.setItem('msfeaAdvisorSessionId', id);
    }
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

// Function to check for and extract schedule JSON from a message
function extractScheduleData(content) {
    // Look for JSON data in the message between ```json and ```
    const jsonMatch = content.match(/```json\s*(\{[\s\S]*?\})\s*```/);
    if (jsonMatch && jsonMatch[1]) {
        try {
            const scheduleData = JSON.parse(jsonMatch[1]);
            if (scheduleData && scheduleData.is_schedule === true) {
                return scheduleData;
            }
        } catch (e) {
            console.error('Failed to parse schedule JSON:', e);
        }
    }
    return null;
}

// Function to generate schedule template with a more visible calendar button
function generateScheduleTemplate(scheduleData) {
    if (!scheduleData || !scheduleData.schedule || !scheduleData.schedule.length) {
        return null;
    }

    // Create schedule container
    const scheduleContainer = document.createElement('div');
    scheduleContainer.className = 'schedule-container';

    // Create schedule header with toggle buttons
    const scheduleHeader = document.createElement('div');
    scheduleHeader.className = 'schedule-header';
    scheduleHeader.innerHTML = '<h3>Course Schedule</h3>';
    
    // Add view toggle buttons
    const toggleContainer = document.createElement('div');
    toggleContainer.className = 'schedule-toggle-container';
    
    const listViewBtn = document.createElement('button');
    listViewBtn.className = 'schedule-toggle-btn active';
    listViewBtn.innerHTML = '<i class="fas fa-list"></i> List View';
    listViewBtn.onclick = () => toggleScheduleView(scheduleContainer, 'list');
    
    const weekViewBtn = document.createElement('button');
    weekViewBtn.className = 'schedule-toggle-btn';
    weekViewBtn.innerHTML = '<i class="fas fa-calendar-week"></i> Week View';
    weekViewBtn.onclick = () => toggleScheduleView(scheduleContainer, 'week');
    
    toggleContainer.appendChild(listViewBtn);
    toggleContainer.appendChild(weekViewBtn);
    scheduleHeader.appendChild(toggleContainer);
    scheduleContainer.appendChild(scheduleHeader);

    // Create list view container
    const listViewContainer = document.createElement('div');
    listViewContainer.className = 'schedule-view list-view active';
    
    // Create the list view table
    const scheduleTable = document.createElement('table');
    scheduleTable.className = 'schedule-table';

    // Create table header
    const tableHeader = document.createElement('thead');
    tableHeader.innerHTML = `
        <tr>
            <th>Course</th>
            <th>Section</th>
            <th>Days</th>
            <th>Time</th>
            <th>Location</th>
            <th>Instructor</th>
        </tr>
    `;
    scheduleTable.appendChild(tableHeader);

    // Create table body
    const tableBody = document.createElement('tbody');
    
    // Add courses to the table
    scheduleData.schedule.forEach(course => {
        course.meetings.forEach((meeting, index) => {
            const row = document.createElement('tr');
            
            // Only show course code and section in first row of multiple meetings
            if (index === 0) {
                row.innerHTML = `
                    <td rowspan="${course.meetings.length}">${course.course_code}</td>
                    <td rowspan="${course.meetings.length}">${course.section}</td>
                    <td>${meeting.days.join(', ')}</td>
                    <td>${meeting.start_time} - ${meeting.end_time}</td>
                    <td>${meeting.location || 'TBA'}</td>
                    <td rowspan="${course.meetings.length}">${course.instructor || 'TBA'}</td>
                `;
            } else {
                row.innerHTML = `
                    <td>${meeting.days.join(', ')}</td>
                    <td>${meeting.start_time} - ${meeting.end_time}</td>
                    <td>${meeting.location || 'TBA'}</td>
                `;
            }
            
            tableBody.appendChild(row);
        });
    });
    
    scheduleTable.appendChild(tableBody);
    listViewContainer.appendChild(scheduleTable);
    scheduleContainer.appendChild(listViewContainer);
    
    // Create week view container
    const weekViewContainer = document.createElement('div');
    weekViewContainer.className = 'schedule-view week-view';
    
    // Create the weekly timetable
    const timetable = generateWeeklyTimetable(scheduleData);
    weekViewContainer.appendChild(timetable);
    scheduleContainer.appendChild(weekViewContainer);

    // Add download and calendar buttons
    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'download-buttons';
    
    const downloadListBtn = document.createElement('button');
    downloadListBtn.className = 'download-schedule-btn';
    downloadListBtn.innerHTML = '<i class="fas fa-download"></i> Download List View';
    downloadListBtn.onclick = () => {
        toggleScheduleView(scheduleContainer, 'list');
        setTimeout(() => {
            downloadScheduleAsImage(listViewContainer, 'schedule-list-view');
        }, 100);
    };

    const downloadWeekBtn = document.createElement('button');
    downloadWeekBtn.className = 'download-schedule-btn';
    downloadWeekBtn.innerHTML = '<i class="fas fa-download"></i> Download Week View';
    downloadWeekBtn.onclick = () => {
        toggleScheduleView(scheduleContainer, 'week');
        setTimeout(() => {
            downloadScheduleAsImage(weekViewContainer, 'schedule-week-view');
        }, 100);
    };
    
    // Add a prominent calendar button at the top
    const calendarButtonTop = document.createElement('div');
    calendarButtonTop.className = 'calendar-button-container';
    calendarButtonTop.style.margin = '10px 0';
    calendarButtonTop.style.textAlign = 'center';
    
    const googleBtn = document.createElement('button');
    googleBtn.className = 'calendar-btn google-btn';
    googleBtn.style.backgroundColor = '#8A0635'; // AUB maroon color
    googleBtn.style.color = 'white';
    googleBtn.style.border = 'none';
    googleBtn.style.borderRadius = '4px';
    googleBtn.style.padding = '10px 20px';
    googleBtn.style.fontSize = '16px';
    googleBtn.style.cursor = 'pointer';
    googleBtn.style.fontWeight = '500';
    googleBtn.style.boxShadow = '0 2px 4px rgba(0,0,0,0.2)';
    googleBtn.style.transition = 'all 0.2s ease';
    googleBtn.innerHTML = '<i class="far fa-calendar-alt"></i> Add to Google Calendar';
    
    // Add hover effect
    googleBtn.onmouseover = function() {
        this.style.backgroundColor = '#6d052a'; // Darker maroon on hover
        this.style.boxShadow = '0 4px 8px rgba(0,0,0,0.3)';
    };
    googleBtn.onmouseout = function() {
        this.style.backgroundColor = '#8A0635';
        this.style.boxShadow = '0 2px 4px rgba(0,0,0,0.2)';
    };
    
    googleBtn.onclick = () => addToGoogleCalendar(scheduleData);
    
    calendarButtonTop.appendChild(googleBtn);
    
    // Add the calendar button right after the header
    scheduleContainer.insertBefore(calendarButtonTop, scheduleContainer.childNodes[1]);

    return scheduleContainer;
}

// Function to add schedule to Google Calendar
function addToGoogleCalendar(scheduleData) {
    console.log("Adding schedule to Google Calendar:", scheduleData);
    
    if (!scheduleData || !scheduleData.schedule || !scheduleData.schedule.length) {
        alert('No schedule data available to add to calendar');
        return;
    }
    
    // Directly generate calendar links without showing options
    generateGoogleCalendarLinks(scheduleData);
}

// Function to generate and open a full schedule link
async function generateFullScheduleLink(scheduleData) {
    try {
        // Show loading state
        const loadingModal = document.createElement('div');
        loadingModal.className = 'loading-modal';
        loadingModal.style.position = 'fixed';
        loadingModal.style.top = '0';
        loadingModal.style.left = '0';
        loadingModal.style.right = '0';
        loadingModal.style.bottom = '0';
        loadingModal.style.backgroundColor = 'rgba(0,0,0,0.7)';
        loadingModal.style.zIndex = '1000';
        loadingModal.style.display = 'flex';
        loadingModal.style.alignItems = 'center';
        loadingModal.style.justifyContent = 'center';
        
        const loadingContent = document.createElement('div');
        loadingContent.style.backgroundColor = 'white';
        loadingContent.style.borderRadius = '8px';
        loadingContent.style.padding = '20px';
        loadingContent.style.textAlign = 'center';
        loadingContent.innerHTML = `
            <h3>Generating Calendar Link...</h3>
            <div class="spinner" style="margin: 10px auto; border: 4px solid #f3f3f3; border-top: 4px solid #3498db; border-radius: 50%; width: 30px; height: 30px; animation: spin 2s linear infinite;"></div>
        `;
        
        // Add the spinner animation style
        const style = document.createElement('style');
        style.textContent = '@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }';
        document.head.appendChild(style);
        
        loadingModal.appendChild(loadingContent);
        document.body.appendChild(loadingModal);
        
        // Call the backend to generate the all-in-one link
        const response = await fetch('/api/gcalendar/generate-all-link', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                schedule_data: scheduleData
            })
        });
        
        // Remove loading modal
        document.body.removeChild(loadingModal);
        
        if (!response.ok) {
            throw new Error('Failed to generate calendar link');
        }
        
        const result = await response.json();
        
        if (result.status === 'success' && result.link) {
            // Open the link in a new tab
            window.open(result.link, '_blank');
            
            // Show a modal with next steps information
            const infoModal = document.createElement('div');
            infoModal.className = 'info-modal';
            infoModal.style.position = 'fixed';
            infoModal.style.top = '0';
            infoModal.style.left = '0';
            infoModal.style.right = '0';
            infoModal.style.bottom = '0';
            infoModal.style.backgroundColor = 'rgba(0,0,0,0.7)';
            infoModal.style.zIndex = '1000';
            infoModal.style.display = 'flex';
            infoModal.style.alignItems = 'center';
            infoModal.style.justifyContent = 'center';
            
            const infoContent = document.createElement('div');
            infoContent.style.backgroundColor = 'white';
            infoContent.style.borderRadius = '8px';
            infoContent.style.padding = '20px';
            infoContent.style.maxWidth = '500px';
            infoContent.style.width = '90%';
            
            infoContent.innerHTML = `
                <h3>Calendar Event Created</h3>
                <p>A complete overview of your schedule has been created in a new tab.</p>
                <p>This summary event includes all your class details. Google Calendar shows one event at a time, so we've created a summary with all your schedule information.</p>
                <p>If you want to add individual class sessions as separate events instead, use the "Get Calendar Links" option.</p>
                <button id="close-info-btn" style="margin-top: 15px; padding: 8px 16px; background-color: #8A0635; color: white; border: none; border-radius: 4px; cursor: pointer; width: 100%;">Close</button>
            `;
            
            infoModal.appendChild(infoContent);
            document.body.appendChild(infoModal);
            
            // Add event listener to close button
            document.getElementById('close-info-btn').addEventListener('click', () => {
                document.body.removeChild(infoModal);
            });
        } else {
            alert('Failed to generate a calendar link for your schedule.');
        }
    } catch (error) {
        console.error('Error generating full schedule link:', error);
        alert('Error generating Google Calendar link');
    }
}

// Start Google OAuth authentication flow
function startGoogleAuth(scheduleData) {
    // Save the schedule data to localStorage to retrieve after OAuth callback
    localStorage.setItem('pendingGoogleSchedule', JSON.stringify(scheduleData));
    
    // Request the auth URL from our backend
    fetch('/api/gcalendar/auth', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        },
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to get authentication URL');
        }
        return response.json();
    })
    .then(data => {
        // Redirect the user to Google's consent screen
        window.location.href = data.auth_url;
    })
    .catch(error => {
        console.error('Error starting Google authentication:', error);
        alert('Failed to connect to Google Calendar. Please try again later.');
    });
}

// Handle the Google OAuth callback
function handleGoogleCallback() {
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    const scheduleData = JSON.parse(localStorage.getItem('pendingGoogleSchedule'));
    
    if (!code || !scheduleData) {
        alert('Failed to authenticate with Google Calendar');
        return;
    }
    
    // Show loading indicator
    const loadingEl = document.createElement('div');
    loadingEl.className = 'google-loading-indicator';
    loadingEl.innerHTML = `
        <div style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.7); z-index: 1000; display: flex; align-items: center; justify-content: center;">
            <div style="background: white; padding: 20px; border-radius: 8px; text-align: center;">
                <h3>Adding events to Google Calendar...</h3>
                <p>Please wait, this may take a moment.</p>
                <div class="spinner" style="margin: 10px auto; border: 4px solid #f3f3f3; border-top: 4px solid #3498db; border-radius: 50%; width: 30px; height: 30px; animation: spin 2s linear infinite;"></div>
            </div>
        </div>
    `;
    document.body.appendChild(loadingEl);
    
    // Add the style for the spinner animation
    const style = document.createElement('style');
    style.textContent = '@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }';
    document.head.appendChild(style);
    
    // Exchange the code for a token and add the events
    fetch('/api/gcalendar/add-events', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            code: code,
            schedule: scheduleData.schedule
        }),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to add events to Google Calendar');
        }
        return response.json();
    })
    .then(data => {
        // Remove the loading indicator
        document.body.removeChild(loadingEl);
        
        // Clear the pending schedule from localStorage
        localStorage.removeItem('pendingGoogleSchedule');
        
        // Remove the code parameter from the URL to prevent re-authentication on page refresh
        const newUrl = window.location.pathname + window.location.hash;
        window.history.replaceState({}, document.title, newUrl);
        
        // Show success message
        alert(`Successfully added ${data.added_count} events to your Google Calendar.`);
    })
    .catch(error => {
        console.error('Error adding events to Google Calendar:', error);
        document.body.removeChild(loadingEl);
        alert('Failed to add events to Google Calendar. Please try again later.');
        
        // Clear localStorage to prevent further attempts with the same data
        localStorage.removeItem('pendingGoogleSchedule');
        
        // Remove the code parameter from the URL
        const newUrl = window.location.pathname + window.location.hash;
        window.history.replaceState({}, document.title, newUrl);
    });
}

// Fallback method for generating direct Google Calendar links
async function generateGoogleCalendarLinks(scheduleData) {
    try {
        // Get direct links from backend
        const response = await fetch('/api/gcalendar/generate-links', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                schedule_data: scheduleData
            })
        });
        
        const result = await response.json();
        
        if (result.status === 'success' && result.links && result.links.length > 0) {
            // Create modal to display links
            const modal = document.createElement('div');
            modal.className = 'calendar-links-modal';
            modal.style.position = 'fixed';
            modal.style.top = '0';
            modal.style.left = '0';
            modal.style.right = '0';
            modal.style.bottom = '0';
            modal.style.backgroundColor = 'rgba(0,0,0,0.7)';
            modal.style.zIndex = '1000';
            modal.style.display = 'flex';
            modal.style.alignItems = 'center';
            modal.style.justifyContent = 'center';
            
            // Create content container with AUB styling
            const content = document.createElement('div');
            content.style.backgroundColor = 'white';
            content.style.borderRadius = '8px';
            content.style.padding = '20px';
            content.style.maxWidth = '750px';
            content.style.width = '90%';
            content.style.maxHeight = '80vh';
            content.style.overflowY = 'auto';
            content.style.boxShadow = '0 5px 15px rgba(0,0,0,0.3)';
            
            // Add header with AUB styling
            const header = document.createElement('div');
            header.style.borderBottom = '2px solid #8A0635'; // AUB maroon color
            header.style.paddingBottom = '10px';
            header.style.marginBottom = '15px';
            
            const headerTitle = document.createElement('h3');
            headerTitle.textContent = 'Add to Google Calendar';
            headerTitle.style.color = '#8A0635'; // AUB maroon color
            headerTitle.style.margin = '0 0 5px 0';
            header.appendChild(headerTitle);
            
            // Add description
            const description = document.createElement('p');
            description.textContent = 'Click on each link below to add the course section to your Google Calendar:';
            description.style.margin = '10px 0';
            header.appendChild(description);
            
            content.appendChild(header);
            
            // Create a table for better presentation
            const table = document.createElement('table');
            table.className = 'calendar-links-table';
            table.style.width = '100%';
            table.style.borderCollapse = 'collapse';
            table.style.margin = '15px 0';
            table.style.borderRadius = '4px';
            table.style.overflow = 'hidden';
            
            // Add table header
            const tableHead = document.createElement('thead');
            tableHead.style.backgroundColor = '#8A0635'; // AUB maroon color
            const headerRow = document.createElement('tr');
            ['Course', 'Section', 'Days', 'Time', 'Add to Calendar'].forEach(title => {
                const th = document.createElement('th');
                th.textContent = title;
                th.style.textAlign = 'left';
                th.style.padding = '12px 15px';
                th.style.color = 'white';
                th.style.fontWeight = '500';
                headerRow.appendChild(th);
            });
            tableHead.appendChild(headerRow);
            table.appendChild(tableHead);
            
            // Add table body
            const tableBody = document.createElement('tbody');
            let rowCounter = 0;
            result.links.forEach(link => {
                const row = document.createElement('tr');
                // Alternate row colors
                row.style.backgroundColor = rowCounter % 2 === 0 ? '#f9f9f9' : 'white';
                rowCounter++;
                
                // Course cell
                const courseCell = document.createElement('td');
                courseCell.textContent = link.course;
                courseCell.style.padding = '10px 15px';
                courseCell.style.borderBottom = '1px solid #ddd';
                row.appendChild(courseCell);
                
                // Section cell
                const sectionCell = document.createElement('td');
                sectionCell.textContent = link.section || 'N/A';
                sectionCell.style.padding = '10px 15px';
                sectionCell.style.borderBottom = '1px solid #ddd';
                row.appendChild(sectionCell);
                
                // Days cell
                const daysCell = document.createElement('td');
                daysCell.textContent = link.days;
                daysCell.style.padding = '10px 15px';
                daysCell.style.borderBottom = '1px solid #ddd';
                row.appendChild(daysCell);
                
                // Time cell
                const timeCell = document.createElement('td');
                timeCell.textContent = link.time;
                timeCell.style.padding = '10px 15px';
                timeCell.style.borderBottom = '1px solid #ddd';
                row.appendChild(timeCell);
                
                // Add link cell
                const linkCell = document.createElement('td');
                linkCell.style.padding = '10px 15px';
                linkCell.style.borderBottom = '1px solid #ddd';
                
                const addButton = document.createElement('a');
                addButton.href = link.url;
                addButton.target = '_blank';
                addButton.textContent = 'Add to Calendar';
                addButton.style.display = 'inline-block';
                addButton.style.padding = '6px 12px';
                addButton.style.backgroundColor = '#8A0635'; // AUB maroon color
                addButton.style.color = 'white';
                addButton.style.textDecoration = 'none';
                addButton.style.borderRadius = '4px';
                addButton.style.fontSize = '14px';
                addButton.style.transition = 'all 0.2s ease';
                
                // Add hover effect
                addButton.onmouseover = function() {
                    this.style.backgroundColor = '#6d052a'; // Darker maroon on hover
                };
                addButton.onmouseout = function() {
                    this.style.backgroundColor = '#8A0635';
                };
                
                linkCell.appendChild(addButton);
                
                row.appendChild(linkCell);
                tableBody.appendChild(row);
            });
            
            table.appendChild(tableBody);
            content.appendChild(table);
            
            // Add close button with AUB styling
            const buttonContainer = document.createElement('div');
            buttonContainer.style.textAlign = 'right';
            buttonContainer.style.marginTop = '20px';
            
            const closeBtn = document.createElement('button');
            closeBtn.textContent = 'Close';
            closeBtn.style.padding = '8px 16px';
            closeBtn.style.backgroundColor = '#8A0635'; // AUB maroon color
            closeBtn.style.color = 'white';
            closeBtn.style.border = 'none';
            closeBtn.style.borderRadius = '4px';
            closeBtn.style.cursor = 'pointer';
            closeBtn.style.fontSize = '14px';
            closeBtn.style.transition = 'all 0.2s ease';
            
            // Add hover effect
            closeBtn.onmouseover = function() {
                this.style.backgroundColor = '#6d052a'; // Darker maroon on hover
            };
            closeBtn.onmouseout = function() {
                this.style.backgroundColor = '#8A0635';
            };
            
            closeBtn.onclick = () => {
                document.body.removeChild(modal);
            };
            buttonContainer.appendChild(closeBtn);
            content.appendChild(buttonContainer);
            
            modal.appendChild(content);
            document.body.appendChild(modal);
        } else {
            alert('No calendar links available for this schedule');
        }
    } catch (error) {
        console.error('Error generating calendar links:', error);
        alert('Error generating Google Calendar links');
    }
}

// Function to toggle between schedule views
function toggleScheduleView(container, viewType) {
    // Get all toggle buttons and views
    const toggleButtons = container.querySelectorAll('.schedule-toggle-btn');
    const views = container.querySelectorAll('.schedule-view');
    
    // Remove active class from all buttons and views
    toggleButtons.forEach(btn => btn.classList.remove('active'));
    views.forEach(view => view.classList.remove('active'));
    
    // Add active class to selected button and view
    if (viewType === 'list') {
        container.querySelector('.schedule-toggle-btn:first-child').classList.add('active');
        container.querySelector('.list-view').classList.add('active');
    } else {
        container.querySelector('.schedule-toggle-btn:last-child').classList.add('active');
        container.querySelector('.week-view').classList.add('active');
    }
}

// Function to generate weekly timetable
function generateWeeklyTimetable(scheduleData) {
    // Time slots from 8:00 AM to 9:00 PM
    const startHour = 8; // 8:00 AM
    const endHour = 21;  // 9:00 PM
    const dayMap = {
        'Monday': 0,
        'Tuesday': 1,
        'Wednesday': 2,
        'Thursday': 3,
        'Friday': 4,
        'Saturday': 5,
        'Sunday': 6
    };
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    
    // Create timetable container
    const timetableContainer = document.createElement('div');
    timetableContainer.className = 'timetable-container';
    
    // Create timetable
    const timetable = document.createElement('table');
    timetable.className = 'timetable';
    
    // Create header row with days
    const headerRow = document.createElement('tr');
    headerRow.innerHTML = '<th class="time-column">Time</th>';
    days.forEach(day => {
        headerRow.innerHTML += `<th>${day}</th>`;
    });
    
    const timetableHeader = document.createElement('thead');
    timetableHeader.appendChild(headerRow);
    timetable.appendChild(timetableHeader);
    
    // Create timetable body
    const timetableBody = document.createElement('tbody');
    
    // Create a 2D array to hold all cells (time slots × days)
    const timeSlots = (endHour - startHour) * 2; // Half-hour increments
    const grid = Array(timeSlots).fill().map(() => Array(days.length).fill(null));
    
    // Parse schedule data to get course meetings
    scheduleData.schedule.forEach(course => {
        course.meetings.forEach(meeting => {
            // Skip if no days defined
            if (!meeting.days || !meeting.days.length) return;
            
            // Parse start and end times
            let startHourVal, startMinVal, endHourVal, endMinVal;
            
            // Handle different time formats
            if (meeting.start_time && meeting.end_time) {
                const startTimeParts = meeting.start_time.match(/(\d+):(\d+)\s*(am|pm)/i);
                const endTimeParts = meeting.end_time.match(/(\d+):(\d+)\s*(am|pm)/i);
                
                if (!startTimeParts || !endTimeParts) return;
                
                startHourVal = parseInt(startTimeParts[1]);
                startMinVal = parseInt(startTimeParts[2]);
                const startPeriod = startTimeParts[3].toLowerCase();
                
                endHourVal = parseInt(endTimeParts[1]);
                endMinVal = parseInt(endTimeParts[2]);
                const endPeriod = endTimeParts[3].toLowerCase();
                
                // Convert to 24-hour format
                if (startPeriod === 'pm' && startHourVal < 12) startHourVal += 12;
                if (startPeriod === 'am' && startHourVal === 12) startHourVal = 0;
                if (endPeriod === 'pm' && endHourVal < 12) endHourVal += 12;
                if (endPeriod === 'am' && endHourVal === 12) endHourVal = 0;
            } else {
                // Skip if no valid times
                return;
            }
            
            // Calculate start and end in half-hour slots
            let startSlot = Math.max(0, (startHourVal - startHour) * 2 + (startMinVal >= 30 ? 1 : 0));
            let endSlot = Math.min(timeSlots, (endHourVal - startHour) * 2 + (endMinVal > 0 ? 1 : 0));
            
            // Ensure valid slots
            if (startSlot >= timeSlots || endSlot <= 0 || startSlot >= endSlot) {
                return;
            }
            
            const duration = endSlot - startSlot;
            
            // Add course to the grid for each day
            meeting.days.forEach(day => {
                // Handle different day formats
                let dayIndex;
                if (typeof day === 'string') {
                    // Try direct mapping first
                    dayIndex = dayMap[day];
                    
                    // If that doesn't work, try a substring match
                    if (dayIndex === undefined) {
                        for (const [dayName, index] of Object.entries(dayMap)) {
                            if (dayName.toLowerCase().includes(day.toLowerCase()) || 
                                day.toLowerCase().includes(dayName.toLowerCase())) {
                                dayIndex = index;
                                break;
                            }
                        }
                    }
                }
                
                // Skip if day not recognized
                if (dayIndex === undefined || dayIndex >= days.length) {
                    return;
                }
                
                // Add the course to the grid
                for (let i = startSlot; i < endSlot; i++) {
                    // Mark cells that will be covered by rowspan
                    if (i === startSlot) {
                        grid[i][dayIndex] = {
                            course: course.course_code,
                            section: course.section,
                            title: course.title || course.course_code,
                            location: meeting.location || 'TBA',
                            duration: duration,
                            instructor: course.instructor || 'TBA',
                            isStart: true
                        };
                    } else {
                        grid[i][dayIndex] = {
                            covered: true
                        };
                    }
                }
            });
        });
    });
    
    // Create rows for each time slot
    for (let timeSlot = 0; timeSlot < timeSlots; timeSlot++) {
        const hour = Math.floor(timeSlot / 2) + startHour;
        const minutes = timeSlot % 2 === 0 ? '00' : '30';
        const displayHour = hour % 12 === 0 ? 12 : hour % 12;
        const period = hour < 12 ? 'am' : 'pm';
        
        const row = document.createElement('tr');
        row.innerHTML = `<td class="time-cell">${displayHour}:${minutes} ${period}</td>`;
        
        // Add cells for each day based on the grid
        for (let dayIndex = 0; dayIndex < days.length; dayIndex++) {
            const cellData = grid[timeSlot][dayIndex];
            
            if (!cellData) {
                // Empty cell
                const cell = document.createElement('td');
                cell.className = 'day-cell';
                row.appendChild(cell);
            } else if (cellData.isStart) {
                // Course cell
                const cell = document.createElement('td');
                cell.className = 'course-cell';
                cell.setAttribute('rowspan', cellData.duration);
                
                // Color coding based on course name (simple hash function for color)
                const courseHash = cellData.course.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
                const hue = courseHash % 360;
                
                cell.style.backgroundColor = `hsl(${hue}, 85%, 92%)`;
                cell.style.borderColor = `hsl(${hue}, 60%, 80%)`;
                
                cell.innerHTML = `
                    <div class="course-info">
                        <div class="course-title">${cellData.course}</div>
                        <div class="course-section">Section ${cellData.section}</div>
                        <div class="course-location">${cellData.location}</div>
                    </div>
                `;
                
                row.appendChild(cell);
            }
            // Covered cells (part of a rowspan) are skipped
        }
        
        timetableBody.appendChild(row);
    }
    
    timetable.appendChild(timetableBody);
    timetableContainer.appendChild(timetable);
    
    return timetableContainer;
}

// Function to download schedule as image
function downloadScheduleAsImage(scheduleElement, filename = 'my-schedule') {
    // Use html2canvas library to convert the schedule to an image
    if (typeof html2canvas !== 'undefined') {
        html2canvas(scheduleElement).then(canvas => {
            const imageData = canvas.toDataURL('image/png');
            const link = document.createElement('a');
            link.href = imageData;
            link.download = `${filename}.png`;
            link.click();
        });
    } else {
        console.error('html2canvas library not loaded');
        alert('Download functionality requires html2canvas library which is not loaded');
    }
}

// Function to render messages
function renderMessages() {
    // Clear the chat display
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
            // System Message (department change) - Enhanced system message styling
            const systemContainer = document.createElement('div');
            systemContainer.className = 'system-message';
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
            
            // Check for schedule data in the message content
            let messageText = message.content;
            let scheduleTemplate = null;
            
            const scheduleData = extractScheduleData(message.content);
            if (scheduleData) {
                // Remove the JSON part from the displayed message
                messageText = message.content.replace(/```json\s*(\{[\s\S]*?\})\s*```/g, '');
                // Generate the schedule template
                scheduleTemplate = generateScheduleTemplate(scheduleData);
            }
            
            const messageTextElement = document.createElement('span');
            messageTextElement.className = 'message-text';
            messageTextElement.innerHTML = formatMarkdown(sanitize(messageText)).replace(/\n/g, '<br>');
            
            chatContent.appendChild(senderLabel);
            chatContent.appendChild(messageTextElement);
            
            botContainer.appendChild(botIcon);
            botContainer.appendChild(chatContent);
            
            // Append the schedule template if it exists
            if (scheduleTemplate) {
                const scheduleWrapper = document.createElement('div');
                scheduleWrapper.className = 'schedule-wrapper';
                scheduleWrapper.appendChild(scheduleTemplate);
                
                // Create a separate container for the schedule after the bot message
                chatDisplay.appendChild(botContainer);
                chatDisplay.appendChild(scheduleWrapper);
            } else {
                chatDisplay.appendChild(botContainer);
            }
            
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
                    content: `Switched to ${responseDepartment} Department Advisor`
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
                        content: `Returned to MSFEA General Advisor`
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
    
    // Adjust layout based on new sidebar state
    adjustLayoutForSidebar();
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

// Remove this since sidebar now starts open
// sidebarToggle.style.display = 'none';

// Function to adjust layout based on sidebar state
function adjustLayoutForSidebar() {
    const isSidebarClosed = sidebar.classList.contains('closed');
    
    // Set appropriate styles for chat display
    document.querySelector('.chat-display').style.marginLeft = isSidebarClosed ? '0' : '280px';
    
    // Set appropriate styles for input container
    document.querySelector('.fixed-input-container').style.left = isSidebarClosed ? '0' : '280px';
}

// Adjust layout on page load
window.addEventListener('load', function() {
    // Chat area layout adjustment
    adjustLayoutForSidebar();
    
    // Remove any loading indicators or splash screens if needed
    const loadingScreen = document.getElementById('loadingScreen');
    if (loadingScreen) {
        loadingScreen.style.opacity = '0';
        setTimeout(() => {
            loadingScreen.style.display = 'none';
        }, 500);
    }
});

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

// Set up event listeners and initialize
document.addEventListener('DOMContentLoaded', function() {
    // Initialize the sidebar state - keep it open by default
    // sidebar.classList.add('closed'); // Removed to keep sidebar open
    sidebarToggle.style.display = 'none'; // Hide the open button
    closeSidebarButton.style.display = 'block'; // Show the close button
    
    // Adjust header position based on sidebar state
    if (header) {
        // Set initial padding for header
        document.querySelector('.aub-header-container').style.paddingLeft = '320px';
        
        sidebar.addEventListener('transitionend', function() {
            // This ensures the transition is complete before adjusting
            if (sidebar.classList.contains('closed')) {
                document.querySelector('.aub-header-container').style.paddingLeft = '80px';
            } else {
                document.querySelector('.aub-header-container').style.paddingLeft = '320px';
            }
        });
    }

    // Populate the department list
    populateDepartmentList();
    
    // Render initial messages
    renderMessages();
    
    // Set up input handlers
    userInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    sendButton.addEventListener('click', sendMessage);
    
    // Setup sidebar toggle
    sidebarToggle.addEventListener('click', toggleSidebar);
    closeSidebarButton.addEventListener('click', toggleSidebar);
    
    // Setup language toggle
    languageToggle.addEventListener('click', function() {
        if (currentLanguage === 'En') {
            currentLanguage = 'Ar';
            languageLabel.textContent = 'Ar';
            document.documentElement.setAttribute('dir', 'rtl');
        } else {
            currentLanguage = 'En';
            languageLabel.textContent = 'En';
            document.documentElement.setAttribute('dir', 'ltr');
        }
    });
    
    // Setup reset button
    resetButton.addEventListener('click', resetChatbot);
    
    // Make sure the chat display is scrolled to the bottom on initial load
    scrollToBottom();
    
    // Auto-focus the input field for immediate typing
    userInput.focus();

    // Check for URL query parameters on page load
    checkUrlParams();
});

// Send message to the backend
async function sendMessageToBackend(userMessage) {
    const apiUrl = API_CHAT_URL;

    try {
        // Show thinking indicator
        showThinkingAnimation();
        
        // Prepare headers
        const headers = {
            'Content-Type': 'application/json'
        };
        
        // Add session ID if we have one
        if (sessionId) {
            headers['X-Session-ID'] = sessionId;
        }
        
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: headers,
            credentials: 'include', // This enables cookies to be sent and received
            body: JSON.stringify({
                text: userMessage
            })
        });

        if (!response.ok) {
            throw new Error(`Server returned ${response.status}: ${response.statusText}`);
        }

        // Check for session ID cookie and save it
        const cookies = document.cookie.split(';');
        for (const cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'session_id') {
                saveSessionId(value);
                break;
            }
        }
        
        // Process response
        const data = await response.json();
        
        // Replace the thinking message with the actual response
        stopThinkingAnimation();
        
        // Add the bot's reply
        addMessage("bot", data.content, data.department || "MSFEA Advisor");
        
        // Update UI based on department change
        if (data.department && departmentMap[data.department]) {
            updateDepartment(data.department);
        }
        
    } catch (error) {
        console.error('Error sending message to backend:', error);
        stopThinkingAnimation();
        
        // Add error message
        addMessage("bot", "I apologize, but there was an error processing your request. Please try again.", "MSFEA Advisor");
    }
}

// Reset conversation function
async function resetConversation() {
    try {
        // If we have a session ID, call the reset API
        if (sessionId) {
            const response = await fetch(`${API_CHAT_URL}/reset/${sessionId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                console.error(`Failed to reset session: ${response.status}`);
            }
            
            // Clear session ID
            sessionId = null;
            localStorage.removeItem('msfeaAdvisorSessionId');
        }
        
        // Clear messages
        messages = [{
            role: "bot",
            content: "Conversation has been reset. How can I help you?",
            department: currentDepartment,
            departmentIcon: currentDepartmentIcon
        }];
        
        // Update localStorage
        saveMessagesToLocalStorage();
        
        // Re-render the chat
        renderMessages();
        
    } catch (error) {
        console.error('Error resetting conversation:', error);
        addMessage("bot", "There was an error resetting the conversation. Please try again.", "MSFEA Advisor");
    }
}

// Add at the end of your script.js file
console.log("Script loaded with Google Calendar functionality");

// Override the extractScheduleData function to log when schedule data is found
const originalExtractScheduleData = extractScheduleData;
extractScheduleData = function(content) {
    const result = originalExtractScheduleData(content);
    if (result) {
        console.log("Schedule data extracted:", result);
    }
    return result;
};

// Check for URL query parameters on page load
function checkUrlParams() {
    const urlParams = new URLSearchParams(window.location.search);
    
    // Check for auth success parameter
    if (urlParams.has('auth') && urlParams.get('auth') === 'success') {
        // Show success notification
        alert('Successfully authenticated with Google Calendar! You can now add your schedule.');
        
        // Clean URL
        const newUrl = window.location.pathname;
        window.history.replaceState({}, document.title, newUrl);
    }
    
    // Check for error parameters
    if (urlParams.has('error')) {
        const errorType = urlParams.get('error');
        let errorMessage = 'An error occurred with Google Calendar authentication.';
        
        switch(errorType) {
            case 'auth_failed':
                errorMessage = 'Authentication with Google Calendar failed.';
                break;
            case 'no_code':
                errorMessage = 'No authorization code received from Google.';
                break;
            case 'token_failed':
                errorMessage = 'Failed to obtain access token from Google.';
                break;
            case 'server_error':
                errorMessage = 'A server error occurred during Google Calendar authentication.';
                break;
        }
        
        alert(errorMessage);
        
        // Clean URL
        const newUrl = window.location.pathname;
        window.history.replaceState({}, document.title, newUrl);
    }
    
    // Continue with normal callback handling if there's a code and pendingGoogleSchedule
    if (urlParams.has('code') && localStorage.getItem('pendingGoogleSchedule')) {
        handleGoogleCallback();
    }
}

// Function to display calendar links
function displayCalendarLinks(links) {
    const container = document.createElement('div');
    container.className = 'calendar-links-container';
    
    // Create a table to display the links
    const table = document.createElement('table');
    table.className = 'table table-striped';
    
    // Create table header
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    ['Course', 'Section', 'Days', 'Time', 'Add to Calendar'].forEach(text => {
        const th = document.createElement('th');
        th.textContent = text;
        headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);
    
    // Create table body
    const tbody = document.createElement('tbody');
    links.forEach(link => {
        const row = document.createElement('tr');
        
        // Course column
        const courseCell = document.createElement('td');
        courseCell.textContent = link.course;
        row.appendChild(courseCell);
        
        // Section column
        const sectionCell = document.createElement('td');
        sectionCell.textContent = link.section || 'N/A';
        row.appendChild(sectionCell);
        
        // Days column
        const daysCell = document.createElement('td');
        daysCell.textContent = link.days;
        row.appendChild(daysCell);
        
        // Time column
        const timeCell = document.createElement('td');
        timeCell.textContent = link.time;
        row.appendChild(timeCell);
        
        // Add to Calendar button column
        const buttonCell = document.createElement('td');
        const addButton = document.createElement('a');
        addButton.href = link.url;
        addButton.target = '_blank';
        addButton.className = 'btn btn-sm btn-primary';
        addButton.innerHTML = '<i class="far fa-calendar-plus"></i> Add';
        buttonCell.appendChild(addButton);
        row.appendChild(buttonCell);
        
        tbody.appendChild(row);
    });
    table.appendChild(tbody);
    container.appendChild(table);
    
    return container;
}
