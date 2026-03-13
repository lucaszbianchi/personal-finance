# Code Review Skill

Comprehensive code review skill for analyzing both GitHub pull requests and local changes using established software engineering principles.

## Features

- **PR Review**: Analyze GitHub pull requests before merging
- **Local Review**: Review local changes before creating a PR
- Applies software engineering principles (DRY, KISS, YAGNI, Clean Code)
- Incorporates project-specific coding guidelines
- Generates detailed reports with code examples and suggestions
- Supports multiple languages for report output

## Usage

### Review a Pull Request

```
/code-review
```

When prompted:
1. Choose "PR Review"
2. Provide the PR number
3. Specify the base branch (e.g., `main`, `develop`)
4. Optionally specify the output language

### Review Local Changes

```
/code-review
```

When prompted:
1. Choose "Local Review"
2. Specify the base branch to compare against (e.g., `main`, `develop`)
3. Optionally specify the output language

The review will include all committed and uncommitted changes in your current branch compared to the base branch.

## Review Criteria

The skill evaluates code based on:

- **DRY (Don't Repeat Yourself)**: Eliminates code duplication
- **KISS (Keep It Simple, Stupid)**: Reduces unnecessary complexity
- **YAGNI (You Aren't Gonna Need It)**: Flags premature optimization and unused code
- **Clean Code**: Assesses readability, naming, function size, and complexity
- **Project Guidelines**: Applies project-specific standards from config files

## Output

Reviews are saved as markdown files:
- PR Reviews: `code-review-pr-<NUMBER>-<DATE>.md`
- Local Reviews: `code-review-local-<BRANCH>-<DATE>.md`

Each review includes:
- Overall quality score (1-10)
- Detailed issues with code examples
- Specific file locations and line numbers
- Suggested fixes with explanations
- Priority classification (Critical/Major/Minor)
- Summary with key recommendations

## Examples

### PR Review
```bash
# Review PR #73 against main branch
/code-review
> PR Review
> PR: 73
> Base: main
> Language: English
```

### Local Review
```bash
# Review current branch against main
/code-review
> Local Review
> Base: main
> Language: Portuguese
```

## Files Structure

```
code-review/
├── SKILL.md                    # Skill configuration and workflow
├── README.md                   # This file
├── references/
│   └── review_criteria.md      # Review criteria reference
└── scripts/
    ├── fetch_pr_diff.sh        # Fetches and diffs PR
    └── local_diff.sh           # Generates local diff
```

## Tips

- Use **Local Review** before creating a PR to catch issues early
- Use **PR Review** during code review process
- The skill automatically finds and applies project-specific guidelines
- Reviews are saved so you can track improvements over time
- All issues include line numbers for easy navigation
