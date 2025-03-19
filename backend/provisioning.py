import subprocess
import uuid
import os
import time

instances = []

VM_IMAGES = {
    "Ubuntu": "images/focal-server-cloudimg-amd64.img",
    "CentOS": "images/CentOS-7-x86_64-GenericCloud.qcow2",
}

CONTAINER_IMAGES = {
    "Ubuntu": "ubuntu:latest",
    "CentOS": "centos:latest",
}


class VMProvisioner:
    def __init__(self):
        pass

    def create_instance(self, os_choice: str, memory: int, cpus: int, disk_space: int, runtime: int,
                        graphic: bool = True, seed_iso: str = None):
        """
        Создает виртуальную машину с использованием QEMU
        """
        if os_choice not in VM_IMAGES:
            raise ValueError("Unsupported OS selected for VM.")
        image_path = VM_IMAGES[os_choice]
        if not os.path.exists(image_path):
            raise RuntimeError(f"Файл образа не найден: {image_path}")
        instance_id = str(uuid.uuid4())
        cmd = [
            "qemu-system-x86_64",
            "-hda", image_path,
            "-m", str(memory),
            "-smp", str(cpus),
            "-net", "nic",
            "-net", "user"
        ]
        if seed_iso and os.path.exists(seed_iso):
            cmd += ["-cdrom", seed_iso, "-boot", "order=dc,menu=on"]
        else:
            cmd += ["-boot", "order=c,menu=on"]
        if graphic:
            cmd += ["-display", "sdl"]
        else:
            cmd += ["-nographic"]
        try:
            process = subprocess.Popen(cmd)
        except Exception as e:
            raise RuntimeError(f"Ошибка запуска QEMU: {str(e)}")
        instance_info = {
            "id": instance_id,
            "type": "vm",
            "os": os_choice,
            "image": image_path,
            "memory": memory,
            "cpus": cpus,
            "disk_space": disk_space,
            "runtime": runtime,
            "pid": process.pid,
            "created_at": time.time(),
            "status": "running"
        }
        instances.append(instance_info)
        return instance_info


class ContainerProvisioner:
    def __init__(self):
        pass

    def create_instance(self, os_choice: str, memory: int, cpus: int, runtime: int, disk_space: int = None):
        """
        Создает Docker-контейнер
        Команда:
          docker run -d --name <container_name> --memory <memory>m --cpus <cpus> <image> tail -f /dev/null
        """
        if os_choice not in CONTAINER_IMAGES:
            raise ValueError("Unsupported OS selected for container")
        image = CONTAINER_IMAGES[os_choice]
        instance_id = str(uuid.uuid4())
        container_name = f"container_{instance_id[:8]}"

        try:
            subprocess.run(["docker", "rm", "-f", container_name], check=False)
        except Exception:
            pass

        cmd = [
            "docker", "run", "-d",
            "--name", container_name,
            "--memory", f"{memory}m",
            "--cpus", str(cpus),
            image,
            "tail", "-f", "/dev/null"
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            raise RuntimeError("Error creating container: " + result.stderr)
        container_id = result.stdout.strip()
        instance_info = {
            "id": instance_id,
            "type": "container",
            "os": os_choice,
            "memory": memory,
            "cpus": cpus,
            "runtime": runtime,
            "disk_space": disk_space,
            "container_name": container_name,
            "container_id": container_id,
            "created_at": time.time(),
            "status": "running"
        }
        instances.append(instance_info)
        return instance_info


def list_instances():
    return instances
