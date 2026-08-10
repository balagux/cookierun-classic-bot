# CookieRun Classic Bot

โปรแกรมช่วยจัดการรอบ CookieRun Classic บน Windows ผ่าน ADB และ OpenCV โดยเน้นเมนูที่จำเป็น:
เชื่อมต่อเกม เลือกซื้อไอเทม และสั่ง START/STOP บอทจากหน้าต่างขนาดกะทัดรัด

> เวอร์ชันปัจจุบัน: **1.4.2**
>
> โปรแกรมนี้เป็นโครงการทดลองด้าน Automation และ Computer Vision การใช้งานกับบัญชีจริง
> อาจขัดกับข้อกำหนดของเกม ผู้ใช้ต้องรับผิดชอบความเสี่ยงด้วยตนเอง

## รุ่น 1.4.2

- เพิ่มปุ่ม **ส่งหัวใจ** สำหรับไล่กดซองหัวใจสีเขียวในรายชื่อเพื่อนทีละคน
- จับภาพใหม่ทุกครั้งก่อนเลือกคนถัดไป ไม่ใช้พิกัดจากภาพเก่าซ้ำ
- รอให้พบปุ่ม Confirm จริงก่อนกด และจัดการหน้าต่างแจ้งว่าส่งสำเร็จก่อนทำรายการต่อ
- แยกการส่งหัวใจออกจาก START BOT จึงไม่ซื้อไอเทม ไม่เริ่มรอบ และไม่รีเซ็ตสถิติ Coins/EXP
- จำกัดจำนวนครั้งที่เลื่อนและรอหน้าจอ หากเปิดผิดหน้าจะหยุดพร้อมแจ้งแทนการคลิกต่อ

## รุ่น 1.4.1

- เมื่อเปลี่ยน Desired Random Boost จะเอาติ๊กตัวเก่าออกและยืนยันให้เหลือตัวใหม่เพียงตัวเดียว
- เพิ่มสวิตช์รับรางวัล Relic อัตโนมัติ ปิดได้เมื่อต้องการดองชิ้นส่วน
- ย่อหน้าต่างโปรแกรมและเหลือเฉพาะส่วนควบคุมที่จำเป็น
- นำหน้า Record, Profile Gallery และระบบเลือก Recorder ออกจาก GUI
- คงระบบซื้อ Fast Start, Cookie Relay และ Desired Random Boost
- คงปุ่ม START BOT / STOP BOT, จำนวนรอบ และสถิติ Coins/EXP
- ปรับการเริ่มเกมให้ทนต่อกรณี `com.devsisters.crg` เปิดไม่สำเร็จ โดยลองเชื่อมต่อใหม่อย่างปลอดภัย

## โปรแกรมทำอะไรได้บ้าง

- เชื่อมต่อ LDPlayer/Android ผ่าน ADB โดยไม่เปิดหน้าต่าง CMD รบกวน
- เริ่มจาก Main Menu แล้วเข้าเมนูซื้อไอเทมตามที่เลือก
- ซื้อ Fast Start และ Cookie Relay ตามเงื่อนไขในเกม
- เลือก Desired Random Boost และยืนยันตัวเลือกก่อนซื้อ
- กด Play และตรวจหน้าจอระหว่างรอบ
- กด Confirm, Result และหน้ารางวัลที่รองรับ
- รับ Mystery Box, Level Up, Daily Reward, Relic และรางวัลหลังจบเกม
- ตรวจ Anti-Bot, Connection Lost และ Inactive พร้อมพยายามกู้สถานะ
- OCR อ่าน Coins/EXP หลังค่าบนหน้า Result หยุดนับ
- สรุปจำนวนรอบ ยอดรวม ค่าเฉลี่ย และเวลาทำงานของ Session
- ส่งหัวใจให้เพื่อนจากหน้า Friends leaderboard ทีละคนด้วยปุ่มแยก

รุ่นนี้ไม่มีเมนู Record/Replay ใน GUI และไม่อัดหรือเล่นจังหวะ W/S ให้ ผู้ใช้ควบคุมการเล่น
หรือใช้ระบบภายนอกของ Emulator ได้เอง โดยบอทยังคงดูแลเมนู ไอเทม ผลรอบ และรางวัลตามเดิม

## ดาวน์โหลดสำหรับ Windows

ดาวน์โหลด `CookieRunClassicBot-Setup.exe` จากหน้า
[GitHub Releases](../../releases/latest) แล้วติดตั้งได้โดยไม่ต้องลง Python

ตัวติดตั้งรองรับภาษาไทย/อังกฤษ ติดตั้งแบบรายผู้ใช้ ไม่ต้องใช้สิทธิ์ Administrator และมีตัวถอนการติดตั้ง

## สิ่งที่ต้องมี

- Windows 10 หรือ Windows 11 แบบ 64-bit
- LDPlayer หรือ Android Emulator ที่เปิด ADB ได้
- ความละเอียดภายใน Emulator **1280×720 เท่านั้น**
- Android Platform Tools (ADB)

โปรแกรมค้นหา `adb.exe` ตามลำดับนี้:

1. `platform-tools\adb.exe` ที่อยู่ข้างโปรแกรม
2. `D:\platform-tools-latest-windows\platform-tools\adb.exe`
3. ADB ที่อยู่ในตัวแปร `PATH`

## เริ่มใช้งาน

1. ตั้งความละเอียดภายใน LDPlayer เป็น `1280×720`
2. เปิด ADB debugging ของ LDPlayer
3. เปิด CookieRun Classic และค้างไว้ที่ Main Menu
4. เปิด CookieRun Classic Bot
5. กรอก IP/Host และ Port เช่น `127.0.0.1:5556`
6. กด **ทดสอบ ADB** และตรวจว่ารายงานความละเอียด `1280×720`
7. เลือก Fast Start, Cookie Relay หรือ Random Boost ที่ต้องการ
8. เปิด **รับ Relic อัตโนมัติ** เมื่อต้องการกด Get/Claim หรือปิดเพื่อดองชิ้นส่วน
9. กำหนดจำนวนรอบ โดย `0` หมายถึงเล่นต่อเนื่อง
10. กด **START BOT** และกด **STOP BOT** เมื่อต้องการหยุด

เมื่อกด START BOT โปรแกรมจะรีเซ็ตจำนวนรอบ Coins/EXP รวม ค่าเฉลี่ย และเวลาของ Session ใหม่

## ส่งหัวใจให้เพื่อน

1. กลับมาที่ Main Menu และเปิดแท็บ **Friends** ให้เห็นรายชื่อกับปุ่มซองหัวใจสีเขียว
2. กดปุ่ม **ส่งหัวใจ** ในแถบ RUN CONTROL
3. โปรแกรมจะเริ่มจากอันดับบนสุด กดทีละคน รอ Confirm และเลื่อนลงจนถึงท้ายรายชื่อ
4. ดูจำนวนที่ส่งสำเร็จได้จาก Live Activity และกด **STOP** ได้ตลอดเวลา

โหมดนี้ไม่ใช้ตัวเลือก Fast Start, Cookie Relay, Random Boost หรือจำนวนรอบ และไม่เปลี่ยนสถิติ
Coins/EXP ของ Session เดิม หากไม่ได้อยู่หน้า Friends โปรแกรมจะหยุดโดยไม่คลิกส่วนอื่นของเกม

## ตัวเลือกซื้อไอเทม

### Fast Start

เมื่อเปิดตัวเลือกนี้ บอทจะซื้อและใช้ Fast Start ก่อนกด Play

### Cookie Relay

บอทจะซื้อ Cookie Relay เมื่อของเหลือ `0` และใช้ระบบ Relay/ออกจากรอบเร็วตาม Stage ที่ตรวจพบ

### Desired Random Boost

รองรับตัวเลือกต่อไปนี้:

1. Double Coins
2. +15% Score Bonus
3. -15% HP Drain
4. Revive Once with 80 HP
5. 70% Crush Chance
6. +17% Base Speed
7. Gold Coin Magic
8. -30% Collision Damage
9. +20% HP from Potions
10. Magnetic Aura
11. 2 Pit Lifts

หลังเปิด Multi-Buy บอทจะเลือก Boost และตรวจยืนยันเครื่องหมายถูกซ้ำสูงสุด 3 ครั้ง
หากยืนยันตัวเลือกไม่ได้จะปิดหน้าต่างโดยไม่กดซื้อ

เมื่อเปลี่ยน Boost ใน GUI บอทจะยกเลิกเครื่องหมายถูกของตัวเลือกเดิมก่อน แล้วจึงเลือกตัวใหม่
และจะกด Multi-Buy ต่อเมื่อยืนยันได้ว่าเหลือเครื่องหมายถูกเพียงรายการเดียว

### Relic Reward

- เปิดสวิตช์: กด `Get!` และรับรางวัล Relic อัตโนมัติเหมือนเดิม
- ปิดสวิตช์: ไม่กด `Get!` และเก็บชิ้นส่วนที่ครบไว้
- หากเปิดบอทตอนหน้ารับ Relic แสดงอยู่ โหมดดองจะกดเฉพาะ `X` โดยไม่กด Claim

ค่าที่เปลี่ยนใน GUI จะมีผลเมื่อกด START BOT ครั้งถัดไป

## Coins และ EXP

OCR ทำงานภายในเครื่องด้วย RapidOCR/ONNX Runtime ไม่มีการส่งภาพไปเซิร์ฟเวอร์ภายนอก
เมื่อพบหน้า Result โปรแกรมจะรอให้ตัวเลขหยุดนับ อ่านซ้ำจนได้ค่าคงที่ แล้วจึงรวมผลเข้า Session

หน้าสรุปแสดงข้อมูลต่อไปนี้:

- จำนวนรอบที่เริ่มและจบสำเร็จ
- Coins รวมและค่าเฉลี่ยต่อรอบ
- EXP รวมและค่าเฉลี่ยต่อรอบ
- เวลาที่บอททำงานใน Session

รอบที่หลุดกลับ Main Menu ก่อนถึง Result จะไม่นำมาคิดยอดรวมหรือค่าเฉลี่ย

## แก้ปัญหาเบื้องต้น

### `Failed to start com.devsisters.crg after 5 attempts`

1. ปิดโปรแกรมและ LDPlayer ให้หมด
2. เปิด LDPlayer ใหม่และรอจน Android เข้าหน้าหลัก
3. เปิด ADB debugging แล้วตรวจ Port ของ Instance
4. เปิดโปรแกรมและกด **ทดสอบ ADB** ก่อน START BOT
5. หากยังไม่สำเร็จ ให้ตรวจว่า Port ไม่ถูก Instance อื่นใช้ และลอง Restart ADB/LDPlayer

### เชื่อมต่อ ADB ไม่ได้

- ตรวจ IP/Port เช่น `127.0.0.1:5556`
- ตรวจว่า `adb.exe` อยู่ที่ `D:\platform-tools-latest-windows\platform-tools\adb.exe`
- ตรวจ Firewall และการตั้งค่า ADB debugging ใน Emulator
- หากใช้หลาย Instance ให้เลือก Port ของหน้าต่างที่เปิดเกมอยู่

### โปรแกรมแจ้งความละเอียดไม่รองรับ

Coordinate และ Template ของเกมรองรับเฉพาะ `1280×720` การย่อหน้าต่าง GUI บนจอคอม
ไม่เปลี่ยนข้อกำหนดความละเอียดภายใน Emulator

### OCR อ่าน Coins/EXP ไม่ได้

- อย่ากด OK บนหน้า Result ก่อนตัวเลขหยุดนับ
- ตรวจว่าหน้าจอเกมเป็น 1280×720 และไม่มีหน้าต่างอื่นบัง
- ดูภาพวิเคราะห์ใน `debug_screens/`

## รันจาก Source Code

```powershell
git clone https://github.com/balagux/cookierun-classic-bot.git
cd cookierun-classic-bot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

หรือดับเบิลคลิก `start_gui.bat`

## สร้าง EXE และ Installer

```powershell
pip install -r requirements-build.txt
.\build_exe.bat
.\build_installer.bat
```

ไฟล์ที่ได้:

- `dist\CookieRunClassicBot.exe`
- `installer\CookieRunClassicBot-Setup.exe`

การสร้าง Installer ต้องติดตั้ง [Inno Setup 6](https://jrsoftware.org/isinfo.php)

## โครงสร้างโปรเจกต์

```text
├── main.py                จุดเริ่มต้นโปรแกรม
├── modern_gui.py          หน้าต่างโปรแกรม
├── gui.py                 Logic ของ GUI และสถิติ Session
├── bot.py                 Game loop และการจัดการ Stage
├── actions.py             คำสั่งกดปุ่ม ซื้อของ และรับรางวัล
├── adb.py                 การเชื่อมต่อ จับภาพ และส่งอินพุตผ่าน ADB
├── detection.py           OpenCV template matching
├── result_ocr.py          OCR อ่าน Coins/EXP
├── config.py              Template, Region, Coordinate และ Timing
├── runtime_paths.py       Path สำหรับ Source/EXE
├── templates/             ภาพ Template ที่ความละเอียด 1280×720
└── tests/                 Automated tests
```

## หมายเหตุ

- UI หรือภาพในเกมเปลี่ยนอาจทำให้ต้องถ่าย Template ใหม่
- Timing อาจต่างกันตามสเปกเครื่องและอาการ Lag ของ Emulator
- โปรเจกต์ยังไม่ได้ระบุสัญญาอนุญาต (License) สำหรับการนำไปแจกจ่ายต่อ
