# Workflow Orchestration

## 1. Plan Mode Default

- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions)
- If something goes sideways, STOP and re-plan immediately - don't keep pushing

## 2. Subagent Strategy

- Use subagents liberally to keep main context window clean
- Offload research, exploration, and parallel analysis to subagents
- For complex problems, throw more compute at it via subagents
- One task per subagent for focused execution

## 3. Coding Convention

### General Guidelines

- Generated source code should include proper error handling, including releasing resources to avoid locking them or leaking memory

### Source Code Comments

- The source code generated should be properly commented
- Comment should focus on what the source code is doing and why, especially when the implementation is complex or non-idiomatic
- When generating comments, while keeping them brief, must convey essential information
- When making changes to the source code, review any comments and update them accordingly to reflect the changes
- Do not comment on the obvious
