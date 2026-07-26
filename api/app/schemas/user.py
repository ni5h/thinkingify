import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, computed_field, field_validator
from slugify import slugify

from app.models.user import AccountType, User, UserRole

# Equally-weighted signals behind profile_completion_percent — the
# account-type-specific field (school vs occupation) is picked per row.
# Location fields are deliberately excluded (see ProfileUpdate/plan notes:
# still editable, just not part of the completion nudge since it's the
# most sensitive optional field for a child account).
_COMMON_COMPLETION_FIELDS = ("first_name", "last_name", "username", "avatar_url", "tagline")


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    name: str
    avatar_url: str | None
    role: UserRole
    is_active: bool
    created_at: datetime

    account_type: AccountType | None
    first_name: str | None
    last_name: str | None
    username: str | None
    tagline: str | None
    school_name: str | None
    occupation: str | None
    location_city: str | None
    location_state: str | None
    location_country: str | None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def profile_completion_percent(self) -> int:
        if self.account_type is None:
            return 0
        type_field = self.school_name if self.account_type == AccountType.child else self.occupation
        signals = [getattr(self, field) for field in _COMMON_COMPLETION_FIELDS] + [type_field]
        filled = sum(1 for value in signals if value)
        return round(100 * filled / len(signals))


class UserPublicSummary(BaseModel):
    """Public-safe tier: what a blog byline can show. Never last_name,
    location, or email — display_name is computed once, server-side, so
    that rule can't be broken by a future frontend change."""

    id: uuid.UUID
    display_name: str | None
    avatar_url: str | None

    @staticmethod
    def from_user(user: User) -> "UserPublicSummary":
        display_name = user.username or user.first_name or None
        return UserPublicSummary(id=user.id, display_name=display_name, avatar_url=user.avatar_url)


class UserLinkedProfileOut(BaseModel):
    """What an accepted guardian/child (or the user themself) can see —
    everything except the account-internal role/is_active/created_at."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    avatar_url: str | None
    account_type: AccountType | None
    first_name: str | None
    last_name: str | None
    username: str | None
    tagline: str | None
    school_name: str | None
    occupation: str | None
    location_city: str | None
    location_state: str | None
    location_country: str | None


class ProfileUpdate(BaseModel):
    account_type: AccountType | None = None
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    avatar_url: str | None = None
    tagline: str | None = None
    school_name: str | None = None
    occupation: str | None = None
    location_city: str | None = None
    location_state: str | None = None
    location_country: str | None = None

    @field_validator("username")
    @classmethod
    def _normalize_username(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = slugify(value, separator="-")
        if not (3 <= len(normalized) <= 30):
            raise ValueError("Username must be 3-30 characters (letters, numbers, dashes).")
        return normalized
