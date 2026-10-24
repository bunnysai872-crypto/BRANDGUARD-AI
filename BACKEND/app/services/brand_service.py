from app.models import db, Brand, BrandMembership, User

class BrandService:
    @staticmethod
    def create_brand(creator_id, data):
        name = (data.get("name") or "").strip()
        if not name or len(name) < 2:
            return None, "Brand name must be at least 2 characters.", 400

        # Check unique
        if Brand.query.filter_by(name=name).first():
            return None, f"Brand with name '{name}' already exists.", 409

        brand = Brand(
            name=name,
            description=(data.get("description") or "").strip(),
            tone_style=(data.get("tone_style") or "").strip(),
            approved_terminology=(data.get("approved_terminology") or "").strip(),
            restricted_words=(data.get("restricted_words") or "").strip(),
            approved_facts=(data.get("approved_facts") or "").strip(),
            prohibited_claims=(data.get("prohibited_claims") or "").strip(),
            created_by_id=creator_id
        )
        db.session.add(brand)
        db.session.flush()

        # Add creator as manager membership
        membership = BrandMembership(
            brand_id=brand.id,
            user_id=creator_id,
            role="manager"
        )
        db.session.add(membership)
        db.session.commit()

        return brand.to_dict(), None, 201

    @staticmethod
    def get_accessible_brands(user_id, role):
        if role == "admin":
            # Admin can access all brands
            brands = Brand.query.order_by(Brand.created_at.desc()).all()
        else:
            # Creator can access brands where they are assigned as member
            brand_ids = [
                m.brand_id for m in BrandMembership.query.filter_by(user_id=user_id).all()
            ]
            brands = Brand.query.filter(Brand.id.in_(brand_ids)).order_by(Brand.name.asc()).all()
        return [b.to_dict() for b in brands]

    @staticmethod
    def get_brand_by_id(brand_id):
        return db.session.get(Brand, brand_id)

    @staticmethod
    def user_has_brand_access(brand_id, user_id, role):
        if role == "admin":
            return True
        membership = BrandMembership.query.filter_by(brand_id=brand_id, user_id=user_id).first()
        return membership is not None

    @staticmethod
    def update_brand(brand_id, data):
        brand = db.session.get(Brand, brand_id)
        if not brand:
            return None, "Brand not found.", 404

        name = (data.get("name") or "").strip()
        if name and name != brand.name:
            if Brand.query.filter_by(name=name).first():
                return None, f"Brand name '{name}' is already taken.", 409
            brand.name = name

        if "description" in data:
            brand.description = (data.get("description") or "").strip()
        if "tone_style" in data:
            brand.tone_style = (data.get("tone_style") or "").strip()
        if "approved_terminology" in data:
            brand.approved_terminology = (data.get("approved_terminology") or "").strip()
        if "restricted_words" in data:
            brand.restricted_words = (data.get("restricted_words") or "").strip()
        if "approved_facts" in data:
            brand.approved_facts = (data.get("approved_facts") or "").strip()
        if "prohibited_claims" in data:
            brand.prohibited_claims = (data.get("prohibited_claims") or "").strip()

        db.session.commit()
        return brand.to_dict(), None, 200

    @staticmethod
    def add_member(brand_id, user_id, role="contributor"):
        brand = db.session.get(Brand, brand_id)
        if not brand:
            return None, "Brand not found.", 404

        user = db.session.get(User, user_id)
        if not user:
            return None, "User not found.", 404

        existing = BrandMembership.query.filter_by(brand_id=brand_id, user_id=user_id).first()
        if existing:
            existing.role = role
            db.session.commit()
            return existing.to_dict(), None, 200

        membership = BrandMembership(brand_id=brand_id, user_id=user_id, role=role)
        db.session.add(membership)
        db.session.commit()
        return membership.to_dict(), None, 201

    @staticmethod
    def remove_member(brand_id, user_id):
        membership = BrandMembership.query.filter_by(brand_id=brand_id, user_id=user_id).first()
        if not membership:
            return False, "Member not found in this brand.", 404

        db.session.delete(membership)
        db.session.commit()
        return True, None, 200

    @staticmethod
    def get_members(brand_id):
        members = BrandMembership.query.filter_by(brand_id=brand_id).all()
        return [m.to_dict() for m in members]

    @staticmethod
    def list_assignable_creators():
        creators = User.query.filter_by(role="creator").order_by(User.username.asc()).all()
        return [c.to_dict() for c in creators]
