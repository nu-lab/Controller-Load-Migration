#!/bin/bash
exec &> ./logs/ifconfig-$1.log

ifconfig; 

