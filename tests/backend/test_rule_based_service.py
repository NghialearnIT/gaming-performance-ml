"""Unit tests for RuleBasedService."""
import pytest
from backend.services.rule_based_service import (
    GameNotFoundError,
    rule_based_service,
)


def test_get_valid_game_requirement():
    """Kiểm tra lấy yêu cầu cấu hình game hợp lệ từ game_requirements.csv."""
    req = rule_based_service.get_game_requirement("Red Dead Redemption 2")
    assert req.game_name == "Red Dead Redemption 2"
    assert req.min_cpu_score == 1690.0
    assert req.rec_cpu_score == 2700.0
    assert req.min_gpu_g3d == 5527.0
    assert req.rec_gpu_g3d == 8540.0
    assert req.min_ram_gb == 8.0
    assert req.rec_ram_gb == 12.0


def test_nonexistent_game_raises_error():
    """Kiểm tra game không tồn tại phải raise GameNotFoundError."""
    with pytest.raises(GameNotFoundError) as exc_info:
        rule_based_service.get_game_requirement("Fictional Game That Does Not Exist 2099")
    assert "Không tìm thấy cấu hình yêu cầu" in str(exc_info.value)


def test_evaluate_meet_recommended():
    """Kiểm tra cấu hình mạnh vượt mức đề xuất -> Dat_de_xuat."""
    result = rule_based_service.evaluate(
        game_name="Red Dead Redemption 2",
        user_cpu_score=5000.0,
        user_gpu_g3d=15000.0,
        user_ram_gb=16.0,
    )
    assert result.status == "Dat_de_xuat"
    assert result.status_label == "Đạt cấu hình đề xuất"
    assert result.components["cpu"].status == "passed_rec"
    assert result.components["gpu"].status == "passed_rec"
    assert result.components["ram"].status == "passed_rec"


def test_evaluate_meet_minimum_not_recommended():
    """Kiểm tra cấu hình đạt mức tối thiểu nhưng thiếu RAM để đạt đề xuất."""
    result = rule_based_service.evaluate(
        game_name="Red Dead Redemption 2",
        user_cpu_score=3000.0,  # >= rec 2700
        user_gpu_g3d=10000.0,  # >= rec 8540
        user_ram_gb=8.0,       # >= min 8 nhưng < rec 12
    )
    assert result.status == "Dat_toi_thieu_chua_dat_de_xuat"
    assert result.status_label == "Đạt cấu hình tối thiểu (chưa đạt đề xuất)"
    assert result.components["ram"].status == "passed_min"
    assert "RAM" in result.summary


def test_evaluate_below_minimum():
    """Kiểm tra cấu hình yếu không đạt tối thiểu GPU."""
    result = rule_based_service.evaluate(
        game_name="Red Dead Redemption 2",
        user_cpu_score=2000.0,  # >= min 1690
        user_gpu_g3d=3000.0,   # < min 5527
        user_ram_gb=8.0,       # >= min 8
    )
    assert result.status == "Khong_dat_toi_thieu"
    assert result.status_label == "Không đạt cấu hình tối thiểu"
    assert result.components["gpu"].status == "below_min"
    assert "GPU" in result.summary


def test_list_games():
    """Kiểm tra danh sách game lấy từ file đạt 585 games."""
    games = rule_based_service.list_games()
    assert len(games) >= 580
    assert "Red Dead Redemption 2" in games
    assert "Cyberpunk 2077" in games
