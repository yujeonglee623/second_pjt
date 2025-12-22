# 2차 프로젝트
```
프로젝트 기간: 2025-12-10 ~ 2025-12-19
팀명: 러다이트
팀원: 이유정, 양지후, 김예림
주제: 재무제표 데이터를 활용한 기업리스크 스코어링 시스템
```
## 프로젝트 개요
![Image](https://github.com/user-attachments/assets/7b262d77-3879-4765-b95c-5024f316acd6)
## 프로젝트 일정
![Image](https://github.com/user-attachments/assets/417ab198-b838-41e8-b7f9-48525460ca5d)

## 프로젝트 주제 선정 과정
![Image](https://github.com/user-attachments/assets/00b3d7ff-6ff6-48bb-8196-7a2a5fe7b6c5)
![Image](https://github.com/user-attachments/assets/b6513a8e-0b14-4669-a832-b86278c12761)
- 티몬/위메프
    - 2017년부터 자본잠식 상태, 영업적자 꾸준히 누적중  
    - but, 외형상으로는 플랫폼이 정상적으로 운영되고 있었기 때문에 기업의 재무 위험 사전에 인지하기 어려웠음
- Wirecard (독일)
    - DAX30에 포함된 대형 상장사였고, 공시/감사보고서 상 안전한기업으로 인식됨
    - 대규모 회계부정으로 파산
- 한진해운 (한국)
    - 국내 최대 해운사아지 국가 기간산업 수준의 기업
    - 2017년 파산 절차에 들어감
- Carillion (영국)
    - 정부 프로젝트 다수 수행하던 외형상 정상기업
    - 파산 직전까지 경고 없이 갑작스럽게 무너짐

## 문제점
### 문제점
![Image](https://github.com/user-attachments/assets/7c9e1fad-5bc7-4f78-99a0-c24c88495db4)
1. 여러가지 요인을 종합적으로 판단해야만 사전 위험을 알 수 있다.
2. 전문 지식이 없는 일반인이 쉽게 이해하기에는 어려운 지표가 많다.
3. 조기대응이 아닌 사후 확인에 그치는 경우가 많다.
### 목표 : 부도 예측 모델 생성
![Image](https://github.com/user-attachments/assets/268f5ab5-6867-4ba6-8867-90b975b2fb6c)
1. 전문가 영역에 있던 기업 리스크 판단을 개인 투자자도 이해하고 활용 가능하게 만드는 것
2. 공공 데이터 기반으로 기업의 상장폐지 및 부실 위험 신호를 조기에 포착하는 분석 프레임워크 구축

## AS-IS / TO-BE
![Image](https://github.com/user-attachments/assets/d2820e2c-9fb4-49e7-a5ca-ea2280d27353)
### AS-IS
1. 부도 원인은 부도/파산 등 위험요소가 발생한 후에야 리스크 인지 가능
2. 외부이용자의 경우 조기 위험 탐지에 한계가 있음
3. 상장 폐지 후 사유 단순 나열
### TO-BE
1. 상장폐지 등 위험요소 발생 전 조기 위험 신호 포착
2. 누적 리스크에 기인한 조기 위험 탐지
3. 비전문가도 설명 가능한 리스크 분석 및 시각화
> 기업의 위험을 사전에 감지하고 이를 정량적인 '리스크 점수' 형태로 제공할 수 있는지 검증

## 프로젝트 과정
### 모델학습설계
![Image](https://github.com/user-attachments/assets/aadcaa25-39c3-437a-93f3-c2ff6c81efc4)

### 사용 수식
- $부채비율=\frac{부채총계}{자본총계}\times100$  
    
- $영업이익률=\frac{영업이익}{매출액}\times100$  
     
- $순이익률=\frac{당기순이익}{매출액}\times100$  
    
- $ROA=\frac{당기순이익}{자산}\times100$
    * ROA: 총자산수익률 - 기업이 보유한 총자산을 얼마나 효율적으로 활용하여 수익을 냈는지 나타내는 수익성 지표

### 등급 산정
#### 신호등값(신용등급기반) 정의
![Image](https://github.com/user-attachments/assets/766f2679-b391-430b-9265-637da123c750)
- 상(안정): 신용도>=70
- 중(주의): 10<=신용도<70
- 하(위험): 신용도>10

#### 재무건전성 - 일반적으로 '부채비율 적정': 200% 이하
- 부채비율
    - 위험수준: 부채비율>200
    - 안정적: 부채비율<=200
- 영업이익률
    - 마이너스: 영업이익률<0
    - 안정적: 영업이익률>=0 (이익창출중)

#### 수익성 vs 안정성
- 초우량기업: 부채비율<=100 and 영업이익률>=5
- 자산가형 기업: 부채비율<=100 and 영업이익률<5
- 성장형기업: 부채비율>100 and 영업이익률>=5
- 위험군 기업: 이외

### 구현 모델
#### 부도기업 시계열 패턴 분석
![Image](https://github.com/user-attachments/assets/79882278-766a-4231-91e5-366da9dfddef)
![Image](https://github.com/user-attachments/assets/4cfb9857-4182-4358-bb0b-df7b7c0e4bb9)

#### y값 value를 활용한 리스크 진단 예시
![Image](https://github.com/user-attachments/assets/4b9cacb8-5c35-4af9-b50f-959d3f3a04d8)

### 활용 데이터
![Image](https://github.com/user-attachments/assets/843fe3cb-2e16-4e29-b594-3932fc89fd00)
![Image](https://github.com/user-attachments/assets/b838a81e-5084-45c7-95c0-7e4bd6bff8b8)

## 서비스 소개
### UI 디자인
![Image](https://github.com/user-attachments/assets/6457b48c-264b-4d2c-bd73-9b29d5c83101)  
![Image](https://github.com/user-attachments/assets/55293291-9b99-485a-8db4-ed39bf7b86ff)  
![Image](https://github.com/user-attachments/assets/f3b2ab2d-b66d-4bf3-8438-66aa1707e87a)

### Streamlit 서비스
- Streamlit 앱 링크
https://yujeonglee623-second-pj-2nd-project-final-streamlit-code-tsxzom.streamlit.app/
![Image](https://github.com/user-attachments/assets/87257d25-708e-4c3c-86e1-eb23776f9ff6)
![Image](https://github.com/user-attachments/assets/2f0f2556-0ef4-4b8c-952b-426b19f8e319)
1. 사이드바에서 종목을 입력해서 종목코드 찾기
2. 종목코드 검색 후 조회
3. 신호등으로 기업 안정성 예측 - 주요 위험 요인 있을시 분석내용 확인 가능
4. 재무 건전성, 기업 유형, 재무지표 수치, 최근 5개년 재무 추이, 동일 업종에서 안정성 더 높은 기업 추천 등 확인 가능

### 핵심 결과
![Image](https://github.com/user-attachments/assets/cca4fd04-f049-4bb5-a308-5204f9274b73)
1. 공공 재무제표 데이터만으로도 기업 리스크 구분 가능
2. 부도는 단일 시간이 아니라, 재무 리스크의 '누적 결과'임을 데이터로 확인 가능
3. 재무 건전성 지표 중심의 리스크 스코어랑 모델 구헌

## 결론
### 기대효과
![Image](https://github.com/user-attachments/assets/6671d31a-4034-4f5c-acc1-56232065b46f)
- 재무 비전공자도 기업 리스크를 점수와 시각화로 이해 가능
- 기업의 신용 리스크로 인한 일반 대중의 피해 예방
- 뉴스, 비재무 데이터 결합 시 고도화된 리스크 조기경보 시스템으로 확장 가능

### 시사점
![Image](https://github.com/user-attachments/assets/35e87146-81c1-45d0-bad7-1b3788bbecef)
- 데이터 딥러닝
    : 현재는2020-2025 상장폐지된 기업들만 학습시켰으나, 이후에 해당기간 이전에 상장폐지 한 기업들도 상장폐지 기업 사유 분석이나 데이터를 더욱 정교하게 전처리하여 머신러닝시키고, 정상기업도 비슷한 숫자로 더 러닝시켜서 이후에 자체적으로 딥러닝 가능하게 하는 것이 목표
- 비재무 데이터 머신러닝
    : 시간의 한계와 비용의 한계로 인해 비재무데이터를 머신러닝시키지 못한 아쉬움이 있음. 따라서 시간과 비용의 한계가 극복이 된다면 비재무 데이터도 머신러닝시키는 것이 목표.  
      AI 심층 분석 리포트의 코멘트는 동일 수치가 나오면 동일한 멘트가 나오게 되어있는데, 비재무데이터까지 머신러닝 시켜서 해당 기업의 상황에 맞는 더 자세한 레포트를 산출할 수 있게 하는 것이 목표.
- 보고서
    : 현재 제공되고 있는 다양한 기업의 신용평가서와 더욱 효율적인 내용과 문체, 그리고 형식을 학습시켜서 원하는대로 지류 보고서를 뽑아서 볼 수 있도록 완성도 높은 모델을 구축하는 것이 목표
