# Rally Code Generator with LangGraph

An automated code generation pipeline that fetches user stories from Rally (CA Agile Central) and generates code using LangGraph with LangChain. The system uses three specialized agents to fetch, generate, and evaluate code based on user story requirements.

## Architecture

The workflow consists of four main nodes:

1. **Fetch User Story Agent** - Retrieves user story and dependencies from Rally
2. **Code Generation Agent** - Generates code based on user story requirements  
3. **Code Evaluation Agent** - Evaluates generated code against requirements (70% threshold)
4. **Attachment Creation Agent** - Creates code files and attaches them back to Rally

## Features

- **Multi-Agent Workflow** using LangGraph for orchestration
- **Iterative Code Generation** with evaluation feedback
- **Rally Integration** for fetching user stories and dependencies
- **Quality Threshold** (70% match) with automatic regeneration
- **Code Attachment** creation for Rally user stories
- **Comprehensive Logging** and error handling

## Setup

### Prerequisites

1. **Python 3.12+** - Required for modern language features
2. Rally API Key and Workspace access
3. OpenAI API Key for LLM operations

### Installation

```bash
# Clone or download the project
cd Langraph-samples

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your actual credentials
nano .env
```

### Environment Variables

Set the following environment variables in your `.env` file:

```bash
# Rally Configuration
RALLY_SERVER=https://rally1.rallydev.com
RALLY_API_KEY=your_rally_api_key_here
RALLY_WORKSPACE_REF=/workspace/12345

# OpenAI Configuration  
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_TEMPERATURE=0.1

# Workflow Configuration
MAX_ITERATIONS=3
EVALUATION_THRESHOLD=70.0
OUTPUT_DIRECTORY=/tmp
```

## Usage

### Command Line Interface

```bash
# Run workflow for a specific user story
python run_workflow.py US12345

# Run with custom max iterations
python run_workflow.py US12345 --max-iterations 5

# Check configuration
python run_workflow.py --check-config US12345
```

### Programmatic Usage

```python
from langgraph_code_generator import RallyCodeGeneratorWorkflow
from config import Config

# Initialize workflow
workflow = RallyCodeGeneratorWorkflow(
    openai_api_key=Config.OPENAI_API_KEY,
    rally_config=Config.get_rally_config()
)

# Run workflow
result = workflow.run_workflow("US12345", max_iterations=3)
```

## Workflow Process

1. **Fetch Phase**: Retrieves user story details and dependencies from Rally
2. **Generate Phase**: Creates code based on user story requirements using GPT-4
3. **Evaluate Phase**: Analyzes code quality and requirement coverage
4. **Decision Phase**: 
   - If score ≥ 70%: Proceed to attachment creation
   - If score < 70% and iterations < max: Regenerate with feedback
   - If max iterations reached: Create attachment with current code
5. **Attach Phase**: Creates code file and prepares for Rally attachment

## Code Generation Features

- **Context-Aware**: Considers user story dependencies and acceptance criteria
- **Best Practices**: Generates clean, documented, and maintainable code
- **Error Handling**: Includes proper exception handling and logging
- **Testing**: Generates unit tests where appropriate
- **Modular Design**: Creates well-structured, reusable code components

## Evaluation Criteria

The evaluation agent assesses code based on:

- **Requirement Coverage**: How well the code addresses user story needs
- **Code Quality**: Adherence to best practices and standards
- **Completeness**: Presence of necessary components and documentation
- **Functionality**: Logical correctness and expected behavior
- **Dependencies**: Proper handling of related user stories

## File Structure

```
Langraph-samples/
├── rally_user_story_fetcher.py    # Rally API integration
├── langgraph_code_generator.py    # Main LangGraph workflow
├── run_workflow.py                # CLI interface
├── config.py                      # Configuration management
├── example_usage.py               # Usage examples
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment template
└── README.md                      # This file
```

## Example Output

```
🚀 Starting workflow for user story: US12345
🔍 Fetching user story: US12345
✅ User story fetched: Implement user authentication system
🔧 Generating code (iteration 1)
✅ Code generated (2847 characters)
🔍 Evaluating generated code...
📊 Evaluation complete: 85% match
🎯 Meets threshold (70%): True
✅ Code meets requirements threshold (≥70%)
📎 Creating code attachment...
✅ Code file created: /tmp/generated_code_US12345_20250804_072856.py

==================================================
🎉 Workflow completed!
📊 Final Score: 85%
🔄 Iterations: 1
📎 Attachment Created: True
==================================================
```

## Rally API Authentication

### Getting an API Key

1. Log into Rally
2. Go to your user profile settings
3. Generate an API Key
4. Use this key for authentication

### Finding Workspace Reference

The workspace reference can be found in the Rally URL or through the API:
- Format: `/workspace/{workspace_id}`
- Example: `/workspace/12345`

## Troubleshooting

### Common Issues

1. **Rally Authentication Errors**
   - Verify API key is correct
   - Check workspace reference format
   - Ensure user has proper permissions

2. **OpenAI API Errors**
   - Verify API key is valid
   - Check rate limits and quotas
   - Ensure model access permissions

3. **Code Generation Issues**
   - Review user story completeness
   - Check for clear acceptance criteria
   - Verify dependency information

### Debug Mode

Enable debug logging by setting:
```bash
export LOG_LEVEL=DEBUG
```

## Security Best Practices

- Store API keys in environment variables
- Use secure credential management systems
- Implement proper access controls
- Enable audit logging
- Regular key rotation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.
