from langchain.schema import Document
from app.db.vector_store import vectorstore

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

if __name__ == "__main__":
    populate_academic_knowledge()
    print("Vector store populated successfully!")
