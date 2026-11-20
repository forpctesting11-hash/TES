TES — yangi loyiha

1. GitHub'da eski loyiha fayllarini o'rniga shu papkadagi fayllarni yuklang:
   app.py
   requirements.txt
   render.yaml

2. Render'da:
   Build Command: pip install -r requirements.txt
   Start Command: gunicorn app:app

3. Render Environment Variables bo'limida SECRET_KEY yarating (render.yaml buni avtomatik sozlaydi).

Eslatma:
- SQLite ma'lumotlar bazasi `tes.db` birinchi ishga tushganda avtomatik yaratiladi.
- Render bepul xizmatida disk doimiy saqlanishi kafolatlanmaydi. Foydalanuvchi hisoblari va writing javoblarini uzoq muddat saqlash uchun keyin PostgreSQL ulash tavsiya etiladi.
- Speaking yozuvi brauzerda qoladi, serverga yuklanmaydi.
- IELTS bo'limi hozircha keyingi bosqich uchun joy sifatida turibdi.
