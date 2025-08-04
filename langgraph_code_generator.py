#!/usr/bin/env python3
"""
LangGraph workflow for automated code generation from Rally user stories
Requires Python 3.12+
"""

import sys

# Ensure Python 3.12+ is being used
if sys.version_info < (3, 12):
    raise RuntimeError("This application requires Python 3.12 or higher. "
                      f"Current version: {sys.version_info.major}.{sys.version_info.minor}")

import json
import os
import tempfile
from typing import Dict, Any, List, TypedDict, Annotated
from datetime import datetime
from dataclasses import dataclass
from enum import Enum, auto
import logging

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser

from rally_user_story_fetcher import RallyUserStoryFetcher

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """Workflow execution status using modern Python 3.12 enum features"""
    INITIALIZING = auto()
    FETCHING_STORY = auto()
    GENERATING_CODE = auto()
    EVALUATING_CODE = auto()
    CREATING_ATTACHMENT = auto()
    COMPLETED = auto()
    FAILED = auto()


@dataclass(frozen=True, slots=True)
class EvaluationResult:
    """Evaluation result with Python 3.12 dataclass features"""
    match_score: float
    issues: List[Dict[str, str]]
    suggestions: List[Dict[str, str]]
    assessment: str
    meets_threshold: bool
    python_3_12_compliance: bool

# State definition for the workflow
class WorkflowState(TypedDict):
    messages: Annotated[List, add_messages]
    user_story_id: str
    rally_config: Dict[str, str]
    user_story_data: Dict[str, Any]
    generated_code: str
    evaluation_result: EvaluationResult | None
    iteration_count: int
    max_iterations: int
    final_code: str
    attachment_created: bool
    status: WorkflowStatus

class RallyCodeGeneratorWorkflow:
    """
    LangGraph workflow for generating code from Rally user stories
    """
    
    def __init__(self, openai_api_key: str, rally_config: Dict[str, str]) -> None:
        """
        Initialize the workflow
        
        Args:
            openai_api_key: OpenAI API key for LLM
            rally_config: Rally configuration dictionary
        """
        if not openai_api_key or not all(rally_config.values()):
            raise ValueError("OpenAI API key and complete Rally configuration are required")
        
        self.llm = ChatOpenAI(
            api_key=openai_api_key,
            model="gpt-4-turbo-preview",
            temperature=0.1
        )
        
        self.rally_config = rally_config
        self.rally_fetcher = RallyUserStoryFetcher(
            rally_server=rally_config['server'],
            api_key=rally_config['api_key'],
            workspace_ref=rally_config['workspace_ref']
        )
        
        # Create the workflow graph
        self.workflow = self._create_workflow()
        logger.info("RallyCodeGeneratorWorkflow initialized successfully")
    
    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow"""
        workflow = StateGraph(WorkflowState)
        
        # Add nodes
        workflow.add_node("fetch_user_story", self.fetch_user_story_node)
        workflow.add_node("generate_code", self.generate_code_node)
        workflow.add_node("evaluate_code", self.evaluate_code_node)
        workflow.add_node("create_attachment", self.create_attachment_node)
        
        # Define the flow
        workflow.set_entry_point("fetch_user_story")
        workflow.add_edge("fetch_user_story", "generate_code")
        workflow.add_edge("generate_code", "evaluate_code")
        workflow.add_conditional_edges(
            "evaluate_code",
            self.should_regenerate,
            {
                "regenerate": "generate_code",
                "create_attachment": "create_attachment",
                "end": END
            }
        )
        workflow.add_edge("create_attachment", END)
        
        return workflow.compile()
    
    def fetch_user_story_node(self, state: WorkflowState) -> WorkflowState:
        """
        Node 1: Fetch user story from Rally
        """
        logger.info(f"🔍 Fetching user story: {state['user_story_id']}")
        state['status'] = WorkflowStatus.FETCHING_STORY
        
        try:
            user_story_data = self.rally_fetcher.get_user_story_with_dependencies(
                state['user_story_id']
            )
            
            match user_story_data:
                case {'error': error_msg}:
                    raise Exception(f"Failed to fetch user story: {error_msg}")
                case {'user_story': story} if story:
                    state['user_story_data'] = user_story_data
                    state['messages'].append(
                        AIMessage(content=f"Successfully fetched user story {state['user_story_id']}")
                    )
                    logger.info(f"✅ User story fetched: {story.get('Name', 'N/A')}")
                case _:
                    raise Exception("Invalid user story data received")
            
        except Exception as e:
            logger.error(f"❌ Error fetching user story: {e}")
            state['status'] = WorkflowStatus.FAILED
            state['messages'].append(
                AIMessage(content=f"Error fetching user story: {str(e)}")
            )
        
        return state
    
    def generate_code_node(self, state: WorkflowState) -> WorkflowState:
        """
        Node 2: Generate code based on user story
        """
        iteration = state.get('iteration_count', 0) + 1
        logger.info(f"🔧 Generating code (iteration {iteration})")
        state['status'] = WorkflowStatus.GENERATING_CODE
        
        user_story = state['user_story_data']['user_story']
        dependencies = state['user_story_data']['dependencies']
        
        # Create prompt for code generation
        code_generation_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert software developer specializing in Python 3.12+. Generate high-quality, production-ready code based on the user story requirements.

Requirements:
1. Use modern Python 3.12+ features and syntax (type hints, match statements, f-strings, etc.)
2. Write clean, well-documented code with comprehensive docstrings
3. Include proper error handling with specific exception types
4. Follow PEP 8 and modern Python best practices
5. Use type hints extensively with proper generic types
6. Include unit tests using pytest where appropriate
7. Make the code modular, maintainable, and scalable
8. Use dataclasses, enums, and modern Python patterns
9. Include logging with structured output
10. Consider the dependencies mentioned in the user story

If this is a regeneration request, improve upon the previous attempt based on the evaluation feedback.
Generate code that leverages Python 3.12 features like:
- Enhanced type system with generics
- Pattern matching with match/case
- Improved error messages and debugging
- Modern async/await patterns where applicable
- Dataclasses and Pydantic models for data validation"""),
            ("human", """
User Story: {story_name}
Description: {story_description}
Acceptance Criteria: {story_details}
Dependencies: {dependencies}

{regeneration_feedback}

Generate complete, runnable Python 3.12+ code for this user story. Include all necessary imports, classes, functions, type hints, and comprehensive documentation.
Structure the code with proper modules and follow modern Python architecture patterns.
""")
        ])
        
        # Prepare regeneration feedback if this is not the first iteration
        regeneration_feedback = ""
        if state.get('evaluation_result') and state.get('iteration_count', 0) > 0:
            eval_result = state['evaluation_result']
            regeneration_feedback = f"""
Previous Evaluation Feedback:
- Match Score: {eval_result.get('match_score', 0)}%
- Issues Found: {eval_result.get('issues', [])}
- Suggestions: {eval_result.get('suggestions', [])}

Please address these issues in the regenerated code.
"""
        
        try:
            # Generate code
            chain = code_generation_prompt | self.llm | StrOutputParser()
            
            generated_code = chain.invoke({
                "story_name": user_story.get('Name', 'N/A'),
                "story_description": user_story.get('Description', 'N/A'),
                "story_details": json.dumps(user_story, indent=2),
                "dependencies": json.dumps(dependencies, indent=2),
                "regeneration_feedback": regeneration_feedback
            })
            
            state['generated_code'] = generated_code
            state['iteration_count'] = state.get('iteration_count', 0) + 1
            
            print(f"✅ Code generated ({len(generated_code)} characters)")
            
        except Exception as e:
            print(f"❌ Error generating code: {e}")
            state['messages'].append(
                AIMessage(content=f"Error generating code: {str(e)}")
            )
        
        return state
    
    def evaluate_code_node(self, state: WorkflowState) -> WorkflowState:
        """
        Node 3: Evaluate generated code against user story requirements
        """
        logger.info("🔍 Evaluating generated code...")
        state['status'] = WorkflowStatus.EVALUATING_CODE
        
        user_story = state['user_story_data']['user_story']
        generated_code = state['generated_code']
        
        # Create evaluation prompt
        evaluation_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a senior code reviewer and requirements analyst specializing in Python 3.12+. Evaluate the generated code against the user story requirements.

Evaluation Criteria:
1. **Requirement Coverage** (30%) - How well does the code meet the user story requirements?
2. **Code Quality** (25%) - Modern Python 3.12+ features, type hints, documentation, structure
3. **Best Practices** (20%) - PEP 8, error handling, logging, testing
4. **Functionality** (15%) - Logical correctness and expected behavior
5. **Maintainability** (10%) - Modularity, readability, scalability

Python 3.12+ Specific Checks:
- Proper use of type hints and generics
- Modern syntax (f-strings, match/case, walrus operator)
- Dataclasses or Pydantic models for data structures
- Appropriate use of async/await patterns
- Comprehensive error handling with specific exceptions
- Structured logging implementation
- Unit tests with pytest

Provide a detailed evaluation with:
1. Match score (0-100%) - weighted average of all criteria
2. List of specific issues found with severity levels
3. List of actionable suggestions for improvement
4. Overall assessment with strengths and weaknesses

Return your evaluation as JSON with the following structure:
{
    "match_score": <number>,
    "issues": [{"severity": "high|medium|low", "description": "<issue>"}],
    "suggestions": [{"priority": "high|medium|low", "description": "<suggestion>"}],
    "assessment": "<detailed overall assessment>",
    "meets_threshold": <boolean - true if score >= 70%>,
    "python_3_12_compliance": <boolean - true if uses modern Python features>
}"""),
            ("human", """
User Story: {story_name}
Description: {story_description}
Requirements: {story_details}

Generated Code:
{generated_code}

Evaluate this Python code against the user story requirements and modern Python 3.12+ standards.
""")
        ])
        
        try:
            # Evaluate code
            chain = evaluation_prompt | self.llm | JsonOutputParser()
            
            evaluation_data = chain.invoke({
                "story_name": user_story.get('Name', 'N/A'),
                "story_description": user_story.get('Description', 'N/A'),
                "story_details": json.dumps(user_story, indent=2),
                "generated_code": generated_code
            })
            
            # Create EvaluationResult dataclass instance
            evaluation_result = EvaluationResult(
                match_score=evaluation_data.get('match_score', 0),
                issues=evaluation_data.get('issues', []),
                suggestions=evaluation_data.get('suggestions', []),
                assessment=evaluation_data.get('assessment', 'No assessment provided'),
                meets_threshold=evaluation_data.get('meets_threshold', False),
                python_3_12_compliance=evaluation_data.get('python_3_12_compliance', False)
            )
            
            state['evaluation_result'] = evaluation_result
            
            logger.info(f"📊 Evaluation complete: {evaluation_result.match_score}% match")
            logger.info(f"🎯 Meets threshold (70%): {evaluation_result.meets_threshold}")
            logger.info(f"🐍 Python 3.12+ compliant: {evaluation_result.python_3_12_compliance}")
            
        except Exception as e:
            logger.error(f"❌ Error evaluating code: {e}")
            # Create failed evaluation result
            evaluation_result = EvaluationResult(
                match_score=0,
                issues=[{"severity": "high", "description": f"Evaluation error: {str(e)}"}],
                suggestions=[],
                assessment="Failed to evaluate",
                meets_threshold=False,
                python_3_12_compliance=False
            )
            state['evaluation_result'] = evaluation_result
        
        return state
    
    def should_regenerate(self, state: WorkflowState) -> str:
        """
        Conditional edge: Decide whether to regenerate code or create attachment
        """
        evaluation_result = state.get('evaluation_result')
        iteration_count = state.get('iteration_count', 0)
        max_iterations = state.get('max_iterations', 3)
        
        if not evaluation_result:
            logger.warning("No evaluation result found, ending workflow")
            return "end"
        
        match (evaluation_result.meets_threshold, iteration_count >= max_iterations):
            case (True, _):
                logger.info("✅ Code meets requirements threshold (≥70%)")
                return "create_attachment"
            case (False, True):
                logger.warning(f"⚠️ Max iterations ({max_iterations}) reached. Proceeding with current code.")
                return "create_attachment"
            case (False, False):
                logger.info(f"🔄 Code needs improvement. Regenerating... (iteration {iteration_count + 1})")
                return "regenerate"
    
    def create_attachment_node(self, state: WorkflowState) -> WorkflowState:
        """
        Node 4: Create code attachment and attach to Rally user story
        """
        logger.info("📎 Creating code attachment...")
        state['status'] = WorkflowStatus.CREATING_ATTACHMENT
        
        try:
            user_story = state['user_story_data']['user_story']
            generated_code = state['generated_code']
            evaluation_result = state['evaluation_result']
            
            if not evaluation_result:
                raise ValueError("No evaluation result available")
            
            # Create comprehensive code file content using f-strings and modern formatting
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            file_content = f"""# Generated Code for User Story: {user_story.get('FormattedID', 'N/A')}
# Story Name: {user_story.get('Name', 'N/A')}
# Generated on: {timestamp}
# Evaluation Score: {evaluation_result.match_score}%
# Python 3.12+ Compliant: {evaluation_result.python_3_12_compliance}

# User Story Description:
# {user_story.get('Description', 'N/A')}

# Evaluation Summary:
# Match Score: {evaluation_result.match_score}%
# Meets Threshold: {evaluation_result.meets_threshold}
# Python 3.12+ Features: {evaluation_result.python_3_12_compliance}
# Assessment: {evaluation_result.assessment}

{generated_code}

# Detailed Evaluation Results:
# Issues Found: {json.dumps([issue for issue in evaluation_result.issues], indent=2)}
# Suggestions: {json.dumps([suggestion for suggestion in evaluation_result.suggestions], indent=2)}
"""
            
            # Save to file with modern path handling
            filename = f"generated_code_{state['user_story_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
            filepath = os.path.join(tempfile.gettempdir(), filename)
            
            # Use modern file writing with proper encoding
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(file_content)
            
            state['final_code'] = file_content
            state['attachment_created'] = True
            state['status'] = WorkflowStatus.COMPLETED
            
            logger.info(f"✅ Code file created: {filepath}")
            logger.info(f"📊 Final evaluation score: {evaluation_result.match_score}%")
            logger.info(f"🐍 Python 3.12+ compliant: {evaluation_result.python_3_12_compliance}")
            
            # Note: In a real implementation, you would use Rally's API to attach the file
            # This would require additional Rally API calls for attachment creation
            
        except Exception as e:
            logger.error(f"❌ Error creating attachment: {e}")
            state['attachment_created'] = False
            state['status'] = WorkflowStatus.FAILED
        
        return state
    
    def run_workflow(self, user_story_id: str, max_iterations: int = 3) -> Dict[str, Any]:
        """
        Run the complete workflow
        
        Args:
            user_story_id: Rally user story FormattedID
            max_iterations: Maximum number of code generation iterations
            
        Returns:
            Final workflow state
        """
        logger.info(f"🚀 Starting workflow for user story: {user_story_id}")
        
        initial_state = WorkflowState(
            messages=[],
            user_story_id=user_story_id,
            rally_config=self.rally_config,
            user_story_data={},
            generated_code="",
            evaluation_result=None,
            iteration_count=0,
            max_iterations=max_iterations,
            final_code="",
            attachment_created=False,
            status=WorkflowStatus.INITIALIZING
        )
        
        try:
            final_state = self.workflow.invoke(initial_state)
            
            # Use match statement for status handling
            match final_state.get('status'):
                case WorkflowStatus.COMPLETED:
                    logger.info("🎉 Workflow completed successfully!")
                case WorkflowStatus.FAILED:
                    logger.error("❌ Workflow failed!")
                case _:
                    logger.warning("⚠️ Workflow ended with unexpected status")
            
            # Print comprehensive summary
            evaluation_result = final_state.get('evaluation_result')
            if evaluation_result:
                logger.info("="*50)
                logger.info("📊 WORKFLOW SUMMARY")
                logger.info(f"📋 User Story: {user_story_id}")
                logger.info(f"📊 Final Score: {evaluation_result.match_score}%")
                logger.info(f"🔄 Iterations: {final_state.get('iteration_count', 0)}")
                logger.info(f"🎯 Meets Threshold: {evaluation_result.meets_threshold}")
                logger.info(f"🐍 Python 3.12+ Compliant: {evaluation_result.python_3_12_compliance}")
                logger.info(f"📎 Attachment Created: {final_state.get('attachment_created', False)}")
                logger.info(f"📏 Status: {final_state.get('status', 'Unknown').name}")
                logger.info("="*50)
            
            return final_state
            
        except Exception as e:
            logger.error(f"❌ Workflow failed with exception: {e}")
            return {
                "error": str(e),
                "status": WorkflowStatus.FAILED,
                "user_story_id": user_story_id
            }

def main():
    """
    Main function to run the workflow
    """
    # Configuration
    rally_config = {
        "server": os.getenv("RALLY_SERVER", "https://rally1.rallydev.com"),
        "api_key": os.getenv("RALLY_API_KEY", "your_rally_api_key"),
        "workspace_ref": os.getenv("RALLY_WORKSPACE_REF", "/workspace/12345")
    }
    
    openai_api_key = os.getenv("OPENAI_API_KEY", "your_openai_api_key")
    
    if not all([rally_config["api_key"] != "your_rally_api_key", 
                rally_config["workspace_ref"] != "/workspace/12345",
                openai_api_key != "your_openai_api_key"]):
        print("❌ Please set the required environment variables:")
        print("   - RALLY_SERVER")
        print("   - RALLY_API_KEY") 
        print("   - RALLY_WORKSPACE_REF")
        print("   - OPENAI_API_KEY")
        return
    
    # Initialize workflow
    workflow = RallyCodeGeneratorWorkflow(openai_api_key, rally_config)
    
    # Run workflow
    user_story_id = input("Enter Rally User Story ID (e.g., US12345): ").strip()
    
    if user_story_id:
        result = workflow.run_workflow(user_story_id, max_iterations=3)
        
        if not result.get('error'):
            print(f"\n📄 Generated code saved to temporary file")
            print(f"🔍 You can review the code and evaluation details")
    else:
        print("❌ Please provide a valid user story ID")

if __name__ == "__main__":
    main()
