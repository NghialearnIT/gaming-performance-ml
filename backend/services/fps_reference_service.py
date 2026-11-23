"""FPS reference service to query actual measured FPS from games_fps_reference.csv."""
import csv
from typing import Dict, List, Optional, Tuple

from backend.config import GAMES_FPS_REFERENCE_PATH
from backend.schemas import FpsReferenceResult


class FpsReferenceService:
    """Service to look up actual measured FPS from games_fps_reference.csv.

    Strict rules:
    - Only map GPUs that have an exact corresponding column in games_fps_reference.csv.
    - No interpolation, extrapolation, or substitution with another GPU.
    - No Desktop FPS substitution for Laptop GPUs.
    - Only provides 1080p High FPS.
    """

    # Mapping: (device_type_lower, normalized_gpu_pattern) -> (column_name, display_gpu_name)
    # Note: 10 of 12 columns are strictly Desktop GPUs. 2 are iGPUs (Iris Xe, 780M).
    # Laptop dedicated GPUs (e.g. RTX 4060 Laptop GPU) MUST NOT map to desktop columns.
    SUPPORTED_GPU_COLUMNS = {
        # Desktop GPUs
        ("desktop", "geforce gtx 1650"): ("fps_1080p_high_gtx_1650", "NVIDIA GeForce GTX 1650 (Desktop)"),
        ("desktop", "gtx 1650"): ("fps_1080p_high_gtx_1650", "NVIDIA GeForce GTX 1650 (Desktop)"),
        ("desktop", "nvidia gtx 1650"): ("fps_1080p_high_gtx_1650", "NVIDIA GeForce GTX 1650 (Desktop)"),
        ("desktop", "geforce gtx 1660 super"): ("fps_1080p_high_gtx_1660_super", "NVIDIA GeForce GTX 1660 SUPER (Desktop)"),
        ("desktop", "gtx 1660 super"): ("fps_1080p_high_gtx_1660_super", "NVIDIA GeForce GTX 1660 SUPER (Desktop)"),
        ("desktop", "nvidia gtx 1660 super"): ("fps_1080p_high_gtx_1660_super", "NVIDIA GeForce GTX 1660 SUPER (Desktop)"),
        ("desktop", "geforce rtx 3060"): ("fps_1080p_high_rtx_3060", "NVIDIA GeForce RTX 3060 (Desktop)"),
        ("desktop", "geforce rtx 3060 12gb"): ("fps_1080p_high_rtx_3060", "NVIDIA GeForce RTX 3060 12GB (Desktop)"),
        ("desktop", "rtx 3060"): ("fps_1080p_high_rtx_3060", "NVIDIA GeForce RTX 3060 (Desktop)"),
        ("desktop", "nvidia rtx 3060"): ("fps_1080p_high_rtx_3060", "NVIDIA GeForce RTX 3060 (Desktop)"),
        ("desktop", "radeon rx 7600"): ("fps_1080p_high_rx_7600", "AMD Radeon RX 7600 (Desktop)"),
        ("desktop", "rx 7600"): ("fps_1080p_high_rx_7600", "AMD Radeon RX 7600 (Desktop)"),
        ("desktop", "geforce rtx 4060"): ("fps_1080p_high_rtx_4060", "NVIDIA GeForce RTX 4060 (Desktop)"),
        ("desktop", "rtx 4060"): ("fps_1080p_high_rtx_4060", "NVIDIA GeForce RTX 4060 (Desktop)"),
        ("desktop", "nvidia rtx 4060"): ("fps_1080p_high_rtx_4060", "NVIDIA GeForce RTX 4060 (Desktop)"),
        ("desktop", "geforce rtx 5060"): ("fps_1080p_high_rtx_5060", "NVIDIA GeForce RTX 5060 (Desktop)"),
        ("desktop", "rtx 5060"): ("fps_1080p_high_rtx_5060", "NVIDIA GeForce RTX 5060 (Desktop)"),
        ("desktop", "geforce rtx 4070"): ("fps_1080p_high_rtx_4070", "NVIDIA GeForce RTX 4070 (Desktop)"),
        ("desktop", "rtx 4070"): ("fps_1080p_high_rtx_4070", "NVIDIA GeForce RTX 4070 (Desktop)"),
        ("desktop", "radeon rx 7800 xt"): ("fps_1080p_high_rx_7800_xt", "AMD Radeon RX 7800 XT (Desktop)"),
        ("desktop", "rx 7800 xt"): ("fps_1080p_high_rx_7800_xt", "AMD Radeon RX 7800 XT (Desktop)"),
        ("desktop", "geforce rtx 5070"): ("fps_1080p_high_rtx_5070", "NVIDIA GeForce RTX 5070 (Desktop)"),
        ("desktop", "rtx 5070"): ("fps_1080p_high_rtx_5070", "NVIDIA GeForce RTX 5070 (Desktop)"),
        ("desktop", "geforce rtx 4090"): ("fps_1080p_high_rtx_4090", "NVIDIA GeForce RTX 4090 (Desktop)"),
        ("desktop", "rtx 4090"): ("fps_1080p_high_rtx_4090", "NVIDIA GeForce RTX 4090 (Desktop)"),
        # iGPUs (Available on Laptop and Desktop)
        ("laptop", "intel iris xe"): ("fps_1080p_high_iris_xe", "Intel Iris Xe Graphics"),
        ("laptop", "iris xe"): ("fps_1080p_high_iris_xe", "Intel Iris Xe Graphics"),
        ("desktop", "intel iris xe"): ("fps_1080p_high_iris_xe", "Intel Iris Xe Graphics"),
        ("desktop", "iris xe"): ("fps_1080p_high_iris_xe", "Intel Iris Xe Graphics"),
        ("laptop", "radeon 780m"): ("fps_1080p_high_radeon_780m", "AMD Radeon 780M"),
        ("laptop", "radeont 780m"): ("fps_1080p_high_radeon_780m", "AMD Radeon 780M"),
        ("desktop", "radeon 780m"): ("fps_1080p_high_radeon_780m", "AMD Radeon 780M"),
    }

    def __init__(self, dataset_path=None):
        self.dataset_path = dataset_path or GAMES_FPS_REFERENCE_PATH
        # Mapping: normalized_game_name -> dict of row data
        self._fps_data: Dict[str, Dict[str, str]] = {}
        self._load_data()

    def _normalize(self, text: str) -> str:
        return text.strip().lower()

    def _load_data(self) -> None:
        """Load benchmark rows from games_fps_reference.csv."""
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Không tìm thấy file: {self.dataset_path}")

        with open(self.dataset_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row["name"].strip()
                if not name:
                    continue
                self._fps_data[self._normalize(name)] = row

    def _find_game_row(self, game_name: str) -> Optional[Dict[str, str]]:
        """Find matching row for game name."""
        g_norm = self._normalize(game_name)
        if g_norm in self._fps_data:
            return self._fps_data[g_norm]

        # Fuzzy match ignoring special characters
        clean_target = "".join(c for c in g_norm if c.isalnum())
        for norm_name, row in self._fps_data.items():
            if "".join(c for c in norm_name if c.isalnum()) == clean_target:
                return row

        return None

    def get_fps_reference(self, game_name: str, gpu_model: str, device_type: str) -> FpsReferenceResult:
        """Tra cứu FPS thực tế từ bảng tham chiếu.

        Tuân thủ:
        - Đúng game và đúng GPU.
        - Không dùng FPS Desktop cho GPU Laptop.
        - Không nội suy/ngoại suy.
        - Trả has_reference: false, reference_fps: null khi không có số liệu.
        """
        d_norm = self._normalize(device_type)
        g_norm = self._normalize(gpu_model)

        # 1. Tìm cột GPU tương ứng
        gpu_col_info = self.SUPPORTED_GPU_COLUMNS.get((d_norm, g_norm))
        if not gpu_col_info:
            # Check if this GPU is a laptop GPU that doesn't have an exact benchmark column
            if d_norm == "laptop" and "laptop" in g_norm:
                msg = f"GPU Laptop '{gpu_model}' không có cột đo FPS riêng trong bảng tham chiếu (hệ thống không dùng FPS Desktop thay thế)."
            else:
                msg = f"GPU '{gpu_model}' ({device_type.capitalize()}) không có cột đo FPS thực tế trong bảng tham chiếu games_fps_reference.csv."
            return FpsReferenceResult(
                has_reference=False,
                reference_fps=None,
                resolution="1920x1080",
                graphics_preset="high",
                gpu_matched=None,
                message=msg,
            )

        col_name, display_gpu = gpu_col_info

        # 2. Tìm thông tin game
        game_row = self._find_game_row(game_name)
        if not game_row:
            return FpsReferenceResult(
                has_reference=False,
                reference_fps=None,
                resolution="1920x1080",
                graphics_preset="high",
                gpu_matched=display_gpu,
                message=f"Game '{game_name}' không có trong bảng dữ liệu tham chiếu FPS games_fps_reference.csv.",
            )

        # 3. Đọc giá trị FPS từ cột
        fps_str = game_row.get(col_name, "").strip()
        if not fps_str:
            return FpsReferenceResult(
                has_reference=False,
                reference_fps=None,
                resolution="1920x1080",
                graphics_preset="high",
                gpu_matched=display_gpu,
                message=f"Game '{game_name}' chưa có số liệu đo FPS trên GPU '{display_gpu}'.",
            )

        try:
            fps_val = float(fps_str)
            if fps_val <= 0:
                return FpsReferenceResult(
                    has_reference=False,
                    reference_fps=None,
                    resolution="1920x1080",
                    graphics_preset="high",
                    gpu_matched=display_gpu,
                    message="Giá trị FPS trong bảng dữ liệu không hợp lệ (<= 0).",
                )
            return FpsReferenceResult(
                has_reference=True,
                reference_fps=fps_val,
                resolution="1920x1080",
                graphics_preset="high",
                gpu_matched=display_gpu,
                message=None,
            )
        except ValueError:
            return FpsReferenceResult(
                has_reference=False,
                reference_fps=None,
                resolution="1920x1080",
                graphics_preset="high",
                gpu_matched=display_gpu,
                message="Lỗi đọc định dạng số liệu FPS trong bảng benchmark.",
            )


# Singleton instance
fps_reference_service = FpsReferenceService()
