import { API_BASE_URL, REQUEST_TIMEOUT_MS } from './config.js';

const byId = id => document.getElementById(id);
const form = byId('predict-form');
const fields = byId('fields');
const gameFieldset = byId('game-fieldset');
const advanced = byId('advanced-options');
const radioGroups = {
  device_type: byId('device-options'),
  game: byId('game-options'),
  graphics_preset: byId('preset-options'),
};
const demo = new URLSearchParams(location.search).get('demo') === '1';
const presetOrder = ['low', 'medium', 'high'];
const gameArtwork = {
  valorant: 'valorant',
  cs2: 'cs2',
  counterstrike2: 'cs2',
  pubg: 'pubg',
  pubgbattlegrounds: 'pubg',
  playerunknownsbattlegrounds: 'pubg',
  fconline: 'fc_online',
  leagueoflegends: 'lol',
  lol: 'lol',
};
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
const advancedFields = ['gpu_vram_gb', 'gpu_tgp_w', 'ram_type', 'ram_channels'];
const requiredChoices = {
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
  'ram_type', 'ram_channels', ...Object.keys(requiredChoices)];
const touched = new Set();
const serverErrors = new Map();
const fpsFormat = new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 0 });

let options;
let chart;
let busy = false;
let pendingPayload;
let displayedPayload;

const selectedPresetBand = {
  id: 'selectedPresetBand',
  beforeDatasetsDraw({ ctx, chartArea, scales }, _args, { index, count, color }) {
    if (index < 0) return;
    const bandWidth = chartArea.width / count;
    const left = scales.x.getPixelForValue(index) - bandWidth / 2 + 2;
    ctx.save();
    ctx.fillStyle = color;
    ctx.fillRect(left, chartArea.top, bandWidth - 4, chartArea.height);
    ctx.restore();
  },
};

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

function artworkFor({ value, label }) {
  const key = name => String(name).toLowerCase().replace(/[^a-z0-9]/g, '');
  return gameArtwork[key(value)] ?? gameArtwork[key(label)] ?? '';
}

function populateChoices(name, choices) {
  const entries = choices.map((choice, index) => {
    const game = name === 'game';
    const item = document.createElement('div');
    item.className = game ? 'game-choice' : 'radio-choice';
    const input = document.createElement('input');
    input.type = 'radio';
    input.className = 'btn-check';
    input.name = name;
    input.id = `${name}-choice-${index}`;
    input.value = choice.value;
    input.required = true;
    const label = document.createElement('label');
    label.htmlFor = input.id;
    label.textContent = choice.label;
    if (game) {
      label.className = 'game-card';
      label.dataset.art = artworkFor(choice);
    }
    item.append(input, label);
    return item;
  });
  radioGroups[name].replaceChildren(...entries);
}

function inputsFor(name) {
  return radioGroups[name] ? [...radioGroups[name].querySelectorAll('input')] : [byId(name)];
}

function formValue(name) {
  const group = radioGroups[name];
  return group ? group.querySelector('input:checked')?.value ?? '' : byId(name).value;
}

function selectChoice(name, preferred) {
  const candidates = inputsFor(name);
  const match = candidates.find(input => input.value === preferred && !input.disabled) ??
    candidates.find(input => !input.disabled);
  if (match) match.checked = true;
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
  populateChoices('game', options.games);
  const defaultResolution = options.resolutions.length === 1 ? String(options.resolutions[0].value) : '';
  populateSelect('resolution', options.resolutions, 'Chọn độ phân giải', defaultResolution);
  populateChoices('graphics_preset', options.graphics_presets);
  populateSelect('ram_type', options.ram_types, 'Không rõ');
  populateSelect('ram_channels', options.ram_channels, 'Không rõ');
  for (const [id, key] of [['cpu-options', 'cpu_models'], ['gpu-options', 'gpu_models']]) {
    byId(id).replaceChildren(...options[key].map(option => new Option(option.label, String(option.value))));
  }
}

function isLaptop() {
  return formValue('device_type').toLowerCase() === 'laptop';
}

function updateDevice(expand = false) {
  const laptop = isLaptop();
  byId('tgp-field').hidden = !laptop;
  byId('gpu_tgp_w').disabled = !laptop;
  if (laptop && expand) advanced.open = true;
}

function validationErrors() {
  const errors = { ...Object.fromEntries(serverErrors) };
  if (!isLaptop()) delete errors.gpu_tgp_w;
  for (const [name, label] of [['cpu_model', 'CPU'], ['gpu_model', 'GPU']]) {
    if (!byId(name).value.trim()) errors[name] = `Nhập tên ${label}.`;
  }
  for (const [name, error] of Object.entries(requiredChoices)) {
    if (!formValue(name)) errors[name] = error;
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
    for (const input of inputsFor(name)) {
      if (message) input.setAttribute('aria-invalid', 'true');
      else input.removeAttribute('aria-invalid');
      const descriptions = [name === 'gpu_tgp_w' ? 'tgp-hint' : '', message ? feedback.id : ''].filter(Boolean);
      if (descriptions.length) input.setAttribute('aria-describedby', descriptions.join(' '));
      else input.removeAttribute('aria-describedby');
    }
  }
  const advancedInvalid = advancedFields.some(name => errors[name]);
  advanced.toggleAttribute('data-error', advancedInvalid);
  byId('advanced-note').textContent = advancedInvalid ? 'Cần kiểm tra' : 'Tùy chọn';
  const invalid = Object.keys(errors).length > 0;
  byId('predict').disabled = !options || busy || invalid;
  byId('form-guidance').textContent = options && !busy && invalid ?
    'Hoàn thành các mục có dấu * và kiểm tra lỗi nhập liệu.' : '';
  byId('reset-form').disabled = !options || busy;
}

function fieldValue(name, optionKey) {
  const value = formValue(name);
  return options[optionKey].find(option => String(option.value) === value)?.value ?? null;
}

function getPayload() {
  return {
    device_type: formValue('device_type'),
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

function optionLabel(key, value) {
  return options[key].find(option => option.value === value)?.label ?? String(value);
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
  displayedPayload = undefined;
  for (const id of ['tier', 'model', 'warnings', 'stub-warning', 'stale-result', 'api-error', 'retry',
    'chart-area', 'chart-legend', 'comparison-details', 'comparison-selected']) byId(id).hidden = true;
  byId('comparison-details').open = false;
  byId('comparison-empty').hidden = false;
  byId('avg').textContent = '—';
  byId('low').textContent = '—';
  byId('result-config').textContent = 'Chưa có cấu hình được gửi';
  byId('comparison-status').textContent = 'Gửi cấu hình để so sánh Low, Medium và High.';
}

function renderResults(response, payload) {
  displayedPayload = JSON.stringify(payload);
  byId('avg').textContent = formatFps(response.avg_fps);
  byId('low').textContent = formatFps(response.one_percent_low_fps);
  const tier = fpsTiers.find(item => Math.round(response.avg_fps) >= item.min);
  byId('tier').textContent = tier.label;
  byId('tier').dataset.tier = tier.min;
  byId('tier').hidden = false;
  const config = [
    optionLabel('games', payload.game),
    optionLabel('resolutions', payload.resolution),
    optionLabel('graphics_presets', payload.graphics_preset),
    displayNames[payload.device_type.toLowerCase()],
  ];
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

function renderComparison(presets, results, submittedPreset) {
  const rows = results.map((result, index) => ({
    ...presets[index],
    response: result.status === 'fulfilled' ? result.value : null,
  }));
  const selectedIndex = rows.findIndex(row => row.value === submittedPreset);
  const selectedLabel = byId('comparison-selected');
  if (selectedIndex >= 0) {
    selectedLabel.textContent = `Mức đã dự đoán · ${rows[selectedIndex].label}`;
    selectedLabel.hidden = false;
  }
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

  byId('comparison-rows').replaceChildren(...rows.map((row, rowIndex) => {
    const entry = document.createElement('tr');
    const selected = rowIndex === selectedIndex;
    if (selected) entry.className = 'active-preset';
    for (const [index, value] of [row.label, formatFps(row.response?.avg_fps ?? null),
      formatFps(row.response?.one_percent_low_fps ?? null)].entries()) {
      const cell = document.createElement(index === 0 ? 'th' : 'td');
      if (index === 0) cell.scope = 'row';
      cell.textContent = value;
      if (index === 0 && selected) {
        const note = document.createElement('span');
        note.className = 'visually-hidden';
        note.textContent = ' (mức đã dự đoán)';
        cell.append(note);
      }
      entry.append(cell);
    }
    return entry;
  }));
  byId('comparison-empty').hidden = true;
  byId('comparison-details').hidden = false;
  if (!window.Chart) {
    byId('comparison-details').open = true;
    return;
  }
  const colors = getComputedStyle(document.documentElement);
  const color = name => colors.getPropertyValue(name).trim();
  byId('chart-area').hidden = false;
  byId('chart-legend').hidden = false;
  chart = new window.Chart(byId('chart'), {
    type: 'bar',
    data: {
      labels: rows.map(row => row.label),
      datasets: [
        { label: 'Average FPS', data: rows.map(row => row.response?.avg_fps ?? null), backgroundColor: color('--avg'), borderRadius: 4, maxBarThickness: 30 },
        { label: '1% Low FPS', data: rows.map(row => row.response?.one_percent_low_fps ?? null), backgroundColor: color('--low'), borderRadius: 4, maxBarThickness: 30 },
      ],
    },
    plugins: [selectedPresetBand],
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      scales: {
        x: { grid: { display: false }, ticks: { color: tick => color(tick.index === selectedIndex ? '--accent' : '--muted') } },
        y: { beginAtZero: true, grid: { color: color('--chart-grid') }, ticks: { color: color('--muted'), maxTicksLimit: 5 } },
      },
      plugins: {
        legend: { display: false },
        selectedPresetBand: { index: selectedIndex, count: rows.length, color: color('--chart-selected') },
      },
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
      if (advancedFields.some(name => serverErrors.has(name))) advanced.open = true;
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
  gameFieldset.disabled = value;
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
    if (window.matchMedia('(max-width: 960px)').matches) byId('result-title').focus();
    const presets = presetOrder.map(name => options.graphics_presets.find(item =>
      String(item.value).toLowerCase() === name));
    if (presets.every(Boolean)) {
      byId('comparison-status').textContent = 'Đang so sánh ba preset…';
      const results = await Promise.allSettled(presets.map(preset => preset.value === payload.graphics_preset ?
        Promise.resolve(result) : predict({ ...payload, graphics_preset: preset.value })));
      renderComparison(presets, results, payload.graphics_preset);
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
    updateDevice(true);
  }
  pendingPayload = undefined;
  byId('retry').hidden = true;
  byId('stale-result').hidden = !displayedPayload || displayedPayload === JSON.stringify(getPayload());
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
  advanced.open = false;
  updateDevice(true);
  updateForm();
});
byId('retry').addEventListener('click', () => {
  if (pendingPayload && !busy) void submit(pendingPayload);
});
byId('sample').addEventListener('click', () => {
  const laptop = isLaptop();
  if (!formValue('game')) selectChoice('game', 'valorant');
  if (!formValue('graphics_preset')) selectChoice('graphics_preset', 'high');
  for (const [id, value] of Object.entries({
    cpu_model: laptop ? 'Intel Core i7-12700H' : 'Intel Core i5-12400F',
    gpu_model: laptop ? 'NVIDIA RTX 4060 Laptop GPU' : 'NVIDIA RTX 3060',
    ram_gb: '16', gpu_vram_gb: laptop ? '8' : '12', gpu_tgp_w: '',
    ram_type: laptop ? 'DDR5' : 'DDR4', ram_channels: 'dual',
  })) byId(id).value = value;
  touched.clear();
  serverErrors.clear();
  pendingPayload = undefined;
  clearResults();
  updateDevice(true);
  updateForm();
});

async function initialize() {
  if (demo) {
    byId('mode-link').href = './';
    byId('mode-link').textContent = 'Chế độ API →';
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
  gameFieldset.disabled = false;
  byId('sample').hidden = !demo;
  updateDevice(true);
  updateForm();
}

void initialize();
