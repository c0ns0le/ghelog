#! /bin/bash

for i in exceptions gitauth audit unicorn auth; do
	ssh admin@ghe.spotify.net "tail -f /var/log/github/$i.log" | python ~/src/ghelog/bin/awesomeparsethingiethatiscool.py ghe.spotify.net $i >$i.log  2>&1 &
done

for i in redis syslog; do
	ssh admin@ghe.spotify.net "tail -f /var/log/$i.log" | python ~/src/ghelog/bin/awesomeparsethingiethatiscool.py ghe.spotify.net $i >$i.log 2>&1 &
done

wait
