import { API_BASE_URL, REQUEST_TIMEOUT_MS } from './config.js';

const byId = id => document.getElementById(id);
const form = byId('predict-form');
const fields = byId('fields');
const demo = new URLSearchParams(location.search).get('demo') === '1';
const presetOrder = ['low', 'medium', 'high'];
const fpsTiers = [
  { min: 144, label: '144+ FPS · Rất mượt' },
  { min: 60, label: '60–143 FPS · Mượt' },
  { min: 30, label: '30–59 FPS · Chơi được' },
  { min: 0, label: 'Dưới 30 FPS · Thấp' },
];
const optionKeys = {
  device_types: ['device_types', 'device_type'],
  games: ['games', 'game'],
  resolutions: ['resolutions', 'resolution'],
  graphics_presets: ['graphics_presets', 'presets', 'graphics_preset'],
  cpu_models: ['cpu_models', 'cpus', 'cpu_model'],
  gpu_models: ['gpu_models', 'gpus', 'gpu_model'],
  ram_types: ['ram_types', 'ram_type'],
  ram_channels: ['ram_channels'],
};
const displayNames = {
  desktop: 'Desktop', laptop: 'Laptop', valorant: 'Valorant', cs2: 'Counter-Strike 2',
  pubg: 'PUBG', fc_online: 'FC Online', lol: 'League of Legends',
  '1920x1080': '1920 × 1080', low: 'Low', medium: 'Medium', high: 'High',
  single: '1 kênh', dual: '2 kênh', quad: '4 kênh',
  1: '1 kênh', 2: '2 kênh', 4: '4 kênh',
};
const numericFields = ['gpu_vram_gb', 'gpu_tgp_w', 'ram_gb'];
const requiredSelects = {
  game: 'Chọn một trò chơi.',
  resolution: 'Chọn độ phân giải.',
  graphics_preset: 'Chọn mức đồ họa.',
};
const serverMessages = {
  missing: 'Trường này là bắt buộc.',
  int_parsing: 'Nhập một số nguyên.',
  float_parsing: 'Nhập một số hợp lệ.',
  enum: 'Chọn giá trị có trong danh sách.',
  greater_than: 'Giá trị nhập chưa đạt mức tối thiểu.',
  greater_than_equal: 'Giá trị nhập chưa đạt mức tối thiểu.',
  less_than_equal: 'Giá trị vượt mức tối đa.',
};
const fieldNames = ['device_type', 'cpu_model', 'gpu_model', ...numericFields,
  'ram_type', 'ram_channels', ...Object.keys(requiredSelects)];
const touched = new Set();
const serverErrors = new Map();
const fpsFormat = new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 0 });

let options;
let chart;
let busy = false;
let pendingPayload;

class HttpError extends Error {
  constructor(status, body) {
    super(`HTTP ${status}`);
    this.status = status;
    this.body = body;
  }
}

async function fetchJson(url, request = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    const response = await fetch(url, { ...request, signal: controller.signal, cache: 'no-store' });
    let body;
    try {
      body = await response.json();
    } catch (error) {
      if (error.name === 'AbortError' || response.ok) throw error;
    }
    if (!response.ok) throw new HttpError(response.status, body);
    return body;
  } finally {
    clearTimeout(timer);
  }
}

function apiUrl(path) {
  return `${API_BASE_URL.replace(/\/+$/, '')}${path}`;
}

function normalizeOptions(payload) {
  const catalog = {};
  for (const [key, aliases] of Object.entries(optionKeys)) {
    const raw = aliases.map(alias => payload[alias]).find(Array.isArray) ?? [];
    const seen = new Set();
    catalog[key] = raw.flatMap(item => {
      const value = item && typeof item === 'object' ? item.value : item;
      if (!['string', 'number'].includes(typeof value) || !String(value).trim() || seen.has(String(value))) {
        return [];
      }
      seen.add(String(value));
      const label = item?.label ?? displayNames[String(value).toLowerCase()] ?? String(value);
      return [{ value, label }];
    });
  }
  if (['device_types', 'games', 'resolutions', 'graphics_presets'].some(key => !catalog[key].length)) {
    throw new Error('Danh sách tùy chọn không đủ trường bắt buộc.');
  }
  if (!catalog.device_types.some(option => ['desktop', 'laptop'].includes(String(option.value).toLowerCase()))) {
    throw new Error('Danh sách loại thiết bị không hợp lệ.');
  }
  return catalog;
}

function setConnection(state, message) {
  byId('connection').dataset.state = state;
  byId('connection').textContent = message;
}

function populateSelect(id, values, placeholder, defaultValue = '') {
  const select = byId(id);
  select.replaceChildren(new Option(placeholder, '', !defaultValue, !defaultValue));
  for (const option of values) {
    const selected = String(option.value) === defaultValue;
    select.add(new Option(option.label, String(option.value), selected, selected));
  }
}

function populateFields() {
  const devices = ['desktop', 'laptop'].map(id => byId(id));
  for (const input of devices) {
    const match = options.device_types.find(option => String(option.value).toLowerCase() === input.id);
    input.closest('.device-choices').querySelector(`label[for="${input.id}"]`).hidden = !match;
    input.disabled = !match;
    input.value = match?.value ?? input.id;
    input.defaultChecked = false;
    input.checked = false;
  }
  const firstDevice = devices.find(input => !input.disabled);
  firstDevice.defaultChecked = true;
  firstDevice.checked = true;
  populateSelect('game', options.games, 'Chọn trò chơi');
  const defaultResolution = options.resolutions.length === 1 ? String(options.resolutions[0].value) : '';
  populateSelect('resolution', options.resolutions, 'Chọn độ phân giải', defaultResolution);
  populateSelect('graphics_preset', options.graphics_presets, 'Chọn mức đồ họa');
  populateSelect('ram_type', options.ram_types, 'Không rõ');
  populateSelect('ram_channels', options.ram_channels, 'Không rõ');
  for (const [id, key] of [['cpu-options', 'cpu_models'], ['gpu-options', 'gpu_models']]) {
    byId(id).replaceChildren(...options[key].map(option => new Option(option.label, String(option.value))));
  }
}

function isLaptop() {
  return form.elements.device_type.value.toLowerCase() === 'laptop';
}

function updateDevice() {
  byId('tgp-field').hidden = !isLaptop();
  byId('gpu_tgp_w').disabled = !isLaptop();
}

function validationErrors() {
  const errors = { ...Object.fromEntries(serverErrors) };
  if (!isLaptop()) delete errors.gpu_tgp_w;
  for (const [name, label] of [['cpu_model', 'CPU'], ['gpu_model', 'GPU']]) {
    if (!byId(name).value.trim()) errors[name] = `Nhập tên ${label}.`;
  }
  for (const [name, error] of Object.entries(requiredSelects)) {
    if (!byId(name).value) errors[name] = error;
  }
  const ram = byId('ram_gb');
  if (!Number.isInteger(ram.valueAsNumber) || ram.valueAsNumber < 1) {
    errors.ram_gb = 'Nhập dung lượng RAM là số nguyên lớn hơn 0.';
  }
  for (const [name, label] of [['gpu_vram_gb', 'VRAM'], ['gpu_tgp_w', 'TGP']]) {
    const input = byId(name);
    if (!input.disabled && (input.validity.badInput || (input.value !== '' && !(input.valueAsNumber > 0)))) {
      errors[name] = `Nhập ${label} lớn hơn 0 hoặc để trống.`;
    }
  }
  return errors;
}

function updateForm() {
  const errors = validationErrors();
  for (const name of fieldNames) {
    const message = (touched.has(name) || serverErrors.has(name)) ? errors[name] : '';
    const feedback = byId(`${name}-error`);
    feedback.textContent = message ?? '';
    feedback.hidden = !message;
    const inputs = name === 'device_type' ? [byId('desktop'), byId('laptop')] : [byId(name)];
    for (const input of inputs) {
      if (message) input.setAttribute('aria-invalid', 'true');
      else input.removeAttribute('aria-invalid');
      const descriptions = [name === 'gpu_tgp_w' ? 'tgp-hint' : '', message ? feedback.id : ''].filter(Boolean);
      if (descriptions.length) input.setAttribute('aria-describedby', descriptions.join(' '));
      else input.removeAttribute('aria-describedby');
    }
  }
  byId('predict').disabled = !options || busy || Object.keys(errors).length > 0;
  byId('reset-form').disabled = !options || busy;
}

function fieldValue(name, optionKey) {
  const value = byId(name).value;
  return options[optionKey].find(option => String(option.value) === value)?.value ?? null;
}

function getPayload() {
  return {
    device_type: form.elements.device_type.value,
    cpu_model: byId('cpu_model').value.trim(),
    gpu_model: byId('gpu_model').value.trim(),
    gpu_vram_gb: byId('gpu_vram_gb').value === '' ? null : byId('gpu_vram_gb').valueAsNumber,
    gpu_tgp_w: isLaptop() && byId('gpu_tgp_w').value !== '' ? byId('gpu_tgp_w').valueAsNumber : null,
    ram_gb: byId('ram_gb').valueAsNumber,
    ram_type: fieldValue('ram_type', 'ram_types'),
    ram_channels: fieldValue('ram_channels', 'ram_channels'),
    game: fieldValue('game', 'games'),
    resolution: fieldValue('resolution', 'resolutions'),
    graphics_preset: fieldValue('graphics_preset', 'graphics_presets'),
  };
}

function formatFps(value) {
  return value === null ? '—' : fpsFormat.format(value);
}

function isStub(response) {
  return response.is_stub === true || response.model_version.trim().toUpperCase() === 'STUB';
}

function clearResults() {
  chart?.destroy();
  chart = undefined;
  for (const id of ['tier', 'model', 'warnings', 'stub-warning', 'api-error', 'retry',
    'chart-area', 'chart-legend', 'comparison-table']) byId(id).hidden = true;
  byId('avg').textContent = '—';
  byId('low').textContent = '—';
  byId('result-config').textContent = 'Chưa có cấu hình được gửi';
  byId('comparison-status').textContent = 'Gửi cấu hình để so sánh Low, Medium và High.';
}

function renderResults(response, payload) {
  byId('avg').textContent = formatFps(response.avg_fps);
  byId('low').textContent = formatFps(response.one_percent_low_fps);
  const tier = fpsTiers.find(item => Math.round(response.avg_fps) >= item.min);
  byId('tier').textContent = tier.label;
  byId('tier').dataset.tier = tier.min;
  byId('tier').hidden = false;
  const config = [options.games.find(item => item.value === payload.game)?.label,
    displayNames[payload.device_type.toLowerCase()], byId('graphics_preset').selectedOptions[0].textContent];
  byId('result-config').textContent = config.join(' · ');
  const source = isStub(response) ? 'Kết quả thử nghiệm' : 'Ước lượng từ mô hình ML';
  const lowInfo = response.one_percent_low_fps === null ? ' · Chưa có ước lượng 1% Low FPS' : '';
  byId('model').textContent = `${source} · Phiên bản ${response.model_version}${lowInfo}`;
  byId('model').hidden = false;
  byId('stub-warning').hidden = !isStub(response);
  const warnings = response.warnings.filter(item => typeof item === 'string' && item.trim());
  byId('warning-list').replaceChildren(...warnings.map(warning => {
    const item = document.createElement('li');
    item.textContent = warning;
    return item;
  }));
  byId('warnings').hidden = !warnings.length;
}

function renderComparison(presets, results) {
  const rows = results.map((result, index) => ({
    ...presets[index],
    response: result.status === 'fulfilled' ? result.value : null,
  }));
  const failures = rows.filter(row => !row.response).map(row => row.label);
  const highest = [...rows].reverse().find(row => row.response?.avg_fps >= 60);
  const containsStub = rows.some(row => row.response && isStub(row.response));
  const status = byId('comparison-status');
  if (containsStub) {
    byId('stub-warning').hidden = false;
    status.textContent = 'Biểu đồ có số liệu thử nghiệm.';
  } else if (!failures.length) {
    status.textContent = highest ? `${highest.label} là preset cao nhất đạt trung bình 60 FPS.` :
      'Các preset đã thử đều có Average FPS dưới 60.';
  } else {
    status.textContent = 'So sánh chưa đủ cả ba preset.';
  }
  if (failures.length) status.append(` Chưa tải được: ${failures.join(', ')}.`);

  byId('comparison-rows').replaceChildren(...rows.map(row => {
    const entry = document.createElement('tr');
    for (const [index, value] of [row.label, formatFps(row.response?.avg_fps ?? null),
      formatFps(row.response?.one_percent_low_fps ?? null)].entries()) {
      const cell = document.createElement(index === 0 ? 'th' : 'td');
      if (index === 0) cell.scope = 'row';
      cell.textContent = value;
      entry.append(cell);
    }
    return entry;
  }));
  byId('comparison-table').hidden = false;
  if (!window.Chart) {
    byId('comparison-table').className = 'table table-dark table-sm';
    return;
  }
  byId('chart-area').hidden = false;
  byId('chart-legend').hidden = false;
  chart = new window.Chart(byId('chart'), {
    type: 'bar',
    data: {
      labels: rows.map(row => row.label),
      datasets: [
        { label: 'Average FPS', data: rows.map(row => row.response?.avg_fps ?? null), backgroundColor: '#d1f86c' },
        { label: '1% Low FPS', data: rows.map(row => row.response?.one_percent_low_fps ?? null), backgroundColor: '#8fc8fa' },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      scales: {
        x: { grid: { display: false }, ticks: { color: '#d9e4d9' } },
        y: { beginAtZero: true, grid: { color: '#364137' }, ticks: { color: '#aeb9af', maxTicksLimit: 5 } },
      },
      plugins: { legend: { display: false } },
    },
  });
}

function showError(error) {
  let message = 'Không kết nối được API. Kiểm tra backend hoặc CORS rồi thử lại.';
  let retryable = true;
  if (error.name === 'AbortError') message = 'API phản hồi quá 10 giây. Bạn có thể thử lại.';
  if (error instanceof HttpError) {
    const detail = error.body?.detail ?? error.body?.message;
    if (error.status === 422) {
      const issues = Array.isArray(detail) ? detail : [];
      for (const issue of issues) {
        const field = Array.isArray(issue?.loc) ?
          [...issue.loc].reverse().find(part => fieldNames.includes(part)) : undefined;
        if (field && (field !== 'gpu_tgp_w' || isLaptop())) {
          serverErrors.set(field, serverMessages[issue.type] ?? issue.msg ?? 'Giá trị không hợp lệ.');
        }
      }
      message = typeof detail === 'string' ? detail :
        serverErrors.size ? 'API yêu cầu sửa các trường được đánh dấu.' : 'API từ chối cấu hình. Hãy kiểm tra dữ liệu đã nhập.';
      retryable = false;
    } else if (error.status === 400) {
      message = typeof detail === 'string' ? detail : 'Cấu hình chưa được API hỗ trợ.';
      retryable = false;
    } else if (error.status >= 500) {
      message = 'Máy chủ đang gặp lỗi khi dự đoán. Bạn có thể thử lại.';
    } else {
      message = `API trả mã ${error.status}. Kiểm tra địa chỉ và endpoint của backend.`;
    }
  } else if (error instanceof SyntaxError || error.message === 'invalid-prediction') {
    message = 'API trả dữ liệu FPS không đúng định dạng. Kiểm tra hợp đồng API rồi thử lại.';
  }
  byId('error-message').textContent = message;
  byId('api-error').hidden = false;
  byId('retry').hidden = !retryable;
}

function setBusy(value) {
  busy = value;
  fields.disabled = value;
  byId('spinner').hidden = !value;
  byId('submit-arrow').hidden = value;
  byId('submit-label').textContent = value ? 'Đang dự đoán…' : 'Dự đoán FPS';
  byId('sample').disabled = value;
  form.setAttribute('aria-busy', String(value));
  updateForm();
}

async function predict(payload) {
  let result;
  if (demo) {
    const { examplePrediction } = await import('./demo.js');
    result = await examplePrediction(payload);
  } else {
    result = await fetchJson(apiUrl('/predict'), {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
    });
  }
  const validFps = value => Number.isFinite(value) && value >= 0;
  const low = result?.one_percent_low_fps ?? null;
  if (!validFps(result?.avg_fps) || (low !== null && !validFps(low)) ||
      typeof result.model_version !== 'string' || !result.model_version.trim()) {
    throw new Error('invalid-prediction');
  }
  return { ...result, one_percent_low_fps: low, warnings: Array.isArray(result.warnings) ? result.warnings : [] };
}

async function submit(payload) {
  pendingPayload = payload;
  clearResults();
  setBusy(true);
  byId('result-config').textContent = 'Đang chờ kết quả dự đoán…';
  try {
    const result = await predict(payload);
    renderResults(result, payload);
    const presets = presetOrder.map(name => options.graphics_presets.find(item =>
      String(item.value).toLowerCase() === name));
    if (presets.every(Boolean)) {
      byId('comparison-status').textContent = 'Đang so sánh ba preset…';
      const results = await Promise.allSettled(presets.map(preset => preset.value === payload.graphics_preset ?
        Promise.resolve(result) : predict({ ...payload, graphics_preset: preset.value })));
      renderComparison(presets, results);
    } else {
      byId('comparison-status').textContent = 'Danh sách từ API chưa có đủ Low, Medium và High.';
    }
  } catch (error) {
    byId('result-config').textContent = 'Chưa nhận được kết quả';
    showError(error);
  } finally {
    setBusy(false);
  }
}

form.addEventListener('submit', event => {
  event.preventDefault();
  if (!byId('predict').disabled) void submit(getPayload());
});
form.addEventListener('input', event => {
  const name = event.target.name;
  if (fieldNames.includes(name)) touched.add(name);
  serverErrors.delete(name);
  if (name === 'device_type') {
    serverErrors.delete('gpu_tgp_w');
    updateDevice();
  }
  pendingPayload = undefined;
  byId('retry').hidden = true;
  updateForm();
});
form.addEventListener('focusout', event => {
  if (fieldNames.includes(event.target.name)) {
    touched.add(event.target.name);
    updateForm();
  }
});
byId('reset-form').addEventListener('click', () => {
  form.reset();
  touched.clear();
  serverErrors.clear();
  pendingPayload = undefined;
  clearResults();
  updateDevice();
  updateForm();
});
byId('retry').addEventListener('click', () => {
  if (pendingPayload && !busy) void submit(pendingPayload);
});
byId('sample').addEventListener('click', () => {
  byId('desktop').checked = true;
  for (const [id, value] of Object.entries({
    cpu_model: 'Intel Core i5-12400F', gpu_model: 'NVIDIA RTX 3060',
    ram_gb: '16', gpu_vram_gb: '12', gpu_tgp_w: '', ram_type: 'DDR4',
    ram_channels: 'dual', game: 'valorant', resolution: '1920x1080', graphics_preset: 'high',
  })) byId(id).value = value;
  touched.clear();
  serverErrors.clear();
  pendingPayload = undefined;
  clearResults();
  updateDevice();
  updateForm();
});

async function initialize() {
  if (demo) {
    byId('mode-link').href = './';
    byId('mode-link').textContent = 'Quay lại chế độ API ↗︎';
  } else {
    try {
      options = normalizeOptions(await fetchJson(apiUrl('/options')));
      setConnection('online', 'Đã tải danh sách cấu hình từ API');
    } catch {
      setConnection('offline', 'Không tải được danh sách từ API. Đang dùng danh sách nhập mẫu.');
    }
  }
  if (!options) {
    try {
      options = normalizeOptions(await fetchJson('./mock-options.json'));
      if (demo) setConnection('demo', 'Chế độ demo · FPS minh họa dùng để thử giao diện');
    } catch {
      setConnection('offline', 'Không tải được danh sách cấu hình. Hãy mở trang qua máy chủ HTTP và tải lại.');
      return;
    }
  }
  populateFields();
  fields.disabled = false;
  byId('sample').hidden = !demo;
  updateDevice();
  updateForm();
}

void initialize();
