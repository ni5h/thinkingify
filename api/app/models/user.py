import enum
import uuid

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class UserRole(str, enum.Enum):
    admin = "admin"
    author = "author"
    learner = "learner"


class AccountType(str, enum.Enum):
    parent = "parent"
    child = "child"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    google_sub: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    # Google's own display name, set once at account creation and never
    # overwritten again (see auth_service.google_sign_in) — first_name/
    # last_name below are the actually user-editable, actually-displayed
    # identity going forward.
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="userrole"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Null until the "Complete your profile" step is done. Independent of
    # UserRole (which is vestigial/unused for authz) and independent of
    # FamilyLink's per-link guardian/child orientation — this is a
    # standing fact about the account itself, editable later in Settings.
    account_type: Mapped[AccountType | None] = mapped_column(
        Enum(AccountType, name="accounttype"), nullable=True
    )
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # Public-facing handle shown on blog bylines. Unique app-wide.
    username: Mapped[str | None] = mapped_column(String(30), unique=True, index=True, nullable=True)
    tagline: Mapped[str | None] = mapped_column(String(140), nullable=True)
    school_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    occupation: Mapped[str | None] = mapped_column(String(150), nullable=True)
    location_city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    location_state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    location_country: Mapped[str | None] = mapped_column(String(100), nullable=True)
