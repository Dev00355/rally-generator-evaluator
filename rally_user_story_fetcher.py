import json
import os
import requests
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RallyUserStoryFetcher:
    """
    A class to fetch user stories and their dependencies from Rally (CA Agile Central)
    """
    
    def __init__(self, rally_server: str, api_key: str, workspace_ref: str):
        """
        Initialize the Rally client
        
        Args:
            rally_server: Rally server URL (e.g., 'https://rally1.rallydev.com')
            api_key: Rally API key for authentication
            workspace_ref: Rally workspace reference
        """
        self.rally_server = rally_server.rstrip('/')
        self.api_key = api_key
        self.workspace_ref = workspace_ref
        self.base_url = f"{self.rally_server}/slm/webservice/v2.0"
        self.headers = {
            'Content-Type': 'application/json',
            'ZSESSIONID': api_key
        }
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Make a request to Rally API
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            JSON response from Rally API
        """
        url = f"{self.base_url}/{endpoint}"
        
        default_params = {
            'workspace': self.workspace_ref,
            'fetch': 'true'
        }
        
        if params:
            default_params.update(params)
        
        try:
            response = requests.get(url, headers=self.headers, params=default_params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making request to Rally API: {e}")
            raise
    
    def get_user_story_by_formatted_id(self, formatted_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user story by FormattedID (e.g., US12345)
        
        Args:
            formatted_id: The FormattedID of the user story
            
        Returns:
            User story data or None if not found
        """
        try:
            params = {
                'query': f'(FormattedID = "{formatted_id}")',
                'fetch': 'FormattedID,Name,Description,State,PlanEstimate,Owner,Project,Dependencies,Predecessors,Successors,Children,Parent'
            }
            
            response = self._make_request('hierarchicalrequirement', params)
            
            if response.get('QueryResult', {}).get('TotalResultCount', 0) > 0:
                return response['QueryResult']['Results'][0]
            else:
                logger.warning(f"User story {formatted_id} not found")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching user story {formatted_id}: {e}")
            raise
    
    def get_dependencies(self, user_story_ref: str) -> List[Dict[str, Any]]:
        """
        Get dependencies for a user story
        
        Args:
            user_story_ref: Reference URL of the user story
            
        Returns:
            List of dependency objects
        """
        try:
            # Extract object ID from reference
            object_id = user_story_ref.split('/')[-1]
            
            # Get predecessors (dependencies)
            params = {
                'query': f'(Successor = "{user_story_ref}")',
                'fetch': 'Predecessor,Successor,Description'
            }
            
            response = self._make_request('dependency', params)
            dependencies = []
            
            for dependency in response.get('QueryResult', {}).get('Results', []):
                predecessor_ref = dependency.get('Predecessor', {}).get('_ref')
                if predecessor_ref:
                    # Get the actual user story details
                    predecessor_id = predecessor_ref.split('/')[-1]
                    predecessor_params = {
                        'fetch': 'FormattedID,Name,Description,State,PlanEstimate,Owner,Project'
                    }
                    predecessor_response = self._make_request(f'hierarchicalrequirement/{predecessor_id}', predecessor_params)
                    
                    if predecessor_response.get('HierarchicalRequirement'):
                        dependencies.append({
                            'dependency_info': dependency,
                            'user_story': predecessor_response['HierarchicalRequirement']
                        })
            
            return dependencies
            
        except Exception as e:
            logger.error(f"Error fetching dependencies for {user_story_ref}: {e}")
            return []
    
    def get_successors(self, user_story_ref: str) -> List[Dict[str, Any]]:
        """
        Get successors (stories that depend on this one) for a user story
        
        Args:
            user_story_ref: Reference URL of the user story
            
        Returns:
            List of successor objects
        """
        try:
            # Get successors (stories that depend on this one)
            params = {
                'query': f'(Predecessor = "{user_story_ref}")',
                'fetch': 'Predecessor,Successor,Description'
            }
            
            response = self._make_request('dependency', params)
            successors = []
            
            for dependency in response.get('QueryResult', {}).get('Results', []):
                successor_ref = dependency.get('Successor', {}).get('_ref')
                if successor_ref:
                    # Get the actual user story details
                    successor_id = successor_ref.split('/')[-1]
                    successor_params = {
                        'fetch': 'FormattedID,Name,Description,State,PlanEstimate,Owner,Project'
                    }
                    successor_response = self._make_request(f'hierarchicalrequirement/{successor_id}', successor_params)
                    
                    if successor_response.get('HierarchicalRequirement'):
                        successors.append({
                            'dependency_info': dependency,
                            'user_story': successor_response['HierarchicalRequirement']
                        })
            
            return successors
            
        except Exception as e:
            logger.error(f"Error fetching successors for {user_story_ref}: {e}")
            return []
    
    def get_user_story_with_dependencies(self, formatted_id: str) -> Dict[str, Any]:
        """
        Get user story along with all its dependencies and successors
        
        Args:
            formatted_id: The FormattedID of the user story (e.g., US12345)
            
        Returns:
            Complete user story data with dependencies
        """
        try:
            # Get the main user story
            user_story = self.get_user_story_by_formatted_id(formatted_id)
            
            if not user_story:
                return {
                    'error': f'User story {formatted_id} not found',
                    'user_story': None,
                    'dependencies': [],
                    'successors': []
                }
            
            user_story_ref = user_story.get('_ref')
            
            # Get dependencies (predecessors)
            dependencies = self.get_dependencies(user_story_ref)
            
            # Get successors
            successors = self.get_successors(user_story_ref)
            
            return {
                'user_story': user_story,
                'dependencies': dependencies,
                'successors': successors,
                'total_dependencies': len(dependencies),
                'total_successors': len(successors)
            }
            
        except Exception as e:
            logger.error(f"Error fetching user story with dependencies: {e}")
            return {
                'error': str(e),
                'user_story': None,
                'dependencies': [],
                'successors': []
            }


def lambda_handler(event, context):
    """
    AWS Lambda handler function to fetch user story with dependencies
    
    Expected event structure:
    {
        "user_story_id": "US12345",
        "rally_config": {
            "server": "https://rally1.rallydev.com",
            "api_key": "your_api_key",
            "workspace_ref": "/workspace/12345"
        }
    }
    """
    try:
        # Extract parameters from event
        user_story_id = event.get('user_story_id')
        rally_config = event.get('rally_config', {})
        
        # Validate required parameters
        if not user_story_id:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'user_story_id is required'
                })
            }
        
        # Get Rally configuration from environment variables or event
        rally_server = rally_config.get('server') or os.environ.get('RALLY_SERVER')
        api_key = rally_config.get('api_key') or os.environ.get('RALLY_API_KEY')
        workspace_ref = rally_config.get('workspace_ref') or os.environ.get('RALLY_WORKSPACE_REF')
        
        if not all([rally_server, api_key, workspace_ref]):
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Rally configuration is incomplete. Required: server, api_key, workspace_ref'
                })
            }
        
        # Initialize Rally fetcher
        fetcher = RallyUserStoryFetcher(rally_server, api_key, workspace_ref)
        
        # Fetch user story with dependencies
        result = fetcher.get_user_story_with_dependencies(user_story_id)
        
        return {
            'statusCode': 200,
            'body': json.dumps(result, default=str),
            'headers': {
                'Content-Type': 'application/json'
            }
        }
        
    except Exception as e:
        logger.error(f"Lambda execution error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'Internal server error: {str(e)}'
            })
        }


# For local testing
if __name__ == "__main__":
    # Example usage for local testing
    test_event = {
        "user_story_id": "US12345",
        "rally_config": {
            "server": "https://rally1.rallydev.com",
            "api_key": "your_api_key_here",
            "workspace_ref": "/workspace/12345"
        }
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))
