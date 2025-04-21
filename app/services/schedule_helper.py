from langchain_openai import ChatOpenAI
from app.core.config import OPENAI_API_KEY
from app.models.schemas import State
import json
import logging
import urllib.parse
from datetime import datetime, timedelta

# Set up logging
logger = logging.getLogger(__name__)

# Initialize OpenAI LLM
llm = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    model_name="gpt-4o"
)

def extract_course_names(message: str) -> list:
    """
    Use LLM to extract course names from the user message
    """
    system_message = """
    Extract only the course names/codes mentioned in the user's message.
    Return them as a comma-separated list.
    Example: For "Can you help me schedule CMPS 200 and MATH 201?" return "CMPS 200, MATH 201"
    If no courses are mentioned, return an empty string.
    """
    
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": message}
    ]
    
    response = llm.invoke(messages)
    if not response.content.strip():
        return []
    return [course.strip() for course in response.content.split(",")]

def get_course_info(course_names: list, courses_data: dict) -> list:
    """
    Retrieve course information from courses.json for specified courses
    """
    course_info = []
    
    # Log the course names we're looking for
    logger.info(f"Looking for courses: {course_names}")
    
    for term_data in courses_data.values():
        if isinstance(term_data, dict) and "subjects" in term_data:
            for subject_code, subject_data in term_data["subjects"].items():
                logger.info(f"Checking subject: {subject_code}")
                if "courses" in subject_data:
                    for course_code, course_data in subject_data["courses"].items():
                        # Log each course we're checking
                        logger.info(f"Checking course: {course_code}")
                        if any(course_name.upper() in course_code.upper() for course_name in course_names):
                            logger.info(f"Found matching course: {course_code}")
                            
                            # The course_data is already a list of sections
                            sections = []
                            for section in course_data:
                                if "meeting_times" in section:
                                    sections.append({
                                        "section": section.get("section", ""),
                                        "meetings": section["meeting_times"],
                                        "instructor": section.get("meeting_times", [{}])[0].get("primary_instructor", ""),
                                        "instructors": section.get("meeting_times", [{}])[0].get("instructor_names", [])
                                    })
                            
                            course_info.append({
                                "code": course_code,
                                "sections": sections
                            })
    
    logger.info(f"Found {len(course_info)} matching courses")
    return course_info

def generate_google_calendar_link(schedule_data):
    """
    Generate a Google Calendar link for the schedule.
    Returns a list of URLs that open Google Calendar with pre-filled event details.
    Each link represents a course section (not individual days).
    """
    if not schedule_data or not schedule_data.get('schedule'):
        return []
    
    links = []
    
    # Process each course in the schedule
    for course in schedule_data['schedule']:
        for meeting in course.get('meetings', []):
            days = meeting.get('days', [])
            if not days:
                continue
                
            start_time = meeting.get('start_time', '')
            end_time = meeting.get('end_time', '')
            
            # Parse time from string (e.g. "9:00 am") to hours and minutes
            def parse_time(time_str):
                time_str = time_str.lower().strip()
                is_pm = 'pm' in time_str
                time_str = time_str.replace('am', '').replace('pm', '').strip()
                
                hour, minute = 9, 0  # Default to 9:00 if parsing fails
                if ':' in time_str:
                    hour_str, minute_str = time_str.split(':')
                    hour = int(hour_str)
                    minute = int(minute_str)
                else:
                    try:
                        hour = int(time_str)
                    except:
                        pass
                
                if is_pm and hour < 12:
                    hour += 12
                elif not is_pm and hour == 12:
                    hour = 0
                    
                return hour, minute
            
            # Find the earliest day of the week for this course
            day_mapping = {
                "MONDAY": 0, "TUESDAY": 1, "WEDNESDAY": 2, 
                "THURSDAY": 3, "FRIDAY": 4, "SATURDAY": 5, "SUNDAY": 6
            }
            day_indices = [day_mapping.get(day.upper(), 0) for day in days]
            min_day_index = min(day_indices)
            
            # Calculate the next occurrence of the earliest day
            today = datetime.now()
            current_day = today.weekday()
            days_ahead = (min_day_index - current_day) % 7
            
            if days_ahead == 0:  # If today is the earliest day, start next week
                days_ahead = 7
                
            next_day = today + timedelta(days=days_ahead)
            
            # Parse start and end times
            start_hour, start_minute = parse_time(start_time)
            end_hour, end_minute = parse_time(end_time)
            
            # Create datetime objects for the event start and end
            start_datetime = next_day.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
            end_datetime = next_day.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)
            
            # Format for Google Calendar URL
            start_str = start_datetime.strftime("%Y%m%dT%H%M%S")
            end_str = end_datetime.strftime("%Y%m%dT%H%M%S")
            
            # Create a list of weekday codes for the recurrence rule
            weekday_codes = []
            for day in days:
                if day.upper() == "MONDAY":
                    weekday_codes.append("MO")
                elif day.upper() == "TUESDAY":
                    weekday_codes.append("TU")
                elif day.upper() == "WEDNESDAY":
                    weekday_codes.append("WE")
                elif day.upper() == "THURSDAY":
                    weekday_codes.append("TH")
                elif day.upper() == "FRIDAY":
                    weekday_codes.append("FR")
                elif day.upper() == "SATURDAY":
                    weekday_codes.append("SA")
                elif day.upper() == "SUNDAY":
                    weekday_codes.append("SU")
            
            # Create recurrence rule that includes all meeting days
            recurrence_rule = f"RRULE:FREQ=WEEKLY;COUNT=15;BYDAY={','.join(weekday_codes)}"
            
            # Create event details
            event_details = {
                "action": "TEMPLATE",
                "text": f"{course['course_code']} - {course.get('title', 'Class')}",
                "details": f"Course: {course['course_code']}\nSection: {course.get('section', '')}\nInstructor: {course.get('instructor', 'TBA')}\nMeeting days: {', '.join(days)}",
                "location": meeting.get('location', 'AUB Campus'),
                "dates": f"{start_str}/{end_str}",
                "recur": recurrence_rule
            }
            
            # Generate URL
            calendar_url = f"https://www.google.com/calendar/render?{urllib.parse.urlencode(event_details)}"
            
            # Create a descriptive label for all meeting days
            days_display = ", ".join(days)
            
            links.append({
                "days": days_display,
                "time": f"{start_time} - {end_time}",
                "course": course['course_code'],
                "section": course.get('section', ''),
                "url": calendar_url
            })
    
    return links

def schedule_helper(state: State):
    """
    Handle queries about course scheduling, conflicts, and classroom locations
    """
    user_message = state["messages"][-1].content
    
    # Step 1: Extract course names using LLM
    course_names = extract_course_names(user_message)
    logger.info(f"Extracted course names: {course_names}")
    
    # Step 2: Load and retrieve course information
    try:
        with open("./Scraper/output/courses.json", 'r', encoding='utf-8') as f:
            courses_data = json.load(f)
            logger.info(f"Successfully loaded courses.json")
            logger.info(f"Number of terms: {len(courses_data)}")
        
        course_info = get_course_info(course_names, courses_data)
        logger.info(f"Retrieved information for {len(course_info)} courses")
        
    except Exception as e:
        logger.error(f"Error retrieving course information: {str(e)}")
        course_info = []
    
    # Step 3: Format course information for LLM
    context_str = ""
    if course_info:
        context_str = "Course Information:\n"
        for course in course_info:
            context_str += f"\n{course['code']}:\n"
            for section in course['sections']:
                section_num = section.get('section', '')
                context_str += f"Section {section_num}:\n"
                if section.get('instructor'):
                    context_str += f"Instructor: {section['instructor']}\n"
                for meeting in section.get('meetings', []):
                    if meeting:
                        context_str += f"- Days: {meeting.get('days_array', '')}\n"
                        context_str += f"  Time: {meeting.get('start_time', '')} to {meeting.get('end_time', '')}\n"
                        context_str += f"  Location: {meeting.get('building', '')} {meeting.get('room', '')}\n"
    
    # Create base prompt
    base_prompt = """
    You are a scheduling assistant for students at the American University of Beirut (AUB).
    
    The student is asking about: "{user_message}"
    
    Your primary responsibilities:
    1. Help students resolve scheduling conflicts
    2. Provide information about course timings and locations
    3. Suggest alternative sections when there are conflicts
    4. Help optimize student schedules to minimize gaps or create preferred time blocks
    
    IMPORTANT: the Letter E in a section means a recitation not a lecture and a letter L means a lecture make sure for every course that has a recitation to also mention the lecture.
    not all courses have a recitation. 

    Use the following course information to help answer their question:
    {context_str}
    IMPORTANT: TAKE CARE FOR CONFLICTS DONT GIVE ME 2 COURSES AT THE SAME TIME IF YOU CANT RUN AWAY FROM CONFLICTS PLEASE TELL THE USER TO CHOOSE DIFFERENT COURSES.
    If you don't have specific information about mentioned courses, explain that you need the correct course codes to provide accurate scheduling information.
    
    Respond in a professional, helpful manner appropriate for a university scheduling assistant.
    
    IF ASKED ABOUT SCHEDULE YOUR JOB IS TO PROPOSE A SCHEDULE NOT TO STATE OPTIONS GIVE THE STUDENT THE BEST SCHEDULE POSSIBLE.
    
    After you create a schedule, tell the user they can add this schedule to their Google Calendar using the calendar button that will appear below your response. When they click "Add to Google Calendar", they'll be asked to sign in with their Google account, and then their classes will be added as recurring events in their calendar.
    """
    
    # Create JSON template instruction separately
    json_instruction = """
    IMPORTANT: When responding to schedule creation requests, you must include a structured representation of the schedule in the following JSON format at the end of your message:
    
    ```json
    {
      "is_schedule": true,
      "schedule": [
        {
          "course_code": "COURSE_CODE",
          "section": "SECTION_NUMBER",
          "title": "COURSE_TITLE",
          "meetings": [
            {
              "days": ["MONDAY", "WEDNESDAY"],
              "start_time": "9:00 am",
              "end_time": "10:15 am",
              "location": "BUILDING ROOM"
            }
          ],
          "instructor": "INSTRUCTOR_NAME"
        }
      ]
    }
    ```
    
    The structured schedule should be included ONLY when the user is specifically asking for a schedule to be created, not for general course information queries.
    """
    
    # Combine the parts using format() instead of f-strings
    system_message = base_prompt.format(user_message=user_message, context_str=context_str) + json_instruction
    
    messages = [{"role": "system", "content": system_message}] + state["messages"]
    
    # Get thread_id from configurable state if available (for conversation memory)
    thread_id = None
    if hasattr(state, "get") and callable(state.get):
        config = state.get("configurable", {})
        if isinstance(config, dict):
            thread_id = config.get("thread_id")
    
    # Pass thread_id to maintain conversation context if available
    if thread_id:
        response = llm.invoke(messages, config={"configurable": {"thread_id": thread_id}})
    else:
        response = llm.invoke(messages)
    
    return {"messages": response}  