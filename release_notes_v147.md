## CookieRun Classic Bot v1.4.7

- แก้บั๊กกด Start แล้วบอทกดปุ่ม "ออกจากเกม" ทันที
- สาเหตุ: Stage `GAME_START` กับ `GAME_RELAY` ใช้ region ตรวจจับเดียวกัน ทำให้ template ของ Relay ไป match กับหน้าจอเริ่มเกม บอทจึงเข้าใจผิดว่าเป็นโหมด Relay แล้วกด Quit
- เพิ่ม safety guard ใน `quick_exit_after_cookie_relay()` ตรวจสอบก่อนกด Quit ว่าเกมกำลังวิ่งจริง (ไม่อยู่บนหน้าจอเริ่มเกมหรือหน้า Main Menu) ถ้ายังไม่เริ่มวิ่งจะยกเลิกการออกจากเกมอย่างปลอดภัย
- ป้องกันการออกจากเกมโดยไม่ตั้งใจเมื่อเปิดใช้ Cookie Relay + Relay Quick Exit

ความละเอียดภายใน LDPlayer ที่รองรับ: **1280×720**

SHA-256 (`CookieRunClassicBot.exe`):
`CE695713844F10768378CEFB0B5AB9D28E14D64B8ECF26FB8604EB7D87ACECC9`
