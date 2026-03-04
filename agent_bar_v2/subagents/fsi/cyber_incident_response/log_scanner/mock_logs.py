MOCK_LOGS = [
    {
        "timestamp": "2023-10-27T10:00:00Z",
        "source_ip": "192.168.1.10",
        "destination_ip": "10.0.0.5",
        "action": "LOGIN_ATTEMPT",
        "status": "SUCCESS",
        "user": "admin"
    },
    {
        "timestamp": "2023-10-27T10:05:00Z",
        "source_ip": "203.0.113.42",
        "destination_ip": "10.0.0.5",
        "action": "LOGIN_ATTEMPT",
        "status": "FAILURE",
        "user": "admin"
    },
    {
        "timestamp": "2023-10-27T10:05:01Z",
        "source_ip": "203.0.113.42",
        "destination_ip": "10.0.0.5",
        "action": "LOGIN_ATTEMPT",
        "status": "FAILURE",
        "user": "admin"
    },
    {
        "timestamp": "2023-10-27T10:05:02Z",
        "source_ip": "203.0.113.42",
        "destination_ip": "10.0.0.5",
        "action": "LOGIN_ATTEMPT",
        "status": "FAILURE",
        "user": "admin"
    },
    {
        "timestamp": "2023-10-27T10:05:03Z",
        "source_ip": "203.0.113.42",
        "destination_ip": "10.0.0.5",
        "action": "LOGIN_ATTEMPT",
        "status": "SUCCESS",
        "user": "admin"
    },
    {
        "timestamp": "2023-10-27T10:10:00Z",
        "source_ip": "203.0.113.42",
        "destination_ip": "10.0.0.5",
        "action": "DATA_EXFILTRATION",
        "status": "DETECTED",
        "details": "Large file transfer to external IP"
    }
]
