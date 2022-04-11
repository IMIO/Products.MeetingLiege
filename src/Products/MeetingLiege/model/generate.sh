#!/bin/sh
archgenxml --cfg generate.conf MeetingLiege.zargo -o tmp

# only keep workflows and rolemap.xml
# cp -rf tmp/profiles/default/workflows ../profiles/default
# cp tmp/profiles/default/rolemap.xml ../profiles/default
rm -rf tmp
