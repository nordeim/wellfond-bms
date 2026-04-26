# Tools CLI — Standalone File Operations Wrapper

> **Status:** ✅ Production Ready | **Version:** 1.0.0 | **Binary:** 20.1 MB
> **Source:** `/home/project/cc-src/src/entrypoints/tools-cli.ts`
> **Compiled:** `/home/project/cc-src/dist/tools-cli.js`

## Overview

Tools CLI is a standalone wrapper that exposes Claude Code's core file operations as a command-line utility. It provides 5 tools for file manipulation without requiring a full Claude session.

**Key Feature:** Runs in `bypass` mode — no permission prompts, suitable for scripting and automation.

---

## Quick Start

```bash
# Environment setup (REQUIRED for glob/grep)
export USE_BUILTIN_RIPGREP=false

# Alias for convenience
alias tools-cli='bun /home/project/cc-src/dist/tools-cli.js'

# Basic usage
tools-cli --version                    # → Tools CLI 1.0.0
tools-cli read --file README.md        # Read file
tools-cli glob --pattern "*.ts"        # Find files
tools-cli grep --pattern "function"    # Search content
```

---

## Commands Reference

### 1. `read` — Read File Contents

Read text files with optional pagination and output formatting.

```bash
# Basic read
tools-cli read --file /path/to/file.md

# With line limit
tools-cli read --file README.md --limit 10

# With offset (start from line 10)
tools-cli read --file README.md --offset 10 --limit 5

# JSON output (structured)
tools-cli read --file README.md --limit 5 --json

# Silent mode (raw content only)
tools-cli read --file README.md --silent
```

**Options:**
| Option | Type | Description |
|--------|------|-------------|
| `--file <path>` | string | File path (supports `~` expansion) |
| `--offset <n>` | number | Start reading from line n |
| `--limit <n>` | number | Maximum lines to read |
| `--json` | flag | Output as structured JSON |
| `--silent` | flag | Raw content only (no metadata) |

**JSON Output Example:**
```json
{
  "type": "text",
  "file": {
    "filePath": "/home/project/cc-src/README.md",
    "content": "# CC-SRC: Claude Code...",
    "numLines": 5,
    "startLine": 1,
    "totalLines": 377
  }
}
```

---

### 2. `write` — Create or Overwrite Files

Write content to files. Creates new files or overwrites existing ones.

```bash
# Create new file
tools-cli write --file /tmp/test.txt --content "Hello World"

# Overwrite existing file
tools-cli write --file config.json --content '{"debug": true}'

# Multi-line content
tools-cli write --file /tmp/notes.txt --content "Line 1
Line 2
Line 3"

# From stdin (shell)
echo "Dynamic content" | tools-cli write --file /tmp/output.txt --content "$(cat)"
```

**Options:**
| Option | Type | Description |
|--------|------|-------------|
| `--file <path>` | string | Target file path |
| `--content <text>` | string | Content to write |

**Note:** `write` bypasses the file state cache — safe for CLI one-liners.

---

### 3. `edit` — String Replacement

Edit files by replacing exact string matches. **⚠️ Has cache protection (see below).**

```bash
# Replace exact string
tools-cli edit --file config.json \
  --old '"debug": false' \
  --new '"debug": true"'

# Replace with multi-line
tools-cli edit --file README.md \
  --old "Old Title" \
  --new "New Title"
```

**Options:**
| Option | Type | Description |
|--------|------|-------------|
| `--file <path>` | string | File to edit |
| `--old <text>` | string | Exact text to replace |
| `--new <text>` | string | Replacement text |

**⚠️ Cache Protection (By Design):**

The `edit` tool enforces a **Read-Modify-Write** pattern for safety:
- Requires the file to have been read in the same session
- Rejects edits if file was modified since last read
- Prevents race conditions and lost changes

**Why this affects CLI:** Each CLI invocation is a fresh process with an empty cache. The edit tool sees no prior read and fails with:
```
Error: File has not been read yet. Read it first before writing to it.
```

**For CLI usage:** Each `tools-cli` invocation is a separate process, so `read` → `edit` won't work across invocations. For CLI scripts, use the `read` → `write` pattern with content replacement:

```bash
# For CLI scripts: read current content, modify, then write back
content=$(tools-cli read --file config.json --silent)
new_content="${content/false/true}"
tools-cli write --file config.json --content "$new_content"
```

**Note:** In agent sessions (OpenClaw, Claude Code), `read` → `edit` works because the cache persists across tool calls.

---

### 4. `glob` — File Pattern Matching

Find files using glob patterns. Requires `USE_BUILTIN_RIPGREP=false`.

```bash
# Find TypeScript files
tools-cli glob --pattern "*.ts" --path src/

# Recursive pattern
tools-cli glob --pattern "src/**/*.tsx"

# Multiple extensions
tools-cli glob --pattern "*.{ts,tsx,js}"

# Limit results
tools-cli glob --pattern "*.md" --head 10
```

**Options:**
| Option | Type | Description |
|--------|------|-------------|
| `--pattern <glob>` | string | Glob pattern (supports `**`, `*`, `?`, `[]`) |
| `--path <dir>` | string | Search directory (default: cwd) |
| `--head <n>` | number | Limit results |
| `--silent` | flag | File paths only (no formatting) |

---

### 5. `grep` — Content Search

Search file contents with regex. Requires `USE_BUILTIN_RIPGREP=false`.

```bash
# Basic search
tools-cli grep --pattern "TODO|FIXME" --path src/

# Case-insensitive
tools-cli grep --pattern "error" --path logs/ --mode content -i

# With context lines
tools-cli grep --pattern "function" --path src/ --context 2

# Limit results
tools-cli grep --pattern "class.*Tool" --path src/tools --head 5
```

**Options:**
| Option | Type | Description |
|--------|------|-------------|
| `--pattern <regex>` | string | Regex pattern to search |
| `--path <dir>` | string | Search directory |
| `--mode <type>` | string | `content` or `files` (default: files) |
| `--head <n>` | number | Limit results |
| `-i` | flag | Case-insensitive |
| `--context <n>` | number | Show n lines of context |

---

## Global Options

All commands support these options:

| Option | Description |
|--------|-------------|
| `--cwd <path>` | Set working directory |
| `--json` | Output as JSON |
| `--silent` | Suppress non-error output |
| `--verbose` | Show debug information |
| `--help` | Show help message |
| `--version` | Show version |

---

## Environment Requirements

### `USE_BUILTIN_RIPGREP=false` (REQUIRED for glob/grep)

The `glob` and `grep` commands require system `rg` (ripgrep) to be available.

```bash
# Set for current session
export USE_BUILTIN_RIPGREP=false

# Or add to shell profile (~/.bashrc or ~/.zshrc)
echo 'export USE_BUILTIN_RIPGREP=false' >> ~/.bashrc
```

**Why needed:** The bundled ripgrep path (`src/utils/vendor/ripgrep/`) may not resolve correctly. Setting this flag uses the system-installed `rg` instead.

---

## File State Cache Explained

### What It Is

The **FileStateCache** (`src/utils/fileStateCache.ts`) is a **safety mechanism**, not a bug. It exists to prevent a critical race condition: editing a file that has been modified by another process since you read it.

**What it tracks:**
- File content at time of read
- Timestamp of read
- Read parameters (offset/limit for partial reads)
- Whether the read was a partial view

**Why it matters:** Without this protection, you'd silently overwrite changes from linters, formatters, other agents, or users working concurrently.

### How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                     FILE STATE CACHE FLOW                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. READ TOOL              2. EDIT TOOL                         │
│  ┌─────────────────┐      ┌─────────────────┐                   │
│  │ Read file       │      │ Validate input  │                   │
│  │        ↓        │      │        ↓        │                   │
│  │ Store in cache: │      │ Check cache:    │                   │
│  │  - content      │      │  - File read?   │                   │
│  │  - timestamp    │      │  - Stale?       │                   │
│  │  - offset/limit │      │  - Partial view?│                   │
│  └─────────────────┘      │        ↓        │                   │
│                           │ Allow or reject │                   │
│                           └─────────────────┘                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**The validation logic checks:**
1. Has the file been read in this session?
2. Was it a full read or partial view?
3. Has the file been modified externally since read?

### ⚠️ CRITICAL INSIGHT: The Cache Is a Safety Signal, Not an Obstacle

**When `edit` fails with "File has not been read yet":**

| ❌ WRONG (Bypass) | ✅ RIGHT (Respect) |
|-------------------|---------------------|
| `edit` fails → switch to `write` | `edit` fails → `read` → retry `edit` |
| Bypass the safety mechanism | Trust and follow the safety mechanism |
| Risk overwriting concurrent changes | Preserve concurrent modifications |
| Treat failure as obstacle | Treat failure as useful signal |

**Why not jump to `write`?**

If another process modified the file after you read it but before your edit, `write` will **silently overwrite** those changes. The cache failure is telling you: "You don't know what's actually in this file right now."

**The correct recovery pattern:**
```bash
# When edit fails with "File has not been read yet" or "File has been modified since read":
# Step 1: Read the current content (refreshes your knowledge)
tools-cli read --file config.json --silent

# Step 2: Retry the edit (now cache is populated)
tools-cli edit --file config.json --old "old_value" --new "new_value"
```

### Why CLI Has Cache Issues

**Root cause** (`src/entrypoints/tools-cli.ts:268`):
```typescript
readFileState: new Map(), // ← Empty map, no cached reads!
```

Each CLI invocation creates a fresh `Map()` with no memory of prior reads. The edit tool checks this empty cache and fails.

**Context matters:**
- **In OpenClaw agent sessions:** `read` → `edit` works because the cache persists across tool calls
- **In CLI invocations:** Each call is a separate process, so `read` → `edit` still fails

### Affected Tools

| Tool | Affected? | Reason |
|------|-----------|--------|
| `read` | ❌ No | Cache population, not consumption |
| `write` | ❌ No | Creates/overwrites without cache check |
| `edit` | ✅ Yes | Requires cached read state |
| `glob` | ❌ No | No file state dependency |
| `grep` | ❌ No | No file state dependency |

### When to Use Each Approach

**Use `read` → `edit` when:**
- Working in an agent session (OpenClaw, Claude Code)
- The file might have been modified by concurrent processes
- You want to preserve others' changes

**Use `write` for CLI scripts when:**
- Each invocation is a fresh process (tools-cli)
- You control all modifications to the file
- You're doing simple replacement in a controlled script:
  ```bash
  content=$(tools-cli read --file config.json --silent)
  new_content="${content/old-text/new-text}"
  tools-cli write --file config.json --content "$new_content"
  ```

### Advanced: Content Comparison Fallback

On systems where timestamps can change without content changes (Windows cloud sync, antivirus), the cache includes a **content comparison fallback**. For full reads, if the timestamp indicates modification but content matches, the edit is still allowed. This prevents false positives while maintaining safety.

---

## Performance Characteristics

| Operation | Typical Time | Notes |
|-----------|--------------|-------|
| Help display | ~500ms | CLI startup overhead |
| File read | ~100ms | Small files (<1MB) |
| Glob search | ~200ms | Depends on file count |
| Grep search | ~300ms | Depends on content size |
| Write operation | ~50ms | Small files |

**Binary size:** 20.1 MB (5,180 modules bundled)

---

## Security Model

**✅ No permission prompts** — Runs in `bypass` mode
**✅ Explicit invocation = consent** — User knows what they're running
**✅ Same protections as main CLI** — Path traversal, blocked devices, etc.
**⚠️ User responsible** — Same caution as `rm`, `cp`, `echo > file`

**Recommendation:** Review commands before running in production. No undo mechanism.

---

## Use Cases

### 1. Script Integration

```bash
#!/bin/bash
# Process all markdown files
for file in $(tools-cli glob --pattern "*.md" --silent); do
  echo "Processing: $file"
  content=$(tools-cli read --file "$file" --silent)
  # Process content...
done
```

### 2. CI/CD Pipeline

```yaml
# .github/workflows/update.yml
- name: Update version
  run: |
    content=$(tools-cli read --file package.json --silent)
    new_content="${content/\"version\": \"1.0.0\"/\"version\": \"1.0.1\"}"
    tools-cli write --file package.json --content "$new_content"
```

### 3. Quick File Operations

```bash
# Find and read
tools-cli read --file $(tools-cli glob --pattern "README.md" --silent | head -1)

# Search and extract
tools-cli grep --pattern "TODO|FIXME" --path src/ --mode content --head 20

# Create file with content
echo "Generated content" | tools-cli write --file /tmp/output.txt --content "$(cat)"
```

---

## Troubleshooting

### "File has not been read yet" or "File has been modified since read" (Edit tool)

**Cause:** The FileStateCache requires a prior read to validate the edit is safe.

**⚠️ DON'T: Jump to `write`** — Jumping to `write` bypasses the safety mechanism and risks overwriting concurrent changes.

**✅ DO: Read first, then retry edit**

```bash
# Step 1: Read the current content (populates cache)
tools-cli read --file /path/to/file

# Step 2: Retry the edit (validation now passes)
tools-cli edit --file /path/to/file --old "old_text" --new "new_text"
```

**For CLI scripts** (separate invocations), use `read` → `write` with content replacement.

### "ripgrep not found" (Glob/Grep tools)

**Cause:** `USE_BUILTIN_RIPGREP` not set or system `rg` not installed.
**Solution:**
```bash
export USE_BUILTIN_RIPGREP=false
# Ensure system rg is installed
which rg || sudo apt install ripgrep
```

### Slow startup

**Cause:** 20MB binary has initialization overhead (~500ms).
**Solution:** Acceptable for script usage. For interactive use, consider shell aliases.

---

## Related Documentation

- **Test Report:** `/home/project/cc-src/TOOLS_CLI_TEST_REPORT.md`
- **Cache Analysis:** `/home/pete/.openclaw/workspace/documents/tools-cli_cache_issue_analysis.md`
- **Implementation Guide:** `/home/project/cc-src/TOOLS_CLI_IMPLEMENTATION_GUIDE.md`
- **Security Model:** `/home/project/cc-src/TOOLS_CLI_SECURITY_MODEL.md`

---

## Quick Reference Card

```bash
# Setup
export USE_BUILTIN_RIPGREP=false
alias tools-cli='bun /home/project/cc-src/dist/tools-cli.js'

# Read
tools-cli read --file README.md --limit 10
tools-cli read --file README.md --offset 5 --limit 3 --json
tools-cli read --file README.md --silent

# Write
tools-cli write --file /tmp/test.txt --content "Hello World"

# Edit (⚠️ cache protection)
tools-cli edit --file config.json --old "false" --new "true"

# Glob
tools-cli glob --pattern "*.ts" --path src/
tools-cli glob --pattern "src/**/*.tsx" --head 10

# Grep
tools-cli grep --pattern "TODO" --path src/ --head 5
tools-cli grep --pattern "class.*Tool" --path src/tools --head 3
```

---

*Last updated: 2026-04-14 07:04 SGT | Updated with cache safety insights | Verified against tools-cli v1.0.0*
