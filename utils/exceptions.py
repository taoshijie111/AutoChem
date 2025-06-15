"""
Custom exceptions for quantum chemistry automation
"""

class QuantumChemAutomationError(Exception):
    """Base exception for quantum chemistry automation"""
    pass

class CoordinateGenerationError(QuantumChemAutomationError):
    """Exception raised during coordinate generation"""
    pass

class CalculationError(QuantumChemAutomationError):
    """Exception raised during quantum chemistry calculations"""
    pass

class InputGenerationError(QuantumChemAutomationError):
    """Exception raised during input file generation"""
    pass

class ConfigurationError(QuantumChemAutomationError):
    """Exception raised for configuration issues"""
    pass