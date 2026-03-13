---
name: code-review
description: "Comprehensive code review skill for analyzing pull requests and local changes using software engineering principles (DRY, KISS, YAGNI, Clean Code). Use when the user requests code review, PR review, local diff review, analysis of code changes, evaluation of code quality, or feedback on code. The skill can review both GitHub PRs and local uncommitted/unpushed changes, performs detailed analysis, and provides structured feedback with code examples, scores, and improvement suggestions."
---

# Code Review

Perform comprehensive code reviews of pull requests or local changes using established software engineering principles and project-specific guidelines.

## Workflow

### 1. Gather Information

Ask the user to choose the review mode:
- **PR Review**: Review a GitHub pull request
- **Local Review**: Review local uncommitted/unpushed changes

#### For PR Review:
Ask the user for:
- **PR number**: The GitHub PR number to review
- **Base branch**: The branch to compare against (e.g., `main`, `develop`)
- **Output language**: The language for the review report (default: English)

Example: "What is the PR number you'd like me to review, and which branch should I compare it against?"

#### For Local Review:
Ask the user for:
- **Base branch**: The branch to compare against (e.g., `main`, `develop`)
- **Output language**: The language for the review report (default: English)

Example: "Which branch should I compare your current changes against?"

**Note**: If the user specifies a language preference (e.g., "in Portuguese", "in English"), use that language for the entire review report. Default to English if not specified.

### 2. Generate Diff

#### For PR Review:
Run the bundled script to fetch the PR and generate the diff:

```bash
bash scripts/fetch_pr_diff.sh <pr_number> <base_branch>
```

This script will:
- Fetch the PR from origin
- Create and checkout a local branch named `pr-<number>`
- Display the full diff against the base branch

#### For Local Review:
Run the bundled script to generate diff from local changes:

```bash
bash scripts/local_diff.sh <base_branch>
```

This script will:
- Get the name of the current branch
- Generate the diff comparing current branch against the specified base branch
- Display the full diff with uncommitted changes included

### 3. Identify Project Guidelines

Before starting the review, search for project-specific coding guidelines:

**Common guideline files to check:**
- `CONTRIBUTING.md`
- `CODING_STANDARDS.md` or `CODE_STYLE.md`
- `.eslintrc.js`, `.eslintrc.json`, or `.eslintrc`
- `.prettierrc` or `prettier.config.js`
- `pyproject.toml` or `setup.cfg` (Python projects)
- `tslint.json` or `tsconfig.json` (TypeScript)
- `.editorconfig`
- Language-specific linter configs (`.rubocop.yml`, `.php-cs-fixer.php`, etc.)

Use Glob tool to find these files:
```
pattern: "**/{CONTRIBUTING,CODING_STANDARDS,CODE_STYLE}.md"
pattern: "**/.{eslintrc,prettierrc,editorconfig}*"
pattern: "**/pyproject.toml"
```

Read any found guideline files to incorporate project-specific standards into the review.

### 4. Analyze the Code

Review the diff comprehensively using the criteria in `references/review_criteria.md`:

- **DRY**: Check for code duplication
- **KISS**: Identify unnecessary complexity
- **YAGNI**: Flag unneeded functionality or premature optimization
- **Clean Code**: Assess readability, naming, function size, cyclomatic complexity
- **Project Guidelines**: Apply any project-specific standards found

**Important**: Analyze ALL issues found, including:
- Major architectural problems
- Logic errors and bugs
- Performance issues
- Security vulnerabilities
- Code smells
- Style inconsistencies
- Minor formatting issues

### 5. Generate Review Report

Create a structured markdown report with:

#### Overall Score
Rate the code from 1-10 based on:
- Adherence to principles (DRY, KISS, YAGNI, Clean Code)
- Code quality and maintainability
- Presence of bugs or security issues
- Alignment with project guidelines

#### Issues Section

For each issue identified, create a markdown section with file path references:

```markdown
### Issue N: [Brief Title]

**Source of Correction**: [DRY | KISS | YAGNI | Clean Code | Project Guidelines]

**Location**: `file/path/to/file.ts:123-145`

**Previous Code**
```language
[problematic code block]
```

**Fixed Code**
```language
[corrected code block]
```

**Comments**
[Detailed explanation of why this is an issue and how the fix improves the code]
```

**Important**: Always include file paths with line numbers when referencing code issues.

#### Summary
Provide a brief summary highlighting:
- Total number of issues found
- Most critical issues
- Overall recommendations

### 6. Save Review Report

After generating the review, save it to a markdown file:

**For PR Review:**
```
code-review-pr-<PR_NUMBER>-<TIMESTAMP>.md
```

**For Local Review:**
```
code-review-local-<BRANCH_NAME>-<TIMESTAMP>.md
```

Use the Write tool to save the complete review report in the current working directory. Include:
- Full review content
- Timestamp of the review
- PR number or branch name in the filename

Example filenames:
- PR Review: `code-review-pr-73-2026-02-12.md`
- Local Review: `code-review-local-feature-auth-2026-02-12.md`

## Example Output Format

### PR Review Example:

```markdown
# Code Review: PR #73

**Review Date**: 2026-02-12
**Base Branch**: main
**Reviewer**: Claude Code Review

## Overall Score: 7/10

The code is functional and mostly follows best practices, but has some areas for improvement in complexity reduction and code organization.

---

### Issue 1: High Cyclomatic Complexity in Authentication Flow

**Source of Correction**: Clean Code

**Location**: `src/auth/authenticator.ts:45-58`

**Previous Code**
```typescript
function authenticateUser(credentials: Credentials) {
  let result = false;
  if (credentials.username) {
    if (credentials.password) {
      if (validateUsername(credentials.username)) {
        if (validatePassword(credentials.password)) {
          result = checkDatabase(credentials);
        }
      }
    }
  }
  return result;
}
```

**Fixed Code**
```typescript
function authenticateUser(credentials: Credentials) {
  if (!credentials.username) return false;
  if (!credentials.password) return false;
  if (!validateUsername(credentials.username)) return false;
  if (!validatePassword(credentials.password)) return false;

  return checkDatabase(credentials);
}
```

**Comments**
The original function has deeply nested conditions that make it hard to read and maintain. Using early returns (guard clauses) reduces cyclomatic complexity and improves readability by making the happy path clear and reducing indentation levels.

---

### Issue 2: Code Duplication in API Handlers

**Source of Correction**: DRY

**Location**: `src/api/handlers.ts:102-145, 178-221`

[... continue with remaining issues ...]

---

## Summary

**Total Issues**: 5
- 2 Critical (security, logic errors)
- 2 Major (complexity, duplication)
- 1 Minor (naming conventions)

**Key Recommendations**:
1. Refactor authentication flow to reduce complexity (src/auth/authenticator.ts:45)
2. Extract duplicated API handling logic into shared utilities (src/api/handlers.ts)
3. Add input validation for user-provided data (src/api/validators.ts)

```

### Local Review Example:

```markdown
# Code Review: Local Branch feature-auth

**Review Date**: 2026-02-12
**Current Branch**: feature-auth
**Base Branch**: main
**Reviewer**: Claude Code Review

## Overall Score: 7/10

The code is functional and mostly follows best practices, but has some areas for improvement in complexity reduction and code organization.

---

### Issue 1: High Cyclomatic Complexity in Authentication Flow

**Source of Correction**: Clean Code

**Location**: `src/auth/authenticator.ts:45-58`

**Previous Code**
```typescript
function authenticateUser(credentials: Credentials) {
  let result = false;
  if (credentials.username) {
    if (credentials.password) {
      if (validateUsername(credentials.username)) {
        if (validatePassword(credentials.password)) {
          result = checkDatabase(credentials);
        }
      }
    }
  }
  return result;
}
```

**Fixed Code**
```typescript
function authenticateUser(credentials: Credentials) {
  if (!credentials.username) return false;
  if (!credentials.password) return false;
  if (!validateUsername(credentials.username)) return false;
  if (!validatePassword(credentials.password)) return false;

  return checkDatabase(credentials);
}
```

**Comments**
The original function has deeply nested conditions that make it hard to read and maintain. Using early returns (guard clauses) reduces cyclomatic complexity and improves readability by making the happy path clear and reducing indentation levels.

---

### Issue 2: Code Duplication in API Handlers

**Source of Correction**: DRY

**Location**: `src/api/handlers.ts:102-145, 178-221`

[... continue with remaining issues ...]

---

## Summary

**Total Issues**: 5
- 2 Critical (security, logic errors)
- 2 Major (complexity, duplication)
- 1 Minor (naming conventions)

**Key Recommendations**:
1. Refactor authentication flow to reduce complexity (src/auth/authenticator.ts:45)
2. Extract duplicated API handling logic into shared utilities (src/api/handlers.ts)
3. Add input validation for user-provided data (src/api/validators.ts)

```

## Tips

- **Be thorough**: Review all changes, not just the obvious issues
- **Be specific**: Always reference exact line numbers and file paths (format: `path/to/file.ts:123-145`)
- **Be constructive**: Explain the "why" behind each suggestion
- **Prioritize**: Note which issues are critical vs. minor
- **Consider context**: Some patterns may be intentional for the project's needs
- **Language**: Generate the review in the language specified by the user (default: English)
- **Save output**: Always save the complete review to a markdown file:
  - PR Review: `code-review-pr-<NUMBER>-<DATE>.md`
  - Local Review: `code-review-local-<BRANCH>-<DATE>.md`

## Workflow Decision Tree

```
User requests code review
  ├─> Ask: "Would you like to review a PR or local changes?"
  │
  ├─> PR Review
  │   ├─> Ask for PR number
  │   ├─> Ask for base branch
  │   ├─> Ask for output language (optional)
  │   ├─> Run: bash scripts/fetch_pr_diff.sh <pr_number> <base_branch>
  │   └─> Generate review report
  │
  └─> Local Review
      ├─> Ask for base branch
      ├─> Ask for output language (optional)
      ├─> Run: bash scripts/local_diff.sh <base_branch>
      └─> Generate review report
```
