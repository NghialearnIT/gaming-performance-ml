"""Pydantic schemas for request and response models."""
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator

from backend.config import FPS_PRESET, FPS_RESOLUTION


class PredictRequest(BaseModel):
    """User hardware and game configuration input."""
    device_type: str = Field(..., description="Loại thiết bị: desktop hoặc laptop")
    cpu_model: str = Field(..., description="Tên CPU")
    gpu_model: str = Field(..., description="Tên GPU")
    ram_gb: int = Field(..., ge=1, description="Dung lượng RAM (GB), tối thiểu 1GB")
    gpu_vram_gb: Optional[float] = Field(None, gt=0, allow_inf_nan=False, description="Dung lượng VRAM (GB)")
    gpu_tgp_w: Optional[float] = Field(None, gt=0, allow_inf_nan=False, description="Công suất GPU laptop (W)")
    ram_type: Optional[str] = Field(None, description="Thế hệ RAM: DDR4, DDR5, ...")
    ram_channels: Optional[str] = Field(None, description="Kênh RAM: single, dual, quad")
    game: str = Field(..., description="Tên game được lựa chọn")
    resolution: str = Field(FPS_RESOLUTION, description="Độ phân giải")
    graphics_preset: str = Field(FPS_PRESET, description="Thiết lập đồ họa: low, medium, high")

    @field_validator("device_type")
    @classmethod
    def validate_device_type(cls, v: str) -> str:
        clean = v.strip().lower()
        if clean not in ("desktop", "laptop"):
            raise ValueError("device_type phải là 'desktop' hoặc 'laptop'")
        return clean

    @field_validator("resolution")
    @classmethod
    def validate_resolution(cls, value: str) -> str:
        normalized = "".join(value.lower().replace("×", "x").split())
        if normalized != FPS_RESOLUTION:
            raise ValueError("Độ phân giải hiện hỗ trợ là 1920x1080.")
        return normalized

    @field_validator("graphics_preset")
    @classmethod
    def validate_graphics_preset(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in ("low", "medium", "high"):
            raise ValueError("Mức đồ họa phải là low, medium hoặc high.")
        return normalized

    @field_validator("cpu_model", "gpu_model", "game")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Không được để trống trường này")
        return clean


class HardwareScoreInfo(BaseModel):
    """Real hardware scores looked up from benchmark dataset."""
    device_type: str
    cpu_model: str
    cpu_score: float
    gpu_model: str
    gpu_score: float
    gpu_type: str
    ram_gb: int


class ComponentCheck(BaseModel):
    """Check status for an individual hardware component."""
    component: str
    user_value: float
    min_value: float
    rec_value: float
    passed_min: bool
    passed_rec: bool
    status: str  # 'passed_rec', 'passed_min', 'below_min'


class GameRequirementDetail(BaseModel):
    """Game requirements detail from game_requirements.csv."""
    game_name: str
    release_year: Optional[float] = None
    min_cpu_score: float
    rec_cpu_score: float
    min_gpu_g3d: float
    rec_gpu_g3d: float
    min_ram_gb: float
    rec_ram_gb: float
    page_url: Optional[str] = None


class RuleBasedResult(BaseModel):
    """Result of rule-based evaluation comparing hardware against game requirements."""
    status: str  # 'Dat_de_xuat', 'Dat_toi_thieu_chua_dat_de_xuat', 'Khong_dat_toi_thieu'
    status_label: str
    summary: str
    components: Dict[str, ComponentCheck]
    game_requirements: GameRequirementDetail


class FpsReferenceResult(BaseModel):
    """Result of FPS benchmark reference lookup."""
    has_reference: bool
    reference_fps: Optional[float] = None
    resolution: str = FPS_RESOLUTION
    graphics_preset: str = FPS_PRESET
    gpu_matched: Optional[str] = None
    message: Optional[str] = None
    page_url: Optional[str] = None


class MachineLearningResult(BaseModel):
    """Prediction and status of the FPS regression model."""
    model_loaded: bool = False
    model_version: Optional[str] = None
    status: str = "unavailable"
    message: str = "Chưa có mô hình FPS."
    prediction: Optional[Dict[str, float]] = None


class PredictResponse(BaseModel):
    """Comprehensive API response containing separate, transparent result sections."""
    user_hardware: HardwareScoreInfo
    rule_based: Optional[RuleBasedResult] = None
    fps_reference: FpsReferenceResult
    machine_learning: MachineLearningResult
    avg_fps: Optional[float] = None
    one_percent_low_fps: Optional[float] = None
    fps_source: Optional[Literal["reference", "ml_estimate"]] = None
    fps_message: Optional[str] = None
    model_version: str = "unavailable"
    is_stub: bool = False
    warnings: List[str] = Field(default_factory=list)


class CatalogItem(BaseModel):
    """Catalog item with value and display label."""
    value: str
    label: str


class CatalogOptionsResponse(BaseModel):
    """Catalog options response for GET /options."""
    device_types: List[CatalogItem]
    games: List[CatalogItem]
    resolutions: List[CatalogItem]
    graphics_presets: List[CatalogItem]
    fps_presets: List[str]
    cpu_models: List[CatalogItem]
    gpu_models: List[CatalogItem]
    desktop_gpus: List[CatalogItem]
    laptop_gpus: List[CatalogItem]
    ram_types: List[str]
    ram_channels: List[CatalogItem]
