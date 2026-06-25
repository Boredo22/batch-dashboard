#include <Wire.h>

// I2C addresses for EZO circuits
#define PH_ADDRESS 99  // 0x63 in hexadecimal
#define EC_ADDRESS 100 // 0x64 in hexadecimal
#define I2C_TIMEOUT 1000 // 1 second timeout for I2C operations
#define MESSAGE_DELAY 500 // Longer delay between messages to prevent merging

char InBuf[100];
String ProbeStat = "OFF"; // Monitoring status: ON or OFF
char cr = '\n';
unsigned long lastReadingTime = 0;
bool readEcNext = true; // Alternating flag for EC and pH readings

void setup() {
  Serial.begin(115200);
  
  Wire.begin();
  Wire.setClock(100000); // Set I2C clock to 100kHz
  delay(1000); // Wait for the EZO circuits to boot up
  
  // Print banner similar to Mega - each line as a separate message
  Serial.println("==========================================================");
  Serial.flush();
  delay(100);
  
  Serial.println("Indoor EC/pH Monitoring System v1.0");
  Serial.flush();
  delay(100);
  
  Serial.println("==========================================================");
  Serial.flush();
  delay(100);
  
  Serial.println("System Configuration:");
  Serial.flush();
  delay(50);
  
  Serial.println("- pH Sensor: Atlas Scientific pH EZO");
  Serial.flush();
  delay(50);
  
  Serial.println("- EC Sensor: Atlas Scientific EC EZO");
  Serial.flush();
  delay(50);
  
  // Initialize pH sensor
  SendPhCommand("C,0"); // Disable continuous mode
  
  // Initialize EC sensor
  SendEcCommand("O,EC,1"); // Enable EC output
  SendEcCommand("O,TDS,0"); // Disable TDS output
  SendEcCommand("O,SG,0");  // Disable SG output
  SendEcCommand("O,S,0");   // Disable salinity output

  Serial.println("System Status: Ready to monitor");
  Serial.flush();
  delay(50);
  
  Serial.println("==========================================================");
  Serial.flush();
  delay(MESSAGE_DELAY);
}

void loop() {
  // Check for incoming serial commands
  if (Serial.available()) {
    delay(100); // Small delay to ensure we have the complete command
    int resp = Serial.readBytesUntil(cr, InBuf, 99);
    if (resp > 0) {
      InBuf[resp] = 0; // Null terminate the string
      
      // Parse the command
      char *Start = strtok(InBuf, ";");
      if (strcmp(Start, "Start") == 0) {
        char *Command = strtok(NULL, ";");
        
        // EcPh command - Start;EcPh;ON/OFF;end
        if (strcmp(Command, "EcPh") == 0) {
          char *Stat = strtok(NULL, ";");
          if (strcmp(Stat, "ON") == 0) {
            ProbeStat = "ON";
            SendStatusMessage("ON");
          } else if (strcmp(Stat, "OFF") == 0) {
            ProbeStat = "OFF";
            SendStatusMessage("OFF");
          }
        }
        // pH Calibration command
        else if (strcmp(Command, "PhCal") == 0) {
          char *CalType = strtok(NULL, ";");
          char *CalValue = strtok(NULL, ";");
          
          if (strcmp(CalType, "mid") == 0) {
            String calCmd = "Cal,mid," + String(CalValue);
            String response = SendPhCommand(calCmd.c_str());
            SendCompleteMessage("Update;PhCal;mid;" + response);
          }
          else if (strcmp(CalType, "low") == 0) {
            String calCmd = "Cal,low," + String(CalValue);
            String response = SendPhCommand(calCmd.c_str());
            SendCompleteMessage("Update;PhCal;low;" + response);
          }
          else if (strcmp(CalType, "high") == 0) {
            String calCmd = "Cal,high," + String(CalValue);
            String response = SendPhCommand(calCmd.c_str());
            SendCompleteMessage("Update;PhCal;high;" + response);
          }
          else if (strcmp(CalType, "clear") == 0) {
            String response = SendPhCommand("Cal,clear");
            SendCompleteMessage("Update;PhCal;clear;" + response);
          }
        }
        // EC Calibration command
        else if (strcmp(Command, "EcCal") == 0) {
          char *CalType = strtok(NULL, ";");
          char *CalValue = strtok(NULL, ";");
          
          if (strcmp(CalType, "dry") == 0) {
            String response = SendEcCommand("Cal,dry");
            SendCompleteMessage("Update;EcCal;dry;" + response);
          }
          else if (strcmp(CalType, "low") == 0 ||
                   strcmp(CalType, "one") == 0 ||
                   strcmp(CalType, "single") == 0) {
            String calCmd = "Cal," + String(CalValue);
            String response = SendEcCommand(calCmd.c_str());
            SendCompleteMessage("Update;EcCal;" + String(CalValue) + ";" + response);
          }
          else if (strcmp(CalType, "clear") == 0) {
            String response = SendEcCommand("Cal,clear");
            SendCompleteMessage("Update;EcCal;clear;" + response);
          }
        }
      }
    }
  }

  // If monitoring is enabled, read the sensors - alternating EC and pH with longer interval
  if (ProbeStat == "ON") {
    unsigned long currentTime = millis();
    if (currentTime - lastReadingTime >= 2000) { // 2 second interval to reduce frequency
      lastReadingTime = currentTime;
      
      if (readEcNext) {
        // Read EC value
        String EcReading = SendEcCommand("R");
        if (EcReading.length() > 0) {
          SendEcMessage(EcReading);
        }
        
        // Wait a bit before potentially reading pH
        delay(MESSAGE_DELAY);
      } else {
        // Read pH value
        String pHReading = SendPhCommand("R");
        if (pHReading.length() > 0) {
          SendPhMessage(pHReading);
        }
        
        // Wait a bit before potentially reading EC
        delay(MESSAGE_DELAY);
      }
      
      // Toggle flag to alternate between EC and pH readings
      readEcNext = !readEcNext;
    }
  }
}

// Send EC reading message - keeping original format for backend compatibility
void SendEcMessage(String value) {
  // Create a simple, clean EC update message
  String message = "Start;Update;Ec;" + value + ";end";
  
  // Send it all at once, ensure it's flushed, and add a significant delay
  Serial.println(message);
  Serial.flush(); // Wait for transmission to complete
  delay(MESSAGE_DELAY); // Longer delay to ensure separation
}

// Send pH reading message - keeping original format for backend compatibility
void SendPhMessage(String value) {
  // Create a simple, clean pH update message
  String message = "Start;Update;Ph;" + value + ";end";
  
  // Send it all at once, ensure it's flushed, and add a significant delay
  Serial.println(message);
  Serial.flush(); // Wait for transmission to complete
  delay(MESSAGE_DELAY); // Longer delay to ensure separation
}

// Send status message - keeping original format for backend compatibility
void SendStatusMessage(String status) {
  String message = "Start;Update;EcPhStatus;" + status + ";end";
  Serial.println(message);
  Serial.flush();
  delay(MESSAGE_DELAY);
}

// Helper function to send complete and properly formatted messages
void SendCompleteMessage(String content) {
  // Create a complete message
  String message = "Start;" + content + ";end";
  
  // Send it all at once, ensure it's flushed, and add a significant delay
  Serial.println(message);
  Serial.flush();
  delay(MESSAGE_DELAY);
}

// Send a command to the pH EZO circuit and return the response
String SendPhCommand(const char* command) {
  Wire.beginTransmission(PH_ADDRESS);
  Wire.write(command);
  byte error = Wire.endTransmission();
  
  if (error != 0) {
    return "error";
  }
  
  delay(900); // Wait for EZO circuit to process command
  Wire.requestFrom(PH_ADDRESS, 20, 1);
  
  unsigned long startTime = millis();
  while (Wire.available() == 0) {
    if (millis() - startTime > I2C_TIMEOUT) {
      return "";
    }
  }
  
  String response = "";
  while (Wire.available()) {
    char c = Wire.read();
    if (c == 0) break;
    if (c > 1) response += c;
  }
  response.trim();
  return response;
}

// Send a command to the EC EZO circuit and return the response
String SendEcCommand(const char* command) {
  Wire.beginTransmission(EC_ADDRESS);
  Wire.write(command);
  byte error = Wire.endTransmission();
  
  if (error != 0) {
    return "error";
  }
  
  delay(900); // Wait for EZO circuit to process command
  Wire.requestFrom(EC_ADDRESS, 20, 1);
  
  unsigned long startTime = millis();
  while (Wire.available() == 0) {
    if (millis() - startTime > I2C_TIMEOUT) {
      return "";
    }
  }
  
  String response = "";
  while (Wire.available()) {
    char c = Wire.read();
    if (c == 0) break;
    if (c > 1) response += c;
  }
  response.trim();
  return response;
}