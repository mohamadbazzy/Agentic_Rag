import requests
from bs4 import BeautifulSoup
import json
import time  # optional: to delay requests if needed
import os
import re
import argparse
import datetime
import logging
import sys
from pathlib import Path

# Create logs directory if it doesn't exist
Path("logs").mkdir(exist_ok=True)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/scraper.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('aub_scraper')

# Base URL for AUB Banner
BASE_URL = "https://www-banner.aub.edu.lb"
# Initial URL (schedule banner)
INITIAL_URL = BASE_URL + "/pls/weba/bwckschd.p_disp_dyn_sched"

# Create a session to persist cookies
session = requests.Session()

# Set your desired term code here (e.g., "202520")
SELECTED_TERM = "202520"

def get_initial_page():
    """Fetches the schedule banner page."""
    response = session.get(INITIAL_URL)
    response.raise_for_status()
    return response.text

def parse_initial_page(html):
    """
    Parses the initial page to extract:
      - The form action URL for term submission.
      - Any hidden input fields.
      - The term dropdown options from the select element (name="p_term").
    """
    soup = BeautifulSoup(html, 'html.parser')
    form = soup.find("form")
    if not form:
        raise Exception("No form found on the initial page.")
    
    # Extract form action (make absolute if needed)
    form_action = form.get("action")
    if not form_action.startswith("http"):
        form_action = BASE_URL + form_action

    # Get hidden inputs from the form
    hidden_fields = {}
    for inp in form.find_all("input", {"type": "hidden"}):
        name = inp.get("name")
        value = inp.get("value", "")
        if name:
            hidden_fields[name] = value

    # Extract term options from the select element (name="p_term")
    term_select = form.find("select", {"name": "p_term"})
    terms = {}
    if term_select:
        for option in term_select.find_all("option"):
            term_value = option.get("value")
            term_text = option.text.strip()
            if term_value and term_value != "":
                terms[term_value] = term_text
    else:
        raise Exception("No term select element found.")

    return form_action, hidden_fields, terms

def submit_term(form_action, hidden_fields, term):
    """
    Submits the term selection form.
    Returns the HTML of the subject selection page.
    """
    data = hidden_fields.copy()
    data["p_term"] = term
    response = session.post(form_action, data=data)
    response.raise_for_status()
    return response.text

def parse_subjects(html):
    """
    From the subject selection page, extract the subject dropdown.
    Returns a dictionary of subjects and the BeautifulSoup object.
    """
    soup = BeautifulSoup(html, 'html.parser')
    subj_select = soup.find("select", {"id": "subj_id"})
    subjects = {}
    if subj_select:
        for option in subj_select.find_all("option"):
            subj_value = option.get("value")
            subj_text = option.text.strip()
            if subj_value:
                subjects[subj_value] = subj_text
    else:
        raise Exception("Subject select element not found.")
    return subjects, soup

def extract_hidden_fields(soup):
    """
    Extracts hidden inputs from the given BeautifulSoup object.
    These fields are typically required for subsequent POST requests.
    """
    hidden = {}
    for inp in soup.find_all("input", {"type": "hidden"}):
        name = inp.get("name")
        value = inp.get("value", "")
        if name:
            hidden[name] = value
    return hidden

def submit_subject(term, subject, hidden_data):
    """
    Submits the subject selection form.
    Returns the HTML of the courses listing page.
    """
    # The correct URL for getting courses by subject
    url = BASE_URL + "/pls/weba/bwckschd.p_get_crse_unsec"
    
    # Use a list of tuples to allow duplicate keys
    data = [
        ("term_in", term),
        ("sel_subj", "dummy"),
        ("sel_day", "dummy"),
        ("sel_schd", "dummy"),
        ("sel_insm", "dummy"),
        ("sel_camp", "dummy"),
        ("sel_levl", "dummy"),
        ("sel_sess", "dummy"),
        ("sel_instr", "dummy"),
        ("sel_ptrm", "dummy"),
        ("sel_attr", "dummy"),
        ("sel_subj", subject),
        ("sel_crse", ""),
        ("sel_title", ""),
        ("sel_schd", "%"),
        ("sel_from_cred", ""),
        ("sel_to_cred", ""),
        ("sel_camp", "%"),
        ("sel_ptrm", "%"),
        ("sel_instr", "%"),
        ("sel_attr", "%"),
        ("begin_hh", "0"),
        ("begin_mi", "0"),
        ("begin_ap", "a"),
        ("end_hh", "0"),
        ("end_mi", "0"),
        ("end_ap", "a"),
        ("SUB_BTN", "Get Courses")
    ]
    
    response = session.post(url, data=data)
    response.raise_for_status()
    
    # Debug: Save the HTML to check its structure
    if subject == "ACCT":  # Just save one subject for debugging
        with open("debug_response.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        print(f"  Saved debug HTML for {subject}")
    
    return response.text

def parse_subject_page_for_courses_and_details(html):
    """
    Parses the subject page that lists all courses (with details) in one place.
    """
    soup = BeautifulSoup(html, "html.parser")
    courses = []
    
    # Debug info
    print("  Parsing HTML, size:", len(html))
    
    # Find all table rows with 'ddtitle' class which contain course headers
    title_rows = soup.find_all("th", {"class": "ddtitle"})
    print(f"  Found {len(title_rows)} course title rows")
    
    for title_row in title_rows:
        course = {}
        
        # Extract course title and URL
        a_tag = title_row.find("a")
        if a_tag:
            full_title = a_tag.text.strip()
            course["full_title"] = full_title
            
            # Parse the title using regex to handle the format:
            # "Course Name - CRN - SUBJ NUM - Section"
            title_pattern = r'(.*?) - (\d+) - ([A-Z]+) (\d+[A-Z]?) - (\w+)'
            match = re.match(title_pattern, full_title)
            
            if match:
                course["course_title"] = match.group(1).strip()
                course["crn"] = match.group(2).strip()
                course["subject_code"] = match.group(3).strip()
                course["course_number"] = match.group(4).strip()
                course["section"] = match.group(5).strip()
            
            course["detail_url"] = a_tag.get("href", "")
            if course["detail_url"] and not course["detail_url"].startswith("http"):
                course["detail_url"] = BASE_URL + course["detail_url"]
        else:
            course["full_title"] = title_row.get_text(strip=True)
        
        # Get the parent TR, then find the next TR which should contain details
        parent_tr = title_row.parent
        if parent_tr and parent_tr.name == "tr":
            details_tr = parent_tr.find_next_sibling("tr")
            if details_tr:
                details_td = details_tr.find("td", {"class": "dddefault"})
                if details_td:
                    # Extract all text
                    detail_text = list(details_td.stripped_strings)
                    course["summary_details"] = " | ".join(detail_text)
                    
                    # Parse structured details
                    details = {}
                    current_key = None
                    
                    for text in detail_text:
                        if ":" in text and text.split(":")[0].strip() in [
                            "Associated Term", "Registration Dates", "Levels", 
                            "Campus", "Instructors", "Status", "Credits"
                        ]:
                            parts = text.split(":", 1)
                            current_key = parts[0].strip()
                            details[current_key] = parts[1].strip()
                        elif current_key and text:
                            details[current_key] += " " + text
                    
                    course["structured_details"] = details
                    
                    # Parse the meeting times table
                    sched_table = details_td.find("table", {"class": "datadisplaytable"})
                    if sched_table:
                        meeting_rows = sched_table.find_all("tr")
                        if len(meeting_rows) > 1:
                            headers = [th.get_text(strip=True) for th in meeting_rows[0].find_all("th")]
                            meeting_info = []
                            for m_row in meeting_rows[1:]:
                                cells = m_row.find_all("td")
                                if len(cells) == len(headers):
                                    row_dict = {
                                        headers[idx]: cells[idx].get_text(strip=True)
                                        for idx in range(len(headers))
                                    }
                                    meeting_info.append(row_dict)
                            course["meeting_times"] = meeting_info
        
        # Enhanced credit parsing
        if "structured_details" in course and "Levels" in course["structured_details"]:
            levels_text = course["structured_details"]["Levels"]
            credit_match = re.search(r'(\d+\.\d+)\s+Credits', course["summary_details"])
            if credit_match:
                course["credits"] = float(credit_match.group(1))
        
        # Enhanced meeting time parsing
        if "meeting_times" in course:
            for meeting in course["meeting_times"]:
                if "Time" in meeting:
                    time_parts = meeting["Time"].split("-")
                    if len(time_parts) == 2:
                        meeting["start_time"] = time_parts[0].strip()
                        meeting["end_time"] = time_parts[1].strip()
                
                if "Days" in meeting:
                    days_text = meeting["Days"]
                    days_mapping = {
                        "M": "Monday",
                        "T": "Tuesday", 
                        "W": "Wednesday",
                        "R": "Thursday",
                        "F": "Friday",
                        "S": "Saturday",
                        "U": "Sunday"
                    }
                    meeting["days_array"] = [days_mapping.get(day, day) for day in days_text]
                
                if "Where" in meeting:
                    where_text = meeting["Where"]
                    # Look for patterns like "Building Name 123" where 123 is the room number
                    room_pattern = r'(.*?)(\s+\w*\d+\w*)\s*$'
                    room_match = re.search(room_pattern, where_text)
                    if room_match:
                        meeting["building"] = room_match.group(1).strip()
                        meeting["room"] = room_match.group(2).strip()
                    else:
                        meeting["building"] = where_text
                        meeting["room"] = ""
        
        # Find the course syllabus link
        syllabus_link = details_td.find('a', href=lambda href: href and 'syllabi' in href)
        if syllabus_link:
            course["syllabus_url"] = syllabus_link['href']
        
        # Find the catalog entry link
        catalog_link = details_td.find('a', href=lambda href: href and 'bwckctlg.p_display_courses' in href)
        if catalog_link:
            course["catalog_url"] = catalog_link['href']
            if course["catalog_url"].startswith('/'):
                course["catalog_url"] = BASE_URL + course["catalog_url"]
        
        # For each meeting_time entry, extract instructor emails
        if "meeting_times" in course:
            for meeting in course["meeting_times"]:
                if "Instructors" in meeting:
                    instructor_text = meeting["Instructors"]
                    # Parse primary instructors (marked with P)
                    primary_pattern = r'([^(]+)\s*\(\s*P\s*\)'
                    primary_match = re.search(primary_pattern, instructor_text)
                    if primary_match:
                        meeting["primary_instructor"] = primary_match.group(1).strip()
                    
                    # Extract all instructors
                    instructors = []
                    # Clean up the text by removing email icons
                    clean_text = re.sub(r'\s*\([^)]*\)\s*', ' ', instructor_text)
                    instructor_names = [name.strip() for name in clean_text.split(',') if name.strip()]
                    meeting["instructor_names"] = instructor_names
        
        # Extract status information (open, closed, etc.)
        if "structured_details" in course and "Status" in course["structured_details"]:
            status_text = course["structured_details"]["Status"]
            course["status"] = status_text
        
        # Add a convenient course_code field (SUBJ NUM format)
        if "subject_code" in course and "course_number" in course:
            course["course_code"] = f"{course['subject_code']} {course['course_number']}"
        
        courses.append(course)
    
    return courses

# Add argument parsing
def parse_arguments():
    parser = argparse.ArgumentParser(description='AUB Course Scraper')
    parser.add_argument('--term', type=str, help='Term code to scrape (default: current configured term)')
    parser.add_argument('--output-dir', type=str, default='output', help='Directory to save the output')
    return parser.parse_args()

# Modify your main function
def main():
    args = parse_arguments()
    
    # Use command line term if provided
    term_to_use = args.term if args.term else SELECTED_TERM
    output_dir = args.output_dir
    
    start_time = datetime.datetime.now()
    logger.info(f"Starting scraper for term {term_to_use}")
    
    try:
        # Step 1: Get the initial schedule banner page.
        initial_html = get_initial_page()
        # Step 2: Parse the initial page to extract form action, hidden fields, and term options.
        form_action, hidden_fields, terms = parse_initial_page(initial_html)
        print("Available terms:")
        for term_id, term_name in terms.items():
            print(f"  {term_id}: {term_name}")
        
        # Check if the selected term exists in the options.
        if term_to_use not in terms:
            raise Exception(f"Selected term '{term_to_use}' not found among available terms.")
        
        # Process only the selected term.
        term_name = terms[term_to_use]
        print(f"\nProcessing selected term: {term_to_use} - {term_name}")
        subj_html = submit_term(form_action, hidden_fields, term_to_use)
        subjects, subj_soup = parse_subjects(subj_html)
        # Extract hidden fields from the subject selection page.
        subj_hidden = extract_hidden_fields(subj_soup)
        
        term_data = {
            "term_name": term_name,
            "subjects": {}
        }
        # For each subject, fetch courses.
        for subj, subj_name in subjects.items():
            print(f"  Processing subject: {subj} - {subj_name}")
            
            # Add retry logic for network requests
            max_retries = 3
            retry_delay = 5  # seconds
            
            for retry in range(max_retries):
                try:
                    courses_html = submit_subject(term_to_use, subj, subj_hidden)
                    courses = parse_subject_page_for_courses_and_details(courses_html)
                    break
                except requests.RequestException as e:
                    if retry < max_retries - 1:
                        logger.warning(f"Request failed for {subj}, retrying in {retry_delay} seconds... ({retry+1}/{max_retries})")
                        time.sleep(retry_delay)
                    else:
                        logger.error(f"Failed to fetch data for {subj} after {max_retries} attempts: {e}")
                        raise
            
            term_data["subjects"][subj] = {
                "subject_name": subj_name,
                "courses": courses
            }
        
        # In the main function, add term metadata to each course
        for subj, subj_data in term_data["subjects"].items():
            for course in subj_data["courses"]:
                course["term_id"] = term_to_use
                course["term_name"] = term_name
        
        # Clean up the data structure before saving
        for subj, subj_data in term_data["subjects"].items():
            for course in subj_data["courses"]:
                # Remove redundant fields
                if "summary_details" in course:
                    del course["summary_details"]
                
                if "structured_details" in course:
                    # Extract any unique information from structured_details
                    # then delete the field
                    del course["structured_details"]
                
                # ... other cleanup logic ...
        
        # Add metadata
        metadata = {
            "scrape_timestamp": datetime.datetime.now().isoformat(),
            "version": "1.0",
            "course_count": sum(len(data["courses"]) for data in term_data["subjects"].values()),
            "subject_count": len(term_data["subjects"])
        }
        
        # Add metadata to output
        output_data = {
            "metadata": metadata,
            term_to_use: term_data
        }
        
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Save to JSON file
        output_file = Path(output_dir) / f"aub_courses_{term_to_use}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        duration = (datetime.datetime.now() - start_time).total_seconds()
        logger.info(f"Scraped {metadata['course_count']} courses in {duration:.2f} seconds")
        logger.info(f"Data saved to {output_file}")
        
        return str(output_file)
        
    except Exception as e:
        logger.error(f"Error during scraping: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
