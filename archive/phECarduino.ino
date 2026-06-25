#include <Wire.h>
#include <LiquidCrystal_I2C.h>

LiquidCrystal_I2C lcd(0x27, 16, 2);

#define PH_ADDR 0x63
#define EC_ADDR 0x64
#define ENC_CLK 3
#define ENC_DT 4
#define ENC_SW 5

// Menu states
#define MENU_NONE 0
#define MENU_TOP 1       // "Calibrate?" Yes/No
#define MENU_SELECT 2    // "pH Cal" / "EC Cal"

bool selectedYes = false;
int lastCLK = HIGH;
bool inCalMode = false;
unsigned long lastEncoderTime = 0;
int menuState = MENU_NONE;
int menuSelection = 0;   // 0 = first option, 1 = second option

void setup() {
  Serial.begin(9600);
  Wire.begin();
  lcd.init();
  lcd.backlight();

  pinMode(ENC_CLK, INPUT_PULLUP);
  pinMode(ENC_DT, INPUT_PULLUP);
  pinMode(ENC_SW, INPUT_PULLUP);

  lcd.setCursor(0, 0);
  lcd.print("pH/EC Monitor");
  lcd.setCursor(0, 1);
  lcd.print("Tank 1");
  delay(2000);
}

void loop() {
  // Check for button press
  if (digitalRead(ENC_SW) == LOW) {
    delay(50);
    if (digitalRead(ENC_SW) == LOW) {
      handleButtonPress();
      while (digitalRead(ENC_SW) == LOW);
      delay(200);
    }
  }

  // Handle rotary encoder when in any menu
  if (menuState != MENU_NONE) {
    int clkState = digitalRead(ENC_CLK);
    unsigned long currentTime = millis();

    // Debounce: 50ms minimum between encoder events
    if (clkState != lastCLK && clkState == LOW && (currentTime - lastEncoderTime > 50)) {
      if (menuState == MENU_TOP) {
        // Toggle Yes/No
        selectedYes = !selectedYes;
        showPrompt();
      } else if (menuState == MENU_SELECT) {
        // Toggle pH Cal / EC Cal
        menuSelection = (menuSelection == 0) ? 1 : 0;
        showCalSelect();
      }
      lastEncoderTime = currentTime;
    }
    lastCLK = clkState;
  }

  // Normal operation - read and send data
  if (menuState == MENU_NONE && !inCalMode) {
    float ph = getReading(PH_ADDR);
    float ec_us = getReading(EC_ADDR);
    float ec = ec_us / 1000.0;

    // Send JSON to Pi via serial (only if readings are valid)
    if (ph > 0 && ec_us >= 0) {
      Serial.print("{\"ph\":");
      Serial.print(ph, 2);
      Serial.print(",\"ec\":");
      Serial.print(ec, 2);
      Serial.println("}");
    }

    displayReadings(ph, ec);
    delay(2000);
  } else {
    delay(100);
  }
}

void handleButtonPress() {
  if (menuState == MENU_NONE && !inCalMode) {
    // First click - show "Calibrate?" prompt
    menuState = MENU_TOP;
    selectedYes = false;
    showPrompt();
  } else if (menuState == MENU_TOP) {
    // Confirm Yes/No
    if (selectedYes) {
      // Show pH/EC selection
      menuState = MENU_SELECT;
      menuSelection = 0;
      showCalSelect();
    } else {
      // Cancel - back to normal
      menuState = MENU_NONE;
    }
  } else if (menuState == MENU_SELECT) {
    // Confirm pH or EC calibration
    menuState = MENU_NONE;
    if (menuSelection == 0) {
      startPhCalibration();
    } else {
      startEcCalibration();
    }
  }
}

void showPrompt() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Calibrate?");
  lcd.setCursor(0, 1);
  if (selectedYes) {
    lcd.print("     > YES <");
  } else {
    lcd.print("     > NO <");
  }
}

void showCalSelect() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Select sensor:");
  lcd.setCursor(0, 1);
  if (menuSelection == 0) {
    lcd.print("  > pH <   EC  ");
  } else {
    lcd.print("    pH   > EC <");
  }
}

void displayReadings(float ph, float ec) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("pH: ");
  lcd.print(ph, 2);

  lcd.setCursor(0, 1);
  lcd.print("EC: ");
  lcd.print(ec, 2);
  lcd.print(" mS");
}

void waitForClick() {
  while (digitalRead(ENC_SW) == HIGH);
  delay(50);
  while (digitalRead(ENC_SW) == LOW);
  delay(200);
}

void startPhCalibration() {
  inCalMode = true;

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("pH Mid: 7.00");
  lcd.setCursor(0, 1);
  lcd.print("Click when ready");

  waitForClick();
  sendCommand(PH_ADDR, "Cal,mid,7.00");

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("pH Low: 4.00");
  lcd.setCursor(0, 1);
  lcd.print("Click when ready");

  waitForClick();
  sendCommand(PH_ADDR, "Cal,low,4.00");

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("pH Calibration");
  lcd.setCursor(0, 1);
  lcd.print("Complete!");
  delay(2000);

  inCalMode = false;
}

void startEcCalibration() {
  inCalMode = true;

  // Step 1: Dry calibration (probe in air)
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("EC Dry Cal");
  lcd.setCursor(0, 1);
  lcd.print("Probe in air");

  waitForClick();
  sendCommand(EC_ADDR, "Cal,dry");

  // Step 2: Single-point calibration with 1413 uS/cm solution
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("EC: 1413 uS/cm");
  lcd.setCursor(0, 1);
  lcd.print("Click when ready");

  waitForClick();
  sendCommand(EC_ADDR, "Cal,one,1413");

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("EC Calibration");
  lcd.setCursor(0, 1);
  lcd.print("Complete!");
  delay(2000);

  inCalMode = false;
}

void sendCommand(int address, const char* command) {
  Wire.beginTransmission(address);
  Wire.write(command);
  Wire.endTransmission();
  delay(900);
}

float getReading(int address) {
  Wire.beginTransmission(address);
  Wire.write('R');
  Wire.endTransmission();
  delay(1000);

  Wire.requestFrom(address, 20);
  if (Wire.available() == 0) {
    return -1;  // No response
  }

  byte code = Wire.read();

  // EZO response codes: 1=success, 2=syntax error, 254=processing, 255=no data
  if (code != 1) {
    // Flush remaining bytes
    while (Wire.available()) Wire.read();
    return -1;  // Reading failed
  }

  char buffer[20] = {0};
  int i = 0;
  while (Wire.available() && i < 19) {
    buffer[i++] = Wire.read();
  }
  return atof(buffer);
}