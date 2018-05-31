import can
import cv2
import numpy


def main():
    can_interface = 'can0'

    bus = can.interface.Bus(can_interface, bustype='socketcan_native')

    data = numpy.array([
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
    ], numpy.float32)

    while True:
        msg = bus.recv()
        if (msg is None) or not (0x100 <= msg.arbitration_id <= 0x107):
            continue
        num_sensor = msg.arbitration_id - 0x100
        for i in range(8):
            data[7-num_sensor][i] = msg.data[i]
        data[7][0] = numpy.average(data)

        img = 4 * (data - 75)
        print (img)
        img = cv2.resize(img, (512, 512))
        img = cv2.applyColorMap(img.astype(numpy.uint8), cv2.COLORMAP_JET)

        cv2.imshow('IR data', img)
        key = cv2.waitKey(1)
        if key == 27:
            break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
