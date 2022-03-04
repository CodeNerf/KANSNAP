import can

CAN_MSG_EXT = 0x80000000
CAN_ERR_FLAG = 0x20000000
CAN_ERR_BUSERROR = 0x00000080
CAN_ERR_DLC = 8


class MyCanutilsLogReader(can.CanutilsLogReader):

    def __init__(self, file):
        super().__init__(file)

    def __iter__(self):
        for line in self.file:

            # skip empty lines
            temp = line.strip()
            if not temp:
                continue

            try:
                timestamp, channel, frame = temp.split()
            except Exception as e:
                print(f"Exception in CAN Reader {e}. Skipping Line")
                continue
            timestamp = float(timestamp[1:-1])
            canId, data = frame.split('#')
            if channel.isdigit():
                channel = int(channel)

            if len(canId) > 3:
                isExtended = True
            else:
                isExtended = False
            canId = int(canId, 16)
            dataBin = None
            if data and data[0].lower() == 'r':
                isRemoteFrame = True
                if len(data) > 1:
                    dlc = int(data[1:])
                else:
                    dlc = 0
            else:
                isRemoteFrame = False

                dlc = len(data) // 2
                dataBin = bytearray()
                for i in range(0, len(data), 2):
                    dataBin.append(int(data[i:(i + 2)], 16))

            if canId & CAN_ERR_FLAG and canId & CAN_ERR_BUSERROR:
                msg = can.Message(timestamp=timestamp, is_error_frame=True)
            else:
                msg = can.Message(timestamp=timestamp, arbitration_id=canId & 0x1FFFFFFF,
                                  is_extended_id=isExtended, is_remote_frame=isRemoteFrame,
                                  dlc=dlc, data=dataBin, channel=channel)
            yield msg

        self.stop()

# coding: utf-8

"""
This module contains the implementation of :class:`~can.Notifier`.
"""

import threading
import logging
import time
try:
    import asyncio
except ImportError:
    asyncio = None

logger = logging.getLogger('can.Notifier')
