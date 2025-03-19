import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.append(project_root)

import streamlit as st
import time
from backend.provisioning import VMProvisioner, ContainerProvisioner, list_instances
from backend.monitor import (list_running_instances, check_and_terminate, reinstall_instance,
                             start_instance, stop_instance, delete_instance)

st.set_page_config(page_title="Сервис аренды виртуальных машин и контейнеров", layout="wide")
st.title("Хостинг-провайдер: Аренда ВМ и контейнеров")

menu = st.sidebar.radio("Выберите раздел", ["Создать экземпляр", "Мониторинг"])

if menu == "Создать экземпляр":
    st.header("Создание нового экземпляра")
    instance_type = st.selectbox("Тип экземпляра", ["Виртуальная машина", "Контейнер"])
    os_choice = st.selectbox("Выберите ОС", ["Ubuntu", "CentOS"])
    st.subheader("Ресурсы")
    if instance_type == "Виртуальная машина":
        memory = st.number_input("Оперативная память (МБ)", min_value=256, max_value=8192, value=1024, step=256)
        cpus = st.number_input("Количество CPU", min_value=1, max_value=8, value=2, step=1)
        disk_space = st.number_input("Объем дискового пространства (ГБ)", min_value=10, max_value=1024, value=50, step=1)
        runtime_minutes = st.number_input("Время работы (минут)", min_value=1, max_value=1440, value=5, step=1)
        runtime_seconds = runtime_minutes * 60
    else:
        memory = st.number_input("Ограничение памяти (МБ)", min_value=128, max_value=8192, value=512, step=128)
        cpus = st.number_input("Количество CPU", min_value=1, max_value=8, value=1, step=1)
        disk_space = st.number_input("Объем дискового пространства (ГБ) (необязательно)", min_value=0, max_value=1024, value=0, step=1)
        runtime_minutes = st.number_input("Время работы (минут)", min_value=1, max_value=1440, value=5, step=1)
        runtime_seconds = runtime_minutes * 60

    if st.button("Создать"):
        with st.spinner("Создаётся экземпляр..."):
            if instance_type == "Виртуальная машина":
                provisioner = VMProvisioner()
                # Передаем graphic=True для графического режима
                instance = provisioner.create_instance(os_choice, memory, cpus, disk_space, runtime_seconds, graphic=True)
            else:
                provisioner = ContainerProvisioner()
                instance = provisioner.create_instance(os_choice, memory, cpus, runtime_seconds, disk_space if disk_space > 0 else None)
            st.success("Экземпляр создан!")
            with st.expander("Детали экземпляра", expanded=False):
                st.json(instance)

elif menu == "Мониторинг":
    st.header("Мониторинг экземпляров")
    if st.button("Проверить и завершить истёкшие экземпляры"):
        terminated = check_and_terminate()
        if terminated:
            st.write("Завершены следующие экземпляры:")
            with st.expander("Детали завершённых экземпляров", expanded=False):
                st.json(terminated)
        else:
            st.write("Нет экземпляров, превышающих лимит времени.")

    running = list_running_instances()
    st.subheader("Экземпляры")
    if running:
        for inst in running:
            st.markdown(f"**ID:** {inst['id']}")
            st.markdown(f"**Тип:** {inst['type']}")
            st.markdown(f"**ОС:** {inst['os']}")
            st.markdown(f"**Ресурсы:** память - {inst['memory']} МБ, CPU - {inst['cpus']}, диск - {inst.get('disk_space', 'N/A')} ГБ, время - {inst.get('runtime', 'N/A')} сек")
            st.markdown(f"**Статус:** {inst['status']}")
            with st.expander("Детали экземпляра", expanded=False):
                st.json(inst)
            st.markdown("---")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                if st.button(f"Перезалить {inst['id']}", key=f"reinstall_{inst['id']}"):
                    new_inst = reinstall_instance(inst["id"])
                    if isinstance(new_inst, str):
                        st.error(new_inst)
                    else:
                        st.success("Экземпляр перезалит!")
                        with st.expander("Детали нового экземпляра", expanded=False):
                            st.json(new_inst)
            with col2:
                if st.button(f"Остановить {inst['id']}", key=f"stop_{inst['id']}"):
                    if stop_instance(inst["id"]):
                        st.success("Экземпляр остановлен!")
                    else:
                        st.error("Не удалось остановить экземпляр.")
            with col3:
                if st.button(f"Запустить {inst['id']}", key=f"start_{inst['id']}"):
                    if start_instance(inst["id"]):
                        st.success("Экземпляр запущен!")
                    else:
                        st.error("Не удалось запустить экземпляр. Для виртуальных машин поддерживается только перезаливка.")
            with col4:
                if st.button(f"Удалить {inst['id']}", key=f"delete_{inst['id']}"):
                    if delete_instance(inst["id"]):
                        st.success("Экземпляр удалён!")
                    else:
                        st.error("Не удалось удалить экземпляр.")
    else:
        st.write("Нет экземпляров.")
