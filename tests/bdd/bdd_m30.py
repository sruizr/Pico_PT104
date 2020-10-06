from PT104 import PT104, DataTypes, Wires
from PT104.usb import USBinteface
from statistics import stdev


SN_1 = 'EY477/119'

interface = USBinteface()

dev_1 = PT104(interface)
dev_2 = PT104(interface)
dev_3 = PT104(interface)


dev_1.connect(SN_1)
print(dev_1.info)
dev_1.channels[1].data_type = DataTypes.PT100
dev_1.channels[1].wires = Wires.WIRES_4
dev_1.channels[1].lower_pass_filter = True
dev_1.channels[2].data_type = DataTypes.PT100
dev_1.channels[2].wires = Wires.WIRES_4
dev_1.convert()


# dev_2.connect(SN_2)
# dev_2.channels[2].data_type = DataTypes.PT100
# dev_2.channels[2].wires = Wires.WIRES_4
# dev_2.convert()
# print(dev_2.info)


def eval_variation():
    data_2 = []
    for _ in range(30):
        data_2.append(dev_1.channels[2].value)
    print(f'Values on device 2, channel 2 are: {data_2}')
    print(f'Standard deviation is {stdev(data_2)}')

    data_1 = []
    for _ in range(30):
        data_1.append(dev_1.channels[1].value)
    print(f'Values on device 1, channel 1 are: {data_1}')
    print(f'Standard deviation is {stdev(data_1)}')

    average = [d1 + d2 for d1, d2 in zip(data_1, data_2)]
    print(f'Promedio tiene una desviacion {stdev(average)}')


eval_variation()
