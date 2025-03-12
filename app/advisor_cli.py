from app.services.advisor import process_query

def main():
    """Command-line interface for the academic advisor system"""
    print("Academic Advisor System initialized. Type 'quit' or 'q' to exit.")
    print("Ask questions about Chemical, Mechanical, Civil Engineering departments, or ECE tracks (CSE, ECE, CCE).")
    
    while True:
        user_input = input("\nStudent: ")
        if user_input.lower() in ["quit", "q"]:
            print("Goodbye!")
            break
        
        result = process_query(user_input)
        print(f"Advisor: {result}")

if __name__ == "__main__":
    main()
