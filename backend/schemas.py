"""Strict request and explicit response contracts for the versioned API."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, FiniteFloat


JsonNumber = Annotated[FiniteFloat | None, Field(description="Finite numeric value or null")]


class WaterPointPredictionRequest(BaseModel):
    """One row of the locked model's 32 raw predictors; every key is required."""

    model_config = ConfigDict(extra="forbid")

    country: str | None
    admin1: str | None
    latitude_wp: JsonNumber
    longitude_wp: JsonNumber
    elevation_wp: JsonNumber
    cwfunded_wp: str | None
    wptype: str | None
    pumptype: str | None
    drillmethod: str | None
    piped_source: str | None
    piped_pump: str | None
    rehabyn: str | None
    qtyhh_wp: JsonNumber
    whomanage_wp: str | None
    wp_age: JsonNumber
    rehab_age: JsonNumber
    qtypeople_wp: JsonNumber
    lockedfullday_wp: str | None
    pumpstrokes: JsonNumber
    wc_present_wp: str | None
    paytocollect_wp: str | None
    improved_wponly_wp: JsonNumber
    qtyhh_c_wp: JsonNumber
    wc_admin_index_wp: str | None
    wc_finance_index_wp: str | None
    wc_mgmt_index_wp: str | None
    wc_maint_index_wp: str | None
    wc_savings_wp: JsonNumber
    wpqty_wp: JsonNumber
    pop_1000: JsonNumber
    annual_rain: JsonNumber
    season: str | None


class PredictionResult(BaseModel):
    class_id: int
    label: str
    confidence: float = Field(description="Maximum model probability; not a calibrated certainty")


class WaterPointPredictionResponse(BaseModel):
    prediction: PredictionResult
    probabilities: dict[str, float] = Field(description="Model probabilities, keyed by class label")
    model_version: str


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list[dict[str, object]] | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody
