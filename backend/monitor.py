import os
import signal
import subprocess
import time
from backend.provisioning import instances

def stop_vm(instance):
    try:
        os.kill(instance["pid"], signal.SIGTERM)
        instance["status"] = "stopped"
        return True
    except Exception as e:
        print(f"Error stopping VM {instance['id']}: {e}")
        return False

def delete_vm(instance):
    if instance["status"] != "stopped":
        stop_vm(instance)
    instance["status"] = "deleted"
    return True

def stop_container(instance):
    try:
        cmd = ["docker", "stop", instance["container_name"]]
        subprocess.check_output(cmd)
        instance["status"] = "stopped"
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error stopping container {instance['id']}: {e}")
        return False

def start_container(instance):
    try:
        cmd = ["docker", "start", instance["container_name"]]
        subprocess.check_output(cmd)
        instance["status"] = "running"
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error starting container {instance['id']}: {e}")
        return False

def stop_instance(instance_id):
    for instance in instances:
        if instance["id"] == instance_id:
            if instance["type"] == "vm":
                return stop_vm(instance)
            elif instance["type"] == "container":
                return stop_container(instance)
    return False

def start_instance(instance_id):
    for instance in instances:
        if instance["id"] == instance_id:
            if instance["type"] == "vm":

                return False
            elif instance["type"] == "container":
                return start_container(instance)
    return False

def delete_instance(instance_id):
    for instance in instances:
        if instance["id"] == instance_id:
            if instance["type"] == "vm":
                if not delete_vm(instance):
                    return False
            elif instance["type"] == "container":
                try:
                    cmd = ["docker", "rm", "-f", instance["container_name"]]
                    subprocess.check_output(cmd)
                except Exception as e:
                    print(f"Error deleting container {instance['id']}: {e}")
            instances.remove(instance)
            return True
    return False

def check_and_terminate():
    current_time = time.time()
    terminated = []
    for instance in instances:
        runtime_elapsed = current_time - instance["created_at"]
        if runtime_elapsed > instance["runtime"] and instance["status"] == "running":
            if instance["type"] == "vm":
                if stop_vm(instance):
                    terminated.append(instance)
            elif instance["type"] == "container":
                if stop_container(instance):
                    terminated.append(instance)
    return terminated

def list_running_instances():

    return instances

def reinstall_instance(instance_id):
    for instance in instances:
        if instance["id"] == instance_id:
            if instance["type"] == "vm":
                if instance["status"] == "running":
                    stop_vm(instance)
                if not delete_vm(instance):
                    return f"Error deleting VM."
                from backend.provisioning import VMProvisioner
                provisioner = VMProvisioner()
                new_instance = provisioner.create_instance(
                    instance["os"],
                    instance["memory"],
                    instance["cpus"],
                    instance["disk_space"],
                    instance["runtime"]
                )
                return new_instance
            elif instance["type"] == "container":
                if instance["status"] == "running":
                    stop_container(instance)
                try:
                    cmd = ["docker", "rm", "-f", instance["container_name"]]
                    subprocess.check_output(cmd)
                except Exception as e:
                    print(f"Error force removing container {instance['id']}: {e}")
                from backend.provisioning import ContainerProvisioner
                provisioner = ContainerProvisioner()
                new_instance = provisioner.create_instance(
                    instance["os"],
                    instance["memory"],
                    instance["cpus"],
                    instance["runtime"],
                    instance.get("disk_space", None)
                )
                return new_instance
    return {"error": "Instance not found"}
