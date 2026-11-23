"""FastAPI Main Application for Gaming Performance Advisor."""
from typing import List
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import CORS_ORIGINS
from backend.schemas import (
    CatalogOptionsResponse,
    HardwareScoreInfo,
    PredictRequest,
    PredictResponse,
)
from backend.services.catalog_service import catalog_service
from backend.services.fps_reference_service import fps_reference_service
from backend.services.hardware_service import (
    DeviceTypeMismatchError,
    HardwareError,
    HardwareNotFoundError,
    hardware_service,
)
from backend.services.ml_service import ml_service
from backend.services.rule_based_service import GameNotFoundError, rule_based_service

app = FastAPI(
    title="Gaming Performance Advisor API",
    description="Hệ thống tư vấn hiệu năng chơi game kết hợp Rule-based và Machine Learning.",
    version="1.0.0",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/", tags=["System"])
async def root():
    """Health check endpoint."""
    return {
        "service": "Gaming Performance Advisor API",
        "status": "online",
        "version": "1.0.0",
        "endpoints": {
            "catalog": "/options",
            "predict": "/predict",
        },
    }


@app.get("/options", response_model=CatalogOptionsResponse, tags=["Catalog"])
async def get_options():
    """Lấy danh mục tùy chọn phần cứng và game cho giao diện Frontend."""
    try:
        return catalog_service.get_options()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi tải danh mục catalog: {str(exc)}",
        )


@app.post("/predict", response_model=PredictResponse, tags=["Prediction"])
@app.post("/analyze", response_model=PredictResponse, tags=["Prediction"])
async def predict_performance(payload: PredictRequest):
    """Phân tích cấu hình máy tính và trả về:

    1. Thông tin điểm phần cứng thực tế (CPU Score, GPU Score).
    2. Đánh giá Rule-based (so sánh với min/rec requirements của game).
    3. FPS Tham chiếu thực tế từ benchmark (chỉ trả khi đúng game & GPU).
    4. Trạng thái Machine Learning (Adapter chờ model thật từ bạn).
    """
    warnings: List[str] = []

    # 1. Tra cứu điểm CPU từ dữ liệu thật
    try:
        canonical_cpu, cpu_score = hardware_service.get_cpu_score(payload.cpu_model)
    except HardwareNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    # 2. Tra cứu điểm GPU từ dữ liệu thật (kiểm tra device_type)
    try:
        canonical_gpu, gpu_type, gpu_g3d_mark = hardware_service.get_gpu_info(
            payload.gpu_model, payload.device_type
        )
    except (DeviceTypeMismatchError, HardwareNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    # Cảnh báo TGP cho laptop nếu chưa nhập
    if payload.device_type == "laptop" and payload.gpu_tgp_w is None:
        warnings.append("Thiếu thông tin TGP của GPU Laptop. Hiệu năng thực tế có thể dao động tùy mức công suất hãng sản xuất thiết lập.")

    # 3. Phân tích Rule-based so với game_requirements.csv
    try:
        rule_result = rule_based_service.evaluate(
            game_name=payload.game,
            user_cpu_score=cpu_score,
            user_gpu_g3d=gpu_g3d_mark,
            user_ram_gb=payload.ram_gb,
        )
    except GameNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    # 4. Tra cứu FPS tham chiếu thực tế từ games_fps_reference.csv
    fps_ref_result = fps_reference_service.get_fps_reference(
        game_name=payload.game,
        gpu_model=canonical_gpu,
        device_type=payload.device_type,
    )
    if not fps_ref_result.has_reference and fps_ref_result.message:
        warnings.append(fps_ref_result.message)

    # 5. Gọi Machine Learning Adapter (chế độ chờ model thật)
    ml_features = {
        "device_type": payload.device_type,
        "cpu_name": canonical_cpu,
        "cpu_gaming_score": cpu_score,
        "gpu_name": canonical_gpu,
        "gpu_g3d_mark": gpu_g3d_mark,
        "ram_gb": payload.ram_gb,
        "game_name": rule_result.game_requirements.game_name,
        "min_cpu_score": rule_result.game_requirements.min_cpu_score,
        "rec_cpu_score": rule_result.game_requirements.rec_cpu_score,
        "min_gpu_g3d": rule_result.game_requirements.min_gpu_g3d,
        "rec_gpu_g3d": rule_result.game_requirements.rec_gpu_g3d,
        "min_ram_gb": rule_result.game_requirements.min_ram_gb,
        "rec_ram_gb": rule_result.game_requirements.rec_ram_gb,
    }
    ml_result = ml_service.predict(ml_features)

    # Cấu trúc phần cứng người dùng
    user_hardware = HardwareScoreInfo(
        device_type=payload.device_type,
        cpu_model=canonical_cpu,
        cpu_score=cpu_score,
        gpu_model=canonical_gpu,
        gpu_score=gpu_g3d_mark,
        gpu_type=gpu_type,
        ram_gb=payload.ram_gb,
    )

    # Gán FPS tham chiếu nếu có và là thiết lập 1080p High
    avg_fps = None
    if fps_ref_result.has_reference and payload.graphics_preset.lower() == "high":
        avg_fps = fps_ref_result.reference_fps

    return PredictResponse(
        user_hardware=user_hardware,
        rule_based=rule_result,
        fps_reference=fps_ref_result,
        machine_learning=ml_result,
        avg_fps=avg_fps,
        one_percent_low_fps=None,
        model_version="waiting_for_user_model",
        is_stub=False,
        warnings=warnings,
    )
