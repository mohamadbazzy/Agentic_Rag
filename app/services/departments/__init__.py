# Import department handlers
from .chemical import chemical_department
from .civil import civil_department
from .ece import ece_department
from .mechanical import mechanical_department
from .msfea_advisor import msfea_advisor
from .Industrial import industrial_department

# Export all department handlers
__all__ = [
    "chemical_department",
    "civil_department", 
    "ece_department",
    "mechanical_department",
    "msfea_advisor",
    "industrial_department"
]
