import socket, struct, time, logging

NTP_SERVER = 'ntp1.stratum1.ru' #'ru.pool.ntp.org' # 'time.euro.apple.com'
NTP_PORT = 123
NTP_TS_DELTA = 2208988800

REQUEST_NUMBER = 5
REQUEST_TIMEOUT = 2

# TODO: precision?
def assemble_ts(integral, fractional):
    return float('{integral}.{fractional}'.format(integral=integral, fractional=fractional))

def sntp_get(request_number, out=False):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # 32 + 8*4*3 + 8*8*4 = 384
    header =                (27, 0, 0, 0)
    root_delay =            (0, 0, 0, 0)
    root_dispersion =       (0, 0, 0, 0)
    reference_identifier =  (0, 0, 0, 0)
    reference_ts =          (0, 0, 0, 0, 0, 0, 0, 0)
    originate_ts =          (0, 0, 0, 0, 0, 0, 0, 0)
    receive_ts =            (0, 0, 0, 0, 0, 0, 0, 0)
    transmit_ts =           (0, 0, 0, 0, 0, 0, 0, 0)

    data = header + root_delay + root_dispersion + reference_identifier + reference_ts + originate_ts + receive_ts + transmit_ts

    before_ts = NTP_TS_DELTA + time.time()
    sock.sendto(struct.pack('!48B', *data), (NTP_SERVER, NTP_PORT))
    sock.settimeout(REQUEST_TIMEOUT)

    bdata, address = sock.recvfrom(1024)
    after_ts = NTP_TS_DELTA + time.time()

    data = struct.unpack('!12I', bdata)
    receive_ts = assemble_ts(data[8], data[9])
    transmit_ts = assemble_ts(data[10], data[11])

    # (T4 - T3) + (T2 - T1)
    package_transmission_delay = (after_ts - transmit_ts) + (receive_ts - before_ts)

    # ((Т2 – Т1) + (Т3 – Т4)) / 2
    local_time_offset = ((receive_ts - before_ts) + (transmit_ts - after_ts)) / 2

    if out:
        logging.warning ('Request #{n}:\nPackage delay: {delay}\nOffset: {offset}\nTime: {time}\n'.format(
            n=request_number+1,
            delay=package_transmission_delay,
            offset=local_time_offset,
            time=time.ctime((after_ts + local_time_offset) - NTP_TS_DELTA)))

    return local_time_offset, after_ts

def get_time():
    offset_sum = 0
    last_ts = 0

    for i in range(REQUEST_NUMBER):
        offset, last_ts = sntp_get(i, out=False)
        offset_sum += offset

    m_offset = offset_sum / REQUEST_NUMBER
    logging.warning ('Offset: {offset}\nTime: {time}\n\n'.format(
        offset=m_offset,
        time=time.ctime((last_ts + m_offset) - NTP_TS_DELTA)))

if __name__ == '__main__':
    get_time()