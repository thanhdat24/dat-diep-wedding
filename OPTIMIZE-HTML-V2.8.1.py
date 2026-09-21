from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "index.html"
CSS_DIR = ROOT / "css"
JS_DIR = ROOT / "js"

if not INDEX.exists():
    print("Khong tim thay index.html.")
    print("Hay dat OPTIMIZE-HTML-V2.8.py cung thu muc voi index.html.")
    input("Nhan Enter de thoat...")
    sys.exit(1)

CSS_DIR.mkdir(exist_ok=True)
JS_DIR.mkdir(exist_ok=True)

source = INDEX.read_text(encoding="utf-8")
backup = ROOT / "index.before-v2.8.html"
if not backup.exists():
    shutil.copy2(INDEX, backup)

def remove_balanced_tag_by_id(text, tag, element_id):
    pattern = re.compile(
        rf'<{tag}\b[^>]*\bid\s*=\s*(["\']){re.escape(element_id)}\1[^>]*>',
        re.I
    )
    m = pattern.search(text)
    if not m:
        return text, set()

    token_re = re.compile(rf'<{tag}\b[^>]*>|</{tag}\s*>', re.I)
    depth = 1
    end = None
    for tm in token_re.finditer(text, m.end()):
        token = tm.group(0).lstrip().lower()
        if token.startswith(f"<{tag.lower()}") and not token.startswith(f"</{tag.lower()}"):
            depth += 1
        else:
            depth -= 1
            if depth == 0:
                end = tm.end()
                break

    if end is None:
        return text, set()

    block = text[m.start():end]
    ids = set(re.findall(r'\bid\s*=\s*["\']([^"\']+)["\']', block, re.I))
    return text[:m.start()] + text[end:], ids

def extract_style(text, style_id):
    pattern = re.compile(
        rf'<style\b[^>]*\bid\s*=\s*["\']{re.escape(style_id)}["\'][^>]*>(.*?)</style>',
        re.I | re.S
    )
    m = pattern.search(text)
    if not m:
        return text, ""
    return text[:m.start()] + text[m.end():], m.group(1).strip()

def clean_css(css, removed_ids):
    if not css.strip():
        return ""

    rule_re = re.compile(r'([^{}]+)\{([^{}]*)\}', re.S)
    out = []

    unused_prefixes = (
        ".ladi-form",
        ".ladi-checkout",
        ".ladi-popup",
        ".popup-close",
        ".ladipage-message",
        ".ladi-loading",
        ".lightbox",
        ".backdrop-",
    )

    for m in rule_re.finditer(css):
        selector = m.group(1).strip()
        body = m.group(2).strip()

        if not selector or not body:
            continue

        low = selector.lower()

        if ".ladi-animation" in selector:
            continue
        if low.startswith("@keyframes") or low.startswith("@-webkit-keyframes"):
            continue

        if low.startswith("@font-face"):
            out.append(selector + " {\n" + body + "\n}")
            continue

        selectors = [s.strip() for s in selector.split(",") if s.strip()]
        kept = []

        for s in selectors:
            if ".ladi-animation" in s:
                continue

            if any(prefix in s for prefix in unused_prefixes):
                continue

            ids = re.findall(r'#([A-Za-z0-9_-]+)', s)
            if any(i in removed_ids for i in ids):
                continue

            kept.append(s)

        if not kept:
            continue

        joined = ",\n".join(kept)

        # Anh cuoi chinh da co local override o wedding-local-images.
        # Xoa URL anh cu mau de source CSS sach hon.
        if any(x in joined for x in (
            "#IMAGE5>", "#IMAGE14>", "#IMAGE16>", "#IMAGE43>",
            "#IMAGE55>", "#GALLERY2 .ladi-gallery-view-item",
            "#GALLERY2 .ladi-gallery-control-item"
        )):
            body = re.sub(
                r'background-image\s*:\s*url\(\s*["\']https://w\.ladicdn\.com/[^;]+;',
                '',
                body,
                flags=re.I
            ).strip()
            if not body:
                continue

        out.append(joined + " {\n" + body + "\n}")

    return "\n\n".join(out)

def replace_headline(text, element_id, html_value):
    pattern = re.compile(
        rf'(<(?:div|a)\b[^>]*\bid\s*=\s*["\']{re.escape(element_id)}["\'][^>]*>.*?'
        rf'<(?:h1|h2|h3|p)\b[^>]*\bclass\s*=\s*["\'][^"\']*\bladi-headline\b[^"\']*["\'][^>]*>)'
        rf'(.*?)'
        rf'(</(?:h1|h2|h3|p)>)',
        re.I | re.S
    )
    return pattern.sub(lambda m: m.group(1) + html_value + m.group(3), text, count=1)

def normalize_classes(text):
    text = re.sub(r'\s+ladi-animation-hidden\b', '', text)
    text = re.sub(r'\bladi-animation-hidden\s+', '', text)
    text = re.sub(r'class=(["\'])\s+', r'class=\1', text)
    return text

html = source
removed_ids = set()

# 1) Bo cac khoi khong su dung.
for element_id in ("SECTION4", "SECTION_POPUP", "GROUP19", "BOX15", "IMAGE53", "IMAGE54"):
    html, ids = remove_balanced_tag_by_id(html, "div", element_id)
    removed_ids.update(ids)

for element_id in ("backdrop-popup", "backdrop-dropbox", "lightbox-screen"):
    html, ids = remove_balanced_tag_by_id(html, "div", element_id)
    removed_ids.update(ids)

# 2) Bo polyfill IE cu va comment publish.
html = re.sub(r'<!--\[if\s+lt\s+IE\s+9\]>.*?<!\[endif\]-->', '', html, flags=re.I | re.S)
html = re.sub(r'<!--Publish time:.*?-->', '', html, flags=re.I | re.S)
html = re.sub(r'<!--LadiPage build time:.*?-->', '', html, flags=re.I | re.S)

# 3) Bo class an cua runtime cu.
html = normalize_classes(html)

# 4) Lay CSS layout ra file rieng.
html, _old_ladi = extract_style(html, "style_ladi")
html, page_css = extract_style(html, "style_page")
html, element_css = extract_style(html, "style_element")
html, _old_lazy = extract_style(html, "style_lazyload")
html, local_images_css = extract_style(html, "wedding-local-images")

# Bo style keyframes cu nam gan cuoi body.
html = re.sub(
    r'<style\b[^>]*>\s*(?:@-webkit-keyframes|@keyframes)\s+fadeIn.*?</style>',
    '',
    html,
    flags=re.I | re.S
)

# 5) Bo font link/preload trung lap.
html = re.sub(r'<link\b[^>]*rel\s*=\s*["\']dns-prefetch["\'][^>]*>\s*', '', html, flags=re.I)
html = re.sub(
    r'<link\b[^>]*href\s*=\s*["\']https://fonts\.googleapis\.com/css2\?[^"\']+["\'][^>]*>\s*',
    '',
    html,
    flags=re.I
)
html = re.sub(
    r'<link\b[^>]*rel\s*=\s*["\']preload["\'][^>]*fonts\.googleapis\.com[^>]*>\s*',
    '',
    html,
    flags=re.I
)
html = re.sub(
    r'<link\b[^>]*href\s*=\s*["\']https://s\.ladicdn\.com/["\'][^>]*>\s*',
    '',
    html,
    flags=re.I
)

# 6) Bo script config/customize o cuoi body; se chen lai bang defer trong head.
html = re.sub(r'<script\b[^>]*src\s*=\s*["\']js/config\.js[^"\']*["\'][^>]*>\s*</script>\s*', '', html, flags=re.I)
html = re.sub(r'<script\b[^>]*src\s*=\s*["\']js/customize\.js[^"\']*["\'][^>]*>\s*</script>\s*', '', html, flags=re.I)

# 7) Gallery V2.7 tu tao slide tu config.
html = re.sub(
    r'<div\s+class=["\']ladi-gallery-view-item[^"\']*["\'][^>]*data-index=["\']\d+["\'][^>]*>\s*</div>\s*',
    '',
    html,
    flags=re.I
)
html = re.sub(
    r'<div\s+class=["\']ladi-gallery-control-item[^"\']*["\'][^>]*data-index=["\']\d+["\'][^>]*>\s*</div>\s*',
    '',
    html,
    flags=re.I
)

# 8) Xoa fallback tieng Anh/cu; customize.js se nap tu config.js.
fallbacks = {
    "HEADLINE8": "Chuyện tình",
    "HEADLINE9": "",
    "HEADLINE12": "",
    "HEADLINE80": "",
    "HEADLINE13": "",
    "HEADLINE95": "Chỉ đường",
    "HEADLINE16": "Tháng",
    "HEADLINE107": "Album",
    "HEADLINE108": "Ảnh cưới",
    "HEADLINE86": "",
    "HEADLINE87": "Thân mến,<br>",
    "HEADLINE100": "Thank You!<br>",
    "HEADLINE90": "Cảm ơn bạn!",
}
for element_id, value in fallbacks.items():
    html = replace_headline(html, element_id, value)

# Map URL cu khong duoc giu lam fallback.
html = re.sub(
    r'(<a\b[^>]*\bid\s*=\s*["\']GROUP33["\'][^>]*\bhref\s*=\s*)["\'][^"\']*["\']',
    r'\1"#"',
    html,
    count=1,
    flags=re.I
)

# 9) Base CSS gon.
LEAN_BASE = r'''
*,*::before,*::after{box-sizing:border-box}
html,body,div,span,h1,h2,h3,p,a,section{margin:0;padding:0;border:0}
html{-webkit-text-size-adjust:100%;text-size-adjust:100%}
body{line-height:1;background:#fff;font-family:"Open Sans",sans-serif;overflow-x:hidden}
a{text-decoration:none;color:inherit}
*{-webkit-tap-highlight-color:transparent}
.ladi-wraper{width:420px;min-height:100%;overflow:hidden;touch-action:manipulation}
.ladi-container{position:relative;margin:0 auto;height:100%}
.ladi-element{position:absolute}
.ladi-section{position:relative;margin:0 auto}
.ladi-section-background{position:absolute;inset:0;width:100%;height:100%;pointer-events:none;overflow:hidden}
.ladi-group,.ladi-image,.ladi-box,.ladi-shape{position:absolute;width:100%;height:100%}
.ladi-image,.ladi-box{overflow:hidden}
.ladi-image-background{position:absolute;width:100%;height:100%;margin:0 auto;background-repeat:no-repeat;background-position:left top;background-size:cover;background-attachment:scroll;background-origin:content-box;pointer-events:none}
.ladi-headline,.ladi-paragraph{display:inline-block;width:100%;word-break:break-word}
.ladi-line{position:relative}
.ladi-line-container{width:100%;height:100%;border-right:0!important;border-bottom:0!important}
.ladi-transition{transition:all 150ms linear}
.opacity-0{opacity:0}
.ladi-lazyload{background-image:none!important}
.ladi-gallery{position:absolute;width:100%;height:100%;overflow:hidden}
.ladi-gallery-view{position:absolute;overflow:hidden}
.ladi-gallery-view-item{position:relative;display:none;width:100%;height:100%;background-size:cover;background-repeat:no-repeat;background-position:center;backface-visibility:hidden}
.ladi-gallery-view-item.selected{display:block}
.ladi-gallery-control{position:absolute;overflow:hidden}
.ladi-gallery-control-box{position:relative;display:inline-flex;left:0}
.ladi-gallery-control-item{position:relative;flex:0 0 auto;background-size:cover;background-repeat:no-repeat;background-position:center;cursor:pointer}
.ladi-gallery-view-arrow{position:absolute;top:calc(50% - 16.5px);z-index:40;width:33px;height:33px;cursor:pointer;background-repeat:no-repeat;background-position:center;background-image:url("data:image/svg+xml;utf8,%3Csvg%20width%3D%2224%22%20height%3D%2224%22%20viewBox%3D%220%200%2024%2024%22%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20fill%3D%22%23fff%22%3E%3Cpath%20d%3D%22M7%20.586L18.414%2012%207%2023.414%205.586%2022%2015.586%2012%205.586%202z%22/%3E%3C/svg%3E")}
.ladi-gallery-view-arrow-left{left:5px;transform:rotateY(180deg)}
.ladi-gallery-view-arrow-right{right:5px}
.ladi-gallery-bottom .ladi-gallery-view{top:0;width:100%}
.ladi-gallery-bottom .ladi-gallery-control{width:100%;bottom:0}
.ladi-shape{pointer-events:none}
svg{display:block}
'''

page_css = clean_css(page_css, removed_ids)
element_css = clean_css(element_css, removed_ids)
local_images_css = clean_css(local_images_css, removed_ids)

base_css = (
    "/* Wedding Tone Hong V2.8.1 - lean base extracted from index.html */\n"
    + LEAN_BASE.strip()
    + "\n\n/* Original page fonts/base */\n" + page_css
    + "\n\n/* Original 420px layout - unused sections removed */\n" + element_css
    + "\n\n/* Local wedding images */\n" + local_images_css
    + "\n"
)

# IMPORTANT:
# CSS nam trong /css/, nen url("assets/...") phai thanh url("../assets/...").
base_css = re.sub(
    r'url\(\s*(["\']?)assets/',
    r'url(\1../assets/',
    base_css,
    flags=re.I
)

(CSS_DIR / "base-v2.8.css").write_text(base_css, encoding="utf-8")

# 10) Responsive CSS.
responsive_css = r'''/* Wedding Tone Hong V2.8 - responsive shell */
html,body{
  width:100%;
  min-width:0;
  margin:0!important;
  padding:0!important;
  overflow-x:hidden!important;
}
body{
  min-height:100vh;
  background:#fff;
}
#wedding-responsive-shell{
  position:relative;
  width:100%;
  overflow:hidden;
}
.ladi-wraper{
  width:420px!important;
  max-width:none!important;
  margin:0!important;
  transform-origin:top left!important;
  backface-visibility:hidden;
  -webkit-backface-visibility:hidden;
}
@media (prefers-reduced-motion:reduce){
  *,*::before,*::after{
    animation-duration:.001ms!important;
    animation-iteration-count:1!important;
    transition-duration:.001ms!important;
    scroll-behavior:auto!important;
  }
}
'''
(CSS_DIR / "responsive-v2.8.css").write_text(responsive_css, encoding="utf-8")

# 11) Responsive JS.
responsive_js = r'''(function(){
  "use strict";

  var DESIGN_WIDTH=420;
  var wrapper=null;
  var shell=null;
  var ro=null;
  var raf=0;

  function ensureShell(){
    wrapper=document.querySelector(".ladi-wraper");
    if(!wrapper)return false;

    if(wrapper.parentElement&&wrapper.parentElement.id==="wedding-responsive-shell"){
      shell=wrapper.parentElement;
      return true;
    }

    shell=document.createElement("div");
    shell.id="wedding-responsive-shell";
    wrapper.parentNode.insertBefore(shell,wrapper);
    shell.appendChild(wrapper);
    return true;
  }

  function fit(){
    if(!wrapper||!shell)return;

    var vw=document.documentElement.clientWidth||window.innerWidth||DESIGN_WIDTH;
    var scale=Math.min(1,vw/DESIGN_WIDTH);
    var rendered=DESIGN_WIDTH*scale;
    var left=Math.max(0,(vw-rendered)/2);

    wrapper.style.position="absolute";
    wrapper.style.top="0";
    wrapper.style.left=left+"px";
    wrapper.style.width=DESIGN_WIDTH+"px";
    wrapper.style.transformOrigin="top left";
    wrapper.style.transform="scale("+scale+")";

    var h=wrapper.scrollHeight||wrapper.offsetHeight||0;
    shell.style.height=Math.ceil(h*scale)+"px";
  }

  function requestFit(){
    cancelAnimationFrame(raf);
    raf=requestAnimationFrame(fit);
  }

  function start(){
    if(!ensureShell())return;
    fit();

    if("ResizeObserver" in window){
      ro=new ResizeObserver(requestFit);
      ro.observe(wrapper);
    }

    window.addEventListener("resize",requestFit,{passive:true});
    window.addEventListener("orientationchange",function(){
      setTimeout(requestFit,120);
    },{passive:true});

    setTimeout(requestFit,250);
    setTimeout(requestFit,900);
  }

  if(document.readyState==="loading"){
    document.addEventListener("DOMContentLoaded",start,{once:true});
  }else{
    start();
  }
})();'''
(JS_DIR / "responsive-v2.8.js").write_text(responsive_js, encoding="utf-8")

# 12) Lazyload gon.
lazy_style = '''<style id="style_lazyload">
body.lazyload .ladi-image-background,
body.lazyload .ladi-gallery-view-item,
body.lazyload .ladi-gallery-control-item{background-image:none!important}
</style>'''

lazy_script = r'''<script id="script_lazyload">
(function(){
  var body=document.body;
  var style=document.getElementById("style_lazyload");
  if(!body)return;

  var nodes=[].slice.call(document.querySelectorAll(
    ".ladi-image-background,.ladi-gallery-view-item,.ladi-gallery-control-item"
  ));
  var h=window.innerHeight||document.documentElement.clientHeight||800;
  var margin=520;

  nodes.forEach(function(el){
    var r=el.getBoundingClientRect();
    if(r.top>h+margin||r.bottom<-margin)el.classList.add("ladi-lazyload");
  });

  if(style)style.remove();
  body.classList.remove("lazyload");

  var lazy=[].slice.call(document.querySelectorAll(".ladi-lazyload"));
  if(!lazy.length)return;

  if(!("IntersectionObserver" in window)){
    lazy.forEach(function(el){el.classList.remove("ladi-lazyload")});
    return;
  }

  var io=new IntersectionObserver(function(entries){
    entries.forEach(function(entry){
      if(!entry.isIntersecting)return;
      entry.target.classList.remove("ladi-lazyload");
      io.unobserve(entry.target);
    });
  },{rootMargin:"520px 0px",threshold:.01});

  lazy.forEach(function(el){io.observe(el)});
})();
</script>'''

html = re.sub(
    r'<script\b[^>]*\bid\s*=\s*["\']script_lazyload["\'][^>]*>.*?</script>',
    lazy_script,
    html,
    flags=re.I | re.S
)

# 13) Chuan hoa head.
html = re.sub(
    r'<link\b[^>]*href\s*=\s*["\']css/custom\.css[^"\']*["\'][^>]*>\s*',
    '',
    html,
    flags=re.I
)

head_inject = r'''
  <!-- Wedding Tone Hong V2.8 optimized assets -->
  <link rel="preconnect" href="https://fonts.googleapis.com" crossorigin>
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="preconnect" href="https://w.ladicdn.com" crossorigin>

  <link rel="preload" as="image" href="assets/images/cover.jpg" fetchpriority="high">

  <link
    rel="stylesheet"
    href="https://fonts.googleapis.com/css2?family=Alex+Brush&family=Dancing+Script:wght@500;600&family=Hepta+Slab:wght@400;700&family=Open+Sans:wght@400;700&family=Roboto+Slab:wght@400;700&display=swap"
  >

  <link rel="stylesheet" href="css/base-v2.8.css?v=2.8.0">
  <link rel="stylesheet" href="css/custom.css?v=2.8.0">
  <link rel="stylesheet" href="css/responsive-v2.8.css?v=2.8.0">

  ''' + lazy_style + r'''

  <script src="js/config.js?v=2.8.0" defer></script>
  <script src="js/customize.js?v=2.8.0" defer></script>
  <script src="js/responsive-v2.8.js?v=2.8.0" defer></script>
'''

html = html.replace("</head>", head_inject + "\n</head>", 1)

# Gop font Google vao head, bo @import neu custom.css co.
custom_path = CSS_DIR / "custom.css"
if custom_path.exists():
    custom = custom_path.read_text(encoding="utf-8")
    custom = re.sub(
        r'^\s*@import\s+url\(["\']?https://fonts\.googleapis\.com/[^;]+;\s*',
        '',
        custom,
        count=1,
        flags=re.I
    )
    # custom.css cung nam trong /css/, sua duong dan asset neu co.
    custom = re.sub(
        r'url\(\s*(["\']?)assets/',
        r'url(\1../assets/',
        custom,
        flags=re.I
    )
    custom_path.write_text(custom, encoding="utf-8")

html = re.sub(r'\n[ \t]+\n', '\n\n', html)
html = re.sub(r'\n{3,}', '\n\n', html)
html = html.strip() + "\n"

INDEX.write_text(html, encoding="utf-8")

print("")
print("==============================================")
print("  WEDDING HTML OPTIMIZER V2.8.1 - HOAN TAT")
print("==============================================")
print("Backup :", backup.name)
print("HTML   :", INDEX.name)
print("CSS    : css/base-v2.8.css")
print("CSS    : css/responsive-v2.8.css")
print("JS     : js/responsive-v2.8.js")
print("")
print("Da bo:")
print("- Timeline / Dresscode SECTION4")
print("- RSVP form va popup cu")
print("- lightbox/backdrop khong dung")
print("- CSS form/checkout/popup/lightbox thua")
print("- animation runtime LadiPage cu")
print("- 10 slide gallery hard-code trong HTML")
print("- fallback tieng Anh cu")
print("")
print("Canvas 420px duoc giu nguyen; mobile <420px se scale vua man hinh.")
input("Nhan Enter de dong...")
