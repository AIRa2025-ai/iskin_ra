#!/data/data/com.termux/files/usr/bin/bash

cd ~/RaSvet/iskin_ra

if [ -n "$(git status --porcelain)" ]; then
  git add .
  COMMIT_MSG="✨ Автообновление Ра: $(date +'%Y-%m-%d %H:%M:%S')"
  git commit -m "$COMMIT_MSG"
  git push origin main
else
  echo "✅ Всё чисто. Нет изменений."
fi
