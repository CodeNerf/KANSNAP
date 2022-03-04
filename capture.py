import urllib.request
import urllib.error as URLErrors
import os
import io
from pathlib import Path
import time
import threading
import random
import tarfile
import glob

class Capture:
    still_number = 0
    current_index = 0
    err = 0

    time_base_format = "10.8f"
    stream = None
    last_image = None
    stream_retry_counter = 0
    max_retries = 10
    marker_a_fake_can_msg = '7FF#DEADBEEF04F1D0AA'
    marker_b_fake_can_msg = '7FF#DEADBEEF04F1D0BB'

    def __init__(self, vin: str, can_interfaces: list, droid_x_host_ips: list, parameter_name: str,
                 windows_screen_capture_host=None, stream_retry_delay=5, max_retries=10):
        self.bus_logged_lines = {}
        self.safe_param_name = "".join([c for c in parameter_name if c.isalpha() or c.isdigit() or c == ' ']).rstrip().replace(" ", "_").lower()
        self.current_time = f"{time.time():{self.time_base_format}}"
        self.capturing = False
        self.droid_x_host_ips = droid_x_host_ips
        self.vin = vin
        self.can_interfaces = can_interfaces
        self.log_directory = self.update_log_directory()
        self.can_log_filename = None
        self.parameter = parameter_name
        self.stream_retry_delay = stream_retry_delay
        self.stream_retry_counter = 0
        self.max_retries = max_retries
        self.logging_status = "Logging not started"
        self.stream_status = "Stream not yet started"
        self.can_log_info = None
        self.set_marker_a = False
        self.set_marker_b = False
        self.maker_set_time = time.time()
        self.logged_lines = 0
        self.marker_count = 0
        self.marker_a_count = 0
        self.marker_b_count = 0
        self.running_thread = threading.Thread()
        self.windows_screen_capture_host = windows_screen_capture_host
        self.stream_threads = []
        self.streams = []
        self.can_capture_threads = []

    def screen_capture(self, capture_rate=1, sc_port=5000):

        while self.capturing:  # TODO: This is not working
            url = urllib.request.urlopen(
                f"http://{self.windows_screen_capture_host}:{sc_port}/capture/?time={time.time()}").read().decode()
            if url is not None:
                img_location = url[2:]
                parts = img_location.split('/')
                file_name = parts[len(parts) - 1]
                ret, http_msg = \
                    urllib.request.urlretrieve(url, f"{self.log_directory}/todo")  # TODO: FIX THIS DIRCTORY
                print(f"{ret}: {http_msg}")
                time.sleep(capture_rate)

    def update_log_directory(self):
        vin = self.vin
        path = os.path.dirname(os.path.realpath(__file__))
        unique_index = int((random.random() * 100000))
        log_directory = f"{path}/static/captures/{vin}/{self.safe_param_name}/{unique_index}/"
        self.log_directory = log_directory
        return log_directory

    def log_can_data(self):
        self.logging_status = "Log Thread Initiated, CAN Logging Not Started"

        self.can_capture_threads = []

        self.current_time = f"{time.time():{self.time_base_format}}"
        self.can_log_filename = f"{self.log_directory}can_{self.current_time}.log"
        can_log_file = open(self.can_log_filename, 'w')
        self.logged_lines = 0
        try:

            self.logging_status = f"Logging traffic."

            for bus in self.can_interfaces:
                interface_thread = threading.Thread(target=self.capture_can_traffic, args=(bus, can_log_file))
                interface_thread.name = f"Thread_{bus.channel}"
                self.can_capture_threads.append(interface_thread)

            while self.capturing:
                for can_capture_thread in self.can_capture_threads:
                    if can_capture_thread.ident is None:
                        can_capture_thread.start()
                        print(f"Starting Thread {can_capture_thread.name}")

                marker = None
                marker_network = 'MARK'
                if self.set_marker_a or self.set_marker_b:
                    if self.set_marker_a:
                        marker = self.marker_a_fake_can_msg
                        self.set_marker_a = False
                        self.logging_status = f"Logging Set Maker A!"
                        self.marker_a_count += 1
                    elif self.set_marker_b:
                        marker = self.marker_b_fake_can_msg
                        self.set_marker_b = False
                        self.logging_status = f"Logging Set Maker B!"
                        self.marker_b_count += 1
                    marker_message = f"({self.maker_set_time:{self.time_base_format}}) {marker_network} {marker}"
                    can_log_file.write(marker_message + '\n')
                    self.logged_lines += 1
                    self.marker_count += 1
            else:
                can_log_file.write("\n")
                time.sleep(0.5)
                can_log_file.close()

                for capture_thread in self.can_capture_threads:
                    capture_thread.join()
                self.logging_status = f"Stopped logging traffic."

        except OSError as e:
            print(f"{e}")

        return True

    def _run(self):
        self.streams = []
        self.stream_threads = []
        self.update_log_directory()

        self.capturing = True

        Path(f"{self.log_directory}/{self.current_index}/").mkdir(parents=True, exist_ok=False)

        # ##### START PHONE VIDEO STREAMS #####
        for droid_x_host_ip in self.droid_x_host_ips:
            # Create Stream Object for Each Droid X Phone IP
            self.streams.append(Stream(droid_x_host_ip, self.current_index, self.log_directory))

        for stream in self.streams:
            stream_thread = threading.Thread(target=stream.start)
            stream_thread.start()

        # ##### START CAN BUS LOGGER #####
        can_loger_thread = threading.Thread(target=self.log_can_data)
        can_loger_thread.start()

        # ##### START REMOTE SCREEN CAPTURE STREAM #####
        if self.windows_screen_capture_host is not None:
            screen_capture_thread = threading.Thread(target=self.screen_capture)
            screen_capture_thread.start()

    def run(self):
        self.capturing = True
        self.current_index += 1
        self._run()

    def stop(self):
        self.stream_retry_counter = 0
        self.capturing = False
        not_stopped = True

        while not_stopped:
            for stream in self.streams:
                if stream.capturing:
                    stream_ended_reason = "User Requested Stream End."
                    stream.stop(stream_ended_reason)
                    continue
                else:
                    not_stopped = False

    def marker_a(self, marker_time):
        self.maker_set_time = marker_time
        self.set_marker_a = True
        print(f"({time.time()}) Marker 'A' Triggered at with 'marker_time' of {marker_time} ")

    def marker_b(self, marker_time):
        self.maker_set_time = marker_time
        self.set_marker_b = True
        print(f"({time.time()}) Marker 'B' Triggered at with 'marker_time' of {marker_time} ")

    def capture_can_traffic(self, bus, can_log_file):
        self.bus_logged_lines.update({bus.channel_info: 0})
        while self.capturing:
            msg = bus.recv(timeout=1)
            if msg is not None:
                arb_id_format = 3 if not msg.is_extended_id else 8
                # =====[ (19293848.92938) can0 7E0#0210010000000000 ]=====
                msg_frame = f"({msg.timestamp:{self.time_base_format}}) " \
                            f"{bus.channel} {msg.arbitration_id:0{arb_id_format}X}#" + ''.join(
                                                                                        [f"{b:02X}" for b in msg.data])
                can_log_file.write(msg_frame + "\n")
                self.logged_lines += 1
                self.bus_logged_lines[bus.channel_info] += 1
                self.logging_status = f"{bus} Logging..."
        else:
            print(f"{bus} done with {can_log_file}!")

        print(f"({bus}) capture traffic finishing!")

    def end_streams(self):
        for stream in self.streams:
            stream.capturing = False

    @staticmethod
    def _find_closest(lst, k):
        return lst[min(range(len(lst)), key = lambda i: abs(lst[i]-k))]


class Stream:

    video_sizes = {
        "240p": "320x240",
        "480p": "640x480",
        "720p": "960x720",
        "FHD720p": "1280x720",
        "FHD1080p": "1920x1080"
    }

    video_size = video_sizes['480p']
    eof = b'\xff\xd9'
    time_base_format = "10.8f"
    still_number = 0
    err = 0

    def __init__(self, droid_x_host_ip: str, current_index: int, log_directory: str):

        self.droid_x_host_ip = droid_x_host_ip
        self.droid_x_host_port = 4747
        self.capturing = False
        self.current_index = current_index
        self.log_directory = log_directory
        self.last_image = None
        self.stream_status = f"Stream Initialized!"
        self.archived_file = None
        self.archiving_directory = None
        self.archive_successful = None
        self.archive_error = None
        self.stream_ended_reason = None

    def _connect_to_stream_url(self):
        video_url = "/video?"

        try:
            local_stream = urllib.request.urlopen(
                f"http://{self.droid_x_host_ip}:{self.droid_x_host_port}{video_url}{self.video_size}")
            print(f"Capturing video Size '{self.video_size}' from {self.droid_x_host_ip} on Port {self.droid_x_host_port}")
            return local_stream

        except URLErrors.URLError as e:
            print(f"Could Not connect to {self.droid_x_host_ip}:{self.droid_x_host_port}! : {e}")
            return None

    def _write_image_to_archive(self, archive, index, timestamp, data):
        info       = tarfile.TarInfo("%08d.jpg" % (index,))
        info.size  = len(data)
        info.mtime = int(timestamp)

        archive.addfile(info, io.BytesIO(data))

    def start(self):
        self.capturing = True

        os.makedirs(f"{self.log_directory}{self.droid_x_host_ip}", exist_ok=True)

        local_stream = self._connect_to_stream_url()
        tar_archive  = tarfile.open(f"{self.log_directory}{self.droid_x_host_ip}/{self.video_size}_capture.tar", 'w')
        tar_index    = 0

        if local_stream is not None:
            self.stream_status = f"Stream Connected on {self.droid_x_host_ip}:{self.droid_x_host_port} at {time.time()}."
            while self.capturing:
                data = local_stream.read(128)
                cll = data.find(b'Content-Length: ')
                if cll == -1:
                    stream_ended_reason = "Stream Failure. Reached End Of Stream"
                    self.last_image = None
                    self.stop(stream_ended_reason)  # Stream has Ended.
                    break
                cl = data[cll:].split(b' ')
                cli = cl[1]
                rl = cli.find(b'\r')
                buffer_size = int(cli[:rl])
                extra = len(cli[rl:])
                for i in range(4 - extra):
                    _ = local_stream.read(1)
                data = local_stream.read(buffer_size)
                if data[-2:] == self.eof:  # End of Image File
                    write_time = time.time()

                    self._write_image_to_archive(tar_archive,
                                                 tar_index,
                                                 write_time,
                                                 data)

                    tar_index += 1

                    self.last_image = data
                else:
                    stream_ended_reason = "Stream Failure. Corrupted Stream"
                    self.last_image = None
                    self.stop(stream_ended_reason)  # Stream has Ended or failed to get EOF
                    self.err = -1
                    break

            tar_archive.close()
            local_stream.close()
            self.stream_status = f"Stream Closed on {self.droid_x_host_ip}:{self.droid_x_host_port} at {time.time()}"


    def stop(self, end_reason):
        self.capturing = False
        self.stream_status = "Stream STOPPED"
        self.stream_ended_reason = end_reason
        time.sleep(0.01)  # Let Stream Settle.
