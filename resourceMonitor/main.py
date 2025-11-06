#!/usr/bin/env python3
"""
시스템 리소스 실시간 모니터링 시스템
메인 애플리케이션

사용법:
    python main.py [옵션]

옵션:
    --duration SECONDS    모니터링 시간 (초), 기본값: 300 (5분)
    --interval SECONDS    샘플링 간격 (초), 기본값: 1
    --no-dashboard       대시보드 없이 실행 (백그라운드 모니터링만)
    --output PATH        PDF 보고서 출로 경로, 기본값: reports/report_TIMESTAMP.pdf
    --help               도움말 표시
"""

import os
import sys
import argparse
import time
import threading
from datetime import datetime
import signal

from config import config, MonitoringConfig
from resource_collector import ResourceCollector
from data_manager import DataManager
from pdf_generator import PDFGenerator
from dashboard import Dashboard


class SystemMonitor:
    """시스템 모니터링 메인 클래스"""

    def __init__(self, monitoring_config: MonitoringConfig = None):
        """초기화

        Args:
            monitoring_config: 모니터링 설정
        """
        self.config = monitoring_config or config
        self.resource_collector = ResourceCollector()
        self.data_manager = DataManager()
        self.dashboard = None

        self.monitoring_thread = None
        self.dashboard_thread = None
        self.is_monitoring = False
        self.is_paused = False

        # 시그널 핸들러 설정
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """시그널 핸들러 (Ctrl+C 등)"""
        print("\n\n모니터링을 중지합니다...")
        self.stop()
        sys.exit(0)

    def start_monitoring(self):
        """모니터링 시작"""
        print("=" * 60)
        print("시스템 리소스 모니터링 시작")
        print("=" * 60)

        # 시스템 정보 출력
        system_info = self.resource_collector.get_system_info()
        print(f"\n운영체제: {system_info['platform']} {system_info.get('platform_version', '')}")
        print(f"프로세서: {system_info['processor']}")
        print(f"CPU 코어: {system_info['cpu_count_physical']} 물리 / {system_info['cpu_count_logical']} 논리")
        print(f"호스트명: {system_info['hostname']}")

        print(f"\n모니터링 설정:")
        print(f"  - 모니터링 시간: {self.config.monitoring_duration}초 ({self.config.monitoring_duration/60:.1f}분)")
        print(f"  - 샘플링 간격: {self.config.sampling_interval}초")
        print(f"  - 데이터 포인트: 약 {int(self.config.monitoring_duration / self.config.sampling_interval)}개")

        print(f"\n임계값 설정:")
        print(f"  - CPU: 주의 {self.config.cpu_warning_threshold}%, 위험 {self.config.cpu_critical_threshold}%")
        print(f"  - 메모리: 주의 {self.config.memory_warning_threshold}%, 위험 {self.config.memory_critical_threshold}%")
        print(f"  - GPU: 주의 {self.config.gpu_warning_threshold}%, 위험 {self.config.gpu_critical_threshold}%")
        print(f"  - 온도: 주의 {self.config.temp_warning_threshold}°C, 위험 {self.config.temp_critical_threshold}°C")

        print("\n" + "=" * 60)
        print("모니터링 중... (Ctrl+C로 중지)")
        print("=" * 60 + "\n")

        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()

    def _monitoring_loop(self):
        """모니터링 루프"""
        start_time = time.time()
        sample_count = 0

        while self.is_monitoring:
            elapsed = time.time() - start_time

            # 모니터링 시간 종료 확인
            if elapsed >= self.config.monitoring_duration:
                print("\n모니터링 시간이 종료되었습니다.")
                self.is_monitoring = False
                break

            # 일시정지 확인
            if self.is_paused:
                time.sleep(0.1)
                continue

            # 데이터 수집
            try:
                data = self.resource_collector.collect_all()
                self.data_manager.add_data(data)
                sample_count += 1

                # 진행 상황 표시
                remaining = self.config.monitoring_duration - elapsed
                if sample_count % 10 == 0:  # 10초마다 출력
                    cpu = data.get('cpu_percent', 0)
                    mem = data.get('memory_percent', 0)
                    print(f"[{sample_count:4d}] CPU: {cpu:5.1f}% | MEM: {mem:5.1f}% | 남은 시간: {remaining:5.0f}초", end='\r')

            except Exception as e:
                print(f"\n데이터 수집 오류: {e}")

            # 다음 샘플까지 대기
            time.sleep(self.config.sampling_interval)

        # 모니터링 종료
        self._on_monitoring_complete()

    def _on_monitoring_complete(self):
        """모니터링 완료 처리"""
        print("\n\n" + "=" * 60)
        print("모니터링 완료")
        print("=" * 60)

        # 세션 종료
        self.data_manager.finalize_session()

        # 통계 출력
        stats = self.data_manager.get_statistics()
        self._print_statistics(stats)

        # 경고 출력
        warnings = self.data_manager.get_warnings()
        if warnings:
            self._print_warnings(warnings)

        # PDF 보고서 생성
        print("\nPDF 보고서를 생성 중...")
        self._generate_pdf_report()

        # 데이터 내보내기
        print("\n데이터를 내보내는 중...")
        self._export_data()

        print("\n" + "=" * 60)
        print("모니터링 세션이 종료되었습니다.")
        print("=" * 60)

    def _print_statistics(self, stats: dict):
        """통계 출력"""
        print("\n통계 요약:")
        print("-" * 60)

        # CPU 통계
        cpu_stats = stats.get('cpu', {})
        print(f"CPU:")
        print(f"  평균: {cpu_stats.get('avg', 0):.1f}%")
        print(f"  최대: {cpu_stats.get('max', 0):.1f}%")
        print(f"  최소: {cpu_stats.get('min', 0):.1f}%")

        # 메모리 통계
        memory_stats = stats.get('memory', {})
        print(f"\n메모리:")
        print(f"  평균: {memory_stats.get('avg', 0):.1f}%")
        print(f"  최대: {memory_stats.get('max', 0):.1f}%")
        print(f"  최소: {memory_stats.get('min', 0):.1f}%")

        # 디스크 통계
        disk_stats = stats.get('disk', {})
        print(f"\n디스크:")
        print(f"  읽기 평균: {disk_stats.get('read_avg', 0)/1024/1024:.2f} MB/s")
        print(f"  읽기 최대: {disk_stats.get('read_max', 0)/1024/1024:.2f} MB/s")
        print(f"  쓰기 평균: {disk_stats.get('write_avg', 0)/1024/1024:.2f} MB/s")
        print(f"  쓰기 최대: {disk_stats.get('write_max', 0)/1024/1024:.2f} MB/s")

        # 네트워크 통계
        network_stats = stats.get('network', {})
        print(f"\n네트워크:")
        print(f"  다운로드 평균: {network_stats.get('download_avg', 0)/1024/1024:.2f} MB/s")
        print(f"  다운로드 최대: {network_stats.get('download_max', 0)/1024/1024:.2f} MB/s")
        print(f"  업로드 평균: {network_stats.get('upload_avg', 0)/1024/1024:.2f} MB/s")
        print(f"  업로드 최대: {network_stats.get('upload_max', 0)/1024/1024:.2f} MB/s")

        # GPU 통계
        gpu_stats = stats.get('gpu', {})
        if gpu_stats:
            print(f"\nGPU:")
            print(f"  사용률 평균: {gpu_stats.get('load_avg', 0):.1f}%")
            print(f"  사용률 최대: {gpu_stats.get('load_max', 0):.1f}%")
            print(f"  온도 평균: {gpu_stats.get('temp_avg', 0):.1f}°C")
            print(f"  온도 최대: {gpu_stats.get('temp_max', 0):.1f}°C")

        # 온도 통계
        temp_stats = stats.get('temperature', {})
        if temp_stats:
            print(f"\nCPU 온도:")
            print(f"  평균: {temp_stats.get('cpu_temp_avg', 0):.1f}°C")
            print(f"  최대: {temp_stats.get('cpu_temp_max', 0):.1f}°C")
            print(f"  최소: {temp_stats.get('cpu_temp_min', 0):.1f}°C")

    def _print_warnings(self, warnings: list):
        """경고 출력"""
        print("\n⚠️  경고 사항:")
        print("-" * 60)
        for warning in warnings:
            level_symbol = "🔴" if warning['level'] == 'critical' else "🟡"
            print(f"{level_symbol} [{warning['type']}] {warning['message']}")

    def _generate_pdf_report(self, output_path: str = None):
        """PDF 보고서 생성"""
        if not output_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = os.path.join(self.config.reports_dir, f"report_{timestamp}.pdf")

        try:
            system_info = self.resource_collector.get_system_info()
            pdf_gen = PDFGenerator(self.data_manager, system_info)
            success = pdf_gen.generate(output_path)

            if success:
                print(f"✅ PDF 보고서가 생성되었습니다: {output_path}")
            else:
                print(f"❌ PDF 보고서 생성에 실패했습니다.")

        except Exception as e:
            print(f"❌ PDF 보고서 생성 오류: {e}")

    def _export_data(self):
        """데이터 내보내기"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # JSON 내보내기
        json_path = os.path.join(self.config.data_dir, f"data_{timestamp}.json")
        self.data_manager.export_to_json(json_path)

        # CSV 내보내기
        csv_path = os.path.join(self.config.data_dir, f"data_{timestamp}.csv")
        self.data_manager.export_to_csv(csv_path)

    def start_dashboard(self):
        """대시보드 시작"""
        self.dashboard = Dashboard(self.resource_collector, self.data_manager)
        self.dashboard_thread = threading.Thread(target=self.dashboard.run, kwargs={'debug': False})
        self.dashboard_thread.daemon = True
        self.dashboard_thread.start()

        print(f"\n대시보드가 시작되었습니다: http://{self.config.dashboard_host}:{self.config.dashboard_port}")
        print("브라우저에서 위 주소로 접속하세요.\n")

    def stop(self):
        """모니터링 중지"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2)

    def pause(self):
        """모니터링 일시정지"""
        self.is_paused = True
        print("\n모니터링이 일시정지되었습니다.")

    def resume(self):
        """모니터링 재개"""
        self.is_paused = False
        print("\n모니터링을 재개합니다.")


def parse_arguments():
    """명령줄 인수 파싱"""
    parser = argparse.ArgumentParser(
        description="시스템 리소스 실시간 모니터링 시스템",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예제:
  python main.py                           # 기본 설정으로 5분간 모니터링
  python main.py --duration 600            # 10분간 모니터링
  python main.py --interval 0.5            # 0.5초마다 샘플링
  python main.py --no-dashboard            # 대시보드 없이 백그라운드 모니터링
  python main.py --output custom_report.pdf  # 사용자 지정 PDF 경로
        """
    )

    parser.add_argument(
        '--duration',
        type=int,
        default=300,
        help='모니터링 시간 (초), 기본값: 300 (5분)'
    )

    parser.add_argument(
        '--interval',
        type=float,
        default=1.0,
        help='샘플링 간격 (초), 기본값: 1.0'
    )

    parser.add_argument(
        '--no-dashboard',
        action='store_true',
        help='대시보드 없이 실행 (백그라운드 모니터링만)'
    )

    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='PDF 보고서 출력 경로'
    )

    return parser.parse_args()


def main():
    """메인 함수"""
    # 명령줄 인수 파싱
    args = parse_arguments()

    # 설정 생성
    monitoring_config = MonitoringConfig()
    monitoring_config.monitoring_duration = args.duration
    monitoring_config.sampling_interval = args.interval

    # 모니터 생성
    monitor = SystemMonitor(monitoring_config)

    try:
        # 대시보드 시작 (옵션)
        if not args.no_dashboard:
            monitor.start_dashboard()
            time.sleep(2)  # 대시보드 초기화 대기

        # 모니터링 시작
        monitor.start_monitoring()

        # 모니터링 완료 대기
        while monitor.is_monitoring:
            time.sleep(0.5)

        # PDF 경로 지정된 경우
        if args.output:
            monitor._generate_pdf_report(args.output)

    except KeyboardInterrupt:
        print("\n\n사용자에 의해 중단되었습니다.")
        monitor.stop()

    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
        monitor.stop()


if __name__ == "__main__":
    main()
