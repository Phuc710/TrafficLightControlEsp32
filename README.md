🚦 HỆ THỐNG ĐIỀU KHIỂN ĐÈN GIAO THÔNG NGÃ TƯ
(ESP32 & Python GUI)
💡 Giới thiệu

Dự án mô phỏng hệ thống đèn giao thông hai chiều sử dụng ESP32 và Python GUI (Tkinter + PySerial).
Hệ thống điều khiển LED 7 đoạn qua Shift Register 74HC595, hiển thị thời gian đếm ngược và hỗ trợ kích hoạt chế độ khẩn cấp (Emergency Mode) bằng nút vật lý hoặc giao diện máy tính.

🎯 Ứng dụng: Học tập về giao tiếp Serial, điều khiển ngoại vi, và lập trình GUI cơ bản.

✨ Tính năng chính

Chu kỳ hoạt động bình thường:
Đèn luân phiên giữa hai hướng (A & B) với các pha Xanh → Vàng (2s) → Đỏ.

Hiển thị đếm ngược:
LED 7 đoạn (2x74HC595) hiển thị thời gian còn lại (00–99s).

Chế độ khẩn cấp (Emergency Mode):

🔒: Cả hai Đỏ (An toàn).

🔄 RESET: Trở lại chế độ bình thường.

Tự động chuyển qua Vàng 2s trước khi vào trạng thái khẩn cấp để đảm bảo an toàn.

Điều khiển từ GUI:

Hiển thị trạng thái đèn theo thời gian thực.

Cho phép gửi lệnh Emergency / Reset / Điều chỉnh thời gian pha.


🛠️ Yêu cầu
🔧 Phần cứng

ESP32 (hoặc tương đương)

2x 74HC595

2x LED 7 đoạn đôi (Common Cathode)

6x LED giao thông (2 Xanh, 2 Vàng, 2 Đỏ)

3x Nút nhấn (Emergency)

Điện trở phụ trợ

💻 Phần mềm

Arduino IDE (ESP32 board package)

Python 3.x với thư viện:
