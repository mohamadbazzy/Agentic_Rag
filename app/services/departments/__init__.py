# Import department handlers
from .chemical import chemical_department
from .civil import civil_department
from .ece import ece_department
from .mechanical import mechanical_department
from .Industrial import industrial_department

# Export all department handlers
__all__ = [
    "chemical_department",
    "civil_department", 
    "ece_department",
    "mechanical_department",
    "industrial_department"
]
