#include <PZEM004Tv30.h>
PZEM004Tv30 pzem(Serial2, 16, 17, PZEM_DEFAULT_ADDR);
void setup() {
  Serial.begin(115200);
  delay(3000);
  pzem.setAddress(0x01); // mude para 0x02 e 0x03 nos outros
  Serial.printf("Endereço configurado: 0x%02X\n", pzem.readAddress());
}
void loop() {}