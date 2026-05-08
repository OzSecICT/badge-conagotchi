Hardware test code


Note: If board boot loops, test if it's a failed PSRAM module/MCU:
`idf.py -DSDKCONFIG_DEFAULTS="sdkconfig.defaults;sdkconfig.defaults.nopsram" reconfigure build flash monitor`

Then when going back to the normal PSRAM enabled option run `idf.py reconfigure build flash monitor` and subsequently just `idf.py build flash monitor` or whatever is needed.
