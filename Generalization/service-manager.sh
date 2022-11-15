#!/bin/sh
# workdir=/home/SimulationCloud/Generalization
workdir=/SimulationCloud/Generalization

server_start(){
   cd $workdir
   python3 main_web.py runserver &
   echo "Server started."
 }
 
server_stop(){
   pid=`ps -ef | grep 'python3 main_web.py' | awk '{ print $2 }'`
   echo $pid
   kill $pid
   sleep 2
   echo "Server Killed."
 }
 
 case "$1" in
   start)
     server_start
     ;;
   stop)
     server_stop
     ;;
   restart)
     server_stop
     server_start
     ;;
   *)
   echo "Usage: Services {start|stop|restart}"
   exit 1
 esac
 exit 0