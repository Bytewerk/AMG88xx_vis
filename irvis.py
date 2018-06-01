import can
import cv2
import numpy

data = numpy.zeros((8, 8), dtype=numpy.float32)


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


def main():
    bus = can.interface.Bus('can0', bustype='socketcan_native')

    while True:
        while process_can(bus):
            pass

        data[7][0] = numpy.average(data)

        img = data.copy()
        img -= img.min()
        img *= 255/(img.max()+1)
        img = cv2.resize(img, (512, 512))
        img = cv2.applyColorMap(img.astype(numpy.uint8), cv2.COLORMAP_JET)
        cv2.imshow('IR data', img)

        key = cv2.waitKey(10)
        if key == 27:
            break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
