with open('config/testbinary.bin', 'wb') as f:
    f.write(b'\x00\x01\x02\x03')
print('✅ Binary file written to config/testbinary.bin') 