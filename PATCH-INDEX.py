from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "index.html"
BACKUP = ROOT / "index.before-v2.7.html"
VERSION = "2.7.0"


def sub(pattern: str, repl: str, text: str, flags: int = 0) -> str:
    return re.sub(pattern, repl, text, flags=flags)


def remove_tag_by_id(html: str, tag: str, element_id: str) -> str:
    pattern = rf"<{tag}\b[^>]*\bid=[\"']{re.escape(element_id)}[\"'][^>]*>.*?</{tag}\s*>"
    return sub(pattern, "", html, flags=re.I | re.S)


def main() -> None:
    if not INDEX.exists():
        raise SystemExit(
            "Không tìm thấy index.html. Hãy đặt PATCH-INDEX.py cùng thư mục với index.html rồi chạy lại."
        )

    html = INDEX.read_text(encoding="utf-8", errors="replace")

    config_file = ROOT / "js" / "config.js"
    config_example = ROOT / "js" / "config.example.js"
    if not config_file.exists() and config_example.exists():
        config_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(config_example, config_file)
        print("Đã tạo js/config.js từ config.example.js vì project chưa có config.js.")

    if not BACKUP.exists():
        shutil.copy2(INDEX, BACKUP)

    # 1) Bỏ preload + runtime LadiPage chính.
    html = sub(
        r"<link\b(?=[^>]*\brel=[\"']preload[\"'])(?=[^>]*\bhref=[\"'][^\"']*ladipagev3\.min\.js[^\"']*[\"'])[^>]*>\s*",
        "",
        html,
        flags=re.I | re.S,
    )
    html = sub(
        r"<script\b[^>]*\bsrc=[\"'][^\"']*ladipagev3\.min\.js[^\"']*[\"'][^>]*>\s*</script>\s*",
        "",
        html,
        flags=re.I | re.S,
    )

    # 2) Không dùng runtime nữa => bỏ JSON event + vòng setTimeout chờ LadiPage.
    html = remove_tag_by_id(html, "script", "script_event_data")
    html = remove_tag_by_id(html, "script", "script_ladipage_run")

    # 3) Bỏ CSS animation ẩn phần tử do runtime trước đây quản lý.
    html = remove_tag_by_id(html, "style", "style_animation")

    # 3b) Thay lazyload kiểu "first scroll tải tất cả" bằng IntersectionObserver.
    lazy_script = r'''<script id="script_lazyload" type="text/javascript">
(function () {
  var body = document.body;
  var style = document.getElementById("style_lazyload");
  if (!body) return;

  var selector = [
    "body.lazyload .ladi-overlay",
    "body.lazyload .ladi-box",
    "body.lazyload .ladi-button-background",
    "body.lazyload .ladi-collection-item",
    "body.lazyload .ladi-countdown-background",
    "body.lazyload .ladi-form-item-background",
    "body.lazyload .ladi-form-label-container .ladi-form-label-item.image",
    "body.lazyload .ladi-frame-background",
    "body.lazyload .ladi-gallery-view-item",
    "body.lazyload .ladi-gallery-control-item",
    "body.lazyload .ladi-headline",
    "body.lazyload .ladi-image-background",
    "body.lazyload .ladi-image-compare",
    "body.lazyload .ladi-list-paragraph ul li",
    "body.lazyload .ladi-section-background",
    "body.lazyload .ladi-survey-option-background",
    "body.lazyload .ladi-survey-option-image",
    "body.lazyload .ladi-tabs-background",
    "body.lazyload .ladi-video-background",
    "body.lazyload .ladi-banner"
  ].join(",");

  var nodes = Array.prototype.slice.call(document.querySelectorAll(selector));
  var viewportHeight = window.innerHeight || document.documentElement.clientHeight || 800;
  var preloadMargin = 420;

  nodes.forEach(function (el) {
    var rect = el.getBoundingClientRect();
    if (rect.top > viewportHeight + preloadMargin || rect.bottom < -preloadMargin) {
      el.classList.add("ladi-lazyload");
    }
  });

  if (style && style.parentNode) style.parentNode.removeChild(style);
  body.classList.remove("lazyload");

  var lazyNodes = Array.prototype.slice.call(document.querySelectorAll(".ladi-lazyload"));
  if (!lazyNodes.length) return;

  if (!("IntersectionObserver" in window)) {
    lazyNodes.forEach(function (el) { el.classList.remove("ladi-lazyload"); });
    return;
  }

  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (!entry.isIntersecting) return;
      entry.target.classList.remove("ladi-lazyload");
      observer.unobserve(entry.target);
    });
  }, { root: null, rootMargin: "520px 0px", threshold: 0.01 });

  lazyNodes.forEach(function (el) { observer.observe(el); });
})();
</script>'''
    lazy_pattern = r"<script\b[^>]*\bid=[\"']script_lazyload[\"'][^>]*>.*?</script\s*>"
    if re.search(lazy_pattern, html, flags=re.I | re.S):
        html = sub(lazy_pattern, lazy_script, html, flags=re.I | re.S)

    # 4) Bỏ preconnect API form vì RSVP đã tắt.
    for host in (
        "api1.ldpform.com",
        "a.ladipage.com",
        "api.sales.ldpform.net",
    ):
        html = sub(
            rf"<link\b[^>]*\brel=[\"']preconnect[\"'][^>]*\bhref=[\"']https://{re.escape(host)}/?[\"'][^>]*>\s*",
            "",
            html,
            flags=re.I | re.S,
        )

    # 5) Bỏ block chống copy/devtools nếu bản export cũ vẫn còn.
    html = sub(
        r"<!--\s*PROTECT_COPY_START\s*-->.*?<!--\s*PROTECT_COPY_END\s*-->",
        "",
        html,
        flags=re.I | re.S,
    )

    # 6) Bỏ bộ nút nhạc cũ nằm sai trong <head>.
    # Bản hiện tại có marker này ngay trước style của music.
    html = sub(
        r"<!--\s*MUSIC\s*\+\s*#A46B61\s*DUSTY\s*ROSE\s*MUSIC\s*TOGGLE\s*-->.*?(?=<link\b[^>]*href=[\"']css/custom\.css)",
        "",
        html,
        flags=re.I | re.S,
    )

    # Fallback nếu marker comment đã bị xóa trước đó.
    html = sub(
        r"<button\b[^>]*\bid=[\"']music-toggle[\"'][^>]*>.*?</button>\s*",
        "",
        html,
        flags=re.I | re.S,
    )
    html = sub(
        r"<script\b[^>]*>\s*(?:const|let|var)\s+musicList\s*=.*?</script>\s*",
        "",
        html,
        flags=re.I | re.S,
    )

    # 7) Bỏ meta no-cache cũ; Vercel sẽ quản lý cache bằng header.
    html = sub(
        r"<meta\b[^>]*http-equiv=[\"'](?:Cache-Control|Expires)[\"'][^>]*>\s*",
        "",
        html,
        flags=re.I | re.S,
    )

    # 8) Xóa các script config/customize cũ để chỉ còn một bản ở cuối body.
    html = sub(
        r"<script\b[^>]*\bsrc=[\"']js/config\.js(?:\?[^\"']*)?[\"'][^>]*>\s*</script>\s*",
        "",
        html,
        flags=re.I | re.S,
    )
    html = sub(
        r"<script\b[^>]*\bsrc=[\"']js/customize\.js(?:\?[^\"']*)?[\"'][^>]*>\s*</script>\s*",
        "",
        html,
        flags=re.I | re.S,
    )

    # 9) Cập nhật custom.css. Nếu chưa có thì tự chèn.
    css_pattern = r"<link\b[^>]*\bhref=[\"']css/custom\.css(?:\?[^\"']*)?[\"'][^>]*>"
    if re.search(css_pattern, html, flags=re.I | re.S):
        html = sub(
            css_pattern,
            f'<link rel="stylesheet" href="css/custom.css?v={VERSION}">',
            html,
            flags=re.I | re.S,
        )
    else:
        html = sub(
            r"</head>",
            f'  <link rel="stylesheet" href="css/custom.css?v={VERSION}">\n</head>',
            html,
            flags=re.I,
        )

    # 10) Chèn marker + config/customize ngay trước </body>.
    injection = f"""
  <!-- Wedding Tone Hong V2.7 - independent runtime -->
  <script src="js/config.js?v={VERSION}"></script>
  <script src="js/customize.js?v={VERSION}"></script>
"""
    if "Wedding Tone Hong V2.7 - independent runtime" not in html:
        html = sub(r"</body>", injection + "</body>", html, flags=re.I)

    # 11) Dọn một ít khoảng trắng thừa do remove block.
    html = re.sub(r"\n{4,}", "\n\n\n", html)

    INDEX.write_text(html, encoding="utf-8", newline="\n")

    print("OK - Đã cập nhật index.html lên Wedding Tone Hồng V2.7")
    print("Backup:", BACKUP.name)
    print("Đã bỏ: ladipagev3.min.js, script_ladipage_run, script_event_data, music block cũ")
    print("Đã dùng: css/custom.css?v=2.7.0 + js/config.js/customize.js?v=2.7.0")


if __name__ == "__main__":
    main()
