#!/bin/sh
set -e
echo "== insJaY: memasang runtime =="

if ! command -v python3 >/dev/null 2>&1; then
    if command -v pkg >/dev/null 2>&1; then
        pkg install -y python
    elif command -v apt >/dev/null 2>&1; then
        apt update && apt install -y python3 python3-pip
    elif command -v dnf >/dev/null 2>&1; then
        dnf install -y python3 python3-pip
    else
        echo "Python 3 belum ada dan pemasang paket tidak dikenali."
        exit 1
    fi
fi

if python3 -m pip --version >/dev/null 2>&1; then
    python3 -m pip install --quiet --upgrade .
else
    echo "pip belum ada; memasang pip ..."
    python3 -m ensurepip --upgrade >/dev/null 2>&1 || true
    python3 -m pip install --quiet --upgrade .
fi

echo
echo "Selesai. Coba jalankan:"
echo "  insjay contoh/halo.Jay"
echo "  insjay contoh/scraper_contoh.Jay https://api.github.com/repos/INsITdeveloper/insJaY"
