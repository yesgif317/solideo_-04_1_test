# 시스템 리소스 실시간 모니터링 시스템

시스템의 모든 리소스를 실시간으로 추적하고 시각화하여 모니터링 후 PDF 보고서를 자동 생성하는 Python 기반 모니터링 시스템입니다.

## 주요 기능

### 모니터링 대상 리소스
- ✅ **CPU**: 전체 및 코어별 사용률, 주파수, 통계
- ✅ **GPU**: 사용률, 메모리, 온도 (NVIDIA GPU 지원)
- ✅ **메모리(RAM)**: 사용/전체/비율, 스왑 메모리
- ✅ **디스크**: 사용량, 읽기/쓰기 속도
- ✅ **네트워크**: 업로드/다운로드 속도, 패킷 통계
- ✅ **온도**: CPU 및 시스템 온도 (지원되는 경우)
- ✅ **프로세스**: 상위 5개 프로세스 (CPU/메모리 기준)

### UI/UX 기능
- 📊 **실시간 웹 대시보드**: Dash 기반 반응형 대시보드
- 📈 **다양한 차트**: 라인 그래프, 게이지, 테이블
- 🎨 **색상 코딩**: 정상(녹색), 주의(노란색), 위험(빨간색)
- ⏱️ **타이머**: 경과 시간 및 남은 시간 표시

### 보고서 기능
- 📄 **자동 PDF 생성**: 모니터링 완료 후 자동 생성
- 📊 **통계 요약**: 평균/최대/최소 값
- 📈 **추세 그래프**: 시간별 리소스 변화
- ⚠️ **경고 사항**: 임계값 초과 항목
- 💾 **데이터 내보내기**: JSON, CSV 형식 지원

## 시스템 요구사항

### 운영체제
- Linux (권장)
- Windows
- macOS

### Python 버전
- Python 3.8 이상

### 필수 라이브러리
모든 필수 라이브러리는 `requirements.txt`에 명시되어 있습니다.

## 설치 가이드

### 1. 저장소 클론 또는 파일 다운로드

```bash
cd resourceMonitor
```

### 2. 가상 환경 생성 (권장)

```bash
# 가상 환경 생성
python3 -m venv venv

# 가상 환경 활성화
# Linux/Mac:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

### 3. 필수 라이브러리 설치

```bash
pip install -r requirements.txt
```

### 4. 한글 폰트 설치 (PDF 생성용, Linux만 해당)

```bash
# Ubuntu/Debian
sudo apt-get install fonts-nanum

# Fedora/CentOS
sudo yum install naver-nanum-fonts
```

### 5. GPU 모니터링 설정 (선택사항)

NVIDIA GPU가 있는 경우:

```bash
# NVIDIA 드라이버 및 CUDA가 설치되어 있어야 합니다
pip install GPUtil py3nvml
```

## 사용 가이드

### 기본 사용법

```bash
python main.py
```

기본 설정:
- 모니터링 시간: 5분 (300초)
- 샘플링 간격: 1초
- 웹 대시보드: http://127.0.0.1:8050

### 고급 옵션

```bash
# 10분간 모니터링
python main.py --duration 600

# 0.5초마다 샘플링
python main.py --interval 0.5

# 대시보드 없이 백그라운드 모니터링
python main.py --no-dashboard

# 사용자 지정 PDF 출력 경로
python main.py --output custom_report.pdf

# 조합 예제: 10분, 0.5초 간격, 대시보드 없음
python main.py --duration 600 --interval 0.5 --no-dashboard
```

### 도움말 보기

```bash
python main.py --help
```

## 프로젝트 구조

```
resourceMonitor/
├── main.py                 # 메인 애플리케이션
├── config.py               # 설정 관리
├── resource_collector.py   # 리소스 수집 모듈
├── data_manager.py         # 데이터 저장 및 관리
├── pdf_generator.py        # PDF 보고서 생성
├── dashboard.py            # 웹 대시보드
├── requirements.txt        # 필수 라이브러리
├── README.md              # 이 파일
├── reports/               # PDF 보고서 저장 (자동 생성)
└── data/                  # 데이터 파일 저장 (자동 생성)
```

## 설정 커스터마이징

`config.py` 파일을 수정하여 다음 항목을 조정할 수 있습니다:

### 임계값 설정

```python
# CPU 임계값
cpu_warning_threshold: float = 70.0   # 주의
cpu_critical_threshold: float = 90.0  # 위험

# 메모리 임계값
memory_warning_threshold: float = 70.0
memory_critical_threshold: float = 85.0

# GPU 임계값
gpu_warning_threshold: float = 75.0
gpu_critical_threshold: float = 90.0

# 온도 임계값
temp_warning_threshold: float = 70.0   # °C
temp_critical_threshold: float = 85.0  # °C
```

### 대시보드 설정

```python
dashboard_host: str = "127.0.0.1"  # 호스트
dashboard_port: int = 8050          # 포트
```

### 프로세스 표시 개수

```python
top_processes_count: int = 5  # 상위 프로세스 개수
```

## 출력 파일

### PDF 보고서
- 위치: `reports/report_YYYYMMDD_HHMMSS.pdf`
- 내용: 시스템 정보, 통계 요약, 그래프, 경고, 상위 프로세스

### 데이터 파일
- JSON: `data/data_YYYYMMDD_HHMMSS.json`
- CSV: `data/data_YYYYMMDD_HHMMSS.csv`

## 문제 해결

### GPU 모니터링이 작동하지 않음

**원인**: GPUtil 라이브러리가 설치되지 않았거나 NVIDIA GPU가 없음

**해결**:
```bash
pip install GPUtil py3nvml
```

NVIDIA GPU가 없으면 GPU 모니터링은 자동으로 비활성화됩니다.

### 한글이 PDF에서 깨짐

**원인**: 한글 폰트가 설치되지 않음

**해결** (Linux):
```bash
sudo apt-get install fonts-nanum
```

### 대시보드에 접속할 수 없음

**원인**: 방화벽 또는 포트 충돌

**해결**:
1. 방화벽에서 포트 8050 허용
2. 다른 포트 사용 (`config.py`에서 `dashboard_port` 변경)

### 권한 오류 (Permission Denied)

**원인**: 일부 시스템 정보는 관리자 권한 필요

**해결**:
```bash
# Linux/Mac
sudo python main.py

# Windows (관리자 권한으로 실행)
```

## 모듈별 기능 설명

### `resource_collector.py`
시스템 리소스를 수집하는 핵심 모듈
- psutil을 사용한 CPU, 메모리, 디스크, 네트워크 정보 수집
- GPUtil을 사용한 GPU 정보 수집 (선택적)
- 온도 센서 정보 수집

### `data_manager.py`
수집된 데이터를 저장하고 분석
- 실시간 데이터 저장
- 통계 계산 (평균, 최대, 최소, 표준편차)
- 경고 생성 (임계값 초과 감지)
- JSON/CSV 내보내기

### `pdf_generator.py`
PDF 보고서 생성
- ReportLab을 사용한 전문적인 PDF 생성
- Matplotlib을 사용한 그래프 생성
- 시스템 정보, 통계, 그래프, 경고 포함

### `dashboard.py`
웹 기반 실시간 대시보드
- Dash와 Plotly를 사용한 인터랙티브 대시보드
- 실시간 그래프 업데이트
- 색상 코딩을 통한 상태 표시

### `main.py`
메인 애플리케이션
- 모니터링 루프 관리
- 대시보드 및 모니터링 스레드 관리
- CLI 인터페이스 제공

## 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.

## 기여

버그 리포트 및 기능 제안을 환영합니다!

## 지원

문제가 발생하면 이슈를 등록해주세요.

## 변경 이력

### v1.0.0 (2024)
- 초기 릴리스
- CPU, GPU, 메모리, 디스크, 네트워크 모니터링
- 웹 대시보드
- PDF 보고서 자동 생성
- 데이터 내보내기 (JSON, CSV)

## 개발자 정보

시스템 리소스 모니터링 시스템

---

**참고**: 이 시스템은 모니터링 도구 자체가 시스템 리소스를 최소한으로 사용하도록 최적화되었습니다.
