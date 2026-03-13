# Code Review Criteria

## Core Principles

### DRY (Don't Repeat Yourself)
- Eliminate code duplication
- Extract common logic into reusable functions/methods
- Use inheritance, composition, or mixins appropriately
- Avoid copy-pasted code blocks

### KISS (Keep It Simple, Stupid)
- Prefer simple, straightforward solutions
- Avoid over-engineering
- Reduce unnecessary complexity
- Use clear, descriptive names

### YAGNI (You Aren't Gonna Need It)
- Don't implement functionality until it's needed
- Remove unused code, imports, and dependencies
- Avoid premature optimization
- Focus on current requirements

### Clean Code Principles
- **Readability**: Code should be easy to understand
- **Single Responsibility**: Each function/class does one thing
- **Low Cyclomatic Complexity**: Reduce nested conditions, use early returns
- **Meaningful Names**: Variables, functions, and classes have descriptive names
- **Small Functions**: Functions should be short and focused
- **Error Handling**: Proper exception handling without swallowing errors
- **Comments**: Explain "why", not "what" (code should be self-documenting)

## Common Issues to Identify

### Code Smells
- Long methods (>20-30 lines)
- Large classes (>200-300 lines)
- Long parameter lists (>3-4 parameters)
- Deeply nested conditions (>3 levels)
- Magic numbers (use constants)
- Dead code
- Commented-out code

### Performance Issues
- Unnecessary loops or iterations
- Inefficient algorithms
- Memory leaks
- Unoptimized database queries
- Missing caching opportunities

### Security Issues
- SQL injection vulnerabilities
- XSS vulnerabilities
- Missing input validation
- Hardcoded credentials
- Insecure cryptographic practices
- Missing authentication/authorization checks

### Maintainability Issues
- Tight coupling
- Missing error handling
- Lack of logging
- Missing tests or low test coverage
- Inconsistent coding style
- Poor documentation

## Output Format

Each issue should be documented with:

1. **Issue title**: Brief description
2. **Source of Correction**: DRY, KISS, YAGNI, Clean Code, or Project Guidelines
3. **Previous Code**: The problematic code block
4. **Fixed Code**: The corrected code
5. **Comments**: Explanation of why the change improves the code
