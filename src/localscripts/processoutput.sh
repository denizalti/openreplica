mkdir processed
for x in *; do
    awk '{print $2 " " $3 " " $4 " " $5}' $x >processed/$x
done