import os

import paramiko
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


app = FastAPI(title="Cisco Paramiko Automation")


SSH_USERNAME = os.getenv("SSH_USERNAME", "admin")
SSH_PASSWORD = os.getenv("SSH_PASSWORD", "cisco")
SSH_PORT = int(os.getenv("SSH_PORT", "22"))


class CommandRequest(BaseModel):
    router_ip: str
    command: str


def execute_ssh_command(router_ip: str, command: str) -> str:

    client = paramiko.SSHClient()

    # Lab environment.
    # In production, verify the router's host key.
    client.set_missing_host_key_policy(
        paramiko.AutoAddPolicy()
    )

    try:

        print(f"Connecting to {router_ip}:{SSH_PORT}")

        client.connect(
            hostname=router_ip,
            port=SSH_PORT,
            username=SSH_USERNAME,
            password=SSH_PASSWORD,
            timeout=10,
            look_for_keys=False,
            allow_agent=False,
        )

        print(f"Executing command: {command}")

        stdin, stdout, stderr = client.exec_command(command)

        output = stdout.read().decode(
            errors="replace"
        )

        error = stderr.read().decode(
            errors="replace"
        )

        if error:
            return output + "\nERROR:\n" + error

        return output

    finally:

        client.close()

        print("SSH connection closed")


@app.get("/")
def root():

    return {
        "message": "Cisco Paramiko Backend is running"
    }


@app.get("/api/health")
def health():

    return {
        "status": "ok"
    }


@app.post("/api/execute")
def execute(request: CommandRequest):

    router_ip = request.router_ip.strip()
    command = request.command.strip()

    if not router_ip:
        raise HTTPException(
            status_code=400,
            detail="Router IP is required"
        )

    if not command:
        raise HTTPException(
            status_code=400,
            detail="Command is required"
        )

    try:

        output = execute_ssh_command(
            router_ip,
            command
        )

        return {
            "success": True,
            "router_ip": router_ip,
            "command": command,
            "output": output,
        }

    except paramiko.AuthenticationException:

        raise HTTPException(
            status_code=401,
            detail="SSH authentication failed"
        )

    except paramiko.SSHException as exc:

        raise HTTPException(
            status_code=502,
            detail=f"SSH error: {exc}"
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=f"Connection failed: {exc}"
        )
