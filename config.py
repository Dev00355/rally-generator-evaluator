#!/usr/bin/env python3
"""
Configuration file for Rally Code Generator Workflow
"""

import os
from typing import Dict, Any

class Config:
    """Configuration class for the Rally Code Generator"""
    
    # Rally Configuration
    RALLY_SERVER = os.getenv("RALLY_SERVER", "https://rally1.rallydev.com")
    RALLY_API_KEY = os.getenv("RALLY_API_KEY")
    RALLY_WORKSPACE_REF = os.getenv("RALLY_WORKSPACE_REF")
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
    OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.1"))
    
    # Workflow Configuration
    MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "3"))
    EVALUATION_THRESHOLD = float(os.getenv("EVALUATION_THRESHOLD", "70.0"))
    
    # File Configuration
    OUTPUT_DIRECTORY = os.getenv("OUTPUT_DIRECTORY", "/tmp")
    
    @classmethod
    def get_rally_config(cls) -> Dict[str, str]:
        """Get Rally configuration as dictionary"""
        return {
            "server": cls.RALLY_SERVER,
            "api_key": cls.RALLY_API_KEY,
            "workspace_ref": cls.RALLY_WORKSPACE_REF
        }
    
    @classmethod
    def validate_config(cls) -> Dict[str, Any]:
        """Validate configuration and return status"""
        missing_configs = []
        
        if not cls.RALLY_API_KEY:
            missing_configs.append("RALLY_API_KEY")
        
        if not cls.RALLY_WORKSPACE_REF:
            missing_configs.append("RALLY_WORKSPACE_REF")
        
        if not cls.OPENAI_API_KEY:
            missing_configs.append("OPENAI_API_KEY")
        
        return {
            "valid": len(missing_configs) == 0,
            "missing_configs": missing_configs,
            "rally_config": cls.get_rally_config()
        }
    
    @classmethod
    def print_config_status(cls):
        """Print current configuration status"""
        validation = cls.validate_config()
        
        print("Configuration Status:")
        print("=" * 30)
        print(f"Rally Server: {cls.RALLY_SERVER}")
        print(f"Rally API Key: {'✅ Set' if cls.RALLY_API_KEY else '❌ Missing'}")
        print(f"Rally Workspace: {'✅ Set' if cls.RALLY_WORKSPACE_REF else '❌ Missing'}")
        print(f"OpenAI API Key: {'✅ Set' if cls.OPENAI_API_KEY else '❌ Missing'}")
        print(f"OpenAI Model: {cls.OPENAI_MODEL}")
        print(f"Max Iterations: {cls.MAX_ITERATIONS}")
        print(f"Evaluation Threshold: {cls.EVALUATION_THRESHOLD}%")
        print(f"Output Directory: {cls.OUTPUT_DIRECTORY}")
        
        if not validation["valid"]:
            print(f"\n❌ Missing configurations: {', '.join(validation['missing_configs'])}")
            print("\nPlease set the following environment variables:")
            for config in validation["missing_configs"]:
                print(f"   export {config}=your_value_here")
        else:
            print("\n✅ All configurations are set!")

if __name__ == "__main__":
    Config.print_config_status()
