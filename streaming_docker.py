import os
import subprocess
import sys
from typing import Any

from minisweagent.environments.docker import DockerEnvironment


class StreamingDockerEnvironment(DockerEnvironment):
    # def execute(self, command: str, cwd: str = "") -> dict[str, Any]:
    #     """Execute a command in the Docker container and return the result as a dict."""
    #     cwd = cwd or self.config.cwd
    #     assert self.container_id, "Container not started"

    #     cmd = [self.config.executable, "exec", "-w", cwd]
    #     for key in self.config.forward_env:
    #         if (value := os.getenv(key)) is not None:
    #             cmd.extend(["-e", f"{key}={value}"])
    #     for key, value in self.config.env.items():
    #         cmd.extend(["-e", f"{key}={value}"])
    #     cmd.extend([self.container_id, "bash", "-lc", command])

    #     result = subprocess.run(
    #         cmd,
    #         text=True,
    #         timeout=self.config.timeout,
    #         encoding="utf-8",
    #         errors="replace",
    #         stdout=subprocess.PIPE,
    #         stderr=subprocess.STDOUT,
    #     )
    #     return {"output": result.stdout, "returncode": result.returncode}

    def execute(self, command: str, cwd: str = "") -> dict[str, Any]:
        """Execute a command in the Docker container, streaming output to stdout."""
        cwd = cwd or self.config.cwd
        assert self.container_id, "Container not started"

        cmd = [self.config.executable, "exec", "-w", cwd]
        for key in self.config.forward_env:
            if (value := os.getenv(key)) is not None:
                cmd.extend(["-e", f"{key}={value}"])
        for key, value in self.config.env.items():
            cmd.extend(["-e", f"{key}={value}"])
        cmd.extend([self.container_id, "bash", "-lc", command])

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        output_lines: list[str] = []
        assert process.stdout is not None
        try:
            for line in process.stdout:
                print(line, end="")
                output_lines.append(line)
            returncode = process.wait(timeout=self.config.timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            print(f"\nCommand timed out after {self.config.timeout}s", file=sys.stderr)
            returncode = -1
        finally:
            process.stdout.close()

        return {"output": "".join(output_lines), "returncode": returncode}
