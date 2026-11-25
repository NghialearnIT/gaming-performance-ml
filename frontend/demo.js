// UI fixtures only. Values are deliberately illustrative and are never benchmarks.
const fpsByGame = {
  valorant: [[184, 117], [151, 98], [124, 79]],
  cs2: [[153, 92], [116, 72], [86, 49]],
  pubg: [[101, 59], [78, 43], [58, 34]],
  fc_online: [[113, 76], [94, 63], [76, 48]],
  lol: [[171, 124], [146, 106], [120, null]],
};

export function examplePrediction(payload) {
  const index = ['low', 'medium', 'high'].indexOf(payload.graphics_preset);
  const [avg, low] = fpsByGame[payload.game][index];
  const warnings = [];
  if (payload.device_type === 'laptop') {
    warnings.push(payload.gpu_tgp_w === null
      ? 'Chưa nhập TGP của GPU Laptop.'
      : 'TGP trong cấu hình mẫu dùng để minh họa biểu mẫu.');
  }
  return new Promise(resolve => {
    setTimeout(() => resolve({
      avg_fps: avg,
      one_percent_low_fps: low,
      model_version: 'STUB',
      is_stub: true,
      warnings,
    }), 180);
  });
}
