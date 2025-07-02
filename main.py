import tkinter as tk
from tkinter import messagebox
import serial
import threading
import time
from datetime import datetime
import sys
import os

# Cấu hình mã hóa console để hiển thị tiếng Việt đúng cách
os.environ["PYTHONIOENCODING"] = "utf-8"
sys.stdout.reconfigure(encoding='utf-8')

class TrafficLight(tk.Frame):
    """
    Lớp TrafficLight tạo một widget tùy chỉnh để hiển thị trạng thái của một đèn giao thông.
    Bao gồm các đèn (đỏ, vàng, xanh) và nhãn hiển thị trạng thái, thời gian đếm ngược.
    """
    def __init__(self, parent, title, **kwargs):
        super().__init__(parent, **kwargs)
        self.title = title

        # Nhãn tiêu đề cho đèn giao thông cụ thể
        title_label = tk.Label(self, text=title, font=("Arial", 14, "bold"),
                               fg="white", bg="#334155")
        title_label.pack(pady=5)

        # Khung chứa các đèn (vòng tròn)
        light_frame = tk.Frame(self, bg="#2c2c2c", relief="raised", bd=3)
        light_frame.pack(pady=10)

        # Canvas cho đèn đỏ
        self.red_light = tk.Canvas(light_frame, width=60, height=60, bg="#2c2c2c", highlightthickness=0)
        self.red_light.pack(pady=5)
        self.red_circle = self.red_light.create_oval(10, 10, 50, 50, fill="#4a0000", outline="#666")

        # Canvas cho đèn vàng
        self.yellow_light = tk.Canvas(light_frame, width=60, height=60, bg="#2c2c2c", highlightthickness=0)
        self.yellow_light.pack(pady=5)
        self.yellow_circle = self.yellow_light.create_oval(10, 10, 50, 50, fill="#4a4a00", outline="#666")

        # Canvas cho đèn xanh
        self.green_light = tk.Canvas(light_frame, width=60, height=60, bg="#2c2c2c", highlightthickness=0)
        self.green_light.pack(pady=5)
        self.green_circle = self.green_light.create_oval(10, 10, 50, 50, fill="#004a00", outline="#666")

        # Nhãn hiển thị trạng thái của đèn (ví dụ: ĐÈN ĐỎ, ĐÈN XANH)
        self.status_label = tk.Label(self, text="Chưa có dữ liệu",
                                     font=("Arial", 12, "bold"), fg="white", bg="#334155")
        self.status_label.pack(pady=10)

        # Nhãn hiển thị thời gian đếm ngược
        self.time_label = tk.Label(self, text="--:--",
                                   font=("Courier", 20, "bold"), fg="#00ff00", bg="#000000",
                                   relief="sunken", bd=2)
        self.time_label.pack(pady=5, padx=10, fill="x")

    def update_light(self, color, time_remaining):
        """
        Cập nhật trạng thái màu sắc của đèn và thời gian đếm ngược.

        Args:
            color (str): Màu của đèn hiện tại ("RED", "YELLOW", "GREEN", hoặc "NONE" cho lỗi).
            time_remaining (int): Thời gian còn lại của pha đèn (tính bằng giây).
        """
        # Đặt lại tất cả đèn về màu tối (tắt)
        self.red_light.itemconfig(self.red_circle, fill="#4a0000")
        self.yellow_light.itemconfig(self.yellow_circle, fill="#4a4a00")
        self.green_light.itemconfig(self.green_circle, fill="#004a00")

        # Cập nhật màu đèn và nhãn trạng thái dựa trên màu sắc được truyền vào
        if color == "RED":
            self.red_light.itemconfig(self.red_circle, fill="#ff0000") # Bật đèn đỏ
            self.status_label.config(text="🔴 ĐÈN ĐỎ", fg="#ff4444")
            self.time_label.config(fg="#ff4444")
        elif color == "YELLOW":
            self.yellow_light.itemconfig(self.yellow_circle, fill="#ffff00") # Bật đèn vàng
            self.status_label.config(text="🟡 ĐÈN VÀNG", fg="#ffaa00")
            self.time_label.config(fg="#ffaa00")
        elif color == "GREEN":
            self.green_light.itemconfig(self.green_circle, fill="#00ff00") # Bật đèn xanh
            self.status_label.config(text="🟢 ĐÈN XANH", fg="#44ff44")
            self.time_label.config(fg="#44ff44")
        else: # Trạng thái không xác định hoặc lỗi
            self.status_label.config(text="⚠️ LỖI DỮ LIỆU", fg="#ef4444")
            self.time_label.config(fg="#ef4444")

        # Cập nhật nhãn thời gian đếm ngược
        if time_remaining >= 0:
            minutes = time_remaining // 60
            seconds = time_remaining % 60
            self.time_label.config(text=f"{minutes:02d}:{seconds:02d}")
        else:
            self.time_label.config(text="00:00")

class TrafficApp:
    """
    Lớp TrafficApp quản lý toàn bộ ứng dụng GUI đèn giao thông.
    Bao gồm kết nối Serial, xử lý dữ liệu, điều khiển GUI và quản lý các chế độ khẩn cấp.
    """
    def __init__(self, root, port='COM5', baudrate=115200):
        self.root = root
        self.root.title("🚦 Hệ thống điều khiển đèn giao thông ESP32")
        self.root.geometry("1000x700")
        self.root.configure(bg="#1e293b") # Màu nền chính của ứng dụng

        self.port = port
        self.baudrate = baudrate
        self.ser = None # Đối tượng Serial connection
        self.emergency_mode = 0 # Trạng thái chế độ khẩn cấp (0: bình thường, 1: E1, 2: E2, 3: E3)
        
        self.build_ui() # Xây dựng giao diện người dùng
        self.connect_serial() # Kết nối với cổng Serial
        self.update_clock() # Bắt đầu cập nhật đồng hồ thời gian thực

        self.serial_data_queue = [] # Hàng đợi để lưu trữ dữ liệu Serial đọc được
        # Khởi tạo luồng để đọc dữ liệu Serial liên tục
        self.read_serial_thread = threading.Thread(target=self.read_serial, daemon=True)
        self.read_serial_thread.start()
        # Bắt đầu xử lý hàng đợi dữ liệu Serial trên luồng chính của Tkinter
        self.process_serial_queue()

    def connect_serial(self):
        """
        Thiết lập kết nối với cổng Serial được chỉ định.
        Cập nhật nhãn trạng thái và bật/tắt các nút điều khiển.
        """
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2) # Đợi một chút để kết nối Serial ổn định
            self.log_message(f"Kết nối Serial thành công tại {self.port}")
            self.status_label.config(text="✅ Trạng thái: KẾT NỐI THÀNH CÔNG", fg="#22c55e")
            # Kích hoạt các nút điều khiển sau khi kết nối thành công
            for widget in self.control_frame.winfo_children():
                for btn in widget.winfo_children():
                    btn.config(state="normal")
            self.enable_time_setting_controls(True) # Kích hoạt các điều khiển đặt thời gian
        except serial.SerialException:
            messagebox.showerror("Lỗi", f"Không thể kết nối Serial tại {self.port}")
            self.log_message(f"Không thể kết nối Serial tại {self.port}")
            self.status_label.config(text="⚠️ Trạng thái: KHÔNG KẾT NỐI", fg="#ef4444")
            self.ser = None # Đặt lại ser về None nếu kết nối thất bại
            # Vô hiệu hóa các nút điều khiển nếu kết nối thất bại
            for widget in self.control_frame.winfo_children():
                for btn in widget.winfo_children():
                    btn.config(state="disabled")
            self.enable_time_setting_controls(False) # Vô hiệu hóa các điều khiển đặt thời gian

    def send_command(self, cmd):
        """
        Gửi một lệnh tới ESP32 qua kết nối Serial.

        Args:
            cmd (str): Chuỗi lệnh cần gửi.
        """
        if self.ser and self.ser.is_open:
            self.ser.write((cmd + "\n").encode()) # Mã hóa lệnh thành bytes và gửi
            self.ser.flush() # Đảm bảo dữ liệu được gửi đi ngay lập tức
            self.log_message(f"Gửi lệnh: {cmd}")
        else:
            self.log_message(f"Lỗi: Không có kết nối Serial để gửi lệnh '{cmd}'")

    def build_ui(self):
        """
        Xây dựng toàn bộ giao diện người dùng của ứng dụng.
        """
        # Khung tiêu đề chính
        header_frame = tk.Frame(self.root, bg="#1e293b")
        header_frame.pack(fill="x", pady=10)

        # Tiêu đề ứng dụng
        title = tk.Label(header_frame, text="🚦 HỆ THỐNG ĐIỀU KHIỂN ĐÈN GIAO THÔNG",
                         bg="#1e293b", fg="white", font=("Arial", 20, "bold"))
        title.pack()

        # Nhãn hiển thị trạng thái kết nối và hệ thống
        self.status_label = tk.Label(header_frame, text="⚡ Trạng thái: ĐANG KẾT NỐI...",
                                     fg="#38bdf8", bg="#1e293b", font=("Arial", 14, "bold"))
        self.status_label.pack(pady=5)

        # Nhãn hiển thị đồng hồ thời gian thực
        self.clock_label = tk.Label(header_frame, text="", fg="#94a3b8", bg="#1e293b",
                                     font=("Courier", 12))
        self.clock_label.pack()

        # Khung chứa hai đèn giao thông và khu vực ngã tư
        lights_frame = tk.Frame(self.root, bg="#1e293b")
        lights_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Khởi tạo đèn giao thông 1 (Hướng A)
        self.traffic_light_1 = TrafficLight(lights_frame, "🚦 MẠCH 1 (Hướng A)",
                                             bg="#334155", relief="raised", bd=2)
        self.traffic_light_1.pack(side="left", fill="both", expand=True, padx=10)

        # Khung và nhãn đại diện cho khu vực ngã tư
        intersection_frame = tk.Frame(lights_frame, bg="#1e293b")
        intersection_frame.pack(side="left", padx=20)
        intersection_label = tk.Label(intersection_frame, text="🏢\nNGÃ TƯ\nTRUNG TÂM",
                                     font=("Arial", 12, "bold"), fg="#64748b", bg="#1e293b")
        intersection_label.pack(expand=True)

        # Khởi tạo đèn giao thông 2 (Hướng B)
        self.traffic_light_2 = TrafficLight(lights_frame, "🚦 MẠCH 2 (Hướng B)",
                                             bg="#334155", relief="raised", bd=2)
        self.traffic_light_2.pack(side="right", fill="both", expand=True, padx=10)

        # Khung điều khiển khẩn cấp
        self.control_frame = tk.LabelFrame(self.root, text="🎛️ ĐIỀU KHIỂN KHẨN CẤP",
                                             bg="#334155", fg="white", font=("Arial", 12, "bold"))
        self.control_frame.pack(fill="x", padx=20, pady=10)

        btn_frame = tk.Frame(self.control_frame, bg="#334155")
        btn_frame.pack(pady=15)

        # Các nút điều khiển khẩn cấp
        tk.Button(btn_frame, text="🚨 KHẨN CẤP\nMẠCH 1", bg="#dc2626", fg="white",
                  font=("Arial", 11, "bold"), command=lambda: self.send_command("E1"),
                  width=15, height=2, state="disabled").grid(row=0, column=0, padx=10)
        tk.Button(btn_frame, text="🚨 KHẨN CẤP\nMẠCH 2", bg="#dc2626", fg="white",
                  font=("Arial", 11, "bold"), command=lambda: self.send_command("E2"),
                  width=15, height=2, state="disabled").grid(row=0, column=1, padx=10)
        tk.Button(btn_frame, text="🔒 AN TOÀN\nCẢ HAI ĐỎ", bg="#ea580c", fg="white",
                  font=("Arial", 11, "bold"), command=lambda: self.send_command("E3"),
                  width=15, height=2, state="disabled").grid(row=0, column=2, padx=10)
        tk.Button(btn_frame, text="🔄 RESET\nBÌNH THƯỜNG", bg="#16a34a", fg="white",
                  font=("Arial", 11, "bold"), command=lambda: self.send_command("NORMAL"),
                  width=15, height=2, state="disabled").grid(row=0, column=3, padx=10)

        # New: Time Setting Control (Phần đặt thời gian mới)
        self.time_setting_frame = tk.LabelFrame(self.root, text="⏱️ ĐẶT THỜI GIAN PHA",
                                                 bg="#334155", fg="white", font=("Arial", 12, "bold"))
        self.time_setting_frame.pack(fill="x", padx=20, pady=(10, 10))

        self.time_setting_inner_frame = tk.Frame(self.time_setting_frame, bg="#334155")
        self.time_setting_inner_frame.pack(pady=10)

        # Lựa chọn Mạch (M1/M2) - Dù thời gian cài đặt là chung, nhưng UI vẫn giữ để dễ hiểu
        tk.Label(self.time_setting_inner_frame, text="Mạch:", bg="#334155", fg="white", font=("Arial", 10)).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.selected_circuit = tk.StringVar(value="M1") # Mặc định Mạch 1
        tk.Radiobutton(self.time_setting_inner_frame, text="Mạch 1", variable=self.selected_circuit, value="M1",
                       bg="#334155", fg="white", selectcolor="#4a4a4a", font=("Arial", 10)).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        tk.Radiobutton(self.time_setting_inner_frame, text="Mạch 2", variable=self.selected_circuit, value="M2",
                       bg="#334155", fg="white", selectcolor="#4a4a4a", font=("Arial", 10)).grid(row=0, column=2, padx=5, pady=5, sticky="w")

        # Lựa chọn Màu (Xanh/Đỏ)
        tk.Label(self.time_setting_inner_frame, text="Màu:", bg="#334155", fg="white", font=("Arial", 10)).grid(row=0, column=3, padx=5, pady=5, sticky="w")
        self.selected_color = tk.StringVar(value="GREEN") # Mặc định Xanh
        tk.Radiobutton(self.time_setting_inner_frame, text="Xanh", variable=self.selected_color, value="GREEN",
                       bg="#334155", fg="white", selectcolor="#4a4a4a", font=("Arial", 10)).grid(row=0, column=4, padx=5, pady=5, sticky="w")
        tk.Radiobutton(self.time_setting_inner_frame, text="Đỏ", variable=self.selected_color, value="RED",
                       bg="#334155", fg="white", selectcolor="#4a4a4a", font=("Arial", 10)).grid(row=0, column=5, padx=5, pady=5, sticky="w")

        # Nhập thời gian
        tk.Label(self.time_setting_inner_frame, text="Giây:", bg="#334155", fg="white", font=("Arial", 10)).grid(row=0, column=6, padx=5, pady=5, sticky="w")
        self.duration_entry = tk.Entry(self.time_setting_inner_frame, width=8, font=("Arial", 10), bg="#0f172a", fg="white", insertbackground="white")
        self.duration_entry.grid(row=0, column=7, padx=5, pady=5, sticky="ew")
        self.duration_entry.insert(0, "5") # Giá trị mặc định

        # Nút "ĐẶT THỜI GIAN"
        self.set_time_button = tk.Button(self.time_setting_inner_frame, text="ĐẶT THỜI GIAN", bg="#0ea5e9", fg="white",
                  font=("Arial", 10, "bold"), command=self.set_light_duration,
                  width=15, height=1, state="disabled")
        self.set_time_button.grid(row=0, column=8, padx=10, pady=5)
        
        # Vô hiệu hóa ban đầu các điều khiển đặt thời gian
        self.enable_time_setting_controls(False)


        # Khung nhật ký hệ thống
        log_frame = tk.LabelFrame(self.root, text="📋 NHẬT KÝ HỆ THỐNG",
                                   bg="#334155", fg="white", font=("Arial", 10))
        log_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Text widget để hiển thị nhật ký
        self.log = tk.Text(log_frame, height=6, bg="#0f172a", fg="#94a3b8",
                            font=("Consolas", 9), wrap="word")
        # Thanh cuộn cho nhật ký
        scrollbar = tk.Scrollbar(log_frame, command=self.log.yview)
        self.log.config(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.log.pack(side="left", fill="both", expand=True)

    def enable_time_setting_controls(self, enable=True):
        """
        Bật hoặc tắt các điều khiển trong phần đặt thời gian.
        """
        state = "normal" if enable else "disabled"
        for child in self.time_setting_inner_frame.winfo_children():
            if isinstance(child, (tk.Button, tk.Radiobutton, tk.Entry)):
                child.config(state=state)

    def update_clock(self):
        """
        Cập nhật nhãn đồng hồ thời gian thực mỗi giây.
        """
        now = datetime.now()
        self.clock_label.config(text=f"🕒 {now.strftime('%H:%M:%S')} - {now.strftime('%d/%m/%Y')}")
        self.root.after(1000, self.update_clock) # Lên lịch gọi lại sau 1 giây

    def log_message(self, message):
        """
        Thêm một tin nhắn vào hộp nhật ký hệ thống.

        Args:
            message (str): Tin nhắn cần ghi.
        """
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        self.log.insert(tk.END, f"{timestamp} {message}\n")
        self.log.see(tk.END) # Cuộn xuống cuối để hiển thị tin nhắn mới nhất
        # Giới hạn số lượng dòng trong nhật ký để tránh tràn bộ nhớ
        current_lines = int(float(self.log.index('end')))
        if current_lines > 200: # Nếu quá 200 dòng, xóa 150 dòng đầu tiên
            self.log.delete("1.0", f"{current_lines - 150}.0")

    def parse_serial(self, line):
        """
        Phân tích cú pháp một dòng dữ liệu nhận được từ Serial và cập nhật GUI.

        Args:
            line (str): Dòng dữ liệu từ Serial.
        """
        valid_colors = ["RED", "GREEN", "YELLOW"]
        if line.startswith("S,"): # Dữ liệu trạng thái đèn
            parts = line.split(",")
            if len(parts) == 5:
                try:
                    # Tách các phần: _, màu_m1, thời_gian_m1, màu_m2, thời_gian_m2
                    _, m1_color, m1_time, m2_color, m2_time = parts
                    
                    # Kiểm tra màu hợp lệ
                    if m1_color not in valid_colors or m2_color not in valid_colors:
                        self.log_message(f"Dữ liệu màu không hợp lệ: {line}")
                        return

                    m1_secs = int(m1_time)
                    m2_secs = int(m2_time)

                    # Cập nhật trạng thái cho từng đèn giao thông
                    self.traffic_light_1.update_light(m1_color, m1_secs)
                    self.traffic_light_2.update_light(m2_color, m2_secs)
                    # Cập nhật trạng thái tổng thể của hệ thống
                    self.update_system_status(m1_color, m1_secs, m2_color, m2_secs)

                except ValueError as e:
                    self.log_message(f"Lỗi parse dữ liệu số: {e} trong dòng: {line}")
                    # Đặt đèn về trạng thái lỗi nếu có lỗi parse
                    self.traffic_light_1.update_light("NONE", 0)
                    self.traffic_light_2.update_light("NONE", 0)
            else:
                self.log_message(f"Dữ liệu Serial không đúng định dạng: {line}")
        elif line.startswith(">>> KHẨN CẤP:"): # Thông báo chế độ khẩn cấp
            if "MẠCH 1 XANH" in line:
                self.traffic_light_1.update_light("GREEN", 0) # Đặt ngay Mạch 1 xanh, Mạch 2 đỏ
                self.traffic_light_2.update_light("RED", 0)
                self.status_label.config(text="🚨 Trạng thái: KHẨN CẤP – MẠCH 1", fg="#ef4444")
                self.emergency_mode = 1
            elif "MẠCH 2 XANH" in line:
                self.traffic_light_1.update_light("RED", 0) # Đặt ngay Mạch 1 đỏ, Mạch 2 xanh
                self.traffic_light_2.update_light("GREEN", 0)
                self.status_label.config(text="🚨 Trạng thái: KHẨN CẤP – MẠCH 2", fg="#ef4444")
                self.emergency_mode = 2
            elif "CẢ HAI ĐỎ" in line:
                self.traffic_light_1.update_light("RED", 0) # Đặt ngay cả hai đỏ
                self.traffic_light_2.update_light("RED", 0)
                self.status_label.config(text="🔒 Trạng thái: AN TOÀN – CẢ HAI ĐỎ", fg="#38bdf8")
                self.emergency_mode = 3
            self.log_message(line)
        elif "TẮT KHẨN CẤP" in line: # Thông báo tắt chế độ khẩn cấp
            self.status_label.config(text="✅ Trạng thái: HOẠT ĐỘNG BÌNH THƯỜNG", fg="#22c55e")
            self.emergency_mode = 0
            self.log_message(line)
        elif line.startswith("SET_UPDATED,"): # Phản hồi khi đặt thời gian pha
            parts = line.split(",")
            if len(parts) == 4:
                _, color_type, val1, val2 = parts
                self.log_message(f"Thời gian pha được cập nhật: Màu {color_type} = {val1}s, Đỏ đối diện = {val2}s. Chu kỳ được đặt lại.")
            else:
                self.log_message(f"Dữ liệu SET_UPDATED không đúng định dạng: {line}")
        elif line.startswith(">>> Cảnh báo:"): # Cảnh báo từ ESP32 (ví dụ: thời gian xanh tối thiểu)
            self.log_message(line)
        else: # Các thông báo khác từ ESP32 (debug, v.v.)
            self.log_message(f"ESP32: {line}")

    def update_system_status(self, m1_color, m1_secs, m2_color, m2_secs):
        """
        Cập nhật nhãn trạng thái tổng thể của ứng dụng dựa trên trạng thái đèn hiện tại.
        Điều này đặc biệt quan trọng để hiển thị trạng thái khẩn cấp được kích hoạt từ ESP32.
        """
        # Nếu đang có đèn vàng ở một trong hai mạch, tức là đang trong pha chuyển tiếp khẩn cấp
        if m1_color == "YELLOW" or m2_color == "YELLOW":
            self.status_label.config(text="⚠️ ĐANG CHUYỂN VÀNG TRƯỚC KHẨN CẤP", fg="#facc15")
        # Kiểm tra các trường hợp đặc biệt khi thời gian đếm ngược về 0 (chế độ khẩn cấp cứng)
        # Chỉ cập nhật trạng thái nếu không ở chế độ khẩn cấp đã được kích hoạt từ nút nhấn/GUI
        elif self.emergency_mode == 0: # Chỉ cập nhật nếu không ở chế độ khẩn cấp đã được kích hoạt
            if m1_secs == 0 and m2_secs == 0:
                if m1_color == "RED" and m2_color == "RED":
                    self.status_label.config(text="🔒 Trạng thái: AN TOÀN – CẢ HAI ĐỎ (Từ ESP32)", fg="#38bdf8")
                elif m1_color == "GREEN" and m2_color == "RED":
                    self.status_label.config(text="🚨 Trạng thái: KHẨN CẤP – MẠCH 1 (Từ ESP32)", fg="#ef4444")
                elif m2_color == "GREEN" and m1_color == "RED":
                    self.status_label.config(text="🚨 Trạng thái: KHẨN CẤP – MẠCH 2 (Từ ESP32)", fg="#ef4444")
                else: # Trạng thái không xác định khác khi thời gian về 0
                    self.status_label.config(text="⚠️ Trạng thái: KHÔNG XÁC ĐỊNH", fg="#fbbf24")
            else: # Trạng thái hoạt động bình thường
                self.status_label.config(text="✅ Trạng thái: HOẠT ĐỘNG BÌNH THƯỜNG", fg="#22c55e")
                self.emergency_mode = 0 # Đảm bảo emergency_mode là 0 nếu phát hiện hoạt động bình thường

    def read_serial(self):
        """
        Hàm được chạy trong một luồng riêng để đọc dữ liệu từ cổng Serial liên tục.
        Dữ liệu đọc được sẽ được thêm vào hàng đợi để xử lý trên luồng chính.
        """
        while True:
            if self.ser and self.ser.is_open and self.ser.in_waiting: # Kiểm tra xem có dữ liệu trong bộ đệm nhận không
                try:
                    # Đọc một dòng, giải mã bằng UTF-8 (bỏ qua lỗi) và loại bỏ khoảng trắng
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        self.serial_data_queue.append(line) # Thêm dòng dữ liệu vào hàng đợi
                except Exception as e:
                    self.log_message(f"Lỗi đọc Serial: {e}")
            time.sleep(0.01) # Tạm dừng 10ms để tránh chiếm dụng CPU quá mức

    def process_serial_queue(self):
        """
        Xử lý các mục trong hàng đợi dữ liệu Serial.
        Hàm này được gọi định kỳ trên luồng chính của Tkinter.
        """
        if self.serial_data_queue:
            line = self.serial_data_queue.pop(0) # Lấy dòng đầu tiên từ hàng đợi
            self.log_message(f"Nhận: {line}") # Ghi vào nhật ký là đã nhận dữ liệu
            self.parse_serial(line) # Phân tích và cập nhật GUI
        self.root.after(10, self.process_serial_queue) # Lên lịch gọi lại sau 10ms

    def set_light_duration(self):
        """
        Gửi lệnh đặt thời gian cho đèn giao thông đến ESP32.
        Lấy thông tin từ các điều khiển UI mới.
        """
        # circuit = self.selected_circuit.get() # Mạch 1 hoặc Mạch 2 (không dùng cho logic ESP32 này vì là tham số chung)
        color = self.selected_color.get()     # GREEN (Xanh) hoặc RED (Đỏ)
        duration_str = self.duration_entry.get()

        try:
            duration = int(duration_str)
            if duration <= 0:
                messagebox.showerror("Lỗi nhập liệu", "Thời gian phải là số dương.")
                return
            
            # Gửi lệnh SET,<MÀU>,<GIÂY> đến ESP32
            cmd_to_send = f"SET,{color.upper()},{duration}"
            self.send_command(cmd_to_send)
            self.log_message(f"Yêu cầu đặt {color.upper()} {duration} giây.")

        except ValueError:
            messagebox.showerror("Lỗi nhập liệu", "Thời gian phải là số nguyên.")


if __name__ == "__main__":
    root = tk.Tk()
    app = TrafficApp(root, port="COM5", baudrate=115200) # Khởi tạo ứng dụng với cổng COM5

    def on_close():
        """
        Xử lý sự kiện khi người dùng đóng cửa sổ ứng dụng.
        Hỏi xác nhận và đóng kết nối Serial trước khi thoát.
        """
        if messagebox.askokcancel("Thoát", "Bạn có chắc muốn thoát ứng dụng?"):
            if app.ser and app.ser.is_open:
                app.ser.close() # Đóng kết nối Serial nếu đang mở
            root.destroy() # Đóng cửa sổ Tkinter

    # Đăng ký hàm on_close để được gọi khi cửa sổ bị đóng
    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop() # Bắt đầu vòng lặp sự kiện chính của Tkinter
