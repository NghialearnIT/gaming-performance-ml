"""FPS reference service to query FPS reference values from games_fps_reference.csv."""
import csv
import logging
import math
from collections import defaultdict
from typing import Dict, Iterator, List, Optional, Set, Tuple

from backend.config import GAMES_FPS_REFERENCE_PATH
from backend.schemas import FpsReferenceResult

logger = logging.getLogger("backend.fps_reference_service")

# These games are present in the FPS table but lack a complete requirements row.
REFERENCE_ONLY_GAMES = {
    "Valorant": "https://pcgamebenchmarks.com/game/valorant-116721",
    "Counter-Strike 2": "https://pcgamebenchmarks.com/game/counter-strike-2-223898",
    "League of Legends": "https://pcgamebenchmarks.com/game/league-of-legends-115",
}
GAME_ALIASES = {"cs2": "Counter-Strike 2", "lol": "League of Legends", "pubg": "PUBG: Battlegrounds"}


class DataIntegrityError(Exception):
    """Raised when data integrity violation is detected in games_fps_reference.csv."""
    pass


class FpsReferenceService:
    """Service to look up FPS reference values from games_fps_reference.csv.

    Strict rules:
    - Only map GPUs that have an exact corresponding column in games_fps_reference.csv.
    - No interpolation, extrapolation, or substitution with another GPU.
    - No Desktop FPS substitution for Laptop GPUs.
    - Only provides 1080p High FPS.
    - Two-level lookup mechanism:
        Level 1: Exact 1-to-1 matching via page_url (no fallback to name if URL missing/invalid).
        Level 2: Ambiguity detection for free-text game names (all records must have identical valid FPS).
    """

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
        # Mapping: page_url -> Dict[str, str] (Exact 1-1 primary key)
        self._fps_by_url: Dict[str, Dict[str, str]] = {}
        # Mapping: normalized_game_name -> List[Dict[str, str]] (Group of all candidate rows)
        self._fps_by_name: Dict[str, List[Dict[str, str]]] = defaultdict(list)
        self._load_data()

    def _normalize(self, text: str) -> str:
        return text.strip().lower()

    def iter_rows(self) -> Iterator[Dict[str, str]]:
        return iter(self._fps_by_url.values())

    def get_row(self, page_url: Optional[str]) -> Optional[Dict[str, str]]:
        return self._fps_by_url.get(page_url) if page_url else None

    def get_gpu_column(self, gpu_model: str, device_type: str) -> Optional[Tuple[str, str]]:
        return self.SUPPORTED_GPU_COLUMNS.get((self._normalize(device_type), self._normalize(gpu_model)))

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

                # Chuẩn hóa page_url: chỉ strip khoảng trắng đầu/cuối, giữ nguyên cấu trúc
                page_url = (row.get("page_url") or "").strip()
                if not page_url:
                    raise DataIntegrityError(f"Phát hiện bản ghi game '{name}' thiếu page_url trong games_fps_reference.csv.")
                if page_url in self._fps_by_url:
                    raise DataIntegrityError(f"Phát hiện trùng lặp page_url trong games_fps_reference.csv: '{page_url}'.")

                self._fps_by_url[page_url] = row
                self._fps_by_name[self._normalize(name)].append(row)

    def verify_cross_dataset_integrity(self, requirements_urls: Set[str]) -> Tuple[int, int]:
        """Kiểm tra toàn vẹn dữ liệu quan hệ giữa game_requirements và games_fps_reference.

        Quy tắc:
        - Toàn bộ URL Requirements đều phải tồn tại trong FPS Reference.
        - Nếu thiếu dù chỉ 1 URL -> raise DataIntegrityError để chặn Backend khởi động.
        - Nếu FPS Reference có URL dư -> ghi nhận thống kê và log info (không xóa dữ liệu).

        Returns:
            Tuple[int, int]: (số lượng URL Requirements khớp, số lượng URL dư trong FPS Reference)
        """
        fps_urls = set(self._fps_by_url.keys())
        missing_urls = sorted(list(requirements_urls - fps_urls))
        if missing_urls:
            sample_missing = ", ".join(f"'{u}'" for u in missing_urls[:3])
            raise DataIntegrityError(
                f"Phát hiện {len(missing_urls)} page_url trong game_requirements.csv "
                f"không tồn tại trong games_fps_reference.csv (Ví dụ: {sample_missing})."
            )
        total_req_urls = len(requirements_urls)
        total_fps_urls = len(fps_urls)
        extra_urls = fps_urls - requirements_urls
        extra_count = len(extra_urls)

        logger.info(
            "Data Integrity Check OK: Toàn bộ %d page_url từ Requirements đều tồn tại trong FPS Reference. "
            "Tổng số URL benchmark trong FPS Reference: %d. Số URL benchmark mở rộng chỉ có trong FPS Reference: %d.",
            total_req_urls,
            total_fps_urls,
            extra_count,
        )
        return total_req_urls, extra_count

    def _parse_fps_from_row(
        self, row: Dict[str, str], col_name: str, display_gpu: str, page_url: Optional[str] = None
    ) -> FpsReferenceResult:
        """Trích xuất và xác thực giá trị FPS từ một dòng dữ liệu duy nhất."""
        fps_str = (row.get(col_name) or "").strip()
        if not fps_str:
            return FpsReferenceResult(
                has_reference=False,
                reference_fps=None,
                resolution="1920x1080",
                graphics_preset="high",
                gpu_matched=display_gpu,
                message=f"Game chưa có số liệu đo FPS trên GPU '{display_gpu}'.",
                page_url=page_url,
            )

        try:
            fps_val = float(fps_str)
            if not math.isfinite(fps_val) or fps_val <= 0:
                return FpsReferenceResult(
                    has_reference=False,
                    reference_fps=None,
                    resolution="1920x1080",
                    graphics_preset="high",
                    gpu_matched=display_gpu,
                    message="Giá trị FPS trong bảng dữ liệu không hợp lệ (<= 0).",
                    page_url=page_url,
                )
            return FpsReferenceResult(
                has_reference=True,
                reference_fps=fps_val,
                resolution="1920x1080",
                graphics_preset="high",
                gpu_matched=display_gpu,
                message=None,
                page_url=page_url,
            )
        except ValueError:
            return FpsReferenceResult(
                has_reference=False,
                reference_fps=None,
                resolution="1920x1080",
                graphics_preset="high",
                gpu_matched=display_gpu,
                message="Lỗi đọc định dạng số liệu FPS trong bảng benchmark.",
                page_url=page_url,
            )

    def get_fps_reference(
        self,
        game_name: str,
        gpu_model: str,
        device_type: str,
        page_url: Optional[str] = None,
    ) -> FpsReferenceResult:
        """Tra cứu FPS thực tế từ bảng tham chiếu với cơ chế hai cấp độ.

        Level 1: Tra cứu chính xác theo page_url (nếu có).
                 Tuyệt đối không fallback sang tìm theo tên nếu URL không khớp.
        Level 2: Tra cứu theo tên game tự do (phát hiện đa nghĩa).
                 Chỉ trả FPS khi tất cả bản ghi đều có FPS hợp lệ và đồng nhất.
        """
        d_norm = self._normalize(device_type)
        g_norm = self._normalize(gpu_model)

        # 1. Xác thực cột GPU
        gpu_col_info = self.get_gpu_column(gpu_model, device_type)
        if not gpu_col_info:
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
                page_url=page_url.strip() if page_url else None,
            )

        col_name, display_gpu = gpu_col_info

        # 2. Cấp độ 1: Tra cứu bằng page_url (ưu tiên tuyệt đối)
        if page_url is not None and page_url.strip():
            clean_url = page_url.strip()
            row = self._fps_by_url.get(clean_url)
            if not row:
                return FpsReferenceResult(
                    has_reference=False,
                    reference_fps=None,
                    resolution="1920x1080",
                    graphics_preset="high",
                    gpu_matched=display_gpu,
                    message=f"Không tìm thấy dữ liệu benchmark FPS tương ứng với page_url '{clean_url}' trong games_fps_reference.csv.",
                    page_url=clean_url,
                )
            return self._parse_fps_from_row(row, col_name, display_gpu, clean_url)

        # 3. Cấp độ 2: Tra cứu theo tên game tự do (phát hiện đa nghĩa)
        candidate_rows = self._fps_by_name.get(self._normalize(game_name), [])
        if not candidate_rows:
            # Tìm kiếm gần đúng (bỏ qua ký tự đặc biệt)
            clean_target = "".join(c for c in self._normalize(game_name) if c.isalnum())
            for norm_name, rlist in self._fps_by_name.items():
                if "".join(c for c in norm_name if c.isalnum()) == clean_target:
                    candidate_rows.extend(rlist)

        if not candidate_rows:
            return FpsReferenceResult(
                has_reference=False,
                reference_fps=None,
                resolution="1920x1080",
                graphics_preset="high",
                gpu_matched=display_gpu,
                message=f"Game '{game_name}' không có trong bảng dữ liệu tham chiếu FPS games_fps_reference.csv.",
                page_url=None,
            )

        if len(candidate_rows) == 1:
            target_row = candidate_rows[0]
            return self._parse_fps_from_row(target_row, col_name, display_gpu, target_row.get("page_url"))

        # Kiểm tra thắt chặt: Có nhiều bản ghi trùng tên
        # 1. Kiểm tra nếu có BẤT KỲ bản ghi nào thiếu hoặc không hợp lệ -> từ chối ngay
        for r in candidate_rows:
            raw_fps = (r.get(col_name) or "").strip()
            if not raw_fps:
                return FpsReferenceResult(
                    has_reference=False,
                    reference_fps=None,
                    resolution="1920x1080",
                    graphics_preset="high",
                    gpu_matched=display_gpu,
                    message=f"Phát hiện {len(candidate_rows)} bản ghi cho game '{game_name}', trong đó có bản ghi thiếu dữ liệu FPS cho GPU '{display_gpu}'. Không thể xác định FPS đồng nhất khi dữ liệu chưa đầy đủ.",
                    page_url=None,
                )
            try:
                f_val = float(raw_fps)
                if not math.isfinite(f_val) or f_val <= 0:
                    return FpsReferenceResult(
                        has_reference=False,
                        reference_fps=None,
                        resolution="1920x1080",
                        graphics_preset="high",
                        gpu_matched=display_gpu,
                        message=f"Phát hiện {len(candidate_rows)} bản ghi cho game '{game_name}', trong đó có bản ghi có số liệu FPS không hợp lệ (<= 0).",
                        page_url=None,
                    )
            except ValueError:
                return FpsReferenceResult(
                    has_reference=False,
                    reference_fps=None,
                    resolution="1920x1080",
                    graphics_preset="high",
                    gpu_matched=display_gpu,
                    message=f"Phát hiện {len(candidate_rows)} bản ghi cho game '{game_name}', trong đó có bản ghi có định dạng số liệu FPS không hợp lệ.",
                    page_url=None,
                )

        # 2. Tất cả N bản ghi đều có FPS hợp lệ -> so sánh các giá trị
        distinct_fps = sorted(list(set(float(r[col_name].strip()) for r in candidate_rows)))
        if len(distinct_fps) == 1:
            # Tất cả các phiên bản đều có FPS giống nhau hoàn toàn
            matched_url = candidate_rows[0].get("page_url")
            return FpsReferenceResult(
                has_reference=True,
                reference_fps=distinct_fps[0],
                resolution="1920x1080",
                graphics_preset="high",
                gpu_matched=display_gpu,
                message=None,
                page_url=matched_url,
            )

        # Có sự khác biệt FPS giữa các phiên bản -> từ chối tự chọn
        fps_summary = ", ".join(f"{v:g} FPS" for v in distinct_fps)
        return FpsReferenceResult(
            has_reference=False,
            reference_fps=None,
            resolution="1920x1080",
            graphics_preset="high",
            gpu_matched=display_gpu,
            message=f"Phát hiện {len(candidate_rows)} phiên bản benchmark khác nhau cho game '{game_name}' với các mức FPS: {fps_summary}. Hệ thống không thể tự chọn FPS nếu thiếu định danh phiên bản (page_url).",
            page_url=None,
        )


# Singleton instance
fps_reference_service = FpsReferenceService()
