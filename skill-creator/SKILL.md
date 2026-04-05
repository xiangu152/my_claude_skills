---
name: skill-creator
description: Create, edit, improve, or audit Claude Code skills. Use when creating a new skill from scratch, improving an existing skill, reviewing a SKILL.md file, or restructuring a skill directory. Triggers on "create a skill", "author a skill", "tidy up a skill", "improve this skill", "review the skill", "clean up the skill", "audit the skill". NOT for: installing skills (use install-skill), using skills, or general file editing.
---

# Skill Creator

Guide for creating effective Claude Code skills.

## What Skills Are

Skills are modular packages that extend Claude Code's capabilities. They provide specialized knowledge, workflows, and tools — like onboarding guides for specific domains.

### What Skills Provide

1. **Specialized workflows** — Multi-step procedures for specific domains
2. **Tool integrations** — Instructions for working with specific file formats or APIs
3. **Domain expertise** — Company-specific knowledge, schemas, business logic
4. **Bundled resources** — Scripts, references, and assets for complex tasks

## Core Principles

### Concise is Key

The context window is a public good. Skills share it with system prompt, conversation history, other skills' metadata, and the actual request.

**Default assumption: Claude is already very smart.** Only add context Claude doesn't already have. Challenge each piece of information: "Does Claude really need this?"

Prefer concise examples over verbose explanations.

### Set Appropriate Degrees of Freedom

- **High freedom (text instructions)**: Multiple approaches valid, context-dependent decisions
- **Medium freedom (pseudocode/scripts with parameters)**: Preferred pattern exists, some variation OK
- **Low freedom (specific scripts, few parameters)**: Fragile operations, consistency critical

## Anatomy of a Skill

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter (required)
│   │   ├── name: (required)
│   │   └── description: (required)
│   └── Markdown body (required)
├── scripts/          — Executable code (Python/Bash/etc.)
├── references/       — Documentation loaded into context as needed
└── assets/           — Files used in output (templates, icons, etc.)
```

### SKILL.md (required)

- **Frontmatter** (YAML): `name` and `description`. These determine when the skill triggers. Be clear and comprehensive — include both what the skill does AND when to use it.
- **Body** (Markdown): Instructions for using the skill. Only loaded AFTER triggering.

### Bundled Resources

#### scripts/

Executable code for tasks requiring deterministic reliability or repeated execution.

- When: Same code rewritten repeatedly, or deterministic reliability needed
- Example: `scripts/search.mjs` for API calls
- Note: Scripts may need reading for patching or adjustments

#### references/

Documentation loaded into context as needed to inform Claude's process.

- When: Claude should reference documentation while working
- Examples: `references/api-docs.md`, `references/schema.md`
- Best practice: If >10k words, include grep patterns in SKILL.md
- Avoid duplication: Information lives in SKILL.md OR references, not both

#### assets/

Files used in output, NOT loaded into context.

- When: Skill needs files for final output
- Examples: `assets/template.docx`, `assets/logo.png`

### What NOT to Include

- README.md (SKILL.md is the README)
- CHANGELOG.md
- INSTALLATION_GUIDE.md
- Any auxiliary documentation not directly supporting the skill's functionality

## Progressive Disclosure

Skills use three loading levels:

1. **Metadata (name + description)** — Always in context (~100 words)
2. **SKILL.md body** — When skill triggers (<5k words, under 500 lines)
3. **Bundled resources** — As needed by Claude

### When to Split Content

Keep SKILL.md under 500 lines. Split when:

- Multiple frameworks/variants supported → separate references
- Complex domain with sub-topics → `references/domain.md`
- Detailed API docs → `references/api.md`

**Pattern: High-level guide with references**

```markdown
# PDF Processing

## Quick start
[code example]

## Advanced features
- **Form filling**: See [references/forms.md](references/forms.md)
- **API reference**: See [references/api.md](references/api.md)
```

**Key rules:**
- References one level deep from SKILL.md (no nesting)
- Files >100 lines should have a table of contents
- Describe in SKILL.md when to read each reference file

## Skill Creation Process

### Step 1: Understand the Skill

Clarify concrete examples of how the skill will be used:

- What functionality should it support?
- What would a user say to trigger it?
- What are concrete usage examples?

Conclude when there's a clear sense of the functionality.

### Step 2: Plan Resources

Analyze each example:

1. Consider how to execute from scratch
2. Identify scripts, references, and assets that would help

Example: Building a `pdf-editor` skill → rotating a PDF rewrites the same code → include `scripts/rotate_pdf.py`.

### Step 3: Initialize the Skill

Create the directory structure:

```bash
mkdir -p skill-name/scripts    # if scripts needed
mkdir -p skill-name/references # if references needed
mkdir -p skill-name/assets     # if assets needed
```

Start with SKILL.md frontmatter:

```yaml
---
name: skill-name
description: "What this does. Use when: (1) specific trigger, (2) another trigger. NOT for: excluded cases."
---
```

### Step 4: Write the Skill

#### Frontmatter Description

- Include both what the skill does AND when to use it
- Include all "when to use" info here — NOT in the body
- Body is only loaded after triggering, so "When to Use" sections in body are useless

Example:
```yaml
description: "Create and edit Excel workbooks with formulas, formatting, and template preservation. Use when (1) task is about .xlsx/.xlsm files, (2) formulas or formatting matter, (3) file must stay reliable after edits. NOT for: plain CSV or when pandas alone suffices."
```

#### Writing Style

- Use imperative/infinitive form ("Run the script" not "You should run the script")
- Prefer code examples over prose explanations
- Keep it under 500 lines
- Reference external files clearly: "See [references/api.md](references/api.md)"

### Step 5: Test the Skill

1. Install the skill to `$HOME/.claude/skills/`
2. Restart Claude Code
3. Test with real queries that should trigger the skill
4. Verify scripts run correctly
5. Check that description accurately triggers

### Step 6: Iterate

1. Use the skill on real tasks
2. Notice struggles or inefficiencies
3. Update SKILL.md or resources
4. Test again

## Skill Naming

- Lowercase letters, digits, hyphens only
- Under 64 characters
- Short, verb-led phrases when possible (e.g., `rotate-pdf`, `search-web`)
- Folder name matches skill name exactly
