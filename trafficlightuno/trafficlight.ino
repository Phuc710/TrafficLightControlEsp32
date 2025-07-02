// Pin definitions for 74HC595 Shift Register for Circuit 1
const int latchPin1 = 19; // Chân ST_CP (Storage Register Clock Pin) cho Mạch 1
const int clockPin1 = 18; // Chân SH_CP (Shift Register Clock Pin) cho Mạch 1
const int dataPin1  = 23; // Chân DS (Serial Data Input) cho Mạch 1

// Pin definitions for 74HC595 Shift Register for Circuit 2
const int latchPin2 = 22; // Chân ST_CP (Storage Register Clock Pin) cho Mạch 2
const int clockPin2 = 21; // Chân SH_CP (Shift Register Clock Pin) cho Mạch 2
const int dataPin2  = 13; // Chân DS (Serial Data Input) cho Mạch 2

// Hex codes for 0-9 digits on common cathode 7-segment LED
const byte so[] = {0xC0, 0xF9, 0xA4, 0xB0, 0x99, 0x92, 0x82, 0xF8, 0x80, 0x90};

// Pin definitions for traffic lights
// Circuit 1 (Direction A)
const int m1Green  = 15;
const int m1Yellow = 2;
const int m1Red    = 4;
// Circuit 2 (Direction B)
const int m2Green  = 17;
const int m2Yellow = 5;
const int m2Red    = 16;

// Pin definitions for emergency buttons (using INPUT_PULLUP)
const int emergencyButton1 = 35; // Button to activate emergency mode: Circuit 1 Green
const int emergencyButton2 = 34; // Button to activate emergency mode: Circuit 2 Green
const int emergencyButton3 = 32; // Button to activate emergency mode: Both Reds

// Default phase durations (can be changed via Serial)
const unsigned long DEFAULT_GREEN_DURATION_MS = 5000; // 5 seconds default for green light
const unsigned long YELLOW_DURATION_MS = 2000;         // 2 seconds fixed for yellow light

// Global variables for current phase durations (modifiable via Serial)
unsigned long current_active_green_duration_ms; // Duration for the current green phase
unsigned long current_opposing_red_duration_ms; // Duration for the opposing red phase (will be green_duration + yellow_duration)
unsigned long current_total_cycle_duration_ms;  // Total duration of a complete normal cycle

// State variables
volatile int emergencyMode = 0; // 0: normal, 1: circuit 1 green (emergency), 2: circuit 2 green (emergency), 3: both red (safe)
unsigned long cycleStartTime = 0; // Time when the current traffic light cycle started
unsigned long lastInterruptTime = 0; // Last interrupt time (for debouncing)
const unsigned long DEBOUNCE_DELAY = 200; // Debounce delay (milliseconds)
unsigned long lastSerialUpdate = 0; // Last time serial status was sent
const unsigned long SERIAL_UPDATE_INTERVAL = 200; // Interval for sending serial status (milliseconds)

bool pendingEmergency = false; // Flag indicating if an emergency request is pending a yellow phase
int pendingMode = 0;           // The emergency mode to apply after the yellow phase
unsigned long yellowStartTime = 0; // Time when the transition yellow phase started
bool yellowPhase = false;      // Flag indicating if currently in a transition yellow phase

// Declare ISR functions and other functions
void IRAM_ATTR toggleEmergency1();
void IRAM_ATTR toggleEmergency2();
void IRAM_ATTR toggleEmergency3();
void displayDigitsCircuit1(int time_val); // Hàm hiển thị cho Mạch 1
void displayDigitsCircuit2(int time_val); // Hàm hiển thị cho Mạch 2
void sendSerialStatus();

void setup() {
  Serial.begin(115200); // Initialize Serial communication at 115200 baud rate

  // Configure Shift Register pins for Circuit 1 as OUTPUT
  pinMode(latchPin1, OUTPUT);
  pinMode(clockPin1, OUTPUT);
  pinMode(dataPin1, OUTPUT);

  // Configure Shift Register pins for Circuit 2 as OUTPUT
  pinMode(latchPin2, OUTPUT);
  pinMode(clockPin2, OUTPUT);
  pinMode(dataPin2, OUTPUT);

  // Configure traffic light pins as OUTPUT
  pinMode(m1Green, OUTPUT); pinMode(m1Yellow, OUTPUT); pinMode(m1Red, OUTPUT);
  pinMode(m2Green, OUTPUT); pinMode(m2Yellow, OUTPUT); pinMode(m2Red, OUTPUT);

  // Ensure all lights are off at startup
  digitalWrite(m1Green, LOW); digitalWrite(m1Yellow, LOW); digitalWrite(m1Red, LOW);
  digitalWrite(m2Green, LOW); digitalWrite(m2Yellow, LOW); digitalWrite(m2Red, LOW);

  // Configure emergency button pins as INPUT_PULLUP (using internal pull-up resistors)
  pinMode(emergencyButton1, INPUT_PULLUP);
  pinMode(emergencyButton2, INPUT_PULLUP);
  pinMode(emergencyButton3, INPUT_PULLUP);

  // Attach interrupts to emergency buttons
  // FALLING: Triggers when pin changes from HIGH to LOW (button press)
  attachInterrupt(digitalPinToInterrupt(emergencyButton1), toggleEmergency1, FALLING);
  attachInterrupt(digitalPinToInterrupt(emergencyButton2), toggleEmergency2, FALLING);
  attachInterrupt(digitalPinToInterrupt(emergencyButton3), toggleEmergency3, FALLING);

  // Initialize default phase durations
  current_active_green_duration_ms = DEFAULT_GREEN_DURATION_MS;
  current_opposing_red_duration_ms = current_active_green_duration_ms + YELLOW_DURATION_MS;
  // Total cycle is (Green + Yellow) + (Opposing Red) = (G + Y) + (G + Y) = 2 * (G + Y)
  current_total_cycle_duration_ms = current_active_green_duration_ms + YELLOW_DURATION_MS + current_opposing_red_duration_ms;

  cycleStartTime = millis(); // Initialize cycle start time
}

void loop() {
  // Process commands received from Serial (from Python GUI)
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n'); // Read string until newline character
    command.trim(); // Remove leading/trailing whitespace

    // Check and call corresponding functions for commands
    if (command == "E1") {
      toggleEmergency1();
    } else if (command == "E2") {
      toggleEmergency2();
    } else if (command == "E3") {
      toggleEmergency3();
    } else if (command == "NORMAL") { // Reset to normal mode and restart cycle
      emergencyMode = 0;
      pendingEmergency = false;
      yellowPhase = false;
      cycleStartTime = millis(); // Reset cycle time to start from the beginning
      Serial.println(">>> TẮT KHẨN CẤP - QUAY LẠI BÌNH THƯỜNG <<<"); // Send message to GUI
    } else if (command.startsWith("SET,")) { // Command to set phase duration
      int comma1 = command.indexOf(',');
      int comma2 = command.indexOf(',', comma1 + 1);
      String color_type = command.substring(comma1 + 1, comma2);
      int seconds = command.substring(comma2 + 1).toInt();
      unsigned long new_duration_ms = (unsigned long)seconds * 1000;

      if (color_type == "GREEN") {
        current_active_green_duration_ms = new_duration_ms;
        current_opposing_red_duration_ms = current_active_green_duration_ms + YELLOW_DURATION_MS;
        Serial.print("SET_UPDATED,GREEN,");
        Serial.print(current_active_green_duration_ms / 1000);
        Serial.print(",");
        Serial.println(current_opposing_red_duration_ms / 1000);
      } else if (color_type == "RED") {
        current_opposing_red_duration_ms = new_duration_ms;
        // Calculate green duration based on the new opposing red duration.
        // It's `red_duration - yellow_duration` because opposing_red_duration is (green_duration + yellow_duration)
        current_active_green_duration_ms = current_opposing_red_duration_ms - YELLOW_DURATION_MS;
        
        // Ensure minimum green duration is 1 second
        if (current_active_green_duration_ms < 1000) {
          current_active_green_duration_ms = 1000; // Set to minimum
          // Recalculate opposing red duration based on the adjusted green
          current_opposing_red_duration_ms = current_active_green_duration_ms + YELLOW_DURATION_MS;
          Serial.println(">>> Cảnh báo: Thời gian đỏ quá ngắn. Đèn xanh tối thiểu 1s. Đã điều chỉnh. <<<");
        }
        Serial.print("SET_UPDATED,RED,");
        Serial.print(current_opposing_red_duration_ms / 1000);
        Serial.print(",");
        Serial.println(current_active_green_duration_ms / 1000);
      } else {
        Serial.println("SET_ERROR: Màu không hợp lệ (chỉ GREEN/RED)");
      }
      // Recalculate total cycle duration after phase time change
      current_total_cycle_duration_ms = current_active_green_duration_ms + YELLOW_DURATION_MS + current_opposing_red_duration_ms;
      cycleStartTime = millis(); // Restart cycle to apply new times immediately
    }
  }

  // Send current light status via Serial periodically
  if (millis() - lastSerialUpdate >= SERIAL_UPDATE_INTERVAL) {
    sendSerialStatus();
    lastSerialUpdate = millis();
  }

  // Handle transition yellow phase when an emergency request is pending
  if (yellowPhase) {
    if (millis() - yellowStartTime >= YELLOW_DURATION_MS) { // If yellow phase has ended
      emergencyMode = pendingMode; // Switch to the pending emergency mode
      pendingEmergency = false; // Reset pending flag
      yellowPhase = false;      // End yellow phase

      // Send notification about activated emergency mode to GUI
      if (pendingMode == 1) {
        Serial.println(">>> KHẨN CẤP: MẠCH 1 XANH <<<");
      } else if (pendingMode == 2) {
        Serial.println(">>> KHẨN CẤP: MẠCH 2 XANH <<<");
      } else if (pendingMode == 3) {
        // Set both lights red immediately if this is the safe mode
        digitalWrite(m1Green, LOW); digitalWrite(m1Yellow, LOW); digitalWrite(m1Red, HIGH);
        digitalWrite(m2Green, LOW); digitalWrite(m2Yellow, LOW); digitalWrite(m2Red, HIGH);
        Serial.println(">>> KHẨN CẤP: CẢ HAI ĐỎ <<<");
      }
    } else { // Still in yellow phase
      // Set yellow light for the circuit that needs to change, and red for the other
      if (pendingMode == 1) { // Preparing for Circuit 1 Green (Circuit 2 Red, so Circuit 2 Yellow)
        digitalWrite(m2Green, LOW); digitalWrite(m2Yellow, HIGH); digitalWrite(m2Red, LOW);
        digitalWrite(m1Green, LOW); digitalWrite(m1Yellow, LOW); digitalWrite(m1Red, HIGH); // Mạch 1 remains Red or goes to Red
      } else if (pendingMode == 2) { // Preparing for Circuit 2 Green (Circuit 1 Red, so Circuit 1 Yellow)
        digitalWrite(m1Green, LOW); digitalWrite(m1Yellow, HIGH); digitalWrite(m1Red, LOW);
        digitalWrite(m2Green, LOW); digitalWrite(m2Yellow, LOW); digitalWrite(m2Red, HIGH); // Mạch 2 remains Red or goes to Red
      } else if (pendingMode == 3) { // Preparing for Both Reds (lights that are green will turn yellow)
        // If m1 was green, turn yellow, else keep current state (likely red)
        digitalWrite(m1Yellow, (digitalRead(m1Green) == HIGH) ? HIGH : LOW);
        digitalWrite(m1Green, LOW); // Turn off green
        digitalWrite(m1Red, (digitalRead(m1Yellow) == LOW && digitalRead(m1Green) == LOW) ? HIGH : LOW); // Ensure red is on if not yellow/green

        // If m2 was green, turn yellow, else keep current state (likely red)
        digitalWrite(m2Yellow, (digitalRead(m2Green) == HIGH) ? HIGH : LOW);
        digitalWrite(m2Green, LOW); // Turn off green
        digitalWrite(m2Red, (digitalRead(m2Yellow) == LOW && digitalRead(m2Green) == LOW) ? HIGH : LOW); // Ensure red is on if not yellow/green
      }
      displayDigitsCircuit1(0); // Hiển thị 00 trên cả hai màn hình trong pha vàng chuyển tiếp
      displayDigitsCircuit2(0);
      return; // Return to the beginning of loop to continue yellow phase
    }
  }

  // Handle activated emergency modes
  if (emergencyMode == 1) { // Circuit 1 Green, Circuit 2 Red
    digitalWrite(m1Green, HIGH); digitalWrite(m1Yellow, LOW); digitalWrite(m1Red, LOW);
    digitalWrite(m2Green, LOW); digitalWrite(m2Yellow, LOW); digitalWrite(m2Red, HIGH);
    displayDigitsCircuit1(0); // Hiển thị 00
    displayDigitsCircuit2(0);
    return; // Return to the beginning of loop
  } else if (emergencyMode == 2) { // Circuit 1 Red, Circuit 2 Green
    digitalWrite(m1Green, LOW); digitalWrite(m1Yellow, LOW); digitalWrite(m1Red, HIGH);
    digitalWrite(m2Green, HIGH); digitalWrite(m2Yellow, LOW); digitalWrite(m2Red, LOW);
    displayDigitsCircuit1(0); // Hiển thị 00
    displayDigitsCircuit2(0);
    return; // Return to the beginning of loop
  } else if (emergencyMode == 3) { // Both lights Red
    digitalWrite(m1Green, LOW); digitalWrite(m1Yellow, LOW); digitalWrite(m1Red, HIGH);
    digitalWrite(m2Green, LOW); digitalWrite(m2Yellow, LOW); digitalWrite(m2Red, HIGH);
    displayDigitsCircuit1(0); // Hiển thị 00
    displayDigitsCircuit2(0);
    return; // Return to the beginning of loop
  }

  // Normal operation mode
  unsigned long currentTime = millis();
  unsigned long cycleTime = (currentTime - cycleStartTime) % current_total_cycle_duration_ms; // Time elapsed in current cycle

  int m1_time = 0, m2_time = 0; // Countdown time for Circuit 1 and Circuit 2

  // Phase 1 of normal cycle: Circuit 1 Red, Circuit 2 Green (then Yellow)
  if (cycleTime < current_opposing_red_duration_ms) { // Entire duration Circuit 1 is RED (when Circuit 2 is Green + Yellow)
    digitalWrite(m1Red, HIGH); digitalWrite(m1Yellow, LOW); digitalWrite(m1Green, LOW); // Circuit 1 Red
    m1_time = (current_opposing_red_duration_ms - cycleTime) / 1000; // Remaining time for Circuit 1 Red

    if (cycleTime < current_active_green_duration_ms) { // Circuit 2 is Green
      digitalWrite(m2Green, HIGH); digitalWrite(m2Yellow, LOW); digitalWrite(m2Red, LOW); // Circuit 2 Green
      m2_time = (current_active_green_duration_ms - cycleTime) / 1000; // Remaining time for Circuit 2 Green
    } else { // Circuit 2 turns Yellow (short yellow phase before Circuit 1 Green)
      digitalWrite(m2Green, LOW); digitalWrite(m2Yellow, HIGH); digitalWrite(m2Red, LOW); // Circuit 2 Yellow
      m2_time = (current_opposing_red_duration_ms - cycleTime) / 1000; // Remaining time for Circuit 2 phase (Yellow)
    }
    displayDigitsCircuit1(m1_time); // Hiển thị thời gian Mạch 1 trên màn hình 7 đoạn của Mạch 1
    displayDigitsCircuit2(m2_time); // Hiển thị thời gian Mạch 2 trên màn hình 7 đoạn của Mạch 2
  }
  // Phase 2 of normal cycle: Circuit 1 Green (then Yellow), Circuit 2 Red
  else {
    unsigned long phase2_time = cycleTime - current_opposing_red_duration_ms; // Time elapsed in this phase

    digitalWrite(m2Red, HIGH); digitalWrite(m2Yellow, LOW); digitalWrite(m2Green, LOW); // Circuit 2 Red
    m2_time = (current_total_cycle_duration_ms - cycleTime) / 1000; // Remaining time for Circuit 2 Red

    if (phase2_time < current_active_green_duration_ms) { // Circuit 1 is Green
      digitalWrite(m1Green, HIGH); digitalWrite(m1Yellow, LOW); digitalWrite(m1Red, LOW); // Circuit 1 Green
      m1_time = (current_active_green_duration_ms - phase2_time) / 1000; // Remaining time for Circuit 1 Green
    } else { // Circuit 1 turns Yellow
      digitalWrite(m1Green, LOW); digitalWrite(m1Yellow, HIGH); digitalWrite(m1Red, LOW); // Circuit 1 Yellow
      m1_time = (current_total_cycle_duration_ms - cycleTime) / 1000; // Remaining time for Circuit 1 phase (Yellow)
    }
    displayDigitsCircuit1(m1_time); // Hiển thị thời gian Mạch 1 trên màn hình 7 đoạn của Mạch 1
    displayDigitsCircuit2(m2_time); // Hiển thị thời gian Mạch 2 trên màn hình 7 đoạn của Mạch 2
  }
}

/**
 * @brief Hiển thị số trên màn hình 7 đoạn của Mạch 1 bằng cách sử dụng shift register.
 *
 * @param time_val Giá trị thời gian (tính bằng giây) cần hiển thị (0-99).
 */
void displayDigitsCircuit1(int time_val) {
  time_val = constrain(time_val, 0, 99); // Giới hạn giá trị từ 0 đến 99
  int tens = time_val / 10;
  int units = time_val % 10;

  digitalWrite(latchPin1, LOW); // Đặt latchPin1 về LOW để bắt đầu truyền dữ liệu
  shiftOut(dataPin1, clockPin1, MSBFIRST, so[units]); // Gửi mã hex của chữ số hàng đơn vị (phải)
  shiftOut(dataPin1, clockPin1, MSBFIRST, so[tens]);  // Gửi mã hex của chữ số hàng chục (trái)
  digitalWrite(latchPin1, HIGH); // Đặt latchPin1 về HIGH để chốt dữ liệu và hiển thị
}

/**
 * @brief Hiển thị số trên màn hình 7 đoạn của Mạch 2 bằng cách sử dụng shift register.
 *
 * @param time_val Giá trị thời gian (tính bằng giây) cần hiển thị (0-99).
 */
void displayDigitsCircuit2(int time_val) {
  time_val = constrain(time_val, 0, 99); // Giới hạn giá trị từ 0 đến 99
  int tens = time_val / 10;
  int units = time_val % 10;

  digitalWrite(latchPin2, LOW); // Đặt latchPin2 về LOW để bắt đầu truyền dữ liệu
  shiftOut(dataPin2, clockPin2, MSBFIRST, so[units]); // Gửi mã hex của chữ số hàng đơn vị (phải)
  shiftOut(dataPin2, clockPin2, MSBFIRST, so[tens]);  // Gửi mã hex của chữ số hàng chục (trái)
  digitalWrite(latchPin2, HIGH); // Đặt latchPin2 về HIGH để chốt dữ liệu và hiển thị
}

/**
 * @brief Sends current traffic light status over Serial.
 * Data is sent in the format "S,<m1_color>,<m1_time>,<m2_color>,<m2_time>".
 */
void sendSerialStatus() {
  String m1_color, m2_color;
  int m1_time = 0, m2_time = 0;

  if (yellowPhase) { // Currently in emergency transition yellow phase
    m1_time = m2_time = (YELLOW_DURATION_MS - (millis() - yellowStartTime)) / 1000;
    if (pendingMode == 1) { // Preparing for Circuit 1 Green (Circuit 2 Yellow, Circuit 1 Red)
      m1_color = "RED";
      m2_color = "YELLOW";
    } else if (pendingMode == 2) { // Preparing for Circuit 2 Green (Circuit 1 Yellow, Circuit 2 Red)
      m1_color = "YELLOW";
      m2_color = "RED";
    } else if (pendingMode == 3) { // Preparing for Both Reds (lights that are green will turn yellow)
      m1_color = (digitalRead(m1Green) == HIGH) ? "YELLOW" : "RED";
      m2_color = (digitalRead(m2Green) == HIGH) ? "YELLOW" : "RED";
    }
  } else if (emergencyMode == 1) { // Emergency mode: Circuit 1 Green
    m1_color = "GREEN"; m2_color = "RED";
  } else if (emergencyMode == 2) { // Emergency mode: Circuit 2 Green
    m1_color = "RED"; m2_color = "GREEN";
  } else if (emergencyMode == 3) { // Emergency mode: Both Reds
    m1_color = "RED"; m2_color = "RED";
  } else { // Normal mode based on dynamic phase times
    unsigned long cycleTime = (millis() - cycleStartTime) % current_total_cycle_duration_ms;

    // Phase 1: Circuit 1 Red, Circuit 2 Green (then Yellow)
    if (cycleTime < current_opposing_red_duration_ms) {
      m1_color = "RED";
      m1_time = (current_opposing_red_duration_ms - cycleTime) / 1000;

      if (cycleTime < current_active_green_duration_ms) {
        m2_color = "GREEN";
        m2_time = (current_active_green_duration_ms - cycleTime) / 1000;
      } else {
        m2_color = "YELLOW";
        m2_time = (current_opposing_red_duration_ms - cycleTime) / 1000;
      }
    }
    // Phase 2: Circuit 1 Green (then Yellow), Circuit 2 Red
    else {
      unsigned long phase2_time = cycleTime - current_opposing_red_duration_ms;
      m2_color = "RED";
      m2_time = (current_total_cycle_duration_ms - cycleTime) / 1000;

      if (phase2_time < current_active_green_duration_ms) {
        m1_color = "GREEN";
        m1_time = (current_active_green_duration_ms - phase2_time) / 1000;
      } else {
        m1_color = "YELLOW";
        m1_time = (current_total_cycle_duration_ms - cycleTime) / 1000;
      }
    }
  }

  // Print status string to Serial
  Serial.print("S,"); Serial.print(m1_color); Serial.print(",");
  Serial.print(m1_time); Serial.print(",");
  Serial.print(m2_color); Serial.print(",");
  Serial.println(m2_time);
}

/**
 * @brief Interrupt service routine (ISR) for emergency button 1 (Circuit 1 green).
 * Activates Circuit 1 emergency mode. If Circuit 2 is currently green, it will transition through yellow for 2 seconds.
 */
void IRAM_ATTR toggleEmergency1() {
  unsigned long now = millis();
  if (now - lastInterruptTime > DEBOUNCE_DELAY) { // Debounce
    if (emergencyMode == 1) { // If already in Circuit 1 emergency mode, turn it off
      emergencyMode = 0; // Revert to normal mode
      // Attempt to re-synchronize the cycle to make Circuit 1 green immediately (as if it just finished its red phase)
      cycleStartTime = millis() - current_opposing_red_duration_ms; 
      Serial.println(">>> TẮT KHẨN CẤP - MẠCH 1 TIẾP TỤC BÌNH THƯỜNG <<<");
    } else { // If not in Circuit 1 emergency mode, activate it
      // Check if Circuit 2 is currently Green or Yellow
      if (digitalRead(m2Green) == HIGH || digitalRead(m2Yellow) == HIGH) { // If Circuit 2 is Green or Yellow
        pendingEmergency = true; // Set emergency pending flag
        pendingMode = 1;         // The mode to activate is Circuit 1 green
        yellowPhase = true;      // Start transition yellow phase
        yellowStartTime = millis(); // Record yellow phase start time
        Serial.println(">>> Mạch 2 đang xanh/vàng – chuyển vàng 2s rồi KHẨN CẤP mạch 1 <<<");
      } else { // Circuit 2 is not green/yellow, activate immediately
        emergencyMode = 1;
        Serial.println(">>> KHẨN CẤP: MẠCH 1 XANH <<<");
      }
    }
    lastInterruptTime = now; // Update last interrupt time
  }
}

/**
 * @brief Interrupt service routine (ISR) for emergency button 2 (Circuit 2 green).
 * Activates Circuit 2 emergency mode. If Circuit 1 is currently green, it will transition through yellow for 2 seconds.
 */
void IRAM_ATTR toggleEmergency2() {
  unsigned long now = millis();
  if (now - lastInterruptTime > DEBOUNCE_DELAY) { // Debounce
    if (emergencyMode == 2) { // If already in Circuit 2 emergency mode, turn it off
      emergencyMode = 0; // Revert to normal mode
      // Attempt to re-synchronize the cycle to make Circuit 2 green immediately (as if it just finished its red phase)
      cycleStartTime = millis(); 
      Serial.println(">>> TẮT KHẨN CẤP - MẠCH 2 TIẾP TỤC BÌNH THƯỜNG <<<");
    } else { // If not in Circuit 2 emergency mode, activate it
      // Check if Circuit 1 is currently Green or Yellow
      if (digitalRead(m1Green) == HIGH || digitalRead(m1Yellow) == HIGH) { // If Circuit 1 is Green or Yellow
        pendingEmergency = true;
        pendingMode = 2;
        yellowPhase = true;
        yellowStartTime = millis();
        Serial.println(">>> Mạch 1 đang xanh/vàng – chuyển vàng 2s rồi KHẨN CẤP mạch 2 <<<");
      } else { // Circuit 1 is not green/yellow, activate immediately
        emergencyMode = 2;
        Serial.println(">>> KHẨN CẤP: MẠCH 2 XANH <<<");
      }
    }
    lastInterruptTime = now;
  }
}

/**
 * @brief Interrupt service routine (ISR) for emergency button 3 (Both lights red).
 * Activates safe mode: both lights are red. If any light is green, it will transition through yellow for 2 seconds.
 */
void IRAM_ATTR toggleEmergency3() {
  unsigned long now = millis();
  if (now - lastInterruptTime > DEBOUNCE_DELAY) { // Debounce
    if (emergencyMode == 3) { // If already in both-red emergency mode, turn it off
      emergencyMode = 0; // Revert to normal mode
      cycleStartTime = millis(); // Reset cycle time
      Serial.println(">>> TẮT KHẨN CẤP - QUAY LẠI BÌNH THƯỜNG <<<");
    } else { // If not in both-red emergency mode, activate it
      if (digitalRead(m1Green) == HIGH || digitalRead(m2Green) == HIGH ||
          digitalRead(m1Yellow) == HIGH || digitalRead(m2Yellow) == HIGH) { // If any green/yellow light is on
        pendingEmergency = true;
        pendingMode = 3;
        yellowPhase = true;
        yellowStartTime = millis();
        Serial.println(">>> Có đèn xanh/vàng – chuyển vàng 2s rồi KHẨN CẤP: CẢ HAI ĐỎ <<<");
      } else { // No green/yellow light, activate immediately
        emergencyMode = 3;
        // Ensure both lights are red
        digitalWrite(m1Green, LOW); digitalWrite(m1Yellow, LOW); digitalWrite(m1Red, HIGH);
        digitalWrite(m2Green, LOW); digitalWrite(m2Yellow, LOW); digitalWrite(m2Red, HIGH);
        Serial.println(">>> KHẨN CẤP: CẢ HAI ĐỎ <<<");
      }
    }
    lastInterruptTime = now;
  }
}
