"""Hardware service for looking up real CPU and GPU scores from gaming_train_dataset.csv."""
import csv
from typing import Dict, List, Optional, Set, Tuple

from backend.config import GAMING_TRAIN_DATASET_PATH


class HardwareError(Exception):
    """Base exception for hardware service."""
    pass


class HardwareNotFoundError(HardwareError):
    """Raised when CPU or GPU is not found in database."""
    pass


class DeviceTypeMismatchError(HardwareError):
    """Raised when a Desktop GPU is selected for Laptop or vice versa."""
    pass


class DataIntegrityError(HardwareError):
    """Raised when conflicting scores are detected for the same hardware model."""
    pass


class HardwareService:
    """Service to query CPU Gaming Score and GPU G3D Mark from benchmark dataset."""

    def __init__(self, dataset_path=None):
        self.dataset_path = dataset_path or GAMING_TRAIN_DATASET_PATH
        # Mapping: normalized_name -> (canonical_name, cpu_score)
        self._cpu_data: Dict[str, Tuple[str, float]] = {}
        # Mapping: (device_type_lower, normalized_gpu_name) -> (canonical_name, gpu_type, gpu_g3d_mark)
        self._gpu_data: Dict[Tuple[str, str], Tuple[str, str, float]] = {}
        # Mapping: normalized_gpu_name -> set of available device_types
        self._gpu_device_types: Dict[str, Set[str]] = {}
        self._load_data()

    def _normalize(self, text: str) -> str:
        """Strip whitespace and lowercase string."""
        return text.strip().lower()

    def _load_data(self) -> None:
        """Load and validate dataset, checking for conflicting scores."""
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Dataset không tồn tại: {self.dataset_path}")

        cpu_conflicts: Dict[str, Set[float]] = {}
        gpu_conflicts: Dict[Tuple[str, str], Set[float]] = {}

        with open(self.dataset_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                device_type = self._normalize(row["device_type"])
                cpu_name = row["cpu_name"].strip()
                gpu_name = row["gpu_name"].strip()
                gpu_type = row["gpu_type"].strip()

                # Process CPU Score
                c_score_raw = row.get("cpu_gaming_score", "").strip()
                if c_score_raw:
                    c_score = float(c_score_raw)
                    c_norm = self._normalize(cpu_name)
                    if c_norm in self._cpu_data:
                        existing_score = self._cpu_data[c_norm][1]
                        if existing_score != c_score:
                            if c_norm not in cpu_conflicts:
                                cpu_conflicts[c_norm] = {existing_score}
                            cpu_conflicts[c_norm].add(c_score)
                    else:
                        self._cpu_data[c_norm] = (cpu_name, c_score)

                # Process GPU Score
                g_score_raw = row.get("gpu_g3d_mark", "").strip()
                if g_score_raw:
                    g_score = float(g_score_raw)
                    g_norm = self._normalize(gpu_name)
                    gpu_key = (device_type, g_norm)

                    if g_norm not in self._gpu_device_types:
                        self._gpu_device_types[g_norm] = set()
                    self._gpu_device_types[g_norm].add(device_type)

                    if gpu_key in self._gpu_data:
                        existing_gscore = self._gpu_data[gpu_key][2]
                        if existing_gscore != g_score:
                            if gpu_key not in gpu_conflicts:
                                gpu_conflicts[gpu_key] = {existing_gscore}
                            gpu_conflicts[gpu_key].add(g_score)
                    else:
                        self._gpu_data[gpu_key] = (gpu_name, gpu_type, g_score)

        # Enforce requirement: Detect and raise error if conflicting scores exist
        if cpu_conflicts or gpu_conflicts:
            err_msg = []
            if cpu_conflicts:
                err_msg.append(f"Xung đột điểm CPU: {cpu_conflicts}")
            if gpu_conflicts:
                err_msg.append(f"Xung đột điểm GPU: {gpu_conflicts}")
            raise DataIntegrityError("; ".join(err_msg))

    def get_cpu_score(self, cpu_model: str) -> Tuple[str, float]:
        """Tra cứu CPU Gaming Score từ dữ liệu thật.

        Returns:
            (canonical_name, cpu_gaming_score)

        Raises:
            HardwareNotFoundError nếu không tìm thấy CPU.
        """
        c_norm = self._normalize(cpu_model)
        if c_norm not in self._cpu_data:
            raise HardwareNotFoundError(
                f"Không tìm thấy CPU '{cpu_model}' trong cơ sở dữ liệu benchmark thực tế."
            )
        return self._cpu_data[c_norm]

    def get_gpu_info(self, gpu_model: str, device_type: str) -> Tuple[str, str, float]:
        """Tra cứu GPU G3D Mark cho đúng device_type (Desktop hoặc Laptop).

        Args:
            gpu_model: Tên GPU.
            device_type: 'desktop' hoặc 'laptop'.

        Returns:
            (canonical_name, gpu_type, gpu_g3d_mark)

        Raises:
            ValueError nếu device_type không hợp lệ.
            DeviceTypeMismatchError nếu dùng GPU Desktop cho Laptop hoặc ngược lại.
            HardwareNotFoundError nếu không tìm thấy GPU.
        """
        d_norm = self._normalize(device_type)
        if d_norm not in ("desktop", "laptop"):
            raise ValueError(f"device_type không hợp lệ: '{device_type}'. Phải là 'desktop' hoặc 'laptop'.")

        g_norm = self._normalize(gpu_model)
        gpu_key = (d_norm, g_norm)

        if gpu_key in self._gpu_data:
            return self._gpu_data[gpu_key]

        # Kiểm tra xem GPU này có tồn tại ở thiết bị khác không
        if g_norm in self._gpu_device_types:
            other_types = self._gpu_device_types[g_norm]
            other_names = ", ".join(t.capitalize() for t in other_types)
            raise DeviceTypeMismatchError(
                f"GPU '{gpu_model}' là card dành cho thiết bị {other_names}, "
                f"không được sử dụng cho thiết bị {device_type.capitalize()}."
            )

        raise HardwareNotFoundError(
            f"Không tìm thấy GPU '{gpu_model}' trong cơ sở dữ liệu benchmark cho thiết bị {device_type.capitalize()}."
        )

    def list_all_cpus(self) -> List[str]:
        """Danh sách tên chuẩn tất cả CPU trong dữ liệu, đã sắp xếp."""
        return sorted(list(set(name for name, _ in self._cpu_data.values())))

    def list_all_gpus(self) -> List[str]:
        """Danh sách tên chuẩn tất cả GPU trong dữ liệu, đã sắp xếp."""
        return sorted(list(set(name for name, _, _ in self._gpu_data.values())))

    def list_gpus_by_device(self, device_type: str) -> List[str]:
        """Danh sách tên chuẩn GPU phân loại theo Desktop hoặc Laptop."""
        d_norm = self._normalize(device_type)
        return sorted(
            list(set(name for (dev, _), (name, _, _) in self._gpu_data.items() if dev == d_norm))
        )


# Singleton instance
hardware_service = HardwareService()
