"""Rule-based evaluation service based on real game_requirements.csv."""
import csv
from typing import Dict, List, Optional

from backend.config import GAME_REQUIREMENTS_PATH
from backend.schemas import ComponentCheck, GameRequirementDetail, RuleBasedResult


class GameNotFoundError(Exception):
    """Raised when game is not found in game_requirements.csv."""
    pass


class RuleBasedService:
    """Evaluates user PC configuration against game minimum and recommended requirements."""

    def __init__(self, requirements_path=None):
        self.requirements_path = requirements_path or GAME_REQUIREMENTS_PATH
        # Mapping: normalized_name -> GameRequirementDetail
        self._games: Dict[str, GameRequirementDetail] = {}
        self._load_requirements()

    def _normalize(self, text: str) -> str:
        return text.strip().lower()

    def _load_requirements(self) -> None:
        """Load 585 games from game_requirements.csv."""
        if not self.requirements_path.exists():
            raise FileNotFoundError(f"Không tìm thấy file: {self.requirements_path}")

        with open(self.requirements_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row["name"].strip()
                if not name:
                    continue

                rel_year = float(row["release_year"]) if row.get("release_year") else None
                min_cpu = float(row.get("min_cpu_score") or 0)
                rec_cpu = float(row.get("rec_cpu_score") or 0)
                min_gpu = float(row.get("min_gpu_g3d") or 0)
                rec_gpu = float(row.get("rec_gpu_g3d") or 0)
                min_ram = float(row.get("min_ram_gb") or 0)
                rec_ram = float(row.get("rec_ram_gb") or 0)

                detail = GameRequirementDetail(
                    game_name=name,
                    release_year=rel_year,
                    min_cpu_score=min_cpu,
                    rec_cpu_score=rec_cpu,
                    min_gpu_g3d=min_gpu,
                    rec_gpu_g3d=rec_gpu,
                    min_ram_gb=min_ram,
                    rec_ram_gb=rec_ram,
                )
                self._games[self._normalize(name)] = detail

    def get_game_requirement(self, game_name: str) -> GameRequirementDetail:
        """Lấy thông số cấu hình yêu cầu của game.

        Raises:
            GameNotFoundError nếu không tìm thấy game.
        """
        g_norm = self._normalize(game_name)
        if g_norm in self._games:
            return self._games[g_norm]

        # Tìm kiếm gần đúng không phân biệt ký tự đặc biệt
        clean_target = "".join(c for c in g_norm if c.isalnum())
        for norm_name, detail in self._games.items():
            if "".join(c for c in norm_name if c.isalnum()) == clean_target:
                return detail

        raise GameNotFoundError(
            f"Không tìm thấy cấu hình yêu cầu cho game '{game_name}' trong game_requirements.csv."
        )

    def evaluate(
        self,
        game_name: str,
        user_cpu_score: float,
        user_gpu_g3d: float,
        user_ram_gb: float,
    ) -> RuleBasedResult:
        """Đánh giá cấu hình theo quy tắc rule-based.

        So sánh CPU, GPU, RAM với min và rec của game.
        """
        req = self.get_game_requirement(game_name)

        # Kiểm tra CPU
        cpu_passed_min = user_cpu_score >= req.min_cpu_score
        cpu_passed_rec = user_cpu_score >= req.rec_cpu_score
        cpu_status = "passed_rec" if cpu_passed_rec else ("passed_min" if cpu_passed_min else "below_min")
        cpu_check = ComponentCheck(
            component="CPU",
            user_value=user_cpu_score,
            min_value=req.min_cpu_score,
            rec_value=req.rec_cpu_score,
            passed_min=cpu_passed_min,
            passed_rec=cpu_passed_rec,
            status=cpu_status,
        )

        # Kiểm tra GPU
        gpu_passed_min = user_gpu_g3d >= req.min_gpu_g3d
        gpu_passed_rec = user_gpu_g3d >= req.rec_gpu_g3d
        gpu_status = "passed_rec" if gpu_passed_rec else ("passed_min" if gpu_passed_min else "below_min")
        gpu_check = ComponentCheck(
            component="GPU",
            user_value=user_gpu_g3d,
            min_value=req.min_gpu_g3d,
            rec_value=req.rec_gpu_g3d,
            passed_min=gpu_passed_min,
            passed_rec=gpu_passed_rec,
            status=gpu_status,
        )

        # Kiểm tra RAM
        ram_passed_min = user_ram_gb >= req.min_ram_gb
        ram_passed_rec = user_ram_gb >= req.rec_ram_gb
        ram_status = "passed_rec" if ram_passed_rec else ("passed_min" if ram_passed_min else "below_min")
        ram_check = ComponentCheck(
            component="RAM",
            user_value=user_ram_gb,
            min_value=req.min_ram_gb,
            rec_value=req.rec_ram_gb,
            passed_min=ram_passed_min,
            passed_rec=ram_passed_rec,
            status=ram_status,
        )

        components = {
            "cpu": cpu_check,
            "gpu": gpu_check,
            "ram": ram_check,
        }

        # Xác định trạng thái tổng thể
        all_passed_rec = cpu_passed_rec and gpu_passed_rec and ram_passed_rec
        all_passed_min = cpu_passed_min and gpu_passed_min and ram_passed_min

        if all_passed_rec:
            status = "Dat_de_xuat"
            status_label = "Đạt cấu hình đề xuất"
            summary = "Cấu hình phần cứng của bạn đáp ứng tốt mức đề xuất của tựa game này."
        elif all_passed_min:
            status = "Dat_toi_thieu_chua_dat_de_xuat"
            status_label = "Đạt cấu hình tối thiểu (chưa đạt đề xuất)"
            bottlenecks = []
            if not cpu_passed_rec:
                bottlenecks.append(f"CPU ({user_cpu_score:,.0f} < {req.rec_cpu_score:,.0f})")
            if not gpu_passed_rec:
                bottlenecks.append(f"GPU ({user_gpu_g3d:,.0f} < {req.rec_gpu_g3d:,.0f})")
            if not ram_passed_rec:
                bottlenecks.append(f"RAM ({user_ram_gb}GB < {req.rec_ram_gb}GB)")
            summary = f"Cấu hình đạt mức tối thiểu nhưng chưa đạt đề xuất ở: {', '.join(bottlenecks)}."
        else:
            status = "Khong_dat_toi_thieu"
            status_label = "Không đạt cấu hình tối thiểu"
            fails = []
            if not cpu_passed_min:
                fails.append(f"CPU ({user_cpu_score:,.0f} < {req.min_cpu_score:,.0f})")
            if not gpu_passed_min:
                fails.append(f"GPU ({user_gpu_g3d:,.0f} < {req.min_gpu_g3d:,.0f})")
            if not ram_passed_min:
                fails.append(f"RAM ({user_ram_gb}GB < {req.min_ram_gb}GB)")
            summary = f"Cấu hình không đạt yêu cầu tối thiểu ở: {', '.join(fails)}."

        return RuleBasedResult(
            status=status,
            status_label=status_label,
            summary=summary,
            components=components,
            game_requirements=req,
        )

    def list_games(self) -> List[str]:
        """Danh sách tên chuẩn tất cả 585 game trong game_requirements.csv, đã sắp xếp."""
        return sorted(list(set(detail.game_name for detail in self._games.values())))


# Singleton instance
rule_based_service = RuleBasedService()
