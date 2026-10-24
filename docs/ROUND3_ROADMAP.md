# BrandGuard AI — Round 3 Roadmap
### Three Substantial Planned Improvements

> **Important:** The features described in this document are **planned improvements for Round 3**, not currently implemented capabilities. Each section honestly describes what exists today, what Round 3 would add, and the realistic implementation approach.

---

## Improvement 1: Visual Brand Compliance Engine

### Problem It Solves

BrandGuard AI currently analyzes **text-only** promotional copy. Enterprise brand governance, however, requires consistent visual identity enforcement across:
- Digital display ads (PNG/JPG/SVG banners)
- Social media creatives
- Email headers and footers
- PDF marketing collateral and pitch decks

A campaign can have perfect text compliance but still violate brand identity by using the wrong logo variant, unapproved color palette, incorrect font family, or placing mandatory disclaimers in an unreadably small typeface. Today, visual review is entirely manual.

### What Exists Today

- The `extract-text` endpoint in `guidelines.py` accepts `.txt` and `.pdf` uploads for text extraction (via `pypdf`)
- The `BrandGuideline` model has a `"Visual Identity"` category that managers can populate with text-based visual rules
- The Gemini 2.5 Flash model supports multimodal inputs via the `google-genai` SDK

### What Round 3 Would Add

**Backend:**
- New endpoint: `POST /api/submissions/:id/analyze-visual` accepting image file uploads (PNG, JPG, PDF page renders)
- Gemini multimodal analysis prompt grounded in the brand's Visual Identity guidelines
- Structured JSON output: detected logo variant, dominant colors (hex values), visible font samples, disclaimer presence/absence
- Cross-reference against brand-configured approved hex color ranges, approved logo identifiers, required disclaimer text
- New DB column: `ComplianceAnalysis.visual_findings` (JSON field) to store visual-specific findings separately from text findings

**Frontend:**
- File drop zone on the submission detail page for uploading creative assets alongside text copy
- Visual findings displayed with side-by-side preview: annotated asset image + finding explanation
- Severity badges matching the existing text finding severity system

**Limitations to be disclosed upfront:**
- Logo detection accuracy depends on Gemini's vision understanding; ambiguous logo variants may require human confirmation
- Color detection operates on rendered pixel values and may not detect programmatic CSS color overrides
- Vector SVG files would require rasterization before upload

**Validation Approach:**
- Create 10 test brand assets: 5 compliant (approved logo, correct colors), 5 violating (wrong logo variant, unapproved palette)
- Measure detection accuracy; target ≥80% precision before production release
- All visual findings flagged with `confidence_level` and `human_verification_required=True` by default until accuracy baseline is established

---

## Improvement 2: Multi-Format & Accessibility Review

### Problem It Solves

Promotional content is created and consumed in many formats beyond plain text:
- **HTML email templates** — contain hyperlinks, embedded images, and alt-text requirements
- **Social media posts** — character limits, hashtag conventions, platform-specific restrictions
- **Long-form documents** — whitepapers, case studies with specific section requirements
- **Accessibility** — screen-reader compatibility, sufficient color contrast, alt-text on images, reading level

Current BrandGuard AI accepts only plain text. Pasting an HTML email template into the text field loses structural context; hashtag rules, CTA link checks, and WCAG accessibility requirements are not evaluated.

### What Exists Today

- The compliance engine accepts `content_text` as a plain string
- The `BrandGuideline` model has an `"Accessibility"` category for text-based accessibility rules
- The Gemini prompt already includes "Accessibility & Clarity" as an audit category

### What Round 3 Would Add

**Content Format Support:**

| Format | Analysis Added |
|:---|:---|
| HTML email | Extract visible text; check alt-text on images; validate CTA link labels; check for required unsubscribe footer |
| Social post (Twitter/LinkedIn) | Character count validation; hashtag convention check; platform policy prohibited terms |
| Long-form document | Section structure validation (e.g., required executive summary); citation consistency |

**Backend changes:**
- New field: `ContentSubmission.content_format` (enum: `plain_text`, `html_email`, `social_post`, `document`)
- Format-aware preprocessing pipeline before Gemini prompt construction
- HTML sanitization and text extraction using `html.parser` (stdlib, no new dependency for basic cases)
- Extended prompt section with format-specific rules

**Accessibility Analysis:**
- Reading level estimation using Flesch-Kincaid approximation (implementable without external library)
- Detection of passive constructions, unclear jargon, and undefined acronyms flagged as "Accessibility & Clarity" findings
- Alt-text presence check for HTML formats

**Honest Limitations:**
- WCAG color contrast checks require access to rendered CSS — not available from text/HTML source alone; this would require a browser-based screenshot approach out of scope for Round 3 baseline
- Platform-specific advertising policies (e.g., Meta Ad Policies) are not officially available as machine-readable rulesets and would need manual encoding by brand managers
- Social media format detection is heuristic-based (character count, `#hashtag` pattern) and may misclassify

**Validation Approach:**
- Create test cases: HTML email with missing alt-text, social post exceeding character limit, document missing required section
- Verify each format type is correctly detected and appropriate rules are applied
- Human reviewers confirm flagged accessibility issues are genuine before marking as validated

---

## Improvement 3: Brand Governance Intelligence

### Problem It Solves

BrandGuard AI currently evaluates each submission independently. After dozens of submissions, brand managers have no view into:
- Which violations recur across multiple creators and campaigns
- Which specific creators repeatedly make the same mistakes (suggesting a training gap)
- Which guideline rules generate the most findings (suggesting the rule may be unclear or too strict)
- Whether compliance rates are improving or deteriorating over time

The Governance Analytics dashboard (already built) shows aggregate counts, but provides no **actionable intelligence** — no prioritized recommendations, no per-creator breakdown, no guideline effectiveness signals.

### What Exists Today

- `AnalyticsService.get_governance_analytics()` computes: total submissions by status, severity distribution, category distribution, top 8 common issues, review outcomes, timeline trends — all from live DB records
- `ComplianceFinding` records store `problematic_text`, `category`, `severity`, and `guideline_id` for every finding
- `ContentSubmission.creator_id` links submissions to creators

### What Round 3 Would Add

**Recurring Violation Detection:**
- Identify `problematic_text` phrases or categories that appear in ≥3 distinct submissions
- Surface as "Persistent Brand Risk" alerts on the manager dashboard
- Link directly to the guideline being repeatedly violated

**Creator Pattern Analysis:**
- Per-creator compliance score computed from: (compliant submissions / total submissions) and average findings per submission
- Breakdown of each creator's most frequent violation categories
- Time-series showing whether a creator's compliance rate is improving after receiving "Changes Requested" feedback
- Displayed on manager dashboard under a new "Creator Insights" tab

**Guideline Effectiveness Signals:**
- For each active guideline: count how many analyses referenced it; count how many findings cited it; compute a "violation rate" per guideline
- Surface guidelines with 0 findings (possibly too vague to generate actionable flags) as "Low Signal" warnings
- Surface guidelines cited in >50% of analyses as "High-Impact Rules" to review for clarity

**Backend changes:**
- New endpoint: `GET /api/analytics/creator-insights` (admin only) returning per-creator compliance metrics
- New endpoint: `GET /api/analytics/guideline-effectiveness` returning per-guideline violation rates
- Both computed from existing `ComplianceFinding`, `ComplianceAnalysis`, and `ContentSubmission` tables — no new DB schema required

**Frontend changes:**
- New tabs on the Governance Analytics page: "Creator Insights" and "Guideline Health"
- Ranked creator table with compliance score, trend arrow, and "Schedule Training" action
- Guideline health table with violation rate bars and "Review Rule Clarity" flag

**Honest Limitations:**
- Creator compliance scores reflect AI analysis outcomes, which may be imperfect; scores should be treated as guidance, not performance evaluations
- A guideline with few findings may simply not be relevant to recent campaigns, not necessarily vague; human interpretation is required
- Creator insights require a minimum of 5 submissions per creator to produce statistically meaningful patterns; smaller datasets show warning indicators

**Validation Approach:**
- Seed 20+ test submissions across 3 creators with known violation patterns
- Verify per-creator scores reflect the seeded pattern
- Verify guideline effectiveness counts match raw DB query results
- Have a non-technical stakeholder (simulated brand manager) review the insights and confirm they are actionable and understandable

---

## Implementation Priority

| Feature | Development Effort | Business Value | Feasibility | Priority |
|:---|:---|:---|:---|:---|
| Brand Governance Intelligence | Medium (2–3 weeks) | High — directly improves workflow decisions | High — uses existing data and DB schema | **Round 3 Priority 1** |
| Multi-Format & Accessibility Review | Medium-High (3–4 weeks) | High — broadens platform use cases | Medium — format parsing adds complexity | **Round 3 Priority 2** |
| Visual Brand Compliance Engine | High (4–6 weeks) | High — unlocks visual review market | Medium — depends on Gemini vision accuracy | **Round 3 Priority 3** |

---

## What Round 3 Will NOT Claim

- No automated external fact verification against live websites (requires reliable web grounding integration not yet available in `google-genai` SDK)
- No cryptographically signed audit certificates (out of scope for Round 3 timeline)
- No direct integrations with Canva, Adobe, Figma, or ad platforms
- No real-time collaboration features

These are valid future directions beyond Round 3.
