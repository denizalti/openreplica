#!/bin/sh

ssh sys01 screen -m -d "killall -9 python"
for (( x=3; x<="9"; x++ )); do
    ssh "sys0$x" screen -m -d "killall -9 python"
done

for (( x=0; x<="5"; x++ )); do
    ssh "sys1$x" screen -m -d "killall -9 python"
done