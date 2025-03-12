import os
from typing import Annotated, List, Dict, Any, Optional
from typing_extensions import TypedDict
import json
from dotenv import load_dotenv

try:
    load_dotenv()
except UnicodeDecodeError:
    # If UTF-8 fails, try with utf-16
    from dotenv import dotenv_values
    
    # Load with explicit encoding
    config = dotenv_values(".env", encoding="utf-16")
    
    # Set environment variables manually
    for key, value in config.items():
        os.environ[key] = value

# Install required packages if not already installed
# pip install langgraph langsmith langchain langchain_openai langchain-community langchain-pinecone pinecone

# LangGraph and LangChain imports
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
# Updated import for Pinecone
from langchain_pinecone import PineconeVectorStore
import pinecone

# Set up environment variables
# Replace these with your actual API keys
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "your_openai_api_key")
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY", "your_pinecone_api_key")
PINECONE_ENVIRONMENT = os.environ.get("PINECONE_ENVIRONMENT", "your_pinecone_environment")
LANGCHAIN_API_KEY = os.environ.get("LANGCHAIN_API_KEY", "your_langchain_api_key")

# Optional LangSmith tracing
os.environ["LANGCHAIN_API_KEY"] = LANGCHAIN_API_KEY
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "AcademicAdvisorSystem"

# Initialize OpenAI LLM
llm = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    model_name="gpt-3.5-turbo"
)

# Initialize Pinecone with the new API
pc = pinecone.Pinecone(api_key=PINECONE_API_KEY)

# Set up vector store with Pinecone
INDEX_NAME = "academic-advisor-knowledge"

# Check if index exists, if not create it
existing_indexes = [index.name for index in pc.list_indexes()]
if INDEX_NAME not in existing_indexes:
    # Create index with the newer API format
    pc.create_index(
        name=INDEX_NAME,
        dimension=1536,  # OpenAI embeddings dimension
        metric="cosine",
        spec=pinecone.ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        )
    )

# Get the index
index = pc.Index(INDEX_NAME)

# Initialize embeddings and vector store
embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
# Updated to use PineconeVectorStore instead of Pinecone
vectorstore = PineconeVectorStore(index=index, embedding=embeddings, text_key="text")

# Define the state for our graph
class State(TypedDict):
    messages: Annotated[list, add_messages]
    context: List[Dict[str, Any]]
    department: Optional[str]
    track: Optional[str]
    query_type: Optional[str]

# Build the graph
graph_builder = StateGraph(State)

# Define the nodes
def supervisor(state: State):
    """
    Main supervisor node that determines which department the query is about
    and routes to the appropriate department node
    """
    # Get the latest user message
    user_message = state["messages"][-1].content
    
    # Use the LLM to determine which department the query is about
    prompt = f"""
    Determine which engineering department this query is about:
    Query: {user_message}
    
    Choose from: Chemical, Mechanical, Civil, ECE (Electrical and Computer Engineering)
    If the query is general or doesn't specify a department, choose the most relevant one.
    
    Return only the department name without any explanation.
    """
    
    department_response = llm.invoke([{"role": "user", "content": prompt}])
    department = department_response.content.strip()
    
    # Also determine the general type of query
    query_type_prompt = f"""
    Determine what type of information the student is looking for:
    Query: {user_message}
    
    Choose from: 
    - Curriculum (courses, requirements)
    - Career (job prospects, internships)
    - Admission (requirements, process)
    - Faculty (professors, research)
    - General (overview, comparison)
    
    Return only the query type without any explanation.
    """
    
    query_type_response = llm.invoke([{"role": "user", "content": query_type_prompt}])
    query_type = query_type_response.content.strip()
    
    # Retrieve context based on department and query type
    docs = vectorstore.similarity_search(f"{department} department {query_type} {user_message}", k=3)
    context = [{"content": doc.page_content, "source": doc.metadata.get("source", "unknown")} 
               for doc in docs]
    
    return {
        "department": department,
        "query_type": query_type,
        "context": context
    }

def chemical_department(state: State):
    """Handle queries about the Chemical Engineering department"""
    user_message = state["messages"][-1].content
    query_type = state.get("query_type", "General")
    context = state.get("context", [])
    
    context_str = "\n".join([item["content"] for item in context])
    
    system_message = f"""
    You are an academic advisor for the Chemical Engineering department.
    
    The student is asking about: {query_type}
    
    Use the following information to help answer their question:
    {context_str}
    
    If you don't have specific information, provide general guidance about Chemical Engineering.
    """
    
    messages = [{"role": "system", "content": system_message}] + state["messages"]
    response = llm.invoke(messages)
    
    return {"messages": response}

def mechanical_department(state: State):
    """Handle queries about the Mechanical Engineering department"""
    user_message = state["messages"][-1].content
    query_type = state.get("query_type", "General")
    context = state.get("context", [])
    
    context_str = "\n".join([item["content"] for item in context])
    
    system_message = f"""
    You are an academic advisor for the Mechanical Engineering department.
    
    The student is asking about: {query_type}
    
    Use the following information to help answer their question:
    {context_str}
    
    If you don't have specific information, provide general guidance about Mechanical Engineering.
    """
    
    messages = [{"role": "system", "content": system_message}] + state["messages"]
    response = llm.invoke(messages)
    
    return {"messages": response}

def civil_department(state: State):
    """Handle queries about the Civil Engineering department"""
    user_message = state["messages"][-1].content
    query_type = state.get("query_type", "General")
    context = state.get("context", [])
    
    context_str = "\n".join([item["content"] for item in context])
    
    system_message = f"""
    You are an academic advisor for the Civil Engineering department.
    
    The student is asking about: {query_type}
    
    Use the following information to help answer their question:
    {context_str}
    
    If you don't have specific information, provide general guidance about Civil Engineering.
    """
    
    messages = [{"role": "system", "content": system_message}] + state["messages"]
    response = llm.invoke(messages)
    
    return {"messages": response}

def ece_department(state: State):
    """
    Handle queries about the ECE department and determine which track within ECE
    the query is about
    """
    user_message = state["messages"][-1].content
    
    # Determine which ECE track the query is about
    prompt = f"""
    Determine which track within the Electrical and Computer Engineering (ECE) department this query is about:
    Query: {user_message}
    
    Choose from: 
    - CSE (Computer Systems Engineering)
    - ECE (Electrical and Computer Engineering general)
    - CCE (Computer and Communications Engineering)
    
    If the query is general or doesn't specify a track, choose ECE.
    
    Return only the track abbreviation without any explanation.
    """
    
    track_response = llm.invoke([{"role": "user", "content": prompt}])
    track = track_response.content.strip()
    
    return {"track": track}

def cse_track(state: State):
    """Handle queries about the Computer Systems Engineering track"""
    user_message = state["messages"][-1].content
    query_type = state.get("query_type", "General")
    context = state.get("context", [])
    
    context_str = "\n".join([item["content"] for item in context])
    
    system_message = f"""
    You are an academic advisor for the Computer Systems Engineering (CSE) track within the ECE department.
    
    The student is asking about: {query_type}
    
    Use the following information to help answer their question:
    {context_str}
    
    If you don't have specific information, provide general guidance about Computer Systems Engineering.
    Focus on topics like computer architecture, operating systems, embedded systems, and hardware-software integration.
    """
    
    messages = [{"role": "system", "content": system_message}] + state["messages"]
    response = llm.invoke(messages)
    
    return {"messages": response}

def ece_track(state: State):
    """Handle queries about the general ECE track"""
    user_message = state["messages"][-1].content
    query_type = state.get("query_type", "General")
    context = state.get("context", [])
    
    context_str = "\n".join([item["content"] for item in context])
    
    system_message = f"""
    You are an academic advisor for the general Electrical and Computer Engineering (ECE) track.
    
    The student is asking about: {query_type}
    
    Use the following information to help answer their question:
    {context_str}
    
    If you don't have specific information, provide general guidance about Electrical and Computer Engineering.
    Cover both electrical engineering aspects (circuits, power systems, control systems) and computer engineering aspects.
    """
    
    messages = [{"role": "system", "content": system_message}] + state["messages"]
    response = llm.invoke(messages)
    
    return {"messages": response}

def cce_track(state: State):
    """Handle queries about the Computer and Communications Engineering track"""
    user_message = state["messages"][-1].content
    query_type = state.get("query_type", "General")
    context = state.get("context", [])
    
    context_str = "\n".join([item["content"] for item in context])
    
    system_message = f"""
    You are an academic advisor for the Computer and Communications Engineering (CCE) track within the ECE department.
    
    The student is asking about: {query_type}
    
    Use the following information to help answer their question:
    {context_str}
    
    If you don't have specific information, provide general guidance about Computer and Communications Engineering.
    Focus on topics like networking, telecommunications, signal processing, and wireless communications.
    """
    
    messages = [{"role": "system", "content": system_message}] + state["messages"]
    response = llm.invoke(messages)
    
    return {"messages": response}

# Add nodes to the graph
graph_builder.add_node("supervisor", supervisor)
graph_builder.add_node("chemical_department", chemical_department)
graph_builder.add_node("mechanical_department", mechanical_department)
graph_builder.add_node("civil_department", civil_department)
graph_builder.add_node("ece_department", ece_department)
graph_builder.add_node("cse_track", cse_track)
graph_builder.add_node("ece_track", ece_track)
graph_builder.add_node("cce_track", cce_track)

# Define the router function for department selection
def route_to_department(state: State):
    department = state.get("department", "").lower()
    
    if "chemical" in department:
        return "chemical_department"
    elif "mechanical" in department:
        return "mechanical_department"
    elif "civil" in department:
        return "civil_department"
    elif "ece" in department or "electrical" in department or "computer" in department:
        return "ece_department"
    else:
        # Default to ECE if unclear
        return "ece_department"

# Define the router function for ECE track selection
def route_to_ece_track(state: State):
    track = state.get("track", "").upper()
    
    if "CSE" in track:
        return "cse_track"
    elif "CCE" in track:
        return "cce_track"
    else:
        # Default to general ECE track
        return "ece_track"

# Add edges to the graph
graph_builder.add_edge(START, "supervisor")
graph_builder.add_conditional_edges(
    "supervisor",
    route_to_department,
    {
        "chemical_department": "chemical_department",
        "mechanical_department": "mechanical_department",
        "civil_department": "civil_department",
        "ece_department": "ece_department"
    }
)

graph_builder.add_conditional_edges(
    "ece_department",
    route_to_ece_track,
    {
        "cse_track": "cse_track",
        "ece_track": "ece_track",
        "cce_track": "cce_track"
    }
)

# Connect all final nodes to END
graph_builder.add_edge("chemical_department", END)
graph_builder.add_edge("mechanical_department", END)
graph_builder.add_edge("civil_department", END)
graph_builder.add_edge("cse_track", END)
graph_builder.add_edge("ece_track", END)
graph_builder.add_edge("cce_track", END)

# Compile the graph
graph = graph_builder.compile()

# Function to add department and track information to Pinecone
def populate_academic_knowledge():
    """Add academic department and track information to Pinecone"""
    
    # Department information
    department_info = [
        {
            "content": """
            Chemical Engineering focuses on the application of chemistry, physics, biology, and mathematics to design and develop processes that convert raw materials into valuable products.
            Curriculum: Core courses include Thermodynamics, Fluid Mechanics, Heat and Mass Transfer, Reaction Engineering, and Process Design.
            Career prospects: Chemical engineers work in industries such as petroleum, pharmaceuticals, food processing, environmental engineering, and materials science.
            Admission requirements: Strong background in chemistry, physics, and mathematics is recommended.
            """,
            "metadata": {"source": "department_info", "department": "Chemical", "type": "overview"}
        },
        {
            "content": """
            Mechanical Engineering is one of the broadest engineering disciplines, dealing with the design, manufacturing, and maintenance of mechanical systems.
            Curriculum: Core courses include Statics, Dynamics, Thermodynamics, Fluid Mechanics, Materials Science, and Machine Design.
            Career prospects: Mechanical engineers work in automotive, aerospace, energy, manufacturing, and robotics industries.
            Admission requirements: Strong background in physics and mathematics is recommended.
            """,
            "metadata": {"source": "department_info", "department": "Mechanical", "type": "overview"}
        },
        {
            "content": """
            Civil Engineering involves the design, construction, and maintenance of the physical and naturally built environment.
            Curriculum: Core courses include Structural Analysis, Geotechnical Engineering, Transportation Engineering, Environmental Engineering, and Construction Management.
            Career prospects: Civil engineers work in construction, transportation, water resources, urban planning, and environmental sectors.
            Admission requirements: Strong background in physics and mathematics is recommended.
            """,
            "metadata": {"source": "department_info", "department": "Civil", "type": "overview"}
        },
        {
            "content": """
            Electrical and Computer Engineering (ECE) combines the study of electrical systems and computer systems.
            The department offers three main tracks: Computer Systems Engineering (CSE), general Electrical and Computer Engineering (ECE), and Computer and Communications Engineering (CCE).
            Curriculum: Core courses across all tracks include Circuit Analysis, Digital Logic, Signals and Systems, and Electromagnetics.
            Career prospects: ECE graduates work in telecommunications, power systems, computer hardware/software, robotics, and semiconductor industries.
            Admission requirements: Strong background in physics, mathematics, and basic programming is recommended.
            """,
            "metadata": {"source": "department_info", "department": "ECE", "type": "overview"}
        }
    ]
    
    # ECE Track information
    ece_track_info = [
        {
            "content": """
            Computer Systems Engineering (CSE) track focuses on the design and development of computer hardware and software systems.
            Curriculum: Specialized courses include Computer Architecture, Operating Systems, Embedded Systems, VLSI Design, and Hardware-Software Co-design.
            Career prospects: CSE graduates work in computer hardware design, embedded systems, IoT devices, and system integration.
            """,
            "metadata": {"source": "track_info", "department": "ECE", "track": "CSE", "type": "overview"}
        },
        {
            "content": """
            The general Electrical and Computer Engineering (ECE) track provides a balanced education in both electrical engineering and computer engineering.
            Curriculum: Specialized courses include Power Systems, Control Systems, Digital Signal Processing, Computer Networks, and Electronics.
            Career prospects: General ECE graduates have versatile career options in power distribution, control systems, electronics design, and computing systems.
            """,
            "metadata": {"source": "track_info", "department": "ECE", "track": "ECE", "type": "overview"}
        },
        {
            "content": """
            Computer and Communications Engineering (CCE) track focuses on the design and implementation of communication systems and networks.
            Curriculum: Specialized courses include Digital Communications, Wireless Networks, Information Theory, Network Security, and Mobile Computing.
            Career prospects: CCE graduates work in telecommunications, network infrastructure, wireless technologies, and data communications.
            """,
            "metadata": {"source": "track_info", "department": "ECE", "track": "CCE", "type": "overview"}
        }
    ]
    
    # Add all information to Pinecone
    all_docs = []
    all_metadata = []
    
    for info in department_info:
        all_docs.append(info["content"])
        all_metadata.append(info["metadata"])
    
    for info in ece_track_info:
        all_docs.append(info["content"])
        all_metadata.append(info["metadata"])
    
    # Create Document objects and add to vectorstore
    documents = [Document(page_content=text, metadata=meta) 
                for text, meta in zip(all_docs, all_metadata)]
    
    vectorstore.add_documents(documents)
    print(f"Added {len(documents)} academic information documents to Pinecone")

# Main chat loop
def main():
    # Uncomment to populate the vector store with academic information
    # populate_academic_knowledge()
    
    print("Academic Advisor System initialized. Type 'quit' or 'q' to exit.")
    print("Ask questions about Chemical, Mechanical, Civil Engineering departments, or ECE tracks (CSE, ECE, CCE).")
    
    while True:
        user_input = input("\nStudent: ")
        if user_input.lower() in ["quit", "q"]:
            print("Goodbye!")
            break
        
        # Initialize state with empty values
        initial_state = {
            "messages": [{"role": "user", "content": user_input}],
            "context": [],
            "department": None,
            "track": None,
            "query_type": None
        }
        
        # Process through the graph
        for event in graph.stream(initial_state):
            # Print intermediate steps for debugging (optional)
            # print(f"Event: {event.keys()}")
            
            # Only print the final assistant response
            if any(node in event.keys() for node in ["chemical_department", "mechanical_department", "civil_department", "cse_track", "ece_track", "cce_track"]):
                for node in ["chemical_department", "mechanical_department", "civil_department", "cse_track", "ece_track", "cce_track"]:
                    if node in event.keys():
                        assistant_message = event[node]["messages"]
                        print(f"Advisor: {assistant_message.content}")

if __name__ == "__main__":
    main()