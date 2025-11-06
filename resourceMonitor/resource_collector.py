"""
시스템 리소스 수집 모듈
CPU, GPU, 메모리, 디스크, 네트워크, 온도 등의 시스템 리소스를 수집합니다.
"""

import psutil
import platform
from datetime import datetime
from typing import Dict, List, Optional, Any
import warnings

# GPU 모니터링 라이브러리 (선택적)
try:
    import GPUtil
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False
    warnings.warn("GPUtil을 사용할 수 없습니다. GPU 모니터링이 비활성화됩니다.")


class ResourceCollector:
    """시스템 리소스 수집 클래스"""

    def __init__(self):
        """초기화"""
        self.platform = platform.system()
        self.platform_version = platform.version()
        self.processor = platform.processor()
        self.cpu_count = psutil.cpu_count(logical=True)
        self.cpu_count_physical = psutil.cpu_count(logical=False)

        # 네트워크/디스크 I/O 초기 측정 (델타 계산용)
        self.last_net_io = psutil.net_io_counters()
        self.last_disk_io = psutil.disk_io_counters()
        self.last_measurement_time = datetime.now()

    def get_system_info(self) -> Dict[str, Any]:
        """시스템 기본 정보 수집"""
        return {
            'platform': self.platform,
            'platform_version': self.platform_version,
            'processor': self.processor,
            'cpu_count_logical': self.cpu_count,
            'cpu_count_physical': self.cpu_count_physical,
            'hostname': platform.node(),
            'architecture': platform.machine(),
        }

    def get_cpu_info(self) -> Dict[str, Any]:
        """CPU 정보 수집"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_percent_per_core = psutil.cpu_percent(interval=0.1, percpu=True)
            cpu_freq = psutil.cpu_freq()
            cpu_stats = psutil.cpu_stats()

            return {
                'cpu_percent': cpu_percent,
                'cpu_percent_per_core': cpu_percent_per_core,
                'cpu_freq_current': cpu_freq.current if cpu_freq else 0,
                'cpu_freq_min': cpu_freq.min if cpu_freq else 0,
                'cpu_freq_max': cpu_freq.max if cpu_freq else 0,
                'cpu_ctx_switches': cpu_stats.ctx_switches,
                'cpu_interrupts': cpu_stats.interrupts,
                'cpu_soft_interrupts': cpu_stats.soft_interrupts,
                'cpu_syscalls': getattr(cpu_stats, 'syscalls', 0),
            }
        except Exception as e:
            print(f"CPU 정보 수집 중 오류: {e}")
            return {
                'cpu_percent': 0,
                'cpu_percent_per_core': [0] * self.cpu_count,
                'cpu_freq_current': 0,
                'cpu_freq_min': 0,
                'cpu_freq_max': 0,
                'cpu_ctx_switches': 0,
                'cpu_interrupts': 0,
                'cpu_soft_interrupts': 0,
                'cpu_syscalls': 0,
            }

    def get_memory_info(self) -> Dict[str, Any]:
        """메모리 정보 수집"""
        try:
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()

            return {
                'memory_total': mem.total,
                'memory_available': mem.available,
                'memory_used': mem.used,
                'memory_percent': mem.percent,
                'memory_free': mem.free,
                'swap_total': swap.total,
                'swap_used': swap.used,
                'swap_free': swap.free,
                'swap_percent': swap.percent,
            }
        except Exception as e:
            print(f"메모리 정보 수집 중 오류: {e}")
            return {
                'memory_total': 0,
                'memory_available': 0,
                'memory_used': 0,
                'memory_percent': 0,
                'memory_free': 0,
                'swap_total': 0,
                'swap_used': 0,
                'swap_free': 0,
                'swap_percent': 0,
            }

    def get_disk_info(self) -> Dict[str, Any]:
        """디스크 정보 수집"""
        try:
            disk_partitions = psutil.disk_partitions()
            disk_usage_list = []

            for partition in disk_partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_usage_list.append({
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'fstype': partition.fstype,
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': usage.percent,
                    })
                except PermissionError:
                    continue

            # 디스크 I/O
            current_disk_io = psutil.disk_io_counters()
            current_time = datetime.now()
            time_delta = (current_time - self.last_measurement_time).total_seconds()

            if time_delta > 0 and self.last_disk_io:
                read_speed = (current_disk_io.read_bytes - self.last_disk_io.read_bytes) / time_delta
                write_speed = (current_disk_io.write_bytes - self.last_disk_io.write_bytes) / time_delta
            else:
                read_speed = 0
                write_speed = 0

            self.last_disk_io = current_disk_io

            return {
                'disk_usage': disk_usage_list,
                'disk_read_bytes': current_disk_io.read_bytes,
                'disk_write_bytes': current_disk_io.write_bytes,
                'disk_read_speed': read_speed,
                'disk_write_speed': write_speed,
                'disk_read_count': current_disk_io.read_count,
                'disk_write_count': current_disk_io.write_count,
            }
        except Exception as e:
            print(f"디스크 정보 수집 중 오류: {e}")
            return {
                'disk_usage': [],
                'disk_read_bytes': 0,
                'disk_write_bytes': 0,
                'disk_read_speed': 0,
                'disk_write_speed': 0,
                'disk_read_count': 0,
                'disk_write_count': 0,
            }

    def get_network_info(self) -> Dict[str, Any]:
        """네트워크 정보 수집"""
        try:
            current_net_io = psutil.net_io_counters()
            current_time = datetime.now()
            time_delta = (current_time - self.last_measurement_time).total_seconds()

            if time_delta > 0 and self.last_net_io:
                upload_speed = (current_net_io.bytes_sent - self.last_net_io.bytes_sent) / time_delta
                download_speed = (current_net_io.bytes_recv - self.last_net_io.bytes_recv) / time_delta
            else:
                upload_speed = 0
                download_speed = 0

            self.last_net_io = current_net_io
            self.last_measurement_time = current_time

            # 네트워크 인터페이스 정보
            net_if_addrs = psutil.net_if_addrs()
            net_if_stats = psutil.net_if_stats()

            interfaces = []
            for interface_name, addrs in net_if_addrs.items():
                if interface_name in net_if_stats:
                    stats = net_if_stats[interface_name]
                    interfaces.append({
                        'name': interface_name,
                        'is_up': stats.isup,
                        'speed': stats.speed,
                        'addresses': [{'address': addr.address, 'family': str(addr.family)} for addr in addrs]
                    })

            return {
                'net_bytes_sent': current_net_io.bytes_sent,
                'net_bytes_recv': current_net_io.bytes_recv,
                'net_upload_speed': upload_speed,
                'net_download_speed': download_speed,
                'net_packets_sent': current_net_io.packets_sent,
                'net_packets_recv': current_net_io.packets_recv,
                'net_errin': current_net_io.errin,
                'net_errout': current_net_io.errout,
                'net_dropin': current_net_io.dropin,
                'net_dropout': current_net_io.dropout,
                'interfaces': interfaces,
            }
        except Exception as e:
            print(f"네트워크 정보 수집 중 오류: {e}")
            return {
                'net_bytes_sent': 0,
                'net_bytes_recv': 0,
                'net_upload_speed': 0,
                'net_download_speed': 0,
                'net_packets_sent': 0,
                'net_packets_recv': 0,
                'net_errin': 0,
                'net_errout': 0,
                'net_dropin': 0,
                'net_dropout': 0,
                'interfaces': [],
            }

    def get_gpu_info(self) -> Dict[str, Any]:
        """GPU 정보 수집"""
        if not GPU_AVAILABLE:
            return {
                'gpu_available': False,
                'gpus': []
            }

        try:
            gpus = GPUtil.getGPUs()
            gpu_list = []

            for gpu in gpus:
                gpu_list.append({
                    'id': gpu.id,
                    'name': gpu.name,
                    'load': gpu.load * 100,  # 0-1 범위를 0-100으로 변환
                    'memory_used': gpu.memoryUsed,
                    'memory_total': gpu.memoryTotal,
                    'memory_percent': (gpu.memoryUsed / gpu.memoryTotal * 100) if gpu.memoryTotal > 0 else 0,
                    'temperature': gpu.temperature,
                })

            return {
                'gpu_available': True,
                'gpus': gpu_list
            }
        except Exception as e:
            print(f"GPU 정보 수집 중 오류: {e}")
            return {
                'gpu_available': False,
                'gpus': []
            }

    def get_temperature_info(self) -> Dict[str, Any]:
        """온도 정보 수집"""
        try:
            if hasattr(psutil, "sensors_temperatures"):
                temps = psutil.sensors_temperatures()
                temp_data = {}

                for name, entries in temps.items():
                    temp_data[name] = []
                    for entry in entries:
                        temp_data[name].append({
                            'label': entry.label or name,
                            'current': entry.current,
                            'high': entry.high if entry.high else None,
                            'critical': entry.critical if entry.critical else None,
                        })

                return {
                    'temperature_available': True,
                    'temperatures': temp_data
                }
            else:
                return {
                    'temperature_available': False,
                    'temperatures': {}
                }
        except Exception as e:
            print(f"온도 정보 수집 중 오류: {e}")
            return {
                'temperature_available': False,
                'temperatures': {}
            }

    def get_top_processes(self, count: int = 5) -> List[Dict[str, Any]]:
        """상위 프로세스 정보 수집"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'username']):
                try:
                    pinfo = proc.info
                    processes.append({
                        'pid': pinfo['pid'],
                        'name': pinfo['name'],
                        'cpu_percent': pinfo['cpu_percent'] or 0,
                        'memory_percent': pinfo['memory_percent'] or 0,
                        'username': pinfo['username'],
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # CPU 사용률 기준 정렬
            top_cpu = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:count]
            # 메모리 사용률 기준 정렬
            top_memory = sorted(processes, key=lambda x: x['memory_percent'], reverse=True)[:count]

            return {
                'top_cpu_processes': top_cpu,
                'top_memory_processes': top_memory,
            }
        except Exception as e:
            print(f"프로세스 정보 수집 중 오류: {e}")
            return {
                'top_cpu_processes': [],
                'top_memory_processes': [],
            }

    def collect_all(self) -> Dict[str, Any]:
        """모든 리소스 정보 수집"""
        timestamp = datetime.now()

        data = {
            'timestamp': timestamp.isoformat(),
            'timestamp_unix': timestamp.timestamp(),
        }

        # 모든 정보 수집
        data.update(self.get_cpu_info())
        data.update(self.get_memory_info())
        data.update(self.get_disk_info())
        data.update(self.get_network_info())
        data.update(self.get_gpu_info())
        data.update(self.get_temperature_info())
        data.update(self.get_top_processes())

        return data


if __name__ == "__main__":
    # 테스트 코드
    collector = ResourceCollector()
    print("시스템 정보:")
    print(collector.get_system_info())
    print("\n현재 리소스 정보:")
    import json
    print(json.dumps(collector.collect_all(), indent=2, default=str))
