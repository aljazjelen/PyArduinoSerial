// Serial with PC
String incomingMsg;

// Periodic Call time definition
float lastTime = 0;
int interval = 10; // miliseconds!

// Peripherals and Devices
byte LED = 13;
byte Pot = A2;


// I suggest to leave this method alone. It works as intended
void PyArduinoSerialWrite(int* data1){
  byte* byteData1 = (byte*)(data1);
  Serial.write(byteData1, 2);
}

// Modify Only the parsing part. Or make a function call to your custom implementation.
void PyArduinoSerialRead(){
  // serial read section
  while (Serial.available()){
    if (Serial.available() >0){
      char c = Serial.read();  //gets one byte from serial buffer
      incomingMsg += c; //makes the string readString
      delay(1); //(not needed on Teensy or more powerful micros then Nano/Uno)
    }}
    
  if (incomingMsg.length() > 1){ 
    
    String firstpackage = getValue(incomingMsg, '$', 0);
    
    String firstpackage_id = getValue(firstpackage, ':', 0);
    String firstpackage_value = getValue(firstpackage, ':', 1);
    // TODO add second, third, etc... package, if you expect more than one package at the time

    // TODO Below here is your "decoding". Let Arduino perform specific actions, requested by PC, based on serial content
    if (firstpackage_id.equals("Pin13")){
      if (firstpackage_value.equals("1")) digitalWrite(LED,HIGH);
      if (firstpackage_value.equals("0")) digitalWrite(LED,LOW);
    }
    incomingMsg = "";
  }
  
  //PyArduinoSerialWrite(&toSend);
  Serial.flush(); //flush it
}

// I suggest to leave this method alone. It works as intended
String getValue(String data, char separator, int index){
  int found = 0;
  int strIndex[] = { 0, -1 };
  int maxIndex = data.length() - 1;
  
  for (int i = 0; i <= maxIndex && found <= index; i++) {
      if (data.charAt(i) == separator || i == maxIndex) {
          found++;
          strIndex[0] = strIndex[1] + 1;
          strIndex[1] = (i == maxIndex) ? i+1 : i;
      }
  }
  return found > index ? data.substring(strIndex[0], strIndex[1]) : "";
}
 
void setup() {
  // put your setup code here, to run once:
  Serial.begin(38400);
  digitalWrite(LED,LOW);
  pinMode(Pot,INPUT);
}

void loop() {
  // put your main code here, to run repeatedly:
  float currentTime = millis();
  if ((currentTime - lastTime) <= interval){
    PyArduinoSerialRead(); // read when write is not needed. Since reading might block due to delay (not needed on Teensy or more powerful micros then Nano/Uno)
  }else{
    int toSend = analogRead(Pot);
    PyArduinoSerialWrite(&toSend);
    lastTime = currentTime;    
  }

}
