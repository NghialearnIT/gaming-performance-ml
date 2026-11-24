"""Unit tests for FpsReferenceService with two-level lookup and data integrity."""
import pytest
from backend.services.fps_reference_service import (
    DataIntegrityError,
    FpsReferenceService,
    fps_reference_service,
)


def test_bayonetta_distinct_page_urls():
    """Kiểm tra Bayonetta: đúng page_url của bản 2009 và 2014 cho kết quả FPS độc lập chính xác."""
    # Bản gốc 2009 (URL kết thúc -2036) bị khóa ở 60 FPS
    res_2009 = fps_reference_service.get_fps_reference(
        game_name="Bayonetta",
        gpu_model="GeForce RTX 3060",
        device_type="desktop",
        page_url="https://pcgamebenchmarks.com/game/bayonetta-2036",
    )
    assert res_2009.has_reference is True
    assert res_2009.reference_fps == 60.0
    assert res_2009.page_url == "https://pcgamebenchmarks.com/game/bayonetta-2036"

    # Bản 2014 (URL kết thúc -257500) mở khóa FPS ở 151 FPS
    res_2014 = fps_reference_service.get_fps_reference(
        game_name="Bayonetta",
        gpu_model="GeForce RTX 3060",
        device_type="desktop",
        page_url="https://pcgamebenchmarks.com/game/bayonetta-257500",
    )
    assert res_2014.has_reference is True
    assert res_2014.reference_fps == 151.0
    assert res_2014.page_url == "https://pcgamebenchmarks.com/game/bayonetta-257500"


def test_skyrim_ambiguous_name_rejected():
    """Kiểm tra Skyrim: tra cứu theo tên tự do có nhiều bản ghi FPS khác nhau (60 vs 160) -> từ chối."""
    result = fps_reference_service.get_fps_reference(
        game_name="The Elder Scrolls V: Skyrim",
        gpu_model="GeForce RTX 3060",
        device_type="desktop",
        page_url=None,
    )
    assert result.has_reference is False
    assert result.reference_fps == None
    assert "Phát hiện 2 phiên bản benchmark khác nhau" in result.message
    assert "60 FPS, 160 FPS" in result.message


def test_gta_v_ambiguous_name_rejected():
    """Kiểm tra GTA V: tra cứu theo tên tự do có 3 bản ghi với FPS khác nhau (151 vs 156) -> từ chối."""
    result = fps_reference_service.get_fps_reference(
        game_name="Grand Theft Auto V",
        gpu_model="GeForce RTX 3060",
        device_type="desktop",
        page_url=None,
    )
    assert result.has_reference is False
    assert result.reference_fps == None
    assert "Phát hiện 3 phiên bản benchmark khác nhau" in result.message
    assert "151 FPS, 156 FPS" in result.message


def test_gta_v_with_specific_page_url():
    """Kiểm tra GTA V khi có page_url rõ ràng thì trả về đúng bản ghi tương ứng."""
    res_2013 = fps_reference_service.get_fps_reference(
        game_name="Grand Theft Auto V",
        gpu_model="GeForce RTX 3060",
        device_type="desktop",
        page_url="https://pcgamebenchmarks.com/game/grand-theft-auto-v-1002",
    )
    assert res_2013.has_reference is True
    assert res_2013.reference_fps == 151.0

    res_2015 = fps_reference_service.get_fps_reference(
        game_name="Grand Theft Auto V",
        gpu_model="GeForce RTX 3060",
        device_type="desktop",
        page_url="https://pcgamebenchmarks.com/game/grand-theft-auto-v-124227",
    )
    assert res_2015.has_reference is True
    assert res_2015.reference_fps == 156.0


def test_nonexistent_page_url_no_fallback():
    """Kiểm tra page_url không tồn tại -> báo lỗi, tuyệt đối không fallback sang tên game."""
    result = fps_reference_service.get_fps_reference(
        game_name="Grand Theft Auto V",
        gpu_model="GeForce RTX 3060",
        device_type="desktop",
        page_url="https://pcgamebenchmarks.com/game/fake-url-9999",
    )
    assert result.has_reference is False
    assert result.reference_fps is None
    assert "Không tìm thấy dữ liệu benchmark FPS tương ứng với page_url" in result.message


def test_duplicate_page_url_raises_integrity_error(tmp_path):
    """Kiểm tra phát hiện trùng lặp page_url trong games_fps_reference.csv."""
    csv_file = tmp_path / "mock_fps_dup.csv"
    csv_file.write_text(
        "name,page_url,fps_1080p_high_rtx_3060\n"
        "Game A,https://pcgamebenchmarks.com/game/same-url,60\n"
        "Game B,https://pcgamebenchmarks.com/game/same-url,70\n",
        encoding="utf-8",
    )
    with pytest.raises(DataIntegrityError) as exc_info:
        FpsReferenceService(dataset_path=csv_file)
    assert "Phát hiện trùng lặp page_url" in str(exc_info.value)


def test_empty_page_url_raises_integrity_error(tmp_path):
    """Kiểm tra phát hiện dòng thiếu page_url trong games_fps_reference.csv."""
    csv_file = tmp_path / "mock_fps_empty_url.csv"
    csv_file.write_text(
        "name,page_url,fps_1080p_high_rtx_3060\n"
        "Game A,,60\n",
        encoding="utf-8",
    )
    with pytest.raises(DataIntegrityError) as exc_info:
        FpsReferenceService(dataset_path=csv_file)
    assert "thiếu page_url" in str(exc_info.value)


def test_multiple_records_all_identical_fps_accepted():
    """Kiểm tra BioShock: 2 bản ghi cùng tên nhưng đều có FPS bằng 324 trên RTX 3060 -> chấp nhận."""
    result = fps_reference_service.get_fps_reference(
        game_name="BioShock",
        gpu_model="GeForce RTX 3060",
        device_type="desktop",
        page_url=None,
    )
    assert result.has_reference is True
    assert result.reference_fps == 324.0


def test_ambiguous_records_with_missing_fps_rejected(tmp_path):
    """Kiểm tra nếu trong các bản ghi trùng tên có bản ghi thiếu FPS -> từ chối, không suy diễn."""
    csv_file = tmp_path / "mock_fps_missing_one.csv"
    csv_file.write_text(
        "name,page_url,fps_1080p_high_rtx_3060\n"
        "Test Game,https://pcgamebenchmarks.com/game/test-1,60\n"
        "Test Game,https://pcgamebenchmarks.com/game/test-2,\n",
        encoding="utf-8",
    )
    service = FpsReferenceService(dataset_path=csv_file)
    res = service.get_fps_reference("Test Game", "GeForce RTX 3060", "desktop", page_url=None)
    assert res.has_reference is False
    assert res.reference_fps is None
    assert "trong đó có bản ghi thiếu dữ liệu FPS" in res.message


def test_multiple_records_different_fps_rejected():
    """Kiểm tra Mass Effect 2: 2 bản ghi có FPS khác nhau (62 vs 162) -> từ chối."""
    result = fps_reference_service.get_fps_reference(
        game_name="Mass Effect 2",
        gpu_model="GeForce RTX 3060",
        device_type="desktop",
        page_url=None,
    )
    assert result.has_reference is False
    assert result.reference_fps is None
    assert "Phát hiện 2 phiên bản benchmark khác nhau" in result.message


def test_gpu_with_empty_or_zero_fps(tmp_path):
    """Kiểm tra cột FPS rỗng hoặc bằng 0 -> has_reference = False, không tự biến thành 0."""
    csv_file = tmp_path / "mock_fps_zero.csv"
    csv_file.write_text(
        "name,page_url,fps_1080p_high_rtx_3060\n"
        "Zero Game,https://pcgamebenchmarks.com/game/zero-1,0\n",
        encoding="utf-8",
    )
    service = FpsReferenceService(dataset_path=csv_file)
    res = service.get_fps_reference("Zero Game", "GeForce RTX 3060", "desktop", page_url="https://pcgamebenchmarks.com/game/zero-1")
    assert res.has_reference is False
    assert res.reference_fps is None
    assert "không hợp lệ (<= 0)" in res.message


def test_fps_reference_laptop_dedicated_gpu_no_substitution():
    """Kiểm tra GPU Laptop không được dùng FPS của GPU Desktop."""
    result = fps_reference_service.get_fps_reference(
        game_name="Grand Theft Auto V",
        gpu_model="GeForce RTX 4060 Laptop GPU",
        device_type="laptop",
    )
    assert result.has_reference is False
    assert result.reference_fps is None
    assert "không có cột đo FPS riêng" in result.message


def test_fps_reference_unsupported_gpu():
    """Kiểm tra GPU không có cột benchmark trong bảng games_fps_reference.csv."""
    result = fps_reference_service.get_fps_reference(
        game_name="Grand Theft Auto V",
        gpu_model="Radeon R9 350",
        device_type="desktop",
    )
    assert result.has_reference is False
    assert result.reference_fps is None
    assert "không có cột đo FPS thực tế" in result.message


def test_fps_reference_game_not_found():
    """Kiểm tra game không có trong bảng tham chiếu FPS."""
    result = fps_reference_service.get_fps_reference(
        game_name="Nonexistent Game Title 123",
        gpu_model="GeForce RTX 3060",
        device_type="desktop",
    )
    assert result.has_reference is False
    assert result.reference_fps is None
    assert "không có trong bảng dữ liệu tham chiếu" in result.message


def test_fps_reference_igpu_with_page_url():
    """Kiểm tra iGPU (Intel Iris Xe) được hỗ trợ trên laptop khi truyền đúng page_url."""
    result = fps_reference_service.get_fps_reference(
        game_name="Grand Theft Auto V",
        gpu_model="Intel Iris Xe",
        device_type="laptop",
        page_url="https://pcgamebenchmarks.com/game/grand-theft-auto-v-1002",
    )
    assert result.has_reference is True
    assert result.reference_fps == 32.0


def test_cross_dataset_all_requirements_urls_exist():
    """Kiểm tra thực tế: Toàn bộ Requirements URLs đều tồn tại trong games_fps_reference.csv."""
    from backend.services.rule_based_service import rule_based_service
    req_urls = rule_based_service.get_all_page_urls()
    total_fps_urls = len(fps_reference_service._fps_by_url)
    expected_extra = total_fps_urls - len(req_urls)

    matched, extra = fps_reference_service.verify_cross_dataset_integrity(req_urls)
    assert matched == len(req_urls)
    assert extra == expected_extra


def test_cross_dataset_missing_url_raises_integrity_error():
    """Kiểm tra nếu có URL trong Requirements không tồn tại trong FPS Reference -> raise DataIntegrityError."""
    fake_req_urls = {
        "https://pcgamebenchmarks.com/game/fake-nonexistent-game-url-99999",
        "https://pcgamebenchmarks.com/game/another-missing-game-url-88888",
    }
    with pytest.raises(DataIntegrityError) as exc_info:
        fps_reference_service.verify_cross_dataset_integrity(fake_req_urls)
    assert "không tồn tại trong games_fps_reference.csv" in str(exc_info.value)
    assert "fake-nonexistent-game-url-99999" in str(exc_info.value)


def test_cross_dataset_extra_urls_statistics(tmp_path):
    """Kiểm tra FPS Reference có URL dư thì vẫn hợp lệ và tính toán đúng số lượng URL dư."""
    csv_file = tmp_path / "mock_fps_extra.csv"
    csv_file.write_text(
        "name,page_url,fps_1080p_high_rtx_3060\n"
        "Game A,https://pcgamebenchmarks.com/game/a,60\n"
        "Game B,https://pcgamebenchmarks.com/game/b,70\n"
        "Game C,https://pcgamebenchmarks.com/game/c,80\n",
        encoding="utf-8",
    )
    service = FpsReferenceService(dataset_path=csv_file)
    req_urls = {
        "https://pcgamebenchmarks.com/game/a",
        "https://pcgamebenchmarks.com/game/b",
    }
    matched_count, extra_count = service.verify_cross_dataset_integrity(req_urls)
    assert matched_count == 2
    assert extra_count == 1  # Game C là URL mở rộng hợp lệ, không bị lỗi
