/* 全站访问守卫：未通过密码验证前遮蔽页面内容。
   纯静态站方案的边界：这是"进入门槛"而非真加密，防普通访客，不防看源码的人。 */
(function () {
  'use strict';
  var KEY = 'wb_gate_v1';
  // base64('0') —— 轻度混淆，不追求对抗逆向
  var CHECK = 'MA==';

  function authed() {
    try {
      return window.localStorage && window.localStorage.getItem(KEY) === '1';
    } catch (e) { return false; }
  }

  function check(input) {
    try { return window.btoa(input) === CHECK; }
    catch (e) { return false; }
  }

  if (authed()) return;

  // 立即遮蔽页面（visibility 可被后代显式覆盖，故遮罩层自身可见）
  document.documentElement.style.visibility = 'hidden';

  function boot() {
    if (authed()) {
      document.documentElement.style.visibility = '';
      return;
    }
    if (document.getElementById('wb-gate')) return;

    var ov = document.createElement('div');
    ov.id = 'wb-gate';
    ov.setAttribute('style',
      'position:fixed;inset:0;z-index:2147483647;display:flex;align-items:center;justify-content:center;' +
      'background:#0a0e1a;visibility:visible;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans SC",sans-serif;');
    ov.innerHTML =
      '<div style="width:min(360px,88vw);background:rgba(20,28,48,0.75);border:1px solid rgba(0,212,255,0.25);' +
      'border-radius:20px;padding:36px 28px;text-align:center;box-shadow:0 16px 56px rgba(0,0,0,0.45);">' +
      '<div style="font-size:2.2rem;line-height:1;margin-bottom:14px;">&#128274;</div>' +
      '<div style="color:#f0f4f8;font-size:1.15rem;font-weight:700;margin-bottom:6px;">访问验证</div>' +
      '<div style="color:#90a0c0;font-size:0.82rem;margin-bottom:20px;">本站内容需输入密码后查看</div>' +
      '<input id="wb-gate-pass" type="password" inputmode="numeric" autocomplete="off" placeholder="请输入密码" ' +
      'style="width:100%;box-sizing:border-box;background:#111726;border:1px solid rgba(0,212,255,0.3);color:#f0f4f8;' +
      'border-radius:12px;padding:12px 14px;font-size:1rem;outline:none;text-align:center;letter-spacing:2px;" />' +
      '<div id="wb-gate-err" style="color:#f87171;font-size:0.8rem;min-height:1.2em;margin-top:8px;"></div>' +
      '<button id="wb-gate-btn" type="button" style="width:100%;margin-top:6px;background:linear-gradient(135deg,#00d4ff,#818cf8);' +
      'border:none;color:#0a0e1a;font-weight:700;font-size:0.95rem;border-radius:12px;padding:12px 0;cursor:pointer;">' +
      '\u8fdb\u5165</button>' +
      '</div>';

    document.body.appendChild(ov);

    var input = ov.querySelector('#wb-gate-pass');
    var err = ov.querySelector('#wb-gate-err');
    var btn = ov.querySelector('#wb-gate-btn');

    function attempt() {
      if (check(input.value)) {
        try { window.localStorage.setItem(KEY, '1'); } catch (e) {}
        ov.parentNode.removeChild(ov);
        document.documentElement.style.visibility = '';
      } else {
        err.textContent = '密码不正确，请重试';
        input.value = '';
        input.focus();
      }
    }

    btn.addEventListener('click', attempt);
    input.addEventListener('keydown', function (ev) {
      if (ev.key === 'Enter') attempt();
    });
    setTimeout(function () { input.focus(); }, 50);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
