import os
import json
import logging
from typing import List, Dict, Any
import argparse
from tqdm import tqdm
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
import re
import datetime
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import environment variables
from dotenv import load_dotenv
load_dotenv()

# Get API keys and settings from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

# Validate environment variables
if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY environment variable is not set")
    sys.exit(1)
    
if not PINECONE_API_KEY:
    logger.error("PINECONE_API_KEY environment variable is not set")
    sys.exit(1)
    
if not PINECONE_INDEX_NAME:
    logger.error("PINECONE_INDEX_NAME environment variable is not set")
    sys.exit(1)

logger.info(f"Using Pinecone index: {PINECONE_INDEX_NAME}")

# Initialize Pinecone
try:
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(PINECONE_INDEX_NAME)
except Exception as e:
    logger.error(f"Failed to initialize Pinecone: {str(e)}")
    sys.exit(1)

# Initialize the embedding model
try:
    embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
except Exception as e:
    logger.error(f"Failed to initialize OpenAI embeddings: {str(e)}")
    sys.exit(1)

# Initialize the vector store
try:
    vectorstore = PineconeVectorStore(
        index=index,
        embedding=embeddings,
        text_key="text",
        namespace="schedule_maker_namespace"
    )
    logger.info("Vector store initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize vector store: {str(e)}")
    sys.exit(1)

def extract_time_info(meeting_times: List[Dict]) -> str:
    """Extract formatted meeting time information from course data"""
    if not meeting_times:
        return "No meeting time information available."
    
    result = []
    for meeting in meeting_times:
        time_info = []
        
        # Get days as full names (Monday, Tuesday, etc.)
        if "days_array" in meeting and meeting["days_array"]:
            time_info.append(f"Days: {', '.join(meeting['days_array'])}")
        elif "Days" in meeting:
            time_info.append(f"Days: {meeting['Days']}")
            
        # Get start and end times
        if "start_time" in meeting and "end_time" in meeting:
            time_info.append(f"Time: {meeting['start_time']} to {meeting['end_time']}")
        elif "Time" in meeting:
            time_info.append(f"Time: {meeting['Time']}")
            
        # Get location information
        location = []
        if "building" in meeting and meeting["building"]:
            location.append(meeting["building"])
        if "room" in meeting and meeting["room"]:
            location.append(meeting["room"])
            
        if location:
            time_info.append(f"Location: {' '.join(location)}")
        elif "Where" in meeting:
            time_info.append(f"Location: {meeting['Where']}")
            
        # Get instructor if available
        if "Instructors" in meeting:
            time_info.append(f"Instructor: {meeting['Instructors']}")
            
        result.append(" | ".join(time_info))
    
    return "\n".join(result)

def create_chunks_from_course_data(course_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Create semantically meaningful chunks from course data that are relevant for scheduling.
    Each chunk contains all sections of a specific course.
    """
    chunks = []
    
    # Process the nested course structure
    for term_id, term_data in course_data.items():
        if term_id == "metadata":  # Skip metadata section
            continue
            
        term_name = term_data.get("term_name", "Unknown Term")
        
        # Process each subject
        for subject_code, subject_data in term_data.get("subjects", {}).items():
            subject_name = subject_data.get("subject_name", "Unknown Subject")
            
            # Process each course code and its sections
            for course_code, course_sections in subject_data.get("courses", {}).items():
                if not course_sections:  # Skip if no sections
                    continue
                
                # Get course info from first section (common across sections)
                first_section = course_sections[0]
                course_title = first_section.get("course_title", "Unknown Course")
                course_subj = first_section.get("subject_code", subject_code)
                course_number = first_section.get("course_number", "")
                course_credits = first_section.get("credits", "Unknown Credits")
                
                # Create a combined description for all sections
                sections_info = []
                
                for section in course_sections:
                    section_code = section.get("section", "")
                    crn = section.get("crn", "Unknown CRN")
                    
                    # Extract meeting time information for this section
                    meeting_times_str = extract_time_info(section.get("meeting_times", []))
                    
                    section_description = f"""
Section: {section_code}
CRN: {crn}
Schedule Information:
{meeting_times_str}
"""
                    sections_info.append(section_description.strip())
                
                # Create a consolidated course description with all sections
                course_description = f"""
Course: {course_subj} {course_number} - {course_title}
Credits: {course_credits}
Term: {term_name} ({term_id})
Subject: {subject_name} ({subject_code})

Available Sections:
"""
                # Add all section information
                course_description += "\n\n".join(sections_info)
                
                # Create metadata for effective retrieval
                metadata = {
                    "course_code": course_code,
                    "course_title": course_title,
                    "subject": course_subj,
                    "term_id": term_id,
                    "term_name": term_name,
                    "type": "course_schedule",
                    "source": f"{course_subj}_{course_number}",
                    "section_count": len(course_sections),
                    "crns": [section.get("crn", "") for section in course_sections]
                }
                
                chunks.append({
                    "text": course_description,
                    "metadata": metadata
                })
                
                # If there are prerequisites, add them as another chunk
                if "prerequisites" in first_section and first_section["prerequisites"]:
                    prereq_description = f"""
Course: {course_subj} {course_number} - {course_title}
Prerequisites: {first_section["prerequisites"]}

These prerequisites should be considered when planning your schedule to ensure you meet all requirements.
                    """.strip()
                    
                    prereq_metadata = metadata.copy()
                    prereq_metadata["type"] = "prerequisites"
                    
                    chunks.append({
                        "text": prereq_description,
                        "metadata": prereq_metadata
                    })
    
    return chunks

def create_general_schedule_guidelines() -> List[Dict[str, Any]]:
    """Create general scheduling guidelines and advice chunks"""
    guidelines = [
        {
            "text": """
Schedule Planning Guidelines:
1. Most classes are scheduled on Monday/Wednesday/Friday for 50 minutes or Tuesday/Thursday for 75 minutes.
2. Try to avoid scheduling back-to-back classes in distant buildings.
3. Consider your energy levels when scheduling early morning or late evening classes.
4. Leave time for meals and study breaks in your schedule.
5. Be mindful of balancing difficult courses throughout the week.
            """.strip(),
            "metadata": {
                "type": "scheduling_guidelines",
                "source": "general_advice",
                "topic": "time_management"
            }
        },
        {
            "text": """
Resolving Schedule Conflicts:
1. If two courses overlap, check if either offers multiple sections with different times.
2. Consider taking one of the conflicting courses in a future semester.
3. Check if any of the courses are offered in summer or winter terms.
4. Some departments may offer independent study options for certain courses.
5. Consult with your academic advisor for program-specific options.
            """.strip(),
            "metadata": {
                "type": "scheduling_guidelines",
                "source": "general_advice",
                "topic": "conflict_resolution"
            }
        },
        {
            "text": """
AUB Campus Buildings:
The AUB campus includes several buildings where classes are held, including:
- College Hall (older building near Main Gate)
- Nicely Hall (houses many humanities classes)
- West Hall (houses lecture halls and classrooms)
- Bliss Hall (home to many language courses)
- IOEC (Engineering building with classrooms and labs)
- Bechtel Engineering Building (newer engineering facilities)
- Issam Fares Institute (includes lecture spaces)
- Science buildings including Chemistry, Physics, and Biology
- Suliman S.Olayan School of Business

When planning your schedule, consider the distance between buildings for back-to-back classes.
            """.strip(),
            "metadata": {
                "type": "campus_info",
                "source": "building_locations",
                "topic": "campus_navigation"
            }
        }
    ]
    
    return guidelines

def populate_schedule_namespace(courses_file_path: str):
    """
    Process course data and upload chunks to the schedule_maker_namespace
    """
    logger.info(f"Loading course data from {courses_file_path}")
    
    try:
        with open(courses_file_path, 'r', encoding='utf-8') as f:
            courses_data = json.load(f)
        
        # Log structure of data to help debug
        term_count = len(courses_data.keys())
        subject_count = sum(len(term_data.get("subjects", {})) 
                         for term_data in courses_data.values())
        
        logger.info(f"Data structure: {term_count} terms, {subject_count} subjects")
        
        # Create chunks from course data
        course_chunks = create_chunks_from_course_data(courses_data)
        logger.info(f"Created {len(course_chunks)} course-specific chunks")
        
        # Add general scheduling guidelines
        general_guidelines = create_general_schedule_guidelines()
        logger.info(f"Created {len(general_guidelines)} general guideline chunks")
        
        # Combine all chunks
        all_chunks = course_chunks + general_guidelines
        
        # Upsert chunks to vector store in batches
        batch_size = 100
        total_batches = (len(all_chunks) + batch_size - 1) // batch_size
        
        logger.info(f"Uploading {len(all_chunks)} chunks in {total_batches} batches")
        
        for i in tqdm(range(0, len(all_chunks), batch_size), desc="Uploading chunks"):
            batch = all_chunks[i:i+batch_size]
            
            # Prepare batch for vector store
            texts = [chunk["text"] for chunk in batch]
            metadatas = [chunk["metadata"] for chunk in batch]
            
            try:
                # Add to vector store
                vectorstore.add_texts(
                    texts=texts,
                    metadatas=metadatas,
                    namespace="schedule_maker_namespace"
                )
                logger.debug(f"Successfully uploaded batch {i//batch_size + 1}/{total_batches}")
            except Exception as e:
                logger.error(f"Error uploading batch {i//batch_size + 1}/{total_batches}: {str(e)}")
                # Continue with next batch
                continue
        
        logger.info(f"Successfully uploaded {len(all_chunks)} chunks to schedule_maker_namespace")
        
    except Exception as e:
        logger.error(f"Error processing and uploading course data: {str(e)}")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Populate schedule_maker_namespace with course data")
    parser.add_argument("--courses", type=str, default="./Scraper/output/courses.json", 
                        help="Path to the courses JSON file from the scraper")
    
    args = parser.parse_args()
    
    # Check if the courses file exists
    if not os.path.exists(args.courses):
        logger.error(f"Courses file not found: {args.courses}")
        sys.exit(1)
    
    populate_schedule_namespace(args.courses)
    logger.info("Done!")