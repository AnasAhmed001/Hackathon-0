---
name: ai-vault-linkedin-posting
description: |
  Create, review, and publish LinkedIn posts for business promotion and sales generation.
  Use this skill whenever the user wants to post on LinkedIn, create LinkedIn content,
  generate business-related social media posts, draft sales or thought-leadership updates,
  or schedule LinkedIn activity. Also use when the user mentions "social media posting",
  "LinkedIn", "business promotion", "generate sales posts", or "post about the business".
  This skill handles the full lifecycle: content creation → HITL approval → Playwright publishing.
---

# LinkedIn Auto-Posting

Publish business content on LinkedIn to generate sales and visibility.
All posts go through human-in-the-loop approval before publishing.

## When to Use

- User wants to post on LinkedIn
- User asks to generate business content for social media
- User wants to promote their business or services
- Scheduled LinkedIn posting tasks
- Any request mentioning LinkedIn, social posts, or business promotion

## Post Creation Workflow

### Step 1: Generate Post Content

Create a LINKEDIN_POST_*.md file in AI_Employee_Vault/Pending_Approval/ with this schema:

```yaml
---
type: approval_request
action: post_linkedin
platform: linkedin
created: <ISO timestamp>
status: pending
risk: low
visibility: public
post_type: <business_update|thought_leadership|milestone|industry_insight>
source: claude
hashtags: [Tag1, Tag2, Tag3]
content: |
  <The actual post text goes here>

  #Tag1 #Tag2 #Tag3
---
```

Include these body sections:

- **## Post Content** — The full post text (same as frontmatter content)
- **## Post Details** — Platform, visibility, type, created date
- **## Suggested Actions** — Review checklist
- **## To Approve** — Move the file to `Approved/`
- **## To Reject** — Move the file to `Rejected/`

### Step 2: Human Approval

The post file sits in Pending_Approval/ until the human:
- Moves it to `Approved/` to authorize publishing
- Moves it to `Rejected/` to discard

Never self-approve. Never publish without folder-state proof.

### Step 3: Automated Publishing

The linkedin_poster.py daemon watches Approved/ for LINKEDIN_POST_*.md files
and publishes them via Playwright browser automation.

After publishing:
- Takes a proof screenshot (saved in Logs/linkedin_screenshots/)
- Moves the file to Done/
- Writes a log entry to Logs/

## Content Guidelines

When generating post content:

1. **Keep it professional** — Match LinkedIn's business-oriented tone
2. **Be concise** — Ideal length is 150-300 words
3. **Add value** — Share insights, achievements, or useful information
4. **Include a CTA** — Call-to-action when appropriate (e.g., "DM me for details")
5. **Use 3-5 hashtags** — Relevant to the content and industry
6. **Avoid hard selling** — Focus on value, not pushy sales language
7. **Read context** — Check Company_Handbook.md and Business_Goals.md for business context

## Content Types

| Type | Purpose | Frequency |
|------|---------|-----------|
| business_update | Share company news, new services | Weekly |
| thought_leadership | Industry insights, expert opinions | 2x/week |
| milestone | Achievements, wins, growth numbers | As they happen |
| industry_insight | Trends, commentary on industry news | Weekly |

## Helper Script

Create posts from the command line:

```bash
python scripts/linkedin_content_generator.py "<vault_path>" "<post_text>" "Tag1,Tag2"
```

## Safety Rules

- Every post must go through Pending_Approval → Approved flow
- Never bypass the approval workflow
- Maximum 2 posts per day (rate limit enforced in poster)
- DRY_RUN mode available for testing without publishing
- All posts are logged with timestamps and proof screenshots

## File Naming

Always use this pattern: `LINKEDIN_POST_<type>_<YYYYmmdd_HHMMSS>.md`

Example: `LINKEDIN_POST_business_update_20260406_150000.md`
