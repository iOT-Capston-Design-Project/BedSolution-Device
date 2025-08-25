# BedSolution Device
침대 압력 감지 및 히트맵 생성 시스템

## 프로젝트 개요
BedSolution Device는 침대에 설치된 압력 센서를 통해 사용자의 체위를 감지하고, 실시간으로 압력 히트맵을 생성하는 시스템입니다. 시리얼 통신을 통해 센서 데이터를 수집하고, AI 기반 감지 알고리즘으로 체위를 분석합니다.

## 주요 기능

- 📡 시리얼 통신을 통한 압력 센서 데이터 수집
- 🧠 AI 기반 체위 감지 및 분석
- 🔥 실시간 압력 히트맵 생성
- 🌐 Supabase를 통한 데이터 저장 및 동기화
- 🖥️ Rich 기반 CLI 인터페이스
- ⚙️ 설정 파일을 통한 시스템 구성

## 초기 세팅 방법

### 1. 저장소 클론

```bash
git clone <repository-url>
cd bedsolution_device
```

### 2. 가상환경 생성 및 활성화

```bash
# 가상환경 생성
python -m venv .venv

# 가상환경 활성화
# macOS/Linux
source .venv/bin/activate
```

### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

## 사용방법

### 1. 기본 실행

```bash
python src/main.py
```

### 2. CLI 메뉴 구조

프로그램 실행 시 다음과 같은 메인 메뉴가 표시됩니다:

- **1. Run**: 실시간 압력 감지 및 히트맵 표시
- **2. View Logs**: 로그 확인 및 상세 정보 조회
- **3. Model Training Logs**: 모델 훈련을 위한 실시간 데이터 수집
- **4. Register Device**: 디바이스 등록
- **5. Settings**: 시스템 설정 관리
- **q. Quit**: 프로그램 종료

### 3. 주요 기능 사용법

#### 실시간 압력 감지 (1. Run)
- `1. Run` 메뉴 선택
- 실시간으로 압력 센서 데이터를 수집하고 히트맵 표시
- 체위 변화를 실시간으로 감지
- 서버와 데이터 동기화 상태 표시

#### 로그 확인 (2. View Logs)
- `2. View Logs` 메뉴 선택
- 날짜별 로그 요약 확인
- 특정 날짜의 상세 로그 조회
- 서버에서 로그 데이터 가져오기

#### 모델 훈련 데이터 수집 (3. Model Training Logs)
- `3. Model Training Logs` 메뉴 선택
- AI 모델 훈련을 위한 실시간 센서 데이터 수집
- CSV 파일로 데이터 저장
- 실시간 데이터 스트림 표시

#### 디바이스 등록 (4. Register Device)
- `4. Register Device` 메뉴 선택
- 새로운 디바이스 ID 등록
- 서버와의 연결 테스트
- 기존 디바이스 정보 확인

#### 설정 관리 (5. Settings)
- `5. Settings` 메뉴 선택
- 서버 URL, API 키 등 서버 설정 수정
- 감지 알고리즘 파라미터 조정
- 설정 변경사항은 자동으로 저장
- 모든 설정 삭제 기능

### 4. 키보드 단축키

- `Enter`: 메뉴 선택
- `Ctrl+C`: 프로그램 강제 종료
- `q`: 일부 화면에서 뒤로 가기

## 문제 해결

### 시리얼 포트 접근 오류
- 시리얼 포트 권한 확인
- 다른 프로그램에서 포트 사용 중인지 확인

### 서버 연결 오류
- 서버 URL과 API 키 확인
- 네트워크 연결 상태 확인

### 의존성 설치 오류
- Python 버전 확인 (3.13 이상)
- 가상환경이 활성화되어 있는지 확인

## 개발자 정보

- **프로젝트**: BedSolution Device
- **언어**: Python 3.13+
- **주요 라이브러리**: Rich, Requests, Supabase, Python-dotenv