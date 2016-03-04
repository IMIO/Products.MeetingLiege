#!/bin/sh
archgenxml-master --cfg generate.conf MeetingLiege.zargo -o tmp 

# only keep workflows
cp -rf tmp/profiles/default/workflows ../profiles/default
rm -rf tmp
