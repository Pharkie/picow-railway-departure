import machine
import sys

# Create I2C object
i2c = machine.I2C(0, scl=machine.Pin(17), sda=machine.Pin(16))
print("I2C object created.")

# Scan for devices and print out any addresses found
devices = i2c.scan()
print("Scanning for I2C devices...")

if devices:
    print("I2C found as follows.")
    for d in devices:
        print("     Device at address: " + hex(d))
else:
    print("No I2C devices found.")
    sys.exit()