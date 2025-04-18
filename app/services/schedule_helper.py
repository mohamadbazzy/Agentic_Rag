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

def generate_outlook_calendar_link(schedule_data):
    """
    Generate an Outlook calendar invitation link for the given schedule.
    Returns a URL that opens Outlook calendar with the schedule details pre-filled.
    """
    if not schedule_data or not schedule_data.get('schedule'):
        return None
    
    # Find the earliest and latest dates in the schedule
    # For simplicity, we'll create a single calendar event for the entire schedule
    start_date = datetime.now() + timedelta(days=1)  # Start tomorrow
    end_date = start_date + timedelta(days=120)  # Academic term ~4 months
    
    # Create a subject line with all course codes
    course_codes = [course['course_code'] for course in schedule_data['schedule']]
    subject = f"Academic Schedule: {', '.join(course_codes)}"
    
    # Create a body with the full schedule details
    body = "My Academic Schedule:\n\n"
    for course in schedule_data['schedule']:
        body += f"Course: {course['course_code']} - {course.get('title', '')}\n"
        body += f"Section: {course.get('section', '')}\n"
        body += f"Instructor: {course.get('instructor', 'TBA')}\n"
        
        # Add meeting times
        for meeting in course.get('meetings', []):
            days = ", ".join(meeting.get('days', []))
            body += f"- {days} {meeting.get('start_time', '')} to {meeting.get('end_time', '')}\n"
            body += f"  Location: {meeting.get('location', 'TBA')}\n"
        body += "\n"
    
    # URL encode parameters
    subject_encoded = urllib.parse.quote(subject)
    body_encoded = urllib.parse.quote(body)
    start_date_str = start_date.strftime("%Y-%m-%dT%H:%M:%S")
    end_date_str = end_date.strftime("%Y-%m-%dT%H:%M:%S")
    
    # Create Outlook web calendar link
    outlook_link = (
        f"https://outlook.office.com/calendar/action/compose?"
        f"subject={subject_encoded}&"
        f"body={body_encoded}&"
        f"startdt={start_date_str}&"
        f"enddt={end_date_str}"
    )
    
    return outlook_link

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
    
    If you don't have specific information about mentioned courses, explain that you need the correct course codes to provide accurate scheduling information.
    
    Respond in a professional, helpful manner appropriate for a university scheduling assistant.
    
    IF ASKED ABOUT SCHEDULE YOUR JOB IS TO PROPOSE A SCHEDULE NOT TO STATE OPTIONS GIVE THE STUDENT THE BEST SCHEDULE POSSIBLE.
    
    After you create a schedule, tell the user they can add this schedule to their Outlook calendar using the calendar link that will appear below your response.
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