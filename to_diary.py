#!/usr/bin/env python3
import subprocess, re, calendar

months = dict((v,k) for k,v in enumerate(calendar.month_abbr))
lines = []
proc = subprocess.Popen(['git log'], stdout=subprocess.PIPE, shell=True)
(out, err) = proc.communicate()
out = out.decode('UTF-8')
out = out.splitlines()
print('Date' + ' ' * 8 + 'Time' + ' ' * 5 + 'Commit Message')
for line in out:
	if line.startswith('Date'):
		regex = re.match('.*([A-Z][a-z]{2}) ([0-3][0-9]) ([0-9]{2}:[0-9]{2}).*', line)
		print(regex.group(2) + '/' + str(months[regex.group(1)]) + '/17    ' + regex.group(3), end='    ')
	if line.startswith('    '):
		print(line.lstrip())