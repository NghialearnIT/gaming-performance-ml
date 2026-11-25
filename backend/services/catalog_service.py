"""Catalog service to provide options for dropdowns, autocomplete and validation."""
from typing import List

from backend.config import FPS_PRESET, FPS_RESOLUTION
from backend.schemas import CatalogItem, CatalogOptionsResponse
from backend.services.fps_reference_service import REFERENCE_ONLY_GAMES, fps_reference_service
from backend.services.hardware_service import hardware_service
from backend.services.rule_based_service import rule_based_service


class CatalogService:
    """Service to supply the catalog for GET /options."""

    def __init__(self):
        self._cached_options: CatalogOptionsResponse | None = None

    def get_options(self) -> CatalogOptionsResponse:
        """Lấy toàn bộ danh mục cho Frontend:

        - Games: Danh mục cấu hình yêu cầu và các game có FPS tham chiếu.
        - CPUs: Lấy từ dữ liệu thật trong gaming_train_dataset.csv.
        - GPUs: Lấy từ dữ liệu thật, phân biệt rõ Desktop và Laptop.
        """
        if self._cached_options is not None:
            return self._cached_options

        # 1. Device types
        device_types = [
            CatalogItem(value="desktop", label="Desktop"),
            CatalogItem(value="laptop", label="Laptop"),
        ]

        # 2. Toàn bộ games từ game_requirements.csv
        all_games = set(rule_based_service.list_games())
        all_games.update(
            name for name, url in REFERENCE_ONLY_GAMES.items() if fps_reference_service.get_row(url)
        )
        games = [CatalogItem(value=name, label=name) for name in sorted(all_games, key=str.casefold)]

        # 3. Resolutions & Presets
        resolutions = [
            CatalogItem(value=FPS_RESOLUTION, label="1920 × 1080"),
        ]
        graphics_presets = [
            CatalogItem(value="low", label="Low"),
            CatalogItem(value="medium", label="Medium"),
            CatalogItem(value=FPS_PRESET, label="High"),
        ]

        # 4. CPUs từ dataset thực tế
        all_cpus = hardware_service.list_all_cpus()
        cpu_models = [CatalogItem(value=name, label=name) for name in all_cpus]

        # 5. GPUs từ dataset thực tế, phân biệt Desktop và Laptop
        all_gpus = hardware_service.list_all_gpus()
        gpu_models = [CatalogItem(value=name, label=name) for name in all_gpus]

        desktop_gpus_list = hardware_service.list_gpus_by_device("desktop")
        desktop_gpus = [CatalogItem(value=name, label=name) for name in desktop_gpus_list]

        laptop_gpus_list = hardware_service.list_gpus_by_device("laptop")
        laptop_gpus = [CatalogItem(value=name, label=name) for name in laptop_gpus_list]

        # 6. RAM types & channels
        ram_types = ["DDR4", "DDR5", "LPDDR4X", "LPDDR5", "LPDDR5X"]
        ram_channels = [
            CatalogItem(value="single", label="1 kênh"),
            CatalogItem(value="dual", label="2 kênh"),
            CatalogItem(value="quad", label="4 kênh"),
        ]

        self._cached_options = CatalogOptionsResponse(
            device_types=device_types,
            games=games,
            resolutions=resolutions,
            graphics_presets=graphics_presets,
            fps_presets=[item.value for item in graphics_presets],
            cpu_models=cpu_models,
            gpu_models=gpu_models,
            desktop_gpus=desktop_gpus,
            laptop_gpus=laptop_gpus,
            ram_types=ram_types,
            ram_channels=ram_channels,
        )
        return self._cached_options


# Singleton instance
catalog_service = CatalogService()
