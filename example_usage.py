#!/usr/bin/env python3
"""
Example usage of the Rally User Story Fetcher
"""

import json
from rally_user_story_fetcher import RallyUserStoryFetcher, lambda_handler

def example_direct_usage():
    """
    Example of using the RallyUserStoryFetcher class directly
    """
    # Initialize the fetcher
    fetcher = RallyUserStoryFetcher(
        rally_server="https://rally1.rallydev.com",
        api_key="your_api_key_here",
        workspace_ref="/workspace/12345"
    )
    
    # Fetch a user story with dependencies
    user_story_id = "US12345"
    result = fetcher.get_user_story_with_dependencies(user_story_id)
    
    print(f"Results for {user_story_id}:")
    print(json.dumps(result, indent=2, default=str))

def example_lambda_usage():
    """
    Example of using the Lambda handler function
    """
    # Simulate a Lambda event
    event = {
        "user_story_id": "US12345",
        "rally_config": {
            "server": "https://rally1.rallydev.com",
            "api_key": "your_api_key_here",
            "workspace_ref": "/workspace/12345"
        }
    }
    
    # Call the Lambda handler
    response = lambda_handler(event, None)
    
    print("Lambda Response:")
    print(json.dumps(response, indent=2))

def example_batch_processing():
    """
    Example of processing multiple user stories
    """
    user_story_ids = ["US12345", "US12346", "US12347"]
    
    fetcher = RallyUserStoryFetcher(
        rally_server="https://rally1.rallydev.com",
        api_key="your_api_key_here",
        workspace_ref="/workspace/12345"
    )
    
    results = {}
    
    for story_id in user_story_ids:
        print(f"Processing {story_id}...")
        result = fetcher.get_user_story_with_dependencies(story_id)
        results[story_id] = result
    
    print("\nBatch Processing Results:")
    print(json.dumps(results, indent=2, default=str))

def example_dependency_analysis():
    """
    Example of analyzing dependencies for a user story
    """
    fetcher = RallyUserStoryFetcher(
        rally_server="https://rally1.rallydev.com",
        api_key="your_api_key_here",
        workspace_ref="/workspace/12345"
    )
    
    user_story_id = "US12345"
    result = fetcher.get_user_story_with_dependencies(user_story_id)
    
    if result.get('user_story'):
        print(f"\nDependency Analysis for {user_story_id}:")
        print(f"Story: {result['user_story'].get('Name', 'N/A')}")
        print(f"State: {result['user_story'].get('State', 'N/A')}")
        print(f"Dependencies (Blocking): {result['total_dependencies']}")
        print(f"Successors (Blocked by this): {result['total_successors']}")
        
        if result['dependencies']:
            print("\nBlocking Dependencies:")
            for i, dep in enumerate(result['dependencies'], 1):
                story = dep['user_story']
                print(f"  {i}. {story.get('FormattedID')} - {story.get('Name')} ({story.get('State')})")
        
        if result['successors']:
            print("\nStories Blocked by This:")
            for i, succ in enumerate(result['successors'], 1):
                story = succ['user_story']
                print(f"  {i}. {story.get('FormattedID')} - {story.get('Name')} ({story.get('State')})")

if __name__ == "__main__":
    print("Rally User Story Fetcher Examples")
    print("=" * 40)
    
    # Uncomment the example you want to run
    # Note: You'll need to update the API credentials and user story IDs
    
    print("\n1. Direct Usage Example:")
    print("Update credentials and uncomment to run")
    # example_direct_usage()
    
    print("\n2. Lambda Usage Example:")
    print("Update credentials and uncomment to run")
    # example_lambda_usage()
    
    print("\n3. Batch Processing Example:")
    print("Update credentials and uncomment to run")
    # example_batch_processing()
    
    print("\n4. Dependency Analysis Example:")
    print("Update credentials and uncomment to run")
    # example_dependency_analysis()
    
    print("\nTo run these examples:")
    print("1. Update the API credentials in each function")
    print("2. Replace 'US12345' with actual user story IDs from your Rally instance")
    print("3. Uncomment the example function you want to run")
    print("4. Run: python example_usage.py")
