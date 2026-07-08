@echo off
cd /d "%~dp0"
echo Fon ve Hisse Analiz Sistemi baslatiliyor...
echo Tarayici birkac saniye icinde otomatik acilacak.
echo Bu pencereyi kapatirsaniz sunucu da durur.
streamlit run app.py
pause
