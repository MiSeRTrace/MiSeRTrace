nn=$(pwd | rev | cut -d'/' -f 1 | rev)
netid=$(docker network ls | grep $nn | cut -d ' ' -f 1)
echo br-$netid