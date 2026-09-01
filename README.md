# Wedding Tone Hồng V2.7 — Final Mobile / Vercel

Bản này được tối ưu để **không còn phụ thuộc `ladipagev3.min.js`** nhưng vẫn giữ layout LadiPage gốc 420px, phần Album, gallery, nút chỉ đường, nội dung từ `config.js` và nhạc nền.

## Cách áp dụng an toàn

1. Giải nén/copy **nội dung** gói V2.7 vào đúng folder website hiện tại.
2. Gói update **không ghi đè `js/config.js`** của bạn; dữ liệu ảnh/gallery đang chỉnh được giữ nguyên. `config.example.js` chỉ là mẫu dự phòng.
3. Đảm bảo `index.html` nằm cùng cấp với `PATCH-INDEX.py`.
4. Nhấp đúp `APPLY-V2.7.bat`.
5. Script tự tạo backup `index.before-v2.7.html`, sau đó chỉnh `index.html`.
6. Chạy `RUN-WEDDING.bat`, mở `http://localhost:8080`, rồi Ctrl + F5.

## Những gì PATCH-INDEX.py tự chỉnh

- Bỏ preload `ladipagev3.min.js`.
- Bỏ `<script src="...ladipagev3.min.js">`.
- Bỏ `script_event_data` và `script_ladipage_run` để không còn vòng `setTimeout` chờ LadiPage.
- Bỏ `style_animation` gây `opacity:0!important`.
- Thay lazy-load kiểu "scroll lần đầu tải hết" bằng `IntersectionObserver`.
- Bỏ preconnect API form không dùng vì RSVP đã tắt.
- Bỏ block chống copy/devtools cũ nếu còn.
- Bỏ bộ nhạc cũ nằm trong `<head>`.
- Đặt `config.js` + `customize.js` V2.7 ở cuối `<body>`.

## Gallery

`customize.js` V2.7 tự quản lý gallery, không cần LadiPage runtime.

Nếu `images.gallery` trong `config.js` để `[]`, script sẽ dùng các ảnh gallery đang có trong `index.html`.

Nếu muốn dùng ảnh local:

```js
gallery: [
  "assets/images/gallery-1.webp",
  "assets/images/gallery-2.webp",
  "assets/images/gallery-3.webp"
],
```

Có bao nhiêu ảnh thì gallery có bấy nhiêu slide. Ảnh lỗi/404 sẽ tự bị bỏ qua khi được tải, không giữ slide trắng.

## Nhạc

Nút nhạc được tạo bằng `customize.js`, không còn đặt button/script trong `<head>`. Audio dùng `preload="none"` và chỉ phát theo thao tác của người dùng.

Nếu `config.js` của bạn đã có `music`, V2.7 dùng đúng cấu hình đó. Nếu chưa có, `customize.js` tự dùng track Catbox cũ làm mặc định để nút nhạc vẫn hoạt động. Mẫu cấu hình nằm trong `js/config.example.js`.

Để ổn định nhất khi lên Vercel, nên chép MP3 vào:

```text
assets/audio/wedding.mp3
```

rồi đổi:

```js
track: "assets/audio/wedding.mp3",
```

## Vercel

Sau khi test local xong, có thể upload nguyên folder website lên Vercel. `vercel.json` đã cấu hình cache cho CSS/JS/assets và revalidate `index.html`.

Sau lần deploy đầu tiên, sửa trong `js/config.js`:

```js
site: {
  url: "https://TEN-DU-AN.vercel.app"
}
```

để canonical / og:url dùng URL thật.
