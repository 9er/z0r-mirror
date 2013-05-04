#!/bin/bash

downloaded=0

total=`wget http://www.z0r.de/0 -O - -q | grep "&laquo;" | cut -d "\"" -f 2`

echo "$total clips available"

for i in `seq 0 1 $total`; do
    if [ ! -f "$i.swf" ]; then
        echo "downloading clip #$i"
        flashobj=`wget "http://z0r.de/$i" -O - -q | grep "swfobject.embedSWF" | cut -d "\"" -f 2`
        wget "$flashobj" -O "swf-files/$i.swf" -q
        downloaded=$(($downloaded+1))
    fi
done

if [ $downloaded -gt 0 ]
then
    echo "$downloaded flash movies downloaded"
else
    echo "already up to date"
fi

