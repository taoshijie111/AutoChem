"""
Configuration management for quantum chemistry automation
"""
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

from utils.exceptions import ConfigurationError

logger = logging.getLogger('Configuration Manager')


class ConfigManager:
    """Manages configuration loading and validation"""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize configuration manager
        
        Args:
            config_path: Path to configuration YAML file
        """
        self.config_path = config_path
        self.config = {}
        
        if config_path:
            self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from YAML file
        
        Returns:
            Configuration dictionary
        """
        if not self.config_path or not self.config_path.exists():
            raise ConfigurationError(f"Configuration file not found: {self.config_path}")
        
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            
            logger.info(f"Configuration loaded from {self.config_path}")
            return self.config
            
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Error parsing YAML configuration: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error loading configuration: {e}")
    
    def get_xtb_config(self) -> Dict[str, Any]:
        """
        Get XTB-specific configuration
        
        Returns:
            XTB configuration dictionary
        """
        if 'xtb' not in self.config:
            raise ConfigurationError("XTB configuration not found in config file")
        
        xtb_config = self.config['xtb']
        
        # Validate required fields
        if 'command' not in xtb_config:
            raise ConfigurationError("XTB commands not specified in configuration")
        
        commands = xtb_config['command']
        if not isinstance(commands, list) or not commands:
            raise ConfigurationError("XTB commands must be a non-empty list")
        
        # Validate command templates
        for i, cmd in enumerate(commands):
            if not isinstance(cmd, str):
                raise ConfigurationError(f"XTB command {i+1} must be a string")
            if '{}' not in cmd:
                logger.warning(f"XTB command {i+1} does not contain placeholder '{{}}': {cmd}")
        
        logger.info(f"XTB configuration validated: {len(commands)} commands found")
        return xtb_config
    
    def has_xtb_config(self) -> bool:
        """Check if XTB configuration is present"""
        return 'xtb' in self.config
    
    def get_config(self) -> Dict[str, Any]:
        """Get full configuration"""
        return self.config
    
    @staticmethod
    def create_sample_config(output_path: Path) -> None:
        """
        Create a sample configuration file
        
        Args:
            output_path: Path where to save the sample config
        """
        sample_config = {
            'xtb': {
                'command': [
                    'xtb {} --opt normal --gbsa benzene',
                    'xtb xtbopt.xyz --vipea --gbsa benzene'
                ]
            }
        }
        
        try:
            with open(output_path, 'w') as f:
                yaml.dump(sample_config, f, default_flow_style=False, indent=2)
            
            logger.info(f"Sample configuration created at {output_path}")
            
        except Exception as e:
            raise ConfigurationError(f"Failed to create sample config: {e}")
        