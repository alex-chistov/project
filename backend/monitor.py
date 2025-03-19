# backend/monitor.py
import os
import signal
import subprocess
import time
from backend.provisioning import instances

# Критерий – время жизни инстанса (например, 5 минут = 300 секунд)
MAX_RUNTIME = 300  # секунд

def check_and_terminate():
    """
    Функция, которая проверяет запущенные инстансы и завершает те, у которых время работы превышает MAX_RUNTIME.
    """
    current_time = time.time()
    terminated = []
    for instance in instances:
        runtime = current_time - instance["created_at"]
        if runtime > MAX_RUNTIME and instance["status"] == "running":
            if instance["type"] == "vm":
                try:
                    os.kill(instance["pid"], signal.SIGTERM)
                    instance["status"] = "terminated"
                    terminated.append(instance)
                except Exception as e:
                    print(f"Error terminating VM {instance['id']}: {e}")
            elif instance["type"] == "container":
                try:
                    cmd = ["docker", "stop", instance["container_name"]]
                    subprocess.check_output(cmd)
                    instance["status"] = "terminated"
                    terminated.append(instance)
                except Exception as e:
                    print(f"Error terminating container {instance['id']}: {e}")
    return terminated


def list_running_instances():
    """
    Возвращает список инстансов, статус которых "running".
    """
    return [inst for inst in instances if inst["status"] == "running"]


def reinstall_instance(instance_id):
    """
    Функция «перезаливки»: останавливает инстанс и создаёт новый с теми же параметрами.
    """
    for instance in instances:
        if instance["id"] == instance_id:
            # Останавливаем текущий инстанс
            if instance["type"] == "vm":
                try:
                    os.kill(instance["pid"], signal.SIGTERM)
                    instance["status"] = "terminated"
                except Exception as e:
                    return f"Error terminating VM: {e}"
            elif instance["type"] == "container":
                try:
                    cmd = ["docker", "stop", instance["container_name"]]
                    subprocess.check_output(cmd)
                    instance["status"] = "terminated"
                except Exception as e:
                    return f"Error terminating container: {e}"
            # Создаем новый инстанс с теми же параметрами
            from backend.provisioning import VMProvisioner, ContainerProvisioner
            if instance["type"] == "vm":
                provisioner = VMProvisioner()
                new_instance = provisioner.create_instance(instance["os"], instance["memory"], instance["cpus"])
            elif instance["type"] == "container":
                provisioner = ContainerProvisioner()
                new_instance = provisioner.create_instance(instance["os"], instance["memory"], instance["cpus"])
            return new_instance
    return "Instance not found"
