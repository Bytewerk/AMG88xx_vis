import can
import cv2
import numpy

# merging defines
overlap_0x100_to_0x110 = 2
overlap_0x110_to_0x120 = 2
overlap_0x120_to_0x130 = 2
SENSOR_RANGE = 8
actual_array_size_x = SENSOR_RANGE * 2 - overlap_0x120_to_0x130
actual_array_size_y = SENSOR_RANGE * 2 - overlap_0x110_to_0x120


# data = numpy.zeros((8, 8), dtype=numpy.float32)
data = numpy.zeros((16, 16), dtype=numpy.float32)
data_resized = numpy.zeros((actual_array_size_x, actual_array_size_y), dtype=numpy.float32)
data0x100 = numpy.zeros((8, 8), dtype=numpy.float32)
data0x110 = numpy.zeros((8, 8), dtype=numpy.float32)
data0x120 = numpy.zeros((8, 8), dtype=numpy.float32)
data0x130 = numpy.zeros((8, 8), dtype=numpy.float32)
thermistor = numpy.zeros(4, dtype=numpy.float32)

# offsets
offset_0x100 = 0
offset_0x110 = 0
offset_0x120 = 0
offset_0x130 = 0


def process_can(bus):
    msg = bus.recv(0)
    if msg is None:
        return False
    if not (0x100 <= msg.arbitration_id <= 0x107):
        return True
    num_sensor = msg.arbitration_id - 0x100
    for i in range(8):
        data[7 - num_sensor][i] = msg.data[i]

    return True


def process_can_all(bus):
    msg = bus.recv(0)
    if msg is None:
        return False

    if msg.arbitration_id == 0x10B:
        thermistor[0] = (((msg.data[0] & 0xF7)<<8) + msg.data[1]) * 0.0625
        print("thermistor value 0x100:", thermistor[0], "°C")
    if msg.arbitration_id == 0x11B:
        thermistor[1] = (((msg.data[0] & 0xF7) << 8) + msg.data[1]) * 0.0625
        print("thermistor value 0x110:", thermistor[1], "°C")
    if msg.arbitration_id == 0x12B:
        thermistor[2] = (((msg.data[0] & 0xF7) << 8) + msg.data[1]) * 0.0625
        print("thermistor value 0x120:", thermistor[2], "°C")
    if msg.arbitration_id == 0x13B:
        thermistor[3] = (((msg.data[0] & 0xF7) << 8) + msg.data[1]) * 0.0625
        print("thermistor value 0x130:", thermistor[3], "°C")

    min_value = thermistor.min()
    print("")
    offset_0x100 = thermistor[0] - min_value
    print("offset for 0x100: ", offset_0x100, "°C")
    offset_0x110 = thermistor[1] - min_value
    print("offset for 0x110: ", offset_0x110, "°C")
    offset_0x120 = thermistor[2] - min_value
    print("offset for 0x120: ", offset_0x120, "°C")
    offset_0x130 = thermistor[3] - min_value
    print("offset for 0x130: ", offset_0x130, "°C")
    print("")

    if not (0x100 <= msg.arbitration_id <= 0x137):
        return True
    num_sensor = msg.arbitration_id - 0x100

    if 0x30 <= num_sensor <= 0x37:  # look for which sensor it represent
        num_sensor = num_sensor - 0x30
        for i in range(8):
            data0x130[7 - num_sensor][7 - i] = msg.data[i]
        return True

    if 0x20 <= num_sensor <= 0x27:
        num_sensor = num_sensor - 0x20
        for i in range(8):
            data0x100[7 - num_sensor][7 - i] = msg.data[i]
            #data0x100[num_sensor][i] = msg.data[i]
        return True

    if 0x10 <= num_sensor <= 0x17:
        num_sensor = num_sensor - 0x10
        for i in range(8):
            data0x110[num_sensor][i] = msg.data[i]
        return True

    if 0x00 <= num_sensor <= 0x07:
        for i in range(8):
            data0x120[7 - num_sensor][7 - i] = msg.data[i]
        return True


def merge_all_sensor_data():
    # sensor location like this
    #
    #  \   15 14 13 12 11 10 9  8 | 7 6 5 4 3 2 1 0
    #    \ 7  6  5  4  3  2  1  0 | 7 6 5 4 3 2 1 0
    # 15 7                        |
    # 14 6                        |
    # 13 5                        |
    # 12 4                        |
    # 11 3       0x120            |      0x110
    # 10 2                        |
    # 9  1                        |
    # 8  0                        |
    # ----------------------------------------------
    # 7  7                        |
    # 6  6                        |
    # 5  5                        |
    # 4  4                        |
    # 3  3       0x130            |      0x100
    # 2  2                        |
    # 1  1                        |
    # 0  0                        |
    ################################################

    # write first sensor (0x120) in the big array of all 1 to 1
    start_x = SENSOR_RANGE
    end_x = SENSOR_RANGE * 2

    start_y = SENSOR_RANGE
    end_y = SENSOR_RANGE * 2

    for x in range(start_x, end_x):  # start from 8 to 15
        for y in range(start_y, end_y):
            data[x][y] = data0x120[end_x - 1 - x][end_y - 1 - y] - offset_0x120

    # now write the sensor 0x110 to the array with the overlap to 0x120
    start_x = overlap_0x110_to_0x120
    end_x = overlap_0x110_to_0x120 + SENSOR_RANGE

    start_y = SENSOR_RANGE
    end_y = SENSOR_RANGE * 2

    for x in range(start_x, end_x):  # start from 2 to 9
        for y in range(start_y, end_y):
            if x <= end_x - start_x:
                data[x][y] = data0x110[x - start_x][y - start_y] - offset_0x110
            else:
                # merge the overlapping data with average
                #   data[x][y] = (data[x][y] + data0x110[x - start_x][y - start_y]) / 2
                data[x][y] = data0x110[x - start_x][y - start_y] - offset_0x110

    # write sensor 0x130 to the array with the overlap to 0x120

    start_x = SENSOR_RANGE
    end_x = SENSOR_RANGE * 2

    start_y = overlap_0x120_to_0x130
    end_y = SENSOR_RANGE + overlap_0x120_to_0x130

    for x in range(start_x, end_x):  # start from 8 to 15
        for y in range(start_y, end_y):  # start from 2 to 9
            if y <= end_y - start_y:
                data[x][y] = data0x130[x - start_x][y - start_y] - offset_0x130
            else:
                # merge the overlapping data with average
                # data[x][y] = (data[x][y] + data0x130[x - start_x][y - start_y]) / 2
                data[x][y] = data0x130[x - start_x][y - start_y] - offset_0x130

    # write sensor 0x100 to the array with the overlap to 0x130 and 0x110

    start_x = overlap_0x110_to_0x120
    end_x = overlap_0x110_to_0x120 + SENSOR_RANGE

    start_y = overlap_0x120_to_0x130
    end_y = SENSOR_RANGE + overlap_0x120_to_0x130

    for x in range(start_x, end_x):  # start from 2 to 9
        for y in range(start_y, end_y):  # start from 2 to 9
            if y <= end_y - start_y or x <= end_x - start_x:
                data[x][y] = data0x100[x - start_x][y - start_y] - offset_0x100
            else:
                # merge the overlapping data with average
                #    data[x][y] = (data[x][y] + data0x130[x - start_x][y - start_y]) / 2
                data[x][y] = data0x100[x - start_x][y - start_y] - offset_0x100


def resize_data(data_to_resize):
    start_x = 0
    end_x = actual_array_size_x

    start_y = 0
    end_y = actual_array_size_y

    for x in range(start_x, end_x):
        for y in range(start_y, end_y):
            data_resized[x][y] = data_to_resize[x + overlap_0x120_to_0x130][y + overlap_0x110_to_0x120]


def print_array(print_array):
    print("Starting printing....")
    for x in range(0, actual_array_size_x):
        for y in range(0, actual_array_size_y):
            print(print_array[x][y])
    print("End of print...")


def main():
    bus = can.interface.Bus('can0', bustype='socketcan_native')

    while True:
        while process_can_all(bus):
            pass

        merge_all_sensor_data()
        # data[7][0] = numpy.average(data)
        # data[15][0] = numpy.average(data)
        resize_data(data)
        img = data_resized.copy()
        img -= img.min()
        img *= 255 / (img.max() + 1)
        img = cv2.resize(img, (512, 512))
        img = cv2.applyColorMap(img.astype(numpy.uint8), cv2.COLORMAP_JET)
        cv2.startWindowThread()
        cv2.imshow('IR data', img)
        key = cv2.waitKey(10) & 0xFF
        if key == 27:
            break
        #print_array(data_resized)

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
