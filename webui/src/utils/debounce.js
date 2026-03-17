/**
 * Phase I-5: APIコール最適化 - デバウンスユーティリティ
 * @param {Function} fn - デバウンス対象の関数
 * @param {number} delay - 待機時間(ms)、デフォルト300ms
 * @returns {Function} デバウンスされた関数
 */
export function debounce(fn, delay = 300) {
  let timer = null;
  return function (...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}

/**
 * Phase I-5: APIバッチング - 複数リクエストを1回にまとめる
 * @param {Function} fn - バッチ処理対象の関数
 * @param {number} delay - バッチ収集時間(ms)、デフォルト50ms
 * @returns {Function} バッチ処理された関数
 */
export function batchDebounce(fn, delay = 50) {
  let timer = null;
  const batch = [];
  return function (item) {
    batch.push(item);
    clearTimeout(timer);
    timer = setTimeout(() => {
      const items = batch.splice(0);
      fn(items);
    }, delay);
  };
}
