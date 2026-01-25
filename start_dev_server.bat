@echo off
echo === Mirai Knowledge Systems Development Server ===
set MKS_JWT_SECRET_KEY=dev-secret-key-for-testing-only-32chars-minimum
set MKS_USE_JSON=true
set MKS_USE_POSTGRESQL=false
set MKS_ENV=development
set MKS_DEBUG=true
set MKS_BRAVE_SEARCH_API_KEY=BSApolE-Bg7mQKmgLXOMUP-JscMZwMD
set MKS_DISABLE_EXTERNAL_NOTIFICATIONS=true
cd /d Z:\Mirai-Knowledge-Systems\backend
set MKS_HTTP_PORT=5200
set MKS_HTTPS_PORT=5243
echo Starting Flask server on port 5200...
python app_v2.py
