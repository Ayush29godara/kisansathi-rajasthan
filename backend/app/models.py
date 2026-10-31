"""SQLAlchemy Database Models for KisanSathi Rajasthan."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Numeric, Date, DateTime, Text, JSON, Integer, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.db import Base


class GUID(TypeDecorator):
    """Platform-independent GUID type.
    
    Uses PostgreSQL's native UUID type when running on Postgres (Supabase),
    and String(36) when running on SQLite (in-memory test suite).
    Transparently coerces strings to UUIDs for seamless compatibility.
    """
    impl = PG_UUID
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            if isinstance(value, uuid.UUID):
                return value
            try:
                return uuid.UUID(str(value))
            except (ValueError, AttributeError):
                return uuid.uuid5(uuid.NAMESPACE_DNS, str(value))
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return str(value)


def utc_now():
    return datetime.now(timezone.utc)


class ProfileModel(Base):
    """User preferences mapped to Supabase public.profiles table."""
    __tablename__ = "profiles"

    user_id = Column(GUID, primary_key=True)
    language = Column(String, nullable=False, default="hi")
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class FarmModel(Base):
    """Farm profile mapped to Supabase public.farms table."""
    __tablename__ = "farms"

    farm_id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, nullable=False, index=True)
    district = Column(String, nullable=False)
    tehsil = Column(String, nullable=False)
    crop = Column(String, nullable=False)
    land_hectare = Column(Numeric(10, 2), nullable=False)
    irrigation = Column(String, nullable=False)
    sowing_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class MessageModel(Base):
    """Advisor chat history mapped to Supabase public.messages table."""
    __tablename__ = "messages"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, nullable=False, index=True)
    question = Column(Text, nullable=False)
    intent = Column(String, nullable=False)
    answer = Column(Text, nullable=False)
    sources = Column(JSON, nullable=False, default=list)
    model_version = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)


class MandiPriceModel(Base):
    """Historical and current APMC mandi prices mapped to public.mandi_prices table."""
    __tablename__ = "mandi_prices"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    mandi = Column(String, nullable=False, index=True)
    commodity = Column(String, nullable=False, index=True)
    price_date = Column(Date, nullable=False)
    min_price = Column(Numeric(10, 2), nullable=False)
    max_price = Column(Numeric(10, 2), nullable=False)
    modal_price = Column(Numeric(10, 2), nullable=False)
    arrivals = Column(Numeric(10, 2), default=0.0)
    created_at = Column(DateTime(timezone=True), default=utc_now)


class DiseasePredictionModel(Base):
    """Crop disease diagnosis history mapped to public.disease_predictions table."""
    __tablename__ = "disease_predictions"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, nullable=False, index=True)
    crop = Column(String, nullable=False)
    predicted_label = Column(String, nullable=False)
    confidence = Column(Numeric(5, 4), nullable=False)
    model_version = Column(String, nullable=False)
    image_path = Column(String, nullable=True)  # Nullable: saved only when user explicitly opted in
    created_at = Column(DateTime(timezone=True), default=utc_now)


class TrainingImageModel(Base):
    """Catalog of training images with file hashes preventing data leakage across splits."""
    __tablename__ = "training_images"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    file_hash = Column(String, unique=True, nullable=False, index=True)
    crop = Column(String, nullable=False)
    label = Column(String, nullable=False)
    source = Column(String, nullable=False)
    split = Column(String, nullable=False)  # 'train', 'val', 'test'
    created_at = Column(DateTime(timezone=True), default=utc_now)


class FeedbackModel(Base):
    """Farmer feedback mapped to Supabase public.feedback table."""
    __tablename__ = "feedback"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    message_id = Column(GUID, nullable=True, index=True)
    user_id = Column(GUID, nullable=False, index=True)
    rating = Column(Integer, nullable=False)  # -1 (thumbs down), 1 (thumbs up), or 1-5
    actual_outcome = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
