"""
PDF 보고서 생성 모듈
시스템 모니터링 데이터를 PDF 보고서로 생성합니다.
"""

import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import matplotlib
matplotlib.use('Agg')  # GUI 없이 그래프 생성
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from data_manager import DataManager
from config import config


class PDFGenerator:
    """PDF 보고서 생성 클래스"""

    def __init__(self, data_manager: DataManager, system_info: Dict[str, Any]):
        """초기화

        Args:
            data_manager: 데이터 매니저 인스턴스
            system_info: 시스템 정보
        """
        self.data_manager = data_manager
        self.system_info = system_info
        self.temp_images = []  # 임시 이미지 파일 목록

        # 한글 폰트 설정 (시스템에 따라 다를 수 있음)
        try:
            # Linux의 경우
            pdfmetrics.registerFont(TTFont('NanumGothic', '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'))
            self.korean_font = 'NanumGothic'
        except:
            try:
                # 다른 경로 시도
                pdfmetrics.registerFont(TTFont('NanumGothic', 'NanumGothic.ttf'))
                self.korean_font = 'NanumGothic'
            except:
                # 한글 폰트를 찾을 수 없으면 기본 폰트 사용
                self.korean_font = 'Helvetica'
                print("경고: 한글 폰트를 찾을 수 없습니다. 기본 폰트를 사용합니다.")

    def generate(self, output_path: str) -> bool:
        """PDF 보고서 생성

        Args:
            output_path: PDF 파일 경로

        Returns:
            성공 여부
        """
        try:
            # 그래프 생성
            self._create_graphs()

            # PDF 문서 생성
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18,
            )

            # 스토리 (내용) 생성
            story = []

            # 제목
            story.extend(self._create_title())

            # 시스템 정보
            story.extend(self._create_system_info())

            # 요약 통계
            story.extend(self._create_summary_statistics())

            # 경고 사항
            story.extend(self._create_warnings())

            # 페이지 나누기
            story.append(PageBreak())

            # 그래프
            story.extend(self._create_graphs_section())

            # 페이지 나누기
            story.append(PageBreak())

            # 상위 프로세스
            story.extend(self._create_top_processes())

            # PDF 빌드
            doc.build(story)

            # 임시 이미지 파일 삭제
            self._cleanup_temp_images()

            print(f"PDF 보고서가 생성되었습니다: {output_path}")
            return True

        except Exception as e:
            print(f"PDF 생성 오류: {e}")
            import traceback
            traceback.print_exc()
            self._cleanup_temp_images()
            return False

    def _create_title(self) -> List:
        """제목 섹션 생성"""
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName=self.korean_font,
        )

        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#7f8c8d'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName=self.korean_font,
        )

        story = []
        story.append(Paragraph("시스템 리소스 모니터링 보고서", title_style))

        # 생성 시간
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        story.append(Paragraph(f"생성 시간: {current_time}", subtitle_style))
        story.append(Spacer(1, 0.2 * inch))

        return story

    def _create_system_info(self) -> List:
        """시스템 정보 섹션 생성"""
        styles = getSampleStyleSheet()
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=12,
            fontName=self.korean_font,
        )

        story = []
        story.append(Paragraph("시스템 정보", heading_style))

        # 시스템 정보 테이블
        data = [
            ['항목', '값'],
            ['운영체제', self.system_info.get('platform', 'N/A')],
            ['OS 버전', self.system_info.get('platform_version', 'N/A')],
            ['프로세서', self.system_info.get('processor', 'N/A')],
            ['CPU 코어', f"{self.system_info.get('cpu_count_physical', 'N/A')} 물리 / {self.system_info.get('cpu_count_logical', 'N/A')} 논리"],
            ['호스트명', self.system_info.get('hostname', 'N/A')],
            ['아키텍처', self.system_info.get('architecture', 'N/A')],
        ]

        # 모니터링 세션 정보
        if self.data_manager.session_start_time and self.data_manager.session_end_time:
            duration = (self.data_manager.session_end_time - self.data_manager.session_start_time).total_seconds()
            data.append(['모니터링 시작', self.data_manager.session_start_time.strftime('%Y-%m-%d %H:%M:%S')])
            data.append(['모니터링 종료', self.data_manager.session_end_time.strftime('%Y-%m-%d %H:%M:%S')])
            data.append(['모니터링 시간', f"{duration:.0f}초 ({duration/60:.1f}분)"])
            data.append(['데이터 포인트', str(self.data_manager.get_data_count())])

        table = Table(data, colWidths=[2.5 * inch, 4 * inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), self.korean_font),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ecf0f1')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
        ]))

        story.append(table)
        story.append(Spacer(1, 0.3 * inch))

        return story

    def _create_summary_statistics(self) -> List:
        """요약 통계 섹션 생성"""
        styles = getSampleStyleSheet()
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=12,
            fontName=self.korean_font,
        )

        story = []
        story.append(Paragraph("요약 통계", heading_style))

        stats = self.data_manager.get_statistics()

        # CPU 통계
        cpu_stats = stats.get('cpu', {})
        memory_stats = stats.get('memory', {})
        disk_stats = stats.get('disk', {})
        network_stats = stats.get('network', {})

        data = [
            ['리소스', '평균', '최대', '최소'],
            ['CPU (%)', f"{cpu_stats.get('avg', 0):.1f}", f"{cpu_stats.get('max', 0):.1f}", f"{cpu_stats.get('min', 0):.1f}"],
            ['메모리 (%)', f"{memory_stats.get('avg', 0):.1f}", f"{memory_stats.get('max', 0):.1f}", f"{memory_stats.get('min', 0):.1f}"],
            ['디스크 읽기 (MB/s)', f"{disk_stats.get('read_avg', 0)/1024/1024:.2f}", f"{disk_stats.get('read_max', 0)/1024/1024:.2f}", '-'],
            ['디스크 쓰기 (MB/s)', f"{disk_stats.get('write_avg', 0)/1024/1024:.2f}", f"{disk_stats.get('write_max', 0)/1024/1024:.2f}", '-'],
            ['네트워크 업로드 (MB/s)', f"{network_stats.get('upload_avg', 0)/1024/1024:.2f}", f"{network_stats.get('upload_max', 0)/1024/1024:.2f}", '-'],
            ['네트워크 다운로드 (MB/s)', f"{network_stats.get('download_avg', 0)/1024/1024:.2f}", f"{network_stats.get('download_max', 0)/1024/1024:.2f}", '-'],
        ]

        # GPU 통계 추가
        gpu_stats = stats.get('gpu', {})
        if gpu_stats:
            data.append(['GPU 사용률 (%)', f"{gpu_stats.get('load_avg', 0):.1f}", f"{gpu_stats.get('load_max', 0):.1f}", '-'])
            data.append(['GPU 온도 (°C)', f"{gpu_stats.get('temp_avg', 0):.1f}", f"{gpu_stats.get('temp_max', 0):.1f}", '-'])

        # 온도 통계 추가
        temp_stats = stats.get('temperature', {})
        if temp_stats:
            data.append(['CPU 온도 (°C)', f"{temp_stats.get('cpu_temp_avg', 0):.1f}", f"{temp_stats.get('cpu_temp_max', 0):.1f}", f"{temp_stats.get('cpu_temp_min', 0):.1f}"])

        table = Table(data, colWidths=[2 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ecc71')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), self.korean_font),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ecf0f1')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
        ]))

        story.append(table)
        story.append(Spacer(1, 0.3 * inch))

        return story

    def _create_warnings(self) -> List:
        """경고 사항 섹션 생성"""
        styles = getSampleStyleSheet()
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=12,
            fontName=self.korean_font,
        )

        story = []
        warnings = self.data_manager.get_warnings()

        if warnings:
            story.append(Paragraph("경고 사항", heading_style))

            data = [['유형', '수준', '메시지']]
            for warning in warnings:
                level_color = colors.HexColor('#e74c3c') if warning['level'] == 'critical' else colors.HexColor('#f39c12')
                data.append([warning['type'], warning['level'].upper(), warning['message']])

            table = Table(data, colWidths=[1.5 * inch, 1 * inch, 4 * inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), self.korean_font),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#fadbd8')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e74c3c')),
            ]))

            story.append(table)
            story.append(Spacer(1, 0.3 * inch))
        else:
            story.append(Paragraph("경고 사항: 없음 (모든 리소스가 정상 범위 내에 있습니다.)", heading_style))
            story.append(Spacer(1, 0.3 * inch))

        return story

    def _create_graphs(self):
        """그래프 이미지 생성"""
        data = self.data_manager.get_all_data()
        if not data:
            return

        # 타임스탬프 변환
        timestamps = [datetime.fromisoformat(item['timestamp']) for item in data]

        # CPU 그래프
        cpu_values = [item.get('cpu_percent', 0) for item in data]
        self._save_line_graph(
            timestamps, cpu_values,
            'cpu_graph.png',
            'CPU 사용률 (%)',
            'CPU Usage Over Time',
            'red'
        )

        # 메모리 그래프
        memory_values = [item.get('memory_percent', 0) for item in data]
        self._save_line_graph(
            timestamps, memory_values,
            'memory_graph.png',
            '메모리 사용률 (%)',
            'Memory Usage Over Time',
            'blue'
        )

        # 디스크 I/O 그래프
        disk_read = [item.get('disk_read_speed', 0) / 1024 / 1024 for item in data]  # MB/s
        disk_write = [item.get('disk_write_speed', 0) / 1024 / 1024 for item in data]
        self._save_dual_line_graph(
            timestamps, disk_read, disk_write,
            'disk_graph.png',
            '디스크 I/O (MB/s)',
            'Disk I/O Over Time',
            'Read', 'Write',
            'green', 'orange'
        )

        # 네트워크 그래프
        net_download = [item.get('net_download_speed', 0) / 1024 / 1024 for item in data]  # MB/s
        net_upload = [item.get('net_upload_speed', 0) / 1024 / 1024 for item in data]
        self._save_dual_line_graph(
            timestamps, net_download, net_upload,
            'network_graph.png',
            '네트워크 트래픽 (MB/s)',
            'Network Traffic Over Time',
            'Download', 'Upload',
            'purple', 'cyan'
        )

        # GPU 그래프 (사용 가능한 경우)
        if data[0].get('gpu_available', False) and data[0].get('gpus', []):
            gpu_values = [item['gpus'][0].get('load', 0) if item.get('gpus', []) else 0 for item in data]
            self._save_line_graph(
                timestamps, gpu_values,
                'gpu_graph.png',
                'GPU 사용률 (%)',
                'GPU Usage Over Time',
                'magenta'
            )

    def _save_line_graph(self, timestamps, values, filename, ylabel, title, color):
        """단일 라인 그래프 저장"""
        plt.figure(figsize=(10, 4))
        plt.plot(timestamps, values, color=color, linewidth=2)
        plt.xlabel('Time')
        plt.ylabel(ylabel)
        plt.title(title)
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()

        filepath = os.path.join(config.reports_dir, filename)
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()
        self.temp_images.append(filepath)

    def _save_dual_line_graph(self, timestamps, values1, values2, filename, ylabel, title, label1, label2, color1, color2):
        """이중 라인 그래프 저장"""
        plt.figure(figsize=(10, 4))
        plt.plot(timestamps, values1, color=color1, linewidth=2, label=label1)
        plt.plot(timestamps, values2, color=color2, linewidth=2, label=label2)
        plt.xlabel('Time')
        plt.ylabel(ylabel)
        plt.title(title)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()

        filepath = os.path.join(config.reports_dir, filename)
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()
        self.temp_images.append(filepath)

    def _create_graphs_section(self) -> List:
        """그래프 섹션 생성"""
        styles = getSampleStyleSheet()
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=12,
            fontName=self.korean_font,
        )

        story = []
        story.append(Paragraph("리소스 추세 그래프", heading_style))

        # 그래프 이미지 추가
        for img_path in self.temp_images:
            if os.path.exists(img_path):
                img = Image(img_path, width=6.5 * inch, height=2.6 * inch)
                story.append(img)
                story.append(Spacer(1, 0.2 * inch))

        return story

    def _create_top_processes(self) -> List:
        """상위 프로세스 섹션 생성"""
        styles = getSampleStyleSheet()
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=12,
            fontName=self.korean_font,
        )

        story = []

        # 최신 데이터에서 프로세스 정보 가져오기
        latest_data = self.data_manager.get_latest_data()
        if not latest_data:
            return story

        # CPU 상위 프로세스
        top_cpu = latest_data.get('top_cpu_processes', [])
        if top_cpu:
            story.append(Paragraph("CPU 사용률 상위 프로세스", heading_style))

            data = [['순위', 'PID', '프로세스명', 'CPU (%)', '사용자']]
            for idx, proc in enumerate(top_cpu[:5], 1):
                data.append([
                    str(idx),
                    str(proc['pid']),
                    proc['name'][:30],  # 이름 길이 제한
                    f"{proc['cpu_percent']:.1f}",
                    proc.get('username', 'N/A')[:15]
                ])

            table = Table(data, colWidths=[0.5 * inch, 0.8 * inch, 2.5 * inch, 1 * inch, 1.7 * inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e67e22')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), self.korean_font),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ecf0f1')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
            ]))

            story.append(table)
            story.append(Spacer(1, 0.3 * inch))

        # 메모리 상위 프로세스
        top_memory = latest_data.get('top_memory_processes', [])
        if top_memory:
            story.append(Paragraph("메모리 사용률 상위 프로세스", heading_style))

            data = [['순위', 'PID', '프로세스명', '메모리 (%)', '사용자']]
            for idx, proc in enumerate(top_memory[:5], 1):
                data.append([
                    str(idx),
                    str(proc['pid']),
                    proc['name'][:30],
                    f"{proc['memory_percent']:.1f}",
                    proc.get('username', 'N/A')[:15]
                ])

            table = Table(data, colWidths=[0.5 * inch, 0.8 * inch, 2.5 * inch, 1 * inch, 1.7 * inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9b59b6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), self.korean_font),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ecf0f1')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
            ]))

            story.append(table)

        return story

    def _cleanup_temp_images(self):
        """임시 이미지 파일 삭제"""
        for img_path in self.temp_images:
            try:
                if os.path.exists(img_path):
                    os.remove(img_path)
            except Exception as e:
                print(f"임시 파일 삭제 오류 ({img_path}): {e}")
        self.temp_images = []


if __name__ == "__main__":
    # 테스트 코드
    print("PDFGenerator 테스트")
