"""
tool_definitions.py — What the model is told about the tools (Ollama tool schemas).

The model only sees these descriptions; the code that runs is in db_tools.py.
Names here must match the dispatcher in db_tools.run_tool.
"""

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "run_sql",
            "description": (
                "Execute a SELECT SQL query against the HR PostgreSQL database. "
                "Use this to answer any question about employees, salaries, departments, organizations, or cities. "
                "Always use table aliases. Filter is_active=TRUE unless asked about inactive employees."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "A valid PostgreSQL SELECT statement."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_employee",
            "description": (
                "Fuzzy-search for an employee by name. "
                "Always call this BEFORE disable_employee to confirm the correct emp_id. "
                "Also useful when the user mentions a name and you need their emp_id for a follow-up query."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Full name, first name, or last name to search for."
                    }
                },
                "required": ["name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "disable_employee",
            "description": (
                "Request to disable an employee (mark them as inactive / left the company). "
                "Pass the employee's name; the system looks them up itself. If several employees "
                "match, it returns them: ask the user which one, then call again with name AND emp_id. "
                "This does NOT disable immediately: the system asks the user to confirm, "
                "so do not ask for confirmation yourself."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of the employee to disable, as the user said it."
                    },
                    "emp_id": {
                        "type": "integer",
                        "description": "Only when choosing between several matches returned by this tool."
                    }
                },
                "required": ["name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_schema",
            "description": "Get the database schema — table names, columns, and key rules. Call this if unsure about the schema.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }
]
