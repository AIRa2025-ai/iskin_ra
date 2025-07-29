#!/data/data/com.termux/files/usr/bin/bash

cd ~/RaSvet/iskin_ra || exit 1

# Сообщение по вдохновению
MESSAGE="${1:-🔥 АвтоПубликация Ра — свет несётся в GitHub}"

git add .
git commit -m "$MESSAGE"
git push origin main