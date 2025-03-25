import requests
from bs4 import BeautifulSoup
import json
import time  # optional: to delay requests if needed
import os

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
            course["title"] = a_tag.text.strip()
            course["detail_url"] = a_tag.get("href", "")
            if course["detail_url"] and not course["detail_url"].startswith("http"):
                course["detail_url"] = BASE_URL + course["detail_url"]
        else:
            course["title"] = title_row.get_text(strip=True)
        
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
        
        courses.append(course)
    
    return courses

def main():
    # Step 1: Get the initial schedule banner page.
    initial_html = get_initial_page()
    # Step 2: Parse the initial page to extract form action, hidden fields, and term options.
    form_action, hidden_fields, terms = parse_initial_page(initial_html)
    print("Available terms:")
    for term_id, term_name in terms.items():
        print(f"  {term_id}: {term_name}")
    
    # Check if the selected term exists in the options.
    if SELECTED_TERM not in terms:
        raise Exception(f"Selected term '{SELECTED_TERM}' not found among available terms.")
    
    # Process only the selected term.
    term_name = terms[SELECTED_TERM]
    print(f"\nProcessing selected term: {SELECTED_TERM} - {term_name}")
    subj_html = submit_term(form_action, hidden_fields, SELECTED_TERM)
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
        courses_html = submit_subject(SELECTED_TERM, subj, subj_hidden)
        courses = parse_subject_page_for_courses_and_details(courses_html)
        
        term_data["subjects"][subj] = {
            "subject_name": subj_name,
            "courses": courses
        }
    
    # Create output directory if it doesn't exist
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Save the data to a well-formatted JSON file
    output_file = os.path.join(output_dir, f"aub_courses_{SELECTED_TERM}.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({SELECTED_TERM: term_data}, f, indent=2, ensure_ascii=False)
    
    print(f"\nData successfully saved to {output_file}")

if __name__ == "__main__":
    main()
