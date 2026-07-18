#!/usr/bin/env python3
import re
import sys

STATUS_AS = {
    1: "AS_OFF",
    2: "AS_READY",
    3: "AS_DRIVING",
    4: "AS_EMERGENCY_BRAKE",
    5: "AS_FINISHED",
}

STATUS_AMI = {
    0: "AMI_NOT_SELECTED",
    1: "AMI_ACCELERATION",
    2: "AMI_SKIDPAD",
    3: "AMI_AUTOCROSS",
    4: "AMI_TRACK_DRIVE",
    5: "AMI_STATIC_INSPECTION_A",
    6: "AMI_STATIC_INSPECTION_B",
    7: "AMI_AUTONOMOUS_DEMO",
}

MISSION_STATUS = {
    0: "MISSION_NOT_SELECTED",
    1: "MISSION_SELECTED",
    2: "MISSION_RUNNING",
    3: "MISSION_FINISHED",
}

DIRECTION_REQUEST = {
    0: "DIRECTION_NEUTRAL",
    1: "DIRECTION_FORWARD",
}

ESTOP_REQUEST = {
    0: "ESTOP_NO",
    1: "ESTOP_YES",
}

CAN_RX_IDS = {
    0x520: "VCU2AI_STATUS",
    0x521: "VCU2AI_DRIVE_F",
    0x522: "VCU2AI_DRIVE_R",
    0x523: "VCU2AI_STEER",
    0x524: "VCU2AI_BRAKE",
    0x525: "VCU2AI_WHEEL_SPEEDS",
    0x526: "VCU2AI_WHEEL_COUNTS",
}

CAN_TX_IDS = {
    0x510: "AI2VCU_STATUS",
    0x511: "AI2VCU_DRIVE_F",
    0x512: "AI2VCU_DRIVE_R",
    0x513: "AI2VCU_STEER",
    0x514: "AI2VCU_BRAKE",
}

LINE_RE = re.compile(
    r"^\s*(?:\[\d+\.\d+\]\s*)?(?P<iface>\S+)\s+"
    r"(?P<id>[0-9A-Fa-f]+)\s+\[(?P<dlc>\d+)\]\s+(?P<data>(?:[0-9A-Fa-f]{2}(?:\s+[0-9A-Fa-f]{2})*))\s*$"
)
LINE_RE_ALT = re.compile(
    r"^\s*(?:\[\d+\.\d+\]\s*)?(?P<iface>\S+)\s+"
    r"(?P<id>[0-9A-Fa-f]+)#(?P<data>[0-9A-Fa-f]+)\s*$"
)


def parse_bytes(data_text):
    data_text = data_text.strip()
    if not data_text:
        return []
    if " " in data_text:
        return [int(x, 16) for x in data_text.split()]
    return [int(data_text[i : i + 2], 16) for i in range(0, len(data_text), 2)]


def u16_le(bytes_, offset=0):
    return bytes_[offset] | (bytes_[offset + 1] << 8)


def i16_le(bytes_, offset=0):
    value = u16_le(bytes_, offset)
    return value - 0x10000 if value & 0x8000 else value


def format_hex(bytes_):
    return " ".join(f"{b:02X}" for b in bytes_)


def decode_rx_status(bytes_):
    handshake = bytes_[0] & 0x01
    res_go = (bytes_[1] >> 3) & 0x01
    as_state = bytes_[2] & 0x0F
    ami_state = (bytes_[2] >> 4) & 0x0F
    return (
        f"handshake={handshake} res_go={res_go} "
        f"AS={as_state}({STATUS_AS.get(as_state, 'UNKNOWN')}) "
        f"AMI={ami_state}({STATUS_AMI.get(ami_state, 'UNKNOWN')})"
    )


def decode_rx_steer(bytes_):
    raw = i16_le(bytes_, 0)
    return f"steer_raw={raw} steer_angle={raw / 10.0:.1f} deg"


def decode_rx_brake(bytes_):
    front = bytes_[0]
    rear = bytes_[2] if len(bytes_) > 2 else 0
    return f"front_raw={front} front_pct={front * 0.5:.1f}% rear_raw={rear} rear_pct={rear * 0.5:.1f}%"


def decode_rx_wheel_speeds(bytes_):
    fields = []
    if len(bytes_) >= 8:
        fields = [u16_le(bytes_, i * 2) for i in range(4)]
    return (
        f"FL={fields[0]} rpm FR={fields[1]} rpm RL={fields[2]} rpm RR={fields[3]} rpm"
        if len(fields) == 4
        else "invalid wheel speeds payload"
    )


def decode_rx_wheel_counts(bytes_):
    fields = []
    if len(bytes_) >= 8:
        fields = [u16_le(bytes_, i * 2) for i in range(4)]
    return (
        f"FL={fields[0]} ticks FR={fields[1]} ticks RL={fields[2]} ticks RR={fields[3]} ticks"
        if len(fields) == 4
        else "invalid wheel counts payload"
    )


def decode_tx_status(bytes_):
    handshake = bytes_[0] & 0x01
    direction = (bytes_[1] >> 6) & 0x03
    mission = (bytes_[1] >> 4) & 0x03
    estop = bytes_[1] & 0x01
    return (
        f"handshake={handshake} direction={direction}({DIRECTION_REQUEST.get(direction, 'UNKNOWN')}) "
        f"mission={mission}({MISSION_STATUS.get(mission, 'UNKNOWN')}) "
        f"estop={estop}({ESTOP_REQUEST.get(estop, 'UNKNOWN')})"
    )


def decode_tx_drive(bytes_, label):
    if len(bytes_) < 4:
        return "invalid drive frame"
    torque = u16_le(bytes_, 0) / 10.0
    speed = u16_le(bytes_, 2)
    return f"{label}_torque={torque:.1f} Nm {label}_speed={speed} rpm"


def decode_tx_steer(bytes_):
    if len(bytes_) < 2:
        return "invalid steer frame"
    raw = i16_le(bytes_, 0)
    return f"steer_raw={raw} steer_angle={raw / 10.0:.1f} deg"


def decode_tx_brake(bytes_):
    if len(bytes_) < 2:
        return "invalid brake frame"
    front = bytes_[0]
    rear = bytes_[1]
    return f"front_raw={front} front_pct={front * 0.5:.1f}% rear_raw={rear} rear_pct={rear * 0.5:.1f}%"


def decode_frame(can_id, data_bytes):
    if can_id in CAN_RX_IDS:
        label = CAN_RX_IDS[can_id]
        if can_id == 0x520:
            return f"[RX] 0x{can_id:03X} {label}  {decode_rx_status(data_bytes)}"
        if can_id == 0x523:
            return f"[RX] 0x{can_id:03X} {label}  {decode_rx_steer(data_bytes)}"
        if can_id == 0x524:
            return f"[RX] 0x{can_id:03X} {label}  {decode_rx_brake(data_bytes)}"
        if can_id == 0x525:
            return f"[RX] 0x{can_id:03X} {label}  {decode_rx_wheel_speeds(data_bytes)}"
        if can_id == 0x526:
            return f"[RX] 0x{can_id:03X} {label}  {decode_rx_wheel_counts(data_bytes)}"
        return f"[RX] 0x{can_id:03X} {label}  raw={format_hex(data_bytes)}"
    if can_id in CAN_TX_IDS:
        label = CAN_TX_IDS[can_id]
        if can_id == 0x510:
            return f"[TX] 0x{can_id:03X} {label}  {decode_tx_status(data_bytes)}"
        if can_id == 0x511:
            return f"[TX] 0x{can_id:03X} {label}  {decode_tx_drive(data_bytes, 'front')}"
        if can_id == 0x512:
            return f"[TX] 0x{can_id:03X} {label}  {decode_tx_drive(data_bytes, 'rear')}"
        if can_id == 0x513:
            return f"[TX] 0x{can_id:03X} {label}  {decode_tx_steer(data_bytes)}"
        if can_id == 0x514:
            return f"[TX] 0x{can_id:03X} {label}  {decode_tx_brake(data_bytes)}"
        return f"[TX] 0x{can_id:03X} {label}  raw={format_hex(data_bytes)}"
    return f"[??] 0x{can_id:03X}  raw={format_hex(data_bytes)}"


def process_line(line):
    line = line.rstrip("\n")
    match = LINE_RE.match(line)
    if not match:
        match = LINE_RE_ALT.match(line)
        if not match:
            return None

    can_id = int(match.group("id"), 16)
    data_bytes = parse_bytes(match.group("data"))
    if not data_bytes:
        return None
    return decode_frame(can_id, data_bytes)


def main():
    if len(sys.argv) > 2:
        print(f"Usage: {sys.argv[0]} [candump.log]", file=sys.stderr)
        return 1

    source = sys.stdin
    if len(sys.argv) == 2:
        try:
            source = open(sys.argv[1], "r", encoding="utf-8")
        except OSError as exc:
            print(f"Failed to open {sys.argv[1]}: {exc}", file=sys.stderr)
            return 1

    with source:
        for line in source:
            decoded = process_line(line)
            if decoded:
                print(decoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
