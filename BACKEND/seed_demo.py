"""
BrandGuard AI - Demo Data Seeder
--------------------------------
This script safely and idempotently seeds realistic brand governance data for hackathon judges and evaluators.
It preserves all existing tables and records and does NOT drop anything.

Usage:
    python seed_demo.py
"""

import os
import sys
from app import create_app
from app.models import db, User, Brand, BrandGuideline, ContentSubmission, ContentRevision, ComplianceAnalysis, ComplianceFinding, ReviewDecision

def seed_demo_data():
    app = create_app(os.getenv("FLASK_ENV", "development"))
    
    with app.app_context():
        print("=" * 60)
        print("[*] BrandGuard AI - Seeding Judge Demo Environment")
        print("=" * 60)

        # 1. Create or retrieve Brand Manager
        manager = User.query.filter_by(email="judge.manager@brandguard.ai").first()
        if not manager:
            manager = User(
                username="judge_manager",
                email="judge.manager@brandguard.ai",
                full_name="Alex Rivera (Brand Governance Lead)",
                role="admin"
            )
            manager.set_password("DemoPassword123!")
            db.session.add(manager)
            db.session.flush()
            print("  [+] Created Brand Manager: judge.manager@brandguard.ai")
        else:
            print("  [i] Brand Manager already exists.")

        # 2. Create or retrieve Content Creator
        creator = User.query.filter_by(email="judge.creator@brandguard.ai").first()
        if not creator:
            creator = User(
                username="judge_creator",
                email="judge.creator@brandguard.ai",
                full_name="Morgan Chen (Senior Growth Copywriter)",
                role="creator"
            )
            creator.set_password("DemoPassword123!")
            db.session.add(creator)
            db.session.flush()
            print("  [+] Created Content Creator: judge.creator@brandguard.ai")
        else:
            print("  [i] Content Creator already exists.")

        # 3. Create or retrieve Brand: CloudNova
        brand = Brand.query.filter_by(name="CloudNova").first()
        if not brand:
            brand = Brand(
                name="CloudNova",
                description="Next-generation enterprise hybrid cloud and AI workload orchestration platform.",
                tone_style="Authoritative, innovative, transparent, and enterprise-grade. Avoid hyperbolic or unsubstantiated guarantees.",
                approved_terminology="CloudNova, CloudNova Mesh, CloudNova Kubernetes Service, Multi-Region Orchestrator",
                approved_facts="CloudNova serves over 45,000 global enterprise customers across 32 availability regions with audited 99.99% multi-region uptime SLA. SOC 2 Type II certified.",
                restricted_words="100% downtime-proof, unhackable, zero cost forever, magical, bulletproof guarantee, cheapest in the market",
                prohibited_claims="Zero transaction fees forever, unbreachable encryption, absolute zero latency",
                created_by_id=manager.id
            )
            db.session.add(brand)
            db.session.flush()
            print("  [+] Created Brand Profile: CloudNova")
        else:
            print("  [i] Brand Profile 'CloudNova' already exists.")

        # 4. Assign Creator to Brand
        from app.models.brand import BrandMembership
        existing_membership = BrandMembership.query.filter_by(brand_id=brand.id, user_id=creator.id).first()
        if not existing_membership:
            membership = BrandMembership(
                brand_id=brand.id,
                user_id=creator.id,
                role="contributor"
            )
            db.session.add(membership)
            db.session.flush()
            print("  [+] Assigned Creator to CloudNova governance team.")

        # 5. Seed Core Brand Guidelines (6 Categories)
        guidelines_data = [
            {
                "category": "Restricted Claims",
                "title": "Strict Prohibition of Absolute Availability Claims",
                "rule_content": "Never claim '100% downtime-proof', 'zero downtime guaranteed', or 'unhackable'. Always reference the audited '99.99% multi-region uptime SLA'.",
                "reference_evidence": "CloudNova SLA Master Services Agreement Section 4.2"
            },
            {
                "category": "Approved Facts",
                "title": "Verified Customer Base & SLA Numbers",
                "rule_content": "Promotional copy must accurately state CloudNova's scale: 'over 45,000 global enterprise customers across 32 availability regions'.",
                "reference_evidence": "CloudNova Annual Enterprise Infrastructure Growth Report 2026"
            },
            {
                "category": "Tone",
                "title": "Enterprise Professional Tone & Vocabulary",
                "rule_content": "Maintain an authoritative, transparent, and mission-critical tone. Avoid slang, hype words ('magical', 'game-changing magic'), or casual jargon.",
                "reference_evidence": "CloudNova Corporate Communications & Tone Guide v3.1"
            },
            {
                "category": "Messaging",
                "title": "Mandatory SLA & Security Compliance Footnote",
                "rule_content": "All external campaigns referencing security or uptime must include: 'Independent audit reports and SOC 2 Type II attestation available upon NDA request.'",
                "reference_evidence": "CloudNova Legal Compliance Playbook 2026"
            },
            {
                "category": "Terminology",
                "title": "Standard Product Name Capitalization",
                "rule_content": "The brand name must always be capitalized as 'CloudNova' (CamelCase with no space). Never write 'Cloud Nova' or 'cloudnova'.",
                "reference_evidence": "CloudNova Trademark & Brand Identity Handbook"
            },
            {
                "category": "Accessibility",
                "title": "Clarity and High-Contrast Technical Communication",
                "rule_content": "Communications must articulate clear value for CTOs and DevOps architects without obscure abbreviations or uncaptioned acronyms.",
                "reference_evidence": "WCAG 2.1 Enterprise Accessibility Standards"
            }
        ]

        for g_data in guidelines_data:
            existing_g = BrandGuideline.query.filter_by(brand_id=brand.id, title=g_data["title"]).first()
            if not existing_g:
                guideline = BrandGuideline(
                    brand_id=brand.id,
                    category=g_data["category"],
                    title=g_data["title"],
                    rule_content=g_data["rule_content"],
                    reference_evidence=g_data["reference_evidence"]
                )
                db.session.add(guideline)
        db.session.flush()
        print("  [+] Seeded 6 comprehensive brand guidelines across all categories.")

        # 6. Seed Sample Submissions for Demo Evaluation
        # Submission A: Ready for AI Review (Contains violations to showcase Gemini compliance detection)
        sub_a = ContentSubmission.query.filter_by(title="Q4 Enterprise Infrastructure Campaign (Un-audited Draft)").first()
        if not sub_a:
            sub_a = ContentSubmission(
                creator_id=creator.id,
                brand_id=brand.id,
                title="Q4 Enterprise Infrastructure Campaign (Un-audited Draft)",
                content_text=(
                    "Migrate your enterprise workloads to CloudNova today! Our revolutionary cloud architecture offers a "
                    "100% downtime-proof guarantee with zero cost forever on foundational tiers. Serving over 100,000 customers "
                    "with magical orchestration, cloudnova is the cheapest in the market."
                ),
                status="Draft"
            )
            db.session.add(sub_a)
            db.session.flush()

            rev_a = ContentRevision(
                submission_id=sub_a.id,
                revision_number=1,
                title=sub_a.title,
                content_text=sub_a.content_text,
                reason="Initial copy draft for Q4 growth push",
                created_by_id=creator.id
            )
            db.session.add(rev_a)
            print("  [+] Seeded Demo Submission A (Draft with deliberate policy violations for Gemini testing).")

        # Submission B: Pending Manager Approval (Awaiting Sign-off in Manager Queue)
        sub_b = ContentSubmission.query.filter_by(title="Hybrid Cloud Kubernetes Ad (Pending Review)").first()
        if not sub_b:
            sub_b = ContentSubmission(
                creator_id=creator.id,
                brand_id=brand.id,
                title="Hybrid Cloud Kubernetes Ad (Pending Review)",
                content_text=(
                    "Accelerate mission-critical workloads with CloudNova Kubernetes Service. Architected for resilience "
                    "with an audited 99.99% multi-region uptime SLA, CloudNova powers over 45,000 enterprise organizations "
                    "across 32 global availability regions. Independent audit reports and SOC 2 Type II attestation available upon request."
                ),
                status="Pending Manager Approval"
            )
            db.session.add(sub_b)
            db.session.flush()

            rev_b = ContentRevision(
                submission_id=sub_b.id,
                revision_number=1,
                title=sub_b.title,
                content_text=sub_b.content_text,
                reason="Aligned with CloudNova enterprise guidelines and approved facts",
                created_by_id=creator.id
            )
            db.session.add(rev_b)

            analysis_b = ComplianceAnalysis(
                submission_id=sub_b.id,
                revision_number=1,
                model_identifier="gemini-2.5-flash",
                summary="Copy fully adheres to CloudNova brand rules, SLA citations, and required security disclaimers.",
                review_status="Compliant",
                issues_count=0,
                high_severity_count=0,
                medium_severity_count=0,
                low_severity_count=0,
                is_outdated=False
            )
            db.session.add(analysis_b)
            print("  [+] Seeded Demo Submission B (Pending Manager Sign-off in Review Queue).")

        db.session.commit()
        print("=" * 60)
        print("[OK] Demo seeding completed successfully!")
        print("\nJudge Demo Accounts:")
        print("  1. Brand Manager:   judge.manager@brandguard.ai / DemoPassword123!")
        print("  2. Content Creator: judge.creator@brandguard.ai / DemoPassword123!")
        print("=" * 60)

if __name__ == "__main__":
    seed_demo_data()
