from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class DetectionItem(BaseModel):
    label: str
    confidence: float
    bbox: List[int]


class FaceMeshResult(BaseModel):
    head_pose: Optional[Dict[str, float]] = None
    gaze_direction: Optional[str] = None


class ViolationItem(BaseModel):
    type: str
    details: Optional[Dict[str, Any]] = None


class LogicResult(BaseModel):
    status: bool
    reason: List[str]
    violations: List[Dict[str, Any]]


class DetectionResponse(BaseModel):
    detections: List[DetectionItem]
    facemesh: Optional[FaceMeshResult] = None
    logic: LogicResult
