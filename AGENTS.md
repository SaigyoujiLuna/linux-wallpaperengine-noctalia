# AGENTS.md

## Project Dependency Transformation
The project has been restructured to use Python's `poetry` for dependency management, integrated with the Uv tool for virtual environment handling.

### Steps Taken:
1. **Initialization**:
   - Uv was used to initialize the project with `uv init`.
   - Poetry was added to handle dependency declarations with `uv add pip poetry`.

2. **GTK+/PyGObject Dependency Declaration**:
   - PyGObject was explicitly installed via Poetry using `poetry add pygobject` to manage the GTK bindings for the project.

3. **Import Refactoring**:
   - Implicit imports for GTK modules were replaced with explicit imports to ensure clarity and proper modular design.

### Next Instructions:
- Verify the runtime of the system for refactored dependency compatibility.
- Follow the testing suite (if provided) to ensure all functionality works seamlessly after modular updates.

### Notes:
- The `pyproject.toml` file reflects the enforced Python version compatibility (`>=3.12,<4.0`) ensuring compatibility with required libraries.
- The explicit imports improved the error traceability during diagnosis of misconfigured GTK components.

