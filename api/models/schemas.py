"""
Pydantic schemas for request/response validation.

Semua input/output API divalidasi melalui schema ini.
FastAPI akan otomatis generate Swagger docs dari schema ini.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# --- Enums ---

class InputType(str, Enum):
    TEXT = "TEXT"
    URL = "URL"
    IMAGE = "IMAGE"


class Label(str, Enum):
    OBJEKTIF = "OBJEKTIF"
    CENDERUNG_BIAS = "CENDERUNG_BIAS"
    SANGAT_MANIPULATIF = "SANGAT_MANIPULATIF"


# --- Request Schemas ---

class AnalyzeTextRequest(BaseModel):
    """Request body untuk analisis teks langsung."""
    input_type: InputType = Field(
        default=InputType.TEXT,
        description="Tipe input: TEXT, URL, atau IMAGE",
    )
    raw_input: str = Field(
        ...,
        min_length=1,
        description="Teks narasi, URL artikel, atau base64 gambar",
    )


class VoteRequest(BaseModel):
    """Request body untuk memberikan vote."""
    is_agree: bool = Field(
        ...,
        description="True = Setuju dengan analisis AI, False = Tidak Setuju",
    )


class CommentRequest(BaseModel):
    """Request body untuk menambahkan komentar."""
    content: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Isi komentar (maks 2000 karakter)",
    )


# --- Response Schemas ---

class AnalysisResult(BaseModel):
    """Data hasil analisis objektivitas."""
    analysis_id: str
    input_type: InputType
    extracted_text: str
    detected_language: str
    score: int = Field(ge=0, le=100)
    label: Label
    reasoning: str
    buzzer_indicators: list[str] = []
    created_at: datetime


class AnalysisDetail(AnalysisResult):
    """Detail analisis lengkap dengan data komunitas."""
    vote_agree: int = 0
    vote_disagree: int = 0
    comments: list[CommentOut] = []


class CommentOut(BaseModel):
    """Data komentar yang dikembalikan ke frontend."""
    id: str
    user_name: str
    content: str
    created_at: datetime


class TrendingTopic(BaseModel):
    """Data satu topik trending di dashboard."""
    topic: str
    average_score: float
    total_analyzed: int
    label_distribution: dict[str, int] = {}


class VoteOut(BaseModel):
    """Data agregat vote setelah user melakukan vote."""
    vote_agree: int
    vote_disagree: int
    user_vote: bool  # vote yang baru saja diberikan user


# --- Generic API Response Wrapper ---

class APIResponse(BaseModel):
    """Format standar response API."""
    success: bool = True
    data: Optional[dict | list] = None
    message: Optional[str] = None


class APIError(BaseModel):
    """Format standar error API."""
    success: bool = False
    error: str
    code: str


# Resolve forward reference for AnalysisDetail
AnalysisDetail.model_rebuild()
