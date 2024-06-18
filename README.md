# Slack Chatbot 
## Project Description
[Placeholder for project description]

## Git Commit Guidelines

To ensure a clear and consistent commit history, we follow these guidelines for commit messages:

### General Rules for Branches
The `main` branch is should only contain stable, production-ready code. All development should be done on `dev` branch, where collaborators work on new features and commits changes. When a feature is ready for production, the `dev` branch should be merged into `main` via a pull request.  
Generally, the branches should look like the following:

```python 
- main branch
- dev branch
    - collab1 branch
    - collab2 branch
    - etc.
```

### Commit Message Format

Each commit message should consist of a **type** and a **subject**:

```
<type>: <subject>
```

- **Type**: Indicates the purpose of the commit. Must be one of the following:
  - `feat`: Adds a new feature or modifies an existing one.
  - `fix`: Fixes a bug or issue.
  - `docs`: Updates or adds documentation.
  - `style`: Changes that do not affect the meaning of the code (formatting, white-space, etc.).
  - `refactor`: Code changes that neither fix a bug nor add a feature.
  - `perf`: Improves performance.
  - `test`: Adds or updates tests.
  - `chore`: Changes to the build process or auxiliary tools.
  - `revert`: Reverts a previous commit.

- **Subject**: A brief description of the change. Should be in imperative mood (e.g., "Add", "Fix", "Update") and not end with a period.

### Examples

- `feat: Add login functionality`
- `fix: Resolve database connection issue`
- `docs: Update installation instructions`
- `style: Fix code formatting`
- `refactor: Simplify string manipulation logic`
- `perf: Optimize data retrieval`
- `test: Add unit tests for user registration`
- `chore: Update project dependencies`
- `revert: Revert "Add login functionality"`
