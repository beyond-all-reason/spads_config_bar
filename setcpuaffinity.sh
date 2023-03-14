#!/bin/bash

#Sets the CPU affinity of all SPADS and spring-dedicated processes to all cpus every 30 minuts

while true
do
	date -u
	pgrep perl | xargs -L1 taskset -cp 0-7
	pgrep spring | xargs -L1 taskset -cp 0-7
	sleep 600
done 
