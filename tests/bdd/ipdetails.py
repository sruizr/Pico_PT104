from PT104 import PT104, DataTypes, Wires
from PT104.usb import USBinteface
from statistics import stdev


SN_1 = 'EY477/119'
SN_3 = 'FO527/106'
SN_2 = 'EY477/080'

interface = USBinteface()

dev_1 = PT104(interface)
dev_2 = PT104(interface)
dev_3 = PT104(interface)


dev_1.connect(SN_1)
print(dev_1.interface.get_ip_details(dev_1.id))
print(dev_1.info)

dev_2.connect(SN_2)
print(dev_2.interface.get_ip_details(dev_2.id))
print(dev_2.info)

dev_3.connect(SN_3)
print(dev_3.interface.get_ip_details(dev_3.id))
print(dev_3.info)


def eval_variation():
    data_2 = []
    for _ in range(30):
        data_2.append(dev_2.channels[2].value)
    print(f'Values on device 2, channel 2 are: {data_2}')
    print(f'Standard deviation is {stdev(data_2)}')

    data_1 = []
    for _ in range(30):
        data_1.append(dev_1.channels[1].value)
    print(f'Values on device 1, channel 1 are: {data_1}')
    print(f'Standard deviation is {stdev(data_1)}')


# eval_variation()
