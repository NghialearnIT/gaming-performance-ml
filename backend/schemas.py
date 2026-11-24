"""Pydantic schemas for request and response models."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class PredictRequest(BaseModel):
    """User hardware and game configuration input."""
    device_type: str = Field(..., description="Loại thiết bị: desktop hoặc laptop")
    cpu_model: str = Field(..., description="Tên CPU")
    gpu_model: str = Field(..., description="Tên GPU")
    ram_gb: int = Field(..., ge=1, description="Dung lượng RAM (GB), tối thiểu 1GB")
    gpu_vram_gb: Optional[float] = Field(None, ge=0, description="Dung lượng VRAM (GB)")
    gpu_tgp_w: Optional[float] = Field(None, ge=0, description="Công suất GPU laptop (W)")
    ram_type: Optional[str] = Field(None, description="Thế hệ RAM: DDR4, DDR5, ...")
    ram_channels: Optional[str] = Field(None, description="Kênh RAM: single, dual, quad")
    game: str = Field(..., description="Tên game được lựa chọn")
    resolution: str = Field("1920x1080", description="Độ phân giải")
    graphics_preset: str = Field("high", description="Thiết lập đồ họa: low, medium, high")

    @field_validator("device_type")
    @classmethod
    def validate_device_type(cls, v: str) -> str:
        clean = v.strip().lower()
        if clean not in ("desktop", "laptop"):
            raise ValueError("device_type phải là 'desktop' hoặc 'laptop'")
        return clean

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
    resolution: str = "1920x1080"
    graphics_preset: str = "high"
    gpu_matched: Optional[str] = None
    message: Optional[str] = None
    page_url: Optional[str] = None


class MachineLearningResult(BaseModel):
    """Machine Learning prediction result (interface waiting for user model)."""
    model_loaded: bool = False
    model_version: Optional[str] = None
    status: str = "waiting_for_user_model"
    message: str = "Chưa tích hợp mô hình ML (chờ mô hình thật từ bạn)"
    prediction: Optional[Dict[str, Any]] = None


class PredictResponse(BaseModel):
    """Comprehensive API response containing separate, transparent result sections."""
    user_hardware: HardwareScoreInfo
    rule_based: RuleBasedResult
    fps_reference: FpsReferenceResult
    machine_learning: MachineLearningResult
    avg_fps: Optional[float] = None
    one_percent_low_fps: Optional[float] = None
    model_version: str = "waiting_for_user_model"
    is_stub: bool = False
    warnings: List[str] = []


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
    cpu_models: List[CatalogItem]
    gpu_models: List[CatalogItem]
    desktop_gpus: List[CatalogItem]
    laptop_gpus: List[CatalogItem]
    ram_types: List[str]
    ram_channels: List[CatalogItem]
