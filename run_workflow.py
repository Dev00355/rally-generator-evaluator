#!/usr/bin/env python3
"""
Main script to run the Rally Code Generator Workflow
"""

import sys
import argparse
from config import Config
from langgraph_code_generator import RallyCodeGeneratorWorkflow

def main():
    """Main function to run the workflow"""
    parser = argparse.ArgumentParser(description="Generate code from Rally user stories using LangGraph")
    parser.add_argument("user_story_id", help="Rally User Story ID (e.g., US12345)")
    parser.add_argument("--max-iterations", type=int, default=3, help="Maximum number of code generation iterations")
    parser.add_argument("--check-config", action="store_true", help="Check configuration and exit")
    
    args = parser.parse_args()
    
    # Check configuration
    if args.check_config:
        Config.print_config_status()
        return
    
    # Validate configuration
    validation = Config.validate_config()
    if not validation["valid"]:
        print("❌ Configuration validation failed!")
        Config.print_config_status()
        sys.exit(1)
    
    print("🚀 Starting Rally Code Generator Workflow")
    print(f"📋 User Story ID: {args.user_story_id}")
    print(f"🔄 Max Iterations: {args.max_iterations}")
    print("-" * 50)
    
    try:
        # Initialize workflow
        workflow = RallyCodeGeneratorWorkflow(
            openai_api_key=Config.OPENAI_API_KEY,
            rally_config=Config.get_rally_config()
        )
        
        # Run workflow
        result = workflow.run_workflow(
            user_story_id=args.user_story_id,
            max_iterations=args.max_iterations
        )
        
        if result.get('error'):
            print(f"❌ Workflow failed: {result['error']}")
            sys.exit(1)
        else:
            print("\n🎉 Workflow completed successfully!")
            
            # Print summary
            evaluation_result = result.get('evaluation_result', {})
            print(f"📊 Final Evaluation Score: {evaluation_result.get('match_score', 0)}%")
            print(f"🔄 Total Iterations: {result.get('iteration_count', 0)}")
            print(f"📎 Code Attachment Created: {result.get('attachment_created', False)}")
            
            if evaluation_result.get('assessment'):
                print(f"📝 Assessment: {evaluation_result['assessment']}")
    
    except KeyboardInterrupt:
        print("\n⚠️ Workflow interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
