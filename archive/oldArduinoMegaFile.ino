//MainArduinoCode.ino

/**
 * Indoor Growing Facility Feed Control System
 * Version 2.0
 * 
 * Enhanced monitoring and control system for:
 * - EZO Peristaltic Pumps (I2C)
 * - Flow Meters
 * - Relay-controlled Solenoids
 */

 #include <Wire.h>

 // ================ Configuration Constants ================
 const bool DEBUG_MODE = true;                        // Enable debug mode to track pump status
 const unsigned long STATUS_UPDATE_INTERVAL = 2000;     // Status update interval in ms
 const unsigned long PUMP_CHECK_INTERVAL = 1000;      // Check active pumps every second
 const unsigned long VOLTAGE_CHECK_INTERVAL = 300000; // Check voltages every 5 minutes
 const int MAX_I2C_RETRIES = 3;                      // Maximum I2C command retries
 const int I2C_RETRY_DELAY = 100;                    // Delay between retries in ms
 
 // ================ Pin Definitions ================
 const int FLOW_METER_PINS[] = {0, 3, 2};  // Index 0 unused, Flow1=Pin3, Flow2=Pin2
 const int RELAY_PINS[] = {
     0,                                          // Index 0 unused
     34, 37, 32, 35, 30, 33, 28, 31,           // Relays 1-8
     26, 29, 24, 27, 22, 25, 36, 23            // Relays 9-16
 };
 
 // ================ Type Definitions ================
 struct PumpInfo {
     char name[17];               // 16 chars + null terminator
     float totalVolume;           // Total volume dispensed
     float voltage;               // Last measured voltage
     bool calibrated;             // Calibration status
     bool inverted;               // Direction inverted
     char lastError[32];          // Last error message
     unsigned long lastCheck;     // Timestamp of last status check
     int status;                  // Current status (0=off, 1=on)
     float targetVolume;          // Target volume for current operation
     float currentVolume;         // Current dispensed volume
     bool isDispensing;          // Flag to track active dispensing
 };
 
 struct FlowMeterInfo {
     volatile unsigned long pulseCount;    // Current pulse count
     volatile unsigned long lastCount;     // Last pulse count
     int status;                          // Current status (0=off, 1=on)
     int targetGallons;                   // Target gallons
     int currentGallons;                  // Current gallons
     int pulsesPerGallon;                // Calibration factor
     unsigned long lastUpdate;            // Last update timestamp
 };
 
 // ================ Global Variables ================
 // Communication buffers
 char commandBuffer[100];
 char pumpCommand[20];
 char pumpResponse[32];
 
 // Device state tracking
 PumpInfo pumps[9];                    // Pump information (index 0 unused)
 FlowMeterInfo flowMeters[3];          // Flow meter information (index 0 unused)
 bool relayStates[17] = {false};       // Relay states (index 0 unused)
 unsigned long lastStatusUpdate = 0;    // Timestamp of last status update
 unsigned long lastVoltageCheck = 0;    // Timestamp of last voltage check
 
 // ================ Interrupt Handlers ================
 void handleFlow1() { flowMeters[1].pulseCount++; }
 void handleFlow2() { flowMeters[2].pulseCount++; }
 
 // ================ Utility Functions ================
 void debugPrint(const char* description, const char* value) {
     if (!DEBUG_MODE) return;
     Serial.print(F("Debug: "));
     Serial.print(description);
     Serial.println(value);
 }
 
 void debugPrint(const char* description, int value) {
     if (!DEBUG_MODE) return;
     Serial.print(F("Debug: "));
     Serial.print(description);
     Serial.println(value);
 }
 
 void debugPrint(const char* description, float value) {
     if (!DEBUG_MODE) return;
     Serial.print(F("Debug: "));
     Serial.print(description);
     Serial.println(value);
 }
 
 // ================ Device Status Updates ================
 void updateFlowMeterStatus(int meterId) {
     if (flowMeters[meterId].status == 0) return;
     
     // Only update if pulse count has changed
     if (flowMeters[meterId].pulseCount != flowMeters[meterId].lastCount) {
         int newGallons = flowMeters[meterId].pulseCount / flowMeters[meterId].pulsesPerGallon;
         flowMeters[meterId].lastCount = flowMeters[meterId].pulseCount;
         
         // Only send update if gallons have changed
         if (newGallons != flowMeters[meterId].currentGallons) {
             flowMeters[meterId].currentGallons = newGallons;
             
             Serial.print(F("Start;Update;FlowStat;"));
             Serial.print(meterId);
             Serial.print(F(";"));
             Serial.print(flowMeters[meterId].currentGallons);
             Serial.print(F(";"));
             Serial.print(flowMeters[meterId].pulseCount);
             Serial.println(F(";end"));
             
             // Check if target reached
             if (flowMeters[meterId].targetGallons <= flowMeters[meterId].currentGallons) {
                 flowMeters[meterId].status = 0;
                 Serial.print(F("Start;Update;FlowComplete;"));
                 Serial.print(meterId);
                 Serial.println(F(";end"));
             }
         }
     }
 }
 
 // Parse the volume from EZO pump response
 float parseVolume(const char* response) {
     debugPrint("Parsing volume from: ", response);
     
     // Skip any prefixes like SOH (ASCII 1), "?", spaces, etc.
     const char* volumeStart = response;
     while (*volumeStart && (*volumeStart == 1 || *volumeStart == '?' || *volumeStart == ' ' || *volumeStart == '\r' || *volumeStart == '\n')) {
         volumeStart++;
     }
     
     // Debug each character to check for hidden characters
     if (DEBUG_MODE) {
         Serial.print(F("Debug: ASCII values: "));
         for(int i = 0; volumeStart[i] != '\0'; i++) {
             Serial.print((int)volumeStart[i]);
             Serial.print(F(" "));
         }
         Serial.println();
     }
     
     // Manual string to float conversion
     float result = 0.0;
     float decimal = 0.0;
     bool isNegative = false;
     bool hasDecimal = false;
     float decimalPlace = 0.1;
     
     // Process each character
     while (*volumeStart) {
         if (*volumeStart == '-') {
             isNegative = true;
         }
         else if (*volumeStart == '.') {
             hasDecimal = true;
         }
         else if (*volumeStart >= '0' && *volumeStart <= '9') {
             if (!hasDecimal) {
                 result = (result * 10.0) + (*volumeStart - '0');
             }
             else {
                 decimal += (*volumeStart - '0') * decimalPlace;
                 decimalPlace *= 0.1;
             }
         }
         else if (*volumeStart != ' ' && *volumeStart != '\r' && *volumeStart != '\n') {
             // Skip invalid characters without breaking
             debugPrint("Skipping invalid character: ", (int)*volumeStart);
         }
         volumeStart++;
     }
     
     result += decimal;
     if (isNegative) result = -result;
     
     debugPrint("Parsed volume: ", result);
     return result;
 }
 
 bool sendPumpCommand(int pumpAddr) {
     byte retryCount = 0;
     bool success = false;
     
     while (retryCount < MAX_I2C_RETRIES && !success) {
         Wire.beginTransmission(pumpAddr);
         Wire.write(pumpCommand);
         byte error = Wire.endTransmission();
         
         if (error == 0) {
             delay(300);  // Required delay for EZO pump processing
             
             // Request response
             byte bytesRead = Wire.requestFrom(pumpAddr, 32);
             if (bytesRead > 0) {
                 // Clear response buffer
                 memset(pumpResponse, 0, sizeof(pumpResponse));
                 
                 // Read response
                 byte i = 0;
                 while (Wire.available() && i < 31) {
                     char c = Wire.read();
                     if (c == 0 || c == '\r' || c == '\n') break;
                     pumpResponse[i++] = c;
                 }
                 pumpResponse[i] = 0; // Ensure null termination
                 
                 debugPrint("Raw I2C response", pumpResponse);
                 success = true;
             }
         }
         
         if (!success) {
             retryCount++;
             delay(I2C_RETRY_DELAY * retryCount);
         }
     }
     
     if (!success) {
         strcpy(pumpResponse, "ERROR");
     }
     return success;
 }
 
 void updatePumpStatus(int pumpAddr) {
     // Skip if pump is not active
     if (pumps[pumpAddr].status == 0 || !pumps[pumpAddr].isDispensing) return;
     
     // Check if it's time to update this pump
     if (millis() - pumps[pumpAddr].lastCheck < PUMP_CHECK_INTERVAL) return;
     
     pumps[pumpAddr].lastCheck = millis();
     
     // Get current dispensed volume using R command
     strcpy(pumpCommand, "R");
     if (sendPumpCommand(pumpAddr)) {
         float currentVolume = parseVolume(pumpResponse);
         
         // Update pump status
         pumps[pumpAddr].currentVolume = currentVolume;
         
         // Determine if dispensing is complete based on volume and a small tolerance
         const float VOLUME_TOLERANCE = 0.1; // 0.1ml tolerance
         bool stillDispensing = (currentVolume + VOLUME_TOLERANCE) < pumps[pumpAddr].targetVolume;
         
         // Send status update in format the server expects
         Serial.print(F("Start;Update;NuteStat;"));
         Serial.print(pumpAddr);
         Serial.print(F(";"));
         Serial.print(stillDispensing ? "ON" : "OFF");
         Serial.print(F(";"));
         Serial.print(currentVolume, 2);  // Send with 2 decimal places
         Serial.print(F(";"));
         Serial.print(pumps[pumpAddr].targetVolume, 2);
         Serial.println(F(";end"));
         
         // If pump has reached target volume, update status
         if (!stillDispensing) {
             debugPrint("Pump Finished - Target: ", pumps[pumpAddr].targetVolume);
             debugPrint("Final Volume: ", currentVolume);
             
             // Issue stop command to ensure pump stops
             strcpy(pumpCommand, "X");
             sendPumpCommand(pumpAddr);
             
             // Update pump state
             pumps[pumpAddr].status = 0;
             pumps[pumpAddr].isDispensing = false;
             pumps[pumpAddr].targetVolume = 0;
         }
     }
 }
 
 void checkPumpVoltages() {
     unsigned long currentTime = millis();
     if (currentTime - lastVoltageCheck < VOLTAGE_CHECK_INTERVAL) return;
     
     debugPrint("Checking pump voltages", "");
     
     for (int i = 1; i < 9; i++) {
         // Only check voltage for inactive pumps
         if (pumps[i].status == 0 && !pumps[i].isDispensing) {
             strcpy(pumpCommand, "PV,?");
             if (sendPumpCommand(i)) {
                 char* voltStr = strchr(pumpResponse, ',');
                 if (voltStr) {
                     pumps[i].voltage = atof(voltStr + 1);
                 }
             }
         }
     }
     
     lastVoltageCheck = currentTime;
 }
 
 // Mock flow meter pulses for testing
 void updateMockFlowMeters() {
     if (!DEBUG_MODE) return;
     
     static unsigned long lastMockPulse = 0;
     const int MOCK_PULSE_INTERVAL = 20;  // 2ms interval for smooth simulation
     
     unsigned long currentTime = millis();
     if (currentTime - lastMockPulse >= MOCK_PULSE_INTERVAL) {
         lastMockPulse = currentTime;
         
         // Increment pulse count for active flow meters
         for (int i = 1; i < 3; i++) {
             if (flowMeters[i].status == 1) {
                 // Target: 10 gallons per minute = 2200 pulses per minute
                 // 2200 pulses/minute = ~37 pulses/second
                 // At 2ms intervals, need ~0.074 pulses per interval
                 // Accumulate fractional pulses over time
                 flowMeters[i].pulseCount += 77;  // This will give us ~37 pulses/second
                 
                 debugPrint("Mock pulses for flow meter ", i);
                 debugPrint("Current pulse count: ", (int)flowMeters[i].pulseCount);
             }
         }
     }
 }
 
 
 void updateAllDevices() {
     unsigned long currentTime = millis();
     
     // Only update at specified interval
     if (currentTime - lastStatusUpdate < STATUS_UPDATE_INTERVAL) return;
     lastStatusUpdate = currentTime;
     
     // Update mock flow meters in debug mode
     updateMockFlowMeters();
     
     // Update flow meters
     for (int i = 1; i < 3; i++) {
         updateFlowMeterStatus(i);
     }
     
     // Update active pumps
     for (int i = 1; i < 9; i++) {
         if (pumps[i].status == 1 || pumps[i].isDispensing) {
             updatePumpStatus(i);
         }
     }
     
     // Check pump voltages (will only run every 5 minutes)
     checkPumpVoltages();
 }
 
 // ================ Command Processing ================
 void processCommand() {
     // Read serial input
     if (!Serial.available()) return;
     
     int bytesRead = Serial.readBytesUntil('\n', commandBuffer, 99);
     if (bytesRead <= 0) {
         Serial.println(F("Start;Error;Bad read;end"));
         return;
     }
     commandBuffer[bytesRead] = 0;
     
     debugPrint("Got Command", commandBuffer);
     
     // Parse command
     char* token = strtok(commandBuffer, ";");
     if (!token || strcmp(token, "Start") != 0) return;
     
     // Get command type
     token = strtok(NULL, ";");
     if (!token) return;
     
     if (strcmp(token, "Pump") == 0) {
         processPumpCommand();
     }
     else if (strcmp(token, "Dispense") == 0) {
         processDispenseCommand();
     }
     else if (strcmp(token, "Cal") == 0) {
         processCalibrationCommand();
     }
     else if (strcmp(token, "Relay") == 0) {
         processRelayCommand();
     }
     else if (strcmp(token, "StartFlow") == 0) {
         processFlowCommand();
     }
 }
 
 void processPumpCommand() {
     char* addr = strtok(NULL, ";");
     char* cmd = strtok(NULL, ";");
     if (!addr || !cmd) return;
     
     int pumpAddr = atoi(addr);
     if (pumpAddr < 1 || pumpAddr > 8) return;
     
     strcpy(pumpCommand, cmd);
     if (sendPumpCommand(pumpAddr)) {
         Serial.print(F("Start;PumpResponse;"));
         Serial.print(pumpAddr);
         Serial.print(F(";"));
         Serial.print(pumpResponse);
         Serial.println(F(";end"));
     }
 }
 
 void processDispenseCommand() {
     char* addr = strtok(NULL, ";");
     char* amount = strtok(NULL, ";");
     if (!addr || !amount) return;
     
     int pumpAddr = atoi(addr);
     if (pumpAddr < 1 || pumpAddr > 8) return;
     
     float targetAmount = atof(amount);
     if (targetAmount <= 0) return;
     
     // Check if pump is already dispensing or just completed
     if (pumps[pumpAddr].isDispensing || pumps[pumpAddr].status == 1) {
         // Get current volume
         strcpy(pumpCommand, "R");
         if (sendPumpCommand(pumpAddr)) {
             float currentVolume = parseVolume(pumpResponse);
             
             // If pump has completed its previous dispense, don't restart
             if (abs(currentVolume - pumps[pumpAddr].targetVolume) < 0.1) {
                 debugPrint("Pump already completed dispense - Current: ", currentVolume);
                 debugPrint("Target: ", pumps[pumpAddr].targetVolume);
                 return;
             }
             
             // If dispense is in progress, update target if different
             if (currentVolume > 0.1) {  // More precise detection threshold
                 debugPrint("Dispense in progress - Current: ", currentVolume);
                 debugPrint("Target: ", targetAmount);
                 // Update target if different
                 if (abs(pumps[pumpAddr].targetVolume - targetAmount) > 0.1) {
                     pumps[pumpAddr].targetVolume = targetAmount;
                 }
                 return;
             }
             
             // If pump shows very low volume but was marked as dispensing,
             // it might have just completed. Check status and clear if needed.
             if (currentVolume < 0.1 && !pumps[pumpAddr].status) {
                 pumps[pumpAddr].isDispensing = false;
                 pumps[pumpAddr].targetVolume = 0;
             }
         }
     }
     
     // Only proceed if pump is truly idle
     if (!pumps[pumpAddr].isDispensing && !pumps[pumpAddr].status) {
         debugPrint("Starting new dispense - Target: ", targetAmount);
         
         // Set up pump for new dispense operation
         pumps[pumpAddr].targetVolume = targetAmount;
         pumps[pumpAddr].isDispensing = true;
         pumps[pumpAddr].currentVolume = 0;
         
         // Add required delay before sending dispense command
         delay(300);  // Required by EZO pump protocol
         
         sprintf(pumpCommand, "D,%s", amount);
         if (sendPumpCommand(pumpAddr)) {
             pumps[pumpAddr].status = 1;
             // Get initial volume reading
             strcpy(pumpCommand, "R");
             if (sendPumpCommand(pumpAddr)) {
                 float initialVolume = parseVolume(pumpResponse);
                 Serial.print(F("Start;Update;NuteStat;"));
                 Serial.print(pumpAddr);
                 Serial.print(F(";ON;"));
                 Serial.print(initialVolume);
                 Serial.print(F(";"));
                 Serial.print(targetAmount);
                 Serial.println(F(";end"));
             }
         }
     }
 }
 
 void processCalibrationCommand() {
     char* addr = strtok(NULL, ";");
     char* amount = strtok(NULL, ";");
     if (!addr || !amount) return;
     
     int pumpAddr = atoi(addr);
     if (pumpAddr < 1 || pumpAddr > 8) return;
     
     sprintf(pumpCommand, "Cal,%s", amount);
     if (sendPumpCommand(pumpAddr)) {
         Serial.print(F("Start;Update;NuteStat;"));
         Serial.print(pumpAddr);
         Serial.print(F(";Cal;"));
         Serial.print(amount);
         Serial.println(F(";end"));
     }
 }
 
 void processRelayCommand() {
     char* relayNum = strtok(NULL, ";");
     char* state = strtok(NULL, ";");
     if (!relayNum || !state) return;
     
     int relayNo = atoi(relayNum);
     bool newState = (strcmp(state, "ON") == 0);
     
     if (relayNo == 0) {  // All relays
         for (int i = 1; i < 17; i++) {
             digitalWrite(RELAY_PINS[i], !newState);  // Relays are active LOW
             relayStates[i] = newState;
         }
     }
     else if (relayNo > 0 && relayNo <= 16) {
         digitalWrite(RELAY_PINS[relayNo], !newState);
         relayStates[relayNo] = newState;
     }
     
     Serial.print(F("Start;RelayResponse;"));
     Serial.print(relayNo);
     Serial.print(F(";"));
     Serial.print(state);
     Serial.println(F(";end"));
 }
 
 void processFlowCommand() {
     char* flowNum = strtok(NULL, ";");
     char* gallons = strtok(NULL, ";");
     char* ppg = strtok(NULL, ";");
     if (!flowNum || !gallons) return;
     
     int flowNo = atoi(flowNum);
     if (flowNo < 1 || flowNo > 2) return;
     
     // Reset flow meter
     flowMeters[flowNo].pulseCount = 0;
     flowMeters[flowNo].currentGallons = 0;
     flowMeters[flowNo].targetGallons = atoi(gallons);
     if (ppg) flowMeters[flowNo].pulsesPerGallon = atoi(ppg);
     flowMeters[flowNo].status = 1;
     
     Serial.print(F("Start;Update;StartFlow;"));
     Serial.print(flowNum);
     Serial.print(F(";"));
     Serial.print(flowMeters[flowNo].targetGallons);
     Serial.println(F(";end"));
 }
 
 // ================ Setup & Main Loop ================
 void setup() {
     // Initialize communication
     Wire.begin();
     Serial.begin(9600);
     
     // Initialize flow meter pins and interrupts
     pinMode(FLOW_METER_PINS[1], INPUT_PULLUP);
     pinMode(FLOW_METER_PINS[2], INPUT_PULLUP);
     attachInterrupt(digitalPinToInterrupt(FLOW_METER_PINS[1]), handleFlow1, FALLING);
     attachInterrupt(digitalPinToInterrupt(FLOW_METER_PINS[2]), handleFlow2, FALLING);
     
     // Initialize relay pins (active LOW)
     for (int i = 1; i < 17; i++) {
         pinMode(RELAY_PINS[i], OUTPUT);
         digitalWrite(RELAY_PINS[i], HIGH);  // Start with all relays OFF
         relayStates[i] = false;
     }
     
     // Initialize flow meter data
     for (int i = 1; i < 3; i++) {
         flowMeters[i].pulseCount = 0;
         flowMeters[i].lastCount = 0;
         flowMeters[i].status = 0;
         flowMeters[i].targetGallons = 0;
         flowMeters[i].currentGallons = 0;
         flowMeters[i].pulsesPerGallon = (i == 1) ? 220 : 220;  // Default calibration
         flowMeters[i].lastUpdate = 0;
     }
     
     // Initialize pump data
     for (int i = 1; i < 9; i++) {
         memset(&pumps[i], 0, sizeof(PumpInfo));
         pumps[i].lastCheck = 0;
         pumps[i].isDispensing = false;
         
         // Get initial pump configuration
         // Check calibration status
         strcpy(pumpCommand, "Cal,?");
         if (sendPumpCommand(i)) {
             pumps[i].calibrated = (atoi(pumpResponse) > 0);
         }
         
         // Check voltage
         strcpy(pumpCommand, "PV,?");
         if (sendPumpCommand(i)) {
             char* voltStr = strchr(pumpResponse, ',');
             if (voltStr) {
                 pumps[i].voltage = atof(voltStr + 1);
             }
         }
         
         // Get pump name
         strcpy(pumpCommand, "Name,?");
         if (sendPumpCommand(i)) {
             char* nameStr = strchr(pumpResponse, ',');
             if (nameStr && strlen(nameStr) > 1) {
                 strncpy(pumps[i].name, nameStr + 1, 16);
                 pumps[i].name[16] = '\0';
             }
         }
     }
     
     // Print system information
     Serial.println(F("=========================================================="));
     Serial.println(F("   Indoor Growing Facility Feed Control System v2.0"));
     Serial.println(F("=========================================================="));
     Serial.println(F("\nSystem Configuration:"));
     Serial.println(F("- Flow Meters: 2 units"));
     Serial.println(F("- Nutrient Pumps: 8 units"));
     Serial.println(F("- Control Relays: 16 units"));
     Serial.println(F("\nSystem Status:"));
     
     // Print pump information
     for (int i = 1; i < 9; i++) {
         Serial.print(F("Pump "));
         Serial.print(i);
         Serial.print(F(": "));
         Serial.print(pumps[i].name[0] ? pumps[i].name : "Unnamed");
         Serial.print(F(" ("));
         Serial.print(pumps[i].calibrated ? "Calibrated" : "Uncalibrated");
         Serial.print(F(", "));
         Serial.print(pumps[i].voltage);
         Serial.println(F("V)"));
     }
     
     Serial.println(F("\nReady to accept commands."));
     Serial.println(F("==========================================================\n"));
 }
 
 void loop() {
     // Process any incoming commands
     processCommand();
     
     // Update device statuses
     updateAllDevices();
     
     // Small delay to prevent overwhelming serial/I2C
     delay(10);
 }