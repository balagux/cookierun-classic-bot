# CookieRun Classic Bot v1.4.15

Release นี้รวมฟีเจอร์ล่าสุดจาก v1.4.14 (Telegram notifications, News popup recovery และ Mailbox Hearts) เข้ากับชุด reliability/stress fixes ที่ทดสอบบน LDPlayer และเกมจริง

## Highlights

- เพิ่ม START preflight: ตรวจ ADB, ความละเอียด 1280×720 และ Main Menu ก่อนเริ่มบอท
- ปรับ GUI/CustomTkinter ให้ Start/Stop, Quick Jump และ Bot Health ใช้งานได้ดีในหน้าต่าง 720×500
- เพิ่ม fallback ไปยัง ADB ที่มากับ LDPlayer 14/9 เมื่อ standalone platform-tools หรือ PATH ไม่มี ADB
- ใส่ timeout 10 วินาทีให้คำสั่ง ADB เพื่อป้องกัน worker แขวนเมื่อ emulator/ADB ไม่ตอบสนอง
- แก้ STOP ของ PyInstaller one-file ให้ปิดทั้ง process tree ไม่ทิ้ง Python child ทำงานเบื้องหลัง
- แก้ Main Menu/Friends false-positive ที่เคยกด BACK จนเปิด Exit dialog
- ป้องกัน Cookie Relay ถูกใช้ซ้ำในรอบเดียว
- ป้องกัน Mystery Box frame ซ้ำจากการนับหรือสร้าง debug screenshot ซ้ำ
- แก้ Daily Check-in ถูก Anti-Bot heuristic ตรวจผิด โดยให้ Daily reward templates ชนะ broad heuristic
- เพิ่ม Anti-Bot fail-safe: หากลองครบ 3 ครั้งแล้วยังไม่ผ่าน บอทหยุดพร้อม error แทนการคลิกไม่จำกัด
- เพิ่ม regression tests สำหรับ GUI health/layout, START preflight, ADB recovery, Anti-Bot false-positive และ process-tree shutdown
- คง Telegram notifications, News popup recovery และ Mailbox Hearts จาก v1.4.14 ไว้ครบ

## Real-game stress validation

- เกมจริงครบ **10 gameplay rounds**
- Coins รวม: **166,905**
- EXP รวม: **98,271**
- เวลาเฉลี่ย: **238.24 วินาที/รอบ**
- Mystery Box รวม: **wood 13 / silver 2 / gold 4 / rainbow 3**
- 9 รอบแรกไม่มี Connection Lost, screen-capture failure หรือ critical gameplay runtime error
- Stress test พบ Daily Check-in → Anti-Bot false-positive ก่อนรอบที่ 10; หลังแก้แล้ว installed EXE ผ่าน `DAILY_CHECKIN → DAILY_TREASURE → MAINMENU → GAME_COMPLETE` และจบรอบด้วย exit code 0
- Memory/process monitoring: **124 samples (~62 นาที)**, PyInstaller process count คงที่ 2, working set 17.5–169.3 MB และไม่พบแนวโน้ม memory leak แบบโตต่อเนื่อง

## Final release validation

- Automated tests: **164 passed + 12 subtests passed**
- LDPlayer resolution: **1280×720**
- Installed EXE hash ตรงกับ `dist` แบบ byte-for-byte
- EXE SHA-256: `5DFDA25D94F39AB1A682E571B114E4B4D9B1FDEAA132317D699940F51802519F`
- Installer SHA-256: `4F73AD555BC0D581747CC0BCA0F9F32391CC100A0A28C46D0E187964730AD89C`
