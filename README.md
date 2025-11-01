🚦 HỆ THỐNG ĐIỀU KHIỂN ĐÈN GIAO THÔNG NGÃ TƯ (ESP32 & PYTHON GUI)

💡 Giới Thiệu

Đây là dự án mô phỏng hệ thống điều khiển đèn giao thông tại một ngã tư hai chiều, được xây dựng trên nền tảng ESP32. Hệ thống sử dụng Shift Register 74HC595 để điều khiển màn hình LED 7 đoạn hiển thị thời gian đếm ngược và có khả năng kích hoạt các chế độ khẩn cấp (Emergency Mode) tức thời thông qua các nút bấm vật lý hoặc giao diện người dùng Python GUI (sử dụng thư viện tkinter và pyserial).

Dự án này rất phù hợp cho việc học tập về điều khiển ngoại vi, giao tiếp Serial giữa MCU và máy tính, cũng như lập trình ứng dụng giao diện người dùng (GUI).

✨ Tính Năng Chính

Chu kỳ Hoạt động Bình thường: Đèn giao thông hoạt động theo chu kỳ luân phiên giữa hai mạch (Hướng A và Hướng B), bao gồm pha Xanh, Vàng chuyển tiếp (2 giây cố định), và Đỏ.

Hiển thị Đếm ngược: Sử dụng hai Shift Register 74HC595 và LED 7 đoạn để hiển thị thời gian đếm ngược (00-99 giây) cho pha đèn hiện tại.

Chế độ Khẩn cấp (Emergency Mode):

Khẩn cấp Mạch 1: Ưu tiên bật Xanh cho Mạch 1 (Đỏ cho Mạch 2).

Khẩn cấp Mạch 2: Ưu tiên bật Xanh cho Mạch 2 (Đỏ cho Mạch 1).

An toàn (Cả hai Đỏ): Bật Đỏ cho cả hai mạch.

Chuyển tiếp An toàn: Khi kích hoạt chế độ khẩn cấp từ pha Xanh, hệ thống sẽ tự động chuyển qua pha Vàng 2 giây trước khi vào chế độ khẩn cấp, đảm bảo an toàn giao thông.

Điều khiển từ xa qua Python GUI:

Giao diện người dùng trực quan hiển thị trạng thái đèn theo thời gian thực.

Có thể gửi lệnh kích hoạt/tắt chế độ khẩn cấp.

Cho phép người dùng điều chỉnh thời gian pha Xanh/Đỏ của chu kỳ bình thường.

📂 Cấu Trúc Dự Án

File

Mô tả

traffic_controller.ino

Mã nguồn Arduino (ESP32) điều khiển logic đèn giao thông, Shift Register và xử lý ngắt khẩn cấp.

gui_controller.py

Mã nguồn Python GUI (Tkinter) để giao tiếp Serial, hiển thị trạng thái trực quan và gửi lệnh điều khiển.

🛠️ Yêu Cầu

Phần Cứng (Hardware)

ESP32 (hoặc ESP8266/Arduino tương đương)

2 x Shift Register 74HC595

2 x Màn hình LED 7 đoạn đôi (Common Cathode)

6 x LED giao thông (2 Xanh, 2 Vàng, 2 Đỏ)

3 x Nút nhấn (dùng cho ngắt khẩn cấp)

Các điện trở phụ trợ.

Phần Mềm (Software)

Arduino IDE: Cần cài đặt Board Support Package cho ESP32.

Python 3.x: Cần cài đặt các thư viện sau:

pip install pyserial


⚙️ Hướng Dẫn Cài Đặt và Sử Dụng

1. Nạp Mã (Code Upload - ESP32)

Mở tệp traffic_controller.ino trong Arduino IDE.

Chọn bo mạch ESP32 Dev Module và cổng COM phù hợp.

Kiểm tra và nạp mã vào ESP32.

2. Kết Nối Mạch (Wiring)

A. Cấu hình Shift Register (Mạch 1 & 2):

Chân ESP32

Chức năng

Chân 74HC595

19 (latchPin1)

ST_CP (Chốt dữ liệu Mạch 1)

RCLK (Chân 12)

18 (clockPin1)

SH_CP (Clock Mạch 1)

SRCLK (Chân 11)

23 (dataPin1)

DS (Dữ liệu Serial Mạch 1)

SER (Chân 14)

22 (latchPin2)

ST_CP (Chốt dữ liệu Mạch 2)

RCLK (Chân 12)

21 (clockPin2)

SH_CP (Clock Mạch 2)

SRCLK (Chân 11)

13 (dataPin2)

DS (Dữ liệu Serial Mạch 2)

SER (Chân 14)

B. Đèn Giao thông (LEDs):

Chân ESP32

Mạch & Màu Sắc

15 (m1Green)

Mạch 1 - Xanh

2 (m1Yellow)

Mạch 1 - Vàng

4 (m1Red)

Mạch 1 - Đỏ

17 (m2Green)

Mạch 2 - Xanh

5 (m2Yellow)

Mạch 2 - Vàng

16 (m2Red)

Mạch 2 - Đỏ

C. Nút Khẩn cấp (Inputs):

Chân ESP32

Chức năng

Chế độ Khẩn cấp

35 (emergencyButton1)

Nút 1

Mạch 1 Xanh

34 (emergencyButton2)

Nút 2

Mạch 2 Xanh

32 (emergencyButton3)

Nút 3

Cả hai Đỏ (An toàn)

3. Khởi Chạy Giao Diện Điều Khiển (Python GUI)

Mở tệp gui_controller.py.

Quan trọng: Cần chỉnh sửa biến port trong hàm if __name__ == "__main__": của file Python để khớp với cổng COM của ESP32 của bạn.

if __name__ == "__main__":
    root = tk.Tk()
    # Thay 'COM5' bằng cổng COM của ESP32 của bạn
    app = TrafficApp(root, port="COM5", baudrate=115200) 
    # ...


Chạy tệp Python:

python gui_controller.py


🕹️ Cách Vận Hành

Chế độ Bình Thường

Hệ thống tự động chạy luân phiên giữa hai mạch (Mạch 1 Đỏ, Mạch 2 Xanh/Vàng -> Mạch 1 Xanh/Vàng, Mạch 2 Đỏ). Thời gian đếm ngược hiển thị trên màn hình LED 7 đoạn và GUI Python.

Chế độ Khẩn Cấp (Emergency Mode)

Chế độ khẩn cấp có thể được kích hoạt bằng Nút nhấn vật lý hoặc nút bấm trên GUI:

Nút/Lệnh

Chức năng

Hành vi

🚨 KHẨN CẤP MẠCH 1 (E1)

Ưu tiên Mạch 1 Xanh

Nếu Mạch 2 đang Xanh, sẽ chuyển Vàng 2s trước khi Mạch 1 Xanh vĩnh viễn (cho đến khi nhấn RESET).

🚨 KHẨN CẤP MẠCH 2 (E2)

Ưu tiên Mạch 2 Xanh

Nếu Mạch 1 đang Xanh, sẽ chuyển Vàng 2s trước khi Mạch 2 Xanh vĩnh viễn (cho đến khi nhấn RESET).

🔒 AN TOÀN CẢ HAI ĐỎ (E3)

Bật Đỏ cả hai mạch

Nếu bất kỳ mạch nào đang Xanh/Vàng, sẽ chuyển Vàng 2s trước khi cả hai chuyển Đỏ.

🔄 RESET BÌNH THƯỜNG (NORMAL)

Tắt khẩn cấp

Đưa hệ thống về chu kỳ hoạt động bình thường ngay lập tức.

Điều chỉnh Thời gian Pha

Sử dụng phần "⏱️ ĐẶT THỜI GIAN PHA" trên Python GUI để thay đổi thời lượng cho pha Xanh hoặc pha Đỏ đối diện:

Xanh (GREEN): Đặt thời gian cho pha Xanh chủ động (đèn Xanh của một mạch). Pha Đỏ đối diện sẽ bằng (Thời gian Xanh + 2s Vàng).

Đỏ (RED): Đặt thời gian cho pha Đỏ đối diện (thời gian tối đa mà một mạch phải chờ đèn Đỏ). Thời gian Xanh chủ động sẽ được tính ngược lại là (Thời gian Đỏ - 2s Vàng).

Nhấn ĐẶT THỜI GIAN để gửi lệnh. Hệ thống ESP32 sẽ xác nhận và khởi động lại chu kỳ với thời gian mới.
