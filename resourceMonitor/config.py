"""
설정 관리 모듈
시스템 모니터링 설정을 관리합니다.
"""

import os
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class MonitoringConfig:
    """모니터링 설정 클래스"""

    # 모니터링 설정
    monitoring_duration: int = 300  # 5분 (초 단위)
    sampling_interval: float = 1.0  # 1초마다 데이터 수집

    # 임계값 설정 (경고 표시용)
    cpu_warning_threshold: float = 70.0  # CPU 사용률 70% 이상 주의
    cpu_critical_threshold: float = 90.0  # CPU 사용률 90% 이상 위험

    memory_warning_threshold: float = 70.0  # 메모리 사용률 70% 이상 주의
    memory_critical_threshold: float = 85.0  # 메모리 사용률 85% 이상 위험

    disk_warning_threshold: float = 75.0  # 디스크 사용률 75% 이상 주의
    disk_critical_threshold: float = 90.0  # 디스크 사용률 90% 이상 위험

    gpu_warning_threshold: float = 75.0  # GPU 사용률 75% 이상 주의
    gpu_critical_threshold: float = 90.0  # GPU 사용률 90% 이상 위험

    temp_warning_threshold: float = 70.0  # 온도 70°C 이상 주의
    temp_critical_threshold: float = 85.0  # 온도 85°C 이상 위험

    # 디스플레이 설정
    top_processes_count: int = 5  # 상위 프로세스 개수

    # 파일 경로 설정
    reports_dir: str = "reports"  # PDF 보고서 저장 디렉토리
    data_dir: str = "data"  # 데이터 저장 디렉토리

    # 대시보드 설정
    dashboard_host: str = "127.0.0.1"
    dashboard_port: int = 8050
    dashboard_debug: bool = False

    # 색상 설정
    color_normal: str = "#28a745"  # 녹색
    color_warning: str = "#ffc107"  # 노란색
    color_critical: str = "#dc3545"  # 빨간색

    def __post_init__(self):
        """초기화 후 디렉토리 생성"""
        os.makedirs(self.reports_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)

    def get_status_color(self, value: float, warning: float, critical: float) -> str:
        """값에 따른 상태 색상 반환"""
        if value >= critical:
            return self.color_critical
        elif value >= warning:
            return self.color_warning
        else:
            return self.color_normal

    def get_cpu_status(self, cpu_percent: float) -> tuple[str, str]:
        """CPU 상태 반환 (상태, 색상)"""
        if cpu_percent >= self.cpu_critical_threshold:
            return "위험", self.color_critical
        elif cpu_percent >= self.cpu_warning_threshold:
            return "주의", self.color_warning
        else:
            return "정상", self.color_normal

    def get_memory_status(self, memory_percent: float) -> tuple[str, str]:
        """메모리 상태 반환 (상태, 색상)"""
        if memory_percent >= self.memory_critical_threshold:
            return "위험", self.color_critical
        elif memory_percent >= self.memory_warning_threshold:
            return "주의", self.color_warning
        else:
            return "정상", self.color_normal

    def get_disk_status(self, disk_percent: float) -> tuple[str, str]:
        """디스크 상태 반환 (상태, 색상)"""
        if disk_percent >= self.disk_critical_threshold:
            return "위험", self.color_critical
        elif disk_percent >= self.disk_warning_threshold:
            return "주의", self.color_warning
        else:
            return "정상", self.color_normal

    def get_gpu_status(self, gpu_percent: float) -> tuple[str, str]:
        """GPU 상태 반환 (상태, 색상)"""
        if gpu_percent >= self.gpu_critical_threshold:
            return "위험", self.color_critical
        elif gpu_percent >= self.gpu_warning_threshold:
            return "주의", self.color_warning
        else:
            return "정상", self.color_normal

    def get_temp_status(self, temp: float) -> tuple[str, str]:
        """온도 상태 반환 (상태, 색상)"""
        if temp >= self.temp_critical_threshold:
            return "위험", self.color_critical
        elif temp >= self.temp_warning_threshold:
            return "주의", self.color_warning
        else:
            return "정상", self.color_normal

    def to_dict(self) -> Dict[str, Any]:
        """설정을 딕셔너리로 변환"""
        return {
            'monitoring_duration': self.monitoring_duration,
            'sampling_interval': self.sampling_interval,
            'cpu_warning_threshold': self.cpu_warning_threshold,
            'cpu_critical_threshold': self.cpu_critical_threshold,
            'memory_warning_threshold': self.memory_warning_threshold,
            'memory_critical_threshold': self.memory_critical_threshold,
            'disk_warning_threshold': self.disk_warning_threshold,
            'disk_critical_threshold': self.disk_critical_threshold,
            'gpu_warning_threshold': self.gpu_warning_threshold,
            'gpu_critical_threshold': self.gpu_critical_threshold,
            'temp_warning_threshold': self.temp_warning_threshold,
            'temp_critical_threshold': self.temp_critical_threshold,
            'top_processes_count': self.top_processes_count,
        }


# 기본 설정 인스턴스
config = MonitoringConfig()
