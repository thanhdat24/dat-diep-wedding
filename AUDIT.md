# Audit V2.7

## Đã xử lý

- LadiPage runtime chính: loại bỏ bằng patch.
- Vòng chờ `window.LadiPageScript`: loại bỏ.
- Album `IMAGE55` / tiêu đề Album: force-visible bằng CSS/JS.
- Ảnh ngang phía sau Album `IMAGE54`: ẩn.
- Lá trang trí Album `IMAGE53`: ẩn.
- Gallery: JS độc lập, swipe/click/arrows/thumbnail.
- Gallery: không kiểm tra/preload toàn bộ ảnh ngay lúc mở trang.
- Gallery: thumbnail chỉ tải khi gần vùng nhìn thấy.
- Gallery: preload kế tiếp chỉ khi mạng không bật Save-Data và không phải 2G/3G.
- Lazy background LadiPage: thay first-scroll mass-load bằng IntersectionObserver.
- Timeline + Dresscode: ẩn hoàn toàn.
- RSVP + popup: ẩn hoàn toàn.
- Nhạc: `preload=none`, một listener pointer đầu tiên thay vì scroll/mousemove/touchmove liên tục.
- Nút nhạc: bỏ animation vô hạn để giảm GPU/CPU trên mobile.
- Safe-area iPhone: áp dụng cho nút nhạc.
- `prefers-reduced-motion`: hỗ trợ.
- CSS/JS Vercel cache: cấu hình.

## Chưa thể tối ưu tự động

- File ảnh thật trong `assets/images/` chưa được cung cấp trong ZIP gốc, nên chưa thể nén/chuyển WebP theo dung lượng thực tế.
- File MP3 hiện không nằm trong ZIP; `config.js` vẫn dùng URL Catbox. Dùng MP3 local sẽ ổn định hơn.
