"""Run UI tests with an HTTP fixture. Fixture FPS values are illustrative."""
import argparse
import csv
import json
import os
import shutil
import threading
import time
from functools import partial
from http.server import BaseHTTPRequestHandler, SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"
CATALOG = json.loads((FRONTEND / "mock-options.json").read_text(encoding="utf-8"))
API_STATE = {"mode": "ok", "requests": []}
UI_URL = "http://127.0.0.1:5500"
API_URL = "http://127.0.0.1:8000"


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class FixtureApi(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send_json(self, code, body=None):
        self.send_response(code)
        self.send_header("Access-Control-Allow-Origin", UI_URL)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        if body is not None:
            raw = json.dumps(body).encode()
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        if body is not None:
            try:
                self.wfile.write(raw)
            except (BrokenPipeError, ConnectionResetError):
                pass

    def do_OPTIONS(self):
        self.send_json(204)

    def do_GET(self):
        if self.path != "/options":
            return self.send_json(404, {"detail": "Endpoint absent"})
        if API_STATE["mode"] == "catalog_error":
            return self.send_json(503, {"detail": "Catalog offline"})
        catalog = CATALOG
        if API_STATE["mode"] == "typed_options":
            catalog = {**CATALOG, "device_types": ["Desktop", "Laptop"], "ram_channels": [1, 2, 4]}
        return self.send_json(200, catalog)

    def do_POST(self):
        if self.path != "/predict":
            return self.send_json(404, {"detail": "Endpoint absent"})
        data = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        API_STATE["requests"].append(data)
        mode = API_STATE["mode"]
        if mode == "validation":
            return self.send_json(422, {"detail": [{"loc": ["body", "ram_gb"], "type": "less_than_equal"}]})
        if mode == "client_error":
            return self.send_json(400, {"detail": "Cấu hình này chưa được hỗ trợ."})
        if mode == "server_error" or (mode == "partial" and data["graphics_preset"] == "low"):
            return self.send_json(500, {"detail": "Fixture error"})
        if mode == "malformed":
            return self.send_json(200, {"avg_fps": "invalid"})
        if mode == "slow":
            time.sleep(11)
        if mode == "delay":
            time.sleep(0.5)
        avg = {"low": 154.25, "medium": 96.7, "high": 59.25}[data["graphics_preset"]]
        warnings = []
        if data["device_type"].lower() == "laptop" and data["gpu_tgp_w"] is None:
            warnings.append("Thiếu thông tin TGP của GPU Laptop.")
        if data["cpu_model"] == "Outside Catalog CPU":
            warnings.append("CPU nằm ngoài catalog.")
        return self.send_json(200, {
            "avg_fps": avg, "one_percent_low_fps": None if mode == "missing_low" else avg * 0.62,
            "model_version": "STUB" if mode == "stub" else "TEST-FIXTURE",
            "is_stub": mode == "stub",
            "warnings": warnings,
        })


def open_form(page, path="", status=None):
    page.goto(UI_URL + "/" + path)
    expect(page.locator("#reset-form")).to_be_enabled()
    if status:
        expect(page.locator("#connection")).to_have_attribute("data-state", status)


def fill_form(page, game="valorant", device="desktop", preset="high", tgp="90", cpu=None):
    page.locator(f'label[for="{device}"]').click()
    page.locator("#cpu_model").fill(cpu or ("Intel Core i7-12700H" if device == "laptop" else "Intel Core i5-12400F"))
    page.locator("#gpu_model").fill("NVIDIA RTX 4060 Laptop GPU" if device == "laptop" else "NVIDIA RTX 3060")
    page.locator("#ram_gb").fill("16")
    page.locator("#gpu_vram_gb").fill("8" if device == "laptop" else "12")
    if device == "laptop":
        page.locator("#gpu_tgp_w").fill(tgp)
    page.locator("#game").select_option(game)
    page.locator("#graphics_preset").select_option(preset)


def click_predict(page):
    page.locator("#predict").click()


def wait_frame(page):
    expect(page.locator("#spinner")).to_be_hidden()


def finish_prediction(page):
    click_predict(page)
    expect(page.locator("#chart-area")).to_be_visible()
    wait_frame(page)


def assert_layout(page):
    assert page.evaluate("document.documentElement.scrollWidth === innerWidth")
    expect(page.locator("#cpu_model")).to_be_visible()
    expect(page.locator("#chart")).to_be_visible()


def run_tests(browser, screenshots):
    page = browser.new_page(viewport={"width": 1440, "height": 1050}, locale="vi-VN")
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    rows = []

    def test(description, steps, expected, action):
        API_STATE["mode"] = "ok"
        API_STATE["requests"].clear()
        try:
            action()
        except Exception as error:
            rows.append([description, steps, expected, str(error).splitlines()[0], "Fail"])
        else:
            rows.append([description, steps, expected, expected, "Pass"])

    for game in CATALOG["games"]:
        for device in CATALOG["device_types"]:
            def main_flow():
                open_form(page, status="online")
                fill_form(page, game["value"], device)
                finish_prediction(page)
                expect(page.locator("#avg")).to_have_text("59")
                expect(page.locator("#low")).to_have_text("37")
                expect(page.locator("#result-config")).to_contain_text(game["label"])
                sent = API_STATE["requests"][0]
                assert sent["game"] == game["value"] and sent["device_type"] == device
                assert sent["gpu_tgp_w"] == (90 if device == "laptop" else None)
                assert len(sent) == 11 and sent["ram_gb"] == 16 and sent["resolution"] == "1920x1080"
            test(f"{game['label']} / {device}", "Chọn game, nhập cấu hình, chọn High và gửi.",
                 "Payload đúng 11 trường. Hai thẻ hiển thị 59 và 37 FPS từ fixture.", main_flow)

    def required():
        open_form(page)
        expect(page.locator("#predict")).to_be_disabled()
        page.locator("#cpu_model").fill(" ")
        page.locator("#gpu_model").focus()
        expect(page.locator("#cpu_model-error")).to_be_visible()
        assert not API_STATE["requests"]

    def ram_boundary():
        open_form(page)
        fill_form(page)
        for bad in ("0", "-1", "15.5"):
            page.locator("#ram_gb").fill(bad)
            expect(page.locator("#ram_gb-error")).to_be_visible()
            expect(page.locator("#predict")).to_be_disabled()
        page.locator("#ram_gb").fill("1")
        expect(page.locator("#ram_gb-error")).to_be_hidden()
        expect(page.locator("#predict")).to_be_enabled()

    def vram_boundary():
        open_form(page)
        fill_form(page)
        page.locator("#gpu_vram_gb").fill("0")
        expect(page.locator("#gpu_vram_gb-error")).to_be_visible()
        expect(page.locator("#predict")).to_be_disabled()
        page.locator("#gpu_vram_gb").fill("")
        expect(page.locator("#predict")).to_be_enabled()

    def tgp_boundary():
        open_form(page)
        fill_form(page, device="laptop", tgp="-5")
        expect(page.locator("#gpu_tgp_w-error")).to_be_visible()
        expect(page.locator("#predict")).to_be_disabled()
        page.locator('label[for="desktop"]').click()
        expect(page.locator("#tgp-field")).to_be_hidden()
        finish_prediction(page)
        assert API_STATE["requests"][0]["gpu_tgp_w"] is None

    def missing_tgp():
        open_form(page)
        fill_form(page, device="laptop", tgp="")
        finish_prediction(page)
        expect(page.locator("#warning-list")).to_contain_text("Thiếu thông tin TGP")

    def outside_catalog():
        open_form(page)
        fill_form(page, cpu="Outside Catalog CPU")
        finish_prediction(page)
        expect(page.locator("#warning-list")).to_contain_text("CPU nằm ngoài catalog")

    def validation_response():
        API_STATE["mode"] = "validation"
        open_form(page)
        fill_form(page)
        click_predict(page)
        expect(page.locator("#ram_gb-error")).to_contain_text("vượt mức tối đa")
        expect(page.locator("#ram_gb")).to_have_value("16")
        expect(page.locator("#predict")).to_be_disabled()
        API_STATE["mode"] = "ok"
        page.locator("#ram_gb").fill("32")
        finish_prediction(page)

    def client_error():
        API_STATE["mode"] = "client_error"
        open_form(page)
        fill_form(page)
        click_predict(page)
        expect(page.locator("#error-message")).to_have_text("Cấu hình này chưa được hỗ trợ.")
        expect(page.locator("#retry")).to_be_hidden()
        expect(page.locator("#ram_gb")).to_have_value("16")

    def server_error():
        API_STATE["mode"] = "server_error"
        open_form(page)
        fill_form(page)
        click_predict(page)
        expect(page.locator("#error-message")).to_contain_text("Máy chủ")
        API_STATE["mode"] = "ok"
        page.locator("#retry").click()
        expect(page.locator("#chart-area")).to_be_visible()
        wait_frame(page)

    def disconnected():
        # Abort the HTTP connection to exercise the same fetch failure as a stopped backend.
        pattern = API_URL + "/**"
        handler = lambda route: route.abort("connectionrefused")
        page.route(pattern, handler)
        try:
            open_form(page, status="offline")
            fill_form(page)
            click_predict(page)
            expect(page.locator("#error-message")).to_contain_text("Không kết nối được")
            expect(page.locator("#retry")).to_be_visible()
            expect(page.locator("#ram_gb")).to_have_value("16")
        finally:
            page.unroute(pattern, handler)

    def timeout():
        API_STATE["mode"] = "slow"
        open_form(page)
        fill_form(page)
        click_predict(page)
        expect(page.locator("#error-message")).to_contain_text("quá 10 giây", timeout=12000)
        expect(page.locator("#retry")).to_be_visible()

    def loading():
        API_STATE["mode"] = "delay"
        open_form(page)
        fill_form(page)
        click_predict(page)
        expect(page.locator("#spinner")).to_be_visible()
        expect(page.locator("#predict")).to_be_disabled()
        expect(page.locator("#fields")).to_have_attribute("disabled", "")
        expect(page.locator("#chart-area")).to_be_visible()
        expect(page.locator("#predict")).to_be_enabled()

    def stub():
        API_STATE["mode"] = "stub"
        open_form(page)
        fill_form(page)
        finish_prediction(page)
        expect(page.locator("#stub-warning")).to_be_visible()
        expect(page.locator("#model")).to_contain_text("STUB")

    def missing_low():
        API_STATE["mode"] = "missing_low"
        open_form(page)
        fill_form(page)
        finish_prediction(page)
        expect(page.locator("#low")).to_have_text("—")
        expect(page.locator("#model")).to_contain_text("Chưa có ước lượng")

    def partial():
        API_STATE["mode"] = "partial"
        open_form(page)
        fill_form(page)
        finish_prediction(page)
        expect(page.locator("#comparison-status")).to_contain_text("Chưa tải được: Low")
        expect(page.locator("#avg")).to_have_text("59")

    def comparison():
        open_form(page)
        fill_form(page)
        finish_prediction(page)
        expect(page.locator("#comparison-status")).to_contain_text("Medium là preset cao nhất")
        assert sorted(x["graphics_preset"] for x in API_STATE["requests"]) == ["high", "low", "medium"]

    def reset():
        open_form(page)
        fill_form(page, device="laptop")
        finish_prediction(page)
        page.locator("#reset-form").click()
        expect(page.locator("#tgp-field")).to_be_hidden()
        expect(page.locator("#cpu_model")).to_have_value("")
        expect(page.locator("#game")).to_have_value("")
        expect(page.locator("#resolution")).to_have_value("1920x1080")
        expect(page.locator("#avg")).to_have_text("—")
        expect(page.locator("#chart-area")).to_be_hidden()

    def demo_offline():
        blocked = []
        def restrict(route):
            if route.request.url.startswith(UI_URL + "/"):
                route.continue_()
            else:
                blocked.append(route.request.url)
                route.abort()
        page.route("**/*", restrict)
        try:
            open_form(page, "?demo=1", "demo")
            page.locator("#sample").click()
            finish_prediction(page)
            expect(page.locator("#stub-warning")).to_be_visible()
            expect(page.locator("#comparison-status")).to_contain_text("số liệu thử nghiệm")
            assert blocked == [] and API_STATE["requests"] == []
        finally:
            page.unroute("**/*", restrict)

    def malformed():
        API_STATE["mode"] = "malformed"
        open_form(page)
        fill_form(page)
        click_predict(page)
        expect(page.locator("#error-message")).to_contain_text("không đúng định dạng")
        expect(page.locator("#avg")).to_have_text("—")

    def typed_options():
        API_STATE["mode"] = "typed_options"
        open_form(page, status="online")
        fill_form(page)
        page.locator("#ram_channels").select_option("2")
        finish_prediction(page)
        sent = API_STATE["requests"][0]
        assert sent["ram_channels"] == 2 and sent["device_type"] == "Desktop"

    scenarios = [
        ("Trường bắt buộc", "Để trống CPU/GPU, chọn sang trường khác.", "Khóa gửi, báo lỗi CPU, không POST.", required),
        ("RAM và giá trị biên", "Nhập 0, -1, 15.5 rồi 1.", "Chặn ba giá trị lỗi và chấp nhận 1 GB.", ram_boundary),
        ("VRAM không hợp lệ", "Nhập 0 rồi xóa VRAM.", "Báo lỗi theo trường, cho phép để trống.", vram_boundary),
        ("TGP âm và đổi thiết bị", "Nhập -5 W trên Laptop rồi đổi Desktop và gửi.", "Chặn TGP âm. Cấu hình Desktop gửi TGP null.", tgp_boundary),
        ("Laptop thiếu TGP", "Để trống TGP, gửi cấu hình Laptop.", "Vẫn có kết quả và có cảnh báo TGP.", missing_tgp),
        ("CPU ngoài catalog", "Gõ Outside Catalog CPU và gửi.", "Cho nhập tự do, hiển thị cảnh báo từ API.", outside_catalog),
        ("API 422", "Fixture trả lỗi ram_gb. Đổi RAM rồi gửi lại.", "Hiện lỗi dưới RAM, giữ dữ liệu đã nhập và gửi lại được.", validation_response),
        ("API 400", "Fixture trả HTTP 400.", "Hiện thông báo nghiệp vụ, giữ cấu hình.", client_error),
        ("API 500 và thử lại", "Fixture trả 500. Khôi phục API rồi nhấn Thử lại.", "Báo lỗi và thử lại bằng cấu hình cũ.", server_error),
        ("Mất kết nối và mock options", "Chặn kết nối đến API trong trình duyệt. Nhập và gửi.", "Dùng catalog mẫu, giữ form, hiện lỗi và nút Thử lại.", disconnected),
        ("API quá thời gian", "Fixture giữ request 11 giây.", "Thông báo timeout sau khoảng 10 giây.", timeout),
        ("Đang xử lý", "Fixture trả API chậm 500 ms.", "Hiện spinner, khóa form rồi mở lại.", loading),
        ("API STUB", "Fixture trả is_stub=true, model_version=STUB.", "Hiện banner Dữ liệu thử nghiệm.", stub),
        ("Thiếu 1% Low", "Fixture trả one_percent_low_fps=null.", "Hiện dấu gạch và ghi chưa có ước lượng.", missing_low),
        ("So sánh lỗi một preset", "API lỗi ở Low nhưng trả kết quả High và Medium.", "Giữ kết quả chính, chỉ rõ Low chưa tải được.", partial),
        ("So sánh ba preset", "Dự đoán High và kiểm tra log của fixture.", "Gọi đúng 3 request. Gợi ý Medium với ngưỡng trung bình 60 FPS.", comparison),
        ("Đặt lại", "Nhập Laptop, dự đoán rồi nhấn Đặt lại.", "Xóa cấu hình và kết quả, khôi phục độ phân giải duy nhất, ẩn TGP.", reset),
        ("Demo offline", "Chặn mọi request ngoài máy chủ frontend, mở demo và dùng cấu hình mẫu.", "Demo hiện biểu đồ và nhãn thử nghiệm. Không gọi API/CDN.", demo_offline),
        ("API sai định dạng", "Fixture trả avg_fps dạng chuỗi.", "Hiện thông báo lỗi định dạng, không hiển thị FPS.", malformed),
        ("Kiểu enum từ options", "Fixture trả kênh RAM dạng số và Desktop viết hoa.", "Payload giữ kiểu số 2 và giá trị Desktop từ API.", typed_options),
    ]
    for args in scenarios:
        test(*args)

    for width, height in [(1440, 1050), (768, 1000), (375, 840)]:
        def layout():
            page.set_viewport_size({"width": width, "height": height})
            open_form(page, "?demo=1", "demo")
            page.locator("#sample").click()
            finish_prediction(page)
            assert_layout(page)
            if screenshots:
                page.screenshot(path=screenshots / f"frontend-{width}.png", full_page=True)
        test(f"Giao diện {width}px", "Mở demo, điền mẫu và xem biểu đồ.",
             "Thao tác được và không tràn ngang ở kích thước kiểm tra.", layout)

    if screenshots:
        page.set_viewport_size({"width": 1440, "height": 1050})
        open_form(page, "?demo=1", "demo")
        page.screenshot(path=screenshots / "frontend-form.png", full_page=True)
    page.close()
    if errors:
        rows.append(["Lỗi JavaScript", "Theo dõi pageerror.", "Không có lỗi JS.", " | ".join(errors), "Fail"])
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--screenshots", type=Path)
    parser.add_argument("--channel", choices=["chrome", "msedge"])
    args = parser.parse_args()
    if args.screenshots:
        args.screenshots.mkdir(parents=True, exist_ok=True)
    with ThreadingHTTPServer(("127.0.0.1", 5500), partial(QuietHandler, directory=FRONTEND)) as ui, \
         ThreadingHTTPServer(("127.0.0.1", 8000), FixtureApi) as api, sync_playwright() as playwright:
        for server in (ui, api):
            threading.Thread(target=server.serve_forever, daemon=True).start()
        browser_path = os.environ.get("BROWSER_PATH") or shutil.which("chromium")
        launch = {"channel": args.channel} if args.channel else (
            {"executable_path": browser_path} if browser_path else {}
        )
        browser = playwright.chromium.launch(**launch)
        try:
            results = run_tests(browser, args.screenshots)
        finally:
            browser.close()
        for server in (ui, api):
            server.shutdown()
    if args.out:
        with args.out.open("w", encoding="utf-8-sig", newline="") as result_file:
            writer = csv.writer(result_file, lineterminator="\n")
            writer.writerow(["ID", "Ca kiểm thử", "Bước thực hiện", "Kỳ vọng", "Thực tế với fixture", "Trạng thái fixture", "Chạy model thật"])
            for index, row in enumerate(results, start=1):
                writer.writerow([f"FE-{index:02}", *row, "Chờ BE-09 và model"])
    for label, _, _, actual, status in results:
        print(f"{status:4}  {label}" + (f" — {actual}" if status == "Fail" else ""))
    print(f"{sum(row[-1] == 'Pass' for row in results)}/{len(results)} passed")
    return int(any(row[-1] == "Fail" for row in results))


if __name__ == "__main__":
    raise SystemExit(main())
