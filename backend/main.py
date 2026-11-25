"""FastAPI endpoints for hardware compatibility and gaming FPS."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from backend.config import CORS_ORIGINS, FPS_PRESET, FRONTEND_DIR
from backend.schemas import (
    CatalogOptionsResponse,
    ComponentCheck,
    GameRequirementDetail,
    RuleBasedResult,
    FpsReferenceResult,
    HardwareScoreInfo,
    PredictRequest,
    PredictResponse,
)
from backend.services.catalog_service import catalog_service
from backend.services.fps_reference_service import (
    GAME_ALIASES,
    REFERENCE_ONLY_GAMES,
    fps_reference_service,
)
from backend.services.hardware_service import HardwareError, hardware_service
from backend.services.ml_service import ml_service
from backend.services.rule_based_service import GameNotFoundError, rule_based_service

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    matched, extra = fps_reference_service.verify_cross_dataset_integrity(
        rule_based_service.get_all_page_urls()
    )
    logger.info("Loaded %d game requirements and %d additional FPS reference rows.", matched, extra)
    ml_service.load()
    yield


app = FastAPI(
    title="Gaming Performance ML API",
    description="Đánh giá cấu hình và ước tính FPS chơi game ở 1080p High.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


@app.get("/", tags=["System"])
def root(request: Request):
    if "text/html" in request.headers.get("accept", ""):
        return RedirectResponse("/app/")
    return {
        "service": "Gaming Performance ML API",
        "status": "online",
        "version": app.version,
        "endpoints": {"catalog": "/options", "predict": "/predict", "frontend": "/app/"},
    }


@app.get("/options", response_model=CatalogOptionsResponse, tags=["Catalog"])
def get_options():
    return catalog_service.get_options()


@app.post("/predict", response_model=PredictResponse, tags=["Prediction"])
@app.post("/analyze", response_model=PredictResponse, tags=["Prediction"])
def predict_performance(payload: PredictRequest):
    warnings: list[str] = []
    try:
        cpu_name, cpu_score = hardware_service.get_cpu_score(payload.cpu_model)
        gpu_name, gpu_type, gpu_score = hardware_service.get_gpu_info(payload.gpu_model, payload.device_type)
    except HardwareError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    game_name = GAME_ALIASES.get(payload.game.casefold(), payload.game)
    try:
        rule_result = rule_based_service.evaluate(game_name, cpu_score, gpu_score, payload.ram_gb)
        page_url = rule_result.game_requirements.page_url
    except GameNotFoundError as exc:
        page_url = next(
            (url for name, url in REFERENCE_ONLY_GAMES.items() if name.casefold() == game_name.casefold()),
            None,
        )
        if page_url is None or fps_reference_service.get_row(page_url) is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        row = fps_reference_service.get_row(page_url)
        requirement = GameRequirementDetail(
            game_name=row["name"], page_url=page_url, min_cpu_description=row["min_cpu"],
            min_gpu_g3d=float(row["min_gpu_g3d"]), min_ram_gb=float(row["min_ram_gb"]),
        )
        components = {}
        for key, actual, minimum in (
            ("gpu", gpu_score, requirement.min_gpu_g3d),
            ("ram", payload.ram_gb, requirement.min_ram_gb),
        ):
            passed = actual >= minimum
            components[key] = ComponentCheck(
                component=key.upper(), user_value=actual, min_value=minimum,
                passed_min=passed, status="passed_min" if passed else "below_min",
            )
        failed = [key.upper() for key, check in components.items() if not check.passed_min]
        rule_result = RuleBasedResult(
            status="Khong_dat_toi_thieu" if failed else "Partial_minimum",
            status_label="Dưới mức tối thiểu" if failed else "GPU và RAM đạt tối thiểu",
            summary=("Dưới ngưỡng tối thiểu: " + ", ".join(failed)) if failed else
                    "GPU và RAM đạt ngưỡng tối thiểu. CPU cần đối chiếu với yêu cầu bên dưới.",
            components=components, game_requirements=requirement,
        )

    if payload.device_type == "laptop" and payload.gpu_tgp_w is None:
        warnings.append("Chưa nhập TGP. Hiệu năng GPU laptop có thể thay đổi theo giới hạn công suất và tản nhiệt.")

    avg_fps = None
    fps_source = None
    if payload.graphics_preset != FPS_PRESET:
        fps_message = "Chưa có dữ liệu FPS cho mức đồ họa này. Chọn 1080p High để xem kết quả."
        reference = FpsReferenceResult(has_reference=False, message=fps_message)
        ml_result = ml_service.status("unsupported_preset", fps_message)
    else:
        reference = fps_reference_service.get_fps_reference(
            game_name, gpu_name, payload.device_type, page_url=page_url,
        )
        if rule_result and rule_result.status == "Khong_dat_toi_thieu":
            fps_message = "Cấu hình dưới mức tối thiểu. Hệ thống chỉ hiển thị FPS tham chiếu của game và GPU nếu có."
            ml_result = ml_service.status("below_minimum_requirements", fps_message)
        elif reference.has_reference:
            avg_fps = reference.reference_fps
            fps_source = "reference"
            fps_message = "FPS tham chiếu cho game và GPU ở 1080p High. CPU và RAM không quyết định số tham chiếu này."
            ml_result = ml_service.status("reference_available", "Đã có FPS tham chiếu cho game và GPU.")
        else:
            game_row = fps_reference_service.get_row(page_url) or {}
            ml_result = ml_service.predict(game_row, gpu_score)
            if ml_result.prediction:
                avg_fps = ml_result.prediction["avg_fps"]
                fps_source = "ml_estimate"
                fps_message = (
                    "Ước tính ở 1080p High dựa trên điểm GPU và dữ liệu tham chiếu của game. "
                    "CPU, RAM và TGP chưa được dùng làm đầu vào của mô hình FPS."
                )
            else:
                fps_message = ml_result.message

    return PredictResponse(
        user_hardware=HardwareScoreInfo(
            device_type=payload.device_type,
            cpu_model=cpu_name,
            cpu_score=cpu_score,
            gpu_model=gpu_name,
            gpu_score=gpu_score,
            gpu_type=gpu_type,
            ram_gb=payload.ram_gb,
        ),
        rule_based=rule_result,
        fps_reference=reference,
        machine_learning=ml_result,
        fps_source=fps_source,
        fps_message=fps_message,
        avg_fps=avg_fps,
        model_version=ml_result.model_version or "unavailable",
        warnings=warnings,
    )


app.mount("/app", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
