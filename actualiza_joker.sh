#!/bin/sh

cd ~/CICAN/Codificación/src
rsync -av . cican@joker:/home/compartido/src
#scp -r * cican@joker:/home/compartido/src
ssh root@joker "chown -R nobody:cican /home/compartido/*"
ssh root@joker "chmod -R g+rw /home/compartido/*"
ssh root@joker "find /home/compartido -type d -exec chmod a+x '{}' \;"
ssh root@joker "cp -f /home/compartido/src/framework/ginn.conf.joker /home/compartido/src/framework/ginn.conf"
cd -
