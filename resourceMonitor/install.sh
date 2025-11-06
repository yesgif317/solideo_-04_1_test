#!/bin/bash
# 시스템 리소스 모니터링 시스템 설치 스크립트

echo "======================================"
echo "시스템 리소스 모니터링 시스템 설치"
echo "======================================"
echo ""

# Python 버전 확인
echo "Python 버전 확인 중..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python 버전: $PYTHON_VERSION"

# Python 3.8 이상 확인
REQUIRED_VERSION="3.8"
if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    echo "오류: Python 3.8 이상이 필요합니다."
    echo "현재 버전: $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python 버전 확인 완료"
echo ""

# 가상 환경 생성 여부 확인
read -p "가상 환경을 생성하시겠습니까? (권장) [y/n]: " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "가상 환경 생성 중..."
    python3 -m venv venv

    if [ $? -eq 0 ]; then
        echo "✅ 가상 환경 생성 완료"

        # 가상 환경 활성화
        source venv/bin/activate
        echo "✅ 가상 환경 활성화"
    else
        echo "❌ 가상 환경 생성 실패"
        exit 1
    fi
fi

echo ""
echo "필수 라이브러리 설치 중..."
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ 라이브러리 설치 완료"
else
    echo "❌ 라이브러리 설치 실패"
    exit 1
fi

echo ""
echo "======================================"
echo "설치가 완료되었습니다!"
echo "======================================"
echo ""
echo "실행 방법:"
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "1. 가상 환경 활성화: source venv/bin/activate"
    echo "2. 프로그램 실행: python main.py"
else
    echo "프로그램 실행: python main.py"
fi
echo ""
echo "자세한 사용법은 README.md를 참조하세요."
echo ""

# 한글 폰트 설치 안내 (Linux만)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "======================================"
    echo "PDF 한글 지원을 위한 추가 설정"
    echo "======================================"
    echo ""
    echo "한글 PDF 생성을 위해 나눔 폰트 설치가 필요합니다."
    echo ""
    echo "Ubuntu/Debian:"
    echo "  sudo apt-get install fonts-nanum"
    echo ""
    echo "Fedora/CentOS:"
    echo "  sudo yum install naver-nanum-fonts"
    echo ""
fi
