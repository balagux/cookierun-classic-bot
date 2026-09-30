# CookieRun Classic Bot v1.4.16

Release นี้แก้ Anti-Bot solver จากปัญหาที่พบระหว่างใช้งานจริงเวลา `Find the jumping card!` แสดงขึ้น แต่ solver รุ่นก่อนยังจัดอันดับการ์ดแบบ sliding และกด candidate เดิมซ้ำจน fail-safe หยุดบอท

## Anti-Bot fixes

- อ่านชนิดคำสั่งจากส่วนคำที่แตกต่างใน Anti-Bot header เพื่อแยก `jumping` / `sliding`
- Align header ก่อน แล้วเทียบเฉพาะบริเวณคำ `jumping` เพื่อลด false match จากข้อความส่วนที่เหมือนกัน
- `jumping` เรียง candidate จาก slide-score ต่ำไปสูง
- `sliding` เรียง candidate จาก slide-score สูงไปต่ำ
- ลอง candidate คนละใบสูงสุด 3 อันดับ แทนการกดใบเดิมซ้ำ 3 ครั้ง
- หากยังไม่ผ่านหลัง 3 candidate จะหยุดอย่างปลอดภัยเหมือนเดิม
- เมื่อ fail-safe ทำงาน จะบันทึก debug screenshot อัตโนมัติเพื่อให้วิเคราะห์ challenge จริงได้
- คง guard ที่ป้องกัน Daily Check-in / reward screens ถูกตรวจผิดเป็น Anti-Bot

## Validation

- Anti-Bot targeted tests: **10 passed**
- Full automated suite: **168 passed + 12 subtests**
- Python compile gate: passed
- Packaged OCR runtime self-test: passed (`1,198`, confidence `0.99994`)
- EXE SHA-256: `74FF8380F32960A0706B19BD9B38DE2CA5A4464F4048AE27719F4DBB53B4B8F8`
- Installer SHA-256: `CAE660CF0D829EFDAE84E4E39049F2AF7766A5A7EF3551A6B82F69A4E459DF1C`

> หมายเหตุ: LDPlayer ไม่ได้เปิดอยู่ในช่วง rebuild รอบนี้ จึงไม่มีการบังคับให้เกิด Anti-Bot challenge ใหม่แบบ live; solver ถูกตรวจด้วย template จริง, synthetic pose layouts, historical failure pattern และ full regression suite
