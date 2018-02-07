valid_bins = [300, 900, 1800, 7200, 14400, 86400]
print(valid_bins)

if 300 in valid_bins:
    print('300 in valid_bins.')
else:
    print('300 NOT in valid_bins.')

if 301 in valid_bins:
    print('301 in valid_bins.')
else:
    print('301 NOT in valid_bins.')
