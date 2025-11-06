"""
웹 기반 실시간 대시보드 모듈
Dash를 사용하여 실시간 시스템 리소스를 시각화합니다.
"""

import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from datetime import datetime
from typing import Dict, List, Any, Optional
import threading
import time

from config import config
from resource_collector import ResourceCollector
from data_manager import DataManager


class Dashboard:
    """실시간 대시보드 클래스"""

    def __init__(self, resource_collector: ResourceCollector, data_manager: DataManager):
        """초기화

        Args:
            resource_collector: 리소스 수집기 인스턴스
            data_manager: 데이터 매니저 인스턴스
        """
        self.resource_collector = resource_collector
        self.data_manager = data_manager
        self.app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        self.setup_layout()
        self.setup_callbacks()

    def setup_layout(self):
        """레이아웃 설정"""
        self.app.layout = dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H1("시스템 리소스 모니터링", className="text-center mb-4"),
                    html.Hr()
                ])
            ]),

            # 상태 카드
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("CPU", className="card-title"),
                            html.H2(id="cpu-value", className="card-text"),
                            html.P(id="cpu-status", className="card-text")
                        ])
                    ], id="cpu-card", color="light")
                ], width=3),

                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("메모리", className="card-title"),
                            html.H2(id="memory-value", className="card-text"),
                            html.P(id="memory-status", className="card-text")
                        ])
                    ], id="memory-card", color="light")
                ], width=3),

                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("디스크 I/O", className="card-title"),
                            html.H2(id="disk-value", className="card-text"),
                            html.P(id="disk-status", className="card-text")
                        ])
                    ], id="disk-card", color="light")
                ], width=3),

                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("네트워크", className="card-title"),
                            html.H2(id="network-value", className="card-text"),
                            html.P(id="network-status", className="card-text")
                        ])
                    ], id="network-card", color="light")
                ], width=3),
            ], className="mb-4"),

            # GPU 카드 (조건부)
            html.Div(id="gpu-row", children=[]),

            # 그래프
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id="cpu-graph")
                ], width=6),
                dbc.Col([
                    dcc.Graph(id="memory-graph")
                ], width=6),
            ], className="mb-4"),

            dbc.Row([
                dbc.Col([
                    dcc.Graph(id="disk-graph")
                ], width=6),
                dbc.Col([
                    dcc.Graph(id="network-graph")
                ], width=6),
            ], className="mb-4"),

            # GPU 그래프 (조건부)
            html.Div(id="gpu-graph-row", children=[]),

            # 상위 프로세스 테이블
            dbc.Row([
                dbc.Col([
                    html.H4("CPU 사용률 상위 프로세스"),
                    html.Div(id="top-cpu-processes")
                ], width=6),
                dbc.Col([
                    html.H4("메모리 사용률 상위 프로세스"),
                    html.Div(id="top-memory-processes")
                ], width=6),
            ], className="mb-4"),

            # 타이머 및 상태
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H5(id="timer-display", className="text-center"),
                        html.P(id="data-count", className="text-center"),
                    ])
                ])
            ]),

            # 업데이트 인터벌
            dcc.Interval(
                id='interval-component',
                interval=1000,  # 1초마다 업데이트
                n_intervals=0
            )
        ], fluid=True, style={'padding': '20px'})

    def setup_callbacks(self):
        """콜백 설정"""

        @self.app.callback(
            [
                Output("cpu-value", "children"),
                Output("cpu-status", "children"),
                Output("cpu-card", "color"),
                Output("memory-value", "children"),
                Output("memory-status", "children"),
                Output("memory-card", "color"),
                Output("disk-value", "children"),
                Output("disk-status", "children"),
                Output("network-value", "children"),
                Output("network-status", "children"),
                Output("gpu-row", "children"),
                Output("cpu-graph", "figure"),
                Output("memory-graph", "figure"),
                Output("disk-graph", "figure"),
                Output("network-graph", "figure"),
                Output("gpu-graph-row", "children"),
                Output("top-cpu-processes", "children"),
                Output("top-memory-processes", "children"),
                Output("timer-display", "children"),
                Output("data-count", "children"),
            ],
            Input("interval-component", "n_intervals")
        )
        def update_dashboard(n):
            """대시보드 업데이트"""
            # 최신 데이터 가져오기
            latest_data = self.data_manager.get_latest_data()
            all_data = self.data_manager.get_all_data()

            if not latest_data:
                return self._empty_dashboard()

            # CPU 카드
            cpu_percent = latest_data.get('cpu_percent', 0)
            cpu_status, cpu_color = config.get_cpu_status(cpu_percent)
            cpu_value = f"{cpu_percent:.1f}%"

            # 메모리 카드
            memory_percent = latest_data.get('memory_percent', 0)
            memory_status, memory_color = config.get_memory_status(memory_percent)
            memory_value = f"{memory_percent:.1f}%"
            memory_used_gb = latest_data.get('memory_used', 0) / 1024 / 1024 / 1024
            memory_total_gb = latest_data.get('memory_total', 0) / 1024 / 1024 / 1024
            memory_status_text = f"{memory_used_gb:.1f}GB / {memory_total_gb:.1f}GB ({memory_status})"

            # 디스크 카드
            disk_read_speed = latest_data.get('disk_read_speed', 0) / 1024 / 1024
            disk_write_speed = latest_data.get('disk_write_speed', 0) / 1024 / 1024
            disk_value = f"R: {disk_read_speed:.1f} MB/s"
            disk_status_text = f"W: {disk_write_speed:.1f} MB/s"

            # 네트워크 카드
            net_download_speed = latest_data.get('net_download_speed', 0) / 1024 / 1024
            net_upload_speed = latest_data.get('net_upload_speed', 0) / 1024 / 1024
            network_value = f"↓ {net_download_speed:.2f} MB/s"
            network_status_text = f"↑ {net_upload_speed:.2f} MB/s"

            # GPU 카드 (조건부)
            gpu_row = []
            if latest_data.get('gpu_available', False) and latest_data.get('gpus', []):
                gpu = latest_data['gpus'][0]
                gpu_load = gpu.get('load', 0)
                gpu_temp = gpu.get('temperature', 0)
                gpu_status, gpu_color = config.get_gpu_status(gpu_load)

                gpu_row = dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H4("GPU", className="card-title"),
                                html.H2(f"{gpu_load:.1f}%", className="card-text"),
                                html.P(f"온도: {gpu_temp:.1f}°C ({gpu_status})", className="card-text")
                            ])
                        ], color=self._get_bootstrap_color(gpu_color))
                    ], width=3),
                ], className="mb-4")

            # 그래프 생성
            cpu_graph = self._create_line_graph(all_data, 'cpu_percent', 'CPU 사용률 (%)', 'red')
            memory_graph = self._create_line_graph(all_data, 'memory_percent', '메모리 사용률 (%)', 'blue')

            # 디스크 그래프 (읽기/쓰기)
            disk_graph = self._create_disk_graph(all_data)

            # 네트워크 그래프 (다운로드/업로드)
            network_graph = self._create_network_graph(all_data)

            # GPU 그래프 (조건부)
            gpu_graph_row = []
            if latest_data.get('gpu_available', False) and latest_data.get('gpus', []):
                gpu_graph = self._create_gpu_graph(all_data)
                gpu_graph_row = dbc.Row([
                    dbc.Col([
                        dcc.Graph(id="gpu-usage-graph", figure=gpu_graph)
                    ], width=12),
                ], className="mb-4")

            # 상위 프로세스 테이블
            top_cpu_table = self._create_process_table(latest_data.get('top_cpu_processes', []), 'cpu')
            top_memory_table = self._create_process_table(latest_data.get('top_memory_processes', []), 'memory')

            # 타이머 표시
            if self.data_manager.session_start_time:
                elapsed = (datetime.now() - self.data_manager.session_start_time).total_seconds()
                remaining = config.monitoring_duration - elapsed
                timer_text = f"경과 시간: {elapsed:.0f}초 / 남은 시간: {max(0, remaining):.0f}초"
            else:
                timer_text = "모니터링 시작 대기 중..."

            data_count_text = f"수집된 데이터 포인트: {self.data_manager.get_data_count()}"

            return (
                cpu_value, f"상태: {cpu_status}", self._get_bootstrap_color(cpu_color),
                memory_value, memory_status_text, self._get_bootstrap_color(memory_color),
                disk_value, disk_status_text,
                network_value, network_status_text,
                gpu_row,
                cpu_graph, memory_graph, disk_graph, network_graph,
                gpu_graph_row,
                top_cpu_table, top_memory_table,
                timer_text, data_count_text
            )

    def _empty_dashboard(self):
        """빈 대시보드 반환"""
        empty_fig = go.Figure()
        empty_fig.update_layout(title="데이터 수집 중...")
        return (
            "0%", "대기 중", "light",
            "0%", "대기 중", "light",
            "0 MB/s", "0 MB/s",
            "0 MB/s", "0 MB/s",
            [],
            empty_fig, empty_fig, empty_fig, empty_fig,
            [],
            html.P("데이터 수집 중..."), html.P("데이터 수집 중..."),
            "대기 중...", "0"
        )

    def _get_bootstrap_color(self, hex_color: str) -> str:
        """HEX 색상을 Bootstrap 색상으로 변환"""
        color_map = {
            config.color_normal: "success",
            config.color_warning: "warning",
            config.color_critical: "danger",
        }
        return color_map.get(hex_color, "light")

    def _create_line_graph(self, data: List[Dict], field: str, title: str, color: str) -> go.Figure:
        """라인 그래프 생성"""
        if not data:
            return go.Figure()

        timestamps = [datetime.fromisoformat(item['timestamp']) for item in data]
        values = [item.get(field, 0) for item in data]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=values,
            mode='lines',
            name=title,
            line=dict(color=color, width=2),
            fill='tozeroy',
            fillcolor=f'rgba{self._hex_to_rgba(color, 0.2)}'
        ))

        fig.update_layout(
            title=title,
            xaxis_title='시간',
            yaxis_title='사용률 (%)',
            hovermode='x unified',
            template='plotly_white',
            height=300,
        )

        return fig

    def _create_disk_graph(self, data: List[Dict]) -> go.Figure:
        """디스크 I/O 그래프 생성"""
        if not data:
            return go.Figure()

        timestamps = [datetime.fromisoformat(item['timestamp']) for item in data]
        read_speeds = [item.get('disk_read_speed', 0) / 1024 / 1024 for item in data]
        write_speeds = [item.get('disk_write_speed', 0) / 1024 / 1024 for item in data]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=read_speeds,
            mode='lines',
            name='읽기',
            line=dict(color='green', width=2)
        ))
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=write_speeds,
            mode='lines',
            name='쓰기',
            line=dict(color='orange', width=2)
        ))

        fig.update_layout(
            title='디스크 I/O 속도',
            xaxis_title='시간',
            yaxis_title='속도 (MB/s)',
            hovermode='x unified',
            template='plotly_white',
            height=300,
        )

        return fig

    def _create_network_graph(self, data: List[Dict]) -> go.Figure:
        """네트워크 트래픽 그래프 생성"""
        if not data:
            return go.Figure()

        timestamps = [datetime.fromisoformat(item['timestamp']) for item in data]
        download_speeds = [item.get('net_download_speed', 0) / 1024 / 1024 for item in data]
        upload_speeds = [item.get('net_upload_speed', 0) / 1024 / 1024 for item in data]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=download_speeds,
            mode='lines',
            name='다운로드',
            line=dict(color='purple', width=2)
        ))
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=upload_speeds,
            mode='lines',
            name='업로드',
            line=dict(color='cyan', width=2)
        ))

        fig.update_layout(
            title='네트워크 트래픽',
            xaxis_title='시간',
            yaxis_title='속도 (MB/s)',
            hovermode='x unified',
            template='plotly_white',
            height=300,
        )

        return fig

    def _create_gpu_graph(self, data: List[Dict]) -> go.Figure:
        """GPU 사용률 그래프 생성"""
        if not data:
            return go.Figure()

        timestamps = [datetime.fromisoformat(item['timestamp']) for item in data]
        gpu_loads = [item['gpus'][0].get('load', 0) if item.get('gpus', []) else 0 for item in data]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=gpu_loads,
            mode='lines',
            name='GPU 사용률',
            line=dict(color='magenta', width=2),
            fill='tozeroy'
        ))

        fig.update_layout(
            title='GPU 사용률 (%)',
            xaxis_title='시간',
            yaxis_title='사용률 (%)',
            hovermode='x unified',
            template='plotly_white',
            height=300,
        )

        return fig

    def _create_process_table(self, processes: List[Dict], type: str) -> dbc.Table:
        """프로세스 테이블 생성"""
        if not processes:
            return html.P("데이터 없음")

        headers = ['순위', 'PID', '프로세스명', 'CPU (%)' if type == 'cpu' else '메모리 (%)']
        rows = []

        for idx, proc in enumerate(processes[:5], 1):
            value = proc.get('cpu_percent' if type == 'cpu' else 'memory_percent', 0)
            rows.append(html.Tr([
                html.Td(str(idx)),
                html.Td(str(proc.get('pid', 'N/A'))),
                html.Td(proc.get('name', 'N/A')[:30]),
                html.Td(f"{value:.1f}"),
            ]))

        table = dbc.Table(
            [html.Thead(html.Tr([html.Th(h) for h in headers]))] +
            [html.Tbody(rows)],
            bordered=True,
            hover=True,
            responsive=True,
            striped=True,
            size='sm'
        )

        return table

    def _hex_to_rgba(self, hex_color: str, alpha: float) -> str:
        """HEX 색상을 RGBA로 변환"""
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return f"({r}, {g}, {b}, {alpha})"

    def run(self, debug: bool = False):
        """대시보드 실행"""
        self.app.run_server(
            host=config.dashboard_host,
            port=config.dashboard_port,
            debug=debug
        )


if __name__ == "__main__":
    # 테스트 코드
    from resource_collector import ResourceCollector
    from data_manager import DataManager

    collector = ResourceCollector()
    manager = DataManager()

    dashboard = Dashboard(collector, manager)
    print(f"대시보드를 시작합니다: http://{config.dashboard_host}:{config.dashboard_port}")
    dashboard.run(debug=True)
