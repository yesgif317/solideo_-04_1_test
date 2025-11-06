"""
데이터 저장 및 관리 모듈
수집된 시스템 리소스 데이터를 저장하고 분석합니다.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from config import config


class DataManager:
    """데이터 관리 클래스"""

    def __init__(self):
        """초기화"""
        self.data_history: List[Dict[str, Any]] = []
        self.session_start_time: Optional[datetime] = None
        self.session_end_time: Optional[datetime] = None

    def add_data(self, data: Dict[str, Any]):
        """데이터 추가"""
        self.data_history.append(data)

        if self.session_start_time is None:
            self.session_start_time = datetime.fromisoformat(data['timestamp'])

    def get_data_count(self) -> int:
        """수집된 데이터 개수 반환"""
        return len(self.data_history)

    def get_latest_data(self) -> Optional[Dict[str, Any]]:
        """최신 데이터 반환"""
        if self.data_history:
            return self.data_history[-1]
        return None

    def get_all_data(self) -> List[Dict[str, Any]]:
        """모든 데이터 반환"""
        return self.data_history

    def clear_data(self):
        """데이터 초기화"""
        self.data_history = []
        self.session_start_time = None
        self.session_end_time = None

    def finalize_session(self):
        """세션 종료"""
        if self.data_history:
            self.session_end_time = datetime.fromisoformat(self.data_history[-1]['timestamp'])

    def export_to_json(self, filepath: str):
        """JSON 파일로 내보내기"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({
                    'session_start': self.session_start_time.isoformat() if self.session_start_time else None,
                    'session_end': self.session_end_time.isoformat() if self.session_end_time else None,
                    'data_count': len(self.data_history),
                    'data': self.data_history
                }, f, indent=2, default=str)
            print(f"데이터를 {filepath}에 저장했습니다.")
            return True
        except Exception as e:
            print(f"JSON 내보내기 오류: {e}")
            return False

    def export_to_csv(self, filepath: str):
        """CSV 파일로 내보내기"""
        try:
            if not self.data_history:
                print("내보낼 데이터가 없습니다.")
                return False

            # DataFrame 생성 (단순 필드만)
            df_data = []
            for item in self.data_history:
                row = {
                    'timestamp': item['timestamp'],
                    'cpu_percent': item.get('cpu_percent', 0),
                    'memory_percent': item.get('memory_percent', 0),
                    'memory_used': item.get('memory_used', 0),
                    'memory_total': item.get('memory_total', 0),
                    'disk_read_speed': item.get('disk_read_speed', 0),
                    'disk_write_speed': item.get('disk_write_speed', 0),
                    'net_upload_speed': item.get('net_upload_speed', 0),
                    'net_download_speed': item.get('net_download_speed', 0),
                }
                df_data.append(row)

            df = pd.DataFrame(df_data)
            df.to_csv(filepath, index=False, encoding='utf-8')
            print(f"데이터를 {filepath}에 저장했습니다.")
            return True
        except Exception as e:
            print(f"CSV 내보내기 오류: {e}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """통계 정보 생성"""
        if not self.data_history:
            return {}

        try:
            # CPU 통계
            cpu_values = [item.get('cpu_percent', 0) for item in self.data_history]
            cpu_stats = {
                'avg': np.mean(cpu_values),
                'max': np.max(cpu_values),
                'min': np.min(cpu_values),
                'std': np.std(cpu_values),
            }

            # 메모리 통계
            memory_values = [item.get('memory_percent', 0) for item in self.data_history]
            memory_stats = {
                'avg': np.mean(memory_values),
                'max': np.max(memory_values),
                'min': np.min(memory_values),
                'std': np.std(memory_values),
            }

            # 디스크 통계
            disk_read_values = [item.get('disk_read_speed', 0) for item in self.data_history]
            disk_write_values = [item.get('disk_write_speed', 0) for item in self.data_history]
            disk_stats = {
                'read_avg': np.mean(disk_read_values),
                'read_max': np.max(disk_read_values),
                'write_avg': np.mean(disk_write_values),
                'write_max': np.max(disk_write_values),
            }

            # 네트워크 통계
            net_upload_values = [item.get('net_upload_speed', 0) for item in self.data_history]
            net_download_values = [item.get('net_download_speed', 0) for item in self.data_history]
            network_stats = {
                'upload_avg': np.mean(net_upload_values),
                'upload_max': np.max(net_upload_values),
                'download_avg': np.mean(net_download_values),
                'download_max': np.max(net_download_values),
            }

            # GPU 통계 (사용 가능한 경우)
            gpu_stats = {}
            if self.data_history[0].get('gpu_available', False):
                gpu_data = [item.get('gpus', []) for item in self.data_history]
                if gpu_data and len(gpu_data[0]) > 0:
                    gpu_load_values = [gpu[0].get('load', 0) for gpu in gpu_data if gpu]
                    gpu_temp_values = [gpu[0].get('temperature', 0) for gpu in gpu_data if gpu and gpu[0].get('temperature', 0) > 0]

                    gpu_stats = {
                        'load_avg': np.mean(gpu_load_values) if gpu_load_values else 0,
                        'load_max': np.max(gpu_load_values) if gpu_load_values else 0,
                        'temp_avg': np.mean(gpu_temp_values) if gpu_temp_values else 0,
                        'temp_max': np.max(gpu_temp_values) if gpu_temp_values else 0,
                    }

            # 온도 통계 (사용 가능한 경우)
            temp_stats = {}
            if self.data_history[0].get('temperature_available', False):
                # CPU 온도 추출 (일반적으로 'coretemp' 또는 'cpu_thermal')
                cpu_temps = []
                for item in self.data_history:
                    temps = item.get('temperatures', {})
                    for sensor_name, sensor_data in temps.items():
                        if 'coretemp' in sensor_name.lower() or 'cpu' in sensor_name.lower():
                            for sensor in sensor_data:
                                cpu_temps.append(sensor.get('current', 0))
                            break

                if cpu_temps:
                    temp_stats = {
                        'cpu_temp_avg': np.mean(cpu_temps),
                        'cpu_temp_max': np.max(cpu_temps),
                        'cpu_temp_min': np.min(cpu_temps),
                    }

            return {
                'session_duration': (self.session_end_time - self.session_start_time).total_seconds() if self.session_end_time and self.session_start_time else 0,
                'data_points': len(self.data_history),
                'cpu': cpu_stats,
                'memory': memory_stats,
                'disk': disk_stats,
                'network': network_stats,
                'gpu': gpu_stats,
                'temperature': temp_stats,
            }
        except Exception as e:
            print(f"통계 생성 오류: {e}")
            return {}

    def get_warnings(self) -> List[Dict[str, str]]:
        """경고 사항 생성"""
        warnings = []
        stats = self.get_statistics()

        if not stats:
            return warnings

        # CPU 경고
        cpu_stats = stats.get('cpu', {})
        if cpu_stats.get('max', 0) >= config.cpu_critical_threshold:
            warnings.append({
                'type': 'CPU',
                'level': 'critical',
                'message': f"CPU 사용률이 위험 수준에 도달했습니다 (최대: {cpu_stats['max']:.1f}%)"
            })
        elif cpu_stats.get('avg', 0) >= config.cpu_warning_threshold:
            warnings.append({
                'type': 'CPU',
                'level': 'warning',
                'message': f"CPU 평균 사용률이 높습니다 (평균: {cpu_stats['avg']:.1f}%)"
            })

        # 메모리 경고
        memory_stats = stats.get('memory', {})
        if memory_stats.get('max', 0) >= config.memory_critical_threshold:
            warnings.append({
                'type': 'Memory',
                'level': 'critical',
                'message': f"메모리 사용률이 위험 수준에 도달했습니다 (최대: {memory_stats['max']:.1f}%)"
            })
        elif memory_stats.get('avg', 0) >= config.memory_warning_threshold:
            warnings.append({
                'type': 'Memory',
                'level': 'warning',
                'message': f"메모리 평균 사용률이 높습니다 (평균: {memory_stats['avg']:.1f}%)"
            })

        # GPU 경고
        gpu_stats = stats.get('gpu', {})
        if gpu_stats.get('load_max', 0) >= config.gpu_critical_threshold:
            warnings.append({
                'type': 'GPU',
                'level': 'critical',
                'message': f"GPU 사용률이 위험 수준에 도달했습니다 (최대: {gpu_stats['load_max']:.1f}%)"
            })

        # 온도 경고
        temp_stats = stats.get('temperature', {})
        if temp_stats.get('cpu_temp_max', 0) >= config.temp_critical_threshold:
            warnings.append({
                'type': 'Temperature',
                'level': 'critical',
                'message': f"CPU 온도가 위험 수준에 도달했습니다 (최대: {temp_stats['cpu_temp_max']:.1f}°C)"
            })

        gpu_temp = gpu_stats.get('temp_max', 0)
        if gpu_temp >= config.temp_critical_threshold:
            warnings.append({
                'type': 'GPU Temperature',
                'level': 'critical',
                'message': f"GPU 온도가 위험 수준에 도달했습니다 (최대: {gpu_temp:.1f}°C)"
            })

        return warnings

    def get_dataframe(self) -> pd.DataFrame:
        """pandas DataFrame으로 변환"""
        if not self.data_history:
            return pd.DataFrame()

        df_data = []
        for item in self.data_history:
            row = {
                'timestamp': item['timestamp'],
                'cpu_percent': item.get('cpu_percent', 0),
                'memory_percent': item.get('memory_percent', 0),
                'memory_used': item.get('memory_used', 0),
                'memory_total': item.get('memory_total', 0),
                'disk_read_speed': item.get('disk_read_speed', 0),
                'disk_write_speed': item.get('disk_write_speed', 0),
                'net_upload_speed': item.get('net_upload_speed', 0),
                'net_download_speed': item.get('net_download_speed', 0),
            }

            # GPU 정보 (사용 가능한 경우)
            if item.get('gpu_available', False) and item.get('gpus', []):
                gpu = item['gpus'][0]
                row['gpu_load'] = gpu.get('load', 0)
                row['gpu_memory_percent'] = gpu.get('memory_percent', 0)
                row['gpu_temperature'] = gpu.get('temperature', 0)

            df_data.append(row)

        return pd.DataFrame(df_data)


if __name__ == "__main__":
    # 테스트 코드
    manager = DataManager()
    print("DataManager 테스트")
