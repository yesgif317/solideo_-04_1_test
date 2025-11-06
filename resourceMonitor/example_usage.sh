#!/bin/bash
# 시스템 리소스 모니터링 시스템 사용 예제

echo "시스템 리소스 모니터링 시스템 사용 예제"
echo ""

echo "1. 기본 사용 (5분간 모니터링, 대시보드 포함)"
echo "   python main.py"
echo ""

echo "2. 10분간 모니터링"
echo "   python main.py --duration 600"
echo ""

echo "3. 30초마다 샘플링"
echo "   python main.py --interval 0.5"
echo ""

echo "4. 대시보드 없이 백그라운드 모니터링"
echo "   python main.py --no-dashboard"
echo ""

echo "5. 사용자 지정 PDF 출력 경로"
echo "   python main.py --output my_report.pdf"
echo ""

echo "6. 조합: 10분, 0.5초 간격, 대시보드 없음"
echo "   python main.py --duration 600 --interval 0.5 --no-dashboard"
echo ""

echo "7. 도움말 보기"
echo "   python main.py --help"
echo ""

read -p "예제를 실행하시겠습니까? [1-7 또는 n]: " -n 1 -r
echo ""

case $REPLY in
    1)
        echo "기본 사용 예제 실행..."
        python main.py
        ;;
    2)
        echo "10분간 모니터링 실행..."
        python main.py --duration 600
        ;;
    3)
        echo "0.5초 간격 샘플링 실행..."
        python main.py --interval 0.5
        ;;
    4)
        echo "대시보드 없이 실행..."
        python main.py --no-dashboard
        ;;
    5)
        echo "사용자 지정 PDF 경로로 실행..."
        python main.py --output my_custom_report.pdf
        ;;
    6)
        echo "조합 예제 실행..."
        python main.py --duration 600 --interval 0.5 --no-dashboard
        ;;
    7)
        echo "도움말 표시..."
        python main.py --help
        ;;
    *)
        echo "종료합니다."
        exit 0
        ;;
esac
