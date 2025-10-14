#!/data/data/com.termux/files/usr/bin/bash
cd ~/RaSvet/iskin_ra

while inotifywait -r -e modify,create,delete ./; do
  bash ra_push.sh
done
